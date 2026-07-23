import json

from prompts import (
    IMPLEMENTATION_PROMPT,
    IMPLEMENTATION_PR_PROMPT
)
from config import (
    REPO_NAME,
    GROK_API_KEY
)
from llm_utils import (
    call_llm
)
from analysis import build_review_context
from state_utils import (
    set_state,
    get_current_state
)
from git_utils import (
    checkout_branch,
    commit_changes,
    push_branch,
    create_branch
)
from github_utils import (
    publish_comment,
    create_pull_request,
    assign_pull_request
)
from analysis import (
    get_latest_agent_analysis
)
from file_utils import (
    load_files,
    apply_changes,
    select_files
)

def generate_implementation(
    analysis,
    code_context,
    grok_api_key,
    repo_name
):

    prompt = IMPLEMENTATION_PROMPT.format(
        analysis=analysis,
        code_context=code_context
    )

    response = call_llm(prompt, grok_api_key, repo_name)

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


def approve_issue(github_token, repo_name, issue_number, issue_title, issue_body, grok_api_key):

    current_state = get_current_state()

    if current_state != "agent:waiting-approval":

        publish_comment(
            f"""⚠️ Commande `/approve` ignorée.

État actuel :

`{current_state}`

L'approbation n'est possible que depuis :

`agent:waiting-approval`
""", 
            github_token,
            repo_name,
            issue_number
        )
        return
    try:
        #
        # Analyse validée
        #
        analysis = get_latest_agent_analysis(repo_name, issue_number, github_token)

        if not analysis:

            publish_comment(
                "❌ Impossible de trouver une analyse à implémenter.",
                github_token,
                repo_name,
                issue_number
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
        selected_files = select_files(issue_title, issue_body, grok_api_key, repo_name)
        code_context = load_files(
            selected_files
        )
        #
        # Génération
        #
        changes = generate_implementation(
            analysis,
            code_context,
            grok_api_key,
            repo_name
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
        commit_changes(issue_number)
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
            github_token,
            repo_name,
            issue_number
        )

    except Exception as ex:

        publish_comment(
            f"""❌ Échec de l'implémentation.

Erreur :

```text
{str(ex)}
""",
            github_token,
            repo_name,
            issue_number
        )
        raise


def handle_changes_requested(issue_number, issue_title, issue_body, repo_name, github_token, grok_api_key, review_state, review_body):

    current_state = get_current_state()

    if current_state != "agent:waiting-review":
        return

    branch_name = f"agent/issue-{issue_number}"

    checkout_branch(
        branch_name
    )

    set_state(
        "agent:implementing"
    )

    analysis = get_latest_agent_analysis(repo_name, issue_number, github_token)

    selected_files = select_files(issue_title, issue_body, grok_api_key, repo_name)

    code_context = load_files(
        selected_files
    )

    review_context = build_review_context(review_state, review_body)

    implementation_pr_prompt = IMPLEMENTATION_PR_PROMPT.format(
        analysis=analysis,
        review_context=review_context,
        code_context=code_context
    )

    response = call_llm(
        implementation_pr_prompt,
        grok_api_key,
        repo_name
    )

    print("=== IMPLEMENTATION RAW RESPONSE ===")
    print(response)

    changes = json.loads(
        response
    )

    apply_changes(
        changes
    )

    commit_changes(issue_number)

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
        github_token,
        repo_name,
        issue_number
    )
