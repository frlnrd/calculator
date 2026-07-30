from dataclasses import dataclass


@dataclass
class ChangeContext:

    path: str

    file_content: str

    repo_name: str

    grok_api_key: str

    change_planning: str
    
    change_id: int

    change_description: str

    total: int