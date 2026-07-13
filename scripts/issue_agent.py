import os
import requests

GROK_API_KEY = os.environ["GROK_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

ISSUE_TITLE = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY = os.environ.get("ISSUE_BODY", "")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")

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

## Plan d'action
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
        "model": "openai/gpt-oss-120b",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    },
    timeout=60
)

print("=== OPENROUTER STATUS ===")
print(response.status_code)

print("=== OPENROUTER RESPONSE ===")
print(response.text)

response.raise_for_status()

analysis = response.json()["choices"][0]["message"]["content"]

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
        "body": f"## 🤖 Analyse automatique\n\n{analysis}"
    }
)

print("=== GITHUB STATUS ===")
print(github_response.status_code)

print("=== GITHUB RESPONSE ===")
print(github_response.text)

github_response.raise_for_status()

print("✅ Commentaire publié avec succès.")