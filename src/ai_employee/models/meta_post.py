"""Meta (Facebook/Instagram) post and engagement models."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ai_employee.models.enums import PostStatus

# Facebook character limit
META_MAX_CHARS_FACEBOOK = 63206

# Instagram caption character limit
META_MAX_CHARS_INSTAGRAM = 2200

# Meta Graph API rate limit: calls per user per hour (FR-028)
META_RATE_LIMIT_PER_HOUR = 200

# Valid platforms
VALID_PLATFORMS = ("facebook", "instagram")

# Valid Instagram media types
VALID_MEDIA_TYPES = ("image", "video", "carousel")


@dataclass
class MetaEngagement:
    """Engagement metrics for a Meta post.

    Tracks likes, comments, shares, reach, and impressions.
    """

    likes: int = 0
    comments: int = 0
    shares: int = 0
    reach: int | None = None
    impressions: int | None = None
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert engagement to dictionary."""
        data: dict[str, Any] = {
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "last_updated": self.last_updated.isoformat(),
        }
        if self.reach is not None:
            data["reach"] = self.reach
        if self.impressions is not None:
            data["impressions"] = self.impressions
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MetaEngagement":
        """Create MetaEngagement from dictionary."""
        return cls(
            likes=data.get("likes", 0),
            comments=data.get("comments", 0),
            shares=data.get("shares", 0),
            reach=data.get("reach"),
            impressions=data.get("impressions"),
            last_updated=datetime.fromisoformat(data["last_updated"]),
        )


@dataclass
class MetaPost:
    """Meta (Facebook/Instagram) post model.

    Stored in /Social/Meta/posts/ as markdown with YAML frontmatter.
    Supports both Facebook and Instagram platforms via Meta Graph API.
    """

    id: str
    platform: str
    page_id: str = ""
    content: str = ""
    media_urls: list[str] | None = None
    media_type: str | None = None
    scheduled_time: datetime | None = None
    posted_time: datetime | None = None
    status: PostStatus = PostStatus.DRAFT
    approval_id: str | None = None
    engagement: MetaEngagement | None = None
    error_message: str | None = None
    cross_post: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    correlation_id: str | None = None
    platform_id: str | None = None

    @classmethod
    def create(
        cls,
        platform: str,
        page_id: str = "",
        content: str = "",
        media_urls: list[str] | None = None,
        media_type: str | None = None,
        scheduled_time: datetime | None = None,
        cross_post: bool = False,
        correlation_id: str | None = None,
    ) -> "MetaPost":
        """Create a new Meta post.

        Args:
            platform: "facebook" or "instagram"
            page_id: Page or account ID
            content: Post content text
            media_urls: Optional list of media URLs
            media_type: Optional media type (image/video/carousel)
            scheduled_time: Optional scheduled posting time
            cross_post: Whether to cross-post to other platforms
            correlation_id: Optional correlation ID for cross-domain

        Returns:
            New MetaPost instance

        Raises:
            ValueError: If platform is invalid or content exceeds limit
        """
        if platform not in VALID_PLATFORMS:
            raise ValueError(
                f"platform must be one of {VALID_PLATFORMS}, got '{platform}'"
            )

        max_chars = (
            META_MAX_CHARS_FACEBOOK
            if platform == "facebook"
            else META_MAX_CHARS_INSTAGRAM
        )
        if len(content) > max_chars:
            raise ValueError(
                f"Content exceeds {max_chars} character limit for {platform}"
            )

        if media_type and media_type not in VALID_MEDIA_TYPES:
            raise ValueError(
                f"media_type must be one of {VALID_MEDIA_TYPES}, "
                f"got '{media_type}'"
            )

        now = datetime.now()
        unique = uuid.uuid4().hex[:8]
        post_id = f"meta_{platform}_{now.strftime('%Y%m%d_%H%M%S')}_{unique}"

        status = (
            PostStatus.SCHEDULED if scheduled_time else PostStatus.DRAFT
        )

        return cls(
            id=post_id,
            platform=platform,
            page_id=page_id,
            content=content,
            media_urls=media_urls,
            media_type=media_type,
            scheduled_time=scheduled_time,
            status=status,
            cross_post=cross_post,
            created_at=now,
            correlation_id=correlation_id,
        )

    def to_frontmatter(self) -> dict[str, Any]:
        """Convert post to YAML frontmatter dictionary."""
        data: dict[str, Any] = {
            "id": self.id,
            "platform": self.platform,
            "page_id": self.page_id,
            "status": self.status.value,
            "cross_post": self.cross_post,
            "created_at": self.created_at.isoformat(),
        }

        if self.platform_id:
            data["platform_id"] = self.platform_id
        if self.media_urls:
            data["media_urls"] = self.media_urls
        if self.media_type:
            data["media_type"] = self.media_type
        if self.scheduled_time:
            data["scheduled_time"] = self.scheduled_time.isoformat()
        if self.posted_time:
            data["posted_time"] = self.posted_time.isoformat()
        if self.approval_id:
            data["approval_id"] = self.approval_id
        if self.engagement:
            data["engagement"] = self.engagement.to_dict()
        if self.error_message:
            data["error_message"] = self.error_message
        if self.correlation_id:
            data["correlation_id"] = self.correlation_id

        return data

    @classmethod
    def from_frontmatter(
        cls,
        data: dict[str, Any],
        content: str = "",
    ) -> "MetaPost":
        """Create MetaPost from YAML frontmatter dictionary."""
        engagement = None
        if data.get("engagement"):
            engagement = MetaEngagement.from_dict(data["engagement"])

        return cls(
            id=data["id"],
            platform=data["platform"],
            page_id=data.get("page_id", ""),
            content=content,
            media_urls=data.get("media_urls"),
            media_type=data.get("media_type"),
            scheduled_time=(
                datetime.fromisoformat(data["scheduled_time"])
                if data.get("scheduled_time")
                else None
            ),
            posted_time=(
                datetime.fromisoformat(data["posted_time"])
                if data.get("posted_time")
                else None
            ),
            status=PostStatus(data.get("status", "draft")),
            approval_id=data.get("approval_id"),
            engagement=engagement,
            error_message=data.get("error_message"),
            cross_post=data.get("cross_post", False),
            created_at=datetime.fromisoformat(data["created_at"]),
            correlation_id=data.get("correlation_id"),
            platform_id=data.get("platform_id"),
        )

    def get_filename(self) -> str:
        """Generate filename for this Meta post."""
        return f"META_{self.id}.md"

    def __post_init__(self) -> None:
        """Validate the Meta post."""
        if self.platform == "facebook":
            max_chars = META_MAX_CHARS_FACEBOOK
        elif self.platform == "instagram":
            max_chars = META_MAX_CHARS_INSTAGRAM
        else:
            return  # Skip validation for loaded posts with unknown platform

        if len(self.content) > max_chars:
            raise ValueError(
                f"Content exceeds {max_chars} character limit "
                f"for {self.platform}"
            )
