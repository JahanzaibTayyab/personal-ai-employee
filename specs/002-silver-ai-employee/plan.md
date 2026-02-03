# Implementation Plan: Silver Tier - Functional Assistant

**Branch**: `002-silver-ai-employee` | **Date**: 2026-02-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-silver-ai-employee/spec.md`
**Skills Created**: 5 skills initialized via skill-creator tool

## Summary

Enhance the Bronze tier AI Employee with human-in-the-loop approval workflows, multi-channel monitoring (WhatsApp via Playwright, LinkedIn via API), Gmail integration via `google_workspace_mcp`, a Claude reasoning loop with Plan.md generation, and cron-based task scheduling. All features exposed through Agent Skills.

## Technical Context

**Language/Version**: Python 3.13+ (matching Bronze tier)
**Primary Dependencies**:
- Existing: watchdog, pyyaml, google-auth, google-api-python-client
- New: playwright (WhatsApp browser automation), python-linkedin-v2 or linkedin-api (LinkedIn integration), google_workspace_mcp (Gmail MCP), schedule or APScheduler (cron scheduling)
**Storage**: File-based (Obsidian vault markdown files) - extending Bronze tier pattern
**Testing**: pytest, pytest-cov (80% target), mypy for type checking
**Target Platform**: macOS/Linux (local machine with persistent browser sessions)
**Project Type**: Single Python package (extending src/ai_employee)
**Performance Goals**:
- WhatsApp message detection within 2 minutes
- Approved actions executed within 60 seconds
- Scheduled tasks within 1 minute of configured time
**Constraints**:
- All sensitive actions require human approval
- LinkedIn rate limits (max 25 posts/day)
- WhatsApp session persistence required
**Scale/Scope**: Single user, personal automation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Since no project-specific constitution is defined, applying general best practices:

| Principle | Status | Notes |
|-----------|--------|-------|
| Library-First | ✅ PASS | Each feature (approval, watchers, scheduler) implemented as independent service |
| Test-First (TDD) | ✅ PASS | Will follow TDD workflow per user's rules |
| Simplicity | ✅ PASS | File-based workflow, no external databases |
| Security | ✅ PASS | Credentials via .env, no secrets in code |

**No violations requiring justification.**

## Project Structure

### Documentation (this feature)

```text
specs/002-silver-ai-employee/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/ai_employee/
├── cli/
│   └── main.py              # Extended with new commands
├── config.py                # Extended VaultConfig for new folders
├── models/
│   ├── action_item.py       # Extended with new types (WhatsApp, LinkedIn)
│   ├── activity_log.py      # (existing)
│   ├── dashboard.py         # (existing)
│   ├── watcher_event.py     # Extended with new source types
│   ├── approval_request.py  # NEW: ApprovalRequest model
│   ├── plan.py              # NEW: Plan and PlanStep models
│   ├── scheduled_task.py    # NEW: ScheduledTask model
│   ├── linkedin_post.py     # NEW: LinkedInPost and engagement models
│   └── whatsapp_message.py  # NEW: WhatsAppMessage model
├── services/
│   ├── dashboard.py         # Extended for approval/plan status
│   ├── handbook.py          # (existing)
│   ├── processor.py         # Extended for approval workflow
│   ├── approval.py          # NEW: ApprovalService (monitor folders)
│   ├── planner.py           # NEW: ReasoningLoop/PlannerService
│   ├── scheduler.py         # NEW: SchedulerService (cron)
│   └── linkedin.py          # NEW: LinkedInService (API integration)
├── utils/
│   ├── frontmatter.py       # (existing)
│   └── jsonl_logger.py      # (existing)
├── watchers/
│   ├── base.py              # (existing)
│   ├── filesystem.py        # (existing)
│   ├── gmail.py             # (existing)
│   ├── whatsapp.py          # NEW: WhatsApp watcher (Playwright)
│   ├── linkedin.py          # NEW: LinkedIn engagement watcher
│   └── approval.py          # NEW: Approval folder watcher
├── mcp/
│   └── gmail_config.py      # NEW: google_workspace_mcp configuration
└── skills/                  # NEW: Agent skill implementations
    ├── __init__.py
    ├── post_linkedin.py     # /post-linkedin skill
    ├── create_plan.py       # /create-plan skill
    ├── send_email.py        # /send-email skill
    ├── approve_action.py    # /approve-action skill
    └── schedule_task.py     # /schedule-task skill

.claude/
├── skills/                  # Skill manifests for Claude Code
│   ├── post-linkedin/
│   │   └── SKILL.md
│   ├── create-plan/
│   │   └── SKILL.md
│   ├── send-email/
│   │   └── SKILL.md
│   ├── approve-action/
│   │   └── SKILL.md
│   └── schedule-task/
│       └── SKILL.md
└── agents/                  # (existing + new)
    ├── inbox-processor.md
    └── watcher-monitor.md

