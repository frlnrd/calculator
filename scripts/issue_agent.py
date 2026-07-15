import os
import json
import requests

MODEL = "openai/gpt-oss-120b"

EVENT_NAME = os.environ.get("EVENT_NAME", "")
COMMENT_BODY = os.environ.get("COMMENT_BODY", "")

GROK_API_KEY = os.environ["GROK_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

ISSUE_TITLE = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY = os.environ.get("ISSUE_BODY", "")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")

print("=== EVENT ===")
print(EVENT_NAME)

if not ISSUE_NUMBER:
    print("Aucune issue détectée.")
    exit(0)


def get_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }


def call_llm(prompt):
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROK_API_KEY}",
            "HTTP-Referer": "https://github.com/frlnrd/calculator",
            "X-Title": "Calculator Agent",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2
        },
        timeout=60
    )

    print("=== GROQ STATUS ===")
    print(response.status_code)

    if response.status_code != 200:
        print(response.text)

        raise Exception(
            f"Erreur IA {response.status_code}: {response.text}"
        )

    data = response.json()

    return (
        data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
    )


def build_repository_tree():
    excluded_dirs = {
        ".git",
        ".github",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv"
    }

    paths = []

    for root, dirs, files in os.walk("."):

        dirs[:] = [
            d for d in dirs
            if d not in excluded_dirs
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


def add_label(label_name):

    response = requests.post(
        f"https://api.github.com/repos/{REPO_NAME}/issues/{ISSUE_NUMBER}/labels",
        headers=get_headers(),
        json={
            "labels": [label_name]
        }
    )

    print(f"=== LABEL {label_name} ===")
    print(response.status_code)


def publish_comment(body):

    comment_url = (
        f"https://api.github.com/repos/"
        f"{REPO_NAME}/issues/{ISSUE_NUMBER}/comments"
    )

    response = requests.post(
        comment_url,
        headers=get_headers(),
        json={
            "body": body
        },
        timeout=30
    )

    print("=== GITHUB STATUS ===")
    print(response.status_code)

    response.raise_for_status()


def select_files():

    repository_tree = build_repository_tree()

    print("=== REPOSITORY TREE ===")
    print(repository_tree)

    prompt = f"""
Tu es un développeur senior.

Voici l'arborescence d'un dépôt GitHub.

{repository_tree}

Issue :

Titre :
{ISSUE_TITLE}

Description :
{ISSUE_BODY}

Quels sont les fichiers les plus pertinents
pour traiter cette issue ?

Réponds UNIQUEMENT avec un tableau JSON.

Exemple :

["style.css", "index.html"]
"""

    response = call_llm(prompt)

    print("=== SELECTED FILES RAW ===")
    print(response)

    try:
        return json.loads(response)

    except Exception:
        return []


def analyse_issue():

    selected_files = select_files()

    print("=== SELECTED FILES ===")
    print(selected_files)

    code_context = load_files(
        selected_files
    )

    analysis_prompt = f"""
Tu es un ingénieur logiciel senior.

Tu analyses une issue GitHub.

Tu as accès au code réel du dépôt.

Tu ne dois jamais prétendre avoir exécuté
l'application.

Issue :

Titre :
{ISSUE_TITLE}

Description :
{ISSUE_BODY}

Code :

{code_context}

Réponds avec :

## Reproductibilité

## Fichiers concernés

## Analyse

## Cause probable

## Correctif proposé

## Complexité

Notée de 1/5 à 5/5

## Plan d'action
"""

    analysis = call_llm(
        analysis_prompt
    )

    print("=== ANALYSIS ===")
    print(analysis)

    add_label(
        "agent:waiting-approval"
    )

    comment_body = f"""## 🤖 Analyse automatique

**Modèle utilisé :** `{MODEL}`

### Fichiers analysés

{chr(10).join(f"- `{f}`" for f in selected_files)}

---

{analysis}

---

Pour lancer l'implémentation :

`/approve`
"""

    publish_comment(
        comment_body
    )


def approve_issue():

    add_label(
        "agent:implementing"
    )

    publish_comment(
        """✅ Validation reçue.

État actuel :

`agent:implementing`

La création automatique de branche
sera implémentée dans la prochaine étape.
"""
    )


if EVENT_NAME == "issue_comment":

    if COMMENT_BODY.strip() == "/approve":
        approve_issue()
    else:
        analyse_issue()

elif EVENT_NAME in [
    "issues",
    "workflow_dispatch"
]:
    analyse_issue()

else:

    print(
        f"Événement ignoré : {EVENT_NAME}"
    )