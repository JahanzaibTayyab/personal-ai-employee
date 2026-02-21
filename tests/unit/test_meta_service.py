"""Unit tests for MetaService (mock facebook-sdk)."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.enums import PostStatus
from ai_employee.models.meta_post import MetaEngagement, MetaPost
from ai_employee.services.meta import (
    MetaAPIError,
    MetaRateLimitError,
    MetaService,
    MetaServiceError,
    detect_business_keywords,
    DEFAULT_BUSINESS_KEYWORDS,
)


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    """Create a temporary vault structure."""
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


@pytest.fixture
def vault_config(vault_path: Path) -> VaultConfig:
    """Create vault config with temp path."""
    config = VaultConfig(root=vault_path)
    config.ensure_structure()
    # Create Gold tier folders
    (vault_path / "Social" / "Meta" / "posts").mkdir(parents=True, exist_ok=True)
    (vault_path / "Needs_Action" / "Facebook").mkdir(parents=True, exist_ok=True)
    return config


@pytest.fixture
def meta_service(vault_config: VaultConfig) -> MetaService:
    """Create a MetaService instance."""
    return MetaService(vault_config)


class TestMetaServiceConnect:
    """Tests for MetaService.connect method."""

    def test_connect_success(self, meta_service: MetaService) -> None:
        """Test successful connection."""
        with patch.object(
            meta_service, "_create_graph_api", return_value=MagicMock()
        ):
            result = meta_service.connect(
                app_id="test_app_id",
                app_secret="test_app_secret",
                access_token="test_token",
                page_id="page_123",
            )

            assert result is True
            assert meta_service.is_connected()

    def test_connect_failure(self, meta_service: MetaService) -> None:
        """Test failed connection."""
        with patch.object(
            meta_service,
            "_create_graph_api",
            side_effect=Exception("Connection failed"),
        ):
            result = meta_service.connect(
                app_id="bad_id",
                app_secret="bad_secret",
                access_token="bad_token",
                page_id="page_123",
            )

            assert result is False
            assert not meta_service.is_connected()

    def test_connect_missing_params(self, meta_service: MetaService) -> None:
        """Test connection with missing parameters."""
        result = meta_service.connect(
            app_id="",
            app_secret="",
            access_token="",
            page_id="",
        )

        assert result is False


class TestMetaServiceCreatePost:
    """Tests for MetaService.create_post method."""

    def test_create_facebook_post(self, meta_service: MetaService) -> None:
        """Test creating a Facebook post."""
        post = meta_service.create_post(
            content="Hello Facebook!",
            platform="facebook",
        )

        assert post.content == "Hello Facebook!"
        assert post.platform == "facebook"
        assert post.status == PostStatus.DRAFT

    def test_create_instagram_post(self, meta_service: MetaService) -> None:
        """Test creating an Instagram post."""
        post = meta_service.create_post(
            content="Hello Instagram!",
            media_urls=["https://example.com/photo.jpg"],
            platform="instagram",
        )

        assert post.platform == "instagram"
        assert post.media_urls == ["https://example.com/photo.jpg"]

    def test_create_scheduled_post(self, meta_service: MetaService) -> None:
        """Test creating a scheduled post."""
        future_time = datetime.now() + timedelta(hours=2)
        post = meta_service.create_post(
            content="Scheduled post",
            platform="facebook",
            scheduled_time=future_time,
        )

        assert post.status == PostStatus.SCHEDULED
        assert post.scheduled_time == future_time

    def test_create_cross_post(self, meta_service: MetaService) -> None:
        """Test creating a cross-posted post."""
        post = meta_service.create_post(
            content="Cross-post content",
            platform="facebook",
            cross_post=True,
        )

        assert post.cross_post is True

    def test_create_post_saves_file(
        self, meta_service: MetaService, vault_path: Path
    ) -> None:
        """Test that creating a post saves to vault."""
        post = meta_service.create_post(
            content="Saved post",
            platform="facebook",
        )

        post_dir = vault_path / "Social" / "Meta" / "posts"
        post_files = list(post_dir.glob("*.md"))
        assert len(post_files) == 1


class TestMetaServicePublishPost:
    """Tests for MetaService.publish_post method."""

    def test_publish_post_success(self, meta_service: MetaService) -> None:
        """Test publishing a post successfully."""
        post = meta_service.create_post(
            content="To publish",
            platform="facebook",
        )

        mock_api = MagicMock()
        mock_api.put_object.return_value = {"id": "fb_post_123"}
        meta_service._graph_api = mock_api
        meta_service._connected = True
        meta_service._page_id = "page_123"

        published = meta_service.publish_post(post.id)

        assert published.status == PostStatus.POSTED
        assert published.platform_id == "fb_post_123"
        assert published.posted_time is not None

    def test_publish_post_not_connected(
        self, meta_service: MetaService
    ) -> None:
        """Test publishing when not connected raises error."""
        post = meta_service.create_post(
            content="Not connected",
            platform="facebook",
        )

        with pytest.raises(MetaServiceError, match="Not connected"):
            meta_service.publish_post(post.id)

    def test_publish_nonexistent_post(
        self, meta_service: MetaService
    ) -> None:
        """Test publishing a nonexistent post raises error."""
        meta_service._connected = True

        with pytest.raises(MetaServiceError, match="not found"):
            meta_service.publish_post("nonexistent_id")

    def test_publish_post_api_error(self, meta_service: MetaService) -> None:
        """Test API error during publish."""
        post = meta_service.create_post(
            content="API error test",
            platform="facebook",
        )

        mock_api = MagicMock()
        mock_api.put_object.side_effect = Exception("API Error")
        meta_service._graph_api = mock_api
        meta_service._connected = True
        meta_service._page_id = "page_123"

        with pytest.raises(MetaAPIError):
            meta_service.publish_post(post.id)


class TestMetaServiceGetPost:
    """Tests for MetaService.get_post method."""

    def test_get_existing_post(self, meta_service: MetaService) -> None:
        """Test getting an existing post."""
        created = meta_service.create_post(
            content="Get me",
            platform="facebook",
        )

        retrieved = meta_service.get_post(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.content == "Get me"

    def test_get_nonexistent_post(self, meta_service: MetaService) -> None:
        """Test getting a nonexistent post returns None."""
        result = meta_service.get_post("nonexistent")
        assert result is None


class TestMetaServiceGetEngagement:
    """Tests for MetaService.get_engagement method."""

    def test_get_engagement_success(
        self, meta_service: MetaService
    ) -> None:
        """Test getting engagement data."""
        mock_api = MagicMock()
        mock_api.get_object.return_value = {
            "likes": {"summary": {"total_count": 42}},
            "comments": {"summary": {"total_count": 7}},
            "shares": {"count": 3},
            "insights": {
                "data": [
                    {
                        "name": "post_impressions",
                        "values": [{"value": 1500}],
                    },
                    {
                        "name": "post_impressions_unique",
                        "values": [{"value": 800}],
                    },
                ]
            },
        }
        meta_service._graph_api = mock_api
        meta_service._connected = True

        engagement = meta_service.get_engagement("fb_post_123")

        assert engagement.likes == 42
        assert engagement.comments == 7
        assert engagement.shares == 3
        assert engagement.impressions == 1500
        assert engagement.reach == 800

    def test_get_engagement_not_connected(
        self, meta_service: MetaService
    ) -> None:
        """Test engagement when not connected."""
        with pytest.raises(MetaServiceError, match="Not connected"):
            meta_service.get_engagement("some_post")


class TestMetaServiceListPosts:
    """Tests for MetaService.list_posts method."""

    def test_list_all_posts(self, meta_service: MetaService) -> None:
        """Test listing all posts."""
        meta_service.create_post(content="Post 1", platform="facebook")
        meta_service.create_post(content="Post 2", platform="instagram")
        meta_service.create_post(content="Post 3", platform="facebook")

        posts = meta_service.list_posts()

        assert len(posts) == 3

    def test_list_posts_by_platform(
        self, meta_service: MetaService
    ) -> None:
        """Test listing posts filtered by platform."""
        meta_service.create_post(content="FB Post", platform="facebook")
        meta_service.create_post(content="IG Post", platform="instagram")

        fb_posts = meta_service.list_posts(platform="facebook")
        ig_posts = meta_service.list_posts(platform="instagram")

        assert len(fb_posts) == 1
        assert fb_posts[0].platform == "facebook"
        assert len(ig_posts) == 1
        assert ig_posts[0].platform == "instagram"

    def test_list_posts_by_status(self, meta_service: MetaService) -> None:
        """Test listing posts filtered by status."""
        meta_service.create_post(content="Draft", platform="facebook")
        future = datetime.now() + timedelta(hours=2)
        meta_service.create_post(
            content="Sched",
            platform="facebook",
            scheduled_time=future,
        )

        drafts = meta_service.list_posts(status=PostStatus.DRAFT)
        scheduled = meta_service.list_posts(status=PostStatus.SCHEDULED)

        assert len(drafts) == 1
        assert len(scheduled) == 1

    def test_list_posts_with_limit(self, meta_service: MetaService) -> None:
        """Test listing posts with a limit."""
        for i in range(5):
            meta_service.create_post(
                content=f"Post {i}", platform="facebook"
            )

        posts = meta_service.list_posts(limit=3)

        assert len(posts) == 3


class TestDetectBusinessKeywords:
    """Tests for detect_business_keywords function."""

    def test_detect_keywords_in_comments(self) -> None:
        """Test keyword detection in comment text."""
        comments = [
            {"text": "I'm interested in pricing", "author": "User1"},
            {"text": "Great post!", "author": "User2"},
            {"text": "Can we schedule a demo?", "author": "User3"},
        ]

        results = detect_business_keywords(comments)

        assert len(results) == 2
        assert any(r["author"] == "User1" for r in results)
        assert any(r["author"] == "User3" for r in results)

    def test_detect_no_keywords(self) -> None:
        """Test no keywords found."""
        comments = [
            {"text": "Nice photo!", "author": "User1"},
            {"text": "Thanks for sharing", "author": "User2"},
        ]

        results = detect_business_keywords(comments)
        assert len(results) == 0

    def test_detect_custom_keywords(self) -> None:
        """Test with custom keyword list."""
        comments = [
            {"text": "What about consulting?", "author": "User1"},
        ]

        results = detect_business_keywords(
            comments, keywords=["consulting", "advisory"]
        )
        assert len(results) == 1

    def test_detect_empty_comments(self) -> None:
        """Test with empty comments list."""
        results = detect_business_keywords([])
        assert len(results) == 0

    def test_default_keywords_defined(self) -> None:
        """Test default business keywords are available."""
        assert "pricing" in DEFAULT_BUSINESS_KEYWORDS
        assert "demo" in DEFAULT_BUSINESS_KEYWORDS
        assert "inquiry" in DEFAULT_BUSINESS_KEYWORDS
