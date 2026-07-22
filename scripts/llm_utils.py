import requests

from config import GROK_API_KEY, REPO_NAME

MODEL = "openai/gpt-oss-120b"

def call_llm(prompt, grok_api_key, repo_name):

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {grok_api_key}",
            "HTTP-Referer": f"https://github.com/{repo_name}",
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

