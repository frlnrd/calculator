import os
import json
from scripts.constants import (
    EXCLUDED_DIRS,
    PROTECTED_PATHS,
    PROTECTED_FILES
)
from scripts.prompts import (
    FILE_SELECTION_PROMPT, 
    IMPLEMENT_CHANGE_PROMPT
)
from scripts.llm_utils import call_llm
from classes.change_context import ChangeContext

def validate_path(path):

    if path.startswith("/"):
        raise Exception(
            f"Chemin absolu interdit : {path}"
        )

    if ".." in path:
        raise Exception(
            f"Path traversal interdit : {path}"
        )

    for protected_path in PROTECTED_PATHS:

        if path.startswith(protected_path) or path in PROTECTED_FILES:

            raise Exception(
                f"Modification interdite : {path}"
            )


def build_repository_tree():

    paths = []

    for root, dirs, files in os.walk("."):

        dirs[:] = [
            d for d in dirs
            if d not in EXCLUDED_DIRS
        ]

        for file in files:

            path = os.path.relpath(
                os.path.join(root, file),
                "."
            )

            paths.append(path)

    return "\n".join(sorted(paths))


def load_files(file_list):

    content = ""

    for file_path in file_list:

        file_path = file_path.strip()

        if not file_path:
            continue

        if not os.path.exists(file_path):
            continue

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as f:

                file_content = f.read()

            content += (
                f"\n\n=== FICHIER : {file_path} ===\n\n"
            )

            content += file_content[:10000]

        except Exception as ex:

            print(
                f"Erreur lecture {file_path}: {ex}"
            )

    return content


def select_files(issue_title, issue_body, grok_api_key, repo_name):

    repository_tree = build_repository_tree()

    print("=== REPOSITORY TREE ===")
    print(repository_tree)

    prompt = FILE_SELECTION_PROMPT.format(
        repository_tree=repository_tree,
        issue_title=issue_title,
        issue_body=issue_body
    )
    response = call_llm(
        prompt=prompt,
        grok_api_key=grok_api_key,
        repo_name=repo_name
    )

    print("=== SELECTED FILES RAW ===")
    print(response)

    try:
        selected_files = json.loads(response)
        selected_files = [
            f.strip()
            for f in selected_files
            if isinstance(f, str)
            and f.strip()
        ]
        print("=== SELECTED FILES FILTERED ===")
        print(selected_files)
        selected_files = selected_files[:3]
        return selected_files
    except Exception:
        return []


def apply_changes(
    changes,
    context
):

    for patch in changes["patches"]:

        path = patch["path"]

        validate_path(path)

        current_content = load_file(
            path=path
        )

        for change in changes["patches"]:

            change_context = (
                ChangeContext(
                    path=path,
                    file_content=current_content,
                    repo_name=context.repo_name,
                    grok_api_key=context.grok_api_key,
                    change_planning=changes,
                    change_id=patch["id"],
                    change_description=patch["description"],
                    total=patch["total"]
                )
            )

            current_content = implement_change(
                change_context
            )

        save_file(
            path=path,
            content=current_content
        )


def load_file(path):

    validate_path(path)

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


def save_file(path, content):

    validate_path(path)

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(content)

def implement_change(change_context):

    content = ""

    for patch_id in range(
        1,
        change_context.total + 1
    ):

        prompt = IMPLEMENT_CHANGE_PROMPT.format(
            patch_id=change_context.change_id,
            change_planning=change_context.change_planning,
            file_content=change_context.file_content
        )

        response = call_llm(
            prompt=prompt,
            grok_api_key=change_context.grok_api_key,
            repo_name=change_context.repo_name
        )

        response = response.strip()

        print("=== IMPLEMENT CHANGE RESPONSE ===")
        print(response)

        print(repr(response))
        print(repr(change_context.end_marker))
        if response.endswith(
            change_context.end_marker
        ):

            content += response.removesuffix(
                change_context.end_marker
            )

            break

        content += response
        print("=== CURRENT CONTENT LENGTH ===")
        print(len(content))

    return content