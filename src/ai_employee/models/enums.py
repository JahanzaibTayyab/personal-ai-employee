"""Gold tier enum definitions shared across models."""

from enum import Enum


class TaskStatus(str, Enum):
    """Status of a Ralph Wiggum autonomous task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class InvoiceStatus(str, Enum):
    """Status of an Odoo invoice."""

    DRAFT = "draft"
    POSTED = "posted"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    """Status of an Odoo payment."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PostStatus(str, Enum):
    """Status of a social media post (Meta or Twitter)."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHING = "publishing"
    POSTED = "posted"
    FAILED = "failed"
    DELETED = "deleted"


class HealthStatus(str, Enum):
    """Health status of an external service."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class ErrorCategory(str, Enum):
    """Category of error for classification and recovery."""

    TRANSIENT = "transient"
    AUTHENTICATION = "authentication"
    LOGIC = "logic"
    DATA = "data"
    SYSTEM = "system"
