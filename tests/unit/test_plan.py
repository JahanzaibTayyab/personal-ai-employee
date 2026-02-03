"""Unit tests for Plan and PlanStep models."""

from datetime import datetime

import pytest

from ai_employee.models.plan import Plan, PlanStatus, PlanStep, StepStatus


class TestPlanStep:
    """Tests for PlanStep dataclass."""

    def test_create_plan_step(self) -> None:
        """Test creating a plan step."""
        step = PlanStep(
            id="step_1",
            plan_id="plan_test",
            order=1,
            description="First step",
        )

        assert step.id == "step_1"
        assert step.plan_id == "plan_test"
        assert step.order == 1
        assert step.status == StepStatus.PENDING
        assert step.requires_approval is False
        assert step.dependencies == []

    def test_is_ready_no_dependencies(self) -> None:
        """Test step readiness with no dependencies."""
        step = PlanStep(
            id="step_1",
            plan_id="plan_test",
            order=1,
            description="Step without dependencies",
        )

        assert step.is_ready(set()) is True

    def test_is_ready_with_dependencies(self) -> None:
        """Test step readiness with dependencies."""
        step = PlanStep(
            id="step_2",
            plan_id="plan_test",
            order=2,
            description="Step with dependencies",
            dependencies=["step_1"],
        )

        # Not ready without dependency
        assert step.is_ready(set()) is False

        # Ready with dependency completed
        assert step.is_ready({"step_1"}) is True

    def test_is_ready_non_pending(self) -> None:
        """Test step readiness returns False if not pending."""
        step = PlanStep(
            id="step_1",
            plan_id="plan_test",
            order=1,
            description="Completed step",
            status=StepStatus.COMPLETED,
        )

        assert step.is_ready(set()) is False

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        step = PlanStep(
            id="step_1",
            plan_id="plan_test",
            order=1,
            description="Test step",
            requires_approval=True,
            dependencies=["step_0"],
        )

        d = step.to_dict()

        assert d["id"] == "step_1"
        assert d["order"] == 1
        assert d["description"] == "Test step"
        assert d["requires_approval"] is True
        assert d["dependencies"] == ["step_0"]

    def test_from_dict(self) -> None:
        """Test creation from dictionary."""
        data = {
            "id": "step_1",
            "order": 1,
            "description": "Restored step",
            "status": "completed",
            "requires_approval": False,
        }

        step = PlanStep.from_dict(data, "plan_test")

        assert step.id == "step_1"
        assert step.plan_id == "plan_test"
        assert step.status == StepStatus.COMPLETED


