# Tasks: Gold Tier - Autonomous Employee

**Input**: Design documents from `/specs/003-gold-ai-employee/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included per project testing requirements (80% coverage target)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US8)
- Include exact file paths in descriptions

## Path Conventions

- **Source**: `src/ai_employee/`
- **Tests**: `tests/`
- **Skills**: `.claude/skills/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Gold tier dependencies

- [ ] T001 Add Gold tier dependencies to pyproject.toml: odoorpc, facebook-sdk, tweepy, jinja2
- [ ] T002 [P] Create vault structure extension: /Active_Tasks/, /Accounting/, /Social/Meta/, /Social/Twitter/, /Archive/
- [ ] T003 [P] Create Business_Goals.md template in vault root
- [ ] T004 [P] Add Gold tier environment variables to .env.example
- [ ] T005 Extend src/ai_employee/config.py with Gold tier VaultConfig paths

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create base enum definitions in src/ai_employee/models/enums.py (TaskStatus, InvoiceStatus, PaymentStatus, PostStatus, HealthStatus, ErrorCategory)
- [ ] T007 [P] Create src/ai_employee/utils/retry.py with exponential backoff decorator (@with_retry)
- [ ] T008 [P] Create src/ai_employee/utils/correlation.py for generating and tracking correlation IDs
- [ ] T009 [P] Create src/ai_employee/utils/redaction.py for sensitive data redaction in logs
- [ ] T010 Create src/ai_employee/services/audit.py with AuditService base implementation (FR-047, FR-048)
- [ ] T011 [P] Create tests/unit/test_retry.py for retry decorator
- [ ] T012 [P] Create tests/unit/test_redaction.py for redaction utilities

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Ralph Wiggum Autonomous Loop (Priority: P1) 🎯 MVP

**Goal**: Enable multi-step autonomous task completion without constant human intervention

**Independent Test**: Trigger a multi-step task, observe iterations, verify completion or max-iteration halt

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Unit test for TaskState model in tests/unit/test_task_state.py
- [ ] T014 [P] [US1] Unit test for RalphWiggumService in tests/unit/test_ralph_wiggum.py
- [ ] T015 [US1] Integration test for Ralph loop flow in tests/integration/test_ralph_loop_flow.py

### Implementation for User Story 1

- [ ] T016 [US1] Create TaskState model in src/ai_employee/models/task_state.py (FR-002)
- [ ] T017 [US1] Create RalphWiggumService in src/ai_employee/services/ralph_wiggum.py (FR-001, FR-003, FR-004, FR-005, FR-006)
  - State file management in /Active_Tasks/
  - Prompt re-injection with context
  - Max iteration enforcement (default: 10)
  - Promise-based and file-movement completion strategies
  - Approval pause/resume support
- [ ] T018 [US1] Create Stop hook script in .claude/hooks/ralph-wiggum-stop.sh (FR-001)
- [ ] T019 [US1] Create /ralph-loop skill in .claude/skills/ralph-loop/SKILL.md (FR-007)
- [ ] T020 [US1] Add ralph-loop CLI command to src/ai_employee/cli/main.py
- [ ] T021 [US1] Integrate RalphWiggumService with existing ApprovalService for mid-loop approvals
- [ ] T022 [US1] Add Ralph Wiggum state section to Dashboard.md template

**Checkpoint**: Ralph Wiggum loop functional - can execute multi-step autonomous tasks

---

## Phase 4: User Story 2 - Odoo Community ERP Integration (Priority: P1)

**Goal**: Integrate with Odoo accounting for invoice and payment management

**Independent Test**: Create invoice via API, verify appears in Odoo, confirm transaction logged

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T023 [P] [US2] Unit test for OdooInvoice model in tests/unit/test_odoo_models.py
- [ ] T024 [P] [US2] Unit test for OdooPayment model in tests/unit/test_odoo_models.py
- [ ] T025 [P] [US2] Unit test for OdooService in tests/unit/test_odoo_service.py
- [ ] T026 [US2] Contract test for Odoo JSON-RPC in tests/contract/test_odoo_rpc.py (mock Odoo server)

### Implementation for User Story 2

- [ ] T027 [P] [US2] Create OdooInvoice model in src/ai_employee/models/odoo_models.py (FR-011)
- [ ] T028 [P] [US2] Create OdooPayment model in src/ai_employee/models/odoo_models.py
- [ ] T029 [P] [US2] Create LineItem embedded model in src/ai_employee/models/odoo_models.py
- [ ] T030 [US2] Create OdooService in src/ai_employee/services/odoo.py (FR-008, FR-009, FR-010, FR-012, FR-013, FR-014)
  - JSON-RPC connection via odoorpc
  - Authentication with database, username, API key
  - CRUD on res.partner, account.move, account.payment
  - Invoice creation with line items and taxes
  - Financial report retrieval (P&L, balance sheet, receivables)
  - Session caching
  - Operation queue for offline mode
