"""Tests for ErrorRecoveryService."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.enums import ErrorCategory, HealthStatus
from ai_employee.models.service_health import ServiceHealth
from ai_employee.services.error_recovery import ErrorRecoveryService


@pytest.fixture
def vault_config(tmp_path: Path) -> VaultConfig:
    """Create a temporary vault config for testing."""
    config = VaultConfig(root=tmp_path)
    config.ensure_structure()
    return config


@pytest.fixture
def recovery_service(vault_config: VaultConfig) -> ErrorRecoveryService:
    """Create an ErrorRecoveryService for testing."""
    return ErrorRecoveryService(vault_config)


class TestRegisterService:
    """Tests for service registration."""

    def test_register_new_service(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test registering a new service returns ServiceHealth."""
        health = recovery_service.register_service(
            name="gmail",
            display_name="Gmail API",
            is_critical=True,
        )

        assert health.service_name == "gmail"
        assert health.display_name == "Gmail API"
        assert health.is_critical is True
        assert health.status == HealthStatus.UNKNOWN
        assert health.consecutive_failures == 0

    def test_register_service_default_not_critical(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test registering a service defaults to non-critical."""
        health = recovery_service.register_service(
            name="twitter",
            display_name="Twitter API",
        )

        assert health.is_critical is False

    def test_register_duplicate_service_returns_existing(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test registering a service with same name returns existing health."""
        first = recovery_service.register_service(
            name="gmail",
            display_name="Gmail API",
            is_critical=True,
        )
        second = recovery_service.register_service(
            name="gmail",
            display_name="Gmail API Updated",
            is_critical=False,
        )

        assert second.service_name == "gmail"
        # Should return existing, not overwrite
        assert second.display_name == "Gmail API"
        assert second.is_critical is True


class TestRecordSuccess:
    """Tests for recording successful operations."""

    def test_record_success_updates_status(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that recording success sets status to HEALTHY."""
        recovery_service.register_service("gmail", "Gmail API")

        health = recovery_service.record_success("gmail")

        assert health.status == HealthStatus.HEALTHY
        assert health.last_success is not None
        assert health.last_check is not None
        assert health.consecutive_failures == 0

    def test_record_success_resets_failures(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that success resets consecutive failure count."""
        recovery_service.register_service("gmail", "Gmail API")
        recovery_service.record_failure(
            "gmail", ConnectionError("timeout")
        )
        recovery_service.record_failure(
            "gmail", ConnectionError("timeout")
        )

        health = recovery_service.record_success("gmail")

        assert health.consecutive_failures == 0
        assert health.last_error is None
        assert health.error_category is None

    def test_record_success_unregistered_service_raises(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that recording success for unknown service raises error."""
        with pytest.raises(KeyError, match="unknown_service"):
            recovery_service.record_success("unknown_service")


class TestRecordFailure:
    """Tests for recording failed operations."""

    def test_record_failure_increments_count(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that failure increments consecutive failure count."""
        recovery_service.register_service("gmail", "Gmail API")

        health = recovery_service.record_failure(
            "gmail", ConnectionError("timeout")
        )

        assert health.consecutive_failures == 1
        assert health.last_error is not None
        assert health.last_check is not None

    def test_record_failure_classifies_error(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that failure classifies the error category."""
        recovery_service.register_service("gmail", "Gmail API")

        health = recovery_service.record_failure(
            "gmail", ConnectionError("Connection timeout")
        )

        assert health.error_category == ErrorCategory.TRANSIENT

    def test_record_failure_sets_degraded_after_one(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that first failure sets status to DEGRADED."""
        recovery_service.register_service("gmail", "Gmail API")

        health = recovery_service.record_failure(
            "gmail", ConnectionError("timeout")
        )

        assert health.status == HealthStatus.DEGRADED

    def test_record_failure_sets_down_after_three(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that three consecutive failures set status to DOWN."""
        recovery_service.register_service("gmail", "Gmail API")

        recovery_service.record_failure(
            "gmail", ConnectionError("timeout")
        )
        recovery_service.record_failure(
            "gmail", ConnectionError("timeout")
        )
        health = recovery_service.record_failure(
            "gmail", ConnectionError("timeout")
        )

        assert health.status == HealthStatus.DOWN

    def test_record_failure_unregistered_service_raises(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that recording failure for unknown service raises error."""
        with pytest.raises(KeyError, match="unknown_service"):
            recovery_service.record_failure(
                "unknown_service", RuntimeError("test")
            )

    def test_record_auth_failure(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test recording an authentication failure."""
        recovery_service.register_service("gmail", "Gmail API")

        health = recovery_service.record_failure(
            "gmail",
            PermissionError("Unauthorized: token expired"),
        )

        assert health.error_category == ErrorCategory.AUTHENTICATION


class TestGetHealth:
    """Tests for getting service health status."""

    def test_get_health_registered_service(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test getting health of a registered service."""
        recovery_service.register_service("gmail", "Gmail API")

        health = recovery_service.get_health("gmail")

        assert health.service_name == "gmail"
        assert health.status == HealthStatus.UNKNOWN

    def test_get_health_unregistered_raises(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test getting health of unknown service raises error."""
        with pytest.raises(KeyError, match="unknown"):
            recovery_service.get_health("unknown")

    def test_get_all_health(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test getting health of all registered services."""
        recovery_service.register_service("gmail", "Gmail API")
        recovery_service.register_service("odoo", "Odoo ERP")

        all_health = recovery_service.get_all_health()

        assert len(all_health) == 2
        names = {h.service_name for h in all_health}
        assert names == {"gmail", "odoo"}


class TestServiceAvailability:
    """Tests for checking service availability."""

    def test_unknown_service_is_available(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that UNKNOWN status is treated as available."""
        recovery_service.register_service("gmail", "Gmail API")

        assert recovery_service.is_service_available("gmail") is True

    def test_healthy_service_is_available(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that HEALTHY status is available."""
        recovery_service.register_service("gmail", "Gmail API")
        recovery_service.record_success("gmail")

        assert recovery_service.is_service_available("gmail") is True

    def test_degraded_service_is_available(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that DEGRADED status is still available."""
        recovery_service.register_service("gmail", "Gmail API")
        recovery_service.record_failure(
            "gmail", ConnectionError("slow")
        )

        assert recovery_service.is_service_available("gmail") is True

    def test_down_service_is_not_available(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that DOWN status is not available."""
        recovery_service.register_service("gmail", "Gmail API")
        for _ in range(3):
            recovery_service.record_failure(
                "gmail", ConnectionError("timeout")
            )

        assert recovery_service.is_service_available("gmail") is False

    def test_unregistered_service_is_not_available(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that unregistered service is not available."""
        assert recovery_service.is_service_available("unknown") is False


class TestDegradedServices:
    """Tests for getting degraded services."""

    def test_no_degraded_services_initially(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that no services are degraded initially."""
        recovery_service.register_service("gmail", "Gmail API")

        degraded = recovery_service.get_degraded_services()

        assert len(degraded) == 0

    def test_degraded_service_appears_in_list(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that degraded service appears in degraded list."""
        recovery_service.register_service("gmail", "Gmail API")
        recovery_service.record_failure(
            "gmail", ConnectionError("timeout")
        )

        degraded = recovery_service.get_degraded_services()

        assert len(degraded) == 1
        assert degraded[0].service_name == "gmail"

    def test_down_service_appears_in_degraded_list(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that DOWN service also appears in degraded list."""
        recovery_service.register_service("gmail", "Gmail API")
        for _ in range(3):
            recovery_service.record_failure(
                "gmail", ConnectionError("timeout")
            )

        degraded = recovery_service.get_degraded_services()

        assert len(degraded) == 1
        assert degraded[0].status == HealthStatus.DOWN

    def test_healthy_service_not_in_degraded_list(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that healthy services are not in degraded list."""
        recovery_service.register_service("gmail", "Gmail API")
        recovery_service.register_service("odoo", "Odoo ERP")
        recovery_service.record_success("gmail")
        recovery_service.record_failure(
            "odoo", ConnectionError("timeout")
        )

        degraded = recovery_service.get_degraded_services()

        assert len(degraded) == 1
        assert degraded[0].service_name == "odoo"


class TestQueueFailedOperation:
    """Tests for queuing failed operations."""

    def test_queue_operation_returns_id(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that queuing an operation returns a unique ID."""
        recovery_service.register_service("gmail", "Gmail API")

        op_id = recovery_service.queue_failed_operation(
            service_name="gmail",
            operation_type="send_email",
            parameters={"to": "user@example.com", "subject": "Test"},
        )

        assert op_id is not None
        assert isinstance(op_id, str)
        assert len(op_id) > 0

    def test_queue_operation_increments_count(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that queuing an operation increments the queued count."""
        recovery_service.register_service("gmail", "Gmail API")

        recovery_service.queue_failed_operation(
            service_name="gmail",
            operation_type="send_email",
            parameters={"to": "user@example.com"},
        )

        health = recovery_service.get_health("gmail")
        assert health.queued_operations == 1

    def test_queue_multiple_operations(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test queuing multiple operations for the same service."""
        recovery_service.register_service("gmail", "Gmail API")

        id1 = recovery_service.queue_failed_operation(
            "gmail", "send_email", {"to": "a@example.com"}
        )
        id2 = recovery_service.queue_failed_operation(
            "gmail", "send_email", {"to": "b@example.com"}
        )

        assert id1 != id2
        health = recovery_service.get_health("gmail")
        assert health.queued_operations == 2

    def test_queue_operation_persists_to_file(
        self, recovery_service: ErrorRecoveryService, vault_config: VaultConfig
    ) -> None:
        """Test that queued operations are persisted as JSON files."""
        recovery_service.register_service("gmail", "Gmail API")

        op_id = recovery_service.queue_failed_operation(
            service_name="gmail",
            operation_type="send_email",
            parameters={"to": "user@example.com"},
        )

        queue_dir = vault_config.logs / "queue" / "gmail"
        assert queue_dir.exists()

        queue_files = list(queue_dir.glob("*.json"))
        assert len(queue_files) == 1

        with open(queue_files[0]) as f:
            data = json.load(f)
        assert data["operation_type"] == "send_email"
        assert data["service_name"] == "gmail"

    def test_queue_operation_unregistered_service_raises(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that queuing for unknown service raises error."""
        with pytest.raises(KeyError):
            recovery_service.queue_failed_operation(
                "unknown", "test", {}
            )


class TestProcessQueuedOperations:
    """Tests for processing queued operations."""

    def test_process_empty_queue(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test processing an empty queue returns zero results."""
        recovery_service.register_service("gmail", "Gmail API")

        result = recovery_service.process_queued_operations("gmail")

        assert result["total"] == 0
        assert result["processed"] == 0
        assert result["failed"] == 0

    def test_process_queued_operations_returns_stats(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that processing queued operations returns statistics."""
        recovery_service.register_service("gmail", "Gmail API")
        recovery_service.queue_failed_operation(
            "gmail", "send_email", {"to": "user@example.com"}
        )

        result = recovery_service.process_queued_operations("gmail")

        assert "total" in result
        assert "processed" in result
        assert "failed" in result
        assert result["total"] == 1

    def test_process_queued_reduces_count(
        self, recovery_service: ErrorRecoveryService
    ) -> None:
        """Test that processing reduces queued operations count."""
        recovery_service.register_service("gmail", "Gmail API")
        recovery_service.queue_failed_operation(
            "gmail", "send_email", {"to": "user@example.com"}
        )

        recovery_service.process_queued_operations("gmail")

        health = recovery_service.get_health("gmail")
        assert health.queued_operations == 0


class TestHealthPersistence:
    """Tests for health status persistence to log files."""

    def test_write_health_to_log(
        self,
        recovery_service: ErrorRecoveryService,
        vault_config: VaultConfig,
    ) -> None:
        """Test that health data is written to log file."""
        recovery_service.register_service("gmail", "Gmail API", is_critical=True)
        recovery_service.record_success("gmail")

        recovery_service.write_health_log()

        health_files = list(vault_config.logs.glob("health_*.log"))
        assert len(health_files) >= 1

    def test_health_log_contains_all_services(
        self,
        recovery_service: ErrorRecoveryService,
        vault_config: VaultConfig,
    ) -> None:
        """Test that health log contains data for all services."""
        recovery_service.register_service("gmail", "Gmail API")
        recovery_service.register_service("odoo", "Odoo ERP")

        recovery_service.write_health_log()

        health_files = list(vault_config.logs.glob("health_*.log"))
        assert len(health_files) >= 1

        with open(health_files[0]) as f:
            content = f.read()

        assert "gmail" in content
        assert "odoo" in content
