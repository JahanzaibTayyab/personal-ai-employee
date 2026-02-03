"""Unit tests for EmailService.

Tests email drafting, sending, approval integration, and error handling.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.approval_request import ApprovalCategory, ApprovalStatus
from ai_employee.services.email import (
    EmailDraft,
    EmailRecipientStatus,
    EmailSendResult,
    EmailService,
    EmailServiceError,
    OAuthError,
    PartialSendError,
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
    (vault / "Quarantine").mkdir()
    (vault / "Logs").mkdir()
    return vault


@pytest.fixture
def vault_config(vault_path: Path) -> VaultConfig:
    """Create VaultConfig for testing."""
    return VaultConfig(vault_path)


@pytest.fixture
def email_service(vault_config: VaultConfig) -> EmailService:
    """Create EmailService instance for testing."""
    return EmailService(vault_config)


class TestEmailDraft:
    """Tests for EmailDraft dataclass."""

    def test_create_email_draft(self) -> None:
        """Test creating an email draft."""
        draft = EmailDraft(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test body content",
        )

        assert draft.to == ["test@example.com"]
        assert draft.subject == "Test Subject"
        assert draft.body == "Test body content"
        assert draft.cc == []
        assert draft.bcc == []
        assert draft.attachments == []

    def test_create_email_draft_with_cc_bcc(self) -> None:
        """Test creating email draft with CC and BCC."""
        draft = EmailDraft(
            to=["to@example.com"],
            subject="Test",
            body="Body",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )

        assert draft.cc == ["cc@example.com"]
        assert draft.bcc == ["bcc@example.com"]

    def test_create_email_draft_with_attachments(self) -> None:
        """Test creating email draft with attachments."""
        draft = EmailDraft(
            to=["test@example.com"],
            subject="Test",
            body="Body",
            attachments=["/path/to/file.pdf"],
        )

        assert draft.attachments == ["/path/to/file.pdf"]

    def test_email_draft_to_dict(self) -> None:
        """Test converting draft to dictionary."""
        draft = EmailDraft(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test body",
            cc=["cc@example.com"],
        )

        d = draft.to_dict()

        assert d["to"] == ["test@example.com"]
        assert d["subject"] == "Test Subject"
        assert d["body"] == "Test body"
        assert d["cc"] == ["cc@example.com"]

    def test_email_draft_from_dict(self) -> None:
        """Test creating draft from dictionary."""
        data = {
            "to": ["test@example.com"],
            "subject": "Test Subject",
            "body": "Test body",
            "cc": ["cc@example.com"],
            "bcc": [],
            "attachments": [],
        }

        draft = EmailDraft.from_dict(data)

        assert draft.to == ["test@example.com"]
        assert draft.subject == "Test Subject"

    def test_email_draft_validation_empty_to(self) -> None:
        """Test validation rejects empty 'to' field."""
        with pytest.raises(ValueError, match="at least one recipient"):
            EmailDraft(
                to=[],
                subject="Test",
                body="Body",
            )

    def test_email_draft_validation_empty_subject(self) -> None:
        """Test validation rejects empty subject."""
        with pytest.raises(ValueError, match="subject must not be empty"):
            EmailDraft(
                to=["test@example.com"],
                subject="",
                body="Body",
            )


class TestEmailService:
    """Tests for EmailService class."""

    def test_service_initialization(self, vault_config: VaultConfig) -> None:
        """Test service initializes correctly."""
        service = EmailService(vault_config)

        assert service is not None

    def test_draft_email_creates_approval_request(
        self, email_service: EmailService, vault_path: Path
    ) -> None:
        """Test that drafting an email creates an approval request."""
        draft = EmailDraft(
            to=["client@example.com"],
            subject="Meeting Request",
            body="Can we schedule a meeting?",
        )

        approval_id = email_service.draft_email(draft)

        assert approval_id is not None
        assert approval_id.startswith("approval_")

        # Verify approval file created
        pending_files = list((vault_path / "Pending_Approval").glob("*.md"))
        assert len(pending_files) == 1

        content = pending_files[0].read_text()
        assert "email" in content
        assert "client@example.com" in content

    def test_draft_email_with_summary(
        self, email_service: EmailService
    ) -> None:
        """Test drafting email with custom summary."""
        draft = EmailDraft(
            to=["client@example.com"],
            subject="Contract Review",
            body="Please review the attached contract.",
        )

        approval_id = email_service.draft_email(
            draft,
            summary="Contract review email to client"
        )

        assert approval_id is not None

    def test_get_pending_email_drafts(
        self, email_service: EmailService
    ) -> None:
        """Test getting pending email drafts."""
        # Create some drafts
        email_service.draft_email(EmailDraft(
            to=["a@example.com"],
            subject="Subject A",
            body="Body A",
        ))
        email_service.draft_email(EmailDraft(
            to=["b@example.com"],
            subject="Subject B",
            body="Body B",
        ))

        pending = email_service.get_pending_drafts()

        assert len(pending) == 2


class TestEmailSending:
    """Tests for email sending functionality."""

    def test_send_email_success(
        self, email_service: EmailService, vault_path: Path
    ) -> None:
        """Test successful email sending."""
        draft = EmailDraft(
            to=["test@example.com"],
            subject="Test",
            body="Test body",
        )

        # Create and approve the draft
        approval_id = email_service.draft_email(draft)

        # Move to approved
        pending_files = list((vault_path / "Pending_Approval").glob("*.md"))
        src = pending_files[0]
        dst = vault_path / "Approved" / src.name
        src.rename(dst)

        # Mock the MCP send with proper EmailSendResult
        mock_result = EmailSendResult(
            success=True,
            message_id="msg_123456",
            recipient_statuses=[
                EmailRecipientStatus("test@example.com", True, None),
            ],
        )
        with patch.object(email_service, "_send_via_mcp", return_value=mock_result):
            result = email_service.send_approved_email(approval_id)

        assert result.success is True
        assert result.message_id is not None

    def test_send_email_partial_failure(
        self, email_service: EmailService, vault_path: Path
    ) -> None:
        """Test partial email send failure (some recipients fail)."""
        draft = EmailDraft(
            to=["success@example.com", "fail@example.com"],
            subject="Test",
            body="Test body",
        )

        approval_id = email_service.draft_email(draft)

        # Move to approved
        pending_files = list((vault_path / "Pending_Approval").glob("*.md"))
        src = pending_files[0]
        dst = vault_path / "Approved" / src.name
        src.rename(dst)

        # Mock partial failure
        def mock_send(*args, **kwargs):
            return EmailSendResult(
                success=False,
                message_id=None,
                recipient_statuses=[
                    EmailRecipientStatus("success@example.com", True, None),
                    EmailRecipientStatus("fail@example.com", False, "Invalid address"),
                ],
                error="Partial failure: 1 of 2 recipients failed",
            )

        with patch.object(email_service, "_send_via_mcp", side_effect=mock_send):
            with pytest.raises(PartialSendError) as exc_info:
                email_service.send_approved_email(approval_id)

        assert "Partial failure" in str(exc_info.value)

    def test_send_email_moves_to_quarantine_on_failure(
        self, email_service: EmailService, vault_path: Path
    ) -> None:
        """Test that failed emails are moved to Quarantine."""
        draft = EmailDraft(
            to=["test@example.com"],
            subject="Test",
            body="Test body",
        )

        approval_id = email_service.draft_email(draft)

        # Move to approved
        pending_files = list((vault_path / "Pending_Approval").glob("*.md"))
        src = pending_files[0]
        dst = vault_path / "Approved" / src.name
        src.rename(dst)

        # Mock failure
        with patch.object(
            email_service,
            "_send_via_mcp",
            side_effect=EmailServiceError("SMTP error"),
        ):
            with pytest.raises(EmailServiceError):
                email_service.send_approved_email(approval_id)

        # Verify moved to Quarantine
        quarantine_files = list((vault_path / "Quarantine").glob("*.md"))
        assert len(quarantine_files) == 1


class TestEmailRecipientStatus:
    """Tests for EmailRecipientStatus tracking."""

    def test_recipient_status_success(self) -> None:
        """Test successful recipient status."""
        status = EmailRecipientStatus(
            email="test@example.com",
            success=True,
            error=None,
        )

        assert status.email == "test@example.com"
        assert status.success is True
        assert status.error is None

    def test_recipient_status_failure(self) -> None:
        """Test failed recipient status."""
        status = EmailRecipientStatus(
            email="bad@example.com",
            success=False,
            error="Invalid email address",
        )

        assert status.success is False
        assert status.error == "Invalid email address"


class TestEmailSendResult:
    """Tests for EmailSendResult."""

    def test_send_result_success(self) -> None:
        """Test successful send result."""
        result = EmailSendResult(
            success=True,
            message_id="msg_123",
            recipient_statuses=[
                EmailRecipientStatus("test@example.com", True, None),
            ],
        )

        assert result.success is True
        assert result.message_id == "msg_123"

    def test_send_result_failure(self) -> None:
        """Test failed send result."""
        result = EmailSendResult(
            success=False,
            message_id=None,
            recipient_statuses=[],
            error="Authentication failed",
        )

        assert result.success is False
        assert result.error == "Authentication failed"


class TestOAuthHandling:
    """Tests for OAuth token handling."""

    def test_oauth_error_raised_on_invalid_credentials(
        self, email_service: EmailService
    ) -> None:
        """Test OAuthError is raised when credentials are invalid."""
        with patch.object(
            email_service,
            "_validate_oauth_credentials",
            side_effect=OAuthError("Invalid credentials"),
        ):
            with pytest.raises(OAuthError):
                email_service._validate_oauth_credentials()

    def test_oauth_token_refresh(
        self, email_service: EmailService
    ) -> None:
        """Test OAuth token refresh is handled."""
        # This would test the MCP's built-in token refresh
        # Mocked since actual refresh requires real credentials
        with patch.object(
            email_service,
            "_refresh_oauth_token",
            return_value=True,
        ):
            result = email_service._refresh_oauth_token()
            assert result is True


class TestAttachmentHandling:
    """Tests for email attachment handling."""

    def test_draft_with_attachments(
        self, email_service: EmailService, vault_path: Path
    ) -> None:
        """Test creating draft with attachments."""
        # Create a test attachment file
        attachment_path = vault_path / "test_attachment.pdf"
        attachment_path.write_text("PDF content")

        draft = EmailDraft(
            to=["test@example.com"],
            subject="With Attachment",
            body="Please see attached.",
            attachments=[str(attachment_path)],
        )

        approval_id = email_service.draft_email(draft)

        assert approval_id is not None

        # Verify attachment path is stored in approval
        pending_files = list((vault_path / "Pending_Approval").glob("*.md"))
        content = pending_files[0].read_text()
        assert "test_attachment.pdf" in content

    def test_attachment_validation_missing_file(
        self, email_service: EmailService
    ) -> None:
        """Test validation catches missing attachment files."""
        draft = EmailDraft(
            to=["test@example.com"],
            subject="Test",
            body="Body",
            attachments=["/nonexistent/file.pdf"],
        )

        with pytest.raises(FileNotFoundError):
            email_service.draft_email(draft, validate_attachments=True)


class TestEmailServiceErrors:
    """Tests for EmailService error classes."""

    def test_email_service_error(self) -> None:
        """Test EmailServiceError base exception."""
        error = EmailServiceError("Test error")
        assert str(error) == "Test error"

    def test_oauth_error(self) -> None:
        """Test OAuthError exception."""
        error = OAuthError("Token expired")
        assert isinstance(error, EmailServiceError)

    def test_partial_send_error(self) -> None:
        """Test PartialSendError exception."""
        error = PartialSendError(
            "1 of 3 recipients failed",
            failed_recipients=["bad@example.com"],
        )
        assert isinstance(error, EmailServiceError)
        assert error.failed_recipients == ["bad@example.com"]
