"""Correlation ID utilities for cross-domain action tracking."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for linking related actions.

    Returns:
        UUID-based correlation ID string
    """
    return f"corr_{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True)
class CorrelationContext:
    """Immutable context that travels with a correlation ID across services.

    Attributes:
        correlation_id: Unique ID linking related actions
        source_domain: Where the action originated (email, whatsapp, social, etc.)
        source_id: ID of the originating item
        created_at: When the correlation was established
        parent_correlation_id: For nested correlations
        metadata: Additional context key-value pairs
        linked_items: Items linked to this correlation across domains
    """

    correlation_id: str
    source_domain: str
    source_id: str
    created_at: datetime = field(default_factory=datetime.now)
    parent_correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    linked_items: tuple[dict[str, str], ...] = field(default_factory=tuple)

    @classmethod
    def create(
        cls,
        source_domain: str,
        source_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> CorrelationContext:
        """Create a new correlation context with a generated ID.

        Args:
            source_domain: Domain that initiated the correlation
            source_id: ID of the source item
            metadata: Optional metadata for the correlation

        Returns:
            New CorrelationContext instance
        """
        return cls(
            correlation_id=generate_correlation_id(),
            source_domain=source_domain,
            source_id=source_id,
            metadata=metadata or {},
        )

    def with_metadata(self, key: str, value: str) -> CorrelationContext:
        """Create a new context with additional metadata.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            New CorrelationContext with updated metadata
        """
        return CorrelationContext(
            correlation_id=self.correlation_id,
            source_domain=self.source_domain,
            source_id=self.source_id,
            created_at=self.created_at,
            parent_correlation_id=self.parent_correlation_id,
            metadata={**self.metadata, key: value},
            linked_items=self.linked_items,
        )

    def create_child(self, domain: str, source_id: str) -> CorrelationContext:
        """Create a child correlation context for a downstream action.

        Args:
            domain: Domain of the child action
            source_id: ID of the child item

        Returns:
            New CorrelationContext linked to this one as parent
        """
        return CorrelationContext(
            correlation_id=generate_correlation_id(),
            source_domain=domain,
            source_id=source_id,
            parent_correlation_id=self.correlation_id,
        )

    def add_linked_item(self, domain: str, item_id: str) -> CorrelationContext:
        """Add a linked item to this correlation context.

        Returns a new context with the linked item added (immutable).

        Args:
            domain: Domain of the linked item
            item_id: ID of the linked item

        Returns:
            New CorrelationContext with the linked item added
        """
        return CorrelationContext(
            correlation_id=self.correlation_id,
            source_domain=self.source_domain,
            source_id=self.source_id,
            created_at=self.created_at,
            parent_correlation_id=self.parent_correlation_id,
            metadata=dict(self.metadata),
            linked_items=(
                *self.linked_items,
                {"domain": domain, "item_id": item_id},
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for storage.

        Returns:
            Dictionary representation
        """
        return {
            "correlation_id": self.correlation_id,
            "source_domain": self.source_domain,
            "source_id": self.source_id,
            "created_at": self.created_at.isoformat(),
            "parent_correlation_id": self.parent_correlation_id,
            "metadata": dict(self.metadata),
            "linked_items": list(self.linked_items),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CorrelationContext:
        """Create from dictionary.

        Args:
            data: Dictionary with correlation context data

        Returns:
            CorrelationContext instance
        """
        return cls(
            correlation_id=data["correlation_id"],
            source_domain=data["source_domain"],
            source_id=data["source_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            parent_correlation_id=data.get("parent_correlation_id"),
            metadata=data.get("metadata", {}),
            linked_items=tuple(data.get("linked_items", [])),
        )
