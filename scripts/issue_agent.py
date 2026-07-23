import json
import requests

from llm_utils import (
    call_llm,
    MODEL
)
from github_utils import (
    publish_comment,
    get_issue_comments,
    get_headers
)
from state_utils import (
    set_state,
    get_current_state
)
from git_utils import (
    checkout_branch,
    commit_changes,
    push_branch
)
from config import (
    EVENT_NAME,
    COMMENT_BODY,
    GITHUB_TOKEN,
    GROK_API_KEY,
    ISSUE_TITLE,
    ISSUE_BODY,
    ISSUE_NUMBER,
    REPO_NAME,
    REVIEW_STATE,
    REVIEW_BODY,
    PR_NUMBER
)
from prompts import (
    ANALYSIS_PROMPT,
    IMPLEMENTATION_PROMPT,
    IMPLEMENTATION_PR_PROMPT
)
from file_utils import (
    load_files,
    select_files,
    apply_changes
)

print("=== EVENT ===")
print(EVENT_NAME)
print("=== ISSUE NUMBER ===")
print(ISSUE_NUMBER)
print("=== PR NUMBER ===")
print(PR_NUMBER)

if EVENT_NAME in [
    "issues",
    "issue_comment"
]:
    if not ISSUE_NUMBER:
        print("Aucune issue détectée.")
        exit(0)


def build_comments_context():

    comments = get_issue_comments(REPO_NAME, ISSUE_NUMBER, GITHUB_TOKEN)

    context = ""

    for comment in comments:

        author = comment["user"]["login"]
        body = comment["body"]

        context += f"""

=== COMMENTAIRE DE {author} ===

{body}
"""

    return context


def analyse_issue():

    selected_files = select_files()

    print("=== SELECTED FILES ===")
    print(selected_files)

    code_context = load_files(
        selected_files
    )

    comments_context = build_comments_context()

    analysis_prompt = ANALYSIS_PROMPT.format(
        issue_title=ISSUE_TITLE,
        issue_body=ISSUE_BODY,
        comments_context=comments_context,
        code_context=code_context
    )
    analysis = call_llm(
        analysis_prompt,
        GROK_API_KEY,
        REPO_NAME
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
        GITHUB_TOKEN,
        REPO_NAME,
        ISSUE_NUMBER
    )


def approve_issue():

    current_state = get_current_state()

    if current_state != "agent:waiting-approval":

        publish_comment(
            f"""⚠️ Commande `/approve` ignorée.

État actuel :

`{current_state}`

L'approbation n'est possible que depuis :

`agent:waiting-approval`
""", 
            GITHUB_TOKEN,
            REPO_NAME,
            ISSUE_NUMBER
        )
        return
    try:
        #
        # Analyse validée
        #
        analysis = get_latest_agent_analysis()

        if not analysis:

            publish_comment(
                "❌ Impossible de trouver une analyse à implémenter.",
                GITHUB_TOKEN,
                REPO_NAME,
                ISSUE_NUMBER
            )

            return
        #
        # Branche
        #
        branch_name = create_branch()
        checkout_branch(
            branch_name
        )
        set_state(
            "agent:implementing"
        )
        #
        # Code source
        #
        selected_files = select_files()
        code_context = load_files(
            selected_files
        )
        #
        # Génération
        #
        changes = generate_implementation(
            analysis,
            code_context
        )
        #
        # Ecriture des fichiers
        #
        apply_changes(
            changes
        )
        #
        # Commit
        #
        commit_changes(ISSUE_NUMBER)
        #
        # Push
        #
        push_branch(
            branch_name
        )
        #
        # Pull Request
        #
        pr = create_pull_request(
            branch_name
        )
        assign_pull_request(
            pr["number"]
        )
        pr_url = pr["html_url"]
        set_state(
            "agent:waiting-review"
        )
        publish_comment(
            f"""✅ Implémentation terminée.

Branche :

`{branch_name}`

Pull Request :

{pr_url}

État actuel :

`agent:waiting-review`
""",
            GITHUB_TOKEN,
            REPO_NAME,
            ISSUE_NUMBER
        )

    except Exception as ex:

        publish_comment(
            f"""❌ Échec de l'implémentation.

Erreur :

```text
{str(ex)}
""",
            GITHUB_TOKEN,
            REPO_NAME,
            ISSUE_NUMBER
        )
        raise


def create_branch():

    headers = get_headers(GITHUB_TOKEN)

    repo_response = requests.get(
        f"https://api.github.com/repos/{REPO_NAME}",
        headers=headers,
        timeout=30
    )

    repo_response.raise_for_status()

    default_branch = repo_response.json()[
        "default_branch"
    ]

    branch_response = requests.get(
        f"https://api.github.com/repos/{REPO_NAME}/branches/{default_branch}",
        headers=headers,
        timeout=30
    )

    branch_response.raise_for_status()

    sha = branch_response.json()[
        "commit"
    ][
        "sha"
    ]

    branch_name = (
        f"agent/issue-{ISSUE_NUMBER}"
    )

    create_response = requests.post(
        f"https://api.github.com/repos/{REPO_NAME}/git/refs",
        headers=headers,
        json={
            "ref": (
                f"refs/heads/{branch_name}"
            ),
            "sha": sha
        },
        timeout=30
    )
    #
    # 201 = créée
    # 422 = existe déjà
    #
    if create_response.status_code not in [
        201,
        422
    ]:
        create_response.raise_for_status()

    print(
        f"=== BRANCH {branch_name} ==="
    )

    return branch_name


