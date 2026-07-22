import os


EVENT_NAME = os.environ.get("EVENT_NAME", "")
COMMENT_BODY = os.environ.get("COMMENT_BODY", "")
GROK_API_KEY = os.environ["GROK_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
ISSUE_TITLE = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY = os.environ.get("ISSUE_BODY", "")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")
REVIEW_STATE = os.environ.get(
    "REVIEW_STATE",
    ""
)
REVIEW_BODY = os.environ.get(
    "REVIEW_BODY",
    ""
)
PR_NUMBER = os.environ.get(
    "PR_NUMBER",
    ""
)
