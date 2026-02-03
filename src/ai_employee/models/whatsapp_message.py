"""WhatsAppMessage model - detected urgent messages from WhatsApp watcher."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class WhatsAppActionStatus(str, Enum):
    """Processing status for WhatsApp messages."""

    NEW = "new"
    REVIEWED = "reviewed"
    RESPONDED = "responded"
    ARCHIVED = "archived"


# Default keywords for urgent message detection (FR-007)
DEFAULT_KEYWORDS = ["urgent", "asap", "invoice", "payment", "help", "pricing"]


@dataclass
class WhatsAppMessage:
    """Detected urgent WhatsApp message (FR-006 to FR-010).

    Stored as markdown file in /Needs_Action/WhatsApp/ with YAML frontmatter.
    """

    id: str
    sender: str  # Sender name or phone number
    content: str
    timestamp: datetime
    keywords: list[str]  # Matched keywords (FR-007)
    action_status: WhatsAppActionStatus = WhatsAppActionStatus.NEW
    chat_name: str | None = None  # Group name if applicable
    phone_number: str | None = None

    @classmethod
    def create(
        cls,
        sender: str,
        content: str,
        keywords: list[str],
        chat_name: str | None = None,
        phone_number: str | None = None,
    ) -> "WhatsAppMessage":
        """Create a new WhatsApp message with auto-generated ID.

        Args:
            sender: Sender name or phone number
            content: Message content
            keywords: Matched keywords that triggered detection
            chat_name: Optional group name
            phone_number: Optional phone number if different from sender

        Returns:
            New WhatsAppMessage instance
        """
        import uuid
        now = datetime.now()
        unique = uuid.uuid4().hex[:6]
        msg_id = f"whatsapp_{now.strftime('%Y%m%d_%H%M%S')}_{unique}"
        return cls(
            id=msg_id,
            sender=sender,
            content=content,
            timestamp=now,
            keywords=keywords,
            chat_name=chat_name,
            phone_number=phone_number,
        )

    @staticmethod
    def detect_keywords(
        content: str,
        keyword_list: list[str] | None = None,
    ) -> list[str]:
        """Detect matching keywords in message content.

        Args:
            content: Message content to scan
            keyword_list: Optional custom keyword list (defaults to DEFAULT_KEYWORDS)

        Returns:
            List of matched keywords (lowercase)
        """
        keywords = keyword_list or DEFAULT_KEYWORDS
        content_lower = content.lower()
        return [kw for kw in keywords if kw.lower() in content_lower]

    def to_frontmatter(self) -> dict[str, Any]:
        """Convert message to YAML frontmatter dictionary."""
        data: dict[str, Any] = {
            "id": self.id,
            "sender": self.sender,
            "timestamp": self.timestamp.isoformat(),
            "keywords": self.keywords,
            "action_status": self.action_status.value,
        }

        if self.chat_name:
            data["chat_name"] = self.chat_name
        if self.phone_number:
            data["phone_number"] = self.phone_number

        return data

    @classmethod
    def from_frontmatter(cls, data: dict[str, Any], content: str = "") -> "WhatsAppMessage":
        """Create WhatsAppMessage from YAML frontmatter dictionary."""
        return cls(
            id=data["id"],
            sender=data["sender"],
            content=content,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            keywords=data.get("keywords", []),
            action_status=WhatsAppActionStatus(data.get("action_status", "new")),
            chat_name=data.get("chat_name"),
            phone_number=data.get("phone_number"),
        )

    def get_filename(self) -> str:
        """Generate filename for this WhatsApp message."""
        return f"WHATSAPP_{self.id}.md"

    def __post_init__(self) -> None:
        """Validate the WhatsApp message."""
        if not self.sender:
            raise ValueError("sender must not be empty")
        if not self.keywords:
            raise ValueError("must have at least one matched keyword")
