"""Cross-domain integration service with correlation tracking.

Links related items across domains (email, social, tasks) using
correlation IDs and provides unified search and relationship graphing.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_employee.config import VaultConfig
from ai_employee.utils.correlation import CorrelationContext
from ai_employee.utils.frontmatter import parse_frontmatter
from ai_employee.utils.jsonl_logger import JsonlLogger

logger = logging.getLogger(__name__)

# Domain-to-directory mapping for search
DOMAIN_DIRECTORY_MAP = {
    "inbox": "Inbox",
    "done": "Done",
    "needs_action": "Needs_Action",
    "quarantine": "Quarantine",
    "email": "Needs_Action/Email",
    "social": "Social",
    "meta": "Social/Meta/posts",
    "twitter": "Social/Twitter/tweets",
    "linkedin": "Social/LinkedIn/posts",
    "plans": "Plans",
    "briefings": "Briefings",
    "task": "Plans",
    "pending_approval": "Pending_Approval",
    "approved": "Approved",
    "rejected": "Rejected",
}


class CrossDomainService:
    """Service for cross-domain integration and correlation tracking.

    Features (FR-043 to FR-046):
    - Link related items across domains using correlation IDs
    - Propagate context when items move between domains
    - Unified search across vaults
    - Relationship graph for briefing
    """

    def __init__(self, vault_config: VaultConfig) -> None:
        """Initialize the cross-domain service.

        Args:
            vault_config: Vault configuration with paths
        """
        self._config = vault_config
        self._correlations_dir = vault_config.root / "Correlations"
        self._correlations_dir.mkdir(parents=True, exist_ok=True)
        self._logger = JsonlLogger[dict](
            logs_dir=vault_config.logs,
            prefix="cross_domain",
            serializer=lambda e: str(e),
            deserializer=lambda s: {},
        )

    def _log_operation(
        self,
        operation: str,
        success: bool,
        details: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Log a cross-domain operation."""
        entry: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "success": success,
        }
        if details:
            entry.update(details)
        if error:
            entry["error"] = error
        self._logger.log(entry)

    def create_correlation(
        self,
        source_domain: str,
        source_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> CorrelationContext:
        """Create a new correlation context.

        Args:
            source_domain: Domain that initiated the correlation
            source_id: ID of the source item
            metadata: Optional metadata for the correlation

        Returns:
            New CorrelationContext instance
        """
        context = CorrelationContext.create(
            source_domain=source_domain,
            source_id=source_id,
            metadata=metadata,
        )

        self._save_correlation(context)
        self._log_operation("create_correlation", True, {
            "correlation_id": context.correlation_id,
            "source_domain": source_domain,
            "source_id": source_id,
        })

        return context

    def link_items(
        self,
        correlation_id: str,
        domain: str,
        item_id: str,
    ) -> None:
        """Link an item to an existing correlation.

        Args:
            correlation_id: Correlation ID to link to
            domain: Domain of the item to link
            item_id: ID of the item to link

        Raises:
            ValueError: If correlation not found
        """
        context = self._load_correlation(correlation_id)
        if context is None:
            raise ValueError(
                f"Correlation not found: {correlation_id}"
            )

        updated = context.add_linked_item(domain, item_id)
        self._save_correlation(updated)

        self._log_operation("link_items", True, {
            "correlation_id": correlation_id,
            "domain": domain,
            "item_id": item_id,
        })

    def get_related_items(
        self,
        correlation_id: str,
    ) -> list[dict[str, Any]]:
        """Get all items related through a correlation.

        Args:
            correlation_id: Correlation ID to look up

        Returns:
            List of related item dicts with domain, item_id, and metadata
        """
        context = self._load_correlation(correlation_id)
        if context is None:
            return []

        items: list[dict[str, Any]] = []

        # Include the source item
        items.append({
            "domain": context.source_domain,
            "item_id": context.source_id,
            "is_source": True,
            "metadata": context.metadata,
        })

        # Include all linked items
        for linked in context.linked_items:
            items.append({
                "domain": linked["domain"],
                "item_id": linked["item_id"],
                "is_source": False,
                "metadata": context.metadata,
            })

        return items

    def search_across_domains(
        self,
        query: str,
        domains: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for items across all vault domains.

        Args:
            query: Search query string
            domains: Optional list of domains to search in

        Returns:
            List of matching items with domain, file, and content
        """
        if not query:
            return []

        query_lower = query.lower()
        results: list[dict[str, Any]] = []

        search_dirs = self._get_search_directories(domains)

        for domain_name, dir_path in search_dirs:
            if not dir_path.exists():
                continue

            for file_path in dir_path.glob("*.md"):
                try:
                    content = file_path.read_text()
                    if query_lower in content.lower():
                        frontmatter, body = parse_frontmatter(content)
                        results.append({
                            "domain": domain_name,
                            "file": str(file_path),
                            "id": frontmatter.get("id", file_path.stem),
                            "content_preview": body[:200] if body else "",
                            "frontmatter": frontmatter,
                        })
                except Exception as e:
                    logger.warning(
                        "Error reading %s: %s", file_path, e
                    )

        self._log_operation("search", True, {
            "query": query,
            "result_count": len(results),
        })

        return results

    def get_relationship_graph(self) -> dict[str, Any]:
        """Build a relationship graph from all correlations.

        Returns:
            Dict with 'nodes' and 'edges' lists for visualization
        """
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        seen_nodes: set[str] = set()

        for file_path in self._correlations_dir.glob("*.json"):
            try:
                data = json.loads(file_path.read_text())
                context = CorrelationContext.from_dict(data)

                # Add source node
                source_key = f"{context.source_domain}:{context.source_id}"
                if source_key not in seen_nodes:
                    nodes.append({
                        "id": source_key,
                        "domain": context.source_domain,
                        "item_id": context.source_id,
                    })
                    seen_nodes.add(source_key)

                # Add linked nodes and edges
                for linked in context.linked_items:
                    linked_key = (
                        f"{linked['domain']}:{linked['item_id']}"
                    )
                    if linked_key not in seen_nodes:
                        nodes.append({
                            "id": linked_key,
                            "domain": linked["domain"],
                            "item_id": linked["item_id"],
                        })
                        seen_nodes.add(linked_key)

                    edges.append({
                        "source": source_key,
                        "target": linked_key,
                        "correlation_id": context.correlation_id,
                    })

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(
                    "Error reading correlation %s: %s",
                    file_path,
                    e,
                )

        return {"nodes": nodes, "edges": edges}

    def _get_search_directories(
        self,
        domains: list[str] | None = None,
    ) -> list[tuple[str, Path]]:
        """Get directories to search based on domain filter.

        Args:
            domains: Optional domain filter list

        Returns:
            List of (domain_name, directory_path) tuples
        """
        if domains:
            return [
                (d, self._config.root / DOMAIN_DIRECTORY_MAP[d])
                for d in domains
                if d in DOMAIN_DIRECTORY_MAP
            ]

        return [
            (name, self._config.root / path)
            for name, path in DOMAIN_DIRECTORY_MAP.items()
        ]

    def _save_correlation(self, context: CorrelationContext) -> None:
        """Persist a correlation context to disk."""
        file_path = (
            self._correlations_dir
            / f"{context.correlation_id}.json"
        )
        file_path.write_text(
            json.dumps(context.to_dict(), indent=2, default=str)
        )

    def _load_correlation(
        self,
        correlation_id: str,
    ) -> CorrelationContext | None:
        """Load a correlation context from disk.

        Args:
            correlation_id: Correlation ID to load

        Returns:
            CorrelationContext if found, None otherwise
        """
        file_path = (
            self._correlations_dir / f"{correlation_id}.json"
        )
        if not file_path.exists():
            return None

        try:
            data = json.loads(file_path.read_text())
            return CorrelationContext.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                "Error loading correlation %s: %s",
                correlation_id,
                e,
            )
            return None
