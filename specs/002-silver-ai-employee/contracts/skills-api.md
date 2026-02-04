# Agent Skills API Contract

**Module**: `src/ai_employee/skills/`
**Skills Directory**: `.claude/skills/`

## Overview

Agent Skills are modular capabilities exposed to Claude Code via SKILL.md manifests. Each skill maps to a Python implementation that executes the requested action.

## Skills Defined (FR-031 to FR-035)

| Skill | Command | Module | Purpose |
|-------|---------|--------|---------|
| post-linkedin | `/post-linkedin` | `post_linkedin.py` | Schedule LinkedIn posts (FR-031) |
| create-plan | `/create-plan` | `create_plan.py` | Generate Plan.md files (FR-032) |
| send-email | `/send-email` | `send_email.py` | Draft emails with approval (FR-033) |
| approve-action | `/approve-action` | `approve_action.py` | List/approve pending actions (FR-034) |
| schedule-task | `/schedule-task` | `schedule_task.py` | Configure scheduled tasks (FR-035) |

---

## Skill Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class SkillResult:
    """Result of skill execution."""
    success: bool
    message: str
    data: dict[str, Any] | None = None
    files_created: list[str] | None = None
    approval_required: bool = False
    approval_id: str | None = None

class BaseSkill(ABC):
    """Base class for all skills."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Skill name (e.g., 'post-linkedin')."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description for SKILL.md."""

    @abstractmethod
    def execute(self, args: dict[str, Any]) -> SkillResult:
        """
        Execute the skill with given arguments.

        Args:
            args: Parsed arguments from skill invocation

        Returns:
            SkillResult with execution outcome
        """

    def validate_args(self, args: dict[str, Any]) -> list[str]:
        """
        Validate arguments before execution.

        Returns:
            List of validation error messages (empty if valid)
        """
        return []
```

---

## /post-linkedin Skill (FR-031)

### SKILL.md
```markdown
# /post-linkedin

Schedule a LinkedIn post for publishing.

## Usage

```
/post-linkedin <content> [--schedule <datetime>]
```

## Arguments

- `content` (required): Post text content (max 3000 characters)
- `--schedule` (optional): When to publish (ISO datetime or "now")

## Examples

```
/post-linkedin "Excited to share our latest product update!"
/post-linkedin "Weekly tips for productivity" --schedule "2026-02-04T10:00:00"
```

## Behavior

1. Creates post draft in `/Social/LinkedIn/posts/`
2. If scheduled, creates approval request in `/Pending_Approval/`
3. After approval, publishes at scheduled time
4. Tracks engagement in `/Social/LinkedIn/engagement.md`
```

### Implementation
```python
class PostLinkedInSkill(BaseSkill):
    """Schedule LinkedIn posts (FR-031)."""

    name = "post-linkedin"
    description = "Schedule a LinkedIn post"

    def __init__(
        self,
        linkedin_service: LinkedInService,
    ) -> None:
        self.linkedin = linkedin_service

    def execute(self, args: dict[str, Any]) -> SkillResult:
        content = args["content"]
        schedule = args.get("schedule")

        # Create post
        post = self.linkedin.create_post(
            content=content,
            scheduled_at=schedule,
        )

        if schedule:
            return SkillResult(
                success=True,
                message=f"Post scheduled for {schedule}. Approval required.",
                approval_required=True,
                approval_id=post.approval_request_id,
                files_created=[str(post.file_path)],
            )

        return SkillResult(
            success=True,
            message="Post draft created.",
            files_created=[str(post.file_path)],
        )
```

---

## /create-plan Skill (FR-032)

### SKILL.md
```markdown
# /create-plan

Generate a Plan.md file for a multi-step task.

## Usage

```
/create-plan <task_description>
```

## Arguments

- `task_description` (required): Natural language description of the task

## Examples

```
/create-plan "Send weekly newsletter to all subscribers"
/create-plan "Onboard new client: setup account, send welcome email, schedule intro call"
```

## Behavior

