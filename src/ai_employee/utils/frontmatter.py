"""YAML frontmatter parser utility."""

from typing import Any

import yaml


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        Tuple of (frontmatter dict, remaining content)
    """
    if not content.startswith("---"):
        return {}, content

    lines = content.split("\n")
    end_index = -1

    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = i
            break

    if end_index == -1:
        return {}, content

    frontmatter_text = "\n".join(lines[1:end_index])
    remaining_content = "\n".join(lines[end_index + 1 :]).strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        return {}, content

    return frontmatter, remaining_content


def generate_frontmatter(data: dict[str, Any], content: str = "") -> str:
    """Generate markdown content with YAML frontmatter.

    Args:
        data: Dictionary to convert to YAML frontmatter
        content: Optional markdown content after frontmatter

    Returns:
        Complete markdown string with frontmatter
    """
    frontmatter_text = yaml.dump(data, default_flow_style=False, sort_keys=False)
    result = f"---\n{frontmatter_text}---\n"

    if content:
        result += f"\n{content}"

    return result


def update_frontmatter(
    original_content: str, updates: dict[str, Any]
) -> str:
    """Update frontmatter in existing markdown content.

    Args:
        original_content: Original markdown content with frontmatter
        updates: Dictionary of fields to update

    Returns:
        Updated markdown content
    """
    frontmatter, body = parse_frontmatter(original_content)
    frontmatter.update(updates)
    return generate_frontmatter(frontmatter, body)
