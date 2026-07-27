from scripts.state_utils import get_current_state
from scripts.analysis import (
    analyse_issue,
    analyse_review_changes
)
from scripts.implementation import (
    approve_issue, 
    handle_changes_requested
)
from scripts.config import (
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
    PR_NUMBER,
    TARGET_TYPE,
    TARGET_ID
)
from scripts.github_utils import (
    get_issue_number_from_pr
)
from classes.context import AgentContext

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


def main():

    global ISSUE_NUMBER

    context = AgentContext(
        repo_name=REPO_NAME,

        issue_number=ISSUE_NUMBER,
        issue_title=ISSUE_TITLE,
        issue_body=ISSUE_BODY,

        github_token=GITHUB_TOKEN,
        grok_api_key=GROK_API_KEY,

        review_state=REVIEW_STATE,
        review_body=REVIEW_BODY,

        target_type=TARGET_TYPE,
        target_id=TARGET_ID
    )

    print("=== ISSUE NUMBER ===")
    print(ISSUE_NUMBER)

    if EVENT_NAME == "issue_comment":

        if COMMENT_BODY.strip() == "/approve":
            current_state = get_current_state(
                repo_name=REPO_NAME,
                issue_number=ISSUE_NUMBER,
                github_token=GITHUB_TOKEN
            )

            if current_state in [
                "agent:waiting-approval",
                "agent:failed"
            ]:

                approve_issue(context)

            elif current_state == "agent:waiting-review-approval":

                handle_changes_requested(context)
            else:
                print(
                    f"/approve ignoré pour l'état : {current_state}"
                )
        else:
            analyse_issue(context)

    elif EVENT_NAME in [
        "issues",
        "workflow_dispatch"
    ]:

        analyse_issue(context)
    elif EVENT_NAME == "pull_request_review":

        print("=== ISSUE NUMBER ===")
        print(ISSUE_NUMBER)

        print("=== REVIEW STATE ===")
        print(REVIEW_STATE)

        print("=== REVIEW BODY ===")
        print(REVIEW_BODY)

        if REVIEW_STATE == "changes_requested":

            ISSUE_NUMBER = get_issue_number_from_pr(REPO_NAME, PR_NUMBER, GITHUB_TOKEN)

            print(f"=== CHANGES REQUESTED FOR ISSUE {ISSUE_NUMBER} ===")
            context.issue_number=ISSUE_NUMBER

            print(f"TARGET_TYPE={context.target_type}")
            print(f"TARGET_ID={context.target_id}")
            print(f"ISSUE_NUMBER={context.issue_number}")
            analyse_review_changes(context)
    else:
        print(
            f"Événement ignoré : {EVENT_NAME}"
        )


if __name__ == "__main__":
    main()
