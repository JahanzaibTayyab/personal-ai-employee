"""Unit tests for PlannerService."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.plan import Plan, PlanStatus, PlanStep, StepStatus


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    """Create a temporary vault structure."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Plans").mkdir()
    (vault / "Pending_Approval").mkdir()
    (vault / "Approved").mkdir()
    (vault / "Done").mkdir()
    (vault / "Logs").mkdir()
    return vault


@pytest.fixture
def vault_config(vault_path: Path) -> VaultConfig:
    """Create VaultConfig for testing."""
    return VaultConfig(vault_path)


class TestPlannerService:
    """Tests for PlannerService class."""

    def test_service_initialization(self, vault_config: VaultConfig) -> None:
        """Test PlannerService initializes correctly."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        assert service is not None

    def test_analyze_task_simple(self, vault_config: VaultConfig) -> None:
        """Test analyzing a simple task."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        analysis = service.analyze_task("Send email to client about meeting")

        assert "objective" in analysis
        assert "steps" in analysis or "complexity" in analysis

    def test_analyze_task_complex(self, vault_config: VaultConfig) -> None:
        """Test analyzing a complex multi-step task."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        analysis = service.analyze_task(
            "Research competitor pricing, compile findings into report, "
            "send to team for review, then schedule meeting to discuss"
        )

        assert "objective" in analysis
        assert analysis.get("complexity", "simple") != "simple"

    def test_create_plan(self, vault_config: VaultConfig, vault_path: Path) -> None:
        """Test creating a plan from task description."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        plan = service.create_plan(
            task="Send weekly status update email",
            objective="Inform team of project progress",
        )

        assert plan is not None
        assert plan.objective == "Inform team of project progress"
        assert len(plan.steps) > 0
        assert plan.status == PlanStatus.PENDING

    def test_create_plan_with_steps(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test creating a plan with specific steps."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        steps = [
            {"description": "Gather project updates from team", "requires_approval": False},
            {"description": "Draft status email", "requires_approval": False},
            {"description": "Send email to stakeholders", "requires_approval": True},
        ]

        plan = service.create_plan(
            task="Weekly status update",
            objective="Keep stakeholders informed",
            steps=steps,
        )

        assert len(plan.steps) == 3
        assert plan.steps[2].requires_approval is True

    def test_create_plan_saves_file(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test that creating a plan saves Plan.md file."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        plan = service.create_plan(
            task="Test task",
            objective="Test objective",
        )

        # Check file was created
        plan_files = list((vault_path / "Plans").glob("*.md"))
        assert len(plan_files) == 1

        content = plan_files[0].read_text()
        assert "Test objective" in content

    def test_plan_file_format(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test Plan.md file format (plain language, no code blocks)."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        plan = service.create_plan(
            task="Deploy application",
            objective="Release new version to production",
            steps=[
                {"description": "Run tests", "requires_approval": False},
                {"description": "Deploy to staging", "requires_approval": False},
                {"description": "Deploy to production", "requires_approval": True},
            ],
        )

        plan_files = list((vault_path / "Plans").glob("*.md"))
        content = plan_files[0].read_text()

        # Verify plain language format (SC-010)
        assert "```" not in content  # No code blocks
        assert "# Objective" in content or "## Objective" in content
        assert "[ ]" in content or "[x]" in content  # Progress symbols

    def test_get_plan(self, vault_config: VaultConfig, vault_path: Path) -> None:
        """Test retrieving a plan by ID."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        created = service.create_plan(
            task="Test task",
            objective="Test objective",
        )

        retrieved = service.get_plan(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.objective == created.objective

    def test_get_plan_not_found(self, vault_config: VaultConfig) -> None:
        """Test getting non-existent plan returns None."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        result = service.get_plan("nonexistent_plan_id")

        assert result is None

    def test_get_active_plans(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test getting all active (non-completed) plans."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)

        # Create some plans
        service.create_plan(task="Task 1", objective="Obj 1")
        service.create_plan(task="Task 2", objective="Obj 2")

        active = service.get_active_plans()

        assert len(active) == 2


class TestPlanExecution:
    """Tests for plan execution tracking."""

    def test_start_plan(self, vault_config: VaultConfig, vault_path: Path) -> None:
        """Test starting plan execution."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        plan = service.create_plan(
            task="Test task",
            objective="Test objective",
        )

        service.start_plan(plan.id)
        updated = service.get_plan(plan.id)

        assert updated.status == PlanStatus.IN_PROGRESS

    def test_complete_step(self, vault_config: VaultConfig, vault_path: Path) -> None:
        """Test completing a plan step."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        plan = service.create_plan(
            task="Test task",
            objective="Test objective",
            steps=[
                {"description": "Step 1", "requires_approval": False},
                {"description": "Step 2", "requires_approval": False},
            ],
        )

        service.start_plan(plan.id)
        service.complete_step(plan.id, step_order=1)

        updated = service.get_plan(plan.id)
        assert updated.steps[0].status == StepStatus.COMPLETED
        assert updated.steps[1].status == StepStatus.PENDING

    def test_fail_step(self, vault_config: VaultConfig, vault_path: Path) -> None:
        """Test marking a step as failed."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        plan = service.create_plan(
            task="Test task",
            objective="Test objective",
            steps=[{"description": "Step 1", "requires_approval": False}],
        )

        service.start_plan(plan.id)
        service.fail_step(plan.id, step_order=1, error="Step failed")

        updated = service.get_plan(plan.id)
        assert updated.steps[0].status == StepStatus.FAILED
        assert updated.status == PlanStatus.PAUSED

    def test_pause_on_approval_required(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test plan pauses when step requires approval."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        plan = service.create_plan(
            task="Test task",
            objective="Test objective",
            steps=[
                {"description": "Auto step", "requires_approval": False},
                {"description": "Manual step", "requires_approval": True},
            ],
        )

        service.start_plan(plan.id)
        service.complete_step(plan.id, step_order=1)

        # Try to start the approval-required step
        service.start_step(plan.id, step_order=2)
        updated = service.get_plan(plan.id)

        assert updated.status == PlanStatus.PAUSED
        assert updated.steps[1].status == StepStatus.AWAITING_APPROVAL

    def test_complete_plan(self, vault_config: VaultConfig, vault_path: Path) -> None:
        """Test completing all steps completes the plan."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        plan = service.create_plan(
            task="Test task",
            objective="Test objective",
            steps=[{"description": "Only step", "requires_approval": False}],
        )

        service.start_plan(plan.id)
        service.complete_step(plan.id, step_order=1)

        updated = service.get_plan(plan.id)
        assert updated.status == PlanStatus.COMPLETED

    def test_completed_plan_moved_to_done(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test completed plan is moved to Done folder."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        plan = service.create_plan(
            task="Test task",
            objective="Test objective",
            steps=[{"description": "Only step", "requires_approval": False}],
        )

        service.start_plan(plan.id)
        service.complete_step(plan.id, step_order=1)

        # Check file moved to Done
        done_files = list((vault_path / "Done").glob(f"*{plan.id}*"))
        assert len(done_files) == 1


