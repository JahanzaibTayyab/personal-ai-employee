"""Unit tests for LinkedInService."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.linkedin_post import (
    LinkedInPost,
    LinkedInPostStatus,
    LinkedInEngagement,
    EngagementType,
)


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    """Create a temporary vault structure."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Pending_Approval").mkdir()
    (vault / "Approved").mkdir()
    (vault / "Rejected").mkdir()
    (vault / "Done").mkdir()
    (vault / "Logs").mkdir()
    (vault / "Needs_Action").mkdir()
    (vault / "Needs_Action" / "LinkedIn").mkdir()
    social = vault / "Social"
    social.mkdir()
    (social / "LinkedIn").mkdir()
    return vault


@pytest.fixture
def vault_config(vault_path: Path) -> VaultConfig:
    """Create VaultConfig for testing."""
    return VaultConfig(vault_path)


class TestLinkedInService:
    """Tests for LinkedInService class."""

    def test_service_initialization(self, vault_config: VaultConfig) -> None:
        """Test LinkedInService initializes correctly."""
        from ai_employee.services.linkedin import LinkedInService

        service = LinkedInService(vault_config)
        assert service is not None

    def test_schedule_post_creates_approval_request(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test scheduling a post creates an approval request."""
        from ai_employee.services.linkedin import LinkedInService

        service = LinkedInService(vault_config)
        approval_id = service.schedule_post(
            content="Excited to announce our new product launch!",
            scheduled_time=datetime.now() + timedelta(hours=1),
        )

        assert approval_id is not None
        assert approval_id.startswith("approval_")

        # Verify approval file created
        pending_files = list((vault_path / "Pending_Approval").glob("*.md"))
        assert len(pending_files) == 1

        content = pending_files[0].read_text()
        assert "social_post" in content or "linkedin" in content.lower()

    def test_schedule_post_with_media(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test scheduling a post with media attachment."""
        from ai_employee.services.linkedin import LinkedInService

        # Create a test media file
        media_path = vault_path / "product.png"
        media_path.write_bytes(b"fake image data")

        service = LinkedInService(vault_config)
        approval_id = service.schedule_post(
            content="Check out our new product!",
            scheduled_time=datetime.now() + timedelta(hours=1),
            media_paths=[str(media_path)],
        )

        assert approval_id is not None

    def test_get_pending_posts(self, vault_config: VaultConfig) -> None:
        """Test getting pending posts awaiting approval."""
        from ai_employee.services.linkedin import LinkedInService

        service = LinkedInService(vault_config)

        # Schedule some posts
        service.schedule_post(
            content="Post 1",
            scheduled_time=datetime.now() + timedelta(hours=1),
        )
        service.schedule_post(
            content="Post 2",
            scheduled_time=datetime.now() + timedelta(hours=2),
        )

        pending = service.get_pending_posts()
        assert len(pending) == 2

    def test_get_posts_today(self, vault_config: VaultConfig) -> None:
        """Test getting count of posts made today."""
        from ai_employee.services.linkedin import LinkedInService

        service = LinkedInService(vault_config)
        count = service.get_posts_today()

        assert count >= 0


class TestLinkedInPostCreation:
    """Tests for post creation and publishing."""

    def test_post_approved_content(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test posting approved content."""
        from ai_employee.services.linkedin import LinkedInService

        service = LinkedInService(vault_config)

        # Create and approve a post
        approval_id = service.schedule_post(
            content="Test post content",
            scheduled_time=datetime.now(),
        )

        # Move to approved
        pending_files = list((vault_path / "Pending_Approval").glob("*.md"))
        src = pending_files[0]
        dst = vault_path / "Approved" / src.name
        src.rename(dst)

        # Mock the API call
        with patch.object(service, "_post_to_linkedin") as mock_post:
            mock_post.return_value = {"post_id": "linkedin_123", "success": True}
            result = service.post_approved(approval_id)

        assert result["success"] is True
        assert "post_id" in result

    def test_post_respects_rate_limit(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test posting respects daily rate limit (25 posts/day)."""
        from ai_employee.services.linkedin import LinkedInService, RateLimitError

        service = LinkedInService(vault_config)

        # Simulate reaching rate limit
        with patch.object(service, "get_posts_today", return_value=25):
            with pytest.raises(RateLimitError, match="rate limit"):
                service.schedule_post(
                    content="This should be rate limited",
                    scheduled_time=datetime.now() + timedelta(hours=1),
                )


class TestEngagementKeywordDetection:
    """Tests for engagement keyword detection (FR-023)."""

    def test_detect_inquiry_keywords(self) -> None:
        """Test detection of inquiry keywords."""
        from ai_employee.services.linkedin import detect_engagement_keywords

        text = "I'm interested in learning more about your product"
        keywords = detect_engagement_keywords(text)

        assert "interested" in keywords

    def test_detect_pricing_keywords(self) -> None:
        """Test detection of pricing keywords."""
        from ai_employee.services.linkedin import detect_engagement_keywords

        text = "What's the pricing for your enterprise plan?"
        keywords = detect_engagement_keywords(text)

        assert "pricing" in keywords

    def test_detect_contact_keywords(self) -> None:
        """Test detection of contact request keywords."""
        from ai_employee.services.linkedin import detect_engagement_keywords

        text = "Please contact me to discuss further"
        keywords = detect_engagement_keywords(text)

        assert "contact" in keywords

    def test_detect_demo_keywords(self) -> None:
        """Test detection of demo request keywords."""
        from ai_employee.services.linkedin import detect_engagement_keywords

        text = "Can I schedule a demo of your platform?"
        keywords = detect_engagement_keywords(text)

        assert "demo" in keywords

    def test_detect_multiple_keywords(self) -> None:
        """Test detection of multiple keywords in one message."""
        from ai_employee.services.linkedin import detect_engagement_keywords

        text = "I'm interested in the pricing and would like a demo"
        keywords = detect_engagement_keywords(text)

        assert "interested" in keywords
        assert "pricing" in keywords
        assert "demo" in keywords

    def test_no_keywords_in_generic_comment(self) -> None:
        """Test no keywords detected in generic comment."""
        from ai_employee.services.linkedin import detect_engagement_keywords

        text = "Great post! Thanks for sharing."
        keywords = detect_engagement_keywords(text)

        assert len(keywords) == 0

    def test_case_insensitive_detection(self) -> None:
        """Test keyword detection is case insensitive."""
        from ai_employee.services.linkedin import detect_engagement_keywords

        text = "INTERESTED in learning more about PRICING"
        keywords = detect_engagement_keywords(text)

        assert "interested" in keywords
        assert "pricing" in keywords


class TestEngagementTracking:
    """Tests for engagement tracking."""

    def test_track_engagement(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test tracking engagement on a post."""
        from ai_employee.services.linkedin import LinkedInService

        service = LinkedInService(vault_config)

        engagement = LinkedInEngagement(
            id="eng_123",
            post_id="post_456",
            engagement_type=EngagementType.COMMENT,
            author="John Doe",
            content="I'm interested in your product",
            timestamp=datetime.now(),
            requires_followup=True,
            followup_keywords=["interested"],
        )

        service.track_engagement(engagement)

        # Verify engagement logged
        log_file = vault_path / "Social" / "LinkedIn" / "engagement.md"
        assert log_file.exists()
        content = log_file.read_text()
        assert "John Doe" in content

    def test_high_priority_engagement_creates_action(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test high-priority engagement creates action item."""
        from ai_employee.services.linkedin import LinkedInService

        service = LinkedInService(vault_config)

        # Engagement with business keywords
        engagement = LinkedInEngagement(
            id="eng_123",
            post_id="post_456",
            engagement_type=EngagementType.COMMENT,
            author="Jane Smith",
            content="What's your pricing? I'd like to schedule a demo.",
            timestamp=datetime.now(),
            requires_followup=True,
            followup_keywords=["pricing", "demo"],
        )

        service.track_engagement(engagement)

        # Verify action item created
        action_files = list((vault_path / "Needs_Action" / "LinkedIn").glob("*.md"))
        assert len(action_files) == 1


class TestLinkedInAuthentication:
    """Tests for LinkedIn API authentication."""

    def test_authenticate_success(self, vault_config: VaultConfig) -> None:
        """Test successful authentication."""
        from ai_employee.services.linkedin import LinkedInService

        service = LinkedInService(vault_config)

        with patch.object(service, "_authenticate_api") as mock_auth:
            mock_auth.return_value = True
            result = service.authenticate()

        assert result is True

    def test_is_authenticated(self, vault_config: VaultConfig) -> None:
        """Test checking authentication status."""
        from ai_employee.services.linkedin import LinkedInService

        service = LinkedInService(vault_config)

        # Initially not authenticated
        assert service.is_authenticated() is False


class TestLinkedInServiceErrors:
    """Tests for LinkedInService error handling."""

    def test_rate_limit_error(self) -> None:
        """Test RateLimitError exception."""
        from ai_employee.services.linkedin import RateLimitError

        error = RateLimitError("Daily rate limit exceeded")
        assert "rate limit" in str(error).lower()

    def test_linkedin_api_error(self) -> None:
        """Test LinkedInAPIError exception."""
        from ai_employee.services.linkedin import LinkedInAPIError

        error = LinkedInAPIError("API request failed")
        assert str(error) == "API request failed"

    def test_authentication_error(self) -> None:
        """Test AuthenticationError exception."""
        from ai_employee.services.linkedin import AuthenticationError

        error = AuthenticationError("Invalid credentials")
        assert "Invalid credentials" in str(error)


class TestEngagementWatcher:
    """Tests for LinkedInEngagementWatcher."""

    def test_watcher_initialization(self, vault_config: VaultConfig) -> None:
        """Test watcher initializes correctly."""
        from ai_employee.watchers.linkedin import LinkedInEngagementWatcher

        watcher = LinkedInEngagementWatcher(vault_config)
        assert watcher is not None

    def test_watcher_status(self, vault_config: VaultConfig) -> None:
        """Test watcher status tracking."""
        from ai_employee.watchers.linkedin import (
            LinkedInEngagementWatcher,
            LinkedInWatcherStatus,
        )

        watcher = LinkedInEngagementWatcher(vault_config)
        assert watcher.status == LinkedInWatcherStatus.DISCONNECTED

    def test_process_engagement_with_keywords(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test processing engagement that contains keywords."""
        from ai_employee.watchers.linkedin import LinkedInEngagementWatcher

        watcher = LinkedInEngagementWatcher(vault_config)

        raw_engagement = {
            "id": "eng_123",
            "post_id": "post_456",
            "type": "comment",
            "author": "John Doe",
            "content": "I'm interested in your pricing",
            "timestamp": datetime.now().isoformat(),
        }

        engagement = watcher.process_engagement(raw_engagement)

        assert engagement is not None
        assert "interested" in engagement.followup_keywords
        assert "pricing" in engagement.followup_keywords
