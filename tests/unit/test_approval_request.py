"""Unit tests for ApprovalRequest model."""

from datetime import datetime, timedelta

import pytest

from ai_employee.models.approval_request import (
    ApprovalCategory,
    ApprovalRequest,
    ApprovalStatus,
)


class TestApprovalRequest:
    """Tests for ApprovalRequest dataclass."""

    def test_create_approval_request(self) -> None:
        """Test creating a new approval request."""
        request = ApprovalRequest.create(
            id="test_123",
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com", "subject": "Test"},
            summary="Test email approval",
        )

        assert request.id == "test_123"
        assert request.category == ApprovalCategory.EMAIL
        assert request.status == ApprovalStatus.PENDING
        assert request.payload["to"] == "test@example.com"
        assert request.expires_at > request.created_at

    def test_create_with_custom_expiration(self) -> None:
        """Test creating approval request with custom expiration."""
        request = ApprovalRequest.create(
            id="test_456",
            category=ApprovalCategory.PAYMENT,
            payload={"amount": 100},
            expiration_hours=48,
        )

        expected_expiry = request.created_at + timedelta(hours=48)
        # Allow 1 second tolerance for test execution time
        assert abs((request.expires_at - expected_expiry).total_seconds()) < 1

    def test_is_expired(self) -> None:
        """Test expiration check."""
        now = datetime.now()
        # Create expired request
        expired_request = ApprovalRequest(
            id="expired_123",
            category=ApprovalCategory.EMAIL,
            payload={},
            created_at=now - timedelta(hours=25),
            expires_at=now - timedelta(hours=1),
            status=ApprovalStatus.PENDING,
        )
        assert expired_request.is_expired() is True

        # Create non-expired request
        valid_request = ApprovalRequest.create(
            id="valid_123",
            category=ApprovalCategory.EMAIL,
            payload={},
        )
        assert valid_request.is_expired() is False

    def test_time_remaining(self) -> None:
        """Test time remaining calculation."""
        request = ApprovalRequest.create(
            id="test_time",
            category=ApprovalCategory.EMAIL,
            payload={},
            expiration_hours=24,
        )

        remaining = request.time_remaining()
        # Should be close to 24 hours
        assert remaining.total_seconds() > 23 * 3600
        assert remaining.total_seconds() <= 24 * 3600

    def test_time_remaining_non_pending(self) -> None:
        """Test time remaining returns zero for non-pending requests."""
        request = ApprovalRequest.create(
            id="approved_test",
            category=ApprovalCategory.EMAIL,
            payload={},
        )
        request.status = ApprovalStatus.APPROVED

        assert request.time_remaining() == timedelta(0)

    def test_to_frontmatter(self) -> None:
        """Test conversion to frontmatter dictionary."""
        request = ApprovalRequest.create(
            id="fm_test",
            category=ApprovalCategory.SOCIAL_POST,
            payload={"content": "Hello world"},
        )

        fm = request.to_frontmatter()

        assert fm["id"] == "fm_test"
        assert fm["category"] == "social_post"
        assert fm["status"] == "pending"
        assert "created_at" in fm
        assert "expires_at" in fm
        assert fm["payload"]["content"] == "Hello world"

    def test_from_frontmatter(self) -> None:
        """Test creation from frontmatter dictionary."""
        fm = {
            "id": "from_fm_test",
            "category": "email",
            "status": "approved",
            "created_at": "2026-02-03T10:00:00",
            "expires_at": "2026-02-04T10:00:00",
            "payload": {"to": "user@example.com"},
        }

        request = ApprovalRequest.from_frontmatter(fm)

        assert request.id == "from_fm_test"
        assert request.category == ApprovalCategory.EMAIL
        assert request.status == ApprovalStatus.APPROVED
        assert request.payload["to"] == "user@example.com"

    def test_get_filename(self) -> None:
        """Test filename generation."""
        request = ApprovalRequest.create(
            id="file_test",
            category=ApprovalCategory.PAYMENT,
            payload={},
        )

        assert request.get_filename() == "APPROVAL_payment_file_test.md"

    def test_validation_expires_after_created(self) -> None:
        """Test validation that expires_at must be after created_at."""
        now = datetime.now()

        with pytest.raises(ValueError, match="expires_at must be after created_at"):
            ApprovalRequest(
                id="invalid",
                category=ApprovalCategory.EMAIL,
                payload={},
                created_at=now,
                expires_at=now - timedelta(hours=1),  # Invalid: before created
            )


class TestApprovalCategory:
    """Tests for ApprovalCategory enum."""

    def test_all_categories_exist(self) -> None:
        """Test all required categories are defined."""
        assert ApprovalCategory.EMAIL.value == "email"
        assert ApprovalCategory.SOCIAL_POST.value == "social_post"
        assert ApprovalCategory.PAYMENT.value == "payment"
        assert ApprovalCategory.FILE_OPERATION.value == "file_operation"
        assert ApprovalCategory.CUSTOM.value == "custom"


class TestApprovalStatus:
    """Tests for ApprovalStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """Test all required statuses are defined."""
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"
        assert ApprovalStatus.EXPIRED.value == "expired"
        assert ApprovalStatus.EXECUTED.value == "executed"
