"""Unit tests for MetaPost and MetaEngagement models."""

from datetime import datetime, timedelta

import pytest

from ai_employee.models.enums import PostStatus
from ai_employee.models.meta_post import (
    META_MAX_CHARS_FACEBOOK,
    META_MAX_CHARS_INSTAGRAM,
    META_RATE_LIMIT_PER_HOUR,
    MetaEngagement,
    MetaPost,
)


class TestMetaPost:
    """Tests for MetaPost dataclass."""

    def test_create_facebook_post(self) -> None:
        """Test creating a new Facebook post."""
        post = MetaPost.create(
            platform="facebook",
            page_id="page_123",
            content="Hello Facebook!",
        )

        assert post.platform == "facebook"
        assert post.page_id == "page_123"
        assert post.content == "Hello Facebook!"
        assert post.status == PostStatus.DRAFT
        assert post.id is not None
        assert post.platform_id is None
        assert post.media_urls is None
        assert post.media_type is None
        assert post.scheduled_time is None
        assert post.posted_time is None
        assert post.approval_id is None
        assert post.engagement is None
        assert post.error_message is None
        assert post.cross_post is False
        assert post.correlation_id is None
        assert post.created_at is not None

    def test_create_instagram_post(self) -> None:
        """Test creating a new Instagram post."""
        post = MetaPost.create(
            platform="instagram",
            page_id="ig_page_123",
            content="Hello Instagram!",
            media_urls=["https://example.com/photo.jpg"],
            media_type="image",
        )

        assert post.platform == "instagram"
        assert post.page_id == "ig_page_123"
        assert post.media_urls == ["https://example.com/photo.jpg"]
        assert post.media_type == "image"

    def test_create_scheduled_post(self) -> None:
        """Test creating a scheduled post."""
        future_time = datetime.now() + timedelta(hours=2)
        post = MetaPost.create(
            platform="facebook",
            page_id="page_123",
            content="Scheduled post",
            scheduled_time=future_time,
        )

        assert post.status == PostStatus.SCHEDULED
        assert post.scheduled_time == future_time

    def test_create_cross_post(self) -> None:
        """Test creating a cross-post."""
        post = MetaPost.create(
            platform="facebook",
            page_id="page_123",
            content="Cross-posted content",
            cross_post=True,
        )

        assert post.cross_post is True

    def test_invalid_platform_raises(self) -> None:
        """Test that an invalid platform raises ValueError."""
        with pytest.raises(ValueError, match="platform must be"):
            MetaPost.create(
                platform="tiktok",
                page_id="page_123",
                content="Invalid",
            )

    def test_facebook_content_length_validation(self) -> None:
        """Test Facebook content length limit."""
        long_content = "x" * (META_MAX_CHARS_FACEBOOK + 1)
        with pytest.raises(ValueError, match="exceeds.*character limit"):
            MetaPost.create(
                platform="facebook",
                page_id="page_123",
                content=long_content,
            )

    def test_instagram_content_length_validation(self) -> None:
        """Test Instagram content length limit."""
        long_content = "x" * (META_MAX_CHARS_INSTAGRAM + 1)
        with pytest.raises(ValueError, match="exceeds.*character limit"):
            MetaPost.create(
                platform="instagram",
                page_id="ig_123",
                content=long_content,
            )

    def test_instagram_media_type_validation(self) -> None:
        """Test Instagram media type must be valid."""
        with pytest.raises(ValueError, match="media_type must be"):
            MetaPost.create(
                platform="instagram",
                page_id="ig_123",
                content="Post",
                media_type="gif",
            )

    def test_to_frontmatter(self) -> None:
        """Test conversion to frontmatter dictionary."""
        post = MetaPost.create(
            platform="facebook",
            page_id="page_123",
            content="Test content",
        )

        fm = post.to_frontmatter()

        assert fm["platform"] == "facebook"
        assert fm["page_id"] == "page_123"
        assert fm["status"] == "draft"
        assert "id" in fm
        assert "created_at" in fm

    def test_to_frontmatter_with_engagement(self) -> None:
        """Test frontmatter with engagement data."""
        engagement = MetaEngagement(
            likes=10,
            comments=5,
            shares=2,
            reach=100,
            impressions=200,
        )
        post = MetaPost.create(
            platform="facebook",
            page_id="page_123",
            content="Test",
        )
        post_with_engagement = MetaPost(
            id=post.id,
            platform=post.platform,
            page_id=post.page_id,
            content=post.content,
            status=post.status,
            engagement=engagement,
            created_at=post.created_at,
        )

        fm = post_with_engagement.to_frontmatter()
        assert fm["engagement"]["likes"] == 10
        assert fm["engagement"]["reach"] == 100

    def test_from_frontmatter(self) -> None:
        """Test creation from frontmatter dictionary."""
        fm = {
            "id": "meta_test_123",
            "platform": "facebook",
            "page_id": "page_456",
            "status": "posted",
            "created_at": "2026-02-10T10:00:00",
            "posted_time": "2026-02-10T10:05:00",
            "engagement": {
                "likes": 10,
                "comments": 2,
                "shares": 1,
                "reach": 50,
                "impressions": 100,
                "last_updated": "2026-02-10T11:00:00",
            },
        }

        post = MetaPost.from_frontmatter(fm, content="Restored content")

        assert post.id == "meta_test_123"
        assert post.platform == "facebook"
        assert post.content == "Restored content"
        assert post.status == PostStatus.POSTED
        assert post.engagement is not None
        assert post.engagement.likes == 10

    def test_from_frontmatter_minimal(self) -> None:
        """Test creation from minimal frontmatter."""
        fm = {
            "id": "meta_min",
            "platform": "instagram",
            "page_id": "ig_page",
            "status": "draft",
            "created_at": "2026-02-10T10:00:00",
        }

        post = MetaPost.from_frontmatter(fm, content="Minimal")
        assert post.id == "meta_min"
        assert post.engagement is None

    def test_get_filename(self) -> None:
        """Test filename generation."""
        post = MetaPost.create(
            platform="facebook",
            page_id="page_123",
            content="Test",
        )

        filename = post.get_filename()
        assert filename.startswith("META_")
        assert filename.endswith(".md")
        assert post.id in filename


