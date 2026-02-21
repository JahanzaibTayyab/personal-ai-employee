"""CEO Briefing data models for weekly business audit reports."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any


@dataclass
class CompletedTask:
    """A task completed during the briefing period.

    Attributes:
        name: Task name or description
        completed_at: When the task was completed
        category: Task category (e.g., engineering, admin, finance)
        source: File path in the vault where the task was stored
    """

    name: str
    completed_at: datetime
    category: str
    source: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "completed_at": self.completed_at.isoformat(),
            "category": self.category,
            "source": self.source,
        }


@dataclass
class Bottleneck:
    """A process bottleneck identified during audit.

    Attributes:
        description: What the bottleneck is
        severity: low, medium, or high
        expected_duration_hours: Expected time to complete
        actual_duration_hours: Actual time taken
        affected_area: Area of business affected
    """

    description: str
    severity: str
    expected_duration_hours: float
    actual_duration_hours: float
    affected_area: str

    def delay_ratio(self) -> float:
        """Calculate ratio of actual to expected duration.

        Returns:
            Ratio (e.g., 3.0 means 3x slower than expected)
        """
        if self.expected_duration_hours == 0:
            return float("inf")
        return self.actual_duration_hours / self.expected_duration_hours

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "description": self.description,
            "severity": self.severity,
            "expected_duration_hours": self.expected_duration_hours,
            "actual_duration_hours": self.actual_duration_hours,
            "affected_area": self.affected_area,
            "delay_ratio": self.delay_ratio(),
        }


@dataclass
class CostSuggestion:
    """A cost-saving suggestion identified during audit.

    Attributes:
        description: What the suggestion is
        estimated_savings: Estimated monthly savings
        currency: Currency code
        category: Category (e.g., subscription, infrastructure)
        confidence: Confidence level (low, medium, high)
    """

    description: str
    estimated_savings: Decimal
    currency: str
    category: str
    confidence: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "description": self.description,
            "estimated_savings": str(self.estimated_savings),
            "currency": self.currency,
            "category": self.category,
            "confidence": self.confidence,
        }


@dataclass
class Deadline:
    """An upcoming deadline.

    Attributes:
        description: What the deadline is for
        due_date: When it is due
        priority: low, medium, or high
        status: on_track, at_risk, or overdue
    """

    description: str
    due_date: date
    priority: str
    status: str

    def days_remaining(self) -> int:
        """Calculate days remaining until deadline.

        Returns:
            Number of days (negative if overdue)
        """
        return (self.due_date - date.today()).days

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "description": self.description,
            "due_date": self.due_date.isoformat(),
            "priority": self.priority,
            "status": self.status,
            "days_remaining": self.days_remaining(),
        }


@dataclass
class SocialSummary:
    """Social media activity summary for the period.

    Attributes:
        posts_published: Number of posts published
        total_impressions: Total impression count
        total_engagements: Total engagement count (likes + comments + shares)
        top_post_topic: Topic of the best-performing post
        leads_detected: Number of potential sales leads detected
    """

    posts_published: int
    total_impressions: int
    total_engagements: int
    top_post_topic: str
    leads_detected: int

    def engagement_rate(self) -> float:
        """Calculate engagement rate as a percentage.

        Returns:
            Engagement rate (0.0 if no impressions)
        """
        if self.total_impressions == 0:
            return 0.0
        return (self.total_engagements / self.total_impressions) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "posts_published": self.posts_published,
            "total_impressions": self.total_impressions,
            "total_engagements": self.total_engagements,
            "top_post_topic": self.top_post_topic,
            "leads_detected": self.leads_detected,
            "engagement_rate": self.engagement_rate(),
        }


@dataclass
class AuditSummary:
    """Financial audit summary.

    Attributes:
        total_transactions: Total transactions reviewed
        flagged_transactions: Number of flagged transactions
        unused_subscriptions: List of unused subscription names
        data_quality_score: Score from 0 to 1
        compliance_issues: List of compliance issue descriptions
    """

    total_transactions: int
    flagged_transactions: int
    unused_subscriptions: list[str]
    data_quality_score: Decimal
    compliance_issues: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_transactions": self.total_transactions,
            "flagged_transactions": self.flagged_transactions,
            "unused_subscriptions": self.unused_subscriptions,
            "data_quality_score": str(self.data_quality_score),
            "compliance_issues": self.compliance_issues,
        }


@dataclass
class CEOBriefing:
    """Weekly CEO briefing report.

    Aggregates data from Odoo, vault activity, social media,
    and log analysis into a comprehensive business report.

    Attributes:
        id: Date-based identifier (YYYY-MM-DD)
        period_start: Start of the reporting period
        period_end: End of the reporting period
        executive_summary: High-level summary paragraph
        revenue_this_week: Revenue for the period
        revenue_mtd: Month-to-date revenue
        monthly_goal: Optional monthly revenue target
        revenue_trend: on_track, ahead, or behind
        completed_tasks: Tasks completed during the period
        bottlenecks: Identified process bottlenecks
        cost_suggestions: Cost-saving suggestions
        upcoming_deadlines: Upcoming deadlines
        social_media_summary: Optional social media metrics
        audit_summary: Optional financial audit summary
        generated_at: When the briefing was generated
    """

    id: str
    period_start: date
    period_end: date
    executive_summary: str
    revenue_this_week: Decimal
    revenue_mtd: Decimal
    revenue_trend: str
    completed_tasks: list[CompletedTask]
    bottlenecks: list[Bottleneck]
    cost_suggestions: list[CostSuggestion]
    upcoming_deadlines: list[Deadline]
    monthly_goal: Decimal | None = None
    social_media_summary: SocialSummary | None = None
    audit_summary: AuditSummary | None = None
    generated_at: datetime = field(default_factory=datetime.now)

    def revenue_progress(self) -> float | None:
        """Calculate revenue progress toward monthly goal.

        Returns:
            Percentage progress, or None if no goal set
        """
        if self.monthly_goal is None or self.monthly_goal == Decimal("0"):
            return None
        return float(
            (self.revenue_mtd / self.monthly_goal) * Decimal("100")
        )

    def get_filename(self) -> str:
        """Generate the filename for this briefing.

        Returns:
            Filename like CEO_Briefing_2026-02-21.md
        """
        return f"CEO_Briefing_{self.id}.md"

    def to_dict(self) -> dict[str, Any]:
        """Convert briefing to dictionary."""
        data: dict[str, Any] = {
            "id": self.id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "executive_summary": self.executive_summary,
            "revenue_this_week": str(self.revenue_this_week),
            "revenue_mtd": str(self.revenue_mtd),
            "revenue_trend": self.revenue_trend,
            "completed_tasks": [t.to_dict() for t in self.completed_tasks],
            "bottlenecks": [b.to_dict() for b in self.bottlenecks],
            "cost_suggestions": [c.to_dict() for c in self.cost_suggestions],
            "upcoming_deadlines": [
                d.to_dict() for d in self.upcoming_deadlines
            ],
            "generated_at": self.generated_at.isoformat(),
        }

        if self.monthly_goal is not None:
            data["monthly_goal"] = str(self.monthly_goal)

        if self.social_media_summary is not None:
            data["social_media_summary"] = (
                self.social_media_summary.to_dict()
            )

        if self.audit_summary is not None:
            data["audit_summary"] = self.audit_summary.to_dict()

        return data