- [ ] T031 [US2] Create Odoo MCP configuration in src/ai_employee/mcp/odoo_config.py
- [ ] T032 [US2] Create /odoo-invoice skill in .claude/skills/odoo-invoice/SKILL.md (FR-015)
- [ ] T033 [US2] Add odoo-test CLI command to src/ai_employee/cli/main.py
- [ ] T034 [US2] Add Accounting section to Dashboard.md template

**Checkpoint**: Odoo integration functional - can create invoices and query financials

---

## Phase 5: User Story 3 - Weekly Business Audit with CEO Briefing (Priority: P1)

**Goal**: Generate comprehensive weekly briefings with revenue, tasks, bottlenecks, and recommendations

**Independent Test**: Trigger audit, verify it reads from Odoo and tasks, produces formatted briefing

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T035 [P] [US3] Unit test for CEOBriefing model in tests/unit/test_briefing_model.py
- [ ] T036 [P] [US3] Unit test for BriefingService in tests/unit/test_briefing_service.py
- [ ] T037 [US3] Integration test for briefing generation in tests/integration/test_briefing_generation.py

### Implementation for User Story 3

- [ ] T038 [US3] Create CEOBriefing model in src/ai_employee/models/briefing.py (includes CompletedTask, Bottleneck, CostSuggestion, Deadline embedded models)
- [ ] T039 [US3] Create SocialSummary model in src/ai_employee/models/briefing.py
- [ ] T040 [US3] Create AuditSummary model in src/ai_employee/models/briefing.py
- [ ] T041 [US3] Create BriefingService in src/ai_employee/services/briefing.py (FR-016, FR-017, FR-018, FR-019, FR-020, FR-021)
  - Schedule weekly audit (Sunday 9:00 PM)
  - Aggregate from Odoo (financials), /Done (tasks), /Logs (activities)
  - Generate sections: Executive Summary, Revenue, Tasks, Bottlenecks, Suggestions
  - Identify unused subscriptions (30+ days no activity)
  - Calculate task bottlenecks (expected vs actual completion)
  - Write to /Briefings/ with date-stamped filenames
- [ ] T042 [US3] Create Jinja2 briefing template in src/ai_employee/templates/ceo_briefing.md.j2
- [ ] T043 [US3] Create /generate-briefing skill in .claude/skills/generate-briefing/SKILL.md (FR-022)
- [ ] T044 [US3] Create business-auditor agent in .claude/agents/business-auditor.md
- [ ] T045 [US3] Add scheduled task for weekly briefing to SchedulerService
- [ ] T046 [US3] Add briefing generation CLI command to src/ai_employee/cli/main.py

**Checkpoint**: CEO Briefing functional - can generate weekly business summaries

---

## Phase 6: User Story 6 - Comprehensive Error Recovery (Priority: P2)

**Goal**: Handle errors gracefully with automatic recovery and graceful degradation

**Independent Test**: Simulate failures, verify retry, recovery, and degraded operation

### Tests for User Story 6

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T047 [P] [US6] Unit test for ServiceHealth model in tests/unit/test_service_health.py
- [ ] T048 [P] [US6] Unit test for ErrorRecoveryService in tests/unit/test_error_recovery.py
- [ ] T049 [P] [US6] Unit test for WatchdogService in tests/unit/test_watchdog.py

### Implementation for User Story 6

- [ ] T050 [US6] Create ServiceHealth model in src/ai_employee/models/service_health.py
- [ ] T051 [US6] Create ErrorRecoveryService in src/ai_employee/services/error_recovery.py (FR-036, FR-037, FR-038, FR-040, FR-041, FR-042)
  - Exponential backoff retry (base: 1s, max: 60s, attempts: 3)
  - Error classification (transient, authentication, logic, data, system)
  - Degraded functionality mode
  - Failed operation queue for retry
  - Dashboard alerts for degraded components
  - Health checks every 5 minutes
- [ ] T052 [US6] Create WatchdogService in src/ai_employee/services/watchdog.py (FR-039)
  - Monitor all registered watchers
  - Auto-restart crashed watchers within 60 seconds
  - Track restart counts and failure patterns
- [ ] T053 [US6] Add watchdog CLI command to src/ai_employee/cli/main.py
- [ ] T054 [US6] Extend Dashboard.md with Service Health section
- [ ] T055 [US6] Integrate ErrorRecoveryService with existing services (Gmail, LinkedIn, WhatsApp watchers)

**Checkpoint**: Error recovery functional - system survives component failures

---

## Phase 7: User Story 4 - Facebook/Instagram Social Media Integration (Priority: P2)

**Goal**: Manage Facebook and Instagram business pages with scheduled posting and engagement monitoring

