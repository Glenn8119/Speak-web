"""
JSON utility functions.
"""


def strip_markdown_code_blocks(content: str) -> str:
    """
    Strip markdown code block wrappers from a string.

    LLMs sometimes wrap JSON responses in markdown code blocks like:
    ```json
    {"key": "value"}
    ```

    This function removes those wrappers to get clean JSON.

    Args:
        content: The string potentially wrapped in markdown code blocks

    Returns:
        The string with code block markers removed
    """
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()
