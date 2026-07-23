import requests

from github_utils import (
    get_headers
)
from analysis import (
    analyse_issue
)
from implementation import (
    approve_issue, 
    handle_changes_requested
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
from github_utils import (
    resolve_issue_number,
    get_issue_number_from_pr
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


def main():

    global ISSUE_NUMBER

    ISSUE_NUMBER = resolve_issue_number(ISSUE_NUMBER, EVENT_NAME, REPO_NAME, PR_NUMBER, GITHUB_TOKEN)

    print("=== ISSUE NUMBER ===")
    print(ISSUE_NUMBER)

    if EVENT_NAME == "issue_comment":

        if COMMENT_BODY.strip() == "/approve":
            approve_issue(GITHUB_TOKEN, REPO_NAME, ISSUE_NUMBER, ISSUE_TITLE, ISSUE_BODY, GROK_API_KEY)
        else:
            analyse_issue()

    elif EVENT_NAME in [
        "issues",
        "workflow_dispatch"
    ]:

        analyse_issue(ISSUE_TITLE, ISSUE_BODY, REPO_NAME, ISSUE_NUMBER, GITHUB_TOKEN, GROK_API_KEY)
    elif EVENT_NAME == "pull_request_review":

        ISSUE_NUMBER = get_issue_number_from_pr(REPO_NAME, PR_NUMBER, GITHUB_TOKEN)

        print("=== ISSUE NUMBER ===")
        print(ISSUE_NUMBER)

        print("=== REVIEW STATE ===")
        print(REVIEW_STATE)

        print("=== REVIEW BODY ===")
        print(REVIEW_BODY)

        if REVIEW_STATE == "changes_requested":
            handle_changes_requested(ISSUE_NUMBER, ISSUE_TITLE, ISSUE_BODY, REPO_NAME, GITHUB_TOKEN, GROK_API_KEY, REVIEW_STATE, REVIEW_BODY)
    else:

        print(
            f"Événement ignoré : {EVENT_NAME}"
        )


if __name__ == "__main__":
    main()