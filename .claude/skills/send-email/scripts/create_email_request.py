#!/usr/bin/env python3
"""Create an email approval request using EmailService."""

import argparse
import json
import os
import sys
from pathlib import Path


def get_vault_path() -> Path:
    """Get vault path from environment or default."""
    vault = os.environ.get("VAULT_PATH", "~/AI_Employee_Vault")
    return Path(vault).expanduser()


def create_email_request(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None,
    bcc: list[str] | None,
    attachments: list[str] | None,
    vault: Path,
    validate_attachments: bool = True,
) -> dict:
    """Create email approval request using EmailService.

    Args:
        to: List of recipient email addresses
        subject: Email subject
        body: Email body content
        cc: Optional CC recipients
        bcc: Optional BCC recipients
        attachments: Optional attachment file paths
        vault: Vault path
        validate_attachments: Whether to validate attachment files exist

    Returns:
        Dict with success status and request details
    """
    try:
        from ai_employee.config import VaultConfig
        from ai_employee.services.email import EmailDraft, EmailService

        vault_config = VaultConfig(vault)
        email_service = EmailService(vault_config)

        draft = EmailDraft(
            to=to,
            subject=subject,
            body=body,
            cc=cc or [],
            bcc=bcc or [],
            attachments=attachments or [],
        )

        approval_id = email_service.draft_email(
            draft,
            summary=f"Email to {', '.join(to)}: {subject}",
            validate_attachments=validate_attachments,
        )

        # Find the created approval file
        approval_file = None
        for f in vault_config.pending_approval.glob("*.md"):
            if approval_id in f.name:
                approval_file = f
                break

        # Get expiration from approval service
        from ai_employee.services.approval import ApprovalService
        approval_service = ApprovalService(vault_config)
        request = None
        for r in approval_service.get_pending_requests():
            if r.id == approval_id:
                request = r
                break

        return {
            "success": True,
            "request_id": approval_id,
            "approval_file": str(approval_file) if approval_file else None,
            "to": to,
            "subject": subject,
            "expires_at": request.expires_at.isoformat() if request else None,
        }

    except FileNotFoundError as e:
        return {"success": False, "error": f"Attachment not found: {e}"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Failed to create email request: {e}"}


def main():
    parser = argparse.ArgumentParser(description="Create email approval request")
    parser.add_argument("--to", required=True, help="Recipient email(s), comma-separated")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", required=True, help="Email body")
    parser.add_argument("--cc", help="CC recipients (comma-separated)")
    parser.add_argument("--bcc", help="BCC recipients (comma-separated)")
    parser.add_argument("--attachments", help="Attachment paths (comma-separated)")
    parser.add_argument("--vault", help="Vault path override")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip attachment file validation"
    )

    args = parser.parse_args()

    vault = Path(args.vault).expanduser() if args.vault else get_vault_path()
    to = [e.strip() for e in args.to.split(",")]
    cc = [e.strip() for e in args.cc.split(",")] if args.cc else None
    bcc = [e.strip() for e in args.bcc.split(",")] if args.bcc else None
    attachments = [a.strip() for a in args.attachments.split(",")] if args.attachments else None

    result = create_email_request(
        to=to,
        subject=args.subject,
        body=args.body,
        cc=cc,
        bcc=bcc,
        attachments=attachments,
        vault=vault,
        validate_attachments=not args.skip_validation,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"✅ Email approval request created: {result['request_id']}")
            print(f"   To: {', '.join(result['to'])}")
            print(f"   Subject: {result['subject']}")
            if result.get("approval_file"):
                print(f"   File: {result['approval_file']}")
            if result.get("expires_at"):
                print(f"   Expires: {result['expires_at']}")
        else:
            print(f"❌ Error: {result['error']}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
