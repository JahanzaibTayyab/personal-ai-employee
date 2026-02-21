"""Unit tests for CrossDomainService."""

from pathlib import Path

import pytest

from ai_employee.config import VaultConfig
from ai_employee.services.cross_domain import CrossDomainService
from ai_employee.utils.correlation import CorrelationContext


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
    return config


@pytest.fixture
def cross_domain_service(vault_config: VaultConfig) -> CrossDomainService:
    """Create a CrossDomainService instance."""
    return CrossDomainService(vault_config)


class TestCreateCorrelation:
    """Tests for CrossDomainService.create_correlation."""

    def test_create_correlation(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test creating a new correlation context."""
        context = cross_domain_service.create_correlation(
            source_domain="email",
            source_id="email_123",
        )

        assert isinstance(context, CorrelationContext)
        assert context.source_domain == "email"
        assert context.source_id == "email_123"
        assert context.correlation_id.startswith("corr_")

    def test_create_correlation_with_metadata(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test creating correlation with metadata."""
        context = cross_domain_service.create_correlation(
            source_domain="social",
            source_id="post_456",
            metadata={"platform": "twitter", "topic": "product launch"},
        )

        assert context.metadata["platform"] == "twitter"
        assert context.metadata["topic"] == "product launch"

    def test_create_correlation_persists(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test that created correlation is persisted."""
        context = cross_domain_service.create_correlation(
            source_domain="email",
            source_id="email_789",
        )

        # Should be retrievable
        related = cross_domain_service.get_related_items(
            context.correlation_id
        )
        assert related is not None


class TestLinkItems:
    """Tests for CrossDomainService.link_items."""

    def test_link_item_to_correlation(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test linking an item to an existing correlation."""
        context = cross_domain_service.create_correlation(
            source_domain="email",
            source_id="email_123",
        )

        cross_domain_service.link_items(
            correlation_id=context.correlation_id,
            domain="social",
            item_id="tweet_456",
        )

        related = cross_domain_service.get_related_items(
            context.correlation_id
        )
        assert len(related) >= 1
        domains = [item["domain"] for item in related]
        assert "social" in domains

    def test_link_multiple_items(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test linking multiple items to same correlation."""
        context = cross_domain_service.create_correlation(
            source_domain="email",
            source_id="email_123",
        )

        cross_domain_service.link_items(
            context.correlation_id, "social", "tweet_1"
        )
        cross_domain_service.link_items(
            context.correlation_id, "meta", "fb_post_1"
        )
        cross_domain_service.link_items(
            context.correlation_id, "task", "task_1"
        )

        related = cross_domain_service.get_related_items(
            context.correlation_id
        )
        assert len(related) >= 3

    def test_link_invalid_correlation_id(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test linking to a nonexistent correlation raises error."""
        with pytest.raises(ValueError, match="not found"):
            cross_domain_service.link_items(
                "nonexistent_corr", "social", "item_1"
            )


class TestGetRelatedItems:
    """Tests for CrossDomainService.get_related_items."""

    def test_get_related_items(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test getting items related through correlation."""
        context = cross_domain_service.create_correlation(
            source_domain="email",
            source_id="email_100",
        )
        cross_domain_service.link_items(
            context.correlation_id, "social", "post_200"
        )

        related = cross_domain_service.get_related_items(
            context.correlation_id
        )

        assert isinstance(related, list)
        assert len(related) >= 1

    def test_get_related_items_includes_source(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test that related items include the source item."""
        context = cross_domain_service.create_correlation(
            source_domain="email",
            source_id="email_100",
        )

        related = cross_domain_service.get_related_items(
            context.correlation_id
        )

        source_items = [
            item for item in related if item["domain"] == "email"
        ]
        assert len(source_items) >= 1

    def test_get_related_items_nonexistent(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test getting related items for nonexistent correlation."""
        related = cross_domain_service.get_related_items("nonexistent")
        assert related == []


class TestSearchAcrossDomains:
    """Tests for CrossDomainService.search_across_domains."""

    def test_search_finds_matching_items(
        self, cross_domain_service: CrossDomainService, vault_path: Path
    ) -> None:
        """Test searching across domains finds matching items."""
        # Create some files with searchable content
        inbox = vault_path / "Inbox"
        inbox.mkdir(exist_ok=True)
        (inbox / "test_item.md").write_text(
            "---\nid: item_1\n---\n\nProduct launch meeting notes"
        )

        done = vault_path / "Done"
        done.mkdir(exist_ok=True)
        (done / "done_item.md").write_text(
            "---\nid: item_2\n---\n\nProduct launch completed"
        )

        results = cross_domain_service.search_across_domains(
            query="product launch"
        )

        assert len(results) >= 1

    def test_search_with_domain_filter(
        self, cross_domain_service: CrossDomainService, vault_path: Path
    ) -> None:
        """Test searching with domain filter."""
        inbox = vault_path / "Inbox"
        inbox.mkdir(exist_ok=True)
        (inbox / "email_item.md").write_text(
            "---\nid: e1\n---\n\nEmail about budget"
        )

        social = vault_path / "Social" / "Meta" / "posts"
        social.mkdir(parents=True, exist_ok=True)
        (social / "social_item.md").write_text(
            "---\nid: s1\n---\n\nSocial post about budget"
        )

        results = cross_domain_service.search_across_domains(
            query="budget",
            domains=["inbox"],
        )

        # Should find results only from inbox domain
        inbox_results = [
            r for r in results if r.get("domain") == "inbox"
        ]
        assert len(inbox_results) >= 1

    def test_search_empty_query(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test searching with empty query."""
        results = cross_domain_service.search_across_domains(query="")
        assert results == []

    def test_search_no_results(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test searching with no matching results."""
        results = cross_domain_service.search_across_domains(
            query="xyznonexistent123"
        )
        assert results == []


class TestGetRelationshipGraph:
    """Tests for CrossDomainService.get_relationship_graph."""

    def test_empty_graph(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test getting graph with no correlations."""
        graph = cross_domain_service.get_relationship_graph()

        assert "nodes" in graph
        assert "edges" in graph
        assert isinstance(graph["nodes"], list)
        assert isinstance(graph["edges"], list)

    def test_graph_with_correlations(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test getting graph with correlations."""
        ctx = cross_domain_service.create_correlation(
            source_domain="email",
            source_id="email_1",
        )
        cross_domain_service.link_items(
            ctx.correlation_id, "social", "post_1"
        )
        cross_domain_service.link_items(
            ctx.correlation_id, "task", "task_1"
        )

        graph = cross_domain_service.get_relationship_graph()

        assert len(graph["nodes"]) >= 3
        assert len(graph["edges"]) >= 2

    def test_graph_multiple_correlations(
        self, cross_domain_service: CrossDomainService
    ) -> None:
        """Test graph with multiple correlation chains."""
        ctx1 = cross_domain_service.create_correlation(
            source_domain="email",
            source_id="email_1",
        )
        cross_domain_service.link_items(
            ctx1.correlation_id, "social", "post_1"
        )

        ctx2 = cross_domain_service.create_correlation(
            source_domain="task",
            source_id="task_1",
        )
        cross_domain_service.link_items(
            ctx2.correlation_id, "meta", "fb_1"
        )

        graph = cross_domain_service.get_relationship_graph()

        assert len(graph["nodes"]) >= 4
        assert len(graph["edges"]) >= 2
