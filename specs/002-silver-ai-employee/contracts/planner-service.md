# Planner Service Contract

**Service**: `PlannerService`
**Module**: `src/ai_employee/services/planner.py`

## Overview

The Planner Service implements Claude's reasoning loop for breaking down complex tasks into step-by-step plans. It creates Plan.md files, tracks execution, and integrates with the approval workflow.

## Interface

```python
from pathlib import Path
from ai_employee.models.plan import Plan, PlanStep, PlanStatus, StepStatus
from ai_employee.services.approval import ApprovalService

class PlannerService:
    """Claude reasoning loop for multi-step task planning (FR-016 to FR-020)."""

    def __init__(
        self,
        vault_config: VaultConfig,
        approval_service: ApprovalService,
    ) -> None:
        """
        Initialize planner service.

        Args:
            vault_config: Vault configuration with paths
            approval_service: Service for creating approval requests
        """

    # ─────────────────────────────────────────────────────────────
    # Plan Creation (FR-016, FR-017)
    # ─────────────────────────────────────────────────────────────

    def create_plan(
        self,
        task_description: str,
        context: dict | None = None,
    ) -> Plan:
        """
        Analyze task and generate Plan.md (FR-016).

        Args:
            task_description: Natural language task description
            context: Additional context (files, data, constraints)

        Returns:
            Created Plan with numbered steps

        Side Effects:
            - Creates Plan.md file in /Plans/
            - Logs plan creation

        Plan.md includes (FR-017):
            - Objective
            - Numbered steps
            - Dependencies between steps
            - Approval requirements per step
            - Success criteria
        """

    def analyze_task_complexity(
        self,
        task_description: str,
    ) -> bool:
        """
        Determine if task requires a plan (multi-step).

        Args:
            task_description: Task to analyze

        Returns:
            True if task should generate Plan.md

        Note:
            Simple tasks (single action) don't need plans.
        """

    # ─────────────────────────────────────────────────────────────
    # Plan Execution (FR-018, FR-019)
    # ─────────────────────────────────────────────────────────────

    def execute_plan(self, plan: Plan) -> None:
        """
        Execute a plan step by step.

        Args:
            plan: Plan to execute

        Side Effects:
            - Updates plan status to IN_PROGRESS
            - Executes steps in dependency order
            - Creates approval requests for steps requiring approval
            - Pauses on approval requirements or failures (FR-019)
            - Updates Dashboard with plan status (FR-020)

        Note:
            Execution pauses and resumes automatically when
            approvals are granted or blocked.
        """

    def execute_step(
        self,
        plan: Plan,
        step: PlanStep,
    ) -> StepStatus:
        """
        Execute a single plan step.

        Args:
            plan: Parent plan
            step: Step to execute

        Returns:
            Final status of step

        Side Effects:
            - Updates step status
            - Creates approval request if requires_approval=True
            - Logs step execution
        """

    def pause_plan(
        self,
        plan: Plan,
        reason: str,
    ) -> None:
        """
        Pause plan execution (FR-019).

        Args:
            plan: Plan to pause
            reason: Why paused (approval_required, step_failed)

        Side Effects:
            - Updates plan status to PAUSED
            - Updates Plan.md file
            - Updates Dashboard
        """

    def resume_plan(self, plan: Plan) -> None:
        """
        Resume paused plan execution.

        Args:
            plan: Plan to resume

        Side Effects:
            - Continues from last incomplete step
            - Updates status to IN_PROGRESS
        """

    # ─────────────────────────────────────────────────────────────
    # Plan Completion (FR-018)
    # ─────────────────────────────────────────────────────────────

    def complete_plan(
        self,
        plan: Plan,
        summary: str,
    ) -> None:
        """
        Mark plan as completed and move to /Done/.

        Args:
            plan: Completed plan
            summary: Completion summary

        Side Effects:
            - Updates status to COMPLETED
            - Adds completion summary
            - Moves Plan.md to /Done/
            - Updates Dashboard
        """

    def fail_plan(
        self,
        plan: Plan,
        error: str,
    ) -> None:
        """
        Mark plan as failed.

        Args:
            plan: Failed plan
            error: Failure description

        Side Effects:
            - Updates status to FAILED
            - Logs failure
            - Updates Dashboard (FR-019)
        """

    # ─────────────────────────────────────────────────────────────
    # Query & Status (FR-020)
    # ─────────────────────────────────────────────────────────────

    def get_active_plans(self) -> list[Plan]:
        """
        Get all active (non-completed) plans.

        Returns:
            List of plans with status PENDING, IN_PROGRESS, or PAUSED
        """

    def get_plan_by_id(self, plan_id: str) -> Plan | None:
        """
        Get plan by ID.

        Args:
            plan_id: Plan identifier

        Returns:
            Plan if found, None otherwise
        """

    def get_plan_status_summary(self) -> dict:
        """
        Get summary for Dashboard (FR-020).

        Returns:
            {
                "active_plans": 2,
                "paused_plans": 1,
                "completed_today": 3,
                "plans": [
                    {"id": "...", "objective": "...", "status": "..."}
                ]
            }
        """
```

