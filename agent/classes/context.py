from dataclasses import dataclass


@dataclass
class AgentContext:

    repo_name: str

    issue_number: str
    issue_title: str
    issue_body: str

    github_token: str
    grok_api_key: str

    review_state: str = ""
    review_body: str = ""

    target_type: str = "issue"
    target_id: str = ""