def get_latest_agent_analysis():

    comments = get_issue_comments(REPO_NAME, ISSUE_NUMBER, GITHUB_TOKEN)

    for comment in reversed(comments):

        body = comment["body"]

        if "## 🤖 Analyse automatique" in body:
            return body

    return None


def generate_implementation(
    analysis,
    code_context
):

    prompt = IMPLEMENTATION_PROMPT.format(
        analysis=analysis,
        code_context=code_context
    )

    response = call_llm(prompt, GROK_API_KEY, REPO_NAME)

    try:
        print("=== GENERATED IMPLEMENTATION RAW ===")
        print(response)
        return json.loads(response)
    except Exception as ex:
        print("=== JSON ERROR ===")
        print(ex)
        print("=== INVALID JSON ===")
        print(response)
        raise


def create_pull_request(branch_name):

    response = requests.post(
        f"https://api.github.com/repos/{REPO_NAME}/pulls",
        headers=get_headers(GITHUB_TOKEN),
        json={
            "title": f"Fix issue #{ISSUE_NUMBER}",
            "head": branch_name,
            "base": "main",
            "body": f"Fixes #{ISSUE_NUMBER}"
        }
    )
    response.raise_for_status()
    return response.json()


def assign_pull_request(pr_number):

    response = requests.post(
        f"https://api.github.com/repos/{REPO_NAME}/issues/{pr_number}/assignees",
        headers=get_headers(GITHUB_TOKEN),
        json={
            "assignees": [
                "frlnrd"
            ]
        }
    )
    response.raise_for_status()


def handle_changes_requested():

    current_state = get_current_state()

    if current_state != "agent:waiting-review":
        return

    branch_name = f"agent/issue-{ISSUE_NUMBER}"

    checkout_branch(
        branch_name
    )

    set_state(
        "agent:implementing"
    )

    analysis = get_latest_agent_analysis()

    selected_files = select_files()

    code_context = load_files(
        selected_files
    )

    review_context = build_review_context()

    implementation_pr_prompt = IMPLEMENTATION_PR_PROMPT.format(
        analysis=analysis,
        review_context=review_context,
        code_context=code_context
    )

    response = call_llm(
        implementation_pr_prompt,
        GROK_API_KEY,
        REPO_NAME
    )

    print("=== IMPLEMENTATION RAW RESPONSE ===")
    print(response)

    changes = json.loads(
        response
    )

    apply_changes(
        changes
    )

    commit_changes(ISSUE_NUMBER)

    push_branch(
        branch_name
    )

    set_state(
        "agent:waiting-review"
    )

    publish_comment(
        """✅ Demandes de revue prises en compte.

Un nouveau commit a été poussé sur la branche associée à l'issue.
""",
        GITHUB_TOKEN,
        REPO_NAME,
        ISSUE_NUMBER
    )


def build_review_context():

    if not REVIEW_BODY:
        return ""

    return f"""
=== REVIEW CHANGES REQUESTED ===

Etat :

{REVIEW_STATE}

Commentaire du reviewer :

{REVIEW_BODY}
"""


def get_issue_number_from_pr():

    response = requests.get(
        f"https://api.github.com/repos/{REPO_NAME}/pulls/{PR_NUMBER}",
        headers=get_headers(GITHUB_TOKEN),
        timeout=30
    )

    response.raise_for_status()

    branch_name = response.json()["head"]["ref"]

    print("=== PR BRANCH ===")
    print(branch_name)

    if not branch_name.startswith(
        "agent/issue-"
    ):
        raise Exception(
            f"Branche invalide : {branch_name}"
        )

    return branch_name.replace(
        "agent/issue-",
        ""
    )


def resolve_issue_number():

    if ISSUE_NUMBER:
        return ISSUE_NUMBER

    if EVENT_NAME == "pull_request_review":
        return get_issue_number_from_pr()

    return ISSUE_NUMBER


def main():

    global ISSUE_NUMBER

    ISSUE_NUMBER = resolve_issue_number()

    print("=== ISSUE NUMBER ===")
    print(ISSUE_NUMBER)

    if EVENT_NAME == "issue_comment":

        if COMMENT_BODY.strip() == "/approve":
            approve_issue()
        else:
            analyse_issue()

    elif EVENT_NAME in [
        "issues",
        "workflow_dispatch"
    ]:

        analyse_issue()
    elif EVENT_NAME == "pull_request_review":

        ISSUE_NUMBER = get_issue_number_from_pr()

        print("=== ISSUE NUMBER ===")
        print(ISSUE_NUMBER)

        print("=== REVIEW STATE ===")
        print(REVIEW_STATE)

        print("=== REVIEW BODY ===")
        print(REVIEW_BODY)

        if REVIEW_STATE == "changes_requested":
            handle_changes_requested()
    else:

        print(
            f"Événement ignoré : {EVENT_NAME}"
        )


if __name__ == "__main__":
    main()