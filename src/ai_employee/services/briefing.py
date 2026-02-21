"""CEO Briefing generation service.

Aggregates data from Odoo, vault activity logs, social media,
and completed tasks to generate weekly CEO briefings.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ai_employee.config import VaultConfig
from ai_employee.models.briefing import (
    AuditSummary,
    Bottleneck,
    CEOBriefing,
    CompletedTask,
    CostSuggestion,
    Deadline,
    SocialSummary,
)

if TYPE_CHECKING:
    from ai_employee.services.odoo import OdooService

logger = logging.getLogger(__name__)

# Threshold for detecting slow operations (in milliseconds)
_SLOW_OPERATION_THRESHOLD_MS = 120_000  # 2 minutes

# Threshold for unused subscription detection (in days)
_UNUSED_SUBSCRIPTION_DAYS = 30

# Template directory relative to package
_TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / "templates"


class BriefingService:
    """Service for generating CEO briefing reports.

    Aggregates data from multiple sources:
    - Odoo ERP (financial data)
    - /Done folder (completed tasks)
    - /Logs folder (activity analysis)
    - /Social/LinkedIn (social media metrics)
    """

    def __init__(
        self,
        vault_config: VaultConfig,
        odoo_service: OdooService | None = None,
    ) -> None:
        """Initialize BriefingService.

        Args:
            vault_config: Vault configuration with paths
            odoo_service: Optional Odoo service for financial data
        """
        self.vault_config = vault_config
        self._odoo_service = odoo_service
        self._jinja_env = self._init_jinja()

    def _init_jinja(self) -> Environment:
        """Initialize Jinja2 template environment.

        Returns:
            Jinja2 Environment
        """
        template_dir = _TEMPLATE_DIR
        if not template_dir.exists():
            template_dir = Path(__file__).parent.parent / "templates"

        if template_dir.exists():
            return Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=select_autoescape(default=False),
                trim_blocks=True,
                lstrip_blocks=True,
            )

        # Fallback: return environment without loader
        return Environment(
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    # ── Data Collection ──────────────────────────────────────────────

    def get_completed_tasks(
        self, period_start: date, period_end: date
    ) -> list[CompletedTask]:
        """Collect completed tasks from /Done folder.

        Args:
            period_start: Start of period
            period_end: End of period

        Returns:
            List of CompletedTask objects
        """
        done_dir = self.vault_config.done
        if not done_dir.exists():
            return []

        tasks: list[CompletedTask] = []

        for md_file in done_dir.glob("*.md"):
            try:
                task = self._parse_done_file(
                    md_file, period_start, period_end
                )
                if task is not None:
                    tasks.append(task)
            except Exception as e:
                logger.warning(
                    "Failed to parse done file %s: %s", md_file.name, e
                )

        return sorted(tasks, key=lambda t: t.completed_at)

    def _parse_done_file(
        self,
        filepath: Path,
        period_start: date,
        period_end: date,
    ) -> CompletedTask | None:
        """Parse a file from /Done folder into a CompletedTask.

        Args:
            filepath: Path to the .md file
            period_start: Period start for filtering
            period_end: Period end for filtering

        Returns:
            CompletedTask or None if outside period
        """
        content = filepath.read_text()

        if not content.startswith("---"):
            return None

        # Parse YAML frontmatter
        lines = content.split("\n")
        end_idx = -1
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                end_idx = i
                break

        if end_idx == -1:
            return None

        try:
            frontmatter_text = "\n".join(lines[1:end_idx])
            frontmatter = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError:
            return None

        # Get processed_at timestamp
        processed_at_str = frontmatter.get("processed_at")
        if not processed_at_str:
            # Fall back to file modification time
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            processed_at = mtime
        else:
            processed_at = datetime.fromisoformat(str(processed_at_str))

        # Filter by period
        processed_date = processed_at.date()
        if processed_date < period_start or processed_date > period_end:
            return None

        # Determine category from type
        item_type = frontmatter.get("type", "unknown")
        category = self._categorize_task(item_type)

        name = frontmatter.get("original_name", filepath.stem)

        return CompletedTask(
            name=str(name),
            completed_at=processed_at,
            category=category,
            source=f"Done/{filepath.name}",
        )

    @staticmethod
    def _categorize_task(item_type: str) -> str:
        """Categorize a task based on its type.

        Args:
            item_type: Action item type string

        Returns:
            Category string
        """
        categories: dict[str, str] = {
            "file_drop": "admin",
            "email": "communication",
            "whatsapp": "communication",
            "linkedin": "social_media",
            "scheduled": "operations",
        }
        return categories.get(item_type, "general")

    def get_revenue_data(
        self, period_start: date, period_end: date
    ) -> dict[str, Any]:
        """Get revenue data from Odoo or return defaults.

        Args:
            period_start: Period start
            period_end: Period end

        Returns:
            Revenue data dict
        """
        if (
            self._odoo_service is not None
            and self._odoo_service.is_connected()
        ):
            try:
                return self._odoo_service.get_revenue_summary(
                    start_date=period_start,
                    end_date=period_end,
                )
            except Exception as e:
                logger.error("Failed to get Odoo revenue data: %s", e)

        return {
            "total_invoiced": Decimal("0"),
            "total_collected": Decimal("0"),
            "total_outstanding": Decimal("0"),
            "invoice_count": 0,
        }

    def _get_mtd_revenue(self, period_end: date) -> Decimal:
        """Get month-to-date revenue.

        Args:
            period_end: End of current period

        Returns:
            MTD revenue
        """
        month_start = period_end.replace(day=1)

        if (
            self._odoo_service is not None
            and self._odoo_service.is_connected()
        ):
            try:
                summary = self._odoo_service.get_revenue_summary(
                    start_date=month_start,
                    end_date=period_end,
                )
                return Decimal(str(summary["total_invoiced"]))
            except Exception as e:
                logger.error("Failed to get MTD revenue: %s", e)

        return Decimal("0")

    def identify_bottlenecks(
        self, period_start: date, period_end: date
    ) -> list[Bottleneck]:
        """Identify process bottlenecks from activity logs.

        Looks for operations that took significantly longer than expected.

        Args:
            period_start: Period start
            period_end: Period end

        Returns:
            List of Bottleneck objects
        """
        logs_dir = self.vault_config.logs
        if not logs_dir.exists():
            return []

        bottlenecks: list[Bottleneck] = []
        slow_operations: list[dict[str, Any]] = []
        failed_operations: list[dict[str, Any]] = []

        # Scan log files for the period
        current_date = period_start
        while current_date <= period_end:
            log_file = logs_dir / f"claude_{current_date.isoformat()}.log"
            if log_file.exists():
                entries = self._read_log_entries(log_file)

                for entry in entries:
                    duration = entry.get("duration_ms", 0)
                    if duration > _SLOW_OPERATION_THRESHOLD_MS:
                        slow_operations.append(entry)

                    if entry.get("outcome") == "failure":
                        failed_operations.append(entry)

            current_date += timedelta(days=1)

        # Create bottlenecks from slow operations
        if slow_operations:
            avg_duration_ms = sum(
                op.get("duration_ms", 0) for op in slow_operations
            ) / len(slow_operations)

            bottlenecks.append(Bottleneck(
                description=(
                    f"{len(slow_operations)} operations exceeded "
                    f"{_SLOW_OPERATION_THRESHOLD_MS / 1000:.0f}s threshold"
                ),
                severity=(
                    "high" if len(slow_operations) > 5 else "medium"
                ),
                expected_duration_hours=(
                    _SLOW_OPERATION_THRESHOLD_MS / 3_600_000
                ),
                actual_duration_hours=avg_duration_ms / 3_600_000,
                affected_area="processing",
            ))

        # Create bottlenecks from failures
        if failed_operations:
            bottlenecks.append(Bottleneck(
                description=(
                    f"{len(failed_operations)} operations failed "
                    "during period"
                ),
                severity=(
                    "high" if len(failed_operations) > 3 else "medium"
                ),
                expected_duration_hours=0,
                actual_duration_hours=0,
                affected_area="reliability",
            ))

        return bottlenecks

    def generate_cost_suggestions(
        self, period_start: date, period_end: date
    ) -> list[CostSuggestion]:
        """Generate cost-saving suggestions.

        Identifies unused subscriptions (30+ days without activity)
        and other optimization opportunities.

        Args:
            period_start: Period start
            period_end: Period end

        Returns:
            List of CostSuggestion objects
        """
        logs_dir = self.vault_config.logs
        if not logs_dir.exists():
            return []

        # Check for any log activity in the last 30 days
        suggestions: list[CostSuggestion] = []
        log_dates = self._get_log_dates(logs_dir)

        if not log_dates:
            return []

        # Look for patterns of unused services
        # This is a heuristic analysis of log content
        recent_services: set[str] = set()
        old_services: set[str] = set()
        threshold_date = period_end - timedelta(days=_UNUSED_SUBSCRIPTION_DAYS)

        for log_date in log_dates:
            log_file = logs_dir / f"claude_{log_date}.log"
            if not log_file.exists():
                continue

            entries = self._read_log_entries(log_file)
            for entry in entries:
                details = entry.get("details", "")
                item_id = entry.get("item_id", "")

                # Extract service references from logs
                service_ref = self._extract_service_ref(details, item_id)
                if service_ref:
                    entry_date = date.fromisoformat(log_date)
                    if entry_date >= threshold_date:
                        recent_services.add(service_ref)
                    else:
                        old_services.add(service_ref)

        # Services found in old logs but not recent ones
        unused = old_services - recent_services
        for service in unused:
            suggestions.append(CostSuggestion(
                description=f"No activity for '{service}' in last 30 days",
                estimated_savings=Decimal("0"),
                currency="USD",
                category="subscription",
                confidence="low",
            ))

        return suggestions

    def get_social_summary(
        self, period_start: date, period_end: date
    ) -> SocialSummary | None:
        """Get social media summary from LinkedIn posts.

        Args:
            period_start: Period start
            period_end: Period end

        Returns:
            SocialSummary or None if no posts found
        """
        posts_dir = self.vault_config.social_linkedin_posts
        if not posts_dir.exists():
            return None

        posts_published = 0
        total_impressions = 0
        total_engagements = 0
        leads_detected = 0
        top_post_topic = ""
        top_impressions = 0

        for post_file in posts_dir.glob("post_*.md"):
            try:
                post_data = self._parse_post_file(
                    post_file, period_start, period_end
                )
                if post_data is None:
                    continue

                posts_published += 1
                impressions = post_data.get("impressions", 0)
                likes = post_data.get("likes", 0)
                comments = post_data.get("comments", 0)
                shares = post_data.get("shares", 0)

                total_impressions += impressions
                total_engagements += likes + comments + shares

                if post_data.get("lead_detected"):
                    leads_detected += 1

                if impressions > top_impressions:
                    top_impressions = impressions
                    top_post_topic = post_data.get("topic", "")

            except Exception as e:
                logger.warning(
                    "Failed to parse post %s: %s", post_file.name, e
                )

        if posts_published == 0:
            return None

        return SocialSummary(
            posts_published=posts_published,
            total_impressions=total_impressions,
            total_engagements=total_engagements,
            top_post_topic=top_post_topic,
            leads_detected=leads_detected,
        )

    def _parse_post_file(
        self,
        filepath: Path,
        period_start: date,
        period_end: date,
    ) -> dict[str, Any] | None:
        """Parse a LinkedIn post file.

        Args:
            filepath: Path to the post file
            period_start: Period start for filtering
            period_end: Period end for filtering

        Returns:
            Post data dict or None if outside period
        """
        content = filepath.read_text()

        if not content.startswith("---"):
            return None

        lines = content.split("\n")
        end_idx = -1
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                end_idx = i
                break

        if end_idx == -1:
            return None

        try:
            frontmatter_text = "\n".join(lines[1:end_idx])
            data = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError:
            return None

        # Check status and date
        if data.get("status") != "published":
            return None

        published_at_str = data.get("published_at")
        if not published_at_str:
            return None

        published_at = datetime.fromisoformat(str(published_at_str))
        published_date = published_at.date()

        if published_date < period_start or published_date > period_end:
            return None

        return data

    # ── Briefing Generation ──────────────────────────────────────────

    def generate_briefing(
        self,
        period_start: date,
        period_end: date,
        monthly_goal: Decimal | None = None,
    ) -> CEOBriefing:
        """Generate a complete CEO briefing for the given period.

        Args:
            period_start: Start of reporting period
            period_end: End of reporting period
            monthly_goal: Optional monthly revenue target

        Returns:
            CEOBriefing instance
        """
        # Collect data from all sources
        completed_tasks = self.get_completed_tasks(
            period_start, period_end
        )
        revenue_data = self.get_revenue_data(period_start, period_end)
        revenue_mtd = self._get_mtd_revenue(period_end)
        bottlenecks = self.identify_bottlenecks(period_start, period_end)
        cost_suggestions = self.generate_cost_suggestions(
            period_start, period_end
        )
        social_summary = self.get_social_summary(period_start, period_end)

        revenue_this_week = revenue_data["total_invoiced"]

        # Determine revenue trend
        revenue_trend = self._determine_revenue_trend(
            revenue_mtd, monthly_goal, period_end
        )

        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            completed_tasks=completed_tasks,
            revenue_this_week=revenue_this_week,
            revenue_trend=revenue_trend,
            bottlenecks=bottlenecks,
            social_summary=social_summary,
        )

        return CEOBriefing(
            id=period_end.isoformat(),
            period_start=period_start,
            period_end=period_end,
            executive_summary=executive_summary,
            revenue_this_week=revenue_this_week,
            revenue_mtd=revenue_mtd,
            monthly_goal=monthly_goal,
            revenue_trend=revenue_trend,
            completed_tasks=completed_tasks,
            bottlenecks=bottlenecks,
            cost_suggestions=cost_suggestions,
            upcoming_deadlines=[],
            social_media_summary=social_summary,
        )

    def write_briefing(self, briefing: CEOBriefing) -> Path:
        """Write a briefing to the /Briefings/ folder.

        Args:
            briefing: CEOBriefing to write

        Returns:
            Path to the written file
        """
        briefings_dir = self.vault_config.briefings
        briefings_dir.mkdir(parents=True, exist_ok=True)

        filepath = briefings_dir / briefing.get_filename()
        content = self.render_briefing(briefing)
        filepath.write_text(content)

        logger.info("Wrote briefing to %s", filepath)
        return filepath

    def render_briefing(self, briefing: CEOBriefing) -> str:
        """Render a briefing to markdown using Jinja2 template.

        Args:
            briefing: CEOBriefing to render

        Returns:
            Rendered markdown string
        """
        try:
            template = self._jinja_env.get_template(
                "ceo_briefing.md.j2"
            )
            return template.render(briefing=briefing)
        except Exception:
            # Fallback: render without template
            return self._render_briefing_fallback(briefing)

    def _render_briefing_fallback(self, briefing: CEOBriefing) -> str:
        """Render briefing without Jinja2 template.

        Args:
            briefing: CEOBriefing to render

        Returns:
            Rendered markdown string
        """
        lines: list[str] = []
        lines.append(
            f"# CEO Briefing - {briefing.period_start.isoformat()} "
            f"to {briefing.period_end.isoformat()}"
        )
        lines.append("")
        lines.append(
            f"*Generated: {briefing.generated_at.strftime('%Y-%m-%d %H:%M')}*"
        )
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(briefing.executive_summary)
        lines.append("")

        # Revenue
        lines.append("## Revenue")
        lines.append("")
        lines.append(
            f"- **This Week:** ${briefing.revenue_this_week:,.2f}"
        )
        lines.append(
            f"- **Month-to-Date:** ${briefing.revenue_mtd:,.2f}"
        )
        if briefing.monthly_goal:
            progress = briefing.revenue_progress()
            lines.append(
                f"- **Monthly Goal:** ${briefing.monthly_goal:,.2f} "
                f"({progress:.1f}% achieved)"
            )
        lines.append(f"- **Trend:** {briefing.revenue_trend}")
        lines.append("")

        # Completed Tasks
        if briefing.completed_tasks:
            lines.append("## Completed Tasks")
            lines.append("")
            for task in briefing.completed_tasks:
                lines.append(
                    f"- **{task.name}** [{task.category}] - "
                    f"{task.completed_at.strftime('%Y-%m-%d %H:%M')}"
                )
            lines.append("")

        # Bottlenecks
        if briefing.bottlenecks:
            lines.append("## Bottlenecks")
            lines.append("")
            for bn in briefing.bottlenecks:
                lines.append(
                    f"- [{bn.severity.upper()}] {bn.description} "
                    f"({bn.affected_area})"
                )
            lines.append("")

        # Cost Suggestions
        if briefing.cost_suggestions:
            lines.append("## Cost Optimization Suggestions")
            lines.append("")
            for cs in briefing.cost_suggestions:
                lines.append(
                    f"- {cs.description} "
                    f"(est. savings: ${cs.estimated_savings:,.2f}, "
                    f"confidence: {cs.confidence})"
                )
            lines.append("")

        # Social Media
        if briefing.social_media_summary:
            sm = briefing.social_media_summary
            lines.append("## Social Media")
            lines.append("")
            lines.append(f"- **Posts Published:** {sm.posts_published}")
            lines.append(
                f"- **Total Impressions:** {sm.total_impressions:,}"
            )
            lines.append(
                f"- **Engagement Rate:** {sm.engagement_rate():.1f}%"
            )
            if sm.top_post_topic:
                lines.append(
                    f"- **Top Post Topic:** {sm.top_post_topic}"
                )
            if sm.leads_detected > 0:
                lines.append(
                    f"- **Leads Detected:** {sm.leads_detected}"
                )
            lines.append("")

        # Upcoming Deadlines
        if briefing.upcoming_deadlines:
            lines.append("## Upcoming Deadlines")
            lines.append("")
            for dl in briefing.upcoming_deadlines:
                days = dl.days_remaining()
                lines.append(
                    f"- **{dl.description}** - "
                    f"{dl.due_date.isoformat()} "
                    f"({days} days, {dl.status})"
                )
            lines.append("")

        return "\n".join(lines)

    # ── Private Helpers ──────────────────────────────────────────────

    @staticmethod
    def _determine_revenue_trend(
        revenue_mtd: Decimal,
        monthly_goal: Decimal | None,
        period_end: date,
    ) -> str:
        """Determine revenue trend based on MTD vs goal.

        Args:
            revenue_mtd: Month-to-date revenue
            monthly_goal: Monthly target
            period_end: End of period

        Returns:
            'on_track', 'ahead', or 'behind'
        """
        if monthly_goal is None or monthly_goal == Decimal("0"):
            return "on_track"

        # Calculate expected progress based on day of month
        day_of_month = period_end.day
        days_in_month = 30  # approximation
        expected_pct = Decimal(str(day_of_month)) / Decimal(
            str(days_in_month)
        )
        expected_revenue = monthly_goal * expected_pct

        if revenue_mtd > expected_revenue * Decimal("1.1"):
            return "ahead"
        elif revenue_mtd < expected_revenue * Decimal("0.9"):
            return "behind"
        return "on_track"

    @staticmethod
    def _generate_executive_summary(
        completed_tasks: list[CompletedTask],
        revenue_this_week: Decimal,
        revenue_trend: str,
        bottlenecks: list[Bottleneck],
        social_summary: SocialSummary | None,
    ) -> str:
        """Generate executive summary paragraph.

        Args:
            completed_tasks: Tasks completed
            revenue_this_week: Weekly revenue
            revenue_trend: Revenue trend
            bottlenecks: Identified bottlenecks
            social_summary: Social media data

        Returns:
            Summary paragraph
        """
        parts: list[str] = []

        # Tasks summary
        task_count = len(completed_tasks)
        if task_count > 0:
            parts.append(
                f"{task_count} tasks completed this period"
            )

        # Revenue summary
        if revenue_this_week > Decimal("0"):
            trend_text = {
                "ahead": "ahead of target",
                "behind": "behind target",
                "on_track": "on track",
            }.get(revenue_trend, "on track")
            parts.append(
                f"revenue is {trend_text} at "
                f"${revenue_this_week:,.2f} this week"
            )

        # Bottleneck summary
        high_bottlenecks = sum(
            1 for b in bottlenecks if b.severity == "high"
        )
        if high_bottlenecks > 0:
            parts.append(
                f"{high_bottlenecks} high-severity bottleneck(s) identified"
            )

        # Social media
        if social_summary and social_summary.leads_detected > 0:
            parts.append(
                f"{social_summary.leads_detected} potential "
                "lead(s) detected on LinkedIn"
            )

        if not parts:
            return "No significant activity during this period."

        summary = ". ".join(p.capitalize() for p in parts) + "."
        return summary

    @staticmethod
    def _read_log_entries(log_file: Path) -> list[dict[str, Any]]:
        """Read entries from a JSONL log file.

        Args:
            log_file: Path to log file

        Returns:
            List of parsed log entries
        """
        entries: list[dict[str, Any]] = []

        try:
            for line in log_file.read_text().strip().split("\n"):
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

        return entries

    @staticmethod
    def _get_log_dates(logs_dir: Path) -> list[str]:
        """Get list of date strings from log filenames.

        Args:
            logs_dir: Path to logs directory

        Returns:
            List of date strings (YYYY-MM-DD)
        """
        dates: list[str] = []

        for log_file in logs_dir.glob("claude_*.log"):
            try:
                date_str = log_file.stem.replace("claude_", "")
                # Validate format
                date.fromisoformat(date_str)
                dates.append(date_str)
            except ValueError:
                continue

        return sorted(dates)

    @staticmethod
    def _extract_service_ref(details: str, item_id: str) -> str | None:
        """Extract a service reference from log entry.

        Args:
            details: Log entry details
            item_id: Log entry item ID

        Returns:
            Service reference string or None
        """
        # Simple heuristic: look for known service patterns
        known_patterns = [
            "slack", "zoom", "notion", "github", "jira",
            "confluence", "trello", "asana",
        ]

        combined = f"{details} {item_id}".lower()
        for pattern in known_patterns:
            if pattern in combined:
                return pattern

        return None
