# Implementation Plan: Gold Tier - Autonomous Employee

**Branch**: `003-gold-ai-employee` | **Date**: 2026-02-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-gold-ai-employee/spec.md`

## Summary

Transform the Silver tier AI Employee into a truly autonomous digital employee with Odoo ERP integration for accounting, expanded social media coverage (Facebook, Instagram, Twitter/X), the Ralph Wiggum autonomous execution loop for multi-step task completion, weekly CEO briefings, comprehensive error recovery with graceful degradation, and production-grade audit logging.

## Technical Context

**Language/Version**: Python 3.13+ (matching Bronze/Silver tiers)
**Primary Dependencies**:
- Existing: watchdog, pyyaml, google-auth, playwright, linkedin-api-client, workspace-mcp, apscheduler
- New: odoo-rpc (Odoo JSON-RPC client), tweepy (Twitter/X API v2), facebook-sdk (Meta Graph API)
**Storage**: File-based (Obsidian vault markdown files) + Odoo ERP (external)
**Testing**: pytest, pytest-cov (80% target), mypy for type checking
**Target Platform**: macOS/Linux (local machine with persistent browser sessions)
**Project Type**: Single Python package (extending src/ai_employee)
**Performance Goals**:
- Odoo operations within 30 seconds
- CEO Briefing generation within 5 minutes
- Watchdog restart within 60 seconds
- Social media posts within 5 minutes of schedule
**Constraints**:
- Ralph Wiggum loop max 10 iterations (configurable)
- Meta rate limits (200 calls/user/hour)
- Twitter rate limits vary by endpoint
- 95% system uptime even with component failures
**Scale/Scope**: Single user, personal automation, 90-day log retention

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Since no project-specific constitution is defined, applying general best practices:

| Principle | Status | Notes |
|-----------|--------|-------|
| Library-First | ✅ PASS | Each feature (Odoo, social media, Ralph loop, briefing) implemented as independent service |
| Test-First (TDD) | ✅ PASS | Will follow TDD workflow per user's rules |
| Simplicity | ✅ PASS | File-based workflow, external Odoo for accounting only |
| Security | ✅ PASS | Credentials via .env, sensitive data redacted in logs |
| Error Handling | ✅ PASS | Comprehensive error recovery with graceful degradation |

**No violations requiring justification.**

## Project Structure

### Documentation (this feature)

```text
specs/003-gold-ai-employee/
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
│   └── main.py                  # Extended with new commands
├── config.py                    # Extended VaultConfig for new folders
├── models/
│   ├── (existing Silver models)
│   ├── task_state.py           # NEW: Ralph Wiggum task state
│   ├── odoo_models.py          # NEW: OdooInvoice, OdooPayment
│   ├── briefing.py             # NEW: CEOBriefing model
│   ├── meta_post.py            # NEW: MetaPost (FB/IG) model
│   ├── tweet.py                # NEW: Tweet model
│   ├── audit_entry.py          # NEW: AuditEntry model
│   └── service_health.py       # NEW: ServiceHealth model
├── services/
│   ├── (existing Silver services)
│   ├── ralph_wiggum.py         # NEW: Ralph Wiggum autonomous loop
│   ├── odoo.py                 # NEW: Odoo ERP integration
│   ├── briefing.py             # NEW: CEO Briefing generation
│   ├── meta.py                 # NEW: Facebook/Instagram service
│   ├── twitter.py              # NEW: Twitter/X service
│   ├── error_recovery.py       # NEW: Error recovery and retry logic
│   ├── watchdog.py             # NEW: Process watchdog
│   ├── audit.py                # NEW: Audit logging service
│   └── cross_domain.py         # NEW: Cross-domain integration
├── utils/
│   ├── (existing utils)
│   └── retry.py                # NEW: Exponential backoff decorator
├── watchers/
│   ├── (existing Silver watchers)
│   ├── meta.py                 # NEW: Facebook/Instagram engagement watcher
│   └── twitter.py              # NEW: Twitter/X mention watcher
├── mcp/
│   ├── gmail_config.py         # (existing)
│   └── odoo_config.py          # NEW: Odoo MCP configuration
├── hooks/
│   └── ralph_stop_hook.py      # NEW: Claude Code Stop hook for Ralph loop
└── skills/
    ├── (existing Silver skills)
    ├── ralph_loop.py           # NEW: /ralph-loop skill
    ├── odoo_invoice.py         # NEW: /odoo-invoice skill
    ├── generate_briefing.py    # NEW: /generate-briefing skill
    ├── post_facebook.py        # NEW: /post-facebook skill
    ├── post_instagram.py       # NEW: /post-instagram skill
    └── post_twitter.py         # NEW: /post-twitter skill