1. Analyzes task complexity
2. Breaks down into numbered steps
3. Identifies dependencies between steps
4. Marks steps requiring approval
5. Creates Plan.md in `/Plans/`
```

### Implementation
```python
class CreatePlanSkill(BaseSkill):
    """Generate Plan.md files (FR-032)."""

    name = "create-plan"
    description = "Create a multi-step plan"

    def __init__(
        self,
        planner_service: PlannerService,
    ) -> None:
        self.planner = planner_service

    def execute(self, args: dict[str, Any]) -> SkillResult:
        task_description = args["task_description"]

        # Check if plan needed
        if not self.planner.analyze_task_complexity(task_description):
            return SkillResult(
                success=True,
                message="Task is simple and doesn't require a plan.",
            )

        # Create plan
        plan = self.planner.create_plan(task_description)

        return SkillResult(
            success=True,
            message=f"Plan created with {len(plan.steps)} steps.",
            data={
                "plan_id": plan.id,
                "objective": plan.objective,
                "step_count": len(plan.steps),
                "approval_steps": sum(1 for s in plan.steps if s.requires_approval),
            },
            files_created=[str(plan.file_path)],
        )
```

---

## /send-email Skill (FR-033)

### SKILL.md
```markdown
# /send-email

Draft an email for approval and sending.

## Usage

```
/send-email --to <recipient> --subject <subject> --body <body> [--cc <cc>] [--attachments <files>]
```

## Arguments

- `--to` (required): Recipient email address
- `--subject` (required): Email subject line
- `--body` (required): Email body content
- `--cc` (optional): CC recipients (comma-separated)
- `--attachments` (optional): File paths (comma-separated)

## Examples

```
/send-email --to client@example.com --subject "Meeting Follow-up" --body "Thank you for meeting with us..."
/send-email --to team@company.com --subject "Weekly Report" --body "..." --attachments "/path/to/report.pdf"
```

## Behavior

1. Creates email draft
2. Creates approval request in `/Pending_Approval/`
3. After approval, sends via Gmail MCP
4. Logs result in activity log
```

### Implementation
```python
class SendEmailSkill(BaseSkill):
    """Draft emails for approval (FR-033)."""

    name = "send-email"
    description = "Draft and send an email (requires approval)"

    def __init__(
        self,
        approval_service: ApprovalService,
    ) -> None:
        self.approval = approval_service

    def execute(self, args: dict[str, Any]) -> SkillResult:
        # Create approval request for email
        request = self.approval.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={
                "to": args["to"],
                "cc": args.get("cc", []),
                "subject": args["subject"],
                "body": args["body"],
                "attachments": args.get("attachments", []),
            },
        )

        return SkillResult(
            success=True,
            message=f"Email draft created. Awaiting approval.",
            approval_required=True,
            approval_id=request.id,
            files_created=[str(request.file_path)],
            data={
                "to": args["to"],
                "subject": args["subject"],
                "expires_at": request.expires_at.isoformat(),
            },
        )
```

---

## /approve-action Skill (FR-034)

### SKILL.md
```markdown
# /approve-action

List and manage pending approval requests.

## Usage

```
/approve-action [list|approve|reject] [--id <approval_id>]
```

## Subcommands

- `list`: Show all pending approvals (default)
- `approve --id <id>`: Approve a specific request
- `reject --id <id>`: Reject a specific request

## Examples

```
/approve-action                    # List all pending
/approve-action list               # Same as above
/approve-action approve --id abc123
/approve-action reject --id abc123
```

## Behavior

- `list`: Shows pending requests with summary
- `approve`: Moves request to `/Approved/` for execution
- `reject`: Moves request to `/Rejected/`

Note: Approving/rejecting can also be done by moving files in Obsidian.
```

### Implementation
```python
class ApproveActionSkill(BaseSkill):
    """Manage approval requests (FR-034)."""

    name = "approve-action"
    description = "List and manage pending approvals"

    def __init__(
        self,
        approval_service: ApprovalService,
    ) -> None:
        self.approval = approval_service

    def execute(self, args: dict[str, Any]) -> SkillResult:
        action = args.get("action", "list")

        if action == "list":
            pending = self.approval.get_pending_requests()
            return SkillResult(
                success=True,
                message=f"Found {len(pending)} pending approvals.",
                data={
                    "pending_count": len(pending),
                    "requests": [
                        {
                            "id": r.id,
                            "category": r.category.value,
                            "created": r.created_at.isoformat(),
                            "expires": r.expires_at.isoformat(),
                        }
                        for r in pending
                    ],
                },
            )

        request_id = args.get("id")
        if not request_id:
            return SkillResult(
                success=False,
                message="--id required for approve/reject",
            )

        if action == "approve":
            # Implementation would move file to /Approved/
            return SkillResult(
                success=True,
                message=f"Approval {request_id} approved. Will execute shortly.",
            )

        if action == "reject":
            # Implementation would move file to /Rejected/
            return SkillResult(
                success=True,
                message=f"Approval {request_id} rejected.",
            )
