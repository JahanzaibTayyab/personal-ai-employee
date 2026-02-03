"""ApprovalRequest model - represents an action awaiting human approval."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class ApprovalCategory(str, Enum):
    """Category of approval request (FR-005)."""

    EMAIL = "email"
    SOCIAL_POST = "social_post"
    PAYMENT = "payment"
    FILE_OPERATION = "file_operation"
    CUSTOM = "custom"


class ApprovalStatus(str, Enum):
    """Status of approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"


@dataclass
class ApprovalRequest:
    """An action awaiting human approval (FR-001 to FR-005).

    Stored as markdown file in /Pending_Approval/ with YAML frontmatter.
    State transitions: PENDING -> APPROVED/REJECTED/EXPIRED -> EXECUTED
    """

    id: str
    category: ApprovalCategory
    payload: dict[str, Any]
    created_at: datetime
    expires_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    executed_at: datetime | None = None
    error: str | None = None
    summary: str = ""

    @classmethod
    def create(
        cls,
        id: str,
        category: ApprovalCategory,
        payload: dict[str, Any],
        summary: str = "",
        expiration_hours: int = 24,
    ) -> "ApprovalRequest":
        """Create a new approval request with default expiration.

        Args:
            id: Unique identifier for the request
            category: Type of approval (email, social_post, etc.)
            payload: Action-specific data
            summary: Human-readable summary of the action
            expiration_hours: Hours until auto-expiration (default: 24)

        Returns:
            New ApprovalRequest instance
        """
        now = datetime.now()
        return cls(
            id=id,
            category=category,
            payload=payload,
            created_at=now,
            expires_at=now + timedelta(hours=expiration_hours),
            summary=summary,
        )

    def is_expired(self) -> bool:
        """Check if the request has expired."""
        return datetime.now() > self.expires_at and self.status == ApprovalStatus.PENDING

    def time_remaining(self) -> timedelta:
        """Get time remaining until expiration."""
        if self.status != ApprovalStatus.PENDING:
            return timedelta(0)
        remaining = self.expires_at - datetime.now()
        return max(remaining, timedelta(0))

    def to_frontmatter(self) -> dict[str, Any]:
        """Convert approval request to YAML frontmatter dictionary."""
        data: dict[str, Any] = {
            "id": self.id,
            "category": self.category.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "payload": self.payload,
        }

        if self.executed_at is not None:
            data["executed_at"] = self.executed_at.isoformat()
        if self.error is not None:
            data["error"] = self.error

        return data

    @classmethod
    def from_frontmatter(cls, data: dict[str, Any], summary: str = "") -> "ApprovalRequest":
        """Create ApprovalRequest from YAML frontmatter dictionary."""
        return cls(
            id=data["id"],
            category=ApprovalCategory(data["category"]),
            payload=data.get("payload", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            status=ApprovalStatus(data.get("status", "pending")),
            executed_at=(
                datetime.fromisoformat(data["executed_at"])
                if data.get("executed_at")
                else None
            ),
            error=data.get("error"),
            summary=summary,
        )

    def get_filename(self) -> str:
        """Generate filename for this approval request."""
        return f"APPROVAL_{self.category.value}_{self.id}.md"

    def __post_init__(self) -> None:
        """Validate the approval request."""
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")
