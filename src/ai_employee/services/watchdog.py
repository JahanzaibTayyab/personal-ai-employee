"""Watchdog service for monitoring and auto-restarting watchers.

Implements FR-039: monitor all registered watchers, auto-restart crashed
watchers within 60 seconds, and track restart counts and failure patterns.
"""

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ai_employee.config import VaultConfig

logger = logging.getLogger(__name__)

# Default health check interval in seconds
DEFAULT_CHECK_INTERVAL: float = 60.0


@dataclass
class WatcherRegistration:
    """Internal record of a registered watcher."""

    name: str
    start_fn: Callable[[], None]
    health_check_fn: Callable[[], bool]
    running: bool = False
    restart_count: int = 0
    last_restart: datetime | None = None
    last_check: datetime | None = None
    last_error: str | None = None


class WatchdogService:
    """Monitors registered watchers and auto-restarts them on failure.

    Runs a background thread that periodically checks watcher health
    and restarts any watchers that have become unhealthy.
    """

    def __init__(
        self,
        vault_config: VaultConfig,
        check_interval: float = DEFAULT_CHECK_INTERVAL,
    ) -> None:
        """Initialize WatchdogService.

        Args:
            vault_config: Vault configuration with paths.
            check_interval: Seconds between health checks.
        """
        self._vault_config = vault_config
        self._check_interval = check_interval
        self._watchers: dict[str, WatcherRegistration] = {}
        self._monitoring = False
        self._monitor_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def register_watcher(
        self,
        name: str,
        start_fn: Callable[[], None],
        health_check_fn: Callable[[], bool],
    ) -> None:
        """Register a watcher for monitoring.

        Args:
            name: Unique watcher identifier.
            start_fn: Callable that starts the watcher.
            health_check_fn: Callable that returns True if watcher is healthy.

        Raises:
            ValueError: If a watcher with the same name is already registered.
        """
        with self._lock:
            if name in self._watchers:
                raise ValueError(
                    f"Watcher '{name}' already registered"
                )

            self._watchers[name] = WatcherRegistration(
                name=name,
                start_fn=start_fn,
                health_check_fn=health_check_fn,
            )

    def start_monitoring(self) -> None:
        """Start the monitoring loop in a background thread.

        Starts all registered watchers and begins periodic health checks.
        If monitoring is already active, this is a no-op.
        """
        if self._monitoring:
            return

        self._monitoring = True
        self._stop_event.clear()

        # Start all registered watchers
        with self._lock:
            for watcher in self._watchers.values():
                self._start_watcher(watcher)

        # Launch monitor thread
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="watchdog-monitor",
        )
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop the monitoring loop.

        Signals the background thread to stop and waits for it to finish.
        """
        self._monitoring = False
        self._stop_event.set()

        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None

    def restart_watcher(self, name: str) -> None:
        """Manually restart a specific watcher.

        Args:
            name: Watcher identifier.

        Raises:
            KeyError: If the watcher is not registered.
        """
        with self._lock:
            if name not in self._watchers:
                raise KeyError(f"Watcher not registered: {name}")

            watcher = self._watchers[name]
            watcher.restart_count += 1
            watcher.last_restart = datetime.now()

            self._start_watcher(watcher)

    def get_watcher_status(self, name: str) -> dict[str, Any]:
        """Get the current status of a watcher.

        Args:
            name: Watcher identifier.

        Returns:
            Dictionary with watcher status information.

        Raises:
            KeyError: If the watcher is not registered.
        """
        with self._lock:
            if name not in self._watchers:
                raise KeyError(f"Watcher not registered: {name}")

            watcher = self._watchers[name]
            return self._watcher_to_status(watcher)

    def get_all_statuses(self) -> list[dict[str, Any]]:
        """Get status of all registered watchers.

        Returns:
            List of status dictionaries for all watchers.
        """
        with self._lock:
            return [
                self._watcher_to_status(w)
                for w in self._watchers.values()
            ]

    def _watcher_to_status(
        self, watcher: WatcherRegistration
    ) -> dict[str, Any]:
        """Convert a WatcherRegistration to a status dictionary.

        Args:
            watcher: The watcher registration to convert.

        Returns:
            Status dictionary.
        """
        return {
            "name": watcher.name,
            "running": watcher.running,
            "restart_count": watcher.restart_count,
            "last_restart": (
                watcher.last_restart.isoformat()
                if watcher.last_restart
                else None
            ),
            "last_check": (
                watcher.last_check.isoformat()
                if watcher.last_check
                else None
            ),
            "last_error": watcher.last_error,
        }

    def _start_watcher(self, watcher: WatcherRegistration) -> None:
        """Attempt to start a watcher.

        Args:
            watcher: The watcher registration to start.
        """
        try:
            watcher.start_fn()
            watcher.running = True
            watcher.last_error = None
        except Exception as exc:
            watcher.running = False
            watcher.last_error = str(exc)
            logger.warning(
                "Failed to start watcher '%s': %s",
                watcher.name,
                exc,
            )

    def _monitor_loop(self) -> None:
        """Background loop that checks watcher health and restarts as needed."""
        while not self._stop_event.is_set():
            with self._lock:
                for watcher in self._watchers.values():
                    self._check_and_restart(watcher)

            self._stop_event.wait(timeout=self._check_interval)

    def _check_and_restart(self, watcher: WatcherRegistration) -> None:
        """Check a watcher's health and restart if unhealthy.

        Args:
            watcher: The watcher registration to check.
        """
        watcher.last_check = datetime.now()

        try:
            is_healthy = watcher.health_check_fn()
        except Exception as exc:
            is_healthy = False
            watcher.last_error = str(exc)

        if not is_healthy:
            logger.info(
                "Watcher '%s' unhealthy, restarting (count: %d)",
                watcher.name,
                watcher.restart_count + 1,
            )
            watcher.running = False
            watcher.restart_count += 1
            watcher.last_restart = datetime.now()
            self._start_watcher(watcher)