```

---

## /schedule-task Skill (FR-035)

### SKILL.md
```markdown
# /schedule-task

Configure recurring or one-time scheduled tasks.

## Usage

```
/schedule-task <action> [options]
```

## Actions

- `create`: Create a new scheduled task
- `list`: List all scheduled tasks
- `enable`: Enable a disabled task
- `disable`: Disable a task
- `delete`: Delete a task

## Options

- `--name`: Task name (required for create)
- `--schedule`: Cron expression or ISO datetime
- `--action`: Action type (briefing, audit, custom)
- `--id`: Task ID (for enable/disable/delete)

## Examples

```
/schedule-task list
/schedule-task create --name "Daily Standup Reminder" --schedule "0 9 * * 1-5" --action briefing
/schedule-task create --name "Quarterly Report" --schedule "2026-04-01T09:00:00" --action audit
/schedule-task disable --id schedule_daily_briefing
```

## Cron Expression Format

```
minute hour day_of_month month day_of_week
  0     8      *           *        *      = Daily at 8:00 AM
  0     21     *           *        0      = Weekly Sunday 9:00 PM
  0     9      *           *       1-5     = Weekdays at 9:00 AM
```
```

### Implementation
```python
class ScheduleTaskSkill(BaseSkill):
    """Configure scheduled tasks (FR-035)."""

    name = "schedule-task"
    description = "Manage scheduled tasks"

    def __init__(
        self,
        scheduler_service: SchedulerService,
    ) -> None:
        self.scheduler = scheduler_service

    def execute(self, args: dict[str, Any]) -> SkillResult:
        action = args.get("action", "list")

        if action == "list":
            tasks = self.scheduler.get_all_tasks()
            return SkillResult(
                success=True,
                message=f"Found {len(tasks)} scheduled tasks.",
                data={
                    "tasks": [
                        {
                            "id": t.id,
                            "name": t.name,
                            "schedule": t.schedule,
                            "enabled": t.enabled,
                            "next_run": t.next_run.isoformat() if t.next_run else None,
                        }
                        for t in tasks
                    ],
                },
            )

        if action == "create":
            schedule = args["schedule"]
            is_cron = " " in schedule  # Cron has spaces

            if is_cron:
                task = self.scheduler.create_recurring_task(
                    name=args["name"],
                    cron_expression=schedule,
                    action={"type": args["action_type"]},
                )
            else:
                task = self.scheduler.create_one_time_task(
                    name=args["name"],
                    run_at=datetime.fromisoformat(schedule),
                    action={"type": args["action_type"]},
                )

            return SkillResult(
                success=True,
                message=f"Task '{task.name}' scheduled.",
                files_created=[str(task.file_path)],
            )

        # enable, disable, delete implementations...
```

---

## SKILL.md Template

```markdown
# /<skill-name>

<Short description of what the skill does>

## Usage

```
/<skill-name> <required_args> [optional_args]
```

## Arguments

- `<arg_name>` (required|optional): Description
- `--flag`: Flag description

## Examples

```
/<skill-name> example_usage
```

## Behavior

1. Step 1 of what happens
2. Step 2
3. Step 3

## Notes

Any additional notes or warnings.
```

---

## CLI Integration

```python
# src/ai_employee/cli/main.py additions

def cmd_skill(args: argparse.Namespace) -> int:
    """Execute a skill from CLI."""
    from ai_employee.skills import get_skill

    skill = get_skill(args.skill_name)
    if not skill:
        print(f"Unknown skill: {args.skill_name}")
        return 1

    result = skill.execute(vars(args))

    if result.success:
        print(result.message)
        if result.files_created:
            print(f"Files created: {', '.join(result.files_created)}")
        if result.approval_required:
            print(f"Approval ID: {result.approval_id}")
        return 0
    else:
        print(f"Error: {result.message}")
        return 1
```
