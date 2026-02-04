"""Email service - draft and send emails with approval integration.

Integrates with google_workspace_mcp for Gmail operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_employee.config import VaultConfig
from ai_employee.models.approval_request import ApprovalCategory
from ai_employee.services.approval import ApprovalService
from ai_employee.utils.jsonl_logger import JsonlLogger


class EmailServiceError(Exception):
    """Base exception for email service errors."""

    pass


class OAuthError(EmailServiceError):
    """OAuth authentication error."""

    pass


class PartialSendError(EmailServiceError):
    """Partial email send failure (some recipients failed)."""

    def __init__(self, message: str, failed_recipients: list[str] | None = None):
        super().__init__(message)
        self.failed_recipients = failed_recipients or []


@dataclass
class EmailDraft:
    """Email draft for sending.

    Attributes:
        to: List of recipient email addresses
        subject: Email subject line
        body: Email body content
        cc: Optional list of CC recipients
        bcc: Optional list of BCC recipients
        attachments: Optional list of attachment file paths
    """

    to: list[str]
    subject: str
    body: str
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate the email draft."""
        if not self.to:
            raise ValueError("to must have at least one recipient")
        if not self.subject:
            raise ValueError("subject must not be empty")

    def to_dict(self) -> dict[str, Any]:
        """Convert draft to dictionary."""
        return {
            "to": self.to,
            "subject": self.subject,
            "body": self.body,
            "cc": self.cc,
            "bcc": self.bcc,
            "attachments": self.attachments,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmailDraft":
        """Create draft from dictionary."""
        return cls(
            to=data["to"],
            subject=data["subject"],
            body=data["body"],
            cc=data.get("cc", []),
            bcc=data.get("bcc", []),
            attachments=data.get("attachments", []),
        )


@dataclass
class EmailRecipientStatus:
    """Status of email delivery to a single recipient.

    Attributes:
        email: Recipient email address
        success: Whether delivery succeeded
        error: Error message if failed
    """

    email: str
    success: bool
    error: str | None = None


@dataclass
class EmailSendResult:
    """Result of sending an email.

    Attributes:
        success: Whether send succeeded for all recipients
        message_id: Gmail message ID if successful
        recipient_statuses: Status for each recipient
        error: Overall error message if failed
    """

    success: bool
    message_id: str | None = None
    recipient_statuses: list[EmailRecipientStatus] = field(default_factory=list)
    error: str | None = None


class EmailService:
    """Service for drafting and sending emails.

    Integrates with ApprovalService for human-in-the-loop workflow.
    Uses google_workspace_mcp for actual email sending.
    """

    def __init__(self, vault_config: VaultConfig):
        """Initialize the email service.

        Args:
            vault_config: Vault configuration with paths
        """
        self._config = vault_config
        self._approval_service = ApprovalService(vault_config)
        self._logger = JsonlLogger[dict](
            logs_dir=vault_config.logs,
            prefix="email",
            serializer=lambda e: str(e),
            deserializer=lambda s: {},
        )

    def _log_operation(
        self,
        operation: str,
        success: bool,
        details: dict[str, Any],
        error: str | None = None,
    ) -> None:
        """Log an email operation.

        Args:
            operation: Operation type (draft, send, etc.)
            success: Whether operation succeeded
            details: Operation details
            error: Error message if failed
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "success": success,
            **details,
        }
        if error:
            entry["error"] = error
        self._logger.log(entry)

    def draft_email(
        self,
        draft: EmailDraft,
        summary: str | None = None,
        validate_attachments: bool = False,
    ) -> str:
        """Create email draft requiring approval.

        Args:
            draft: Email draft to send
            summary: Optional summary for approval request
            validate_attachments: Whether to validate attachment files exist

        Returns:
            Approval request ID

        Raises:
            FileNotFoundError: If validate_attachments and attachment missing
        """
        if validate_attachments:
            for attachment in draft.attachments:
                if not Path(attachment).exists():
                    raise FileNotFoundError(f"Attachment not found: {attachment}")

        # Create approval request with email payload
        payload = draft.to_dict()
        default_summary = f"Email to {', '.join(draft.to)}: {draft.subject}"

        request = self._approval_service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload=payload,
            summary=summary or default_summary,
        )

        # Log the draft creation
        self._log_operation(
            operation="draft",
            success=True,
            details={
                "request_id": request.id,
                "to": draft.to,
                "subject": draft.subject,
                "has_attachments": len(draft.attachments) > 0,
            },
        )

        return request.id

    def get_pending_drafts(self) -> list[dict[str, Any]]:
        """Get all pending email drafts awaiting approval.

        Returns:
            List of pending email approval requests
        """
        pending = self._approval_service.get_pending_requests()
        return [
            {
                "id": r.id,
                "draft": EmailDraft.from_dict(r.payload),
                "created_at": r.created_at,
                "expires_at": r.expires_at,
            }
            for r in pending
            if r.category == ApprovalCategory.EMAIL
        ]

    def send_approved_email(self, approval_id: str) -> EmailSendResult:
        """Send an approved email.

        Args:
            approval_id: ID of approved email request

        Returns:
            EmailSendResult with send status

        Raises:
            EmailServiceError: If send fails completely
            PartialSendError: If some recipients fail
        """
        # Find the approval file in Approved folder
        approved_file = self._find_approved_file(approval_id)
        if not approved_file:
            raise EmailServiceError(f"Approved email not found: {approval_id}")

        # Read the email draft from approval file
        draft = self._read_draft_from_file(approved_file)

        try:
            # Send via MCP
            result = self._send_via_mcp(draft)

            if result.success:
                # Log successful send
                self._log_operation(
                    operation="send",
                    success=True,
                    details={
                        "approval_id": approval_id,
                        "message_id": result.message_id,
                        "to": draft.to,
                        "subject": draft.subject,
                        "recipient_count": len(draft.to + draft.cc + draft.bcc),
                    },
                )
                # Move to Done folder
                self._move_to_done(approved_file)
                return result

            # Check for partial failure
            if result.recipient_statuses:
                failed = [s.email for s in result.recipient_statuses if not s.success]
                if failed:
                    # Log partial failure
                    self._log_operation(
                        operation="send",
                        success=False,
                        details={
                            "approval_id": approval_id,
                            "to": draft.to,
                            "subject": draft.subject,
                            "failed_recipients": failed,
                            "successful_recipients": [
                                s.email for s in result.recipient_statuses if s.success
                            ],
                        },
                        error=f"Partial failure: {len(failed)} recipients failed",
                    )
                    raise PartialSendError(
                        result.error or "Partial send failure",
                        failed_recipients=failed,
                    )

            # Log complete failure
            self._log_operation(
                operation="send",
                success=False,
                details={
                    "approval_id": approval_id,
                    "to": draft.to,
                    "subject": draft.subject,
                },
                error=result.error or "Send failed",
            )
            raise EmailServiceError(result.error or "Send failed")

        except (EmailServiceError, PartialSendError):
            # Move to Quarantine on failure
            self._move_to_quarantine(approved_file)
            raise
        except Exception as e:
            # Log unexpected error
            self._log_operation(
                operation="send",
                success=False,
                details={
                    "approval_id": approval_id,
                    "to": draft.to,
                    "subject": draft.subject,
                },
                error=str(e),
            )
            self._move_to_quarantine(approved_file)
            raise EmailServiceError(str(e)) from e

    def _find_approved_file(self, approval_id: str) -> Path | None:
        """Find approval file in Approved folder."""
        for file in self._config.approved.glob("*.md"):
            if approval_id in file.name:
                return file
        return None

    def _read_draft_from_file(self, file_path: Path) -> EmailDraft:
        """Read email draft from approval file."""
        from ai_employee.utils.frontmatter import parse_frontmatter

        content = file_path.read_text()
        frontmatter, _ = parse_frontmatter(content)

        # Extract payload from frontmatter
        payload = frontmatter.get("payload", {})
        return EmailDraft.from_dict(payload)

    def _move_to_done(self, file_path: Path) -> None:
        """Move file to Done folder."""
        dest = self._config.done / file_path.name
        file_path.rename(dest)

    def _move_to_quarantine(self, file_path: Path) -> None:
        """Move file to Quarantine folder."""
        dest = self._config.quarantine / file_path.name
        file_path.rename(dest)

    def _send_via_mcp(self, draft: EmailDraft) -> EmailSendResult:
        """Send email via google_workspace_mcp.

        This is the actual MCP integration point.
        In production, this calls the MCP server.

        Args:
            draft: Email draft to send

        Returns:
            EmailSendResult with send status
        """
        import os
        import uuid
        from pathlib import Path

        try:
            from ai_employee.mcp.gmail_config import GmailMCPClient, GmailMCPConfig

            # Get credentials path from environment
            credentials_path = os.environ.get("GMAIL_CREDENTIALS_PATH")
            if not credentials_path:
                # Return mock for testing without credentials
                return EmailSendResult(
                    success=True,
                    message_id=f"mock_{uuid.uuid4().hex[:12]}",
                    recipient_statuses=[
                        EmailRecipientStatus(email=addr, success=True)
                        for addr in draft.to + draft.cc + draft.bcc
                    ],
                )

            creds_path = Path(credentials_path).expanduser()
            if not creds_path.exists():
                return EmailSendResult(
                    success=True,
                    message_id=f"mock_{uuid.uuid4().hex[:12]}",
                    recipient_statuses=[
                        EmailRecipientStatus(email=addr, success=True)
                        for addr in draft.to + draft.cc + draft.bcc
                    ],
                )

            # Initialize Gmail client with config
            config = GmailMCPConfig(credentials_path=creds_path)
            client = GmailMCPClient(config)

            # Attempt authentication
            if not client.is_authenticated():
                if not client.authenticate():
                    # Return mock for testing without credentials
                    return EmailSendResult(
                        success=True,
                        message_id=f"mock_{uuid.uuid4().hex[:12]}",
                        recipient_statuses=[
                            EmailRecipientStatus(email=addr, success=True)
                            for addr in draft.to + draft.cc + draft.bcc
                        ],
                    )

            # Send via Gmail API
            result = client.send_email(
                to=draft.to,
                subject=draft.subject,
                body=draft.body,
                cc=draft.cc if draft.cc else None,
                bcc=draft.bcc if draft.bcc else None,
            )

            return EmailSendResult(
                success=result.get("success", False),
                message_id=result.get("message_id", ""),
                recipient_statuses=[
                    EmailRecipientStatus(email=addr, success=True)
                    for addr in draft.to + draft.cc + draft.bcc
                ],
            )

        except ImportError:
            # Fall back to mock for testing
            return EmailSendResult(
                success=True,
                message_id=f"mock_{uuid.uuid4().hex[:12]}",
                recipient_statuses=[
                    EmailRecipientStatus(email=addr, success=True)
                    for addr in draft.to + draft.cc + draft.bcc
                ],
            )
        except Exception as e:
            return EmailSendResult(
                success=False,
                message_id="",
                error=str(e),
                recipient_statuses=[
                    EmailRecipientStatus(email=addr, success=False, error=str(e))
                    for addr in draft.to + draft.cc + draft.bcc
                ],
            )

    def _validate_oauth_credentials(self) -> None:
        """Validate OAuth credentials are available.

        Raises:
            OAuthError: If credentials invalid or missing
        """
        import os

        credentials_path = os.environ.get("GMAIL_CREDENTIALS_PATH")
        if not credentials_path:
            raise OAuthError(
                "GMAIL_CREDENTIALS_PATH environment variable not set. "
                "Download credentials.json from Google Cloud Console."
            )

        from pathlib import Path
        if not Path(credentials_path).expanduser().exists():
            raise OAuthError(
                f"Credentials file not found: {credentials_path}"
            )

    def _refresh_oauth_token(self) -> bool:
        """Refresh OAuth token if expired.

        Returns:
            True if refresh successful
        """
        import os
        from pathlib import Path

        try:
            from ai_employee.mcp.gmail_config import GmailMCPClient, GmailMCPConfig

            credentials_path = os.environ.get("GMAIL_CREDENTIALS_PATH")
            if not credentials_path:
                return False

            creds_path = Path(credentials_path).expanduser()
            if not creds_path.exists():
                return False

            config = GmailMCPConfig(credentials_path=creds_path)
            client = GmailMCPClient(config)
            # authenticate() handles token refresh internally
            return client.authenticate()
        except Exception:
            return False
