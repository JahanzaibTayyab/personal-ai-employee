"""Tests for CEO Briefing data models."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from ai_employee.models.briefing import (
    AuditSummary,
    Bottleneck,
    CEOBriefing,
    CompletedTask,
    CostSuggestion,
    Deadline,
    SocialSummary,
)


class TestCompletedTask:
    """Tests for CompletedTask dataclass."""

    def test_create_completed_task(self) -> None:
        """Test creating a completed task."""
        task = CompletedTask(
            name="Deploy v2.0",
            completed_at=datetime(2026, 2, 20, 14, 30),
            category="engineering",
            source="Done/TASK_deploy_v2.md",
        )

        assert task.name == "Deploy v2.0"
        assert task.category == "engineering"
        assert task.source == "Done/TASK_deploy_v2.md"

    def test_completed_task_to_dict(self) -> None:
        """Test converting completed task to dict."""
        task = CompletedTask(
            name="Write Report",
            completed_at=datetime(2026, 2, 19, 10, 0),
            category="admin",
            source="Done/TASK_report.md",
        )

        data = task.to_dict()

        assert data["name"] == "Write Report"
        assert data["category"] == "admin"
        assert "completed_at" in data


class TestBottleneck:
    """Tests for Bottleneck dataclass."""

    def test_create_bottleneck(self) -> None:
        """Test creating a bottleneck."""
        bottleneck = Bottleneck(
            description="Invoice approval taking >3 days",
            severity="high",
            expected_duration_hours=24,
            actual_duration_hours=72,
            affected_area="finance",
        )

        assert bottleneck.description == "Invoice approval taking >3 days"
        assert bottleneck.severity == "high"
        assert bottleneck.expected_duration_hours == 24
        assert bottleneck.actual_duration_hours == 72
        assert bottleneck.affected_area == "finance"

    def test_bottleneck_delay_ratio(self) -> None:
        """Test calculating the delay ratio."""
        bottleneck = Bottleneck(
            description="Slow process",
            severity="medium",
            expected_duration_hours=10,
            actual_duration_hours=30,
            affected_area="ops",
        )

        assert bottleneck.delay_ratio() == 3.0

    def test_bottleneck_delay_ratio_zero_expected(self) -> None:
        """Test delay ratio when expected is zero."""
        bottleneck = Bottleneck(
            description="Unexpected task",
            severity="low",
            expected_duration_hours=0,
            actual_duration_hours=5,
            affected_area="ops",
        )

        assert bottleneck.delay_ratio() == float("inf")

    def test_bottleneck_to_dict(self) -> None:
        """Test converting bottleneck to dict."""
        bottleneck = Bottleneck(
            description="Test",
            severity="high",
            expected_duration_hours=10,
            actual_duration_hours=20,
            affected_area="test",
        )

        data = bottleneck.to_dict()

        assert data["severity"] == "high"
        assert data["delay_ratio"] == 2.0


class TestCostSuggestion:
    """Tests for CostSuggestion dataclass."""

    def test_create_cost_suggestion(self) -> None:
        """Test creating a cost suggestion."""
        suggestion = CostSuggestion(
            description="Cancel unused Slack premium plan",
            estimated_savings=Decimal("150.00"),
            currency="USD",
            category="subscription",
            confidence="high",
        )

        assert suggestion.description == "Cancel unused Slack premium plan"
        assert suggestion.estimated_savings == Decimal("150.00")
        assert suggestion.category == "subscription"
        assert suggestion.confidence == "high"

    def test_cost_suggestion_to_dict(self) -> None:
        """Test converting cost suggestion to dict."""
        suggestion = CostSuggestion(
            description="Downgrade hosting",
            estimated_savings=Decimal("300.00"),
            currency="USD",
            category="infrastructure",
            confidence="medium",
        )

        data = suggestion.to_dict()

        assert data["estimated_savings"] == "300.00"
        assert data["category"] == "infrastructure"


class TestDeadline:
    """Tests for Deadline dataclass."""

    def test_create_deadline(self) -> None:
        """Test creating a deadline."""
        deadline = Deadline(
            description="Q1 report due",
            due_date=date(2026, 3, 31),
            priority="high",
            status="on_track",
        )

        assert deadline.description == "Q1 report due"
        assert deadline.due_date == date(2026, 3, 31)
        assert deadline.priority == "high"
        assert deadline.status == "on_track"

    def test_deadline_days_remaining(self) -> None:
        """Test calculating days remaining."""
        future_date = date(2099, 12, 31)
        deadline = Deadline(
            description="Far future",
            due_date=future_date,
            priority="low",
            status="on_track",
        )

        days = deadline.days_remaining()
        assert days > 0

    def test_deadline_overdue(self) -> None:
        """Test detecting overdue deadline."""
        past_date = date(2020, 1, 1)
        deadline = Deadline(
            description="Past deadline",
            due_date=past_date,
            priority="high",
            status="at_risk",
        )

        days = deadline.days_remaining()
        assert days < 0

    def test_deadline_to_dict(self) -> None:
        """Test converting deadline to dict."""
        deadline = Deadline(
            description="Test",
            due_date=date(2026, 6, 1),
            priority="medium",
            status="on_track",
        )

        data = deadline.to_dict()

        assert data["due_date"] == "2026-06-01"
        assert "days_remaining" in data


class TestSocialSummary:
    """Tests for SocialSummary dataclass."""

    def test_create_social_summary(self) -> None:
        """Test creating a social media summary."""
        summary = SocialSummary(
            posts_published=3,
            total_impressions=15000,
            total_engagements=450,
            top_post_topic="AI in Business",
            leads_detected=2,
        )

        assert summary.posts_published == 3
        assert summary.total_impressions == 15000
        assert summary.total_engagements == 450
        assert summary.top_post_topic == "AI in Business"
        assert summary.leads_detected == 2

    def test_social_summary_engagement_rate(self) -> None:
        """Test calculating engagement rate."""
        summary = SocialSummary(
            posts_published=5,
            total_impressions=10000,
            total_engagements=500,
            top_post_topic="Tech",
            leads_detected=1,
        )

        rate = summary.engagement_rate()
        assert rate == 5.0

    def test_social_summary_engagement_rate_zero_impressions(self) -> None:
        """Test engagement rate with zero impressions."""
        summary = SocialSummary(
            posts_published=0,
            total_impressions=0,
            total_engagements=0,
            top_post_topic="",
            leads_detected=0,
        )

        rate = summary.engagement_rate()
        assert rate == 0.0

    def test_social_summary_to_dict(self) -> None:
        """Test converting social summary to dict."""
        summary = SocialSummary(
            posts_published=2,
            total_impressions=8000,
            total_engagements=400,
            top_post_topic="Growth",
            leads_detected=3,
        )

        data = summary.to_dict()

        assert data["posts_published"] == 2
        assert data["engagement_rate"] == 5.0


class TestAuditSummary:
    """Tests for AuditSummary dataclass."""

    def test_create_audit_summary(self) -> None:
        """Test creating an audit summary."""
        summary = AuditSummary(
            total_transactions=150,
            flagged_transactions=3,
            unused_subscriptions=["Slack Premium", "Zoom Pro"],
            data_quality_score=Decimal("0.95"),
            compliance_issues=[],
        )

        assert summary.total_transactions == 150
        assert summary.flagged_transactions == 3
        assert len(summary.unused_subscriptions) == 2
        assert summary.data_quality_score == Decimal("0.95")
        assert len(summary.compliance_issues) == 0

    def test_audit_summary_to_dict(self) -> None:
        """Test converting audit summary to dict."""
        summary = AuditSummary(
            total_transactions=100,
            flagged_transactions=5,
            unused_subscriptions=["Service A"],
            data_quality_score=Decimal("0.88"),
            compliance_issues=["Missing receipts for 3 transactions"],
        )

        data = summary.to_dict()

        assert data["total_transactions"] == 100
        assert data["flagged_transactions"] == 5
        assert data["data_quality_score"] == "0.88"
        assert len(data["compliance_issues"]) == 1


class TestCEOBriefing:
    """Tests for CEOBriefing dataclass."""

    def test_create_briefing_minimal(self) -> None:
        """Test creating a briefing with minimal fields."""
        briefing = CEOBriefing(
            id="2026-02-21",
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
            executive_summary="Business on track this week.",
            revenue_this_week=Decimal("15000.00"),
            revenue_mtd=Decimal("45000.00"),
            revenue_trend="on_track",
            completed_tasks=[],
            bottlenecks=[],
            cost_suggestions=[],
            upcoming_deadlines=[],
        )

        assert briefing.id == "2026-02-21"
        assert briefing.revenue_this_week == Decimal("15000.00")
        assert briefing.revenue_trend == "on_track"
        assert briefing.monthly_goal is None
        assert briefing.social_media_summary is None
        assert briefing.audit_summary is None
        assert isinstance(briefing.generated_at, datetime)

    def test_create_briefing_full(self) -> None:
        """Test creating a full briefing with all sections."""
        briefing = CEOBriefing(
            id="2026-02-21",
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
            executive_summary="Strong week with revenue ahead of target.",
            revenue_this_week=Decimal("20000.00"),
            revenue_mtd=Decimal("60000.00"),
            monthly_goal=Decimal("80000.00"),
            revenue_trend="ahead",
            completed_tasks=[
                CompletedTask(
                    name="Launch Feature X",
                    completed_at=datetime(2026, 2, 20, 16, 0),
                    category="engineering",
                    source="Done/feature_x.md",
                ),
            ],
            bottlenecks=[
                Bottleneck(
                    description="Slow code review",
                    severity="medium",
                    expected_duration_hours=4,
                    actual_duration_hours=12,
                    affected_area="engineering",
                ),
            ],
            cost_suggestions=[
                CostSuggestion(
                    description="Unused CI minutes",
                    estimated_savings=Decimal("50.00"),
                    currency="USD",
                    category="infrastructure",
                    confidence="high",
                ),
            ],
            upcoming_deadlines=[
                Deadline(
                    description="Sprint end",
                    due_date=date(2026, 2, 28),
                    priority="high",
                    status="on_track",
                ),
            ],
            social_media_summary=SocialSummary(
                posts_published=4,
                total_impressions=20000,
                total_engagements=600,
                top_post_topic="Product Launch",
                leads_detected=5,
            ),
            audit_summary=AuditSummary(
                total_transactions=200,
                flagged_transactions=2,
                unused_subscriptions=[],
                data_quality_score=Decimal("0.97"),
                compliance_issues=[],
            ),
        )

        assert len(briefing.completed_tasks) == 1
        assert len(briefing.bottlenecks) == 1
        assert len(briefing.cost_suggestions) == 1
        assert len(briefing.upcoming_deadlines) == 1
        assert briefing.social_media_summary is not None
        assert briefing.audit_summary is not None
        assert briefing.monthly_goal == Decimal("80000.00")

    def test_briefing_revenue_progress(self) -> None:
        """Test calculating revenue progress percentage."""
        briefing = CEOBriefing(
            id="2026-02-21",
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
            executive_summary="Test",
            revenue_this_week=Decimal("10000"),
            revenue_mtd=Decimal("60000"),
            monthly_goal=Decimal("80000"),
            revenue_trend="on_track",
            completed_tasks=[],
            bottlenecks=[],
            cost_suggestions=[],
            upcoming_deadlines=[],
        )

        progress = briefing.revenue_progress()
        assert progress == 75.0

    def test_briefing_revenue_progress_no_goal(self) -> None:
        """Test revenue progress when no monthly goal is set."""
        briefing = CEOBriefing(
            id="2026-02-21",
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
            executive_summary="Test",
            revenue_this_week=Decimal("10000"),
            revenue_mtd=Decimal("60000"),
            revenue_trend="on_track",
            completed_tasks=[],
            bottlenecks=[],
            cost_suggestions=[],
            upcoming_deadlines=[],
        )

        progress = briefing.revenue_progress()
        assert progress is None

    def test_briefing_to_dict(self) -> None:
        """Test converting briefing to dictionary."""
        briefing = CEOBriefing(
            id="2026-02-21",
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
            executive_summary="Summary text",
            revenue_this_week=Decimal("15000"),
            revenue_mtd=Decimal("45000"),
            revenue_trend="on_track",
            completed_tasks=[],
            bottlenecks=[],
            cost_suggestions=[],
            upcoming_deadlines=[],
        )

        data = briefing.to_dict()

        assert data["id"] == "2026-02-21"
        assert data["revenue_this_week"] == "15000"
        assert data["revenue_mtd"] == "45000"
        assert data["revenue_trend"] == "on_track"
        assert "generated_at" in data

    def test_briefing_get_filename(self) -> None:
        """Test getting the filename for the briefing."""
        briefing = CEOBriefing(
            id="2026-02-21",
            period_start=date(2026, 2, 15),
            period_end=date(2026, 2, 21),
            executive_summary="Test",
            revenue_this_week=Decimal("0"),
            revenue_mtd=Decimal("0"),
            revenue_trend="behind",
            completed_tasks=[],
            bottlenecks=[],
            cost_suggestions=[],
            upcoming_deadlines=[],
        )

        assert briefing.get_filename() == "CEO_Briefing_2026-02-21.md"
