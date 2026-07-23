import requests

from github_utils import (
    get_headers
)
from analysis import (
    analyse_issue
)
from implementation import approve_issue, handle_changes_requested
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
            approve_issue(GITHUB_TOKEN, REPO_NAME, ISSUE_NUMBER, ISSUE_TITLE, ISSUE_BODY, GROK_API_KEY)
        else:
            analyse_issue()

    elif EVENT_NAME in [
        "issues",
        "workflow_dispatch"
    ]:

        analyse_issue(ISSUE_TITLE, ISSUE_BODY, REPO_NAME, ISSUE_NUMBER, GITHUB_TOKEN, GROK_API_KEY)
    elif EVENT_NAME == "pull_request_review":

        ISSUE_NUMBER = get_issue_number_from_pr()

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