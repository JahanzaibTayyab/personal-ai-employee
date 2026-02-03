"""Gmail MCP configuration and client.

Handles OAuth 2.0 credentials, token refresh, and MCP client initialization
for google_workspace_mcp integration.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class GmailMCPError(Exception):
    """Base exception for Gmail MCP errors."""

    pass


class TokenRefreshError(GmailMCPError):
    """OAuth token refresh failed."""

    pass


class CredentialsNotFoundError(GmailMCPError):
    """OAuth credentials file not found."""

    pass


class InvalidCredentialsError(GmailMCPError):
    """OAuth credentials are invalid or malformed."""

    pass


@dataclass
class OAuthToken:
    """OAuth 2.0 token data.

    Attributes:
        access_token: Current access token
        refresh_token: Token for refreshing access
        expires_at: When access token expires
        token_type: Usually "Bearer"
        scope: OAuth scopes granted
    """

    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "Bearer"
    scope: str = ""

    def is_expired(self, buffer_minutes: int = 5) -> bool:
        """Check if token is expired or about to expire.

        Args:
            buffer_minutes: Minutes before expiry to consider expired

        Returns:
            True if token is expired or will expire soon
        """
        buffer = timedelta(minutes=buffer_minutes)
        return datetime.now() >= (self.expires_at - buffer)

    def to_dict(self) -> dict[str, Any]:
        """Convert token to dictionary for storage."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat(),
            "token_type": self.token_type,
            "scope": self.scope,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OAuthToken":
        """Create token from dictionary."""
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            token_type=data.get("token_type", "Bearer"),
            scope=data.get("scope", ""),
        )


