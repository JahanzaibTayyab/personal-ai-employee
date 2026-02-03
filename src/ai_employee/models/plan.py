"""Plan and PlanStep models - multi-step task breakdown for reasoning loop."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PlanStatus(str, Enum):
    """Status of a plan (FR-018)."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"  # Waiting for approval or failed step


class StepStatus(str, Enum):
    """Status of a plan step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    AWAITING_APPROVAL = "awaiting_approval"


@dataclass
class PlanStep:
    """Individual step in a plan (FR-017).

    Steps are embedded within Plan.md files.
    """

    id: str
    plan_id: str
    order: int  # 1-indexed step number
    description: str
    status: StepStatus = StepStatus.PENDING
    requires_approval: bool = False
    dependencies: list[str] = field(default_factory=list)  # Step IDs
    approval_request_id: str | None = None  # Links to ApprovalRequest if needed
    error: str | None = None
    completed_at: datetime | None = None
    file_references: list[str] = field(default_factory=list)  # Paths referenced by this step

    def is_ready(self, completed_steps: set[str]) -> bool:
        """Check if this step is ready to execute (all dependencies met)."""
        if self.status != StepStatus.PENDING:
            return False
        return all(dep in completed_steps for dep in self.dependencies)

    def to_dict(self) -> dict[str, Any]:
        """Convert step to dictionary."""
        data: dict[str, Any] = {
            "id": self.id,
            "order": self.order,
            "description": self.description,
            "status": self.status.value,
            "requires_approval": self.requires_approval,
        }

        if self.dependencies:
            data["dependencies"] = self.dependencies
        if self.approval_request_id:
            data["approval_request_id"] = self.approval_request_id
        if self.error:
            data["error"] = self.error
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        if self.file_references:
            data["file_references"] = self.file_references

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any], plan_id: str) -> "PlanStep":
        """Create PlanStep from dictionary."""
        return cls(
            id=data["id"],
            plan_id=plan_id,
            order=data["order"],
            description=data["description"],
            status=StepStatus(data.get("status", "pending")),
            requires_approval=data.get("requires_approval", False),
            dependencies=data.get("dependencies", []),
            approval_request_id=data.get("approval_request_id"),
            error=data.get("error"),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
            file_references=data.get("file_references", []),
        )


@dataclass
class Plan:
    """Multi-step task breakdown (FR-016 to FR-020).

    Stored as Plan.md files in /Plans/ folder with YAML frontmatter.
    """

    id: str
    objective: str
    steps: list[PlanStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    completion_summary: str | None = None

    def get_current_step(self) -> PlanStep | None:
        """Get the current step being executed or awaiting execution."""
        completed_ids = {s.id for s in self.steps if s.status == StepStatus.COMPLETED}

        for step in sorted(self.steps, key=lambda s: s.order):
            if step.status in (StepStatus.PENDING, StepStatus.AWAITING_APPROVAL):
                if step.is_ready(completed_ids):
                    return step
            elif step.status == StepStatus.IN_PROGRESS:
                return step
        return None

    def get_progress(self) -> tuple[int, int]:
        """Get progress as (completed_steps, total_steps)."""
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        return completed, len(self.steps)

    def is_blocked(self) -> bool:
        """Check if plan is blocked (waiting for approval or has failed step)."""
        for step in self.steps:
            if step.status == StepStatus.AWAITING_APPROVAL:
                return True
            if step.status == StepStatus.FAILED:
                return True
        return False

    def add_step(
        self,
        description: str,
        requires_approval: bool = False,
        dependencies: list[str] | None = None,
        file_references: list[str] | None = None,
    ) -> PlanStep:
        """Add a new step to the plan."""
        step_id = f"step_{len(self.steps) + 1}"
        step = PlanStep(
            id=step_id,
            plan_id=self.id,
            order=len(self.steps) + 1,
            description=description,
            requires_approval=requires_approval,
            dependencies=dependencies or [],
            file_references=file_references or [],
        )
        self.steps.append(step)
        return step

    def to_frontmatter(self) -> dict[str, Any]:
        """Convert plan to YAML frontmatter dictionary."""
        data: dict[str, Any] = {
            "id": self.id,
            "objective": self.objective,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "steps": [step.to_dict() for step in self.steps],
        }

        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        if self.completion_summary:
            data["completion_summary"] = self.completion_summary

        return data

    @classmethod
    def from_frontmatter(cls, data: dict[str, Any]) -> "Plan":
        """Create Plan from YAML frontmatter dictionary."""
        plan_id = data["id"]
        steps = [
            PlanStep.from_dict(step_data, plan_id)
            for step_data in data.get("steps", [])
        ]

        return cls(
            id=plan_id,
            objective=data["objective"],
            steps=steps,
            status=PlanStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
            completion_summary=data.get("completion_summary"),
        )

    def get_filename(self) -> str:
        """Generate filename for this plan."""
        return f"PLAN_{self.id}.md"

    def __post_init__(self) -> None:
        """Validate the plan."""
        # Validate step order is sequential
        for i, step in enumerate(sorted(self.steps, key=lambda s: s.order)):
            if step.order != i + 1:
                raise ValueError(f"Step order must be sequential, got {step.order} at position {i+1}")

        # Validate no circular dependencies
        self._check_circular_dependencies()

    def _check_circular_dependencies(self) -> None:
        """Check for circular dependencies in steps."""
        step_ids = {s.id for s in self.steps}

        def has_cycle(step_id: str, visited: set[str], path: set[str]) -> bool:
            if step_id in path:
                return True
            if step_id in visited:
                return False

            visited.add(step_id)
            path.add(step_id)

            step = next((s for s in self.steps if s.id == step_id), None)
            if step:
                for dep in step.dependencies:
                    if dep in step_ids and has_cycle(dep, visited, path):
                        return True

            path.remove(step_id)
            return False

        for step in self.steps:
            if has_cycle(step.id, set(), set()):
                raise ValueError(f"Circular dependency detected involving step {step.id}")
