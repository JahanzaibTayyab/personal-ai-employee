"""Sensitive data redaction utilities for audit logging."""

import re

REDACTED = "[REDACTED]"

# Patterns for sensitive data detection
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("api_key", re.compile(r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{16,})['\"]?")),
    ("bearer_token", re.compile(r"(?i)(bearer)\s+([a-zA-Z0-9_\-\.]{20,})")),
    ("password", re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?(\S+)['\"]?")),
    ("secret", re.compile(r"(?i)(secret|token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{16,})['\"]?")),
    ("email_body", re.compile(r"(?i)(email[_-]?body|message[_-]?body)\s*[:=]\s*['\"](.+?)['\"]")),
    ("credit_card", re.compile(r"\b(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})\b")),
    ("ssn", re.compile(r"\b(\d{3}-\d{2}-\d{4})\b")),
    ("oauth_token", re.compile(r"(?i)(oauth[_-]?token|access[_-]?token)\s*[:=]\s*['\"]?(\S{20,})['\"]?")),
]

# Keys that should always be redacted in dictionaries
_SENSITIVE_KEYS = frozenset({
    "password", "passwd", "pwd",
    "secret", "api_key", "apikey", "api_secret",
    "token", "access_token", "refresh_token", "bearer_token",
    "oauth_token", "oauth_secret",
    "credentials", "credential",
    "private_key", "private_key_id",
    "client_secret",
    "authorization",
})


def redact_string(text: str) -> str:
    """Redact sensitive patterns from a string.

    Args:
        text: Input text potentially containing sensitive data

    Returns:
        Text with sensitive patterns replaced by [REDACTED]
    """
    result = text
    for _name, pattern in _PATTERNS:
        result = pattern.sub(
            lambda m: m.group(0).replace(m.group(m.lastindex or 1), REDACTED),
            result,
        )
    return result


def redact_dict(data: dict[str, object], depth: int = 0, max_depth: int = 10) -> dict[str, object]:
    """Redact sensitive values from a dictionary recursively.

    Args:
        data: Dictionary to redact
        depth: Current recursion depth
        max_depth: Maximum recursion depth to prevent infinite loops

    Returns:
        New dictionary with sensitive values redacted
    """
    if depth >= max_depth:
        return data

    result: dict[str, object] = {}
    for key, value in data.items():
        lower_key = key.lower().replace("-", "_")

        if lower_key in _SENSITIVE_KEYS:
            result[key] = REDACTED
        elif isinstance(value, str):
            result[key] = redact_string(value)
        elif isinstance(value, dict):
            result[key] = redact_dict(value, depth + 1, max_depth)
        elif isinstance(value, list):
            result[key] = [
                redact_dict(item, depth + 1, max_depth) if isinstance(item, dict)
                else redact_string(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value

    return result


def is_sensitive_key(key: str) -> bool:
    """Check if a dictionary key represents sensitive data.

    Args:
        key: Dictionary key to check

    Returns:
        True if the key likely contains sensitive data
    """
    return key.lower().replace("-", "_") in _SENSITIVE_KEYS
