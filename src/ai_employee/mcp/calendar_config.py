"""Calendar MCP configuration.

Google Calendar integration for creating and managing events.
Matches the PDF's calendar-mcp server recommendation.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class CalendarConfigError(Exception):
    """Raised when Calendar MCP configuration is invalid."""


@dataclass(frozen=True)
class CalendarMCPConfig:
    """Configuration for Calendar MCP integration.

    Attributes:
        credentials_path: Path to Google OAuth credentials file
        token_path: Path to stored OAuth token
        calendar_id: Default calendar ID (default: primary)
        scopes: OAuth scopes for Calendar API
    """

    credentials_path: str = ""
    token_path: str = ""
    calendar_id: str = "primary"
    scopes: tuple[str, ...] = (
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
    )

    def validate(self) -> bool:
        """Validate that required fields are present.

        Returns:
            True if valid

        Raises:
            CalendarConfigError: If configuration is invalid
        """
        if not self.credentials_path:
            raise CalendarConfigError("CALENDAR_CREDENTIALS_PATH is required")
        if not Path(self.credentials_path).exists():
            raise CalendarConfigError(
                f"Credentials file not found: {self.credentials_path}"
            )
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (redacting sensitive fields)."""
        return {
            "credentials_path": self.credentials_path,
            "token_path": self.token_path,
            "calendar_id": self.calendar_id,
        }

    def to_mcp_server_config(self) -> dict[str, Any]:
        """Generate MCP server JSON config for .claude/mcp.json."""
        return {
            "name": "calendar",
            "command": "node",
            "args": ["/path/to/calendar-mcp/index.js"],
            "env": {
                "GOOGLE_CREDENTIALS": self.credentials_path,
                "CALENDAR_ID": self.calendar_id,
            },
        }

    @classmethod
    def from_env(cls) -> "CalendarMCPConfig":
        """Create config from environment variables.

        Environment variables:
            CALENDAR_CREDENTIALS_PATH: Path to OAuth credentials
            CALENDAR_TOKEN_PATH: Path to stored token
            CALENDAR_ID: Default calendar ID (default: primary)

        Returns:
            CalendarMCPConfig instance
        """
        credentials_path = os.environ.get("CALENDAR_CREDENTIALS_PATH", "")
        token_path = os.environ.get("CALENDAR_TOKEN_PATH", "")
        calendar_id = os.environ.get("CALENDAR_ID", "primary")

        return cls(
            credentials_path=credentials_path,
            token_path=token_path,
            calendar_id=calendar_id,
        )
