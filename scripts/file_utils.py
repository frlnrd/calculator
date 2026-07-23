import os
import json
from constants import (
    EXCLUDED_DIRS,
    PROTECTED_PATHS,
)
from prompts import FILE_SELECTION_PROMPT
from llm_utils import call_llm

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

        if path.startswith(protected_path):

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
    response = call_llm(prompt, grok_api_key, repo_name)

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
        return selected_files
    except Exception:
        return []


def apply_changes(changes):

    files = changes.get("files", [])

    for file in files:

        path = file["path"]
        if path.endswith(".pyc"):
            raise Exception(
                f"Modification interdite : {path}"
            )
        validate_path(path)
        content = file["content"]

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(content)

        print(f"=== WRITE {path} ===")
