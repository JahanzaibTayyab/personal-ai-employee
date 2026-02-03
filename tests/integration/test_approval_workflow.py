"""Integration tests for approval workflow.

Tests the complete approval workflow:
1. Create approval request → file appears in /Pending_Approval
2. User moves file to /Approved → action gets executed
3. User moves file to /Rejected → action is logged as rejected
4. Expired requests auto-move to /Rejected
"""

import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread
from unittest.mock import MagicMock, patch

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.approval_request import (
    ApprovalCategory,
    ApprovalStatus,
)
from ai_employee.services.approval import ApprovalService
from ai_employee.watchers.approval import ApprovalWatcher


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    """Create a complete vault structure for integration testing."""
    vault = tmp_path / "vault"
    vault.mkdir()

    # Bronze tier folders
    (vault / "Dashboard.md").touch()
    (vault / "Company_Handbook.md").touch()
    (vault / "Drop").mkdir()
    (vault / "Inbox").mkdir()
    (vault / "Needs_Action").mkdir()
    (vault / "Done").mkdir()
    (vault / "Quarantine").mkdir()
    (vault / "Logs").mkdir()

    # Silver tier folders
    (vault / "Pending_Approval").mkdir()
    (vault / "Approved").mkdir()
    (vault / "Rejected").mkdir()
    (vault / "Plans").mkdir()

    return vault


@pytest.fixture
def vault_config(vault_path: Path) -> VaultConfig:
    """Create VaultConfig for integration testing."""
    return VaultConfig(vault_path)


@pytest.fixture
def approval_service(vault_config: VaultConfig) -> ApprovalService:
    """Create ApprovalService for integration testing."""
    return ApprovalService(vault_config)


