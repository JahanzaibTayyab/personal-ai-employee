#!/usr/bin/env python3
"""Create a LinkedIn post draft with approval request using LinkedInService."""

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


def create_post_via_service(content: str, schedule: str | None, vault: Path) -> dict:
    """Create LinkedIn post using LinkedInService."""
    try:
        from ai_employee.config import VaultConfig
        from ai_employee.services.linkedin import LinkedInService, RateLimitError
        from ai_employee.models.linkedin_post import LINKEDIN_MAX_CHARS

        # Validate content length early
        if len(content) > LINKEDIN_MAX_CHARS:
            return {"success": False, "error": f"Content exceeds {LINKEDIN_MAX_CHARS} character limit"}

        vault_config = VaultConfig(root=vault)
        service = LinkedInService(vault_config)

        # Determine schedule time
        now = datetime.now()
        if schedule:
            if schedule.lower() == "now":
                scheduled_at = now + timedelta(minutes=5)  # Schedule 5 min from now
            else:
                try:
                    scheduled_at = datetime.fromisoformat(schedule)
                except ValueError:
                    return {"success": False, "error": f"Invalid datetime format: {schedule}"}
        else:
            scheduled_at = now + timedelta(hours=1)  # Default: 1 hour from now

        # Schedule the post (creates approval request)
        approval_id = service.schedule_post(
            content=content,
            scheduled_time=scheduled_at,
        )

        # Get pending posts count
        posts_today = service.get_posts_today()
        pending_posts = service.get_pending_posts()

        return {
            "success": True,
            "approval_id": approval_id,
            "scheduled_at": scheduled_at.isoformat(),
            "char_count": len(content),
            "posts_today": posts_today,
            "pending_count": len(pending_posts),
            "rate_limit_remaining": 25 - posts_today,
        }

    except RateLimitError as e:
        return {"success": False, "error": str(e)}
    except ImportError as e:
        # Fallback to standalone creation if ai_employee not installed
        return create_post_standalone(content, schedule, vault)
    except Exception as e:
        return {"success": False, "error": f"Service error: {str(e)}"}


def create_post_standalone(content: str, schedule: str | None, vault: Path) -> dict:
    """Fallback: Create LinkedIn post without service dependency."""
    post_id = f"linkedin_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if len(content) > 3000:
        return {"success": False, "error": "Content exceeds 3000 character limit"}

    # Create directories
    posts_dir = vault / "Social" / "LinkedIn" / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    pending_dir = vault / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    scheduled_at = None
    if schedule:
        if schedule.lower() == "now":
            scheduled_at = now + timedelta(minutes=5)
        else:
            try:
                scheduled_at = datetime.fromisoformat(schedule)
            except ValueError:
                return {"success": False, "error": f"Invalid datetime format: {schedule}"}
    else:
        scheduled_at = now + timedelta(hours=1)

    expires_at = now + timedelta(hours=24)

    # Create post draft
    post_content = f"""---
id: "{post_id}"
status: "pending_approval"
scheduled_at: "{scheduled_at.isoformat() if scheduled_at else ''}"
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
  scheduled_at: "{scheduled_at.isoformat() if scheduled_at else ''}"
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
        "approval_id": approval_id,
        "post_file": str(post_file),
        "approval_file": str(approval_file),
        "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
        "char_count": len(content),
        "mode": "standalone",
    }


def main():
    parser = argparse.ArgumentParser(description="Create LinkedIn post draft")
    parser.add_argument("content", help="Post content")
    parser.add_argument("--schedule", help="Schedule time (ISO datetime or 'now')")
    parser.add_argument("--vault", help="Vault path override")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--standalone", action="store_true", help="Use standalone mode (skip service)")

    args = parser.parse_args()

    vault = Path(args.vault).expanduser() if args.vault else get_vault_path()

    if args.standalone:
        result = create_post_standalone(args.content, args.schedule, vault)
    else:
        result = create_post_via_service(args.content, args.schedule, vault)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"LinkedIn post created: {result['approval_id']}")
            print(f"   Scheduled for: {result['scheduled_at']}")
            print(f"   Characters: {result['char_count']}/3000")
            if "rate_limit_remaining" in result:
                print(f"   Rate limit remaining: {result['rate_limit_remaining']}/25")
            if result.get("mode") == "standalone":
                print(f"   Mode: standalone (service not available)")
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