class TestPlan:
    """Tests for Plan dataclass."""

    def test_create_plan(self) -> None:
        """Test creating a plan."""
        plan = Plan(
            id="plan_test",
            objective="Test the system",
        )

        assert plan.id == "plan_test"
        assert plan.objective == "Test the system"
        assert plan.status == PlanStatus.PENDING
        assert plan.steps == []

    def test_add_step(self) -> None:
        """Test adding steps to a plan."""
        plan = Plan(id="plan_test", objective="Test")

        step1 = plan.add_step("First step")
        step2 = plan.add_step("Second step", requires_approval=True, dependencies=["step_1"])

        assert len(plan.steps) == 2
        assert step1.id == "step_1"
        assert step1.order == 1
        assert step2.id == "step_2"
        assert step2.order == 2
        assert step2.requires_approval is True
        assert step2.dependencies == ["step_1"]

    def test_get_current_step(self) -> None:
        """Test getting the current step."""
        plan = Plan(id="plan_test", objective="Test")
        plan.add_step("Step 1")
        plan.add_step("Step 2", dependencies=["step_1"])

        # Initial state: first step is current
        current = plan.get_current_step()
        assert current is not None
        assert current.id == "step_1"

        # After completing step 1, step 2 becomes current
        plan.steps[0].status = StepStatus.COMPLETED
        current = plan.get_current_step()
        assert current is not None
        assert current.id == "step_2"

    def test_get_progress(self) -> None:
        """Test progress calculation."""
        plan = Plan(id="plan_test", objective="Test")
        plan.add_step("Step 1")
        plan.add_step("Step 2")
        plan.add_step("Step 3")

        # No progress
        completed, total = plan.get_progress()
        assert completed == 0
        assert total == 3

        # Some progress
        plan.steps[0].status = StepStatus.COMPLETED
        plan.steps[1].status = StepStatus.COMPLETED
        completed, total = plan.get_progress()
        assert completed == 2
        assert total == 3

    def test_is_blocked_by_approval(self) -> None:
        """Test blocked status when awaiting approval."""
        plan = Plan(id="plan_test", objective="Test")
        plan.add_step("Step 1", requires_approval=True)

        assert plan.is_blocked() is False

        plan.steps[0].status = StepStatus.AWAITING_APPROVAL
        assert plan.is_blocked() is True

    def test_is_blocked_by_failure(self) -> None:
        """Test blocked status when step failed."""
        plan = Plan(id="plan_test", objective="Test")
        plan.add_step("Step 1")

        plan.steps[0].status = StepStatus.FAILED
        assert plan.is_blocked() is True

    def test_to_frontmatter(self) -> None:
        """Test conversion to frontmatter dictionary."""
        plan = Plan(id="plan_test", objective="Test objective")
        plan.add_step("First step")

        fm = plan.to_frontmatter()

        assert fm["id"] == "plan_test"
        assert fm["objective"] == "Test objective"
        assert fm["status"] == "pending"
        assert len(fm["steps"]) == 1

    def test_from_frontmatter(self) -> None:
        """Test creation from frontmatter dictionary."""
        fm = {
            "id": "restored_plan",
            "objective": "Restored objective",
            "status": "in_progress",
            "created_at": "2026-02-03T10:00:00",
            "steps": [
                {
                    "id": "step_1",
                    "order": 1,
                    "description": "Restored step",
                    "status": "completed",
                }
            ],
        }

        plan = Plan.from_frontmatter(fm)

        assert plan.id == "restored_plan"
        assert plan.status == PlanStatus.IN_PROGRESS
        assert len(plan.steps) == 1
        assert plan.steps[0].status == StepStatus.COMPLETED

    def test_get_filename(self) -> None:
        """Test filename generation."""
        plan = Plan(id="test_plan_123", objective="Test")

        assert plan.get_filename() == "PLAN_test_plan_123.md"

    def test_validation_step_order(self) -> None:
        """Test validation of sequential step order."""
        # This should work fine
        plan = Plan(id="valid_plan", objective="Test")
        plan.add_step("Step 1")
        plan.add_step("Step 2")

        # Manually mess up order to trigger validation
        with pytest.raises(ValueError, match="Step order must be sequential"):
            Plan(
                id="invalid_plan",
                objective="Test",
                steps=[
                    PlanStep(id="step_1", plan_id="invalid_plan", order=1, description="Step 1"),
                    PlanStep(id="step_2", plan_id="invalid_plan", order=3, description="Step 3"),
                ],
            )

    def test_validation_circular_dependency(self) -> None:
        """Test validation catches circular dependencies."""
        with pytest.raises(ValueError, match="Circular dependency"):
            Plan(
                id="circular_plan",
                objective="Test",
                steps=[
                    PlanStep(
                        id="step_1",
                        plan_id="circular_plan",
                        order=1,
                        description="Step 1",
                        dependencies=["step_2"],
                    ),
                    PlanStep(
                        id="step_2",
                        plan_id="circular_plan",
                        order=2,
                        description="Step 2",
                        dependencies=["step_1"],
                    ),
                ],
            )


class TestPlanStatus:
    """Tests for PlanStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """Test all required statuses are defined."""
        assert PlanStatus.PENDING.value == "pending"
        assert PlanStatus.IN_PROGRESS.value == "in_progress"
        assert PlanStatus.COMPLETED.value == "completed"
        assert PlanStatus.FAILED.value == "failed"
        assert PlanStatus.PAUSED.value == "paused"


class TestStepStatus:
    """Tests for StepStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """Test all required statuses are defined."""
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.IN_PROGRESS.value == "in_progress"
        assert StepStatus.COMPLETED.value == "completed"
        assert StepStatus.FAILED.value == "failed"
        assert StepStatus.SKIPPED.value == "skipped"
        assert StepStatus.AWAITING_APPROVAL.value == "awaiting_approval"
