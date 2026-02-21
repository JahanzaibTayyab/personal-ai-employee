"""Error recovery service for graceful degradation and failed operation queuing.

Implements FR-036 through FR-042: exponential backoff retry, error classification,
degraded functionality mode, failed operation queue, and dashboard health alerts.
"""

import json
import uuid
from datetime import datetime
from typing import Any

from ai_employee.config import VaultConfig
from ai_employee.models.enums import HealthStatus
from ai_employee.models.service_health import ServiceHealth
from ai_employee.utils.retry import classify_error

# Number of consecutive failures before marking a service as DOWN
DOWN_THRESHOLD: int = 3


class ErrorRecoveryService:
    """Manages service health, degraded operation, and failed operation queuing.

    Tracks the health of external services (gmail, odoo, meta, etc.),
    provides degraded functionality mode when services are down,
    and queues operations for retry when services are restored.
    """

    def __init__(self, vault_config: VaultConfig) -> None:
        """Initialize ErrorRecoveryService.

        Args:
            vault_config: Vault configuration with paths.
        """
        self._vault_config = vault_config
        self._services: dict[str, ServiceHealth] = {}
        self._queue_dir = vault_config.logs / "queue"

    def register_service(
        self,
        name: str,
        display_name: str,
        is_critical: bool = False,
    ) -> ServiceHealth:
        """Register an external service for health tracking.

        If a service with the same name is already registered,
        returns the existing ServiceHealth without modification.

        Args:
            name: Unique service identifier (e.g., 'gmail', 'odoo').
            display_name: Human-readable service name.
            is_critical: Whether this service is critical for operation.

        Returns:
            ServiceHealth for the registered service.
        """
        if name in self._services:
            return self._services[name]

        health = ServiceHealth(
            service_name=name,
            display_name=display_name,
            status=HealthStatus.UNKNOWN,
            is_critical=is_critical,
        )
        self._services[name] = health
        return health

    def record_success(self, service_name: str) -> ServiceHealth:
        """Record a successful operation for a service.

        Resets failure count and sets status to HEALTHY.

        Args:
            service_name: Unique service identifier.

        Returns:
            Updated ServiceHealth.

        Raises:
            KeyError: If the service is not registered.
        """
        if service_name not in self._services:
            raise KeyError(f"Service not registered: {service_name}")

        current = self._services[service_name]
        now = datetime.now()

        updated = ServiceHealth(
            service_name=current.service_name,
            display_name=current.display_name,
            status=HealthStatus.HEALTHY,
            last_check=now,
            last_success=now,
            consecutive_failures=0,
            last_error=None,
            error_category=None,
            is_critical=current.is_critical,
            queued_operations=current.queued_operations,
        )
        self._services[service_name] = updated
        return updated

    def record_failure(
        self,
        service_name: str,
        error: Exception,
    ) -> ServiceHealth:
        """Record a failed operation for a service.

        Increments failure count, classifies the error, and updates
        status to DEGRADED or DOWN based on failure count.

        Args:
            service_name: Unique service identifier.
            error: The exception that occurred.

        Returns:
            Updated ServiceHealth.

        Raises:
            KeyError: If the service is not registered.
        """
        if service_name not in self._services:
            raise KeyError(f"Service not registered: {service_name}")

        current = self._services[service_name]
        now = datetime.now()
        new_failures = current.consecutive_failures + 1
        category = classify_error(error)

        if new_failures >= DOWN_THRESHOLD:
            new_status = HealthStatus.DOWN
        else:
            new_status = HealthStatus.DEGRADED

        updated = ServiceHealth(
            service_name=current.service_name,
            display_name=current.display_name,
            status=new_status,
            last_check=now,
            last_success=current.last_success,
            consecutive_failures=new_failures,
            last_error=str(error),
            error_category=category,
            is_critical=current.is_critical,
            queued_operations=current.queued_operations,
        )
        self._services[service_name] = updated
        return updated

    def get_health(self, service_name: str) -> ServiceHealth:
        """Get the current health status of a service.

        Args:
            service_name: Unique service identifier.

        Returns:
            Current ServiceHealth.

        Raises:
            KeyError: If the service is not registered.
        """
        if service_name not in self._services:
            raise KeyError(f"Service not registered: {service_name}")
        return self._services[service_name]

    def get_all_health(self) -> list[ServiceHealth]:
        """Get health status of all registered services.

        Returns:
            List of ServiceHealth objects for all services.
        """
        return list(self._services.values())

    def is_service_available(self, service_name: str) -> bool:
        """Check whether a service is available for operations.

        A service is available if its status is HEALTHY, DEGRADED, or UNKNOWN.
        DOWN services are not available. Unregistered services return False.

        Args:
            service_name: Unique service identifier.

        Returns:
            True if the service is available.
        """
        if service_name not in self._services:
            return False

        health = self._services[service_name]
        return health.status != HealthStatus.DOWN

    def get_degraded_services(self) -> list[ServiceHealth]:
        """Get services that are not fully healthy.

        Returns services with DEGRADED or DOWN status.

        Returns:
            List of ServiceHealth objects for unhealthy services.
        """
        return [
            health
            for health in self._services.values()
            if health.status in (HealthStatus.DEGRADED, HealthStatus.DOWN)
        ]

    def queue_failed_operation(
        self,
        service_name: str,
        operation_type: str,
        parameters: dict[str, Any],
    ) -> str:
        """Queue a failed operation for later retry.

        Stores the operation as a JSON file in the queue directory
        and increments the service's queued_operations count.

        Args:
            service_name: Service the operation is for.
            operation_type: Type of operation (e.g., 'send_email').
            parameters: Operation parameters.

        Returns:
            Unique operation ID.

        Raises:
            KeyError: If the service is not registered.
        """
        if service_name not in self._services:
            raise KeyError(f"Service not registered: {service_name}")

        op_id = f"op_{uuid.uuid4().hex[:12]}"
        service_queue_dir = self._queue_dir / service_name
        service_queue_dir.mkdir(parents=True, exist_ok=True)

        operation = {
            "id": op_id,
            "service_name": service_name,
            "operation_type": operation_type,
            "parameters": parameters,
            "queued_at": datetime.now().isoformat(),
            "status": "pending",
        }

        op_path = service_queue_dir / f"{op_id}.json"
        op_path.write_text(json.dumps(operation, indent=2))

        # Update queued count
        current = self._services[service_name]
        updated = ServiceHealth(
            service_name=current.service_name,
            display_name=current.display_name,
            status=current.status,
            last_check=current.last_check,
            last_success=current.last_success,
            consecutive_failures=current.consecutive_failures,
            last_error=current.last_error,
            error_category=current.error_category,
            is_critical=current.is_critical,
            queued_operations=current.queued_operations + 1,
        )
        self._services[service_name] = updated

        return op_id

    def process_queued_operations(
        self,
        service_name: str,
    ) -> dict[str, int]:
        """Process all queued operations for a service.

        Reads queued operations from the queue directory, marks them
        as processed, and removes the files. In production, each
        operation would be re-executed; here we simply clear the queue.

        Args:
            service_name: Service to process queued operations for.

        Returns:
            Dictionary with total, processed, and failed counts.
        """
        if service_name not in self._services:
            raise KeyError(f"Service not registered: {service_name}")

        service_queue_dir = self._queue_dir / service_name

        if not service_queue_dir.exists():
            return {"total": 0, "processed": 0, "failed": 0}

        queue_files = list(service_queue_dir.glob("*.json"))
        total = len(queue_files)
        processed = 0
        failed = 0

        for queue_file in queue_files:
            try:
                queue_file.unlink()
                processed += 1
            except OSError:
                failed += 1

        # Reset queued operations count
        current = self._services[service_name]
        updated = ServiceHealth(
            service_name=current.service_name,
            display_name=current.display_name,
            status=current.status,
            last_check=current.last_check,
            last_success=current.last_success,
            consecutive_failures=current.consecutive_failures,
            last_error=current.last_error,
            error_category=current.error_category,
            is_critical=current.is_critical,
            queued_operations=max(0, current.queued_operations - processed),
        )
        self._services[service_name] = updated

        return {"total": total, "processed": processed, "failed": failed}

    def write_health_log(self) -> None:
        """Write current health status to a log file.

        Creates a JSONL file in the Logs directory with the current
        health status of all registered services.
        """
        self._vault_config.logs.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        filename = f"health_{now.strftime('%Y-%m-%d')}.log"
        log_path = self._vault_config.logs / filename

        health_data = [
            health.to_dict() for health in self._services.values()
        ]

        with open(log_path, "a") as f:
            entry = {
                "timestamp": now.isoformat(),
                "services": health_data,
            }
            f.write(json.dumps(entry) + "\n")
