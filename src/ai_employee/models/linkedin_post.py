"""LinkedIn models - posts and engagement tracking for social media automation."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LinkedInPostStatus(str, Enum):
    """Status of LinkedIn post."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    POSTED = "posted"
    FAILED = "failed"


class EngagementType(str, Enum):
    """Type of LinkedIn engagement."""

    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    MENTION = "mention"


# Maximum LinkedIn post length
LINKEDIN_MAX_CHARS = 3000

# Rate limit: max posts per day (FR-025)
LINKEDIN_MAX_POSTS_PER_DAY = 25

# Keywords for followup detection (FR-023)
DEFAULT_FOLLOWUP_KEYWORDS = ["inquiry", "interested", "pricing", "contact", "demo"]


@dataclass
class LinkedInPost:
    """LinkedIn post content (FR-021 to FR-025).

    Stored in /Social/LinkedIn/posts/ folder with YAML frontmatter.
    """

    id: str
    content: str
    status: LinkedInPostStatus = LinkedInPostStatus.DRAFT
    scheduled_at: datetime | None = None
    posted_at: datetime | None = None
    approval_request_id: str | None = None
    linkedin_post_id: str | None = None  # ID from LinkedIn API after posting
    engagement: dict[str, int] = field(default_factory=lambda: {
        "likes": 0,
        "comments": 0,
        "shares": 0,
        "impressions": 0,
    })
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        content: str,
        scheduled_at: datetime | None = None,
    ) -> "LinkedInPost":
        """Create a new LinkedIn post.

        Args:
            content: Post content (max 3000 characters)
            scheduled_at: Optional scheduled posting time

        Returns:
            New LinkedInPost instance

        Raises:
            ValueError: If content exceeds maximum length
        """
        if len(content) > LINKEDIN_MAX_CHARS:
            raise ValueError(f"Content exceeds {LINKEDIN_MAX_CHARS} character limit")

        now = datetime.now()
        post_id = f"linkedin_{now.strftime('%Y%m%d_%H%M%S')}"

        status = LinkedInPostStatus.SCHEDULED if scheduled_at else LinkedInPostStatus.DRAFT

        return cls(
            id=post_id,
            content=content,
            status=status,
            scheduled_at=scheduled_at,
            created_at=now,
        )

    def to_frontmatter(self) -> dict[str, Any]:
        """Convert post to YAML frontmatter dictionary."""
        data: dict[str, Any] = {
            "id": self.id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "engagement": self.engagement,
        }

        if self.scheduled_at:
            data["scheduled_at"] = self.scheduled_at.isoformat()
        if self.posted_at:
            data["posted_at"] = self.posted_at.isoformat()
        if self.approval_request_id:
            data["approval_request_id"] = self.approval_request_id
        if self.linkedin_post_id:
            data["linkedin_post_id"] = self.linkedin_post_id
        if self.error:
            data["error"] = self.error

        return data

    @classmethod
    def from_frontmatter(cls, data: dict[str, Any], content: str = "") -> "LinkedInPost":
        """Create LinkedInPost from YAML frontmatter dictionary."""
        return cls(
            id=data["id"],
            content=content,
            status=LinkedInPostStatus(data.get("status", "draft")),
            scheduled_at=(
                datetime.fromisoformat(data["scheduled_at"])
                if data.get("scheduled_at")
                else None
            ),
            posted_at=(
                datetime.fromisoformat(data["posted_at"])
                if data.get("posted_at")
                else None
            ),
            approval_request_id=data.get("approval_request_id"),
            linkedin_post_id=data.get("linkedin_post_id"),
            engagement=data.get("engagement", {
                "likes": 0, "comments": 0, "shares": 0, "impressions": 0
            }),
            error=data.get("error"),
            created_at=datetime.fromisoformat(data["created_at"]),
        )

    def get_filename(self) -> str:
        """Generate filename for this LinkedIn post."""
        return f"POST_{self.id}.md"

    def __post_init__(self) -> None:
        """Validate the LinkedIn post."""
        if len(self.content) > LINKEDIN_MAX_CHARS:
            raise ValueError(f"Content exceeds {LINKEDIN_MAX_CHARS} character limit")

        if self.scheduled_at and self.status == LinkedInPostStatus.SCHEDULED:
            if self.scheduled_at < datetime.now():
                raise ValueError("scheduled_at must be in the future for scheduled posts")


@dataclass
class LinkedInEngagement:
    """LinkedIn engagement activity (FR-022 to FR-024).

    Stored as entries in /Social/LinkedIn/engagement.md
    """

    id: str
    post_id: str
    engagement_type: EngagementType
    author: str  # Name of person who engaged
    content: str | None = None  # Comment content if applicable
    timestamp: datetime = field(default_factory=datetime.now)
    requires_followup: bool = False  # True if matches keywords (FR-023)
    followup_keywords: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        post_id: str,
        engagement_type: EngagementType,
        author: str,
        content: str | None = None,
        keyword_list: list[str] | None = None,
    ) -> "LinkedInEngagement":
        """Create a new engagement record with auto-detection of followup keywords.

        Args:
            post_id: ID of the post being engaged with
            engagement_type: Type of engagement (like, comment, share, mention)
            author: Name of the person who engaged
            content: Optional comment content
            keyword_list: Optional custom keyword list for followup detection

        Returns:
            New LinkedInEngagement instance
        """
        now = datetime.now()
        eng_id = f"engagement_{now.strftime('%Y%m%d_%H%M%S')}"

        # Detect followup keywords in comments
        followup_keywords: list[str] = []
        requires_followup = False

        if content and engagement_type == EngagementType.COMMENT:
            keywords = keyword_list or DEFAULT_FOLLOWUP_KEYWORDS
            content_lower = content.lower()
            followup_keywords = [kw for kw in keywords if kw.lower() in content_lower]
            requires_followup = len(followup_keywords) > 0

        return cls(
            id=eng_id,
            post_id=post_id,
            engagement_type=engagement_type,
            author=author,
            content=content,
            timestamp=now,
            requires_followup=requires_followup,
            followup_keywords=followup_keywords,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert engagement to dictionary for logging."""
        data: dict[str, Any] = {
            "id": self.id,
            "post_id": self.post_id,
            "type": self.engagement_type.value,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
            "requires_followup": self.requires_followup,
        }

        if self.content:
            data["content"] = self.content
        if self.followup_keywords:
            data["followup_keywords"] = self.followup_keywords

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LinkedInEngagement":
        """Create LinkedInEngagement from dictionary."""
        return cls(
            id=data["id"],
            post_id=data["post_id"],
            engagement_type=EngagementType(data["type"]),
            author=data["author"],
            content=data.get("content"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            requires_followup=data.get("requires_followup", False),
            followup_keywords=data.get("followup_keywords", []),
        )
