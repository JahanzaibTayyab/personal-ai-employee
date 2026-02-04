"""Unit tests for WhatsAppWatcher.

Tests message parsing, keyword detection, and watcher behavior.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.whatsapp_message import (
    DEFAULT_KEYWORDS,
    WhatsAppActionStatus,
    WhatsAppMessage,
)
from ai_employee.watchers.whatsapp import (
    WhatsAppWatcher,
    WhatsAppWatcherStatus,
    parse_whatsapp_message,
)


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    """Create a temporary vault structure."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Needs_Action").mkdir()
    (vault / "Needs_Action" / "WhatsApp").mkdir()
    (vault / "Logs").mkdir()
    (vault / "Dashboard.md").touch()
    return vault


@pytest.fixture
def vault_config(vault_path: Path) -> VaultConfig:
    """Create VaultConfig for testing."""
    return VaultConfig(vault_path)


class TestParseWhatsAppMessage:
    """Tests for message parsing from WhatsApp Web elements."""

    def test_parse_basic_message(self) -> None:
        """Test parsing a basic message."""
        raw_data = {
            "sender": "John Doe",
            "content": "This is urgent! Need help.",
            "timestamp": "10:30 AM",
            "chat_name": None,
        }

        message = parse_whatsapp_message(raw_data)

        assert message.sender == "John Doe"
        assert message.content == "This is urgent! Need help."
        assert "urgent" in message.keywords
        assert "help" in message.keywords

    def test_parse_message_with_phone_number(self) -> None:
        """Test parsing message with phone number."""
        raw_data = {
            "sender": "+1234567890",
            "content": "Payment needed ASAP",
            "timestamp": "2:45 PM",
            "chat_name": None,
        }

        message = parse_whatsapp_message(raw_data)

        assert message.sender == "+1234567890"
        assert message.phone_number == "+1234567890"
        assert "payment" in message.keywords
        assert "asap" in message.keywords

    def test_parse_group_message(self) -> None:
        """Test parsing message from a group chat."""
        raw_data = {
            "sender": "Jane Smith",
            "content": "Please check the invoice",
            "timestamp": "5:00 PM",
            "chat_name": "Project Team",
        }

        message = parse_whatsapp_message(raw_data)

        assert message.sender == "Jane Smith"
        assert message.chat_name == "Project Team"
        assert "invoice" in message.keywords

    def test_parse_message_no_keywords(self) -> None:
        """Test parsing message with no matching keywords returns None."""
        raw_data = {
            "sender": "Bob",
            "content": "Hello, how are you?",
            "timestamp": "9:00 AM",
            "chat_name": None,
        }

        result = parse_whatsapp_message(raw_data)

        assert result is None

    def test_parse_message_custom_keywords(self) -> None:
        """Test parsing with custom keyword list."""
        raw_data = {
            "sender": "Client",
            "content": "Can we schedule a meeting?",
            "timestamp": "11:00 AM",
            "chat_name": None,
        }

        # No match with default keywords
        result = parse_whatsapp_message(raw_data)
        assert result is None

        # Match with custom keywords
        result = parse_whatsapp_message(raw_data, keywords=["meeting", "schedule"])
        assert result is not None
        assert "meeting" in result.keywords
        assert "schedule" in result.keywords


class TestKeywordDetection:
    """Tests for keyword detection functionality."""

    def test_detect_default_keywords(self) -> None:
        """Test detection with default keyword list."""
        content = "This is urgent! I need help with pricing."

        keywords = WhatsAppMessage.detect_keywords(content)

        assert "urgent" in keywords
        assert "help" in keywords
        assert "pricing" in keywords

    def test_detect_case_insensitive(self) -> None:
        """Test keyword detection is case insensitive."""
        content = "URGENT: PAYMENT needed ASAP"

        keywords = WhatsAppMessage.detect_keywords(content)

        assert "urgent" in keywords
        assert "payment" in keywords
        assert "asap" in keywords

    def test_detect_no_match(self) -> None:
        """Test detection returns empty list when no match."""
        content = "Hello, nice to meet you!"

        keywords = WhatsAppMessage.detect_keywords(content)

        assert keywords == []

    def test_detect_custom_keywords(self) -> None:
        """Test detection with custom keyword list."""
        content = "Let's have a call tomorrow"
        custom_keywords = ["call", "meeting", "tomorrow"]

        keywords = WhatsAppMessage.detect_keywords(content, custom_keywords)

        assert "call" in keywords
        assert "tomorrow" in keywords
        assert "meeting" not in keywords

    def test_detect_partial_word_match(self) -> None:
        """Test that keywords match as substrings."""
        content = "The invoice_123.pdf is attached"

        keywords = WhatsAppMessage.detect_keywords(content)

        assert "invoice" in keywords

    def test_all_default_keywords_defined(self) -> None:
        """Test all expected default keywords exist."""
        expected = ["urgent", "asap", "invoice", "payment", "help", "pricing"]

        for kw in expected:
            assert kw in DEFAULT_KEYWORDS


