from github_utils import (
    get_current_labels, 
    add_label, 
    remove_label
)

STATES = [
    "agent:waiting-approval",
    "agent:implementing",
    "agent:waiting-review",
    "agent:completed"
]

def get_current_state():

    labels = get_current_labels()

    for state in STATES:

        if state in labels:
            return state

    return None


def set_state(new_state):

    current_labels = get_current_labels()

    if new_state in current_labels:

        print(
            f"État déjà positionné : {new_state}"
        )

        return

    for state in STATES:

        if state in current_labels:

            remove_label(state)

    add_label(new_state)

    print(
        f"Changement d'état : {new_state}"
    )

