import os
import json
import requests

MODEL = "openai/gpt-oss-120b"

GROK_API_KEY = os.environ["GROK_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

ISSUE_TITLE = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY = os.environ.get("ISSUE_BODY", "")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")

if not ISSUE_NUMBER:
    print("Aucune issue détectée.")
    exit(0)


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

    print("=== STATUS ===")
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

        except Exception as e:
            print(f"Erreur lecture {file_path}: {e}")

    return content


# --------------------------------------------------
# ETAPE 1 : ARBORESCENCE
# --------------------------------------------------

repository_tree = build_repository_tree()

print("=== REPOSITORY TREE ===")
print(repository_tree)

file_selection_prompt = f"""
Tu es un développeur senior.

Voici l'arborescence d'un dépôt GitHub.

{repository_tree}

Issue :

Titre :
{ISSUE_TITLE}

Description :
{ISSUE_BODY}

Quels sont les fichiers les plus pertinents pour
traiter cette issue ?

Réponds UNIQUEMENT par un JSON.

Exemple :

["style.css", "index.html"]

Ne mets aucun texte avant ou après le JSON.
"""

selected_files_response = call_llm(
    file_selection_prompt
)

print("=== SELECTED FILES RAW ===")
print(selected_files_response)

try:

    selected_files = json.loads(
        selected_files_response
    )

except Exception:

    selected_files = []

print("=== SELECTED FILES ===")
print(selected_files)

# --------------------------------------------------
# ETAPE 2 : CHARGEMENT DU CODE
# --------------------------------------------------

code_context = load_files(selected_files)

print("=== CODE CONTEXT SIZE ===")
print(len(code_context))

# --------------------------------------------------
# ETAPE 3 : ANALYSE
# --------------------------------------------------

analysis_prompt = f"""
Tu es un ingénieur logiciel senior.

Tu analyses une issue GitHub.

Tu as accès au code réel du dépôt.

Tu ne dois pas prétendre avoir exécuté
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

# --------------------------------------------------
# ETAPE 4 : COMMENTAIRE GITHUB
# --------------------------------------------------

comment_body = f"""## 🤖 Analyse automatique

**Modèle utilisé :** `{MODEL}`

### Fichiers analysés

{chr(10).join(f"- `{f}`" for f in selected_files)}

---

{analysis}
"""

comment_url = (
    f"https://api.github.com/repos/"
    f"{REPO_NAME}/issues/{ISSUE_NUMBER}/comments"
)

github_response = requests.post(
    comment_url,
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    },
    json={
        "body": comment_body
    },
    timeout=30
)

print("=== GITHUB STATUS ===")
print(github_response.status_code)

print("=== GITHUB RESPONSE ===")
print(github_response.text)

github_response.raise_for_status()

print("✅ Commentaire publié avec succès.")