class TestMetaEngagement:
    """Tests for MetaEngagement dataclass."""

    def test_create_engagement(self) -> None:
        """Test creating an engagement record."""
        engagement = MetaEngagement(
            likes=10,
            comments=5,
            shares=2,
        )

        assert engagement.likes == 10
        assert engagement.comments == 5
        assert engagement.shares == 2
        assert engagement.reach is None
        assert engagement.impressions is None
        assert engagement.last_updated is not None

    def test_create_engagement_with_reach(self) -> None:
        """Test engagement with reach and impressions."""
        engagement = MetaEngagement(
            likes=100,
            comments=20,
            shares=10,
            reach=500,
            impressions=1000,
        )

        assert engagement.reach == 500
        assert engagement.impressions == 1000

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        engagement = MetaEngagement(
            likes=10,
            comments=5,
            shares=2,
            reach=50,
            impressions=100,
        )

        d = engagement.to_dict()

        assert d["likes"] == 10
        assert d["comments"] == 5
        assert d["shares"] == 2
        assert d["reach"] == 50
        assert d["impressions"] == 100
        assert "last_updated" in d

    def test_from_dict(self) -> None:
        """Test creation from dictionary."""
        data = {
            "likes": 15,
            "comments": 3,
            "shares": 1,
            "reach": 200,
            "impressions": 500,
            "last_updated": "2026-02-10T12:00:00",
        }

        engagement = MetaEngagement.from_dict(data)

        assert engagement.likes == 15
        assert engagement.reach == 200

    def test_from_dict_minimal(self) -> None:
        """Test creation from minimal dictionary."""
        data = {
            "likes": 5,
            "comments": 1,
            "shares": 0,
            "last_updated": "2026-02-10T12:00:00",
        }

        engagement = MetaEngagement.from_dict(data)
        assert engagement.reach is None
        assert engagement.impressions is None

    def test_default_values(self) -> None:
        """Test default engagement values."""
        engagement = MetaEngagement()

        assert engagement.likes == 0
        assert engagement.comments == 0
        assert engagement.shares == 0


class TestConstants:
    """Tests for Meta constants."""

    def test_facebook_max_chars(self) -> None:
        """Test Facebook character limit constant."""
        assert META_MAX_CHARS_FACEBOOK == 63206

    def test_instagram_max_chars(self) -> None:
        """Test Instagram character limit constant."""
        assert META_MAX_CHARS_INSTAGRAM == 2200

    def test_rate_limit(self) -> None:
        """Test rate limit constant."""
        assert META_RATE_LIMIT_PER_HOUR == 200
