#!/usr/bin/env python3
"""Create an email approval request."""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


def get_vault_path() -> Path:
    """Get vault path from environment or default."""
    vault = os.environ.get("VAULT_PATH", "~/AI_Employee_Vault")
    return Path(vault).expanduser()


def generate_id() -> str:
    """Generate unique ID."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_email_request(
    to: str,
    subject: str,
    body: str,
    cc: list[str] | None,
    bcc: list[str] | None,
    attachments: list[str] | None,
    vault: Path
) -> dict:
    """Create email approval request file."""
    request_id = f"email_{generate_id()}"
    now = datetime.now()
    expires_at = now + timedelta(hours=24)

    pending_dir = vault / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)

    cc_list = cc or []
    bcc_list = bcc or []
    attachment_list = attachments or []

    # Validate attachments exist
    missing = [a for a in attachment_list if not Path(a).exists()]
    if missing:
        return {"success": False, "error": f"Attachments not found: {missing}"}

    cc_yaml = "\n".join(f"    - {e}" for e in cc_list) if cc_list else ""
    bcc_yaml = "\n".join(f"    - {e}" for e in bcc_list) if bcc_list else ""
    attach_yaml = "\n".join(f"    - {a}" for a in attachment_list) if attachment_list else ""

    content = f"""---
id: "{request_id}"
category: "email"
status: "pending"
created_at: "{now.isoformat()}"
expires_at: "{expires_at.isoformat()}"
payload:
  to: "{to}"
  cc: [{", ".join(f'"{e}"' for e in cc_list)}]
  bcc: [{", ".join(f'"{e}"' for e in bcc_list)}]
  subject: "{subject}"
  body: |
    {body.replace(chr(10), chr(10) + "    ")}
  attachments: [{", ".join(f'"{a}"' for a in attachment_list)}]
---

## Email Approval Request

**To**: {to}
{f"**CC**: {', '.join(cc_list)}" if cc_list else ""}
{f"**BCC**: {', '.join(bcc_list)}" if bcc_list else ""}
**Subject**: {subject}

### Body

{body}

{f"### Attachments" if attachment_list else ""}
{chr(10).join(f"- {a}" for a in attachment_list) if attachment_list else ""}

---
**Created**: {now.strftime("%Y-%m-%d %H:%M")}
**Expires**: {expires_at.strftime("%Y-%m-%d %H:%M")}

*Move to /Approved/ to send, or /Rejected/ to cancel*
*Expires in 24 hours*
"""

    approval_file = pending_dir / f"APPROVAL_{request_id}.md"
    approval_file.write_text(content)

    return {
        "success": True,
        "request_id": request_id,
        "approval_file": str(approval_file),
        "to": to,
        "subject": subject,
        "expires_at": expires_at.isoformat()
    }


def main():
    parser = argparse.ArgumentParser(description="Create email approval request")
    parser.add_argument("--to", required=True, help="Recipient email")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", required=True, help="Email body")
    parser.add_argument("--cc", help="CC recipients (comma-separated)")
    parser.add_argument("--bcc", help="BCC recipients (comma-separated)")
    parser.add_argument("--attachments", help="Attachment paths (comma-separated)")
    parser.add_argument("--vault", help="Vault path override")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    vault = Path(args.vault).expanduser() if args.vault else get_vault_path()
    cc = [e.strip() for e in args.cc.split(",")] if args.cc else None
    bcc = [e.strip() for e in args.bcc.split(",")] if args.bcc else None
    attachments = [a.strip() for a in args.attachments.split(",")] if args.attachments else None

    result = create_email_request(
        args.to, args.subject, args.body, cc, bcc, attachments, vault
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"✅ Email approval request created: {result['request_id']}")
            print(f"   To: {result['to']}")
            print(f"   Subject: {result['subject']}")
            print(f"   File: {result['approval_file']}")
            print(f"   Expires: {result['expires_at']}")
        else:
            print(f"❌ Error: {result['error']}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
