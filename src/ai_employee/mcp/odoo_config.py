"""Odoo MCP configuration.

Manages connection configuration for the Odoo ERP integration,
loading credentials from environment variables or configuration files.
"""

import os
from dataclasses import dataclass
from typing import Any


class OdooConfigError(Exception):
    """Raised when Odoo configuration is invalid or missing."""


@dataclass(frozen=True)
class OdooMCPConfig:
    """Configuration for Odoo MCP integration.

    Attributes:
        url: Odoo server URL
        database: Database name
        username: Login username
        api_key: API key for authentication
        timeout: Connection timeout in seconds
    """

    url: str
    database: str
    username: str
    api_key: str
    timeout: int = 30

    def validate(self) -> bool:
        """Validate that all required fields are present.

        Returns:
            True if valid

        Raises:
            OdooConfigError: If configuration is invalid
        """
        if not self.url:
            raise OdooConfigError("ODOO_URL is required")
        if not self.database:
            raise OdooConfigError("ODOO_DATABASE is required")
        if not self.username:
            raise OdooConfigError("ODOO_USERNAME is required")
        if not self.api_key:
            raise OdooConfigError("ODOO_API_KEY is required")
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (redacting sensitive fields).

        Returns:
            Config dict with redacted api_key
        """
        return {
            "url": self.url,
            "database": self.database,
            "username": self.username,
            "api_key": "***REDACTED***",
            "timeout": self.timeout,
        }

    @classmethod
    def from_env(cls) -> "OdooMCPConfig":
        """Create config from environment variables.

        Environment variables:
            ODOO_URL: Server URL (e.g., http://localhost:8069)
            ODOO_DATABASE: Database name
            ODOO_USERNAME: Login username
            ODOO_API_KEY: API key for authentication
            ODOO_TIMEOUT: Connection timeout in seconds (optional)

        Returns:
            OdooMCPConfig instance

        Raises:
            OdooConfigError: If required env vars are missing
        """
        url = os.environ.get("ODOO_URL", "")
        database = os.environ.get("ODOO_DATABASE", "")
        username = os.environ.get("ODOO_USERNAME", "")
        api_key = os.environ.get("ODOO_API_KEY", "")
        timeout = int(os.environ.get("ODOO_TIMEOUT", "30"))

        config = cls(
            url=url,
            database=database,
            username=username,
            api_key=api_key,
            timeout=timeout,
        )

        config.validate()
        return config

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OdooMCPConfig":
        """Create config from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            OdooMCPConfig instance
        """
        return cls(
            url=data.get("url", ""),
            database=data.get("database", ""),
            username=data.get("username", ""),
            api_key=data.get("api_key", ""),
            timeout=data.get("timeout", 30),
        )
