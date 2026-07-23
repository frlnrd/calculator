from llm_utils import (
    call_llm,
    MODEL
)
from file_utils import (
    load_files
)
from github_utils import (
    get_issue_comments
)
from prompts import (
    ANALYSIS_PROMPT
)
from file_utils import (
    select_files
)
from state_utils import (
    set_state
)
from git_utils import (
    publish_comment
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


def analyse_issue(issue_title, issue_body, repo_name, issue_number, github_token, grok_api_key):

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
        "agent:waiting-approval"
    )

    comment_body = f"""## 🤖 Analyse automatique

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


def get_latest_agent_analysis(repo_name, issue_number, github_token):

    comments = get_issue_comments(repo_name, issue_number, github_token)

    for comment in reversed(comments):

        body = comment["body"]

        if "## 🤖 Analyse automatique" in body:
            return body

    return None