**Independent Test**: Schedule post, approve, verify appears on platform, confirm metrics captured

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T056 [P] [US4] Unit test for MetaPost model in tests/unit/test_meta_post.py
- [ ] T057 [P] [US4] Unit test for MetaService in tests/unit/test_meta_service.py
- [ ] T058 [US4] Contract test for Meta Graph API in tests/contract/test_meta_api.py (mock API)

### Implementation for User Story 4

- [ ] T059 [US4] Create MetaPost model in src/ai_employee/models/meta_post.py (includes MetaEngagement embedded)
- [ ] T060 [US4] Create MetaService in src/ai_employee/services/meta.py (FR-023, FR-024, FR-025, FR-026, FR-027, FR-028)
  - Meta Graph API integration
  - Post scheduling with images, videos, text
  - Engagement monitoring (likes, comments, shares, reach)
  - Business keyword detection in comments
  - Rate limiting (200 calls/user/hour)
  - Store in /Social/Meta/
- [ ] T061 [US4] Create Meta engagement watcher in src/ai_employee/watchers/meta.py
- [ ] T062 [US4] Create /post-facebook skill in .claude/skills/post-facebook/SKILL.md (FR-029)
- [ ] T063 [US4] Create /post-instagram skill in .claude/skills/post-instagram/SKILL.md (FR-029)
- [ ] T064 [US4] Add meta-test CLI command to src/ai_employee/cli/main.py
- [ ] T065 [US4] Add watch-meta CLI command to src/ai_employee/cli/main.py
- [ ] T066 [US4] Integrate MetaService with ApprovalService for post approval workflow

**Checkpoint**: Meta integration functional - can post to Facebook/Instagram with approval

---

## Phase 8: User Story 5 - Twitter/X Social Media Integration (Priority: P2)

**Goal**: Manage Twitter/X presence with scheduled posting and engagement monitoring

**Independent Test**: Schedule tweet, approve, verify appears on Twitter, confirm engagement tracked

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T067 [P] [US5] Unit test for Tweet model in tests/unit/test_tweet.py
- [ ] T068 [P] [US5] Unit test for TwitterService in tests/unit/test_twitter_service.py
- [ ] T069 [US5] Contract test for Twitter API v2 in tests/contract/test_twitter_api.py (mock API)

### Implementation for User Story 5

- [ ] T070 [US5] Create Tweet model in src/ai_employee/models/tweet.py (includes TweetEngagement embedded)
- [ ] T071 [US5] Create TwitterService in src/ai_employee/services/twitter.py (FR-030, FR-031, FR-032, FR-033, FR-034)
  - Twitter API v2 integration via tweepy
  - Tweet scheduling, threads, media attachments
  - Monitor mentions, replies, DMs for keywords
  - Rate limit handling (varies by endpoint)
  - Store in /Social/Twitter/
- [ ] T072 [US5] Create Twitter mention watcher in src/ai_employee/watchers/twitter.py
- [ ] T073 [US5] Create /post-twitter skill in .claude/skills/post-twitter/SKILL.md (FR-035)
- [ ] T074 [US5] Add twitter-test CLI command to src/ai_employee/cli/main.py
- [ ] T075 [US5] Add watch-twitter CLI command to src/ai_employee/cli/main.py
- [ ] T076 [US5] Integrate TwitterService with ApprovalService for tweet approval workflow

**Checkpoint**: Twitter integration functional - can post tweets with approval

---

## Phase 9: User Story 7 - Full Cross-Domain Integration (Priority: P2)

**Goal**: Seamlessly manage both personal and business affairs with unified context

**Independent Test**: Trigger cross-domain action (WhatsApp → Odoo invoice), verify correlation maintained

### Tests for User Story 7

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T077 [P] [US7] Unit test for CrossDomainService in tests/unit/test_cross_domain.py
- [ ] T078 [US7] Integration test for cross-domain flow in tests/integration/test_cross_domain.py

### Implementation for User Story 7

- [ ] T079 [US7] Create CrossDomainService in src/ai_employee/services/cross_domain.py (FR-043, FR-044, FR-045, FR-046)
  - Correlation ID linking across domains
  - Context propagation between services
  - Unified search across vaults and data sources
  - Relationship graph for briefing
- [ ] T080 [US7] Extend existing services (WhatsApp, Email, LinkedIn) with correlation ID support
- [ ] T081 [US7] Add cross-domain relationships to Dashboard.md
- [ ] T082 [US7] Integrate CrossDomainService with BriefingService for relationship reporting

**Checkpoint**: Cross-domain integration functional - unified handling of personal and business

---

## Phase 10: User Story 8 - Enhanced Audit Logging (Priority: P3)

**Goal**: Comprehensive audit logs for accountability, compliance, and debugging

**Independent Test**: Trigger actions, verify logged with complete metadata, query logs

