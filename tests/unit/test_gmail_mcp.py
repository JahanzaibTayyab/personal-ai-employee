"""Unit tests for Gmail MCP configuration and client."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_employee.mcp.gmail_config import (
    CredentialsNotFoundError,
    GmailMCPClient,
    GmailMCPConfig,
    GmailMCPError,
    InvalidCredentialsError,
    OAuthToken,
    TokenRefreshError,
)


class TestOAuthToken:
    """Tests for OAuthToken dataclass."""

    def test_create_token(self) -> None:
        """Test creating an OAuth token."""
        expires_at = datetime.now() + timedelta(hours=1)
        token = OAuthToken(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=expires_at,
        )

        assert token.access_token == "test_access"
        assert token.refresh_token == "test_refresh"
        assert token.expires_at == expires_at
        assert token.token_type == "Bearer"

    def test_token_not_expired(self) -> None:
        """Test token is not expired when valid."""
        expires_at = datetime.now() + timedelta(hours=1)
        token = OAuthToken(
            access_token="test",
            refresh_token="test",
            expires_at=expires_at,
        )

        assert token.is_expired() is False

    def test_token_expired(self) -> None:
        """Test token is expired when past expiry."""
        expires_at = datetime.now() - timedelta(hours=1)
        token = OAuthToken(
            access_token="test",
            refresh_token="test",
            expires_at=expires_at,
        )

        assert token.is_expired() is True

    def test_token_expired_with_buffer(self) -> None:
        """Test token is considered expired within buffer."""
        # Token expires in 3 minutes, buffer is 5 minutes
        expires_at = datetime.now() + timedelta(minutes=3)
        token = OAuthToken(
            access_token="test",
            refresh_token="test",
            expires_at=expires_at,
        )

        assert token.is_expired(buffer_minutes=5) is True
        assert token.is_expired(buffer_minutes=1) is False

    def test_token_to_dict(self) -> None:
        """Test converting token to dictionary."""
        expires_at = datetime.now() + timedelta(hours=1)
        token = OAuthToken(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=expires_at,
            scope="gmail.send",
        )

        d = token.to_dict()

        assert d["access_token"] == "test_access"
        assert d["refresh_token"] == "test_refresh"
        assert d["token_type"] == "Bearer"
        assert d["scope"] == "gmail.send"

    def test_token_from_dict(self) -> None:
        """Test creating token from dictionary."""
        expires_at = datetime.now() + timedelta(hours=1)
        data = {
            "access_token": "test_access",
            "refresh_token": "test_refresh",
            "expires_at": expires_at.isoformat(),
            "token_type": "Bearer",
            "scope": "gmail.send",
        }

        token = OAuthToken.from_dict(data)

        assert token.access_token == "test_access"
        assert token.refresh_token == "test_refresh"
        assert token.scope == "gmail.send"


class TestGmailMCPConfig:
    """Tests for GmailMCPConfig."""

    @pytest.fixture
    def credentials_file(self, tmp_path: Path) -> Path:
        """Create a test credentials file."""
        creds = {
            "installed": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            }
        }
        creds_path = tmp_path / "credentials.json"
        creds_path.write_text(json.dumps(creds))
        return creds_path

    @pytest.fixture
    def web_credentials_file(self, tmp_path: Path) -> Path:
        """Create a web-type credentials file."""
        creds = {
            "web": {
                "client_id": "web_client_id",
                "client_secret": "web_client_secret",
            }
        }
        creds_path = tmp_path / "web_credentials.json"
        creds_path.write_text(json.dumps(creds))
        return creds_path

    def test_config_loads_credentials(self, credentials_file: Path) -> None:
        """Test config loads credentials from file."""
        config = GmailMCPConfig(credentials_path=credentials_file)

        assert config.client_id == "test_client_id"
        assert config.client_secret == "test_client_secret"

    def test_config_loads_web_credentials(self, web_credentials_file: Path) -> None:
        """Test config loads web-type credentials."""
        config = GmailMCPConfig(credentials_path=web_credentials_file)

        assert config.client_id == "web_client_id"
        assert config.client_secret == "web_client_secret"

    def test_config_default_scopes(self, credentials_file: Path) -> None:
        """Test config has default Gmail scopes."""
        config = GmailMCPConfig(credentials_path=credentials_file)

        assert "https://www.googleapis.com/auth/gmail.send" in config.scopes
        assert "https://www.googleapis.com/auth/gmail.compose" in config.scopes

    def test_config_custom_scopes(self, credentials_file: Path) -> None:
        """Test config with custom scopes."""
        custom_scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        config = GmailMCPConfig(
            credentials_path=credentials_file,
            scopes=custom_scopes,
        )

        assert config.scopes == custom_scopes

    def test_config_missing_credentials(self, tmp_path: Path) -> None:
        """Test config handles missing credentials file gracefully."""
        # Config doesn't raise on init if file doesn't exist
        # But credentials won't be loaded
        config = GmailMCPConfig(
            credentials_path=tmp_path / "nonexistent.json"
        )

        assert config.client_id == ""
        assert config.client_secret == ""

    def test_config_invalid_json(self, tmp_path: Path) -> None:
        """Test config handles invalid JSON."""
        creds_path = tmp_path / "invalid.json"
        creds_path.write_text("not valid json")

        with pytest.raises(InvalidCredentialsError):
            GmailMCPConfig(credentials_path=creds_path)

    def test_config_missing_fields(self, tmp_path: Path) -> None:
        """Test config handles missing required fields."""
        creds_path = tmp_path / "incomplete.json"
        creds_path.write_text(json.dumps({"installed": {}}))

        with pytest.raises(InvalidCredentialsError):
            GmailMCPConfig(credentials_path=creds_path)

    def test_config_default_token_path(self, credentials_file: Path) -> None:
        """Test config creates default token path."""
        config = GmailMCPConfig(credentials_path=credentials_file)

        expected = credentials_file.parent / "gmail_token.json"
        assert config.token_path == expected

    def test_config_custom_token_path(
        self, credentials_file: Path, tmp_path: Path
    ) -> None:
        """Test config with custom token path."""
        token_path = tmp_path / "custom_token.json"
        config = GmailMCPConfig(
            credentials_path=credentials_file,
            token_path=token_path,
        )

        assert config.token_path == token_path

    def test_save_and_load_token(
        self, credentials_file: Path, tmp_path: Path
    ) -> None:
        """Test saving and loading OAuth token."""
        token_path = tmp_path / "token.json"
        config = GmailMCPConfig(
            credentials_path=credentials_file,
            token_path=token_path,
        )

        expires_at = datetime.now() + timedelta(hours=1)
        token = OAuthToken(
            access_token="saved_access",
            refresh_token="saved_refresh",
            expires_at=expires_at,
        )

        config.save_token(token)
        loaded = config.load_token()

        assert loaded is not None
        assert loaded.access_token == "saved_access"
        assert loaded.refresh_token == "saved_refresh"

    def test_has_valid_token(self, credentials_file: Path, tmp_path: Path) -> None:
        """Test checking for valid token."""
        token_path = tmp_path / "token.json"
        config = GmailMCPConfig(
            credentials_path=credentials_file,
            token_path=token_path,
        )

        # No token initially
        assert config.has_valid_token() is False

        # Save valid token
        token = OAuthToken(
            access_token="valid",
            refresh_token="refresh",
            expires_at=datetime.now() + timedelta(hours=1),
        )
        config.save_token(token)

        assert config.has_valid_token() is True

    def test_has_expired_token(self, credentials_file: Path, tmp_path: Path) -> None:
        """Test detecting expired token."""
        token_path = tmp_path / "token.json"
        config = GmailMCPConfig(
            credentials_path=credentials_file,
            token_path=token_path,
        )

        # Save expired token
        token = OAuthToken(
            access_token="expired",
            refresh_token="refresh",
            expires_at=datetime.now() - timedelta(hours=1),
        )
        config.save_token(token)

        assert config.has_valid_token() is False

    def test_from_env(self, credentials_file: Path) -> None:
        """Test creating config from environment variables."""
        with patch.dict(
            "os.environ",
            {"GMAIL_CREDENTIALS_PATH": str(credentials_file)},
        ):
            config = GmailMCPConfig.from_env()

        assert config.client_id == "test_client_id"

    def test_from_env_missing_var(self) -> None:
        """Test error when env var not set."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(GmailMCPError):
                GmailMCPConfig.from_env()


