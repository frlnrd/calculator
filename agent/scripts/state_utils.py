from scripts.github_utils import (
    get_current_labels, 
    add_label, 
    remove_label
)
from scripts.config import REPO_NAME, ISSUE_NUMBER, GITHUB_TOKEN

STATES = [
    "agent:waiting-approval",
    "agent:implementing",
    "agent:waiting-review",
    "agent:completed"
]

def get_current_state(repo_name, issue_number, github_token):

    labels = get_current_labels(repo_name, issue_number, github_token)

    for state in STATES:

        if state in labels:
            return state

    return None


def set_state(new_state, repo_name, issue_number, github_token):

    current_labels = get_current_labels(repo_name, issue_number, github_token)

    if new_state in current_labels:

        print(
            f"État déjà positionné : {new_state}"
        )

        return

    for state in STATES:

        if state in current_labels:

            remove_label(state, github_token, repo_name, issue_number)

    add_label(new_state, github_token, repo_name, issue_number)

    print(
        f"Changement d'état : {new_state}"
    )

