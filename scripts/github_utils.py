import requests

def get_headers(github_token):
    return {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }


def publish_comment(body, github_token):

    response = requests.post(
        f"https://api.github.com/repos/{REPO_NAME}/issues/{ISSUE_NUMBER}/comments",
        headers=get_headers(github_token),
        json={
            "body": body
        },
        timeout=30
    )

    print("=== GITHUB STATUS ===")
    print(response.status_code)

    response.raise_for_status()


def add_label(label_name, github_token):

    response = requests.post(
        f"https://api.github.com/repos/{REPO_NAME}/issues/{ISSUE_NUMBER}/labels",
        headers=get_headers(github_token),
        json={
            "labels": [label_name]
        }
    )

    print(f"=== ADD LABEL {label_name} ===")
    print(response.status_code)


def remove_label(label_name, github_token):

    response = requests.delete(
        f"https://api.github.com/repos/"
        f"{REPO_NAME}/issues/"
        f"{ISSUE_NUMBER}/labels/"
        f"{label_name}",
        headers=get_headers(github_token)
    )

    print(f"=== REMOVE LABEL {label_name} ===")
    print(response.status_code)


def get_issue_comments(github_token):

    response = requests.get(
        f"https://api.github.com/repos/{REPO_NAME}/issues/{ISSUE_NUMBER}/comments",
        headers=get_headers(github_token),
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def get_current_labels(github_token):

    response = requests.get(
        f"https://api.github.com/repos/{REPO_NAME}/issues/{ISSUE_NUMBER}",
        headers=get_headers(github_token),
        timeout=30
    )

    response.raise_for_status()

    return [
        label["name"]
        for label in response.json()["labels"]
    ]