## Plan.md File Structure

```markdown
---
id: "plan_20260203_091500_xyz789"
objective: "Send weekly newsletter to all subscribers"
status: "in_progress"
created_at: "2026-02-03T09:15:00"
completed_at: null
---

# Plan: Send weekly newsletter to all subscribers

## Objective

Send the weekly newsletter summarizing company updates to all active subscribers.

## Success Criteria

- [ ] Newsletter content gathered from this week's updates
- [ ] Email template drafted with personalization
- [ ] All active subscribers receive the email
- [ ] Delivery rate > 95%

## Steps

### Step 1: Gather newsletter content
- **Status**: ✅ completed
- **Requires Approval**: No
- **Dependencies**: None
- **Completed**: 2026-02-03T09:16:00

Compile content from:
- Blog posts published this week
- Product updates
- Team announcements

### Step 2: Draft email template
- **Status**: ✅ completed
- **Requires Approval**: No
- **Dependencies**: Step 1
- **Completed**: 2026-02-03T09:18:00

Create email template with:
- Subject line
- Header with company logo
- Content sections
- Unsubscribe footer

### Step 3: Review subscriber list
- **Status**: ⏳ in_progress
- **Requires Approval**: No
- **Dependencies**: None

Query database for active subscribers.

### Step 4: Send newsletter
- **Status**: ⏸️ pending
- **Requires Approval**: Yes
- **Dependencies**: Step 2, Step 3

Send email to all subscribers. Requires approval before execution.

## Execution Log

| Time | Step | Action | Result |
|------|------|--------|--------|
| 09:15:00 | - | Plan created | - |
| 09:16:00 | 1 | Gather content | ✅ Success |
| 09:18:00 | 2 | Draft template | ✅ Success |
| 09:18:30 | 3 | Review subscribers | ⏳ Started |
```

## Step Execution Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        execute_plan()                             │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │ Get next pending step │
                    │ (respecting deps)     │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │ Check dependencies    │
                    │ all completed?        │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │ No              │ Yes             │
              ▼                 │                 ▼
        (wait/skip)             │     ┌───────────────────┐
                                │     │ requires_approval?│
                                │     └─────────┬─────────┘
                                │               │
                    ┌───────────┼───────────────┼───────────┐
                    │           │               │           │
                    │ Yes       │               │ No        │
                    ▼           │               ▼           │
        ┌───────────────────┐   │   ┌───────────────────┐   │
        │ Create approval   │   │   │ Execute step      │   │
        │ request           │   │   │ action            │   │
        └─────────┬─────────┘   │   └─────────┬─────────┘   │
                  │             │             │             │
                  ▼             │             ▼             │
        ┌───────────────────┐   │   ┌───────────────────┐   │
        │ PAUSE plan        │   │   │ Update status     │   │
        │ (awaiting)        │   │   │ (completed/failed)│   │
        └───────────────────┘   │   └─────────┬─────────┘   │
                                │             │             │
                                │             ▼             │
                                │   ┌───────────────────┐   │
                                │   │ More steps?       │   │
                                │   └─────────┬─────────┘   │
                                │             │             │
                                └─────────────┴─────────────┘
```

## Error Handling

```python
class PlannerError(Exception):
    """Base exception for planner service."""

class PlanCreationError(PlannerError):
    """Raised when plan creation fails."""

class StepExecutionError(PlannerError):
    """Raised when step execution fails."""

class DependencyError(PlannerError):
    """Raised when step dependencies cannot be resolved."""

class PlanNotFoundError(PlannerError):
    """Raised when plan ID not found."""
```

## Events & Logging

| Event | Log Level | Details |
|-------|-----------|---------|
| Plan created | INFO | plan_id, objective, step_count |
| Plan started | INFO | plan_id |
| Step started | INFO | plan_id, step_id, description |
| Step completed | INFO | plan_id, step_id, duration_ms |
| Step failed | ERROR | plan_id, step_id, error |
| Plan paused | WARNING | plan_id, reason |
| Plan resumed | INFO | plan_id |
| Plan completed | INFO | plan_id, total_duration_ms |
| Plan failed | ERROR | plan_id, failed_step, error |
