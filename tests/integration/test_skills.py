"""Integration tests for Silver Tier Agent Skills."""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ai_employee.config import VaultConfig


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    """Create a temporary vault structure with all Silver tier folders."""
    vault = tmp_path / "vault"
    vault.mkdir()

    # Bronze tier folders
    (vault / "Inbox").mkdir()
    (vault / "Needs_Action").mkdir()
    (vault / "Needs_Action" / "Email").mkdir()
    (vault / "Done").mkdir()
    (vault / "Drop").mkdir()
    (vault / "Quarantine").mkdir()
    (vault / "Logs").mkdir()

    # Silver tier folders
    (vault / "Pending_Approval").mkdir()
    (vault / "Approved").mkdir()
    (vault / "Rejected").mkdir()
    (vault / "Plans").mkdir()
    (vault / "Needs_Action" / "WhatsApp").mkdir()
    (vault / "Needs_Action" / "LinkedIn").mkdir()
    (vault / "Social").mkdir()
    (vault / "Social" / "LinkedIn").mkdir()
    (vault / "Social" / "LinkedIn" / "posts").mkdir()
    (vault / "Briefings").mkdir()
    (vault / "Schedules").mkdir()

    return vault


@pytest.fixture
def vault_config(vault_path: Path) -> VaultConfig:
    """Create VaultConfig for testing."""
    return VaultConfig(vault_path)


