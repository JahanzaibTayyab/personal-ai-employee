"""Unit tests for ApprovalService."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.approval_request import (
    ApprovalCategory,
    ApprovalRequest,
    ApprovalStatus,
)
from ai_employee.services.approval import (
    ApprovalError,
    ApprovalExpiredError,
    ApprovalService,
    ExecutionError,
    InvalidPayloadError,
)


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    """Create a temporary vault structure."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Pending_Approval").mkdir()
    (vault / "Approved").mkdir()
    (vault / "Rejected").mkdir()
    (vault / "Done").mkdir()
    (vault / "Logs").mkdir()
    return vault


@pytest.fixture
def vault_config(vault_path: Path) -> VaultConfig:
    """Create VaultConfig for testing."""
    return VaultConfig(vault_path)


@pytest.fixture
def approval_service(vault_config: VaultConfig) -> ApprovalService:
    """Create ApprovalService instance for testing."""
    return ApprovalService(vault_config)


class TestApprovalServiceCreation:
    """Tests for creating approval requests."""

    def test_create_email_approval_request(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test creating an email approval request."""
        payload = {
            "to": "test@example.com",
            "subject": "Test Subject",
            "body": "Test body content",
        }

        request = approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload=payload,
        )

        assert request.category == ApprovalCategory.EMAIL
        assert request.status == ApprovalStatus.PENDING
        assert request.payload == payload
        assert request.id.startswith("approval_")

        # Verify file was created
        pending_files = list((vault_path / "Pending_Approval").glob("*.md"))
        assert len(pending_files) == 1
        assert request.id in pending_files[0].name

    def test_create_payment_approval_request(
        self, approval_service: ApprovalService
    ) -> None:
        """Test creating a payment approval request."""
        payload = {
            "amount": 100.00,
            "currency": "USD",
            "recipient": "vendor@example.com",
            "description": "Invoice #1234",
        }

        request = approval_service.create_approval_request(
            category=ApprovalCategory.PAYMENT,
            payload=payload,
        )

        assert request.category == ApprovalCategory.PAYMENT
        assert request.payload["amount"] == 100.00

    def test_create_social_post_approval_request(
        self, approval_service: ApprovalService
    ) -> None:
        """Test creating a social post approval request."""
        payload = {
            "platform": "linkedin",
            "content": "Hello LinkedIn!",
        }

        request = approval_service.create_approval_request(
            category=ApprovalCategory.SOCIAL_POST,
            payload=payload,
        )

        assert request.category == ApprovalCategory.SOCIAL_POST

    def test_create_with_custom_expiration(
        self, approval_service: ApprovalService
    ) -> None:
        """Test creating request with custom expiration time."""
        request = approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com"},
            expiration_hours=48,
        )

        expected_expiry = request.created_at + timedelta(hours=48)
        assert abs((request.expires_at - expected_expiry).total_seconds()) < 1

    def test_create_generates_unique_ids(
        self, approval_service: ApprovalService
    ) -> None:
        """Test that each request gets a unique ID."""
        request1 = approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com"},
        )
        request2 = approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com"},
        )

        assert request1.id != request2.id


class TestApprovalServiceRetrieval:
    """Tests for retrieving approval requests."""

    def test_get_pending_requests(
        self, approval_service: ApprovalService
    ) -> None:
        """Test getting all pending requests."""
        # Create some requests
        approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test1@example.com"},
        )
        approval_service.create_approval_request(
            category=ApprovalCategory.PAYMENT,
            payload={"amount": 50},
        )

        pending = approval_service.get_pending_requests()

        assert len(pending) == 2
        assert all(r.status == ApprovalStatus.PENDING for r in pending)

    def test_get_pending_requests_empty(
        self, approval_service: ApprovalService
    ) -> None:
        """Test getting pending requests when none exist."""
        pending = approval_service.get_pending_requests()
        assert pending == []

    def test_get_approved_requests(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test getting approved requests."""
        # Create and manually move to approved
        request = approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com"},
        )

        # Simulate user moving file to Approved folder
        src = vault_path / "Pending_Approval" / request.get_filename()
        dst = vault_path / "Approved" / request.get_filename()
        src.rename(dst)

        approved = approval_service.get_approved_requests()

        assert len(approved) == 1
        assert approved[0].id == request.id

    def test_get_rejected_requests(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test getting rejected requests."""
        request = approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com"},
        )

        # Simulate user moving file to Rejected folder
        src = vault_path / "Pending_Approval" / request.get_filename()
        dst = vault_path / "Rejected" / request.get_filename()
        src.rename(dst)

        rejected = approval_service.get_rejected_requests()

        assert len(rejected) == 1

    def test_get_requests_by_category(
        self, approval_service: ApprovalService
    ) -> None:
        """Test filtering requests by category."""
        approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com"},
        )
        approval_service.create_approval_request(
            category=ApprovalCategory.PAYMENT,
            payload={"amount": 100},
        )
        approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test2@example.com"},
        )

        email_requests = approval_service.get_requests_by_category(
            ApprovalCategory.EMAIL
        )

        assert len(email_requests) == 2
        assert all(r.category == ApprovalCategory.EMAIL for r in email_requests)


class TestApprovalServiceExpiration:
    """Tests for expiration handling."""

    def test_check_expired_requests(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test finding and auto-rejecting expired requests."""
        # Create a request and manually make it expired by modifying the file
        from ai_employee.utils.frontmatter import generate_frontmatter

        now = datetime.now()
        expired_request = ApprovalRequest(
            id="expired_test_123",
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com"},
            created_at=now - timedelta(hours=25),
            expires_at=now - timedelta(hours=1),  # Already expired
            status=ApprovalStatus.PENDING,
        )

        # Write directly to Pending_Approval folder
        file_path = vault_path / "Pending_Approval" / expired_request.get_filename()
        body = f"# Approval Request: Email\n\n**ID**: {expired_request.id}"
        content = generate_frontmatter(expired_request.to_frontmatter(), body)
        file_path.write_text(content)

        expired = approval_service.check_expired_requests()

        assert len(expired) == 1
        assert expired[0].id == expired_request.id

        # Verify file was moved to Rejected
        rejected_files = list((vault_path / "Rejected").glob("*.md"))
        assert len(rejected_files) == 1

        pending_files = list((vault_path / "Pending_Approval").glob("*.md"))
        assert len(pending_files) == 0

    def test_check_expired_requests_none_expired(
        self, approval_service: ApprovalService
    ) -> None:
        """Test when no requests are expired."""
        approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com"},
            expiration_hours=24,
        )

        expired = approval_service.check_expired_requests()

        assert expired == []

    def test_expired_status_set_correctly(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test that expired requests get EXPIRED status."""
        from ai_employee.utils.frontmatter import generate_frontmatter

        now = datetime.now()
        expired_request = ApprovalRequest(
            id="expired_status_test",
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

        approval_service.check_expired_requests()

        # Read the rejected file and verify status
        rejected = approval_service.get_rejected_requests()
        assert len(rejected) == 1
        assert rejected[0].status == ApprovalStatus.EXPIRED


class TestApprovalServiceExecution:
    """Tests for executing approved requests."""

    def test_execute_approved_request(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test executing an approved email request."""
        request = approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com", "subject": "Test", "body": "Body"},
        )

        # Move to approved
        src = vault_path / "Pending_Approval" / request.get_filename()
        dst = vault_path / "Approved" / request.get_filename()
        src.rename(dst)

        # Mock the actual email sending
        with patch.object(approval_service, "_execute_email", return_value=True):
            approved_requests = approval_service.get_approved_requests()
            result = approval_service.execute_approved_request(approved_requests[0])

        assert result is True

        # Verify file moved to Done
        done_files = list((vault_path / "Done").glob("*.md"))
        assert len(done_files) == 1

    def test_execute_expired_request_raises_error(
        self, approval_service: ApprovalService
    ) -> None:
        """Test that executing expired request raises error."""
        now = datetime.now()
        # Create an approved but expired request - need to bypass validation
        # by creating with valid dates first, then checking if it's expired
        expired_request = ApprovalRequest(
            id="expired_test",
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com"},
            created_at=now - timedelta(hours=25),
            expires_at=now - timedelta(hours=1),
            status=ApprovalStatus.PENDING,  # Use PENDING so is_expired() returns True
        )

        with pytest.raises(ApprovalExpiredError):
            approval_service.execute_approved_request(expired_request)

    def test_process_approval_queue(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test processing multiple approved requests."""
        # Create multiple requests
        for i in range(3):
            request = approval_service.create_approval_request(
                category=ApprovalCategory.EMAIL,
                payload={"to": f"test{i}@example.com"},
            )
            # Move to approved
            src = vault_path / "Pending_Approval" / request.get_filename()
            dst = vault_path / "Approved" / request.get_filename()
            src.rename(dst)

        with patch.object(approval_service, "_execute_email", return_value=True):
            success, failure = approval_service.process_approval_queue()

        assert success == 3
        assert failure == 0

    def test_process_approval_queue_with_failures(
        self, approval_service: ApprovalService, vault_path: Path
    ) -> None:
        """Test queue processing with some failures."""
        for i in range(3):
            request = approval_service.create_approval_request(
                category=ApprovalCategory.EMAIL,
                payload={"to": f"test{i}@example.com"},
            )
            src = vault_path / "Pending_Approval" / request.get_filename()
            dst = vault_path / "Approved" / request.get_filename()
            src.rename(dst)

        call_count = 0

        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ExecutionError("Simulated failure")
            return True

        with patch.object(approval_service, "_execute_email", side_effect=mock_execute):
            success, failure = approval_service.process_approval_queue()

        assert success == 2
        assert failure == 1


class TestApprovalServiceValidation:
    """Tests for payload validation."""

    def test_invalid_email_payload_missing_to(
        self, approval_service: ApprovalService
    ) -> None:
        """Test that email payload requires 'to' field."""
        with pytest.raises(InvalidPayloadError, match="'to' field"):
            approval_service.create_approval_request(
                category=ApprovalCategory.EMAIL,
                payload={"subject": "Test"},
            )

    def test_invalid_payment_payload_missing_amount(
        self, approval_service: ApprovalService
    ) -> None:
        """Test that payment payload requires 'amount' field."""
        with pytest.raises(InvalidPayloadError, match="'amount' field"):
            approval_service.create_approval_request(
                category=ApprovalCategory.PAYMENT,
                payload={"recipient": "vendor@example.com"},
            )

    def test_custom_category_accepts_any_payload(
        self, approval_service: ApprovalService
    ) -> None:
        """Test that custom category accepts any payload."""
        request = approval_service.create_approval_request(
            category=ApprovalCategory.CUSTOM,
            payload={"anything": "goes", "here": 123},
        )

        assert request.payload["anything"] == "goes"


class TestApprovalErrors:
    """Tests for error classes."""

    def test_approval_error_base(self) -> None:
        """Test ApprovalError base exception."""
        error = ApprovalError("Test error")
        assert str(error) == "Test error"

    def test_approval_expired_error(self) -> None:
        """Test ApprovalExpiredError."""
        error = ApprovalExpiredError("Request has expired")
        assert isinstance(error, ApprovalError)

    def test_execution_error(self) -> None:
        """Test ExecutionError."""
        error = ExecutionError("Failed to send email")
        assert isinstance(error, ApprovalError)

    def test_invalid_payload_error(self) -> None:
        """Test InvalidPayloadError."""
        error = InvalidPayloadError("Missing required field")
        assert isinstance(error, ApprovalError)
