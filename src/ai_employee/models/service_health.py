"""ServiceHealth model for tracking external service status."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ai_employee.models.enums import ErrorCategory, HealthStatus


@dataclass
class ServiceHealth:
    """Tracks the health status of an external service.

    Used by ErrorRecoveryService to manage degraded functionality
    and dashboard alerts.

    Services tracked: gmail, odoo, meta, twitter, linkedin, whatsapp, filesystem
    """

    service_name: str
    display_name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check: datetime | None = None
    last_success: datetime | None = None
    consecutive_failures: int = 0
    last_error: str | None = None
    error_category: ErrorCategory | None = None
    is_critical: bool = False
    queued_operations: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert ServiceHealth to a dictionary for serialization.

        Returns:
            Dictionary representation of the service health.
        """
        return {
            "service_name": self.service_name,
            "display_name": self.display_name,
            "status": self.status.value,
            "last_check": (
                self.last_check.isoformat() if self.last_check else None
            ),
            "last_success": (
                self.last_success.isoformat() if self.last_success else None
            ),
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error,
            "error_category": (
                self.error_category.value if self.error_category else None
            ),
            "is_critical": self.is_critical,
            "queued_operations": self.queued_operations,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServiceHealth":
        """Create ServiceHealth from a dictionary.

        Args:
            data: Dictionary with service health data.

        Returns:
            ServiceHealth instance.
        """
        last_check_raw = data.get("last_check")
        last_success_raw = data.get("last_success")
        error_category_raw = data.get("error_category")

        return cls(
            service_name=data["service_name"],
            display_name=data["display_name"],
            status=HealthStatus(data["status"]),
            last_check=(
                datetime.fromisoformat(last_check_raw)
                if last_check_raw
                else None
            ),
            last_success=(
                datetime.fromisoformat(last_success_raw)
                if last_success_raw
                else None
            ),
            consecutive_failures=data.get("consecutive_failures", 0),
            last_error=data.get("last_error"),
            error_category=(
                ErrorCategory(error_category_raw)
                if error_category_raw
                else None
            ),
            is_critical=data.get("is_critical", False),
            queued_operations=data.get("queued_operations", 0),
        )
