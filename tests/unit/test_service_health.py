"""Tests for ServiceHealth model."""

from datetime import datetime

import pytest

from ai_employee.models.enums import ErrorCategory, HealthStatus
from ai_employee.models.service_health import ServiceHealth


class TestServiceHealth:
    """Tests for the ServiceHealth dataclass."""

    def test_create_service_health_with_defaults(self) -> None:
        """Test creating ServiceHealth with default values."""
        health = ServiceHealth(
            service_name="gmail",
            display_name="Gmail API",
        )

        assert health.service_name == "gmail"
        assert health.display_name == "Gmail API"
        assert health.status == HealthStatus.UNKNOWN
        assert health.last_check is None
        assert health.last_success is None
        assert health.consecutive_failures == 0
        assert health.last_error is None
        assert health.error_category is None
        assert health.is_critical is False
        assert health.queued_operations == 0

    def test_create_service_health_with_all_fields(self) -> None:
        """Test creating ServiceHealth with all fields specified."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        health = ServiceHealth(
            service_name="odoo",
            display_name="Odoo ERP",
            status=HealthStatus.HEALTHY,
            last_check=now,
            last_success=now,
            consecutive_failures=0,
            last_error=None,
            error_category=None,
            is_critical=True,
            queued_operations=5,
        )

        assert health.service_name == "odoo"
        assert health.display_name == "Odoo ERP"
        assert health.status == HealthStatus.HEALTHY
        assert health.last_check == now
        assert health.last_success == now
        assert health.consecutive_failures == 0
        assert health.is_critical is True
        assert health.queued_operations == 5

    def test_service_health_with_failure_state(self) -> None:
        """Test ServiceHealth representing a failed service."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        health = ServiceHealth(
            service_name="meta",
            display_name="Meta API",
            status=HealthStatus.DOWN,
            last_check=now,
            last_success=None,
            consecutive_failures=3,
            last_error="Connection timeout",
            error_category=ErrorCategory.TRANSIENT,
            is_critical=False,
            queued_operations=12,
        )

        assert health.status == HealthStatus.DOWN
        assert health.consecutive_failures == 3
        assert health.last_error == "Connection timeout"
        assert health.error_category == ErrorCategory.TRANSIENT
        assert health.queued_operations == 12

    def test_service_health_to_dict(self) -> None:
        """Test converting ServiceHealth to dictionary."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        health = ServiceHealth(
            service_name="gmail",
            display_name="Gmail API",
            status=HealthStatus.HEALTHY,
            last_check=now,
            last_success=now,
            consecutive_failures=0,
            is_critical=True,
        )

        result = health.to_dict()

        assert result["service_name"] == "gmail"
        assert result["display_name"] == "Gmail API"
        assert result["status"] == "healthy"
        assert result["last_check"] == now.isoformat()
        assert result["last_success"] == now.isoformat()
        assert result["consecutive_failures"] == 0
        assert result["is_critical"] is True
        assert result["queued_operations"] == 0

    def test_service_health_to_dict_with_none_values(self) -> None:
        """Test converting ServiceHealth with None values to dictionary."""
        health = ServiceHealth(
            service_name="twitter",
            display_name="Twitter API",
        )

        result = health.to_dict()

        assert result["service_name"] == "twitter"
        assert result["last_check"] is None
        assert result["last_success"] is None
        assert result["last_error"] is None
        assert result["error_category"] is None

    def test_service_health_from_dict(self) -> None:
        """Test creating ServiceHealth from a dictionary."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        data = {
            "service_name": "linkedin",
            "display_name": "LinkedIn API",
            "status": "degraded",
            "last_check": now.isoformat(),
            "last_success": now.isoformat(),
            "consecutive_failures": 1,
            "last_error": "Rate limited",
            "error_category": "transient",
            "is_critical": False,
            "queued_operations": 3,
        }

        health = ServiceHealth.from_dict(data)

        assert health.service_name == "linkedin"
        assert health.display_name == "LinkedIn API"
        assert health.status == HealthStatus.DEGRADED
        assert health.last_check == now
        assert health.consecutive_failures == 1
        assert health.last_error == "Rate limited"
        assert health.error_category == ErrorCategory.TRANSIENT

    def test_service_health_from_dict_with_missing_optionals(self) -> None:
        """Test creating ServiceHealth from dict with missing optional fields."""
        data = {
            "service_name": "filesystem",
            "display_name": "File System",
            "status": "healthy",
            "consecutive_failures": 0,
            "is_critical": True,
            "queued_operations": 0,
        }

        health = ServiceHealth.from_dict(data)

        assert health.service_name == "filesystem"
        assert health.last_check is None
        assert health.last_success is None
        assert health.last_error is None
        assert health.error_category is None

    def test_service_health_roundtrip(self) -> None:
        """Test that to_dict and from_dict are inverses."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        original = ServiceHealth(
            service_name="whatsapp",
            display_name="WhatsApp API",
            status=HealthStatus.DEGRADED,
            last_check=now,
            last_success=now,
            consecutive_failures=2,
            last_error="Slow response",
            error_category=ErrorCategory.TRANSIENT,
            is_critical=False,
            queued_operations=7,
        )

        data = original.to_dict()
        restored = ServiceHealth.from_dict(data)

        assert restored.service_name == original.service_name
        assert restored.display_name == original.display_name
        assert restored.status == original.status
        assert restored.last_check == original.last_check
        assert restored.last_success == original.last_success
        assert restored.consecutive_failures == original.consecutive_failures
        assert restored.last_error == original.last_error
        assert restored.error_category == original.error_category
        assert restored.is_critical == original.is_critical
        assert restored.queued_operations == original.queued_operations

    def test_all_known_service_names(self) -> None:
        """Test creating ServiceHealth for all tracked services."""
        known_services = [
            ("gmail", "Gmail API"),
            ("odoo", "Odoo ERP"),
            ("meta", "Meta API"),
            ("twitter", "Twitter API"),
            ("linkedin", "LinkedIn API"),
            ("whatsapp", "WhatsApp API"),
            ("filesystem", "File System"),
        ]

        for name, display in known_services:
            health = ServiceHealth(service_name=name, display_name=display)
            assert health.service_name == name
            assert health.display_name == display