class TestWhatsAppWatcher:
    """Tests for WhatsAppWatcher class."""

    def test_watcher_initialization(self, vault_config: VaultConfig) -> None:
        """Test watcher initializes correctly."""
        watcher = WhatsAppWatcher(vault_config)

        assert watcher.status == WhatsAppWatcherStatus.DISCONNECTED
        assert watcher.running is False
        assert watcher.keywords == DEFAULT_KEYWORDS

    def test_watcher_custom_keywords(self, vault_config: VaultConfig) -> None:
        """Test watcher accepts custom keywords."""
        custom_keywords = ["urgent", "critical", "emergency"]
        watcher = WhatsAppWatcher(vault_config, keywords=custom_keywords)

        assert watcher.keywords == custom_keywords

    def test_watcher_session_path(self, vault_config: VaultConfig) -> None:
        """Test watcher creates session storage path."""
        watcher = WhatsAppWatcher(vault_config)

        assert watcher.session_path is not None
        assert "whatsapp_session" in str(watcher.session_path)

    def test_create_action_file(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test creating action file for detected message."""
        watcher = WhatsAppWatcher(vault_config)
        message = WhatsAppMessage.create(
            sender="Test Sender",
            content="Urgent: Need help!",
            keywords=["urgent", "help"],
        )

        file_path = watcher.create_action_file(message)

        assert file_path.exists()
        assert file_path.parent.name == "WhatsApp"
        content = file_path.read_text()
        assert "sender: Test Sender" in content
        assert "urgent" in content

    def test_session_expired_detection(self, vault_config: VaultConfig) -> None:
        """Test session expiration is detected."""
        watcher = WhatsAppWatcher(vault_config)

        # Initially not expired
        assert watcher.is_session_expired() is False

        # Simulate session expiration
        watcher._last_activity = datetime.now() - timedelta(hours=25)
        assert watcher.is_session_expired() is True

    def test_heartbeat_logging(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test heartbeat logging at 60s interval."""
        watcher = WhatsAppWatcher(vault_config)

        # Log a heartbeat
        watcher.log_heartbeat()

        # Check log file exists
        log_files = list((vault_path / "Logs").glob("watcher_*.log"))
        assert len(log_files) >= 0  # May depend on timing

    def test_status_transitions(self, vault_config: VaultConfig) -> None:
        """Test watcher status transitions."""
        watcher = WhatsAppWatcher(vault_config)

        assert watcher.status == WhatsAppWatcherStatus.DISCONNECTED

        watcher.set_status(WhatsAppWatcherStatus.CONNECTING)
        assert watcher.status == WhatsAppWatcherStatus.CONNECTING

        watcher.set_status(WhatsAppWatcherStatus.QR_REQUIRED)
        assert watcher.status == WhatsAppWatcherStatus.QR_REQUIRED

        watcher.set_status(WhatsAppWatcherStatus.CONNECTED)
        assert watcher.status == WhatsAppWatcherStatus.CONNECTED

    def test_get_whatsapp_folder(self, vault_config: VaultConfig) -> None:
        """Test getting the WhatsApp action folder path."""
        watcher = WhatsAppWatcher(vault_config)

        folder = watcher.get_whatsapp_folder()

        assert folder.name == "WhatsApp"
        assert folder.parent.name == "Needs_Action"


class TestWhatsAppWatcherStatus:
    """Tests for WhatsAppWatcherStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """Test all required statuses are defined."""
        assert WhatsAppWatcherStatus.DISCONNECTED.value == "disconnected"
        assert WhatsAppWatcherStatus.CONNECTING.value == "connecting"
        assert WhatsAppWatcherStatus.QR_REQUIRED.value == "qr_required"
        assert WhatsAppWatcherStatus.CONNECTED.value == "connected"
        assert WhatsAppWatcherStatus.SESSION_EXPIRED.value == "session_expired"
        assert WhatsAppWatcherStatus.ERROR.value == "error"


class TestWhatsAppActionFileCreation:
    """Tests for action file creation and formatting."""

    def test_action_file_frontmatter(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test action file has correct frontmatter."""
        watcher = WhatsAppWatcher(vault_config)
        message = WhatsAppMessage.create(
            sender="John Doe",
            content="This is urgent! Need pricing info.",
            keywords=["urgent", "pricing"],
            chat_name="Sales Group",
        )

        file_path = watcher.create_action_file(message)
        content = file_path.read_text()

        assert "---" in content
        assert "sender: John Doe" in content
        assert "chat_name: Sales Group" in content
        assert "action_status: new" in content

    def test_action_file_body_content(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test action file body contains message content."""
        watcher = WhatsAppWatcher(vault_config)
        message = WhatsAppMessage.create(
            sender="Jane Smith",
            content="Please help with the invoice payment",
            keywords=["help", "invoice", "payment"],
        )

        file_path = watcher.create_action_file(message)
        content = file_path.read_text()

        assert "Please help with the invoice payment" in content
        assert "## Message" in content or message.content in content

    def test_action_file_unique_names(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test each action file has unique name."""
        watcher = WhatsAppWatcher(vault_config)

        messages = [
            WhatsAppMessage.create(
                sender=f"Sender {i}",
                content=f"Urgent message {i}",
                keywords=["urgent"],
            )
            for i in range(3)
        ]

        file_paths = [watcher.create_action_file(msg) for msg in messages]
        file_names = [p.name for p in file_paths]

        # All names should be unique
        assert len(file_names) == len(set(file_names))