class TestPlanApprovalIntegration:
    """Tests for plan-approval workflow integration."""

    def test_step_creates_approval_request(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test approval-required step creates approval request."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        plan = service.create_plan(
            task="Send important email",
            objective="Communicate with client",
            steps=[
                {"description": "Draft email", "requires_approval": False},
                {"description": "Send email", "requires_approval": True},
            ],
        )

        service.start_plan(plan.id)
        service.complete_step(plan.id, step_order=1)
        service.start_step(plan.id, step_order=2)

        # Check approval request created
        pending_files = list((vault_path / "Pending_Approval").glob("*.md"))
        assert len(pending_files) == 1


class TestPlanValidation:
    """Tests for plan validation and file reference checking."""

    def test_validate_file_references(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test validation of file references in steps."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)

        # Create a referenced file
        ref_file = vault_path / "report.pdf"
        ref_file.write_text("test content")

        plan = service.create_plan(
            task="Process report",
            objective="Analyze and summarize report",
            steps=[
                {
                    "description": "Read report",
                    "requires_approval": False,
                    "file_references": [str(ref_file)],
                },
            ],
        )

        # Validation should pass
        is_valid, errors = service.validate_plan(plan.id)
        assert is_valid is True

    def test_validate_missing_file_references(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test validation fails for missing file references."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        plan = service.create_plan(
            task="Process report",
            objective="Analyze report",
            steps=[
                {
                    "description": "Read report",
                    "requires_approval": False,
                    "file_references": ["/nonexistent/file.pdf"],
                },
            ],
        )

        is_valid, errors = service.validate_plan(plan.id)
        assert is_valid is False
        assert len(errors) > 0


class TestPlannerServiceErrors:
    """Tests for PlannerService error handling."""

    def test_create_plan_empty_objective(self, vault_config: VaultConfig) -> None:
        """Test error on empty objective."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)

        with pytest.raises(ValueError, match="objective"):
            service.create_plan(task="Test", objective="")

    def test_start_nonexistent_plan(self, vault_config: VaultConfig) -> None:
        """Test error starting non-existent plan."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)

        with pytest.raises(ValueError, match="not found"):
            service.start_plan("nonexistent_id")

    def test_complete_invalid_step_order(
        self, vault_config: VaultConfig, vault_path: Path
    ) -> None:
        """Test error completing invalid step order."""
        from ai_employee.services.planner import PlannerService

        service = PlannerService(vault_config)
        plan = service.create_plan(
            task="Test",
            objective="Test",
            steps=[{"description": "Step 1", "requires_approval": False}],
        )

        service.start_plan(plan.id)

        with pytest.raises(ValueError, match="not found"):
            service.complete_step(plan.id, step_order=99)
