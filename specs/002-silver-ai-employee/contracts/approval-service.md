# Approval Service Contract

**Service**: `ApprovalService`
**Module**: `src/ai_employee/services/approval.py`

## Overview

The Approval Service manages the human-in-the-loop workflow for sensitive actions. It creates approval requests, monitors folder changes, and executes approved actions.

## Interface

```python
from pathlib import Path
from datetime import datetime, timedelta
from ai_employee.models.approval_request import ApprovalRequest, ApprovalCategory, ApprovalStatus

class ApprovalService:
    """Service for managing human-in-the-loop approval workflow."""

    def __init__(self, vault_config: VaultConfig) -> None:
        """Initialize with vault configuration."""

    # ─────────────────────────────────────────────────────────────
    # Creation (FR-001)
    # ─────────────────────────────────────────────────────────────

    def create_approval_request(
        self,
        category: ApprovalCategory,
        payload: dict,
        expiration_hours: int = 24,
    ) -> ApprovalRequest:
        """
        Create an approval request file in /Pending_Approval/.

        Args:
            category: Type of action (email, social_post, payment, etc.)
            payload: Action-specific data (to, subject, body for email)
            expiration_hours: Hours until auto-expiration (default: 24)

        Returns:
            Created ApprovalRequest with generated ID

        Side Effects:
            - Creates markdown file in /Pending_Approval/
            - Logs creation to activity log
        """

    # ─────────────────────────────────────────────────────────────
    # Monitoring (FR-002, FR-003)
    # ─────────────────────────────────────────────────────────────

    def get_pending_requests(self) -> list[ApprovalRequest]:
        """
        Get all pending approval requests.

        Returns:
            List of ApprovalRequest objects from /Pending_Approval/
        """

    def get_approved_requests(self) -> list[ApprovalRequest]:
        """
        Get all approved requests ready for execution.

        Returns:
            List of ApprovalRequest objects from /Approved/
        """

    def get_rejected_requests(self) -> list[ApprovalRequest]:
        """
        Get all rejected requests.

        Returns:
            List of ApprovalRequest objects from /Rejected/
        """

    # ─────────────────────────────────────────────────────────────
    # Expiration (FR-004, FR-004a)
    # ─────────────────────────────────────────────────────────────

    def check_expired_requests(self) -> list[ApprovalRequest]:
        """
        Find and auto-reject expired pending requests.

        Returns:
            List of newly expired requests

        Side Effects:
            - Moves expired files to /Rejected/
            - Updates status to EXPIRED
            - Updates Dashboard with stale items flag
            - Logs expiration events
        """

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

        Side Effects:
            - Performs the action (send email, post to LinkedIn, etc.)
            - Moves file to /Done/
            - Updates status to EXECUTED
            - Logs execution result

        Raises:
            ExecutionError: If action fails
        """

    def process_approval_queue(self) -> tuple[int, int]:
        """
        Process all approved requests sequentially (FR-004b).

        Returns:
            Tuple of (success_count, failure_count)

        Note:
            Processes one at a time in detection order to handle
            concurrent approvals safely.
        """

    # ─────────────────────────────────────────────────────────────
    # Query (FR-005)
    # ─────────────────────────────────────────────────────────────

    def get_requests_by_category(
        self,
        category: ApprovalCategory,
    ) -> list[ApprovalRequest]:
        """
        Get all requests of a specific category.

        Args:
            category: Category to filter by

        Returns:
            List of matching ApprovalRequest objects
        """
```

## Folder Watcher Integration

```python
class ApprovalWatcher(BaseWatcher):
    """Watches approval folders for changes."""

    def __init__(self, vault_path: Path) -> None:
        """
        Initialize approval folder watcher.

        Monitors:
            - /Pending_Approval/ for new requests
            - /Approved/ for user approvals
            - /Rejected/ for user rejections
        """

    def on_file_moved(
        self,
        src_path: Path,
        dest_path: Path,
    ) -> None:
        """
        Handle file move events (user approval/rejection).

        Args:
            src_path: Original file location
            dest_path: New file location

        Side Effects:
            - If moved to /Approved/: queue for execution
            - If moved to /Rejected/: log rejection
        """
```

## Payload Schemas by Category

### Email (FR-001)
```python
email_payload = {
    "to": "recipient@example.com",
    "cc": ["cc@example.com"],  # optional
    "bcc": ["bcc@example.com"],  # optional
    "subject": "Email Subject",
    "body": "Email body content...",
    "attachments": ["/path/to/file"],  # optional
}
```

### Social Post (FR-001)
```python
social_payload = {
    "platform": "linkedin",
    "content": "Post content...",
    "scheduled_at": "2026-02-04T10:00:00",  # optional
    "media": ["/path/to/image"],  # optional
}
```

### Payment (FR-001)
```python
payment_payload = {
    "amount": 100.00,
    "currency": "USD",
    "recipient": "vendor@example.com",
    "description": "Invoice #1234",
    "invoice_id": "INV-1234",  # optional
}
```

### File Operation (FR-001)
```python
file_payload = {
    "operation": "delete|move|copy",
    "source": "/path/to/source",
    "destination": "/path/to/dest",  # for move/copy
    "reason": "Cleanup old files",
}
```

## Error Handling

```python
class ApprovalError(Exception):
    """Base exception for approval service."""

class ApprovalExpiredError(ApprovalError):
    """Raised when attempting to execute expired approval."""

class ExecutionError(ApprovalError):
    """Raised when action execution fails."""

class InvalidPayloadError(ApprovalError):
    """Raised when payload validation fails."""
```

## Events & Logging

| Event | Log Level | Details |
|-------|-----------|---------|
| Request created | INFO | category, id, expires_at |
| Request approved | INFO | id, approval_time |
| Request rejected | INFO | id, rejection_time |
| Request expired | WARNING | id, was_pending_for |
| Execution started | INFO | id, category |
| Execution succeeded | INFO | id, duration_ms |
| Execution failed | ERROR | id, error_message |
