import os
import json
import subprocess
import requests


MODEL = "openai/gpt-oss-120b"

STATES = [
    "agent:waiting-approval",
    "agent:implementing",
    "agent:waiting-review",
    "agent:completed"
]

PROTECTED_PATHS = [
    ".git/",
    ".github/"
]

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

PROTECTED_PATHS = [
    ".git/",
    ".github/"
]

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

def get_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

def get_current_labels():

    response = requests.get(
        f"https://api.github.com/repos/{REPO_NAME}/issues/{ISSUE_NUMBER}",
        headers=get_headers(),
        timeout=30
    )

    response.raise_for_status()

    return [
        label["name"]
        for label in response.json()["labels"]
    ]

def get_current_state():

    labels = get_current_labels()

    for state in STATES:

        if state in labels:
            return state

    return None

def call_llm(prompt):

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROK_API_KEY}",
            "HTTP-Referer": f"https://github.com/{REPO_NAME}",
            "X-Title": "Calculator Agent",
            "Content-Type": "application/json"
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


def get_issue_comments():

    response = requests.get(
        f"https://api.github.com/repos/{REPO_NAME}/issues/{ISSUE_NUMBER}/comments",
        headers=get_headers(),
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def build_comments_context():

    comments = get_issue_comments()

    context = ""

    for comment in comments:

        author = comment["user"]["login"]
        body = comment["body"]

        context += f"""

=== COMMENTAIRE DE {author} ===

{body}
"""

    return context


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

    print(f"=== ADD LABEL {label_name} ===")
    print(response.status_code)


def remove_label(label_name):

    response = requests.delete(
        f"https://api.github.com/repos/"
        f"{REPO_NAME}/issues/"
        f"{ISSUE_NUMBER}/labels/"
        f"{label_name}",
        headers=get_headers()
    )

    print(f"=== REMOVE LABEL {label_name} ===")
    print(response.status_code)


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

def publish_comment(body):

    response = requests.post(
        f"https://api.github.com/repos/{REPO_NAME}/issues/{ISSUE_NUMBER}/comments",
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

Voici l'arborescence du dépôt.

=== ARBORESCENCE ===

{repository_tree}

=== ISSUE ===

Titre :
{ISSUE_TITLE}

Description :
{ISSUE_BODY}

Quels fichiers semblent pertinents ?

Réponds UNIQUEMENT avec un JSON.

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

    comments_context = build_comments_context()

    analysis_prompt = f"""
Tu es un ingénieur logiciel senior.

Tu participes à une discussion GitHub.

Tu dois prendre en compte :

- l'issue initiale
- le code
- tous les commentaires
- toutes les analyses précédentes
- les remarques humaines

Si une solution a été critiquée,
tu dois adapter ta proposition.

La dernière proposition prévaut
sur les précédentes.

Tu ne dois jamais prétendre avoir exécuté
l'application.

=== ISSUE ===

Titre :
{ISSUE_TITLE}

Description :
{ISSUE_BODY}

=== HISTORIQUE ===

{comments_context}

=== CODE ===

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

    set_state(
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

    current_state = get_current_state()

    if current_state != "agent:waiting-approval":

        publish_comment(
            f"""⚠️ Commande `/approve` ignorée.

État actuel :

`{current_state}`

L'approbation n'est possible que depuis :

`agent:waiting-approval`
"""
        )

        return

    try:

        #
        # Analyse validée
        #

        analysis = get_latest_agent_analysis()

        if not analysis:

            publish_comment(
                "❌ Impossible de trouver une analyse à implémenter."
            )

            return

        #
        # Branche
        #

        branch_name = create_branch()

        checkout_branch(
            branch_name
        )

        set_state(
            "agent:implementing"
        )

        #
        # Code source
        #

        selected_files = select_files()

        code_context = load_files(
            selected_files
        )

        #
        # Génération
        #

        changes = generate_implementation(
            analysis,
            code_context
        )

        #
        # Ecriture des fichiers
        #

        apply_changes(
            changes
        )

        #
        # Commit
        #

        commit_changes()

        #
        # Push
        #

        push_branch(
            branch_name
        )

        #
        # Pull Request
        #

        pr = create_pull_request(
            branch_name
        )
        assign_pull_request(
            pr["number"]
        )
        pr_url = pr["html_url"]
        set_state(
            "agent:waiting-review"
        )

        publish_comment(
            f"""✅ Implémentation terminée.

Branche :

`{branch_name}`

Pull Request :

{pr_url}

État actuel :

`agent:waiting-review`
"""
        )

    except Exception as ex:

        publish_comment(
            f"""❌ Échec de l'implémentation.

Erreur :

```text
{str(ex)}
""")
        raise

def create_branch():

    headers = get_headers()

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


def get_latest_agent_analysis():

    comments = get_issue_comments()

    for comment in reversed(comments):

        body = comment["body"]

        if "## 🤖 Analyse automatique" in body:
            return body

    return None


def checkout_branch(branch_name):

    subprocess.run(
        ["git", "checkout", "-B", branch_name],
        check=True
    )

    print(f"=== CHECKOUT {branch_name} ===")


def generate_implementation(
    analysis,
    code_context
):

    prompt = f"""
Tu es un développeur senior.

Implémente la dernière solution validée.

Réponds UNIQUEMENT avec du JSON.

Format :

{{
  "files": [
    {{
      "path": "style.css",
      "content": "contenu complet"
    }}
  ]
}}

=== ANALYSE VALIDEE ===

{analysis}

=== CODE ===

{code_context}
"""

    response = call_llm(prompt)

    try:
        print("=== GENERATED IMPLEMENTATION RAW ===")
        print(response)
        return json.loads(response)
    except Exception as ex:
        print("=== JSON ERROR ===")
        print(ex)
        print("=== INVALID JSON ===")
        print(response)
        raise

def apply_changes(changes):

    files = changes.get("files", [])

    for file in files:

        path = file["path"]
        validate_path(path)
        content = file["content"]

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(content)

        print(f"=== WRITE {path} ===")


def commit_changes():

    import subprocess

    subprocess.run(
        [
            "git",
            "config",
            "user.name",
            "calculator-agent"
        ],
        check=True
    )

    subprocess.run(
        [
            "git",
            "config",
            "user.email",
            "agent@github.local"
        ],
        check=True
    )

    subprocess.run(
        ["git", "add", "."],
        check=True
    )

    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"Agent implementation for issue #{ISSUE_NUMBER}"
        ],
        check=True
    )


def push_branch(branch_name):

    import subprocess

    subprocess.run(
        [
            "git",
            "push",
            "--set-upstream",
            "origin",
            branch_name
        ],
        capture_output=True,
        check=True
    )
    print("=== PUSH STDOUT ===")
    print(result.stdout)
    print("=== PUSH STDERR ===")
    print(result.stderr)
    result.check_returncode()

def create_pull_request(branch_name):

    response = requests.post(
        f"https://api.github.com/repos/{REPO_NAME}/pulls",
        headers=get_headers(),
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
        headers=get_headers(),
        json={
            "assignees": [
                "frlnrd"
            ]
        }
    )
    response.raise_for_status()

def main():

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


if __name__ == "__main__":
    main()