@dataclass
class GmailMCPConfig:
    """Configuration for Gmail MCP integration.

    Attributes:
        credentials_path: Path to OAuth credentials JSON file
        token_path: Path to store/load OAuth tokens
        scopes: Gmail API scopes to request
        client_id: OAuth client ID (loaded from credentials)
        client_secret: OAuth client secret (loaded from credentials)
    """

    credentials_path: Path
    token_path: Path | None = None
    scopes: list[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.modify",
    ])
    client_id: str = ""
    client_secret: str = ""
    _token: OAuthToken | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Load credentials from file."""
        if self.token_path is None:
            self.token_path = self.credentials_path.parent / "gmail_token.json"

        if self.credentials_path.exists():
            self._load_credentials()

    def _load_credentials(self) -> None:
        """Load OAuth credentials from file.

        Raises:
            CredentialsNotFoundError: If credentials file not found
            InvalidCredentialsError: If credentials file is malformed
        """
        if not self.credentials_path.exists():
            raise CredentialsNotFoundError(
                f"Credentials file not found: {self.credentials_path}"
            )

        try:
            content = self.credentials_path.read_text()
            data = json.loads(content)

            # Handle both "installed" and "web" credential types
            if "installed" in data:
                creds = data["installed"]
            elif "web" in data:
                creds = data["web"]
            else:
                creds = data

            self.client_id = creds.get("client_id", "")
            self.client_secret = creds.get("client_secret", "")

            if not self.client_id or not self.client_secret:
                raise InvalidCredentialsError(
                    "Credentials file missing client_id or client_secret"
                )

        except json.JSONDecodeError as e:
            raise InvalidCredentialsError(
                f"Invalid JSON in credentials file: {e}"
            ) from e

    def load_token(self) -> OAuthToken | None:
        """Load OAuth token from token file.

        Returns:
            OAuthToken if found and valid, None otherwise
        """
        if self.token_path is None or not self.token_path.exists():
            return None

        try:
            content = self.token_path.read_text()
            data = json.loads(content)
            self._token = OAuthToken.from_dict(data)
            return self._token
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def save_token(self, token: OAuthToken) -> None:
        """Save OAuth token to token file.

        Args:
            token: Token to save
        """
        if self.token_path is None:
            return

        self._token = token
        self.token_path.write_text(json.dumps(token.to_dict(), indent=2))

    def get_token(self) -> OAuthToken | None:
        """Get current token, loading from file if needed.

        Returns:
            Current OAuth token or None
        """
        if self._token is None:
            self._token = self.load_token()
        return self._token

    def has_valid_token(self) -> bool:
        """Check if we have a valid, non-expired token.

        Returns:
            True if valid token exists
        """
        token = self.get_token()
        return token is not None and not token.is_expired()

    @classmethod
    def from_env(cls) -> "GmailMCPConfig":
        """Create config from environment variables.

        Environment variables:
            GMAIL_CREDENTIALS_PATH: Path to credentials file
            GMAIL_TOKEN_PATH: Path to token file (optional)

        Returns:
            GmailMCPConfig instance
        """
        credentials_path = os.environ.get("GMAIL_CREDENTIALS_PATH", "")
        token_path = os.environ.get("GMAIL_TOKEN_PATH")

        if not credentials_path:
            raise GmailMCPError(
                "GMAIL_CREDENTIALS_PATH environment variable not set"
            )

        return cls(
            credentials_path=Path(credentials_path),
            token_path=Path(token_path) if token_path else None,
        )


class GmailMCPClient:
    """Client for Gmail operations via google_workspace_mcp.

    Handles authentication, token refresh, and email operations.
    """

    def __init__(self, config: GmailMCPConfig):
        """Initialize Gmail MCP client.

        Args:
            config: Gmail MCP configuration
        """
        self.config = config
        self._authenticated = False

    def authenticate(self) -> bool:
        """Authenticate with Gmail API.

        If token exists and is valid, use it.
        If token is expired, attempt refresh.
        Otherwise, initiate new OAuth flow.

        Returns:
            True if authentication successful
        """
        token = self.config.get_token()

        if token is not None:
            if token.is_expired():
                try:
                    self._refresh_token(token)
                except TokenRefreshError:
                    # Need new authentication
                    return self._initiate_oauth_flow()
            self._authenticated = True
            return True

        return self._initiate_oauth_flow()

    def _refresh_token(self, token: OAuthToken) -> OAuthToken:
        """Refresh an expired OAuth token.

        Args:
            token: Expired token with valid refresh_token

        Returns:
            New OAuthToken with refreshed access_token

        Raises:
            TokenRefreshError: If refresh fails
        """
        # TODO: Implement actual token refresh via Google OAuth API
        # For now, raise error indicating refresh is needed
        raise TokenRefreshError(
            "Token refresh not implemented - please re-authenticate"
        )

    def _initiate_oauth_flow(self) -> bool:
        """Initiate OAuth 2.0 authorization flow.

        Returns:
            True if flow completed successfully
        """
        # TODO: Implement OAuth flow
        # This would typically open a browser for user authorization
        return False

    def is_authenticated(self) -> bool:
        """Check if client is authenticated.

        Returns:
            True if authenticated with valid token
        """
        return self._authenticated and self.config.has_valid_token()

    def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[str] | None = None,
    ) -> dict[str, Any]:
        """Send an email via Gmail MCP.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            attachments: Optional list of attachment file paths

        Returns:
            Dict with message_id and status

        Raises:
            GmailMCPError: If not authenticated or send fails
        """
        if not self.is_authenticated():
            raise GmailMCPError("Not authenticated - call authenticate() first")

        # TODO: Implement actual MCP call to google_workspace_mcp
        # For now, return mock success
        import uuid

        return {
            "success": True,
            "message_id": f"msg_{uuid.uuid4().hex[:12]}",
            "recipients": {
                "to": to,
                "cc": cc or [],
                "bcc": bcc or [],
            },
        }

    def create_draft(
        self,
        to: list[str],
        subject: str,
        body: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create an email draft in Gmail.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            attachments: Optional list of attachment file paths

        Returns:
            Dict with draft_id and status

        Raises:
            GmailMCPError: If not authenticated or draft creation fails
        """
        if not self.is_authenticated():
            raise GmailMCPError("Not authenticated - call authenticate() first")

        # TODO: Implement actual MCP call
        import uuid

        return {
            "success": True,
            "draft_id": f"draft_{uuid.uuid4().hex[:12]}",
        }