.claude/
├── skills/
│   ├── (existing Silver skills)
│   ├── ralph-loop/
│   │   └── SKILL.md
│   ├── odoo-invoice/
│   │   └── SKILL.md
│   ├── generate-briefing/
│   │   └── SKILL.md
│   ├── post-facebook/
│   │   └── SKILL.md
│   ├── post-instagram/
│   │   └── SKILL.md
│   └── post-twitter/
│       └── SKILL.md
├── hooks/
│   └── ralph-wiggum-stop.sh    # NEW: Stop hook script
└── agents/
    ├── (existing agents)
    └── business-auditor.md     # NEW: CEO Briefing agent

tests/
├── unit/
│   ├── test_ralph_wiggum.py
│   ├── test_odoo_service.py
│   ├── test_briefing_service.py
│   ├── test_meta_service.py
│   ├── test_twitter_service.py
│   ├── test_error_recovery.py
│   ├── test_watchdog.py
│   └── test_audit_service.py
├── integration/
│   ├── test_ralph_loop_flow.py
│   ├── test_cross_domain.py
│   └── test_briefing_generation.py
└── contract/
    ├── test_odoo_rpc.py
    ├── test_meta_api.py
    └── test_twitter_api.py
```

**Structure Decision**: Extending the existing single-package structure established in Bronze/Silver tiers. New functionality organized by domain (models, services, watchers, skills, hooks) following the established patterns.

## Vault Structure Extension

```text
AI_Employee_Vault/
├── Dashboard.md              # Extended with service health status
├── Company_Handbook.md       # (existing)
├── Business_Goals.md         # NEW: Business objectives for briefing
├── Drop/                     # (existing)
├── Inbox/                    # (existing)
├── Needs_Action/
│   ├── Email/                # (existing)
│   ├── WhatsApp/             # (existing)
│   ├── LinkedIn/             # (existing)
│   ├── Facebook/             # NEW: Facebook engagement items
│   ├── Twitter/              # NEW: Twitter engagement items
│   └── Odoo/                 # NEW: Odoo action items
├── Active_Tasks/             # NEW: Ralph Wiggum active task states
├── Pending_Approval/         # (existing)
├── Approved/                 # (existing)
├── Rejected/                 # (existing)
├── Plans/                    # (existing)
├── Done/                     # Extended with correlation IDs
├── Quarantine/               # (existing)
├── Logs/
│   ├── (existing logs)
│   ├── audit_YYYY-MM-DD.jsonl  # NEW: Structured audit logs
│   └── health_YYYY-MM-DD.log   # NEW: Service health logs
├── Social/
│   ├── LinkedIn/             # (existing)
│   ├── Meta/                 # NEW: Facebook/Instagram
│   │   ├── posts/
│   │   └── engagement.md
│   └── Twitter/              # NEW: Twitter/X
│       ├── tweets/
│       └── engagement.md
├── Briefings/                # Extended with CEO briefings
│   └── YYYY-MM-DD_Monday_Briefing.md
├── Schedules/                # (existing)
├── Accounting/               # NEW: Financial data from Odoo
│   ├── Current_Month.md
│   └── transactions/
└── Archive/                  # NEW: Compressed old logs
```

## Complexity Tracking

> No constitution violations requiring justification.

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Odoo JSON-RPC | Official external API, no special access needed | Direct database (security risk, maintenance burden) |
| Separate Meta/Twitter services | Different APIs, rate limits, authentication | Unified social service (would be too complex) |
| File-based task state | Matches existing vault pattern, survives crashes | In-memory state (lost on restart) |
| SQLite for audit archival | Efficient querying, compression support | JSON files (harder to query at scale) |

## Implementation Phases

### Phase 1: Ralph Wiggum Loop (P1 - Foundation)
- FR-001 to FR-007: Stop hook, state management, iteration control
- TaskState model
- RalphWiggumService with completion strategies
- Stop hook script for Claude Code
- /ralph-loop skill

### Phase 2: Odoo ERP Integration (P1)
- FR-008 to FR-015: JSON-RPC connection, CRUD operations
- OdooInvoice, OdooPayment models
- OdooService with connection pooling
- Operation queue for offline handling
- /odoo-invoice skill

### Phase 3: CEO Briefing (P1)
- FR-016 to FR-022: Audit scheduling, data aggregation, report generation
- CEOBriefing model
- BriefingService with analysis logic
- Subscription audit patterns
- /generate-briefing skill

### Phase 4: Error Recovery & Watchdog (P2)
- FR-036 to FR-042: Retry logic, error classification, watchdog
- ServiceHealth model
- ErrorRecoveryService with exponential backoff
- WatchdogService for process monitoring
- Dashboard health integration

### Phase 5: Meta Integration (P2)
- FR-023 to FR-029: Graph API, posting, engagement monitoring
- MetaPost model
- MetaService with rate limiting
- Meta engagement watcher
- /post-facebook and /post-instagram skills

### Phase 6: Twitter/X Integration (P2)
- FR-030 to FR-035: API v2, posting, monitoring
- Tweet model
- TwitterService with rate limiting
- Twitter mention watcher
- /post-twitter skill

### Phase 7: Cross-Domain Integration (P2)
- FR-043 to FR-046: Correlation IDs, context propagation, unified search
- CrossDomainService
- Relationship graph for briefing
- Updated Dashboard with cross-references

### Phase 8: Audit Logging (P3)
- FR-047 to FR-052: Structured logging, redaction, archival
- AuditEntry model
- AuditService with query support
- Log rotation and archival
- Briefing audit summary

### Phase 9: Agent Skills (All Priorities)
- All skill implementations
- SKILL.md manifests for Claude Code
- CLI commands for each skill
- business-auditor agent

## Dependencies Graph

```
Silver Tier (002)
       │
       ▼
