#!/usr/bin/env python3
"""Manage scheduled tasks."""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def get_vault_path() -> Path:
    """Get vault path from environment or default."""
    vault = os.environ.get("VAULT_PATH", "~/AI_Employee_Vault")
    return Path(vault).expanduser()


def generate_id(name: str) -> str:
    """Generate schedule ID from name."""
    return "schedule_" + name.lower().replace(" ", "_")


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
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            result[key] = value

    return result


def list_schedules(vault: Path) -> dict:
    """List all scheduled tasks."""
    schedules_dir = vault / "Schedules"

    if not schedules_dir.exists():
        return {"success": True, "count": 0, "tasks": []}

    tasks = []

    for file in schedules_dir.glob("schedule_*.md"):
        content = file.read_text()
        fm = parse_frontmatter(content)

        tasks.append({
            "id": fm.get("id", file.stem),
            "name": fm.get("name", file.stem),
            "schedule": fm.get("schedule", ""),
            "enabled": fm.get("enabled", True),
            "last_run": fm.get("last_run"),
            "next_run": fm.get("next_run"),
            "file": str(file)
        })

    tasks.sort(key=lambda x: x.get("name", ""))

    return {
        "success": True,
        "count": len(tasks),
        "tasks": tasks
    }


def create_schedule(
    name: str,
    schedule: str,
    action: str,
    timezone: str,
    missed: str,
    vault: Path
) -> dict:
    """Create a new scheduled task."""
    schedules_dir = vault / "Schedules"
    schedules_dir.mkdir(parents=True, exist_ok=True)

    task_id = generate_id(name)
    now = datetime.now()

    # Determine if cron or one-time
    is_cron = " " in schedule

    content = f"""---
id: "{task_id}"
name: "{name}"
schedule: "{schedule}"
timezone: "{timezone}"
enabled: true
missed_strategy: "{missed}"
created_at: "{now.isoformat()}"
last_run: null
next_run: null
---

## Scheduled Task: {name}

**Schedule**: {schedule}
**Timezone**: {timezone}
**Type**: {"Recurring (cron)" if is_cron else "One-time"}
**Missed Strategy**: {missed}

### Action

```yaml
type: {action}
```

### Execution History

| Date | Time | Duration | Result |
|------|------|----------|--------|
| - | - | - | - |

---
*Created: {now.strftime("%Y-%m-%d %H:%M")}*
"""

    task_file = schedules_dir / f"{task_id}.md"
    task_file.write_text(content)

    return {
        "success": True,
        "task_id": task_id,
        "name": name,
        "schedule": schedule,
        "file": str(task_file)
    }


def toggle_schedule(task_id: str, enabled: bool, vault: Path) -> dict:
    """Enable or disable a scheduled task."""
    schedules_dir = vault / "Schedules"

    matching = list(schedules_dir.glob(f"*{task_id}*.md"))
    if not matching:
        return {"success": False, "error": f"Task not found: {task_id}"}

    task_file = matching[0]
    content = task_file.read_text()

    # Update enabled status
    if "enabled: true" in content:
        content = content.replace("enabled: true", f"enabled: {str(enabled).lower()}")
    elif "enabled: false" in content:
        content = content.replace("enabled: false", f"enabled: {str(enabled).lower()}")

    task_file.write_text(content)

    return {
        "success": True,
        "task_id": task_id,
        "enabled": enabled,
        "file": str(task_file)
    }


def delete_schedule(task_id: str, vault: Path) -> dict:
    """Delete a scheduled task."""
    schedules_dir = vault / "Schedules"

    matching = list(schedules_dir.glob(f"*{task_id}*.md"))
    if not matching:
        return {"success": False, "error": f"Task not found: {task_id}"}

    task_file = matching[0]
    task_file.unlink()

    return {
        "success": True,
        "task_id": task_id,
        "action": "deleted"
    }


def main():
    parser = argparse.ArgumentParser(description="Manage scheduled tasks")
    parser.add_argument("action", choices=["list", "create", "enable", "disable", "delete"],
                       nargs="?", default="list", help="Action to perform")
    parser.add_argument("--id", help="Task ID")
    parser.add_argument("--name", help="Task name (for create)")
    parser.add_argument("--schedule", help="Cron expression or ISO datetime")
    parser.add_argument("--action-type", default="custom", help="Action type")
    parser.add_argument("--timezone", default="local", help="Timezone")
    parser.add_argument("--missed", default="run", choices=["skip", "run", "queue"],
                       help="Missed schedule strategy")
    parser.add_argument("--vault", help="Vault path override")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()
    vault = Path(args.vault).expanduser() if args.vault else get_vault_path()

    if args.action == "list":
        result = list_schedules(vault)
    elif args.action == "create":
        if not args.name or not args.schedule:
            print("Error: --name and --schedule required for create", file=sys.stderr)
            sys.exit(1)
        result = create_schedule(
            args.name, args.schedule, args.action_type,
            args.timezone, args.missed, vault
        )
    elif args.action == "enable":
        if not args.id:
            print("Error: --id required", file=sys.stderr)
            sys.exit(1)
        result = toggle_schedule(args.id, True, vault)
    elif args.action == "disable":
        if not args.id:
            print("Error: --id required", file=sys.stderr)
            sys.exit(1)
        result = toggle_schedule(args.id, False, vault)
    elif args.action == "delete":
        if not args.id:
            print("Error: --id required", file=sys.stderr)
            sys.exit(1)
        result = delete_schedule(args.id, vault)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if args.action == "list":
            if result["count"] == 0:
                print("No scheduled tasks.")
            else:
                print(f"## Scheduled Tasks ({result['count']})\n")
                print("| ID | Name | Schedule | Status |")
                print("|----|------|----------|--------|")
                for t in result["tasks"]:
                    status = "✅ Enabled" if t["enabled"] else "⏸️ Disabled"
                    print(f"| {t['id']} | {t['name']} | {t['schedule']} | {status} |")
        elif result.get("success"):
            if args.action == "create":
                print(f"✅ Task created: {result['name']}")
                print(f"   ID: {result['task_id']}")
                print(f"   Schedule: {result['schedule']}")
                print(f"   File: {result['file']}")
            elif args.action in ("enable", "disable"):
                status = "enabled" if result["enabled"] else "disabled"
                print(f"✅ Task {status}: {result['task_id']}")
            elif args.action == "delete":
                print(f"✅ Task deleted: {result['task_id']}")
        else:
            print(f"❌ Error: {result['error']}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
