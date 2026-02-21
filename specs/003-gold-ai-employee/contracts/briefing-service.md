# CEO Briefing Service Contract

**Version**: 1.0.0 | **Created**: 2026-02-21

## Overview

Service for generating weekly CEO briefings with business metrics, task analysis, and proactive recommendations.

---

## Interface: BriefingService

### Generation Methods

#### generate_briefing

Generate a comprehensive CEO briefing for a period.

**Input**:
```python
def generate_briefing(
    period_start: date = None,  # Default: 7 days ago
    period_end: date = None,    # Default: today
    include_suggestions: bool = True
) -> CEOBriefing
```

**Output**: CEOBriefing model

**Errors**:
- `OdooConnectionError`: Cannot fetch financial data
- `DataAggregationError`: Error collecting metrics

---

#### get_briefing

Retrieve a previously generated briefing.

**Input**:
```python
def get_briefing(briefing_id: str) -> Optional[CEOBriefing]
```

---

#### list_briefings

List generated briefings.

**Input**:
```python
def list_briefings(
    limit: int = 10
) -> list[CEOBriefing]
```

---

### Data Aggregation Methods

#### get_revenue_metrics

Aggregate revenue data from Odoo.

**Input**:
```python
def get_revenue_metrics(
    start_date: date,
    end_date: date
) -> dict
```

**Output**:
```python
{
    "this_week": Decimal,
    "mtd": Decimal,
    "monthly_goal": Decimal,  # From Business_Goals.md
    "percentage_of_goal": float,
    "trend": str  # "ahead", "on_track", "behind"
}
```

---

#### get_completed_tasks

Get tasks completed in the period.

**Input**:
```python
def get_completed_tasks(
    start_date: date,
    end_date: date
) -> list[CompletedTask]
```

---

#### analyze_bottlenecks

Identify tasks that took longer than expected.

**Input**:
```python
def analyze_bottlenecks(
    start_date: date,
    end_date: date,
    threshold_ratio: float = 1.5  # 50% over expected
) -> list[Bottleneck]
```

---

#### analyze_subscriptions

Identify unused subscriptions from transaction history.

**Input**:
```python
def analyze_subscriptions(
    lookback_days: int = 90,
    activity_threshold_days: int = 30
) -> list[CostSuggestion]
```

---

#### get_upcoming_deadlines

Get approaching deadlines from Plans and Business_Goals.

**Input**:
```python
def get_upcoming_deadlines(
    days_ahead: int = 14
) -> list[Deadline]
```

---

#### get_social_summary

Aggregate social media engagement metrics.

**Input**:
```python
def get_social_summary(
    start_date: date,
    end_date: date
) -> SocialSummary
```

**Output**:
```python
{
    "linkedin": {
        "posts": int,
        "total_engagement": int,
        "top_post": str
    },
    "facebook": {
        "posts": int,
        "total_engagement": int,
        "reach": int
    },
    "instagram": {
        "posts": int,
        "total_engagement": int,
        "reach": int
    },
    "twitter": {
        "tweets": int,
        "total_engagement": int,
        "impressions": int
    }
}
```

---

#### get_audit_summary

Summarize actions from audit logs.

**Input**:
```python
def get_audit_summary(
    start_date: date,
    end_date: date
) -> AuditSummary
```

**Output**:
```python
{
    "total_actions": int,
    "by_type": dict[str, int],
    "success_rate": float,
    "anomalies": list[str]  # Unusual patterns
}
```

---

### Template Methods

#### render_briefing

Render briefing to Markdown using template.

**Input**:
```python
def render_briefing(briefing: CEOBriefing) -> str
```

**Output**: Markdown string

---

#### save_briefing

Save briefing to vault.

**Input**:
```python
def save_briefing(
    briefing: CEOBriefing,
    rendered_content: str
) -> Path
```

**Output**: Path to saved file

---

## Scheduled Task

The briefing service should be configured with a scheduled task:

```python
{
    "name": "weekly_ceo_briefing",
    "schedule": "0 21 * * 0",  # Sunday 9:00 PM
    "action": "generate_briefing",
    "parameters": {}
}
```

---

## Events

| Event | When | Payload |
|-------|------|---------|
| `briefing_started` | Generation begins | period |
| `briefing_completed` | Generation done | briefing_id, path |
| `briefing_failed` | Generation error | error |
| `subscription_flagged` | Unused subscription | service, cost |
| `bottleneck_identified` | Delayed task | task, delay_days |

---

## Business_Goals.md Schema

The briefing service reads from `/Business_Goals.md`:

```yaml
---
last_updated: 2026-02-21
review_frequency: weekly
---

## Revenue Targets
monthly_goal: 10000
quarterly_goal: 30000

## Key Metrics
client_response_time_hours: 24
invoice_payment_rate_percent: 90
max_software_costs: 500

## Active Projects
- name: Project Alpha
  due_date: 2026-03-15
  budget: 2000
- name: Project Beta
  due_date: 2026-03-30
  budget: 3500

## Subscription Patterns
# Services to track for usage
tracked_services:
  - netflix.com
  - spotify.com
  - notion.so
  - slack.com
  - github.com
```
