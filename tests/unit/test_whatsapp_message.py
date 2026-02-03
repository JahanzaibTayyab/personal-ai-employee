"""Unit tests for WhatsAppMessage model."""

from datetime import datetime

import pytest

from ai_employee.models.whatsapp_message import (
    DEFAULT_KEYWORDS,
    WhatsAppActionStatus,
    WhatsAppMessage,
)


class TestWhatsAppMessage:
    """Tests for WhatsAppMessage dataclass."""

    def test_create_whatsapp_message(self) -> None:
        """Test creating a new WhatsApp message."""
        msg = WhatsAppMessage.create(
            sender="John Doe",
            content="This is urgent! Need help.",
            keywords=["urgent", "help"],
        )

        assert msg.sender == "John Doe"
        assert msg.content == "This is urgent! Need help."
        assert msg.keywords == ["urgent", "help"]
        assert msg.action_status == WhatsAppActionStatus.NEW
        assert msg.id.startswith("whatsapp_")

    def test_create_with_optional_fields(self) -> None:
        """Test creating message with optional fields."""
        msg = WhatsAppMessage.create(
            sender="Jane",
            content="Payment needed",
            keywords=["payment"],
            chat_name="Project Group",
            phone_number="+1234567890",
        )

        assert msg.chat_name == "Project Group"
        assert msg.phone_number == "+1234567890"

    def test_detect_keywords_default(self) -> None:
        """Test keyword detection with default keywords."""
        content = "This is urgent! I need help with the payment."

        detected = WhatsAppMessage.detect_keywords(content)

        assert "urgent" in detected
        assert "help" in detected
        assert "payment" in detected

    def test_detect_keywords_custom(self) -> None:
        """Test keyword detection with custom keywords."""
        content = "Can we schedule a meeting?"
        custom_keywords = ["meeting", "call", "schedule"]

        detected = WhatsAppMessage.detect_keywords(content, custom_keywords)

        assert "meeting" in detected
        assert "schedule" in detected
        assert "call" not in detected

    def test_detect_keywords_case_insensitive(self) -> None:
        """Test keyword detection is case insensitive."""
        content = "URGENT: PAYMENT needed ASAP"

        detected = WhatsAppMessage.detect_keywords(content)

        assert "urgent" in detected
        assert "payment" in detected
        assert "asap" in detected

    def test_detect_keywords_no_match(self) -> None:
        """Test keyword detection with no matches."""
        content = "Just saying hello!"

        detected = WhatsAppMessage.detect_keywords(content)

        assert detected == []

    def test_to_frontmatter(self) -> None:
        """Test conversion to frontmatter dictionary."""
        msg = WhatsAppMessage.create(
            sender="Test Sender",
            content="Test content",
            keywords=["urgent"],
            chat_name="Test Group",
        )

        fm = msg.to_frontmatter()

        assert fm["sender"] == "Test Sender"
        assert fm["keywords"] == ["urgent"]
        assert fm["action_status"] == "new"
        assert fm["chat_name"] == "Test Group"

    def test_from_frontmatter(self) -> None:
        """Test creation from frontmatter dictionary."""
        fm = {
            "id": "whatsapp_test",
            "sender": "From FM",
            "timestamp": "2026-02-03T10:00:00",
            "keywords": ["payment"],
            "action_status": "reviewed",
            "phone_number": "+9876543210",
        }

        msg = WhatsAppMessage.from_frontmatter(fm, content="Restored content")

        assert msg.id == "whatsapp_test"
        assert msg.sender == "From FM"
        assert msg.content == "Restored content"
        assert msg.action_status == WhatsAppActionStatus.REVIEWED
        assert msg.phone_number == "+9876543210"

    def test_get_filename(self) -> None:
        """Test filename generation."""
        msg = WhatsAppMessage.create(
            sender="Test",
            content="Test",
            keywords=["urgent"],
        )

        filename = msg.get_filename()
        assert filename.startswith("WHATSAPP_whatsapp_")
        assert filename.endswith(".md")

    def test_validation_empty_sender(self) -> None:
        """Test validation rejects empty sender."""
        with pytest.raises(ValueError, match="sender must not be empty"):
            WhatsAppMessage(
                id="test",
                sender="",
                content="Test",
                timestamp=datetime.now(),
                keywords=["urgent"],
            )

    def test_validation_empty_keywords(self) -> None:
        """Test validation rejects empty keywords list."""
        with pytest.raises(ValueError, match="must have at least one matched keyword"):
            WhatsAppMessage(
                id="test",
                sender="Test Sender",
                content="Test",
                timestamp=datetime.now(),
                keywords=[],
            )


class TestWhatsAppActionStatus:
    """Tests for WhatsAppActionStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """Test all required statuses are defined."""
        assert WhatsAppActionStatus.NEW.value == "new"
        assert WhatsAppActionStatus.REVIEWED.value == "reviewed"
        assert WhatsAppActionStatus.RESPONDED.value == "responded"
        assert WhatsAppActionStatus.ARCHIVED.value == "archived"


class TestDefaultKeywords:
    """Tests for default keywords configuration."""

    def test_default_keywords_defined(self) -> None:
        """Test default keywords are defined."""
        assert "urgent" in DEFAULT_KEYWORDS
        assert "asap" in DEFAULT_KEYWORDS
        assert "invoice" in DEFAULT_KEYWORDS
        assert "payment" in DEFAULT_KEYWORDS
        assert "help" in DEFAULT_KEYWORDS
        assert "pricing" in DEFAULT_KEYWORDS
