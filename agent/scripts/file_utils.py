import os
import json
from scripts.constants import (
    EXCLUDED_DIRS,
    PROTECTED_PATHS,
    PROTECTED_FILES
)
from scripts.prompts import FILE_SELECTION_PROMPT
from scripts.llm_utils import call_llm

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


def apply_changes(changes):

    for file in changes["files"]:

        path = file["path"]

        validate_path(path)

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read()

        for change in file["changes"]:

            action = change["action"]

            if action == "append":

                content += (
                    "\n"
                    + change["content"]
                )

            elif action == "insert_after":

                anchor = change["anchor"]

                occurrences = content.count(
                    anchor
                )

                if occurrences == 0:

                    raise Exception(
                        f"Ancre introuvable : "
                        f"{anchor}"
                    )

                if occurrences > 1:

                    raise Exception(
                        f"Ancre non unique : "
                        f"{anchor}"
                    )

                index = content.find(anchor)

                if index == -1:

                    raise Exception(
                        f"Ancre introuvable : "
                        f"{anchor}"
                    )

                insert_position = (
                    index
                    + len(anchor)
                )

                content = (
                    content[:insert_position]
                    + "\n"
                    + change["content"]
                    + content[insert_position:]
                )

            elif action == "replace":

                search = change["search"]

                if search not in content:

                    raise Exception(
                        f"Texte introuvable : "
                        f"{search}"
                    )

                content = content.replace(
                    search,
                    change["replace"],
                    1
                )

            else:

                raise Exception(
                    f"Action inconnue : "
                    f"{action}"
                )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(content)