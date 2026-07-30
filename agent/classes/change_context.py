from dataclasses import dataclass


@dataclass
class ChangeContext:

    repo_name: str

    grok_api_key: str

    path: str

    change_id: int

    change_description: str

    content: str

    total: int