import requests

def get_headers(github_token):
    return {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }


def publish_comment(body, github_token, repo_name, issue_number):

    response = requests.post(
        f"https://api.github.com/repos/{repo_name}/issues/{issue_number}/comments",
        headers=get_headers(github_token),
        json={
            "body": body
        },
        timeout=30
    )

    print("=== GITHUB STATUS ===")
    print(response.status_code)

    response.raise_for_status()


def add_label(
    label_name, 
    github_token,
    repo_name,
    issue_number,
):

    response = requests.post(
        f"https://api.github.com/repos/{repo_name}/issues/{issue_number}/labels",
        headers=get_headers(github_token),
        json={
            "labels": [label_name]
        }
    )

    print(f"=== ADD LABEL {label_name} ===")
    print(response.status_code)


def remove_label(
    label_name, 
    github_token,
    repo_name,
    issue_number
):

    response = requests.delete(
        f"https://api.github.com/repos/"
        f"{repo_name}/issues/"
        f"{issue_number}/labels/"
        f"{label_name}",
        headers=get_headers(github_token)
    )

    print(f"=== REMOVE LABEL {label_name} ===")
    print(response.status_code)


def get_issue_comments(
    repo_name,
    issue_number,
    github_token
):
    response = requests.get(
        f"https://api.github.com/repos/{repo_name}/issues/{issue_number}/comments",
        headers=get_headers(github_token),
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def get_current_labels(
    repo_name,
    issue_number,
    github_token
):

    response = requests.get(
        f"https://api.github.com/repos/{repo_name}/issues/{issue_number}",
        headers=get_headers(github_token),
        timeout=30
    )

    response.raise_for_status()

    return [
        label["name"]
        for label in response.json()["labels"]
    ]


def create_branch(github_token, repo_name, issue_number):

    headers = get_headers(github_token)

    repo_response = requests.get(
        f"https://api.github.com/repos/{repo_name}",
        headers=headers,
        timeout=30
    )

    repo_response.raise_for_status()

    default_branch = repo_response.json()[
        "default_branch"
    ]

    branch_response = requests.get(
        f"https://api.github.com/repos/{repo_name}/branches/{default_branch}",
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
        f"agent/issue-{issue_number}"
    )

    create_response = requests.post(
        f"https://api.github.com/repos/{repo_name}/git/refs",
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


def create_pull_request(branch_name, repo_name, github_token, issue_number):

    response = requests.post(
        f"https://api.github.com/repos/{repo_name}/pulls",
        headers=get_headers(github_token),
        json={
            "title": f"Fix issue #{issue_number}",
            "head": branch_name,
            "base": "main",
            "body": f"Fixes #{issue_number}"
        }
    )
    response.raise_for_status()
    return response.json()


def assign_pull_request(pr_number, repo_name, github_token):

    response = requests.post(
        f"https://api.github.com/repos/{repo_name}/issues/{pr_number}/assignees",
        headers=get_headers(github_token),
        json={
            "assignees": [
                "frlnrd"
            ]
        }
    )
    response.raise_for_status()


def get_issue_number_from_pr(repo_name, pr_number, github_token):

    response = requests.get(
        f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}",
        headers=get_headers(github_token),
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


def resolve_issue_number(issue_number, event_name, repo_name, pr_number, github_token):

    if issue_number:
        return issue_number

    if event_name == "pull_request_review":
        return get_issue_number_from_pr(repo_name, pr_number, github_token)

    return issue_number


