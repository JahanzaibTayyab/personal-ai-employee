"""Data models for AI Employee."""

from ai_employee.models.action_item import (
    ActionItem,
    ActionItemStatus,
    ActionItemType,
    Priority,
    SourceType,
)
from ai_employee.models.activity_log import ActionType, ActivityLogEntry, Outcome
from ai_employee.models.watcher_event import EventType, WatcherEvent
from ai_employee.models.watcher_event import SourceType as WatcherSourceType

# Silver tier models
from ai_employee.models.approval_request import (
    ApprovalCategory,
    ApprovalRequest,
    ApprovalStatus,
)
from ai_employee.models.linkedin_post import (
    EngagementType,
    LinkedInEngagement,
    LinkedInPost,
    LinkedInPostStatus,
)
from ai_employee.models.plan import Plan, PlanStatus, PlanStep, StepStatus
from ai_employee.models.scheduled_task import (
    MissedStrategy,
    ScheduledTask,
    TaskType,
    create_daily_briefing_task,
    create_weekly_audit_task,
)
from ai_employee.models.whatsapp_message import (
    WhatsAppActionStatus,
    WhatsAppMessage,
)

__all__ = [
    # Bronze tier
    "ActionItem",
    "ActionItemStatus",
    "ActionItemType",
    "Priority",
    "SourceType",
    "ActivityLogEntry",
    "ActionType",
    "Outcome",
    "WatcherEvent",
    "EventType",
    "WatcherSourceType",
    # Silver tier - Approval
    "ApprovalRequest",
    "ApprovalCategory",
    "ApprovalStatus",
    # Silver tier - Planning
    "Plan",
    "PlanStep",
    "PlanStatus",
    "StepStatus",
    # Silver tier - WhatsApp
    "WhatsAppMessage",
    "WhatsAppActionStatus",
    # Silver tier - LinkedIn
    "LinkedInPost",
    "LinkedInPostStatus",
    "LinkedInEngagement",
    "EngagementType",
    # Silver tier - Scheduling
    "ScheduledTask",
    "MissedStrategy",
    "TaskType",
    "create_daily_briefing_task",
    "create_weekly_audit_task",
]
