"""Planner service - create and manage Plan.md files with step-by-step task breakdowns.

Implements the Claude reasoning loop for breaking down complex tasks.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from ai_employee.config import VaultConfig
from ai_employee.models.approval_request import ApprovalCategory
from ai_employee.models.plan import Plan, PlanStatus, PlanStep, StepStatus
from ai_employee.services.approval import ApprovalService
from ai_employee.utils.frontmatter import generate_frontmatter, parse_frontmatter
from ai_employee.utils.jsonl_logger import JsonlLogger


class PlannerService:
    """Service for creating and managing Plan.md files.

    Creates step-by-step task breakdowns with:
    - Plain language descriptions (no code blocks)
    - Verb-first action steps
    - Progress tracking symbols
    - Approval integration for sensitive steps
    """

    def __init__(self, vault_config: VaultConfig):
        """Initialize the planner service.

        Args:
            vault_config: Vault configuration with paths
        """
        self._config = vault_config
        self._approval_service = ApprovalService(vault_config)
        self._logger = JsonlLogger[dict](
            logs_dir=vault_config.logs,
            prefix="planner",
            serializer=lambda e: str(e),
            deserializer=lambda s: {},
        )

    def _log_operation(
        self,
        operation: str,
        plan_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log a planner operation."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "plan_id": plan_id,
            **(details or {}),
        }
        self._logger.log(entry)

    def analyze_task(self, task_description: str) -> dict[str, Any]:
        """Analyze a task to determine complexity and breakdown strategy.

        Args:
            task_description: Description of the task to analyze

        Returns:
            Analysis including objective, complexity, suggested steps
        """
        # Simple heuristic analysis
        words = task_description.lower().split()
        step_indicators = ["then", "and", "after", "before", "finally", "first"]
        action_verbs = ["send", "create", "review", "compile", "research", "schedule"]

        has_multiple_steps = any(ind in words for ind in step_indicators)
        action_count = sum(1 for v in action_verbs if v in words)

        if has_multiple_steps or action_count > 1:
            complexity = "complex"
        else:
            complexity = "simple"

        return {
            "objective": task_description,
            "complexity": complexity,
            "estimated_steps": max(1, action_count) if complexity == "simple" else action_count + 2,
        }

    def create_plan(
        self,
        task: str,
        objective: str,
        steps: list[dict[str, Any]] | None = None,
    ) -> Plan:
        """Create a new plan from task description.

        Args:
            task: Brief task name
            objective: What the plan aims to accomplish
            steps: Optional list of step definitions

        Returns:
            Created Plan instance

        Raises:
            ValueError: If objective is empty
        """
        if not objective or not objective.strip():
            raise ValueError("objective must not be empty")

        # Generate plan ID with unique suffix
        import uuid
        unique = uuid.uuid4().hex[:6]
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{unique}"

        # Create steps
        plan_steps: list[PlanStep] = []
        if steps:
            for i, step_def in enumerate(steps):
                plan_steps.append(PlanStep(
                    id=f"step_{i + 1}",
                    plan_id=plan_id,
                    order=i + 1,
                    description=step_def["description"],
                    status=StepStatus.PENDING,
                    requires_approval=step_def.get("requires_approval", False),
                    file_references=step_def.get("file_references", []),
                ))
        else:
            # Generate default step based on task
            plan_steps.append(PlanStep(
                id="step_1",
                plan_id=plan_id,
                order=1,
                description=f"Complete: {task}",
                status=StepStatus.PENDING,
                requires_approval=False,
            ))

        # Create plan
        plan = Plan(
            id=plan_id,
            objective=objective,
            steps=plan_steps,
            status=PlanStatus.PENDING,
            created_at=datetime.now(),
        )

        # Save to file
        self._save_plan(plan)

        self._log_operation("create", plan_id, {
            "objective": objective,
            "step_count": len(plan_steps),
        })

        return plan

    def _save_plan(self, plan: Plan) -> None:
        """Save plan to markdown file."""
        plans_dir = self._config.plans
        plans_dir.mkdir(parents=True, exist_ok=True)

        file_path = plans_dir / f"PLAN_{plan.id}.md"
        content = self._generate_plan_markdown(plan)
        file_path.write_text(content)

    def _generate_plan_markdown(self, plan: Plan) -> str:
        """Generate Plan.md content in plain language format (SC-010).

        No code blocks, verb-first steps, progress symbols.
        """
        frontmatter = {
            "id": plan.id,
            "status": plan.status.value,
            "created_at": plan.created_at.isoformat(),
            "objective": plan.objective,
        }

        lines = [
            generate_frontmatter(frontmatter),
            "",
            f"# Plan: {plan.objective}",
            "",
            "## Objective",
            "",
            plan.objective,
            "",
            "## Steps",
            "",
        ]

        for step in plan.steps:
            # Progress symbol based on status
            if step.status == StepStatus.COMPLETED:
                symbol = "[x]"
            elif step.status == StepStatus.IN_PROGRESS:
                symbol = "[~]"
            elif step.status == StepStatus.FAILED:
                symbol = "[!]"
            elif step.status == StepStatus.AWAITING_APPROVAL:
                symbol = "[?]"
            else:
                symbol = "[ ]"

            approval_note = " *(requires approval)*" if step.requires_approval else ""
            lines.append(f"{step.order}. {symbol} {step.description}{approval_note}")

            if step.file_references:
                for ref in step.file_references:
                    lines.append(f"   - References: {ref}")

        lines.extend([
            "",
            "## Status",
            "",
            f"**Current**: {plan.status.value}",
            f"**Created**: {plan.created_at.strftime('%Y-%m-%d %H:%M')}",
        ])

        if plan.completed_at:
            lines.append(f"**Completed**: {plan.completed_at.strftime('%Y-%m-%d %H:%M')}")

        lines.extend([
            "",
            "---",
            "*Auto-generated by AI Employee Planner*",
        ])

        return "\n".join(lines)

    def get_plan(self, plan_id: str) -> Plan | None:
        """Retrieve a plan by ID.

        Args:
            plan_id: Plan ID to retrieve

        Returns:
            Plan if found, None otherwise
        """
        # Check Plans folder
        plan_file = self._config.plans / f"PLAN_{plan_id}.md"
        if plan_file.exists():
            return self._load_plan(plan_file)

        # Check Done folder
        for file in self._config.done.glob(f"*{plan_id}*.md"):
            return self._load_plan(file)

        return None

    def _load_plan(self, file_path: Path) -> Plan:
        """Load plan from markdown file."""
        content = file_path.read_text()
        frontmatter, body = parse_frontmatter(content)

        plan_id = frontmatter["id"]
        # Parse steps from markdown body
        steps = self._parse_steps_from_markdown(body, plan_id)

        return Plan(
            id=frontmatter["id"],
            objective=frontmatter["objective"],
            steps=steps,
            status=PlanStatus(frontmatter["status"]),
            created_at=datetime.fromisoformat(frontmatter["created_at"]),
            completed_at=datetime.fromisoformat(frontmatter["completed_at"]) if frontmatter.get("completed_at") else None,
        )

    def _parse_steps_from_markdown(self, markdown: str, plan_id: str) -> list[PlanStep]:
        """Parse steps from Plan.md body content."""
        import re

        steps = []
        in_steps = False
        current_step = None

        for line in markdown.split("\n"):
            if "## Steps" in line:
                in_steps = True
                continue
            if line.startswith("## ") and in_steps:
                break

            if in_steps and line.strip():
                # Parse step line: "1. [x] Description *(requires approval)*"
                match = re.match(r"(\d+)\.\s*\[(.)\]\s*(.+?)(\s*\*\(requires approval\)\*)?$", line.strip())
                if match:
                    # Save previous step if exists
                    if current_step:
                        steps.append(current_step)

                    order = int(match.group(1))
                    symbol = match.group(2)
                    description = match.group(3).strip()
                    requires_approval = bool(match.group(4))

                    # Map symbol to status
                    status_map = {
                        "x": StepStatus.COMPLETED,
                        "~": StepStatus.IN_PROGRESS,
                        "!": StepStatus.FAILED,
                        "?": StepStatus.AWAITING_APPROVAL,
                        " ": StepStatus.PENDING,
                    }
                    status = status_map.get(symbol, StepStatus.PENDING)

                    current_step = PlanStep(
                        id=f"step_{order}",
                        plan_id=plan_id,
                        order=order,
                        description=description,
                        status=status,
                        requires_approval=requires_approval,
                    )
                elif current_step and line.strip().startswith("- References:"):
                    # Parse file reference line
                    ref = line.strip().replace("- References:", "").strip()
                    current_step.file_references.append(ref)

        # Add last step
        if current_step:
            steps.append(current_step)

        return steps

    def get_active_plans(self) -> list[Plan]:
        """Get all active (non-completed) plans.

        Returns:
            List of active plans
        """
        plans = []
        for file in self._config.plans.glob("PLAN_*.md"):
            plan = self._load_plan(file)
            if plan.status != PlanStatus.COMPLETED:
                plans.append(plan)
        return plans

    def start_plan(self, plan_id: str) -> None:
        """Start executing a plan.

        Args:
            plan_id: Plan ID to start

        Raises:
            ValueError: If plan not found
        """
        plan = self.get_plan(plan_id)
        if plan is None:
            raise ValueError(f"Plan not found: {plan_id}")

        plan.status = PlanStatus.IN_PROGRESS
        self._save_plan(plan)

        self._log_operation("start", plan_id)

    def start_step(self, plan_id: str, step_order: int) -> None:
        """Start a specific step.

        If step requires approval, creates approval request and pauses plan.

        Args:
            plan_id: Plan ID
            step_order: Order (1-indexed) of step to start
        """
        plan = self.get_plan(plan_id)
        if plan is None:
            raise ValueError(f"Plan not found: {plan_id}")

        step = self._find_step_by_order(plan, step_order)
        if step is None:
            raise ValueError(f"Step with order {step_order} not found")

        if step.requires_approval:
            # Create approval request and pause
            self._approval_service.create_approval_request(
                category=ApprovalCategory.CUSTOM,
                payload={
                    "plan_id": plan_id,
                    "step_order": step_order,
                    "step_description": step.description,
                },
                summary=f"Plan step approval: {step.description}",
            )
            step.status = StepStatus.AWAITING_APPROVAL
            plan.status = PlanStatus.PAUSED
        else:
            step.status = StepStatus.IN_PROGRESS

        self._save_plan(plan)

        self._log_operation("start_step", plan_id, {"step_order": step_order})

    def _find_step_by_order(self, plan: Plan, step_order: int) -> PlanStep | None:
        """Find a step by its order number."""
        for step in plan.steps:
            if step.order == step_order:
                return step
        return None

    def complete_step(self, plan_id: str, step_order: int) -> None:
        """Mark a step as completed.

        Args:
            plan_id: Plan ID
            step_order: Order (1-indexed) of step to complete

        Raises:
            ValueError: If plan or step not found
        """
        plan = self.get_plan(plan_id)
        if plan is None:
            raise ValueError(f"Plan not found: {plan_id}")

        step = self._find_step_by_order(plan, step_order)
        if step is None:
            raise ValueError(f"Step with order {step_order} not found")

        step.status = StepStatus.COMPLETED
        step.completed_at = datetime.now()

        # Check if all steps completed
        if all(s.status == StepStatus.COMPLETED for s in plan.steps):
            plan.status = PlanStatus.COMPLETED
            plan.completed_at = datetime.now()
            self._move_to_done(plan)
        else:
            self._save_plan(plan)

        self._log_operation("complete_step", plan_id, {"step_order": step_order})

    def fail_step(
        self,
        plan_id: str,
        step_order: int,
        error: str,
    ) -> None:
        """Mark a step as failed and pause the plan.

        Args:
            plan_id: Plan ID
            step_order: Order (1-indexed) of failed step
            error: Error message
        """
        plan = self.get_plan(plan_id)
        if plan is None:
            raise ValueError(f"Plan not found: {plan_id}")

        step = self._find_step_by_order(plan, step_order)
        if step is None:
            raise ValueError(f"Step with order {step_order} not found")

        step.status = StepStatus.FAILED
        step.error = error
        plan.status = PlanStatus.PAUSED

        self._save_plan(plan)

        self._log_operation("fail_step", plan_id, {
            "step_order": step_order,
            "error": error,
        })

    def _move_to_done(self, plan: Plan) -> None:
        """Move completed plan to Done folder."""
        source = self._config.plans / f"PLAN_{plan.id}.md"
        dest = self._config.done / f"PLAN_{plan.id}.md"

        if source.exists():
            # Update file with completion info
            self._save_plan_to_path(plan, dest)
            source.unlink()

    def _save_plan_to_path(self, plan: Plan, path: Path) -> None:
        """Save plan to specific path."""
        path.parent.mkdir(parents=True, exist_ok=True)
        content = self._generate_plan_markdown(plan)
        path.write_text(content)

    def validate_plan(self, plan_id: str) -> tuple[bool, list[str]]:
        """Validate a plan's file references.

        Args:
            plan_id: Plan ID to validate

        Returns:
            Tuple of (is_valid, list of errors)
        """
        plan = self.get_plan(plan_id)
        if plan is None:
            return False, [f"Plan not found: {plan_id}"]

        errors = []
        for step in plan.steps:
            for ref in step.file_references:
                if not Path(ref).exists():
                    errors.append(f"Step {step.order}: Missing file reference: {ref}")

        return len(errors) == 0, errors
