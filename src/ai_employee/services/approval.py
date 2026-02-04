"""Approval service for human-in-the-loop workflow.

Manages sensitive action approvals with file-based workflow:
- Creates approval requests in /Pending_Approval/
- Monitors /Approved/ and /Rejected/ folders
- Executes approved actions
- Auto-rejects expired requests
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ai_employee.config import VaultConfig
from ai_employee.models.approval_request import (
    ApprovalCategory,
    ApprovalRequest,
    ApprovalStatus,
)
from ai_employee.utils.frontmatter import generate_frontmatter, parse_frontmatter


class ApprovalError(Exception):
    """Base exception for approval service."""


class ApprovalExpiredError(ApprovalError):
    """Raised when attempting to execute expired approval."""


class ExecutionError(ApprovalError):
    """Raised when action execution fails."""


class InvalidPayloadError(ApprovalError):
    """Raised when payload validation fails."""


# Required fields by category
REQUIRED_FIELDS: dict[ApprovalCategory, list[str]] = {
    ApprovalCategory.EMAIL: ["to"],
    ApprovalCategory.PAYMENT: ["amount"],
    ApprovalCategory.SOCIAL_POST: ["content"],
    ApprovalCategory.FILE_OPERATION: ["operation", "source"],
    ApprovalCategory.CUSTOM: [],  # No required fields for custom
}


class ApprovalService:
    """Service for managing human-in-the-loop approval workflow."""

    def __init__(self, vault_config: VaultConfig) -> None:
        """Initialize with vault configuration."""
        self._config = vault_config

    def _validate_payload(
        self,
        category: ApprovalCategory,
        payload: dict[str, Any],
    ) -> None:
        """Validate payload has required fields for category."""
        required = REQUIRED_FIELDS.get(category, [])
        for field in required:
            if field not in payload:
                raise InvalidPayloadError(
                    f"'{field}' field is required for {category.value} approval"
                )

    def _generate_id(self) -> str:
        """Generate unique approval request ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique = uuid.uuid4().hex[:8]
        return f"approval_{timestamp}_{unique}"

    def _read_approval_file(self, file_path: Path) -> ApprovalRequest | None:
        """Read and parse an approval request file."""
        if not file_path.exists():
            return None

        content = file_path.read_text()
        frontmatter, body = parse_frontmatter(content)

        if not frontmatter:
            return None

        return ApprovalRequest.from_frontmatter(frontmatter)

    def _write_approval_file(
        self,
        request: ApprovalRequest,
        folder: Path,
    ) -> Path:
        """Write approval request to a markdown file."""
        file_path = folder / request.get_filename()

        # Build body content with payload details
        body_lines = [
            f"# Approval Request: {request.category.value.title()}",
            "",
            f"**ID**: {request.id}",
            f"**Status**: {request.status.value}",
            f"**Created**: {request.created_at.isoformat()}",
            f"**Expires**: {request.expires_at.isoformat()}",
            "",
            "## Payload",
            "",
        ]

        for key, value in request.payload.items():
            body_lines.append(f"- **{key}**: {value}")

        body = "\n".join(body_lines)

        content = generate_frontmatter(request.to_frontmatter(), body)
        file_path.write_text(content)

        return file_path

    def _list_approval_files(self, folder: Path) -> list[ApprovalRequest]:
        """List all approval requests in a folder."""
        requests: list[ApprovalRequest] = []
        if not folder.exists():
            return requests

        for file_path in folder.glob("APPROVAL_*.md"):
            request = self._read_approval_file(file_path)
            if request:
                requests.append(request)

        return requests

    # ─────────────────────────────────────────────────────────────
    # Creation (FR-001)
    # ─────────────────────────────────────────────────────────────

    def create_approval_request(
        self,
        category: ApprovalCategory,
        payload: dict[str, Any],
        expiration_hours: int = 24,
        summary: str | None = None,
    ) -> ApprovalRequest:
        """
        Create an approval request file in /Pending_Approval/.

        Args:
            category: Type of action (email, social_post, payment, etc.)
            payload: Action-specific data
            expiration_hours: Hours until auto-expiration (default: 24)
            summary: Optional human-readable summary

        Returns:
            Created ApprovalRequest with generated ID

        Raises:
            InvalidPayloadError: If payload is missing required fields
        """
        self._validate_payload(category, payload)

        request = ApprovalRequest.create(
            id=self._generate_id(),
            category=category,
            payload=payload,
            summary=summary or "",
            expiration_hours=expiration_hours,
        )

        self._write_approval_file(request, self._config.pending_approval)

        return request

    # ─────────────────────────────────────────────────────────────
    # Monitoring (FR-002, FR-003)
    # ─────────────────────────────────────────────────────────────

    def get_pending_requests(self) -> list[ApprovalRequest]:
        """Get all pending approval requests."""
        return self._list_approval_files(self._config.pending_approval)

    def get_approved_requests(self) -> list[ApprovalRequest]:
        """Get all approved requests ready for execution."""
        return self._list_approval_files(self._config.approved)

    def get_rejected_requests(self) -> list[ApprovalRequest]:
        """Get all rejected requests."""
        return self._list_approval_files(self._config.rejected)

    # ─────────────────────────────────────────────────────────────
    # Direct Approve/Reject (for dashboard/API use)
    # ─────────────────────────────────────────────────────────────

    def approve_request(self, approval_id: str) -> ApprovalRequest:
        """
        Approve a pending request by ID.

        Moves the request file from Pending_Approval to Approved folder.

        Args:
            approval_id: The approval request ID

        Returns:
            The approved request

        Raises:
            ApprovalError: If request not found or already processed
        """
        # Find the pending request
        pending = self.get_pending_requests()
        request = next((r for r in pending if r.id == approval_id), None)

        if not request:
            raise ApprovalError(f"Pending approval not found: {approval_id}")

        if request.is_expired():
            raise ApprovalExpiredError(f"Approval has expired: {approval_id}")

        # Update status
        approved_request = ApprovalRequest(
            id=request.id,
            category=request.category,
            payload=request.payload,
            created_at=request.created_at,
            expires_at=request.expires_at,
            status=ApprovalStatus.APPROVED,
            summary=request.summary,
        )

        # Move file from Pending to Approved
        src = self._config.pending_approval / request.get_filename()
        if src.exists():
            self._write_approval_file(approved_request, self._config.approved)
            src.unlink()

        return approved_request

    def reject_request(self, approval_id: str, reason: str = "") -> ApprovalRequest:
        """
        Reject a pending request by ID.

        Moves the request file from Pending_Approval to Rejected folder.

        Args:
            approval_id: The approval request ID
            reason: Optional rejection reason

        Returns:
            The rejected request

        Raises:
            ApprovalError: If request not found or already processed
        """
        # Find the pending request
        pending = self.get_pending_requests()
        request = next((r for r in pending if r.id == approval_id), None)

        if not request:
            raise ApprovalError(f"Pending approval not found: {approval_id}")

        # Update status
        rejected_request = ApprovalRequest(
            id=request.id,
            category=request.category,
            payload=request.payload,
            created_at=request.created_at,
            expires_at=request.expires_at,
            status=ApprovalStatus.REJECTED,
            summary=request.summary,
        )

        # Move file from Pending to Rejected
        src = self._config.pending_approval / request.get_filename()
        if src.exists():
            self._write_approval_file(rejected_request, self._config.rejected)
            src.unlink()

        return rejected_request

    # ─────────────────────────────────────────────────────────────
    # Expiration (FR-004, FR-004a)
    # ─────────────────────────────────────────────────────────────

    def check_expired_requests(self) -> list[ApprovalRequest]:
        """
        Find and auto-reject expired pending requests.

        Returns:
            List of newly expired requests
        """
        expired = []
        pending_folder = self._config.pending_approval
        rejected_folder = self._config.rejected

        for request in self.get_pending_requests():
            if request.is_expired():
                # Update status to EXPIRED
                expired_request = ApprovalRequest(
                    id=request.id,
                    category=request.category,
                    payload=request.payload,
                    created_at=request.created_at,
                    expires_at=request.expires_at,
                    status=ApprovalStatus.EXPIRED,
                    summary=request.summary,
                )

                # Move file to Rejected folder
                src = pending_folder / request.get_filename()
                dst = rejected_folder / request.get_filename()

                if src.exists():
                    # Write updated status first
                    self._write_approval_file(expired_request, rejected_folder)
                    src.unlink()

                expired.append(expired_request)

        return expired

    # ─────────────────────────────────────────────────────────────
    # Execution (FR-002)
    # ─────────────────────────────────────────────────────────────

    def execute_approved_request(
        self,
        request: ApprovalRequest,
    ) -> bool:
        """
        Execute an approved action request.

        Args:
            request: The approved request to execute

        Returns:
            True if execution succeeded

        Raises:
            ApprovalExpiredError: If request has expired
            ExecutionError: If action fails
        """
        # Check if expiry time has passed (regardless of status)
        if datetime.now() > request.expires_at:
            raise ApprovalExpiredError(
                f"Approval request {request.id} has expired"
            )

        # Execute based on category
        success = False
        if request.category == ApprovalCategory.EMAIL:
            success = self._execute_email(request)
        elif request.category == ApprovalCategory.SOCIAL_POST:
            success = self._execute_social_post(request)
        elif request.category == ApprovalCategory.PAYMENT:
            success = self._execute_payment(request)
        elif request.category == ApprovalCategory.FILE_OPERATION:
            success = self._execute_file_operation(request)
        elif request.category == ApprovalCategory.CUSTOM:
            success = self._execute_custom(request)

        if success:
            # Update status and move to Done
            executed_request = ApprovalRequest(
                id=request.id,
                category=request.category,
                payload=request.payload,
                created_at=request.created_at,
                expires_at=request.expires_at,
                status=ApprovalStatus.EXECUTED,
                summary=request.summary,
            )

            # Move file to Done folder
            src = self._config.approved / request.get_filename()
            if src.exists():
                self._write_approval_file(executed_request, self._config.done)
                src.unlink()

        return success

    def _execute_email(self, request: ApprovalRequest) -> bool:
        """Execute email action. Override or inject for actual implementation."""
        # Placeholder - actual implementation in EmailService
        return True

    def _execute_social_post(self, request: ApprovalRequest) -> bool:
        """Execute social post action. Override for actual implementation."""
        # Placeholder - actual implementation in LinkedInService
        return True

    def _execute_payment(self, request: ApprovalRequest) -> bool:
        """Execute payment action. Override for actual implementation."""
        # Placeholder - requires payment provider integration
        return True

    def _execute_file_operation(self, request: ApprovalRequest) -> bool:
        """Execute file operation action."""
        payload = request.payload
        operation = payload.get("operation")
        source = Path(payload.get("source", ""))
        destination = payload.get("destination")

        if operation == "delete" and source.exists():
            source.unlink()
            return True
        elif operation == "move" and source.exists() and destination:
            source.rename(Path(destination))
            return True
        elif operation == "copy" and source.exists() and destination:
            import shutil
            shutil.copy2(source, destination)
            return True

        return False

    def _execute_custom(self, request: ApprovalRequest) -> bool:
        """Execute custom action. Override for actual implementation."""
        # Custom actions require external handling
        return True

    def process_approval_queue(self) -> tuple[int, int]:
        """
        Process all approved requests sequentially (FR-004b).

        Returns:
            Tuple of (success_count, failure_count)
        """
        approved = self.get_approved_requests()
        success_count = 0
        failure_count = 0

        # Process one at a time in detection order
        for request in approved:
            try:
                if self.execute_approved_request(request):
                    success_count += 1
                else:
                    failure_count += 1
            except (ApprovalExpiredError, ExecutionError):
                failure_count += 1

        return success_count, failure_count

    # ─────────────────────────────────────────────────────────────
    # Query (FR-005)
    # ─────────────────────────────────────────────────────────────

    def get_requests_by_category(
        self,
        category: ApprovalCategory,
    ) -> list[ApprovalRequest]:
        """Get all pending requests of a specific category."""
        return [
            r for r in self.get_pending_requests()
            if r.category == category
        ]
