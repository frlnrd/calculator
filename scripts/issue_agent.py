import os
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

prompt = f"""
Tu es un ingénieur logiciel senior.

Analyse cette issue GitHub.

Avant de proposer un correctif :

- détermine si les informations fournies permettent de reproduire le problème
- si ce n'est pas le cas, indique les informations manquantes
- ne prétends jamais avoir exécuté l'application ou reproduit le bug

Titre :
{ISSUE_TITLE}

Description :
{ISSUE_BODY}

Réponds avec :

## Reproductibilité

## Analyse

## Cause probable

## Correctif proposé

## Complexité

## Plan d'action
"""

prompt += f"""

Titre :
{ISSUE_TITLE}

Description :
{ISSUE_BODY}
"""

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

print("=== MODEL ===")
print(MODEL)

print("=== GROQ STATUS ===")
print(response.status_code)

print("=== GROQ RESPONSE ===")
print(response.text)

if response.status_code != 200:
    raise Exception(
        f"Erreur Groq {response.status_code}: {response.text}"
    )

data = response.json()

analysis = (
    data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "Aucune analyse générée.")
)

print("=== ANALYSIS ===")
print(analysis)

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
        "body": f"""## 🤖 Analyse automatique

Modèle utilisé : `{MODEL}`

{analysis}
"""
    },
    timeout=30
)

print("=== GITHUB STATUS ===")
print(github_response.status_code)

print("=== GITHUB RESPONSE ===")
print(github_response.text)

github_response.raise_for_status()

print("✅ Commentaire publié avec succès.")