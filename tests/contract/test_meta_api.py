"""Contract tests for Meta Graph API integration (mock API)."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from ai_employee.services.meta import MetaService
from ai_employee.config import VaultConfig
from pathlib import Path


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
    (vault_path / "Social" / "Meta" / "posts").mkdir(
        parents=True, exist_ok=True
    )
    return config


@pytest.fixture
def meta_service(vault_config: VaultConfig) -> MetaService:
    """Create a MetaService with mocked API."""
    service = MetaService(vault_config)
    return service


class TestMetaGraphAPIContract:
    """Contract tests verifying Meta Graph API interaction patterns."""

    def test_connect_validates_access_token(
        self, meta_service: MetaService
    ) -> None:
        """Test that connect validates the access token with Graph API."""
        mock_graph = MagicMock()
        mock_graph.get_object.return_value = {
            "id": "page_123",
            "name": "Test Page",
        }

        with patch.object(
            meta_service, "_create_graph_api", return_value=mock_graph
        ):
            result = meta_service.connect(
                app_id="app_123",
                app_secret="secret_456",
                access_token="valid_token",
                page_id="page_123",
            )

        assert result is True
        mock_graph.get_object.assert_called_once()

    def test_publish_calls_put_object(
        self, meta_service: MetaService
    ) -> None:
        """Test that publish uses put_object for Facebook Graph API."""
        post = meta_service.create_post(
            content="Contract test post",
            platform="facebook",
        )

        mock_graph = MagicMock()
        mock_graph.put_object.return_value = {"id": "fb_contract_123"}
        meta_service._graph_api = mock_graph
        meta_service._connected = True
        meta_service._page_id = "page_123"

        published = meta_service.publish_post(post.id)

        mock_graph.put_object.assert_called_once()
        call_args = mock_graph.put_object.call_args
        assert call_args[0][0] == "page_123"
        assert call_args[0][1] == "feed"
        assert published.platform_id == "fb_contract_123"

    def test_get_engagement_calls_get_object(
        self, meta_service: MetaService
    ) -> None:
        """Test that get_engagement uses get_object with correct fields."""
        mock_graph = MagicMock()
        mock_graph.get_object.return_value = {
            "likes": {"summary": {"total_count": 10}},
            "comments": {"summary": {"total_count": 3}},
            "shares": {"count": 1},
            "insights": {"data": []},
        }
        meta_service._graph_api = mock_graph
        meta_service._connected = True

        meta_service.get_engagement("fb_post_456")

        mock_graph.get_object.assert_called_once()
        call_args = mock_graph.get_object.call_args
        assert call_args[0][0] == "fb_post_456"

    def test_rate_limit_header_handling(
        self, meta_service: MetaService
    ) -> None:
        """Test that rate limit errors are properly handled."""
        mock_graph = MagicMock()
        mock_graph.put_object.side_effect = Exception(
            "rate limit exceeded"
        )
        meta_service._graph_api = mock_graph
        meta_service._connected = True
        meta_service._page_id = "page_123"

        post = meta_service.create_post(
            content="Rate limit test",
            platform="facebook",
        )

        from ai_employee.services.meta import MetaAPIError

        with pytest.raises(MetaAPIError):
            meta_service.publish_post(post.id)

    def test_instagram_publish_uses_media_endpoint(
        self, meta_service: MetaService
    ) -> None:
        """Test that Instagram publish uses the media container flow."""
        post = meta_service.create_post(
            content="Instagram contract test",
            media_urls=["https://example.com/photo.jpg"],
            platform="instagram",
        )

        mock_graph = MagicMock()
        # Instagram requires two-step: create container, then publish
        mock_graph.put_object.side_effect = [
            {"id": "container_123"},  # Container creation
            {"id": "ig_post_123"},    # Publish
        ]
        meta_service._graph_api = mock_graph
        meta_service._connected = True
        meta_service._page_id = "page_123"
        meta_service._ig_user_id = "ig_user_123"

        published = meta_service.publish_post(post.id)

        assert published.platform_id is not None

    def test_api_response_format_for_engagement(
        self, meta_service: MetaService
    ) -> None:
        """Test that engagement parsing handles the full Graph API response."""
        mock_graph = MagicMock()
        mock_graph.get_object.return_value = {
            "likes": {"summary": {"total_count": 100}},
            "comments": {
                "summary": {"total_count": 20},
                "data": [
                    {
                        "message": "Interested in pricing",
                        "from": {"name": "User1", "id": "u1"},
                    },
                    {
                        "message": "Great post!",
                        "from": {"name": "User2", "id": "u2"},
                    },
                ],
            },
            "shares": {"count": 5},
            "insights": {
                "data": [
                    {
                        "name": "post_impressions",
                        "values": [{"value": 5000}],
                    },
                    {
                        "name": "post_impressions_unique",
                        "values": [{"value": 3000}],
                    },
                ]
            },
        }
        meta_service._graph_api = mock_graph
        meta_service._connected = True

        engagement = meta_service.get_engagement("fb_full_test")

        assert engagement.likes == 100
        assert engagement.comments == 20
        assert engagement.shares == 5
        assert engagement.impressions == 5000
        assert engagement.reach == 3000
