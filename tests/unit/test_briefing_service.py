"""Tests for BriefingService."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_employee.config import VaultConfig
from ai_employee.models.briefing import (
    CEOBriefing,
    CompletedTask,
)
from ai_employee.services.briefing import BriefingService


@pytest.fixture
def vault_dir(tmp_path: Path) -> Path:
    """Create a temporary vault directory structure."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Done").mkdir()
    (vault / "Logs").mkdir()
    (vault / "Briefings").mkdir()
    (vault / "Social" / "LinkedIn" / "posts").mkdir(parents=True)
    (vault / "Plans").mkdir()
    (vault / "Needs_Action").mkdir()
    return vault


@pytest.fixture
def vault_config(vault_dir: Path) -> VaultConfig:
    """Create a VaultConfig for the test vault."""
    return VaultConfig(root=vault_dir)


@pytest.fixture
def briefing_service(vault_config: VaultConfig) -> BriefingService:
    """Create a BriefingService instance."""
    return BriefingService(vault_config=vault_config)


class TestBriefingServiceInit:
    """Tests for BriefingService initialization."""

    def test_create_service(self, vault_config: VaultConfig) -> None:
        """Test creating a briefing service."""
        service = BriefingService(vault_config=vault_config)

        assert service.vault_config == vault_config

    def test_create_service_with_odoo(self, vault_config: VaultConfig) -> None:
        """Test creating a briefing service with Odoo integration."""
        mock_odoo = MagicMock()

        service = BriefingService(
            vault_config=vault_config,
            odoo_service=mock_odoo,
        )

        assert service._odoo_service is mock_odoo


class TestBriefingServiceTasks:
    """Tests for task aggregation from /Done folder."""

    def test_get_completed_tasks_from_done_folder(
        self, briefing_service: BriefingService, vault_dir: Path
    ) -> None:
        """Test reading completed tasks from /Done folder."""
        done_dir = vault_dir / "Done"

        # Create some done files
        task1 = done_dir / "FILE_report.md"
        task1.write_text(
            "---\n"
            "type: file_drop\n"
            "original_name: report.pdf\n"
            "status: done\n"
            "processed_at: '2026-02-20T14:30:00'\n"
            "---\n\n"
            "Quarterly report processed and filed.\n"
        )

        task2 = done_dir / "EMAIL_meeting.md"
        task2.write_text(
            "---\n"
            "type: email\n"
            "original_name: Meeting Invitation\n"
            "status: done\n"
            "processed_at: '2026-02-19T10:00:00'\n"
            "---\n\n"
            "Meeting scheduled.\n"
        )

        period_start = date(2026, 2, 15)
        period_end = date(2026, 2, 21)

        tasks = briefing_service.get_completed_tasks(period_start, period_end)

        assert len(tasks) >= 1
        assert all(isinstance(t, CompletedTask) for t in tasks)

    def test_get_completed_tasks_empty_folder(
        self, briefing_service: BriefingService
    ) -> None:
        """Test reading from empty /Done folder."""
        tasks = briefing_service.get_completed_tasks(
            date(2026, 2, 15), date(2026, 2, 21)
        )

        assert tasks == []


class TestBriefingServiceRevenue:
    """Tests for revenue aggregation."""

    def test_get_revenue_data_from_odoo(
        self, vault_config: VaultConfig
    ) -> None:
        """Test getting revenue data from Odoo service."""
        mock_odoo = MagicMock()
        mock_odoo.is_connected.return_value = True
        mock_odoo.get_revenue_summary.return_value = {
            "total_invoiced": Decimal("25000.00"),
            "total_collected": Decimal("20000.00"),
            "total_outstanding": Decimal("5000.00"),
            "invoice_count": 8,
        }

        service = BriefingService(
            vault_config=vault_config,
            odoo_service=mock_odoo,
        )

        revenue = service.get_revenue_data(
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
        )

        assert revenue["total_invoiced"] == Decimal("25000.00")
        assert revenue["total_collected"] == Decimal("20000.00")

    def test_get_revenue_data_no_odoo(
        self, briefing_service: BriefingService
    ) -> None:
        """Test getting revenue data when Odoo is not available."""
        revenue = briefing_service.get_revenue_data(
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
        )

        assert revenue["total_invoiced"] == Decimal("0")
        assert revenue["total_collected"] == Decimal("0")


class TestBriefingServiceBottlenecks:
    """Tests for bottleneck detection."""

    def test_identify_bottlenecks_from_logs(
        self, briefing_service: BriefingService, vault_dir: Path
    ) -> None:
        """Test identifying bottlenecks from activity logs."""
        logs_dir = vault_dir / "Logs"

        # Create a log with some slow operations
        log_file = logs_dir / "claude_2026-02-20.log"
        import json

        entries = [
            {
                "timestamp": "2026-02-20T10:00:00",
                "action_type": "process",
                "item_id": "item_1",
                "outcome": "success",
                "duration_ms": 300000,  # 5 minutes
            },
            {
                "timestamp": "2026-02-20T11:00:00",
                "action_type": "process",
                "item_id": "item_2",
                "outcome": "failure",
                "duration_ms": 600000,  # 10 minutes
                "details": "Timeout waiting for approval",
            },
        ]
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n"
        )

        bottlenecks = briefing_service.identify_bottlenecks(
            date(2026, 2, 15), date(2026, 2, 21)
        )

        assert isinstance(bottlenecks, list)

    def test_identify_bottlenecks_no_logs(
        self, briefing_service: BriefingService
    ) -> None:
        """Test bottleneck detection with no logs."""
        bottlenecks = briefing_service.identify_bottlenecks(
            date(2026, 2, 15), date(2026, 2, 21)
        )

        assert bottlenecks == []


