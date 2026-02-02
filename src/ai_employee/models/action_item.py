"""Action Item model - represents a file or message requiring AI processing."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ActionItemType(str, Enum):
    """Type of action item."""

    FILE_DROP = "file_drop"
    EMAIL = "email"


class ActionItemStatus(str, Enum):
    """Processing status of an action item."""

    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    QUARANTINED = "quarantined"


class Priority(str, Enum):
    """Priority level for action items."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SourceType(str, Enum):
    """Source of the action item."""

    FILESYSTEM = "filesystem"
    GMAIL = "gmail"


@dataclass
class ActionItem:
    """A file or message requiring AI processing.

    Stored as markdown file in /Needs_Action/ folder with YAML frontmatter.
    """

    type: ActionItemType
    source: SourceType
    original_name: str
    created: datetime
    status: ActionItemStatus = ActionItemStatus.PENDING
    priority: Priority = Priority.NORMAL
    file_size: int | None = None
    file_type: str | None = None
    from_address: str | None = None
    message_id: str | None = None
    processed_at: datetime | None = None
    error: str | None = None
    content: str = field(default="")

    def to_frontmatter(self) -> dict[str, Any]:
        """Convert action item to YAML frontmatter dictionary."""
        data: dict[str, Any] = {
            "type": self.type.value,
            "source": self.source.value,
            "original_name": self.original_name,
            "created": self.created.isoformat(),
            "status": self.status.value,
            "priority": self.priority.value,
        }

        if self.file_size is not None:
            data["file_size"] = self.file_size
        if self.file_type is not None:
            data["file_type"] = self.file_type
        if self.from_address is not None:
            data["from_address"] = self.from_address
        if self.message_id is not None:
            data["message_id"] = self.message_id
        if self.processed_at is not None:
            data["processed_at"] = self.processed_at.isoformat()
        if self.error is not None:
            data["error"] = self.error

        return data

    @classmethod
    def from_frontmatter(cls, data: dict[str, Any], content: str = "") -> "ActionItem":
        """Create ActionItem from YAML frontmatter dictionary."""
        return cls(
            type=ActionItemType(data["type"]),
            source=SourceType(data["source"]),
            original_name=data["original_name"],
            created=datetime.fromisoformat(data["created"]),
            status=ActionItemStatus(data.get("status", "pending")),
            priority=Priority(data.get("priority", "normal")),
            file_size=data.get("file_size"),
            file_type=data.get("file_type"),
            from_address=data.get("from_address"),
            message_id=data.get("message_id"),
            processed_at=(
                datetime.fromisoformat(data["processed_at"])
                if data.get("processed_at")
                else None
            ),
            error=data.get("error"),
            content=content,
        )

    def get_filename(self) -> str:
        """Generate filename for this action item."""
        if self.type == ActionItemType.FILE_DROP:
            return f"FILE_{self.original_name}.md"
        elif self.type == ActionItemType.EMAIL:
            return f"EMAIL_{self.message_id}.md"
        return f"ITEM_{self.original_name}.md"
