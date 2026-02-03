#!/usr/bin/env python3
"""Create a LinkedIn post draft with approval request."""

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
    """Generate unique post ID."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_post_file(content: str, schedule: str | None, vault: Path) -> dict:
    """Create LinkedIn post draft and approval request."""
    post_id = f"linkedin_{generate_id()}"

    # Validate content length
    if len(content) > 3000:
        return {"success": False, "error": "Content exceeds 3000 character limit"}

    # Create directories
    posts_dir = vault / "Social" / "LinkedIn" / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    pending_dir = vault / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)

    # Determine schedule
    now = datetime.now()
    scheduled_at = None
    if schedule:
        if schedule.lower() == "now":
            scheduled_at = now
        else:
            try:
                scheduled_at = datetime.fromisoformat(schedule)
            except ValueError:
                return {"success": False, "error": f"Invalid datetime format: {schedule}"}

    expires_at = now + timedelta(hours=24)

    # Create post draft
    post_content = f"""---
id: "{post_id}"
content: "{content[:100]}..."
status: "pending_approval"
scheduled_at: {f'"{scheduled_at.isoformat()}"' if scheduled_at else 'null'}
created_at: "{now.isoformat()}"
---

## LinkedIn Post Draft

**Status**: Pending Approval
**Created**: {now.strftime("%Y-%m-%d %H:%M")}
{f'**Scheduled**: {scheduled_at.strftime("%Y-%m-%d %H:%M")}' if scheduled_at else ''}

### Content

{content}

---
*Character count: {len(content)}/3000*
"""

    post_file = posts_dir / f"{post_id}.md"
    post_file.write_text(post_content)

    # Create approval request
    approval_id = f"approval_{post_id}"
    approval_content = f"""---
id: "{approval_id}"
category: "social_post"
status: "pending"
created_at: "{now.isoformat()}"
expires_at: "{expires_at.isoformat()}"
payload:
  platform: "linkedin"
  post_id: "{post_id}"
  content: |
    {content}
  scheduled_at: {f'"{scheduled_at.isoformat()}"' if scheduled_at else 'null'}
---

## LinkedIn Post Approval

**Platform**: LinkedIn
**Created**: {now.strftime("%Y-%m-%d %H:%M")}
**Expires**: {expires_at.strftime("%Y-%m-%d %H:%M")}
{f'**Scheduled**: {scheduled_at.strftime("%Y-%m-%d %H:%M")}' if scheduled_at else ''}

### Content Preview

{content}

---
*Move to /Approved/ to publish, or /Rejected/ to cancel*
*Expires in 24 hours*
"""

    approval_file = pending_dir / f"APPROVAL_social_{post_id}.md"
    approval_file.write_text(approval_content)

    return {
        "success": True,
        "post_id": post_id,
        "approval_id": approval_id,
        "post_file": str(post_file),
        "approval_file": str(approval_file),
        "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
        "expires_at": expires_at.isoformat(),
        "char_count": len(content)
    }


def main():
    parser = argparse.ArgumentParser(description="Create LinkedIn post draft")
    parser.add_argument("content", help="Post content")
    parser.add_argument("--schedule", help="Schedule time (ISO datetime or 'now')")
    parser.add_argument("--vault", help="Vault path override")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    vault = Path(args.vault).expanduser() if args.vault else get_vault_path()
    result = create_post_file(args.content, args.schedule, vault)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"✅ LinkedIn post created: {result['post_id']}")
            print(f"   Post file: {result['post_file']}")
            print(f"   Approval file: {result['approval_file']}")
            if result["scheduled_at"]:
                print(f"   Scheduled for: {result['scheduled_at']}")
            print(f"   Expires: {result['expires_at']}")
        else:
            print(f"❌ Error: {result['error']}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
