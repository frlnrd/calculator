import json

from scripts.prompts import (
    IMPLEMENTATION_PROMPT,
    IMPLEMENTATION_PR_PROMPT
)
from scripts.llm_utils import (
    call_llm
)
from scripts.analysis import build_review_context
from scripts.state_utils import (
    set_state,
    get_current_state
)
from scripts.git_utils import (
    checkout_branch,
    commit_changes,
    push_branch,
)
from scripts.github_utils import (
    publish_comment,
    create_pull_request,
    assign_pull_request,
    create_branch
)
from scripts.analysis import (
    get_latest_agent_analysis
)
from scripts.file_utils import (
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

    response = call_llm(
        prompt, 
        grok_api_key=grok_api_key, 
        repo_name=repo_name
    )

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

    current_state = get_current_state(
        repo_name=repo_name,
        issue_number=issue_number,
        github_token=github_token
    )

    if current_state not in [
        "agent:waiting-approval",
        "agent:failed"
    ]:

        publish_comment(
            body=f"""⚠️ Commande `/approve` ignorée.

État actuel :

`{current_state}`

L'approbation n'est possible que depuis :

`agent:waiting-approval`
""", 
            github_token=github_token,
            repo_name=repo_name,
            issue_number=issue_number
        )
        return
    try:
        #
        # Analyse validée
        #
        analysis = get_latest_agent_analysis(
            repo_name=repo_name, 
            issue_number=issue_number, 
            github_token=github_token
            )

        if not analysis:

            publish_comment(
                body=f"""❌ Impossible de trouver une analyse à implémenter.""",
                github_token=github_token,
                repo_name=repo_name,
                issue_number=issue_number
            )

            return
        #
        # Branche
        #
        branch_name = create_branch(
            github_token=github_token, 
            repo_name=repo_name, 
            issue_number=issue_number
            )
        checkout_branch(
            branch_name=branch_name
        )
        set_state(
            new_state="agent:implementing",
            repo_name=repo_name,
            issue_number=issue_number,
            github_token=github_token
        )
        #
        # Code source
        #
        selected_files = select_files(
            issue_title=issue_title,
            issue_body=issue_body,
            grok_api_key=grok_api_key,
            repo_name=repo_name
        )
        code_context = load_files(
            file_list=selected_files
        )
        #
        # Génération
        #
        changes = generate_implementation(
            analysis=analysis,
            code_context=code_context,
            grok_api_key=grok_api_key,
            repo_name=repo_name
        )
        #
        # Ecriture des fichiers
        #
        apply_changes(
            changes=changes
        )
        #
        # Commit
        #
        commit_changes(issue_number=issue_number)
        #
        # Push
        #
        push_branch(
            branch_name=branch_name
        )
        #
        # Pull Request
        #
        pr = create_pull_request(
            branch_name=branch_name,
            repo_name=repo_name,
            github_token=github_token,
            issue_number=issue_number
        )
        assign_pull_request(
            pr_number=pr["number"],
            repo_name=repo_name,
            github_token=github_token
        )
        pr_url = pr["html_url"]
        set_state(
            new_state="agent:waiting-review",
            repo_name=repo_name,
            issue_number=issue_number,
            github_token=github_token
        )
        publish_comment(
            body=f"""✅ Implémentation terminée.

Branche :

`{branch_name}`

Pull Request :

{pr_url}

État actuel :

`agent:waiting-review`
""",
            github_token=github_token,
            repo_name=repo_name,
            issue_number=issue_number
        )

    except Exception as ex:

        set_state(
            new_state="agent:failed",
            repo_name=repo_name,
            issue_number=issue_number,
            github_token=github_token
        )

        publish_comment(
            body=f"""❌ Échec de l'implémentation.

Etat :

'agent:failed'

Erreur :

```text
{str(ex)}
""",
            github_token=github_token,
            repo_name=repo_name,
            issue_number=issue_number
        )
        raise


def handle_changes_requested(issue_number, issue_title, issue_body, repo_name, github_token, grok_api_key, review_state, review_body):

    current_state = get_current_state(
        repo_name=repo_name, 
        issue_number=issue_number, 
        github_token=github_token
        )

    if current_state != "agent:waiting-review":
        return

    try:
        branch_name = f"agent/issue-{issue_number}"

        checkout_branch(
            branch_name=branch_name
        )

        set_state(
            new_state="agent:implementing",
            repo_name=repo_name,
            issue_number=issue_number,
            github_token=github_token
        )

        analysis = get_latest_agent_analysis(
            repo_name=repo_name, 
            issue_number=issue_number, 
            github_token=github_token
            )

        selected_files = select_files(
            issue_title=issue_title, 
            issue_body=issue_body, 
            grok_api_key=grok_api_key, 
            repo_name=repo_name
            )

        code_context = load_files(
            file_list=selected_files
        )

        review_context = build_review_context(
            review_state=review_state, 
            review_body=review_body
        )

        implementation_pr_prompt = IMPLEMENTATION_PR_PROMPT.format(
            analysis=analysis,
            review_context=review_context,
            code_context=code_context
        )

        response = call_llm(
            prompt=implementation_pr_prompt,
            grok_api_key=grok_api_key,
            repo_name=repo_name
        )

        print("=== IMPLEMENTATION RAW RESPONSE ===")
        print(response)

        response = response.strip()

        if not response.endswith("}"):

            publish_comment(
                body=f"""❌ Réponse du modèle tronquée.

La réponse ne se termine pas par une accolade fermante.
""",
                github_token=github_token,
                repo_name=repo_name,
                issue_number=issue_number
            )

            return

        try:

            changes = json.loads(
                response
            )

        except Exception as ex:

            print("=== INVALID JSON ===")
            print(response)

            publish_comment(
                body=f"❌ JSON invalide généré par le modèle : {str(ex)}",
                github_token=github_token,
                repo_name=repo_name,
                issue_number=issue_number
            )

            return

        apply_changes(
            changes=changes
        )

        commit_changes(issue_number=issue_number)

        push_branch(
            branch_name=branch_name
        )

        set_state(
            new_state="agent:waiting-review",
            repo_name=repo_name,
            issue_number=issue_number,
            github_token=github_token
        )

        publish_comment(
            body="""✅ Demandes de revue prises en compte.

Un nouveau commit a été poussé sur la branche associée à l'issue.
""",
            github_token=github_token,
            repo_name=repo_name,
            issue_number=issue_number
        )

    except Exception as ex:

        set_state(
            new_state="agent:failed",
            repo_name=repo_name,
            issue_number=issue_number,
            github_token=github_token
        )

        publish_comment(
            body=f"""❌ Échec de la prise en compte de la review.

Etat :

`agent:failed`

Erreur :

```text
{str(ex)}
""",
            github_token=github_token,
            repo_name=repo_name,
            issue_number=issue_number
        )

        raise