class TestBriefingServiceCostSuggestions:
    """Tests for cost suggestion generation."""

    def test_identify_unused_subscriptions(
        self, briefing_service: BriefingService, vault_dir: Path
    ) -> None:
        """Test identifying subscriptions unused for 30+ days."""
        # Create logs that reference some services
        logs_dir = vault_dir / "Logs"
        import json

        # Old log (40 days ago)
        old_date = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d")
        old_log = logs_dir / f"claude_{old_date}.log"
        old_log.write_text(
            json.dumps({
                "timestamp": f"{old_date}T10:00:00",
                "action_type": "process",
                "item_id": "slack_notification",
                "outcome": "success",
                "details": "Processed Slack notification",
            }) + "\n"
        )

        suggestions = briefing_service.generate_cost_suggestions(
            date(2026, 2, 15), date(2026, 2, 21)
        )

        assert isinstance(suggestions, list)

    def test_no_cost_suggestions_when_no_data(
        self, briefing_service: BriefingService
    ) -> None:
        """Test no suggestions when no data is available."""
        suggestions = briefing_service.generate_cost_suggestions(
            date(2026, 2, 15), date(2026, 2, 21)
        )

        assert suggestions == []


class TestBriefingServiceSocialMedia:
    """Tests for social media summary aggregation."""

    def test_get_social_summary_from_linkedin(
        self, briefing_service: BriefingService, vault_dir: Path
    ) -> None:
        """Test aggregating social media data from LinkedIn folder."""
        posts_dir = vault_dir / "Social" / "LinkedIn" / "posts"

        # Create a post file
        post = posts_dir / "post_2026-02-20.md"
        post.write_text(
            "---\n"
            "status: published\n"
            "published_at: '2026-02-20T09:00:00'\n"
            "impressions: 5000\n"
            "likes: 120\n"
            "comments: 15\n"
            "shares: 8\n"
            "topic: AI Trends\n"
            "---\n\n"
            "Great article about AI trends.\n"
        )

        summary = briefing_service.get_social_summary(
            date(2026, 2, 15), date(2026, 2, 21)
        )

        assert summary is not None
        assert summary.posts_published >= 1

    def test_get_social_summary_no_posts(
        self, briefing_service: BriefingService
    ) -> None:
        """Test social summary when no posts exist."""
        summary = briefing_service.get_social_summary(
            date(2026, 2, 15), date(2026, 2, 21)
        )

        assert summary is None


class TestBriefingServiceGeneration:
    """Tests for full briefing generation."""

    def test_generate_briefing(
        self, briefing_service: BriefingService, vault_dir: Path
    ) -> None:
        """Test generating a complete CEO briefing."""
        briefing = briefing_service.generate_briefing(
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
            monthly_goal=Decimal("80000.00"),
        )

        assert isinstance(briefing, CEOBriefing)
        assert briefing.id == "2026-02-21"
        assert briefing.period_start == date(2026, 2, 15)
        assert briefing.period_end == date(2026, 2, 21)
        assert briefing.monthly_goal == Decimal("80000.00")
        assert isinstance(briefing.executive_summary, str)
        assert briefing.revenue_trend in ("on_track", "ahead", "behind")

    def test_write_briefing_to_file(
        self, briefing_service: BriefingService, vault_dir: Path
    ) -> None:
        """Test writing briefing to vault /Briefings/ folder."""
        briefing = briefing_service.generate_briefing(
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
        )

        filepath = briefing_service.write_briefing(briefing)

        assert filepath.exists()
        assert filepath.name == "CEO_Briefing_2026-02-21.md"
        assert filepath.parent == vault_dir / "Briefings"

        content = filepath.read_text()
        assert "CEO Briefing" in content or "Executive Summary" in content

    def test_generate_briefing_with_odoo(
        self, vault_config: VaultConfig
    ) -> None:
        """Test briefing generation with Odoo revenue data."""
        mock_odoo = MagicMock()
        mock_odoo.is_connected.return_value = True
        mock_odoo.get_revenue_summary.return_value = {
            "total_invoiced": Decimal("30000.00"),
            "total_collected": Decimal("25000.00"),
            "total_outstanding": Decimal("5000.00"),
            "invoice_count": 12,
        }
        mock_odoo.get_expense_summary.return_value = {
            "total_expenses": Decimal("10000.00"),
            "bill_count": 5,
        }

        service = BriefingService(
            vault_config=vault_config,
            odoo_service=mock_odoo,
        )

        briefing = service.generate_briefing(
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
            monthly_goal=Decimal("100000.00"),
        )

        assert briefing.revenue_this_week == Decimal("30000.00")

    def test_render_briefing_markdown(
        self, briefing_service: BriefingService
    ) -> None:
        """Test rendering briefing to markdown format."""
        briefing = CEOBriefing(
            id="2026-02-21",
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
            executive_summary="Business is on track.",
            revenue_this_week=Decimal("15000"),
            revenue_mtd=Decimal("45000"),
            monthly_goal=Decimal("80000"),
            revenue_trend="on_track",
            completed_tasks=[
                CompletedTask(
                    name="Deploy v2",
                    completed_at=datetime(2026, 2, 20, 14, 0),
                    category="engineering",
                    source="Done/deploy.md",
                ),
            ],
            bottlenecks=[],
            cost_suggestions=[],
            upcoming_deadlines=[],
        )

        markdown = briefing_service.render_briefing(briefing)

        assert isinstance(markdown, str)
        assert "CEO Briefing" in markdown
        assert "Executive Summary" in markdown
        assert "Revenue" in markdown
        assert "15,000" in markdown or "15000" in markdown
