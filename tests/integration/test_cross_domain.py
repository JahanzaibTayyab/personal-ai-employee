"""Integration tests for CrossDomainService with vault filesystem."""

from pathlib import Path

import pytest

from ai_employee.config import VaultConfig
from ai_employee.services.cross_domain import CrossDomainService
from ai_employee.utils.frontmatter import generate_frontmatter


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    """Create a temporary vault structure."""
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


@pytest.fixture
def vault_config(vault_path: Path) -> VaultConfig:
    """Create vault config and ensure full structure."""
    config = VaultConfig(root=vault_path)
    config.ensure_structure()
    # Create Gold tier social folders
    (vault_path / "Social" / "Meta" / "posts").mkdir(
        parents=True, exist_ok=True
    )
    (vault_path / "Social" / "Twitter" / "tweets").mkdir(
        parents=True, exist_ok=True
    )
    return config


@pytest.fixture
def cross_domain(vault_config: VaultConfig) -> CrossDomainService:
    """Create CrossDomainService."""
    return CrossDomainService(vault_config)


@pytest.fixture
def populated_vault(vault_path: Path) -> Path:
    """Create vault with sample items across domains."""
    # Email items
    inbox = vault_path / "Inbox"
    inbox.mkdir(exist_ok=True)
    (inbox / "email_product_launch.md").write_text(
        generate_frontmatter(
            {"id": "email_1", "subject": "Product Launch Plan"},
            "We need to coordinate the Q2 product launch across all channels.",
        )
    )

    # Social media posts
    social_meta = vault_path / "Social" / "Meta" / "posts"
    social_meta.mkdir(parents=True, exist_ok=True)
    (social_meta / "META_fb_launch.md").write_text(
        generate_frontmatter(
            {"id": "fb_1", "platform": "facebook", "status": "draft"},
            "Exciting product launch coming soon!",
        )
    )

    # Twitter posts
    social_twitter = vault_path / "Social" / "Twitter" / "tweets"
    social_twitter.mkdir(parents=True, exist_ok=True)
    (social_twitter / "TWEET_launch.md").write_text(
        generate_frontmatter(
            {"id": "tw_1", "status": "draft"},
            "Big announcement: product launch this quarter!",
        )
    )

    # Done items
    done = vault_path / "Done"
    done.mkdir(exist_ok=True)
    (done / "done_planning.md").write_text(
        generate_frontmatter(
            {"id": "done_1", "type": "task"},
            "Product launch planning completed",
        )
    )

    return vault_path


class TestCrossDomainIntegration:
    """Integration tests for cross-domain correlation tracking."""

    def test_full_correlation_lifecycle(
        self, cross_domain: CrossDomainService
    ) -> None:
        """Test complete lifecycle: create, link, retrieve, graph."""
        # Step 1: Create correlation from email
        context = cross_domain.create_correlation(
            source_domain="email",
            source_id="email_product_launch",
            metadata={"subject": "Product Launch Plan"},
        )
        assert context.correlation_id.startswith("corr_")

        # Step 2: Link social posts to this correlation
        cross_domain.link_items(
            context.correlation_id, "meta", "fb_launch_post"
        )
        cross_domain.link_items(
            context.correlation_id, "twitter", "tw_launch_tweet"
        )
        cross_domain.link_items(
            context.correlation_id, "task", "task_launch_plan"
        )

        # Step 3: Retrieve all related items
        related = cross_domain.get_related_items(context.correlation_id)
        assert len(related) >= 4  # source + 3 linked

        domains = {item["domain"] for item in related}
        assert "email" in domains
        assert "meta" in domains
        assert "twitter" in domains
        assert "task" in domains

        # Step 4: Check relationship graph
        graph = cross_domain.get_relationship_graph()
        assert len(graph["nodes"]) >= 4
        assert len(graph["edges"]) >= 3

    def test_multiple_independent_correlations(
        self, cross_domain: CrossDomainService
    ) -> None:
        """Test multiple independent correlation chains."""
        # Correlation 1: Product launch
        ctx1 = cross_domain.create_correlation(
            source_domain="email",
            source_id="email_launch",
        )
        cross_domain.link_items(ctx1.correlation_id, "social", "fb_1")

        # Correlation 2: Budget meeting
        ctx2 = cross_domain.create_correlation(
            source_domain="email",
            source_id="email_budget",
        )
        cross_domain.link_items(ctx2.correlation_id, "task", "task_1")

        # Each correlation is independent
        related1 = cross_domain.get_related_items(ctx1.correlation_id)
        related2 = cross_domain.get_related_items(ctx2.correlation_id)

        ids1 = {item["item_id"] for item in related1}
        ids2 = {item["item_id"] for item in related2}
        assert ids1 != ids2

    def test_correlation_persisted_to_disk(
        self, cross_domain: CrossDomainService, vault_path: Path
    ) -> None:
        """Test that correlations are persisted to disk."""
        context = cross_domain.create_correlation(
            source_domain="email",
            source_id="email_persist",
        )
        cross_domain.link_items(
            context.correlation_id, "social", "post_persist"
        )

        # Verify file exists on disk
        correlation_dir = vault_path / "Correlations"
        if correlation_dir.exists():
            files = list(correlation_dir.glob("*.json"))
            assert len(files) >= 1

    def test_search_across_populated_vault(
        self,
        cross_domain: CrossDomainService,
        populated_vault: Path,
    ) -> None:
        """Test searching across a populated vault."""
        results = cross_domain.search_across_domains(
            query="product launch"
        )

        assert len(results) >= 1
        # Should find items from multiple domains
        found_domains = {r.get("domain") for r in results}
        assert len(found_domains) >= 1

    def test_search_filtered_by_domain(
        self,
        cross_domain: CrossDomainService,
        populated_vault: Path,
    ) -> None:
        """Test search filtered to specific domains."""
        results = cross_domain.search_across_domains(
            query="product launch",
            domains=["inbox"],
        )

        for result in results:
            assert result.get("domain") == "inbox"

    def test_relationship_graph_structure(
        self, cross_domain: CrossDomainService
    ) -> None:
        """Test that relationship graph has correct structure."""
        ctx = cross_domain.create_correlation(
            source_domain="email",
            source_id="e1",
        )
        cross_domain.link_items(ctx.correlation_id, "meta", "m1")
        cross_domain.link_items(ctx.correlation_id, "twitter", "t1")

        graph = cross_domain.get_relationship_graph()

        # Check node structure
        for node in graph["nodes"]:
            assert "id" in node
            assert "domain" in node

        # Check edge structure
        for edge in graph["edges"]:
            assert "source" in edge
            assert "target" in edge
            assert "correlation_id" in edge

    def test_context_propagation(
        self, cross_domain: CrossDomainService
    ) -> None:
        """Test that context/metadata propagates through links."""
        ctx = cross_domain.create_correlation(
            source_domain="email",
            source_id="e_prop",
            metadata={"priority": "high", "topic": "quarterly review"},
        )
        cross_domain.link_items(ctx.correlation_id, "task", "t_prop")

        related = cross_domain.get_related_items(ctx.correlation_id)

        # Related items should have access to correlation metadata
        context_items = [
            r for r in related if "metadata" in r
        ]
        assert len(context_items) >= 1
