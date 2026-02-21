"""Tests for WatchdogService."""

import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ai_employee.config import VaultConfig
from ai_employee.services.watchdog import WatchdogService


@pytest.fixture
def vault_config(tmp_path: Path) -> VaultConfig:
    """Create a temporary vault config for testing."""
    config = VaultConfig(root=tmp_path)
    config.ensure_structure()
    return config


@pytest.fixture
def watchdog_service(vault_config: VaultConfig) -> WatchdogService:
    """Create a WatchdogService for testing."""
    service = WatchdogService(vault_config, check_interval=0.1)
    yield service
    # Ensure monitoring is stopped after each test
    if service._monitoring:
        service.stop_monitoring()


def make_start_fn(should_fail: bool = False) -> MagicMock:
    """Create a mock start function."""
    fn = MagicMock()
    if should_fail:
        fn.side_effect = RuntimeError("Start failed")
    return fn


def make_health_check_fn(is_healthy: bool = True) -> MagicMock:
    """Create a mock health check function."""
    return MagicMock(return_value=is_healthy)


class TestRegisterWatcher:
    """Tests for registering watchers with the watchdog."""

    def test_register_watcher(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test registering a watcher."""
        start_fn = make_start_fn()
        health_fn = make_health_check_fn()

        watchdog_service.register_watcher(
            name="filesystem",
            start_fn=start_fn,
            health_check_fn=health_fn,
        )

        status = watchdog_service.get_watcher_status("filesystem")
        assert status["name"] == "filesystem"
        assert status["running"] is False
        assert status["restart_count"] == 0

    def test_register_duplicate_watcher_raises(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test that registering a duplicate watcher raises error."""
        watchdog_service.register_watcher(
            "fs", make_start_fn(), make_health_check_fn()
        )

        with pytest.raises(ValueError, match="already registered"):
            watchdog_service.register_watcher(
                "fs", make_start_fn(), make_health_check_fn()
            )

    def test_get_watcher_status_unregistered_raises(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test getting status of unregistered watcher raises error."""
        with pytest.raises(KeyError, match="unknown"):
            watchdog_service.get_watcher_status("unknown")


class TestStartStopMonitoring:
    """Tests for starting and stopping the monitoring loop."""

    def test_start_monitoring_starts_thread(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test that start_monitoring creates a monitoring thread."""
        watchdog_service.register_watcher(
            "fs", make_start_fn(), make_health_check_fn()
        )

        watchdog_service.start_monitoring()
        time.sleep(0.05)

        assert watchdog_service._monitoring is True
        assert watchdog_service._monitor_thread is not None
        assert watchdog_service._monitor_thread.is_alive()

        watchdog_service.stop_monitoring()

    def test_stop_monitoring_stops_thread(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test that stop_monitoring stops the monitoring thread."""
        watchdog_service.register_watcher(
            "fs", make_start_fn(), make_health_check_fn()
        )

        watchdog_service.start_monitoring()
        time.sleep(0.05)
        watchdog_service.stop_monitoring()
        time.sleep(0.2)

        assert watchdog_service._monitoring is False

    def test_start_monitoring_starts_watchers(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test that start_monitoring calls start_fn for each watcher."""
        start_fn = make_start_fn()
        watchdog_service.register_watcher(
            "fs", start_fn, make_health_check_fn()
        )

        watchdog_service.start_monitoring()
        time.sleep(0.05)

        start_fn.assert_called()

        watchdog_service.stop_monitoring()

    def test_start_monitoring_twice_is_noop(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test that calling start_monitoring again is harmless."""
        watchdog_service.register_watcher(
            "fs", make_start_fn(), make_health_check_fn()
        )

        watchdog_service.start_monitoring()
        watchdog_service.start_monitoring()  # Should not raise
        time.sleep(0.05)

        assert watchdog_service._monitoring is True

        watchdog_service.stop_monitoring()


class TestRestartWatcher:
    """Tests for restarting individual watchers."""

    def test_restart_watcher(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test manually restarting a watcher."""
        start_fn = make_start_fn()
        watchdog_service.register_watcher(
            "fs", start_fn, make_health_check_fn()
        )

        watchdog_service.restart_watcher("fs")

        assert start_fn.called
        status = watchdog_service.get_watcher_status("fs")
        assert status["restart_count"] == 1

    def test_restart_increments_count(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test that each restart increments the count."""
        watchdog_service.register_watcher(
            "fs", make_start_fn(), make_health_check_fn()
        )

        watchdog_service.restart_watcher("fs")
        watchdog_service.restart_watcher("fs")
        watchdog_service.restart_watcher("fs")

        status = watchdog_service.get_watcher_status("fs")
        assert status["restart_count"] == 3

    def test_restart_unregistered_watcher_raises(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test restarting unregistered watcher raises error."""
        with pytest.raises(KeyError, match="unknown"):
            watchdog_service.restart_watcher("unknown")

    def test_restart_records_last_restart_time(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test that restart records the timestamp."""
        watchdog_service.register_watcher(
            "fs", make_start_fn(), make_health_check_fn()
        )

        before = time.time()
        watchdog_service.restart_watcher("fs")

        status = watchdog_service.get_watcher_status("fs")
        assert status["last_restart"] is not None


class TestAutoRestart:
    """Tests for automatic watcher restart on failure."""

    def test_unhealthy_watcher_gets_restarted(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test that an unhealthy watcher is automatically restarted."""
        start_fn = make_start_fn()
        health_fn = make_health_check_fn(is_healthy=False)

        watchdog_service.register_watcher("fs", start_fn, health_fn)
        watchdog_service.start_monitoring()

        # Wait for at least one check cycle
        time.sleep(0.3)
        watchdog_service.stop_monitoring()

        # Start fn should be called more than once (initial + restart)
        assert start_fn.call_count >= 2

    def test_healthy_watcher_not_restarted(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test that a healthy watcher is not restarted."""
        start_fn = make_start_fn()
        health_fn = make_health_check_fn(is_healthy=True)

        watchdog_service.register_watcher("fs", start_fn, health_fn)
        watchdog_service.start_monitoring()

        time.sleep(0.3)
        watchdog_service.stop_monitoring()

        # Start fn should be called exactly once (initial start)
        assert start_fn.call_count == 1

    def test_failed_start_is_tracked(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test that a failed start attempt is tracked."""
        start_fn = make_start_fn(should_fail=True)
        health_fn = make_health_check_fn(is_healthy=False)

        watchdog_service.register_watcher("fs", start_fn, health_fn)

        # Manual restart that fails
        watchdog_service.restart_watcher("fs")

        status = watchdog_service.get_watcher_status("fs")
        assert status["last_error"] is not None
        assert "Start failed" in status["last_error"]


class TestGetAllStatuses:
    """Tests for getting all watcher statuses."""

    def test_get_all_statuses_empty(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test getting statuses when no watchers registered."""
        statuses = watchdog_service.get_all_statuses()
        assert statuses == []

    def test_get_all_statuses_multiple(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test getting statuses for multiple watchers."""
        watchdog_service.register_watcher(
            "fs", make_start_fn(), make_health_check_fn()
        )
        watchdog_service.register_watcher(
            "gmail", make_start_fn(), make_health_check_fn()
        )

        statuses = watchdog_service.get_all_statuses()

        assert len(statuses) == 2
        names = {s["name"] for s in statuses}
        assert names == {"fs", "gmail"}

    def test_status_dict_has_required_fields(
        self, watchdog_service: WatchdogService
    ) -> None:
        """Test that status dict contains all required fields."""
        watchdog_service.register_watcher(
            "fs", make_start_fn(), make_health_check_fn()
        )

        status = watchdog_service.get_watcher_status("fs")

        assert "name" in status
        assert "running" in status
        assert "restart_count" in status
        assert "last_restart" in status
        assert "last_error" in status
        assert "last_check" in status