class TestGmailMCPClient:
    """Tests for GmailMCPClient."""

    @pytest.fixture
    def config(self, tmp_path: Path) -> GmailMCPConfig:
        """Create a test config with credentials."""
        creds = {
            "installed": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            }
        }
        creds_path = tmp_path / "credentials.json"
        creds_path.write_text(json.dumps(creds))

        return GmailMCPConfig(
            credentials_path=creds_path,
            token_path=tmp_path / "token.json",
        )

    @pytest.fixture
    def authenticated_config(
        self, config: GmailMCPConfig, tmp_path: Path
    ) -> GmailMCPConfig:
        """Create config with valid token."""
        token = OAuthToken(
            access_token="valid_token",
            refresh_token="refresh_token",
            expires_at=datetime.now() + timedelta(hours=1),
        )
        config.save_token(token)
        return config

    def test_client_initialization(self, config: GmailMCPConfig) -> None:
        """Test client initializes correctly."""
        client = GmailMCPClient(config)

        assert client.config == config
        assert client.is_authenticated() is False

    def test_authenticate_with_valid_token(
        self, authenticated_config: GmailMCPConfig
    ) -> None:
        """Test authentication succeeds with valid token."""
        client = GmailMCPClient(authenticated_config)

        result = client.authenticate()

        assert result is True
        assert client.is_authenticated() is True

    def test_authenticate_with_expired_token(self, config: GmailMCPConfig) -> None:
        """Test authentication handles expired token."""
        # Save expired token
        token = OAuthToken(
            access_token="expired",
            refresh_token="refresh",
            expires_at=datetime.now() - timedelta(hours=1),
        )
        config.save_token(token)

        client = GmailMCPClient(config)

        # Should fail because refresh is not implemented
        result = client.authenticate()

        assert result is False

    def test_authenticate_without_token(self, config: GmailMCPConfig) -> None:
        """Test authentication without existing token."""
        client = GmailMCPClient(config)

        # Should fail because OAuth flow is not implemented
        result = client.authenticate()

        assert result is False

    def test_send_email_requires_auth(self, config: GmailMCPConfig) -> None:
        """Test send_email requires authentication."""
        client = GmailMCPClient(config)

        with pytest.raises(GmailMCPError, match="Not authenticated"):
            client.send_email(
                to=["test@example.com"],
                subject="Test",
                body="Test body",
            )

    def test_send_email_success(
        self, authenticated_config: GmailMCPConfig
    ) -> None:
        """Test successful email send."""
        client = GmailMCPClient(authenticated_config)
        client.authenticate()

        result = client.send_email(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test body content",
            cc=["cc@example.com"],
        )

        assert result["success"] is True
        assert "message_id" in result
        assert result["recipients"]["to"] == ["test@example.com"]
        assert result["recipients"]["cc"] == ["cc@example.com"]

    def test_create_draft_requires_auth(self, config: GmailMCPConfig) -> None:
        """Test create_draft requires authentication."""
        client = GmailMCPClient(config)

        with pytest.raises(GmailMCPError, match="Not authenticated"):
            client.create_draft(
                to=["test@example.com"],
                subject="Test",
                body="Test body",
            )

    def test_create_draft_success(
        self, authenticated_config: GmailMCPConfig
    ) -> None:
        """Test successful draft creation."""
        client = GmailMCPClient(authenticated_config)
        client.authenticate()

        result = client.create_draft(
            to=["test@example.com"],
            subject="Draft Subject",
            body="Draft body",
        )

        assert result["success"] is True
        assert "draft_id" in result


class TestGmailMCPErrors:
    """Tests for Gmail MCP error classes."""

    def test_gmail_mcp_error(self) -> None:
        """Test GmailMCPError base exception."""
        error = GmailMCPError("Test error")
        assert str(error) == "Test error"

    def test_token_refresh_error(self) -> None:
        """Test TokenRefreshError exception."""
        error = TokenRefreshError("Refresh failed")
        assert isinstance(error, GmailMCPError)

    def test_credentials_not_found_error(self) -> None:
        """Test CredentialsNotFoundError exception."""
        error = CredentialsNotFoundError("File not found")
        assert isinstance(error, GmailMCPError)

    def test_invalid_credentials_error(self) -> None:
        """Test InvalidCredentialsError exception."""
        error = InvalidCredentialsError("Invalid format")
        assert isinstance(error, GmailMCPError)
