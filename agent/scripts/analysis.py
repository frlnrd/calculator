from scripts.llm_utils import (
    call_llm,
    MODEL
)
from scripts.file_utils import (
    load_files
)
from scripts.github_utils import (
    get_issue_comments,
    publish_comment
)
from scripts.prompts import (
    ANALYSIS_PROMPT
)
from scripts.file_utils import (
    select_files
)
from scripts.state_utils import (
    set_state
)

def build_comments_context(repo_name, issue_number, github_token):

    comments = get_issue_comments(repo_name, issue_number, github_token)

    context = ""

    for comment in comments:

        author = comment["user"]["login"]
        body = comment["body"]

        context += f"""

=== COMMENTAIRE DE {author} ===

{body}
"""

    return context


def analyse_request(
    issue_number,
    issue_title,
    issue_body,
    repo_name,
    github_token,
    grok_api_key,
    additional_context="",
    target_state="agent:waiting-approval",
    analysis_title="## 🤖 Analyse automatique"
):
    selected_files = select_files(issue_title, issue_body, grok_api_key, repo_name)

    print("=== SELECTED FILES ===")
    print(selected_files)

    code_context = load_files(
        selected_files
    )

    comments_context = build_comments_context(repo_name, issue_number, github_token)

    analysis_prompt = ANALYSIS_PROMPT.format(
        issue_title=issue_title,
        issue_body=issue_body,
        comments_context=comments_context,
        additional_context=additional_context,
        code_context=code_context
    )
    analysis = call_llm(
        analysis_prompt,
        grok_api_key,
        repo_name
    )

    print("=== ANALYSIS ===")
    print(analysis)

    set_state(
        target_state,
        repo_name,
        issue_number,
        github_token
    )

    comment_body = f"""{analysis_title}

**Modèle utilisé :** `{MODEL}`

### Fichiers analysés

{chr(10).join(f"- `{f}`" for f in selected_files)}

---

{analysis}

---

Pour lancer l'implémentation :

`/approve`
"""

    publish_comment(
        comment_body, 
        github_token,
        repo_name,
        issue_number
    )


def analyse_issue(
    issue_number,
    issue_title,
    issue_body,
    repo_name,
    github_token,
    grok_api_key
):

    analyse_request(
        issue_number,
        issue_title,
        issue_body,
        repo_name,
        github_token,
        grok_api_key
    )


def analyse_review_changes(
    issue_number,
    issue_title,
    issue_body,
    repo_name,
    github_token,
    grok_api_key,
    review_state,
    review_body
):

    analyse_request(
        issue_number,
        issue_title,
        issue_body,
        repo_name,
        github_token,
        grok_api_key,
        additional_context=f"""
=== REVIEW CHANGES REQUESTED ===

Etat :

{review_state}

Commentaire :

{review_body}
""",
        target_state="agent:waiting-review-approval",
        analysis_title="## 🤖 Analyse des changements demandés"
    )


def get_latest_agent_analysis(repo_name, issue_number, github_token):

    comments = get_issue_comments(repo_name, issue_number, github_token)

    for comment in reversed(comments):

        body = comment["body"]

        if "## 🤖 Analyse automatique" in body:
            return body

    return None


def build_review_context(review_state, review_body):

    if not review_body:
        return ""

    return f"""
=== REVIEW CHANGES REQUESTED ===

Etat :

{review_state}

Commentaire du reviewer :

{review_body}
"""


