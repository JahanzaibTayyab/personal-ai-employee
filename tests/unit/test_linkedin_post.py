"""Unit tests for LinkedInPost and LinkedInEngagement models."""

from datetime import datetime, timedelta

import pytest

from ai_employee.models.linkedin_post import (
    DEFAULT_FOLLOWUP_KEYWORDS,
    LINKEDIN_MAX_CHARS,
    LINKEDIN_MAX_POSTS_PER_DAY,
    EngagementType,
    LinkedInEngagement,
    LinkedInPost,
    LinkedInPostStatus,
)


class TestLinkedInPost:
    """Tests for LinkedInPost dataclass."""

    def test_create_linkedin_post(self) -> None:
        """Test creating a new LinkedIn post."""
        post = LinkedInPost.create(
            content="Hello LinkedIn!",
        )

        assert post.content == "Hello LinkedIn!"
        assert post.status == LinkedInPostStatus.DRAFT
        assert post.id.startswith("linkedin_")
        assert post.scheduled_at is None

    def test_create_scheduled_post(self) -> None:
        """Test creating a scheduled LinkedIn post."""
        future_time = datetime.now() + timedelta(hours=2)
        post = LinkedInPost.create(
            content="Scheduled post",
            scheduled_at=future_time,
        )

        assert post.status == LinkedInPostStatus.SCHEDULED
        assert post.scheduled_at == future_time

    def test_create_post_exceeds_limit(self) -> None:
        """Test creating post that exceeds character limit."""
        long_content = "x" * (LINKEDIN_MAX_CHARS + 1)

        with pytest.raises(ValueError, match="exceeds.*character limit"):
            LinkedInPost.create(content=long_content)

    def test_default_engagement(self) -> None:
        """Test default engagement metrics."""
        post = LinkedInPost.create(content="Test")

        assert post.engagement["likes"] == 0
        assert post.engagement["comments"] == 0
        assert post.engagement["shares"] == 0
        assert post.engagement["impressions"] == 0

    def test_to_frontmatter(self) -> None:
        """Test conversion to frontmatter dictionary."""
        post = LinkedInPost.create(content="Test content")

        fm = post.to_frontmatter()

        assert fm["status"] == "draft"
        assert "created_at" in fm
        assert "engagement" in fm

    def test_from_frontmatter(self) -> None:
        """Test creation from frontmatter dictionary."""
        fm = {
            "id": "linkedin_test",
            "status": "posted",
            "created_at": "2026-02-03T10:00:00",
            "posted_at": "2026-02-03T10:05:00",
            "engagement": {"likes": 10, "comments": 2, "shares": 1, "impressions": 100},
        }

        post = LinkedInPost.from_frontmatter(fm, content="Restored content")

        assert post.id == "linkedin_test"
        assert post.content == "Restored content"
        assert post.status == LinkedInPostStatus.POSTED
        assert post.engagement["likes"] == 10

    def test_get_filename(self) -> None:
        """Test filename generation."""
        post = LinkedInPost.create(content="Test")

        filename = post.get_filename()
        assert filename.startswith("POST_linkedin_")
        assert filename.endswith(".md")

    def test_validation_content_length(self) -> None:
        """Test validation of content length."""
        with pytest.raises(ValueError, match="exceeds.*character limit"):
            LinkedInPost(
                id="test",
                content="x" * (LINKEDIN_MAX_CHARS + 1),
            )


