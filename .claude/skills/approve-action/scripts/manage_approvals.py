#!/usr/bin/env python3
"""List and manage pending approval requests.

This script integrates with the ApprovalService when available,
falling back to direct file operations for compatibility.
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


def get_vault_path() -> Path:
    """Get vault path from environment or default."""
    vault = os.environ.get("VAULT_PATH", "~/AI_Employee_Vault")
    return Path(vault).expanduser()


def get_approval_service(vault: Path):
    """Try to get ApprovalService if ai_employee is installed."""
    try:
        from ai_employee.config import VaultConfig
        from ai_employee.services.approval import ApprovalService
        config = VaultConfig(root=vault)
        return ApprovalService(config)
    except ImportError:
        return None


def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown file."""
    if not content.startswith("---"):
        return {}

    end = content.find("---", 3)
    if end == -1:
        return {}

    frontmatter = content[3:end].strip()
    result = {}

    for line in frontmatter.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            result[key] = value

    return result


def list_approvals(vault: Path) -> dict:
    """List all pending approval requests."""
    # Try using ApprovalService if available
    service = get_approval_service(vault)
    if service:
        try:
            requests = service.get_pending_requests()
            approvals = []
            for req in requests:
                time_remaining = req.time_remaining()
                hours = int(time_remaining.total_seconds() // 3600)
                approvals.append({
                    "id": req.id,
                    "category": req.category.value,
                    "file": str(vault / "Pending_Approval" / req.get_filename()),
                    "created_at": req.created_at.isoformat(),
                    "expires_at": req.expires_at.isoformat(),
                    "time_remaining": f"{hours}h" if hours > 0 else "EXPIRED",
                    "is_expired": req.is_expired(),
                    "summary": req.summary or _get_summary_from_payload(req.category.value, req.payload)
                })
            return {"success": True, "count": len(approvals), "approvals": approvals}
        except Exception:
            pass  # Fall back to file-based approach

    pending_dir = vault / "Pending_Approval"

    if not pending_dir.exists():
        return {"success": True, "count": 0, "approvals": []}

    approvals = []
    now = datetime.now()

    for file in pending_dir.glob("APPROVAL_*.md"):
        content = file.read_text()
        fm = parse_frontmatter(content)

        created = fm.get("created_at", "")
        expires = fm.get("expires_at", "")
        category = fm.get("category", "unknown")
        approval_id = fm.get("id", file.stem)

        # Calculate time remaining
        time_remaining = ""
        is_expired = False
        if expires:
            try:
                exp_dt = datetime.fromisoformat(expires)
                delta = exp_dt - now
                if delta.total_seconds() < 0:
                    is_expired = True
                    time_remaining = "EXPIRED"
                else:
                    hours = int(delta.total_seconds() // 3600)
                    time_remaining = f"{hours}h"
            except ValueError:
                pass

        # Extract summary from content
        summary = ""
        if category == "email":
            to_match = re.search(r'\*\*To\*\*:\s*(.+)', content)
            subj_match = re.search(r'\*\*Subject\*\*:\s*(.+)', content)
            if to_match and subj_match:
                summary = f"To: {to_match.group(1)[:20]}... Subject: {subj_match.group(1)[:20]}..."
        elif category == "social_post":
            summary = "LinkedIn post"

        approvals.append({
            "id": approval_id,
            "category": category,
            "file": str(file),
            "created_at": created,
            "expires_at": expires,
            "time_remaining": time_remaining,
            "is_expired": is_expired,
            "summary": summary
        })

    # Sort by created time
    approvals.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return {
        "success": True,
        "count": len(approvals),
        "approvals": approvals
    }


def _get_summary_from_payload(category: str, payload: dict) -> str:
    """Generate summary from payload based on category."""
    if category == "email":
        to = payload.get("to", "")[:20]
        subject = payload.get("subject", "")[:20]
        return f"To: {to}... Subject: {subject}..."
    elif category == "social_post":
        return "LinkedIn post"
    elif category == "payment":
        amount = payload.get("amount", 0)
        recipient = payload.get("recipient", "")[:15]
        return f"${amount} to {recipient}"
    return ""


def approve_request(approval_id: str, vault: Path) -> dict:
    """Move approval request to Approved folder."""
    pending_dir = vault / "Pending_Approval"
    approved_dir = vault / "Approved"
    approved_dir.mkdir(parents=True, exist_ok=True)

    # Find the file
    matching = list(pending_dir.glob(f"*{approval_id}*.md"))
    if not matching:
        return {"success": False, "error": f"Approval not found: {approval_id}"}

    src_file = matching[0]
    dst_file = approved_dir / src_file.name

    shutil.move(str(src_file), str(dst_file))

    return {
        "success": True,
        "approval_id": approval_id,
        "action": "approved",
        "file": str(dst_file)
    }


def reject_request(approval_id: str, vault: Path) -> dict:
    """Move approval request to Rejected folder."""
    pending_dir = vault / "Pending_Approval"
    rejected_dir = vault / "Rejected"
    rejected_dir.mkdir(parents=True, exist_ok=True)

    # Find the file
    matching = list(pending_dir.glob(f"*{approval_id}*.md"))
    if not matching:
        return {"success": False, "error": f"Approval not found: {approval_id}"}

    src_file = matching[0]
    dst_file = rejected_dir / src_file.name

    shutil.move(str(src_file), str(dst_file))

    return {
        "success": True,
        "approval_id": approval_id,
        "action": "rejected",
        "file": str(dst_file)
    }


def main():
    parser = argparse.ArgumentParser(description="Manage approval requests")
    parser.add_argument("action", choices=["list", "approve", "reject"],
                       nargs="?", default="list", help="Action to perform")
    parser.add_argument("--id", help="Approval ID (for approve/reject)")
    parser.add_argument("--vault", help="Vault path override")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()
    vault = Path(args.vault).expanduser() if args.vault else get_vault_path()

    if args.action == "list":
        result = list_approvals(vault)
    elif args.action == "approve":
        if not args.id:
            print("Error: --id required for approve action", file=sys.stderr)
            sys.exit(1)
        result = approve_request(args.id, vault)
    elif args.action == "reject":
        if not args.id:
            print("Error: --id required for reject action", file=sys.stderr)
            sys.exit(1)
        result = reject_request(args.id, vault)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if args.action == "list":
            if result["count"] == 0:
                print("No pending approvals.")
            else:
                print(f"## Pending Approvals ({result['count']})\n")
                print("| ID | Category | Expires | Summary |")
                print("|----|----------|---------|---------|")
                for a in result["approvals"]:
                    print(f"| {a['id'][:15]}... | {a['category']} | {a['time_remaining']} | {a['summary'][:30]} |")
        else:
            if result["success"]:
                print(f"✅ {result['action'].capitalize()}: {result['approval_id']}")
                print(f"   File: {result['file']}")
            else:
                print(f"❌ Error: {result['error']}", file=sys.stderr)
                sys.exit(1)


if __name__ == "__main__":
    main()
