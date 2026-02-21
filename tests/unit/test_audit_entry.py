"""Tests for AuditEntry model."""

from datetime import datetime

import pytest

from ai_employee.models.audit_entry import AuditEntry


class TestAuditEntry:
    """Tests for the AuditEntry dataclass."""

    def test_create_audit_entry_with_defaults(self) -> None:
        """Test creating AuditEntry with minimal fields."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        entry = AuditEntry(
            timestamp=now,
            action_type="email_send",
            actor="ai_employee",
            target="user@example.com",
        )

        assert entry.timestamp == now
        assert entry.action_type == "email_send"
        assert entry.actor == "ai_employee"
        assert entry.target == "user@example.com"
        assert entry.parameters is None
        assert entry.approval_status == "not_required"
        assert entry.approved_by is None
        assert entry.result == "success"
        assert entry.error_message is None
        assert entry.correlation_id is None
        assert entry.duration_ms is None

    def test_create_audit_entry_with_all_fields(self) -> None:
        """Test creating AuditEntry with all fields."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        entry = AuditEntry(
            timestamp=now,
            action_type="invoice_create",
            actor="ai_employee",
            target="INV-2026-001",
            parameters={"amount": 1500, "currency": "USD"},
            approval_status="approved",
            approved_by="admin",
            result="success",
            error_message=None,
            correlation_id="corr-123",
            duration_ms=250,
        )

        assert entry.action_type == "invoice_create"
        assert entry.parameters == {"amount": 1500, "currency": "USD"}
        assert entry.approval_status == "approved"
        assert entry.approved_by == "admin"
        assert entry.correlation_id == "corr-123"
        assert entry.duration_ms == 250

    def test_create_audit_entry_with_failure(self) -> None:
        """Test creating AuditEntry representing a failure."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        entry = AuditEntry(
            timestamp=now,
            action_type="email_send",
            actor="ai_employee",
            target="user@example.com",
            result="failure",
            error_message="SMTP connection refused",
            duration_ms=5000,
        )

        assert entry.result == "failure"
        assert entry.error_message == "SMTP connection refused"
        assert entry.duration_ms == 5000

    def test_to_dict(self) -> None:
        """Test converting AuditEntry to dictionary."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        entry = AuditEntry(
            timestamp=now,
            action_type="post_facebook",
            actor="linkedin_service",
            target="post-123",
            parameters={"content": "Hello world"},
            result="success",
            correlation_id="corr-abc",
            duration_ms=1200,
        )

        result = entry.to_dict()

        assert result["timestamp"] == now.isoformat()
        assert result["action_type"] == "post_facebook"
        assert result["actor"] == "linkedin_service"
        assert result["target"] == "post-123"
        assert result["parameters"] == {"content": "Hello world"}
        assert result["result"] == "success"
        assert result["correlation_id"] == "corr-abc"
        assert result["duration_ms"] == 1200

    def test_to_dict_excludes_none_optionals(self) -> None:
        """Test that to_dict excludes None optional fields."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        entry = AuditEntry(
            timestamp=now,
            action_type="task_start",
            actor="scheduler",
            target="daily_briefing",
        )

        result = entry.to_dict()

        assert "parameters" not in result
        assert "error_message" not in result
        assert "correlation_id" not in result
        assert "duration_ms" not in result
        assert "approved_by" not in result

    def test_from_dict(self) -> None:
        """Test creating AuditEntry from a dictionary."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        data = {
            "timestamp": now.isoformat(),
            "action_type": "approval_granted",
            "actor": "admin",
            "target": "email-draft-456",
            "parameters": {"reason": "looks good"},
            "approval_status": "approved",
            "approved_by": "admin",
            "result": "success",
            "correlation_id": "corr-789",
            "duration_ms": 50,
        }

        entry = AuditEntry.from_dict(data)

        assert entry.timestamp == now
        assert entry.action_type == "approval_granted"
        assert entry.actor == "admin"
        assert entry.target == "email-draft-456"
        assert entry.parameters == {"reason": "looks good"}
        assert entry.approval_status == "approved"
        assert entry.approved_by == "admin"
        assert entry.correlation_id == "corr-789"
        assert entry.duration_ms == 50

    def test_from_dict_with_missing_optionals(self) -> None:
        """Test from_dict with missing optional fields."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        data = {
            "timestamp": now.isoformat(),
            "action_type": "watcher_start",
            "actor": "watchdog",
            "target": "gmail_watcher",
            "result": "success",
            "approval_status": "not_required",
        }

        entry = AuditEntry.from_dict(data)

        assert entry.parameters is None
        assert entry.approved_by is None
        assert entry.error_message is None
        assert entry.correlation_id is None
        assert entry.duration_ms is None

    def test_roundtrip(self) -> None:
        """Test that to_dict and from_dict are inverses."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        original = AuditEntry(
            timestamp=now,
            action_type="ralph_loop_complete",
            actor="ralph_service",
            target="plan-001",
            parameters={"iterations": 5},
            approval_status="approved",
            approved_by="admin",
            result="success",
            correlation_id="corr-loop",
            duration_ms=30000,
        )

        data = original.to_dict()
        restored = AuditEntry.from_dict(data)

        assert restored.timestamp == original.timestamp
        assert restored.action_type == original.action_type
        assert restored.actor == original.actor
        assert restored.target == original.target
        assert restored.parameters == original.parameters
        assert restored.approval_status == original.approval_status
        assert restored.approved_by == original.approved_by
        assert restored.result == original.result
        assert restored.correlation_id == original.correlation_id
        assert restored.duration_ms == original.duration_ms

    def test_all_action_types(self) -> None:
        """Test that all known action types can be used."""
        action_types = [
            "email_draft", "email_send",
            "invoice_create", "invoice_post",
            "payment_record",
            "post_facebook", "post_instagram", "post_twitter",
            "task_start", "task_complete", "task_fail",
            "approval_request", "approval_granted",
            "watcher_start", "watcher_stop", "watcher_restart",
            "briefing_generate",
            "ralph_loop_start", "ralph_loop_iterate", "ralph_loop_complete",
        ]
        now = datetime(2026, 2, 21, 10, 0, 0)

        for action_type in action_types:
            entry = AuditEntry(
                timestamp=now,
                action_type=action_type,
                actor="test",
                target="test_target",
            )
            assert entry.action_type == action_type

    def test_to_json(self) -> None:
        """Test converting AuditEntry to JSON string."""
        now = datetime(2026, 2, 21, 10, 0, 0)
        entry = AuditEntry(
            timestamp=now,
            action_type="email_send",
            actor="ai_employee",
            target="user@example.com",
            result="success",
        )

        json_str = entry.to_json()

        assert isinstance(json_str, str)
        import json
        data = json.loads(json_str)
        assert data["action_type"] == "email_send"

    def test_from_json(self) -> None:
        """Test creating AuditEntry from JSON string."""
        import json
        now = datetime(2026, 2, 21, 10, 0, 0)
        data = {
            "timestamp": now.isoformat(),
            "action_type": "task_complete",
            "actor": "processor",
            "target": "item-789",
            "result": "success",
            "approval_status": "not_required",
        }
        json_str = json.dumps(data)

        entry = AuditEntry.from_json(json_str)

        assert entry.action_type == "task_complete"
        assert entry.actor == "processor"