class TestLinkedInEngagement:
    """Tests for LinkedInEngagement dataclass."""

    def test_create_engagement_like(self) -> None:
        """Test creating a like engagement."""
        engagement = LinkedInEngagement.create(
            post_id="post_123",
            engagement_type=EngagementType.LIKE,
            author="John Doe",
        )

        assert engagement.post_id == "post_123"
        assert engagement.engagement_type == EngagementType.LIKE
        assert engagement.author == "John Doe"
        assert engagement.requires_followup is False

    def test_create_engagement_comment_with_followup(self) -> None:
        """Test creating a comment that requires followup."""
        engagement = LinkedInEngagement.create(
            post_id="post_123",
            engagement_type=EngagementType.COMMENT,
            author="Jane Smith",
            content="I'm interested in learning more about pricing",
        )

        assert engagement.requires_followup is True
        assert "interested" in engagement.followup_keywords
        assert "pricing" in engagement.followup_keywords

    def test_create_engagement_comment_no_followup(self) -> None:
        """Test creating a comment without followup keywords."""
        engagement = LinkedInEngagement.create(
            post_id="post_123",
            engagement_type=EngagementType.COMMENT,
            author="Bob",
            content="Great post!",
        )

        assert engagement.requires_followup is False
        assert engagement.followup_keywords == []

    def test_create_engagement_custom_keywords(self) -> None:
        """Test followup detection with custom keywords."""
        engagement = LinkedInEngagement.create(
            post_id="post_123",
            engagement_type=EngagementType.COMMENT,
            author="User",
            content="Can we schedule a call?",
            keyword_list=["call", "meeting", "schedule"],
        )

        assert engagement.requires_followup is True
        assert "call" in engagement.followup_keywords
        assert "schedule" in engagement.followup_keywords

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        engagement = LinkedInEngagement.create(
            post_id="post_123",
            engagement_type=EngagementType.COMMENT,
            author="Test User",
            content="Test comment",
        )

        d = engagement.to_dict()

        assert d["post_id"] == "post_123"
        assert d["type"] == "comment"
        assert d["author"] == "Test User"
        assert d["content"] == "Test comment"

    def test_from_dict(self) -> None:
        """Test creation from dictionary."""
        data = {
            "id": "engagement_test",
            "post_id": "post_456",
            "type": "share",
            "author": "From Dict",
            "timestamp": "2026-02-03T10:00:00",
            "requires_followup": False,
        }

        engagement = LinkedInEngagement.from_dict(data)

        assert engagement.id == "engagement_test"
        assert engagement.engagement_type == EngagementType.SHARE
        assert engagement.author == "From Dict"


class TestLinkedInPostStatus:
    """Tests for LinkedInPostStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """Test all required statuses are defined."""
        assert LinkedInPostStatus.DRAFT.value == "draft"
        assert LinkedInPostStatus.SCHEDULED.value == "scheduled"
        assert LinkedInPostStatus.PENDING_APPROVAL.value == "pending_approval"
        assert LinkedInPostStatus.APPROVED.value == "approved"
        assert LinkedInPostStatus.POSTED.value == "posted"
        assert LinkedInPostStatus.FAILED.value == "failed"


class TestEngagementType:
    """Tests for EngagementType enum."""

    def test_all_types_exist(self) -> None:
        """Test all required engagement types are defined."""
        assert EngagementType.LIKE.value == "like"
        assert EngagementType.COMMENT.value == "comment"
        assert EngagementType.SHARE.value == "share"
        assert EngagementType.MENTION.value == "mention"


class TestConstants:
    """Tests for LinkedIn constants."""

    def test_max_chars(self) -> None:
        """Test maximum character limit is defined."""
        assert LINKEDIN_MAX_CHARS == 3000

    def test_max_posts_per_day(self) -> None:
        """Test rate limit constant is defined."""
        assert LINKEDIN_MAX_POSTS_PER_DAY == 25

    def test_followup_keywords_defined(self) -> None:
        """Test default followup keywords are defined."""
        assert "inquiry" in DEFAULT_FOLLOWUP_KEYWORDS
        assert "interested" in DEFAULT_FOLLOWUP_KEYWORDS
        assert "pricing" in DEFAULT_FOLLOWUP_KEYWORDS
        assert "contact" in DEFAULT_FOLLOWUP_KEYWORDS
        assert "demo" in DEFAULT_FOLLOWUP_KEYWORDS
