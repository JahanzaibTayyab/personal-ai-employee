"""Browser MCP configuration.

Playwright-based browser automation for payment portals and form filling.
Matches the PDF's browser-mcp server recommendation.
"""

import os
from dataclasses import dataclass
from typing import Any


class BrowserConfigError(Exception):
    """Raised when Browser MCP configuration is invalid."""


@dataclass(frozen=True)
class BrowserMCPConfig:
    """Configuration for Browser MCP integration.

    Attributes:
        headless: Run browser in headless mode
        timeout: Page load timeout in seconds
        user_data_dir: Path to persistent browser profile
        allowed_domains: Domains the browser is allowed to navigate to
    """

    headless: bool = True
    timeout: int = 30
    user_data_dir: str = ""
    allowed_domains: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MCP server config."""
        return {
            "headless": self.headless,
            "timeout": self.timeout,
            "user_data_dir": self.user_data_dir,
            "allowed_domains": list(self.allowed_domains),
        }

    def to_mcp_server_config(self) -> dict[str, Any]:
        """Generate MCP server JSON config for .claude/mcp.json."""
        env: dict[str, str] = {}
        if self.headless:
            env["HEADLESS"] = "true"
        if self.user_data_dir:
            env["USER_DATA_DIR"] = self.user_data_dir

        return {
            "name": "browser",
            "command": "npx",
            "args": ["@anthropic/browser-mcp"],
            "env": env,
        }

    @classmethod
    def from_env(cls) -> "BrowserMCPConfig":
        """Create config from environment variables.

        Environment variables:
            BROWSER_HEADLESS: Run headless (default: true)
            BROWSER_TIMEOUT: Page load timeout (default: 30)
            BROWSER_USER_DATA_DIR: Persistent profile path
            BROWSER_ALLOWED_DOMAINS: Comma-separated allowed domains

        Returns:
            BrowserMCPConfig instance
        """
        headless = os.environ.get("BROWSER_HEADLESS", "true").lower() == "true"
        timeout = int(os.environ.get("BROWSER_TIMEOUT", "30"))
        user_data_dir = os.environ.get("BROWSER_USER_DATA_DIR", "")
        domains_str = os.environ.get("BROWSER_ALLOWED_DOMAINS", "")
        allowed_domains = tuple(
            d.strip() for d in domains_str.split(",") if d.strip()
        )

        return cls(
            headless=headless,
            timeout=timeout,
            user_data_dir=user_data_dir,
            allowed_domains=allowed_domains,
        )