### Tests for User Story 8

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T083 [P] [US8] Unit test for AuditEntry model in tests/unit/test_audit_entry.py
- [ ] T084 [P] [US8] Unit test for AuditService in tests/unit/test_audit_service.py

### Implementation for User Story 8

- [ ] T085 [US8] Create AuditEntry model in src/ai_employee/models/audit_entry.py
- [ ] T086 [US8] Extend AuditService in src/ai_employee/services/audit.py (FR-049, FR-050, FR-051, FR-052)
  - 90-day retention (configurable)
  - Query by date range, action type, actor
  - Archive and compress old logs
  - Include audit summary in briefings
- [ ] T087 [US8] Create log rotation and archival in src/ai_employee/services/audit.py
- [ ] T088 [US8] Integrate AuditService with all Gold tier services (Ralph, Odoo, Meta, Twitter)
- [ ] T089 [US8] Add audit-query CLI command to src/ai_employee/cli/main.py
- [ ] T090 [US8] Add audit section to CEO Briefing template

**Checkpoint**: Audit logging functional - all actions tracked with complete metadata

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T091 [P] Update CLAUDE.md with Gold tier agent context
- [ ] T092 [P] Update README.md with Gold tier features and setup
- [ ] T093 Run quickstart.md validation (verify all steps work)
- [ ] T094 Code cleanup and refactoring across all Gold tier services
- [ ] T095 [P] Add type hints validation with mypy
- [ ] T096 [P] Run ruff linter and fix issues
- [ ] T097 Verify 80% test coverage target with pytest-cov
- [ ] T098 Performance testing for CEO Briefing (< 5 minutes target)
- [ ] T099 Security review: credential handling, API key storage, log redaction
- [ ] T100 Integration testing: run all watchers simultaneously
- [ ] T101 Update vault init script for Gold tier folders

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **US1 Ralph Wiggum (Phase 3)**: Foundation complete - MVP, blocks others conceptually
- **US2 Odoo (Phase 4)**: Foundation complete, can run parallel with US1
- **US3 CEO Briefing (Phase 5)**: Depends on US2 (Odoo) for financial data
- **US6 Error Recovery (Phase 6)**: Can start after Foundation, enhances all services
- **US4 Meta (Phase 7)**: Depends on US6 (error recovery) for reliability
- **US5 Twitter (Phase 8)**: Depends on US6 (error recovery) for reliability
- **US7 Cross-Domain (Phase 9)**: Depends on US2, US4, US5 being functional
- **US8 Audit Logging (Phase 10)**: Can run parallel, integrates with all services
- **Polish (Phase 11)**: Depends on all user stories complete

### User Story Dependencies Graph

```
Foundation (Phase 2)
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
US1 Ralph Wiggum (P1)           US2 Odoo (P1)
       │                                 │
       │                                 ▼
       │                        US3 CEO Briefing (P1)
       │                                 │
       └────────────┬────────────────────┘
                    ▼
           US6 Error Recovery (P2)
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
   US4 Meta (P2)         US5 Twitter (P2)
         │                     │
         └──────────┬──────────┘
                    ▼
        US7 Cross-Domain (P2)
                    │
                    ▼
         US8 Audit Logging (P3)
                    │
                    ▼
           Polish (Phase 11)
```

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before skills
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- US1 and US2 can run in parallel after Foundation
- US4 and US5 can run in parallel after US6
- All tests marked [P] can run in parallel within a story
- Models marked [P] can run in parallel within a story

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: US1 Ralph Wiggum
4. Complete Phase 4: US2 Odoo
5. Complete Phase 5: US3 CEO Briefing
6. **STOP and VALIDATE**: Test all P1 stories independently
7. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 Ralph Wiggum → Test independently → Demo (autonomous task execution!)
3. Add US2 Odoo → Test independently → Demo (invoice creation!)
4. Add US3 CEO Briefing → Test independently → Demo (weekly briefings!)
5. Add US6 Error Recovery → System becomes production-ready
6. Add US4/US5 Social Media → Expanded platform coverage
7. Add US7 Cross-Domain → Unified experience
8. Add US8 Audit Logging → Complete audit trail

---

## Task Count Summary

| Phase | Story | Tasks | Priority |
|-------|-------|-------|----------|
| 1 | Setup | 5 | - |
| 2 | Foundation | 7 | - |
| 3 | US1 Ralph Wiggum | 10 | P1 |
| 4 | US2 Odoo | 12 | P1 |
| 5 | US3 CEO Briefing | 12 | P1 |
| 6 | US6 Error Recovery | 9 | P2 |
| 7 | US4 Meta | 11 | P2 |
| 8 | US5 Twitter | 10 | P2 |
| 9 | US7 Cross-Domain | 6 | P2 |
| 10 | US8 Audit Logging | 8 | P3 |
| 11 | Polish | 11 | - |
| **Total** | | **101** | |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