class TestPostLinkedInSkill:
    """Integration tests for /post-linkedin skill (T084)."""

    def test_create_post_script_exists(self) -> None:
        """Test that the create_post.py script exists."""
        script_path = Path(".claude/skills/post-linkedin/scripts/create_post.py")
        assert script_path.exists()

    def test_create_post_via_service(self, vault_path: Path) -> None:
        """Test creating a LinkedIn post via the service integration."""
        from ai_employee.config import VaultConfig
        from ai_employee.services.linkedin import LinkedInService

        config = VaultConfig(vault_path)
        service = LinkedInService(config)

        approval_id = service.schedule_post(
            content="Test post for skill integration",
            scheduled_time=datetime.now() + timedelta(hours=1),
        )

        assert approval_id is not None
        assert approval_id.startswith("approval_")

        # Verify approval file created
        pending_files = list(vault_path.glob("Pending_Approval/*.md"))
        assert len(pending_files) == 1

    def test_create_post_script_integration(self, vault_path: Path) -> None:
        """Test running the create_post.py script."""
        script_path = Path(".claude/skills/post-linkedin/scripts/create_post.py")

        result = subprocess.run(
            [sys.executable, str(script_path), "Test post content", "--json", "--vault", str(vault_path)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["success"] is True
        assert "approval_id" in output


class TestCreatePlanSkill:
    """Integration tests for /create-plan skill (T085)."""

    def test_create_plan_script_exists(self) -> None:
        """Test that the create_plan.py script exists."""
        script_path = Path(".claude/skills/create-plan/scripts/create_plan.py")
        assert script_path.exists()

    def test_create_plan_via_service(self, vault_path: Path) -> None:
        """Test creating a plan via the service integration."""
        from ai_employee.config import VaultConfig
        from ai_employee.services.planner import PlannerService

        config = VaultConfig(vault_path)
        service = PlannerService(config)

        plan = service.create_plan(
            task="Test task for skill integration",
            objective="Verify skill integration works correctly",
            steps=[
                {"description": "Step 1: Setup"},
                {"description": "Step 2: Execute"},
                {"description": "Step 3: Verify"},
            ],
        )

        assert plan is not None
        assert plan.id.startswith("plan_")

        # Verify plan file created
        plan_files = list(vault_path.glob("Plans/*.md"))
        assert len(plan_files) == 1

    def test_create_plan_script_integration(self, vault_path: Path) -> None:
        """Test running the create_plan.py script."""
        script_path = Path(".claude/skills/create-plan/scripts/create_plan.py")

        result = subprocess.run(
            [
                sys.executable, str(script_path),
                "Implement new feature",
                "--objective", "Complete the feature implementation",
                "--json", "--vault", str(vault_path)
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["success"] is True
        assert "plan_id" in output


class TestSendEmailSkill:
    """Integration tests for /send-email skill (T086)."""

    def test_send_email_script_exists(self) -> None:
        """Test that the create_email_request.py script exists."""
        script_path = Path(".claude/skills/send-email/scripts/create_email_request.py")
        assert script_path.exists()

    def test_draft_email_via_service(self, vault_path: Path) -> None:
        """Test drafting an email via the service integration."""
        from ai_employee.config import VaultConfig
        from ai_employee.services.email import EmailService, EmailDraft

        config = VaultConfig(vault_path)
        service = EmailService(config)

        draft = EmailDraft(
            to=["test@example.com"],
            subject="Test Email",
            body="This is a test email for skill integration.",
        )

        approval_id = service.draft_email(draft)

        assert approval_id is not None
        assert approval_id.startswith("approval_")

        # Verify approval file created
        pending_files = list(vault_path.glob("Pending_Approval/*.md"))
        assert len(pending_files) == 1

    def test_send_email_script_integration(self, vault_path: Path) -> None:
        """Test running the create_email_request.py script."""
        script_path = Path(".claude/skills/send-email/scripts/create_email_request.py")

        result = subprocess.run(
            [
                sys.executable, str(script_path),
                "--to", "test@example.com",
                "--subject", "Test Subject",
                "--body", "Test body content",
                "--json", "--vault", str(vault_path)
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["success"] is True
        assert "request_id" in output or "approval_id" in output


class TestApproveActionSkill:
    """Integration tests for /approve-action skill (T087)."""

    def test_approve_action_script_exists(self) -> None:
        """Test that the manage_approvals.py script exists."""
        script_path = Path(".claude/skills/approve-action/scripts/manage_approvals.py")
        assert script_path.exists()

    def test_list_approvals_via_service(self, vault_path: Path) -> None:
        """Test listing approvals via the service integration."""
        from ai_employee.config import VaultConfig
        from ai_employee.services.approval import ApprovalService
        from ai_employee.models.approval_request import ApprovalCategory

        config = VaultConfig(vault_path)
        service = ApprovalService(config)

        # Create a test approval
        request = service.create_approval_request(
            category=ApprovalCategory.EMAIL,
            payload={"to": "test@example.com", "subject": "Test"},
            summary="Test email approval",
        )

        # List pending approvals
        pending = service.get_pending_requests()
        assert len(pending) == 1
        assert pending[0].id == request.id

    def test_approve_action_script_integration(self, vault_path: Path) -> None:
        """Test running the manage_approvals.py script."""
        script_path = Path(".claude/skills/approve-action/scripts/manage_approvals.py")

        result = subprocess.run(
            [sys.executable, str(script_path), "list", "--json", "--vault", str(vault_path)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["success"] is True
        assert "approvals" in output or "requests" in output


class TestScheduleTaskSkill:
    """Integration tests for /schedule-task skill (T088)."""

    def test_schedule_task_script_exists(self) -> None:
        """Test that the manage_schedules.py script exists."""
        script_path = Path(".claude/skills/schedule-task/scripts/manage_schedules.py")
        assert script_path.exists()

    def test_create_schedule_via_service(self, vault_path: Path) -> None:
        """Test creating a schedule via the service integration."""
        from ai_employee.config import VaultConfig
        from ai_employee.services.scheduler import SchedulerService
        from ai_employee.models.scheduled_task import ScheduledTask, TaskType

        config = VaultConfig(vault_path)
        service = SchedulerService(config)

        task = ScheduledTask.create(
            name="Test Schedule",
            schedule="0 9 * * *",
            task_type=TaskType.CUSTOM,
        )

        result = service.add_task(task)
        assert result is True

        # Verify schedule file created
        schedule_files = list(vault_path.glob("Schedules/*.md"))
        assert len(schedule_files) == 1

    def test_schedule_task_script_integration(self, vault_path: Path) -> None:
        """Test running the manage_schedules.py script."""
        script_path = Path(".claude/skills/schedule-task/scripts/manage_schedules.py")

        result = subprocess.run(
            [
                sys.executable, str(script_path),
                "create",
                "--name", "Daily Task",
                "--schedule", "0 8 * * *",
                "--json", "--vault", str(vault_path)
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["success"] is True
        assert "task_id" in output


class TestSkillServiceIntegration:
    """Cross-skill integration tests (T089)."""

    def test_all_skills_use_consistent_vault_config(self, vault_path: Path) -> None:
        """Test that all services use consistent VaultConfig paths."""
        from ai_employee.config import VaultConfig
        from ai_employee.services.linkedin import LinkedInService
        from ai_employee.services.planner import PlannerService
        from ai_employee.services.email import EmailService
        from ai_employee.services.approval import ApprovalService
        from ai_employee.services.scheduler import SchedulerService

        config = VaultConfig(vault_path)

        # Initialize all services with same config
        linkedin = LinkedInService(config)
        planner = PlannerService(config)
        email = EmailService(config)
        approval = ApprovalService(config)
        scheduler = SchedulerService(config)

        # All services should be initialized without error
        assert linkedin is not None
        assert planner is not None
        assert email is not None
        assert approval is not None
        assert scheduler is not None

    def test_approval_workflow_integration(self, vault_path: Path) -> None:
        """Test that services properly integrate with approval workflow."""
        from ai_employee.config import VaultConfig
        from ai_employee.services.linkedin import LinkedInService
        from ai_employee.services.email import EmailService, EmailDraft
        from ai_employee.services.approval import ApprovalService
        from ai_employee.models.approval_request import ApprovalCategory

        config = VaultConfig(vault_path)

        linkedin = LinkedInService(config)
        email = EmailService(config)
        approval = ApprovalService(config)

        # Create LinkedIn post approval
        linkedin_id = linkedin.schedule_post(
            content="Test LinkedIn post",
            scheduled_time=datetime.now() + timedelta(hours=1),
        )

        # Create email approval
        email_draft = EmailDraft(
            to=["test@example.com"],
            subject="Test",
            body="Test body",
        )
        email_id = email.draft_email(email_draft)

        # Both should create pending approvals
        pending = approval.get_pending_requests()
        assert len(pending) == 2

        # Verify categories
        categories = {r.category for r in pending}
        assert ApprovalCategory.SOCIAL_POST in categories
        assert ApprovalCategory.EMAIL in categories

    def test_logging_integration(self, vault_path: Path) -> None:
        """Test that all services log to the Logs folder."""
        from ai_employee.config import VaultConfig
        from ai_employee.services.linkedin import LinkedInService
        from ai_employee.services.scheduler import SchedulerService
        from ai_employee.models.scheduled_task import ScheduledTask, TaskType

        config = VaultConfig(vault_path)

        # Use services that log
        linkedin = LinkedInService(config)
        linkedin.schedule_post(
            content="Test post",
            scheduled_time=datetime.now() + timedelta(hours=1),
        )

        scheduler = SchedulerService(config)
        task = ScheduledTask.create(
            name="Test Task",
            schedule="0 8 * * *",
            task_type=TaskType.CUSTOM,
        )
        scheduler.add_task(task)

        # Verify log files created
        log_files = list(vault_path.glob("Logs/*.log"))
        assert len(log_files) >= 1
