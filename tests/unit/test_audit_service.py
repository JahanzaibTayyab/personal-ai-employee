"""Tests for AuditService (extended for Gold tier)."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ai_employee.config import VaultConfig
from ai_employee.services.audit import AuditService


@pytest.fixture
def vault_config(tmp_path: Path) -> VaultConfig:
    """Create a temporary vault config for testing."""
    config = VaultConfig(root=tmp_path)
    config.ensure_structure()
    return config


@pytest.fixture
def audit_service(vault_config: VaultConfig) -> AuditService:
    """Create an AuditService for testing."""
    return AuditService(vault_config)


class TestLogAction:
    """Tests for logging audit actions."""

    def test_log_action_returns_entry(
        self, audit_service: AuditService
    ) -> None:
        """Test that log_action returns the logged entry."""
        entry = audit_service.log_action(
            action_type="email_send",
            actor="ai_employee",
            target="user@example.com",
        )

        assert entry["action_type"] == "email_send"
        assert entry["actor"] == "ai_employee"
        assert entry["target"] == "user@example.com"
        assert entry["result"] == "success"
        assert "timestamp" in entry

    def test_log_action_writes_to_file(
        self,
        audit_service: AuditService,
        vault_config: VaultConfig,
    ) -> None:
        """Test that log_action persists to a JSONL file."""
        audit_service.log_action(
            action_type="email_send",
            actor="ai_employee",
            target="user@example.com",
        )

        log_files = list(vault_config.logs.glob("audit_*.log"))
        assert len(log_files) == 1

        with open(log_files[0]) as f:
            lines = f.readlines()
        assert len(lines) == 1

        data = json.loads(lines[0])
        assert data["action_type"] == "email_send"

    def test_log_action_with_all_fields(
        self, audit_service: AuditService
    ) -> None:
        """Test logging with all optional fields."""
        entry = audit_service.log_action(
            action_type="invoice_create",
            actor="processor",
            target="INV-001",
            parameters={"amount": 1500},
            result="success",
            error_message=None,
            correlation_id="corr-123",
            duration_ms=250,
            approval_status="approved",
            approved_by="admin",
        )

        assert entry["correlation_id"] == "corr-123"
        assert entry["duration_ms"] == 250
        assert entry["approval_status"] == "approved"
        assert entry["approved_by"] == "admin"

    def test_log_action_redacts_sensitive_params(
        self, audit_service: AuditService
    ) -> None:
        """Test that sensitive parameters are redacted."""
        entry = audit_service.log_action(
            action_type="email_send",
            actor="ai_employee",
            target="user@example.com",
            parameters={"password": "secret123", "subject": "Hello"},
        )

        assert entry["parameters"]["password"] == "[REDACTED]"
        assert entry["parameters"]["subject"] == "Hello"

    def test_log_multiple_actions(
        self, audit_service: AuditService
    ) -> None:
        """Test logging multiple actions to the same file."""
        audit_service.log_action(
            action_type="task_start",
            actor="scheduler",
            target="daily_briefing",
        )
        audit_service.log_action(
            action_type="task_complete",
            actor="scheduler",
            target="daily_briefing",
        )

        entries = audit_service.read_entries()
        assert len(entries) == 2


class TestReadEntries:
    """Tests for reading audit entries."""

    def test_read_entries_empty(
        self, audit_service: AuditService
    ) -> None:
        """Test reading entries when no log file exists."""
        entries = audit_service.read_entries()
        assert entries == []

    def test_read_entries_returns_all(
        self, audit_service: AuditService
    ) -> None:
        """Test reading all entries for today."""
        for i in range(5):
            audit_service.log_action(
                action_type="task_start",
                actor="scheduler",
                target=f"task-{i}",
            )

        entries = audit_service.read_entries()
        assert len(entries) == 5

    def test_read_entries_for_specific_date(
        self,
        audit_service: AuditService,
        vault_config: VaultConfig,
    ) -> None:
        """Test reading entries for a specific date."""
        # Write a log file for a specific date
        specific_date = datetime(2026, 1, 15)
        log_path = vault_config.logs / "audit_2026-01-15.log"
        with open(log_path, "w") as f:
            f.write(json.dumps({
                "timestamp": "2026-01-15T10:00:00",
                "action_type": "email_send",
                "actor": "ai_employee",
                "target": "user@example.com",
                "result": "success",
            }) + "\n")

        entries = audit_service.read_entries(date=specific_date)
        assert len(entries) == 1
        assert entries[0]["action_type"] == "email_send"


class TestQueryEntries:
    """Tests for querying audit entries with filters."""

    def test_query_by_action_type(
        self, audit_service: AuditService
    ) -> None:
        """Test filtering entries by action type."""
        audit_service.log_action("email_send", "ai", "target1")
        audit_service.log_action("task_start", "scheduler", "target2")
        audit_service.log_action("email_send", "ai", "target3")

        results = audit_service.query_entries(action_type="email_send")
        assert len(results) == 2

    def test_query_by_actor(
        self, audit_service: AuditService
    ) -> None:
        """Test filtering entries by actor."""
        audit_service.log_action("task_start", "scheduler", "t1")
        audit_service.log_action("task_start", "ai_employee", "t2")

        results = audit_service.query_entries(actor="scheduler")
        assert len(results) == 1
        assert results[0]["actor"] == "scheduler"

    def test_query_by_target_substring(
        self, audit_service: AuditService
    ) -> None:
        """Test filtering entries by target substring match."""
        audit_service.log_action("email_send", "ai", "user@example.com")
        audit_service.log_action("email_send", "ai", "admin@example.com")
        audit_service.log_action("task_start", "scheduler", "briefing")

        results = audit_service.query_entries(target="example.com")
        assert len(results) == 2

    def test_query_by_result(
        self, audit_service: AuditService
    ) -> None:
        """Test filtering entries by result."""
        audit_service.log_action(
            "email_send", "ai", "t1", result="success"
        )
        audit_service.log_action(
            "email_send", "ai", "t2", result="failure",
            error_message="SMTP error",
        )

        results = audit_service.query_entries(result="failure")
        assert len(results) == 1
        assert results[0]["error_message"] == "SMTP error"

    def test_query_by_correlation_id(
        self, audit_service: AuditService
    ) -> None:
        """Test filtering entries by correlation ID."""
        audit_service.log_action(
            "task_start", "scheduler", "t1",
            correlation_id="corr-abc",
        )
        audit_service.log_action(
            "task_complete", "scheduler", "t1",
            correlation_id="corr-abc",
        )
        audit_service.log_action(
            "task_start", "scheduler", "t2",
            correlation_id="corr-xyz",
        )

        results = audit_service.query_entries(correlation_id="corr-abc")
        assert len(results) == 2

    def test_query_with_limit(
        self, audit_service: AuditService
    ) -> None:
        """Test that query respects the limit parameter."""
        for i in range(10):
            audit_service.log_action("task_start", "scheduler", f"t{i}")

        results = audit_service.query_entries(limit=3)
        assert len(results) == 3

    def test_query_combined_filters(
        self, audit_service: AuditService
    ) -> None:
        """Test query with multiple filters combined."""
        audit_service.log_action(
            "email_send", "ai_employee", "user@example.com",
            result="success",
        )
        audit_service.log_action(
            "email_send", "ai_employee", "admin@example.com",
            result="failure", error_message="SMTP error",
        )
        audit_service.log_action(
            "task_start", "scheduler", "briefing",
            result="success",
        )

        results = audit_service.query_entries(
            action_type="email_send",
            result="failure",
        )
        assert len(results) == 1
        assert results[0]["target"] == "admin@example.com"


class TestGetActionCounts:
    """Tests for getting action type counts."""

    def test_get_action_counts_empty(
        self, audit_service: AuditService
    ) -> None:
        """Test action counts with no entries."""
        counts = audit_service.get_action_counts()
        assert counts == {}

    def test_get_action_counts(
        self, audit_service: AuditService
    ) -> None:
        """Test counting actions by type."""
        audit_service.log_action("email_send", "ai", "t1")
        audit_service.log_action("email_send", "ai", "t2")
        audit_service.log_action("task_start", "scheduler", "t3")

        counts = audit_service.get_action_counts()

        assert counts["email_send"] == 2
        assert counts["task_start"] == 1


class TestRetentionAndArchival:
    """Tests for log retention and archival (FR-049 to FR-052)."""

    def test_get_retention_stats_empty(
        self, audit_service: AuditService
    ) -> None:
        """Test retention stats when no logs exist."""
        stats = audit_service.get_retention_stats()

        assert stats["file_count"] == 0
        assert stats["oldest_date"] is None
        assert stats["newest_date"] is None
        assert stats["total_size_bytes"] == 0

    def test_get_retention_stats_with_files(
        self,
        audit_service: AuditService,
        vault_config: VaultConfig,
    ) -> None:
        """Test retention stats with existing log files."""
        # Create log files for different dates
        for day in [1, 5, 10]:
            log_path = vault_config.logs / f"audit_2026-01-{day:02d}.log"
            log_path.write_text('{"action":"test"}\n')

        stats = audit_service.get_retention_stats()

        assert stats["file_count"] == 3
        assert stats["oldest_date"] == "2026-01-01"
        assert stats["newest_date"] == "2026-01-10"
        assert stats["total_size_bytes"] > 0

    def test_archive_old_entries(
        self,
        audit_service: AuditService,
        vault_config: VaultConfig,
    ) -> None:
        """Test archiving log files older than retention period."""
        # Create old log file (60 days ago)
        old_date = datetime.now() - timedelta(days=60)
        old_log = (
            vault_config.logs
            / f"audit_{old_date.strftime('%Y-%m-%d')}.log"
        )
        old_log.write_text('{"action":"old"}\n')

        # Create recent log file
        audit_service.log_action("task_start", "scheduler", "recent")

        archived = audit_service.archive_old_entries(retention_days=30)

        assert len(archived) == 1
        assert old_log.name in archived

        # Old file should be in archive
        archive_dir = vault_config.logs / "archive"
        assert (archive_dir / old_log.name).exists()

        # Old file should not be in logs dir anymore
        assert not old_log.exists()

    def test_archive_preserves_recent(
        self,
        audit_service: AuditService,
        vault_config: VaultConfig,
    ) -> None:
        """Test that archival preserves recent log files."""
        # Create a log file for today
        audit_service.log_action("task_start", "scheduler", "today")

        archived = audit_service.archive_old_entries(retention_days=30)

        assert len(archived) == 0

    def test_purge_archived(
        self,
        audit_service: AuditService,
        vault_config: VaultConfig,
    ) -> None:
        """Test permanently deleting old archived logs."""
        archive_dir = vault_config.logs / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Create an old archived file (120 days ago)
        old_date = datetime.now() - timedelta(days=120)
        old_file = (
            archive_dir
            / f"audit_{old_date.strftime('%Y-%m-%d')}.log"
        )
        old_file.write_text('{"action":"very_old"}\n')

        purged = audit_service.purge_archived(older_than_days=90)

        assert len(purged) == 1
        assert not old_file.exists()

    def test_purge_preserves_recent_archived(
        self,
        audit_service: AuditService,
        vault_config: VaultConfig,
    ) -> None:
        """Test that purge preserves recently archived files."""
        archive_dir = vault_config.logs / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Create a recently archived file (30 days ago)
        recent_date = datetime.now() - timedelta(days=30)
        recent_file = (
            archive_dir
            / f"audit_{recent_date.strftime('%Y-%m-%d')}.log"
        )
        recent_file.write_text('{"action":"recent_archive"}\n')

        purged = audit_service.purge_archived(older_than_days=90)

        assert len(purged) == 0
        assert recent_file.exists()
