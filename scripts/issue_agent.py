import os
import requests
from mistralai import Mistral

MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]

ISSUE_TITLE = os.environ["ISSUE_TITLE"]
ISSUE_BODY = os.environ["ISSUE_BODY"]

ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
REPO_NAME = os.environ["REPO_NAME"]

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

client = Mistral(api_key=MISTRAL_API_KEY)

prompt = f"""
Tu es un développeur senior.

Analyse le ticket suivant.

Titre :
{ISSUE_TITLE}

Description :
{ISSUE_BODY}

Donne :

- Résumé du problème
- Cause probable
- Solution proposée
- Difficulté (Faible/Moyenne/Forte)
"""

response = client.chat.complete(
    model="mistral-small-latest",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

analysis = response.choices[0].message.content

comment_url = f"https://api.github.com/repos/{REPO_NAME}/issues/{ISSUE_NUMBER}/comments"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

payload = {
    "body": f"## 🤖 Analyse automatique\n\n{analysis}"
}

response = requests.post(
    comment_url,
    headers=headers,
    json=payload
)

print(response.status_code)
print("Commentaire publié.")