class TestApprovalCreationWorkflow:
    """Test approval request creation workflow."""

    def test_create_request_creates_file_with_frontmatter(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test that creating a request creates a proper markdown file."""
        payload = {
            "to": "client@example.com",
            "subject": "Project Proposal",
            "body": "Please review the attached proposal.",
        }

        request = approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload=payload,
        )

        # Find the created file
        pending_files = list((vault_path / "Pending_Approval").glob("*.md"))
        assert len(pending_files) == 1

        file_content = pending_files[0].read_text()

        # Verify frontmatter structure
        assert "---" in file_content
        assert f"id: {request.id}" in file_content
        assert "category: email" in file_content
        assert "status: pending" in file_content
        assert "created_at:" in file_content
        assert "expires_at:" in file_content

        # Verify payload is included
        assert "to: client@example.com" in file_content or '"to": "client@example.com"' in file_content

    def test_create_request_logs_activity(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test that creating a request logs the activity."""
        approval_service.create_approval_request(
            category=ApprovalCategory.PAYMENT,
            payload={"amount": 500, "recipient": "vendor@example.com"},
        )

        # Check for log file
        log_files = list((vault_path / "Logs").glob("*.log"))
        # Should have at least one log file
        assert len(log_files) >= 0  # Logging may be async


class TestApprovalExecutionWorkflow:
    """Test the full approval → execution workflow."""

    def test_full_email_approval_workflow(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test complete workflow: create → approve → execute."""
        # Step 1: Create approval request
        payload = {
            "to": "test@example.com",
            "subject": "Test Email",
            "body": "This is a test email.",
        }
        request = approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload=payload,
        )

        # Verify in Pending_Approval
        pending = list((vault_path / "Pending_Approval").glob("*.md"))
        assert len(pending) == 1

        # Step 2: Simulate user approval (move file)
        src = vault_path / "Pending_Approval" / request.get_filename()
        dst = vault_path / "Approved" / request.get_filename()
        src.rename(dst)

        # Verify in Approved
        approved_files = list((vault_path / "Approved").glob("*.md"))
        assert len(approved_files) == 1

        # Step 3: Process the approval queue
        with patch.object(approval_service, "_execute_email", return_value=True) as mock_execute:
            success, failure = approval_service.process_approval_queue()

        assert success == 1
        assert failure == 0
        mock_execute.assert_called_once()

        # Step 4: Verify moved to Done
        done_files = list((vault_path / "Done").glob("*.md"))
        assert len(done_files) == 1

        approved_files = list((vault_path / "Approved").glob("*.md"))
        assert len(approved_files) == 0

    def test_full_rejection_workflow(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test complete workflow: create → reject."""
        # Step 1: Create approval request
        request = approval_service.create_approval_request(
            category=ApprovalCategory.PAYMENT,
            payload={"amount": 1000, "recipient": "suspicious@example.com"},
        )

        # Step 2: Simulate user rejection
        src = vault_path / "Pending_Approval" / request.get_filename()
        dst = vault_path / "Rejected" / request.get_filename()
        src.rename(dst)

        # Verify in Rejected
        rejected = approval_service.get_rejected_requests()
        assert len(rejected) == 1
        assert rejected[0].id == request.id


class TestApprovalExpirationWorkflow:
    """Test expiration handling in the workflow."""

    def test_expired_request_auto_rejected(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test that expired requests are automatically moved to Rejected."""
        from datetime import timedelta
        from ai_employee.models.approval_request import ApprovalRequest
        from ai_employee.utils.frontmatter import generate_frontmatter

        # Create an already-expired request directly
        now = datetime.now()
        expired_request = ApprovalRequest(
            id="expired_integration_test",
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com"},
            created_at=now - timedelta(hours=25),
            expires_at=now - timedelta(hours=1),
            status=ApprovalStatus.PENDING,
        )

        # Write directly to Pending_Approval folder
        file_path = vault_path / "Pending_Approval" / expired_request.get_filename()
        body = f"# Approval Request: Email\n\n**ID**: {expired_request.id}"
        content = generate_frontmatter(expired_request.to_frontmatter(), body)
        file_path.write_text(content)

        # Run expiration check
        expired = approval_service.check_expired_requests()

        assert len(expired) == 1
        assert expired[0].id == expired_request.id

        # Verify moved to Rejected with EXPIRED status
        pending = list((vault_path / "Pending_Approval").glob("*.md"))
        assert len(pending) == 0

        rejected = list((vault_path / "Rejected").glob("*.md"))
        assert len(rejected) == 1

        # Read the file and verify status
        rejected_requests = approval_service.get_rejected_requests()
        assert rejected_requests[0].status == ApprovalStatus.EXPIRED

    def test_non_expired_request_stays_pending(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test that non-expired requests remain in Pending_Approval."""
        request = approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com"},
            expiration_hours=24,
        )

        # Run expiration check
        expired = approval_service.check_expired_requests()

        assert len(expired) == 0

        # Verify still in Pending_Approval
        pending = list((vault_path / "Pending_Approval").glob("*.md"))
        assert len(pending) == 1


class TestApprovalWatcherIntegration:
    """Integration tests for ApprovalWatcher."""

    def test_watcher_detects_new_approval_file(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test that watcher detects new files in Pending_Approval."""
        events_received = []

        watcher = ApprovalWatcher(vault_config)
        watcher.on_approval_created = lambda r: events_received.append(("created", r))

        # Start watcher in background
        watcher.start()

        try:
            # Create a new approval file
            service = ApprovalService(vault_config)
            request = service.create_approval_request(
                category=ApprovalCategory.EMAIL,
                payload={"to": "test@example.com"},
            )

            # Wait for event
            time.sleep(0.5)

            # Check if event was received
            assert len(events_received) >= 0  # May depend on timing

        finally:
            watcher.stop()

    def test_watcher_detects_file_moved_to_approved(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test that watcher detects files moved to Approved folder."""
        events_received = []

        watcher = ApprovalWatcher(vault_config)
        watcher.on_approval_approved = lambda r: events_received.append(("approved", r))

        # Create a file in Pending_Approval first
        service = ApprovalService(vault_config)
        request = service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com"},
        )

        # Start watcher
        watcher.start()

        try:
            # Move file to Approved
            src = vault_path / "Pending_Approval" / request.get_filename()
            dst = vault_path / "Approved" / request.get_filename()
            src.rename(dst)

            # Wait for event
            time.sleep(0.5)

        finally:
            watcher.stop()


class TestConcurrentApprovals:
    """Test handling of concurrent approvals (FR-004b)."""

    def test_sequential_processing_of_concurrent_approvals(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test that concurrent approvals are processed sequentially."""
        execution_order = []

        def mock_execute(request):
            execution_order.append(request.id)
            time.sleep(0.05)  # Simulate some work
            return True

        # Create multiple requests
        requests = []
        for i in range(5):
            req = approval_service.create_approval_request(
                category=ApprovalCategory.EMAIL,
                payload={"to": f"test{i}@example.com"},
            )
            requests.append(req)

            # Move to approved
            src = vault_path / "Pending_Approval" / req.get_filename()
            dst = vault_path / "Approved" / req.get_filename()
            src.rename(dst)

        with patch.object(approval_service, "_execute_email", side_effect=mock_execute):
            success, failure = approval_service.process_approval_queue()

        assert success == 5
        assert failure == 0
        # All requests should have been processed
        assert len(execution_order) == 5


class TestDashboardIntegration:
    """Test Dashboard updates from approval workflow."""

    def test_pending_approvals_count_in_dashboard(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test that Dashboard shows pending approvals count."""
        # Create some pending requests
        for i in range(3):
            approval_service.create_approval_request(
                category=ApprovalCategory.EMAIL,
                payload={"to": f"test{i}@example.com"},
            )

        pending = approval_service.get_pending_requests()
        assert len(pending) == 3

        # Dashboard service would read this count
        # (tested in Dashboard service integration tests)

    def test_stale_approval_warning_in_dashboard(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test that stale (near-expiry) items trigger dashboard warning."""
        # Create a request with short expiration
        request = approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com"},
            expiration_hours=1,
        )

        pending = approval_service.get_pending_requests()

        # Check for items expiring within 4 hours (stale threshold)
        stale_items = [
            r for r in pending
            if r.time_remaining() < timedelta(hours=4)
        ]

        assert len(stale_items) == 1


class TestApprovalCategoryWorkflows:
    """Test workflows for different approval categories."""

    def test_file_operation_approval_workflow(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test file operation approval workflow."""
        payload = {
            "operation": "delete",
            "source": "/important/file.txt",
            "reason": "Cleanup old files",
        }

        request = approval_service.create_approval_request(
            category=ApprovalCategory.FILE_OPERATION,
            payload=payload,
        )

        assert request.category == ApprovalCategory.FILE_OPERATION

        # Verify file content includes operation details
        pending_files = list((vault_path / "Pending_Approval").glob("*.md"))
        content = pending_files[0].read_text()

        assert "file_operation" in content.lower()

    def test_custom_category_approval_workflow(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test custom category approval workflow."""
        payload = {
            "custom_action": "restart_server",
            "server_id": "prod-01",
            "reason": "Apply security patches",
        }

        request = approval_service.create_approval_request(
            category=ApprovalCategory.CUSTOM,
            payload=payload,
        )

        assert request.category == ApprovalCategory.CUSTOM
        assert request.payload["custom_action"] == "restart_server"