tests/
├── unit/
│   ├── test_approval_service.py
│   ├── test_planner_service.py
│   ├── test_scheduler_service.py
│   ├── test_whatsapp_watcher.py
│   └── test_linkedin_service.py
├── integration/
│   ├── test_approval_workflow.py
│   ├── test_plan_execution.py
│   └── test_scheduled_tasks.py
└── contract/
    └── test_gmail_mcp.py
```

**Structure Decision**: Extending the existing single-package structure established in Bronze tier. New functionality organized by domain (models, services, watchers, skills) following the established patterns.

## Vault Structure Extension

```text
AI_Employee_Vault/
├── Dashboard.md           # Extended with approval/plan status
├── Company_Handbook.md    # (existing)
├── Drop/                  # (existing)
├── Inbox/                 # (existing)
├── Needs_Action/
│   ├── Email/             # (existing)
│   └── WhatsApp/          # NEW: WhatsApp action items
├── Pending_Approval/      # NEW: Items awaiting human approval
├── Approved/              # NEW: User moves approved items here
├── Rejected/              # NEW: User moves rejected items here
├── Plans/                 # NEW: Active Plan.md files
├── Done/                  # Extended to include completed plans
├── Quarantine/            # (existing)
├── Logs/                  # (existing)
├── Social/
│   └── LinkedIn/
│       ├── posts/         # NEW: Scheduled and posted content
│       └── engagement.md  # NEW: Engagement metrics
├── Briefings/             # NEW: Daily briefings
└── Schedules/             # NEW: Schedule configurations
```

## Complexity Tracking

> No constitution violations requiring justification.

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Playwright for WhatsApp | Official WhatsApp Business API requires business verification; Playwright allows personal account monitoring | Twilio WhatsApp API (requires business account) |
| google_workspace_mcp | Existing well-maintained package (1,283 stars) vs custom MCP | Custom Email MCP (more work, same functionality) |
| File-based approval | Matches existing vault pattern, no new infrastructure | Database queue (over-engineering for single user) |

## Implementation Phases

### Phase 1: Approval Workflow (P1 - Foundation)
- FR-001 to FR-005: Approval request creation and monitoring
- Extend VaultConfig with new folder paths
- ApprovalRequest model and ApprovalService
- Approval folder watcher
- Dashboard integration

### Phase 2: WhatsApp Watcher (P2)
- FR-006 to FR-010: Playwright-based WhatsApp monitoring
- WhatsAppMessage model
- WhatsApp watcher with keyword detection
- Session persistence handling

### Phase 3: Gmail MCP Integration (P2)
- FR-011 to FR-015: google_workspace_mcp setup
- MCP configuration and OAuth flow
- Email draft/send through approval workflow

### Phase 4: Reasoning Loop & Planning (P2)
- FR-016 to FR-020: Plan.md generation
- Plan and PlanStep models
- PlannerService with step tracking
- Plan execution with approval integration

### Phase 5: LinkedIn Integration (P3)
- FR-021 to FR-025: LinkedIn API integration
- LinkedInPost and engagement models
- LinkedIn watcher for engagement
- Auto-posting with approval

### Phase 6: Scheduling (P3)
- FR-026 to FR-030: Cron-based scheduling
- ScheduledTask model and SchedulerService
- Missed schedule handling
- Timezone support

### Phase 7: Agent Skills (All Priorities)
- FR-031 to FR-035: Skill implementations
- SKILL.md manifests for Claude Code
- CLI commands for each skill

## Dependencies Graph

```
Bronze Tier (001)
       │
       ▼
┌─────────────────┐
│ Phase 1: Approval│ ◄── Foundation for all sensitive actions
└────────┬────────┘
         │
    ┌────┴────┬────────────┐
    ▼         ▼            ▼
Phase 2   Phase 3      Phase 4
WhatsApp  Gmail MCP    Planning
    │         │            │
    └────┬────┴────────────┘
         ▼
    Phase 5: LinkedIn
         │
         ▼
    Phase 6: Scheduling
         │
         ▼
    Phase 7: Skills
```

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| WhatsApp session expiration | Alert via Dashboard, session persistence, reconnection logic |
| LinkedIn rate limiting | Track API calls, queue posts, respect 25/day limit |
| OAuth token expiration | google_workspace_mcp handles refresh; add monitoring |
| Approval request expiration | Auto-reject with notification after 24h |
| Missed scheduled tasks | Configurable catch-up behavior (skip/run/queue) |
