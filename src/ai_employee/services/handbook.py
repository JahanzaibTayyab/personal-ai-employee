"""Handbook Parser service - extracts and applies rules from Company_Handbook.md."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from ai_employee.models.action_item import Priority

# Default priority keywords used across the application
DEFAULT_PRIORITY_KEYWORDS: dict[str, Priority] = {
    # Urgent keywords
    "urgent": Priority.URGENT,
    "asap": Priority.URGENT,
    "emergency": Priority.URGENT,
    "critical": Priority.URGENT,
    "immediately": Priority.URGENT,
    # High priority keywords
    "important": Priority.HIGH,
    "priority": Priority.HIGH,
    "action required": Priority.HIGH,
    "please respond": Priority.HIGH,
}


def detect_priority_from_text(
    text: str,
    additional_keywords: dict[str, Priority] | None = None,
) -> Priority:
    """Detect priority from text based on keywords.

    This is a standalone utility that can be used without a handbook file.

    Args:
        text: Text to analyze (filename, content, subject, etc.)
        additional_keywords: Optional extra keywords to check

    Returns:
        Detected priority (defaults to NORMAL)
    """
    text_lower = text.lower()
    keywords = dict(DEFAULT_PRIORITY_KEYWORDS)

    if additional_keywords:
        keywords.update(additional_keywords)

    # Check for urgent first, then high, then default to normal
    for keyword, priority in keywords.items():
        if keyword in text_lower:
            if priority == Priority.URGENT:
                return Priority.URGENT

    for keyword, priority in keywords.items():
        if keyword in text_lower:
            if priority == Priority.HIGH:
                return Priority.HIGH

    return Priority.NORMAL


@dataclass
class HandbookRule:
    """A rule extracted from the Company Handbook."""

    number: int
    title: str
    content: str
    priority_keywords: dict[str, Priority] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"Rule {self.number}: {self.title}"


class HandbookParser:
    """Service for parsing and applying rules from Company_Handbook.md."""

    def __init__(self, handbook_path: Path):
        """Initialize the handbook parser.

        Args:
            handbook_path: Path to Company_Handbook.md
        """
        self.handbook_path = handbook_path
        self._rules: list[HandbookRule] | None = None
        self._priority_keywords: dict[str, Priority] | None = None

    def parse(self) -> list[HandbookRule]:
        """Parse rules from the handbook.

        Returns:
            List of parsed rules
        """
        if not self.handbook_path.exists():
            return []

        content = self.handbook_path.read_text()
        rules = []

        # Pattern to match ### Rule N: Title
        rule_pattern = r"### Rule (\d+):?\s*(.+?)(?=\n)"
        matches = list(re.finditer(rule_pattern, content))

        for i, match in enumerate(matches):
            rule_num = int(match.group(1))
            rule_title = match.group(2).strip()

            # Get content until next rule or section
            start_pos = match.end()
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                # Find next ## section or end of file
                next_section = re.search(r"\n## ", content[start_pos:])
                if next_section:
                    end_pos = start_pos + next_section.start()
                else:
                    end_pos = len(content)

            rule_content = content[start_pos:end_pos].strip()

            # Extract priority keywords from rule content
            priority_keywords = self._extract_priority_keywords(rule_content)

            rules.append(HandbookRule(
                number=rule_num,
                title=rule_title,
                content=rule_content,
                priority_keywords=priority_keywords,
            ))

        self._rules = rules
        return rules

    def _extract_priority_keywords(self, content: str) -> dict[str, Priority]:
        """Extract priority keyword mappings from rule content.

        Args:
            content: Rule content text

        Returns:
            Dictionary of keyword -> Priority mappings
        """
        keywords: dict[str, Priority] = {}

        # Look for patterns like: "keyword" → priority: level
        # Or: - "keyword", "keyword2" → priority: urgent
        lines = content.lower().split("\n")

        for line in lines:
            if "→" in line or "->" in line:
                # Split on arrow
                parts = re.split(r"→|->", line)
                if len(parts) == 2:
                    keyword_part = parts[0]
                    priority_part = parts[1].strip()

                    # Extract keywords (quoted strings)
                    found_keywords = re.findall(r'"([^"]+)"', keyword_part)

                    # Determine priority
                    if "urgent" in priority_part:
                        priority = Priority.URGENT
                    elif "high" in priority_part:
                        priority = Priority.HIGH
                    elif "low" in priority_part:
                        priority = Priority.LOW
                    else:
                        priority = Priority.NORMAL

                    for kw in found_keywords:
                        keywords[kw.lower()] = priority

        return keywords

    def get_rules(self) -> list[HandbookRule]:
        """Get parsed rules, parsing if necessary.

        Returns:
            List of parsed rules
        """
        if self._rules is None:
            self.parse()
        return self._rules or []

    def get_priority_keywords(self) -> dict[str, Priority]:
        """Get all priority keywords from all rules.

        Returns:
            Combined dictionary of keyword -> Priority mappings
        """
        if self._priority_keywords is not None:
            return self._priority_keywords

        keywords = dict(DEFAULT_PRIORITY_KEYWORDS)

        for rule in self.get_rules():
            keywords.update(rule.priority_keywords)

        self._priority_keywords = keywords
        return keywords

    def detect_priority(self, text: str) -> Priority:
        """Detect priority from text based on keywords.

        Args:
            text: Text to analyze (filename, content, subject)

        Returns:
            Detected priority (defaults to NORMAL)
        """
        text_lower = text.lower()
        keywords = self.get_priority_keywords()

        # Check for urgent first, then high, then default to normal
        for keyword, priority in keywords.items():
            if keyword in text_lower:
                if priority == Priority.URGENT:
                    return Priority.URGENT

        for keyword, priority in keywords.items():
            if keyword in text_lower:
                if priority == Priority.HIGH:
                    return Priority.HIGH

        return Priority.NORMAL

    def find_applicable_rules(self, text: str) -> list[HandbookRule]:
        """Find rules that may apply to given text.

        Args:
            text: Text to check against rules

        Returns:
            List of potentially applicable rules
        """
        text_lower = text.lower()
        applicable = []

        for rule in self.get_rules():
            # Check if any keywords from this rule match
            for keyword in rule.priority_keywords:
                if keyword in text_lower:
                    applicable.append(rule)
                    break

        return applicable

    def get_first_applicable_rule(self, text: str) -> HandbookRule | None:
        """Get the first (highest priority) applicable rule.

        Rules are ordered by their number, so Rule 1 takes precedence over Rule 2.

        Args:
            text: Text to check against rules

        Returns:
            First applicable rule or None
        """
        applicable = self.find_applicable_rules(text)
        if applicable:
            return min(applicable, key=lambda r: r.number)
        return None

    def reload(self) -> None:
        """Reload rules from the handbook file."""
        self._rules = None
        self._priority_keywords = None
        self.parse()
