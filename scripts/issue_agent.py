import os
import requests

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

ISSUE_TITLE = os.environ["ISSUE_TITLE"]
ISSUE_BODY = os.environ["ISSUE_BODY"]
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
REPO_NAME = os.environ["REPO_NAME"]

prompt = f"""
Tu es un développeur senior.

Analyse le ticket GitHub suivant.

Titre :
{ISSUE_TITLE}

Description :
{ISSUE_BODY}

Fournis :

## Résumé
## Cause probable
## Solution proposée
## Niveau de difficulté
"""

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "mistralai/mistral-small-3.2-24b-instruct:free",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
)

response.raise_for_status()

analysis = response.json()["choices"][0]["message"]["content"]

comment_url = f"https://api.github.com/repos/{REPO_NAME}/issues/{ISSUE_NUMBER}/comments"

github_response = requests.post(
    comment_url,
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    },
    json={
        "body": f"## 🤖 Analyse automatique\n\n{analysis}"
    }
)

github_response.raise_for_status()

print("Commentaire publié avec succès.")