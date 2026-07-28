from dataclasses import dataclass


@dataclass
class ChangeContext:

    path: str

    file_content: str

    change_description: str

    repo_name: str

    grok_api_key: str

    end_marker: str = (
        "<<<END_OF_RESPONSE>>>"
    )

    max_lines_per_response: int = 300