┌─────────────────────┐
│ Phase 1: Ralph Loop │ ◄── Foundation for autonomous execution
└─────────┬───────────┘
          │
     ┌────┴────┐
     ▼         ▼
Phase 2     Phase 4
Odoo ERP    Error Recovery
     │         │
     └────┬────┘
          ▼
   Phase 3: CEO Briefing
          │
     ┌────┴────────────┐
     ▼                 ▼
Phase 5            Phase 6
Meta Integration   Twitter Integration
     │                 │
     └────────┬────────┘
              ▼
     Phase 7: Cross-Domain
              │
              ▼
     Phase 8: Audit Logging
              │
              ▼
     Phase 9: Skills
```

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Ralph Wiggum infinite loop | Max iteration limit (10), timeout per iteration |
| Odoo API changes | Version pinning (Odoo 19+), API compatibility layer |
| Meta rate limiting | Rate tracker, queue with backoff, respect 200/hour limit |
| Twitter API access revoked | Graceful degradation, feature flags, user notification |
| CEO Briefing data inconsistency | Atomic reads from Odoo, transaction logging |
| Watchdog missing failures | Health heartbeats every 60s, cascading alerts |
| Audit log disk space | 90-day retention, compression, archival to SQLite |
| Cross-domain correlation loss | Immutable correlation IDs, graph persistence |

## New Skills Summary

| Skill | Priority | Description |
|-------|----------|-------------|
| /ralph-loop | P1 | Start autonomous multi-step task execution |
| /odoo-invoice | P1 | Create invoice in Odoo via natural language |
| /generate-briefing | P1 | On-demand CEO briefing generation |
| /post-facebook | P2 | Schedule Facebook post with approval |
| /post-instagram | P2 | Schedule Instagram post with approval |
| /post-twitter | P2 | Schedule tweet with approval |

## Environment Variables (New)

```bash
# Odoo ERP
ODOO_URL=http://localhost:8069
ODOO_DB=company_db
ODOO_USER=admin
ODOO_API_KEY=your_odoo_api_key

# Meta Graph API
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_ACCESS_TOKEN=your_long_lived_token
META_PAGE_ID=your_page_id

# Twitter/X API v2
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret
TWITTER_BEARER_TOKEN=your_bearer_token
```
