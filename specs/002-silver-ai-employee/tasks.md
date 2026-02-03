# Tasks: Silver Tier - Functional Assistant

**Input**: Design documents from `/specs/002-silver-ai-employee/`
**Prerequisites**: plan.md (✅), spec.md (✅), research.md (✅), data-model.md (✅), contracts/ (✅)

**Tests**: Tests included as specified in project requirements (80% coverage target).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and vault structure extension

- [x] T001 Add new dependencies to pyproject.toml (playwright, linkedin-api-client, apscheduler, workspace-mcp)
- [x] T002 [P] Extend VaultConfig in src/ai_employee/config.py with new folder paths (Pending_Approval, Approved, Rejected, Plans, Social/LinkedIn, Briefings, Schedules)
- [x] T003 [P] Create vault initialization script extension in scripts/init_vault_silver.sh for new folders
- [x] T004 Run `uv sync` to install new dependencies

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Models (All Can Run in Parallel)

- [x] T005 [P] Create ApprovalCategory and ApprovalStatus enums in src/ai_employee/models/approval_request.py
- [x] T006 [P] Create ApprovalRequest dataclass in src/ai_employee/models/approval_request.py
- [x] T007 [P] Create PlanStatus and StepStatus enums in src/ai_employee/models/plan.py
- [x] T008 [P] Create Plan and PlanStep dataclasses in src/ai_employee/models/plan.py
- [x] T009 [P] Create WhatsAppActionStatus enum and WhatsAppMessage dataclass in src/ai_employee/models/whatsapp_message.py
- [x] T010 [P] Create LinkedInPostStatus enum and LinkedInPost dataclass in src/ai_employee/models/linkedin_post.py
- [x] T011 [P] Create EngagementType enum and LinkedInEngagement dataclass in src/ai_employee/models/linkedin_post.py
- [x] T012 [P] Create MissedStrategy enum and ScheduledTask dataclass in src/ai_employee/models/scheduled_task.py
- [x] T013 [P] Extend ActionItemType enum in src/ai_employee/models/action_item.py with WHATSAPP, LINKEDIN, SCHEDULED
- [x] T014 [P] Extend SourceType enum in src/ai_employee/models/watcher_event.py with WHATSAPP, LINKEDIN, SCHEDULER

### Model Tests

- [x] T015 [P] Unit tests for ApprovalRequest validation in tests/unit/test_approval_request.py
- [x] T016 [P] Unit tests for Plan and PlanStep validation in tests/unit/test_plan.py
- [x] T017 [P] Unit tests for WhatsAppMessage validation in tests/unit/test_whatsapp_message.py
- [x] T018 [P] Unit tests for LinkedInPost/LinkedInEngagement validation in tests/unit/test_linkedin_post.py
- [x] T019 [P] Unit tests for ScheduledTask validation in tests/unit/test_scheduled_task.py

**Checkpoint**: Foundation ready - all models tested. User story implementation can now begin.

---

## Phase 3: User Story 1 - Human-in-the-Loop Approval Workflow (Priority: P1) MVP

**Goal**: Enable sensitive actions to require explicit human approval before execution via file-based workflow

**Independent Test**: Trigger action requiring approval → verify file appears in /Pending_Approval → move to /Approved → confirm action executes

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T020 [P] [US1] Unit tests for ApprovalService in tests/unit/test_approval_service.py
- [x] T021 [P] [US1] Integration tests for approval workflow in tests/integration/test_approval_workflow.py

### Implementation for User Story 1

- [x] T022 [US1] Create ApprovalService in src/ai_employee/services/approval.py with create_request(), approve(), reject(), check_expired() methods (FR-001, FR-002, FR-003)
- [x] T023 [US1] Implement approval file serialization/deserialization with YAML frontmatter in ApprovalService
- [x] T024 [US1] Create ApprovalWatcher in src/ai_employee/watchers/approval.py to monitor /Approved/ and /Rejected/ folders (FR-002, FR-003)
- [x] T025 [US1] Implement expiration check and auto-reject logic in ApprovalService (FR-004, FR-004a)
- [x] T026 [US1] Implement sequential processing queue for concurrent approvals (FR-004b)
- [x] T027 [US1] Add approval category validation for email, social_post, payment, file_operation, custom (FR-005)
- [x] T028 [US1] Extend Dashboard service in src/ai_employee/services/dashboard.py to show pending approvals count and stale warnings
- [x] T029 [US1] Add CLI command `ai-employee watch-approvals` in src/ai_employee/cli/main.py
- [x] T030 [US1] Update /approve-action skill script in .claude/skills/approve-action/scripts/manage_approvals.py to integrate with ApprovalService

**Checkpoint**: User Story 1 fully functional - approvals can be created, monitored, approved/rejected, and expired items handled

---

## Phase 4: User Story 2 - WhatsApp Message Monitoring (Priority: P2)

**Goal**: Monitor WhatsApp messages for urgent business communications using Playwright browser automation

**Independent Test**: Send WhatsApp message with urgent keyword → verify action item appears in /Needs_Action/WhatsApp → confirm Dashboard reflects new item

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T031 [P] [US2] Unit tests for WhatsApp message parsing in tests/unit/test_whatsapp_watcher.py
- [x] T032 [P] [US2] Unit tests for keyword detection in tests/unit/test_whatsapp_watcher.py

### Implementation for User Story 2

- [x] T033 [US2] Create WhatsAppWatcher base structure in src/ai_employee/watchers/whatsapp.py (FR-006)
- [x] T034 [US2] Implement Playwright browser automation for WhatsApp Web in WhatsAppWatcher
- [x] T035 [US2] Implement keyword filtering with configurable keyword list (default: urgent, asap, invoice, payment, help, pricing) (FR-007)
- [x] T036 [US2] Implement action file creation with sender info, content, timestamp, matched keywords (FR-008)
- [x] T037 [US2] Implement session expiration detection and Dashboard alerting (FR-009)
- [x] T038 [US2] Implement persistent browser session storage to avoid repeated QR scans (FR-010)
- [x] T039 [US2] Add CLI command `ai-employee watch-whatsapp` in src/ai_employee/cli/main.py
- [x] T040 [US2] Extend Dashboard to show WhatsApp watcher status (connected/disconnected/session_expired)
- [x] T040a [US2] Implement heartbeat logging (60s interval) for WhatsApp watcher uptime tracking (SC-007)

**Checkpoint**: User Story 2 fully functional - WhatsApp messages monitored and urgent ones filed as action items

---

## Phase 5: User Story 3 - Gmail Integration via Google Workspace MCP (Priority: P2)

**Goal**: Draft and send emails on user's behalf with approval workflow, using google_workspace_mcp package

**Independent Test**: Request email draft → verify draft appears for approval → approve → confirm email sent via Gmail

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T041 [P] [US3] Unit tests for EmailService in tests/unit/test_email_service.py (25 tests covering draft, send, approval integration, errors)
- [x] T041b [P] [US3] Unit tests for Gmail MCP configuration in tests/unit/test_gmail_mcp.py (32 tests covering OAuthToken, GmailMCPConfig, GmailMCPClient)
- [ ] T042 [P] [US3] Contract tests for Gmail MCP integration in tests/contract/test_gmail_mcp.py

### Implementation for User Story 3

- [x] T043 [US3] Create Gmail MCP configuration module in src/ai_employee/mcp/gmail_config.py (FR-011)
- [x] T044 [US3] Configure OAuth 2.0 credentials loading for Gmail API access (OAuthToken, GmailMCPConfig) (FR-012)
- [x] T045 [US3] Create EmailService in src/ai_employee/services/email.py with draft_email(), send_approved_email() methods
- [x] T045a [US3] Integrate EmailService with ApprovalService for draft-then-approve workflow
- [ ] T046 [US3] Implement email send via google_workspace_mcp after approval (TODO placeholder in _send_via_mcp)
- [x] T047 [US3] Add attachment support with validation (validate_attachments flag) (FR-013)
- [x] T048 [US3] Implement operation logging with timestamps and outcomes in EmailService (_log_operation) (FR-014)
- [x] T048a [US3] Implement partial email send failure handling: PartialSendError with failed_recipients, quarantine on failure (FR-014a)
- [x] T049 [US3] Implement OAuth token refresh handling in GmailMCPClient (_refresh_token stub) (FR-015)
- [x] T050 [US3] Update /send-email skill script to integrate with EmailService

**Checkpoint**: User Story 3 fully functional - emails drafted, approved, and sent via Gmail

---

## Phase 6: User Story 4 - Claude Reasoning Loop with Plan.md (Priority: P2)

**Goal**: Break down complex tasks into step-by-step Plan.md files for transparency and approval integration

**Independent Test**: Request multi-step task → verify Plan.md created with clear steps → confirm each step can be tracked

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T051 [P] [US4] Unit tests for PlannerService in tests/unit/test_planner_service.py (22 tests)
- [ ] T052 [P] [US4] Integration tests for plan execution in tests/integration/test_plan_execution.py

### Implementation for User Story 4

- [x] T053 [US4] Create PlannerService in src/ai_employee/services/planner.py with analyze_task(), create_plan() methods (FR-016)
- [x] T054 [US4] Implement Plan.md file generation with objective, numbered steps, dependencies, approval requirements, success criteria - ensure plain language per SC-010 (no code blocks, verb-first steps, progress symbols) (FR-017)
- [x] T055 [US4] Implement plan execution status tracking (pending, in_progress, completed, failed, paused) (FR-018)
- [x] T056 [US4] Implement plan pause on approval required or step failure (FR-019)
- [x] T056a [US4] Implement plan file reference validation: check paths before step execution, pause and alert on missing references (FR-019a)
- [x] T057 [US4] Integrate PlannerService with ApprovalService for steps requiring approval
- [x] T058 [US4] Update Dashboard to show active plan status (active_plan_count, active_plan_name, active_plan_progress) (FR-020)
- [x] T059 [US4] Implement plan completion with move to /Done/ and completion summary
- [ ] T060 [US4] Update /create-plan skill SKILL.md in .claude/skills/create-plan/SKILL.md with examples

**Checkpoint**: User Story 4 fully functional - complex tasks broken down into transparent, trackable plans

---

## Phase 7: User Story 5 - LinkedIn Monitoring and Auto-Posting (Priority: P3)

**Goal**: Schedule LinkedIn posts with approval and monitor engagement for sales lead generation

**Independent Test**: Schedule LinkedIn post → approve → verify post appears on LinkedIn → check engagement metrics captured

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T061 [P] [US5] Unit tests for LinkedInService in tests/unit/test_linkedin_service.py
- [ ] T062 [P] [US5] Unit tests for engagement keyword detection in tests/unit/test_linkedin_service.py

### Implementation for User Story 5

- [ ] T063 [US5] Create LinkedInService in src/ai_employee/services/linkedin.py with schedule_post(), post(), get_engagement() methods (FR-021)
- [ ] T064 [US5] Implement LinkedIn API authentication using linkedin-api-client (official API)
- [ ] T065 [US5] Implement post scheduling with approval request creation
- [ ] T066 [US5] Create LinkedInEngagementWatcher in src/ai_employee/watchers/linkedin.py for engagement monitoring (FR-022)
- [ ] T067 [US5] Implement keyword detection for business-relevant comments (inquiry, interested, pricing, contact, demo) (FR-023)
- [ ] T068 [US5] Implement action item creation for high-priority LinkedIn interactions (FR-024)
- [ ] T069 [US5] Implement rate limiting (max 25 posts/day) with tracking (FR-025)
- [ ] T070 [US5] Create engagement log in /Social/LinkedIn/engagement.md
- [ ] T070a [US5] Implement heartbeat logging (60s interval) for LinkedIn watcher uptime tracking (SC-007)
- [ ] T071 [US5] Update /post-linkedin skill script in .claude/skills/post-linkedin/scripts/create_post.py to integrate with LinkedInService

**Checkpoint**: User Story 5 fully functional - LinkedIn posts scheduled, approved, posted, and engagement tracked

---

## Phase 8: User Story 6 - Scheduled Tasks via Cron (Priority: P3)

**Goal**: Run routine tasks automatically on a schedule using APScheduler

**Independent Test**: Configure scheduled task → wait for schedule trigger → verify task executed and logged

### Tests for User Story 6

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T072 [P] [US6] Unit tests for SchedulerService in tests/unit/test_scheduler_service.py
- [ ] T073 [P] [US6] Integration tests for scheduled task execution in tests/integration/test_scheduled_tasks.py

### Implementation for User Story 6

- [ ] T074 [US6] Create SchedulerService in src/ai_employee/services/scheduler.py with add_task(), remove_task(), run_task() methods (FR-026)
- [ ] T075 [US6] Implement cron expression parsing and scheduling using APScheduler
- [ ] T076 [US6] Implement one-time scheduled tasks with specific datetime (FR-027)
- [ ] T077 [US6] Implement task execution logging with outcomes (FR-028)
- [ ] T078 [US6] Implement missed schedule handling (skip, run_immediately, queue) (FR-029)
- [ ] T079 [US6] Implement timezone support for scheduling (FR-030)
- [ ] T080 [US6] Add CLI command `ai-employee scheduler` in src/ai_employee/cli/main.py
- [ ] T081 [US6] Implement briefing generation scheduled task template
- [ ] T082 [US6] Implement weekly audit scheduled task template
- [ ] T083 [US6] Update /schedule-task skill script in .claude/skills/schedule-task/scripts/manage_schedules.py to integrate with SchedulerService

**Checkpoint**: User Story 6 fully functional - tasks run on schedule with missed execution handling

---

## Phase 9: Agent Skills Integration (All User Stories)

**Purpose**: Ensure all Agent Skills are properly integrated and documented (FR-031 to FR-035)

- [ ] T084 [P] Verify /post-linkedin skill integration with LinkedInService (FR-031)
- [ ] T085 [P] Verify /create-plan skill integration with PlannerService (FR-032)
- [ ] T086 [P] Verify /send-email skill integration with email service (FR-033)
- [ ] T087 [P] Verify /approve-action skill integration with ApprovalService (FR-034)
- [ ] T088 [P] Verify /schedule-task skill integration with SchedulerService (FR-035)
- [ ] T089 Add skill integration tests in tests/integration/test_skills.py

**Checkpoint**: All 5 Agent Skills fully integrated with their respective services

---

## Phase 10: Security & Polish (Cross-Cutting Concerns)

**Purpose**: Security hardening, credential management, and final validation

### Security (FR-036 to FR-038)

- [ ] T090 [P] Create .env.example template with all required credentials
- [ ] T091 [P] Verify .env is in .gitignore (FR-037)
- [ ] T092 Implement credential loading from environment variables (FR-036)
- [ ] T093 Audit all logging to ensure no credential exposure (FR-038)

### Documentation & Validation

- [ ] T094 [P] Update CLAUDE.md with Silver tier documentation
- [ ] T095 [P] Update scripts/init_vault.sh to include Silver tier folders
- [ ] T096 Run quickstart.md validation to verify all commands work
- [ ] T097 Run full test suite with coverage report (target: 80%)
- [ ] T098 Type check all new code with mypy

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 - **BLOCKS all user stories**
- **User Story 1 (Phase 3)**: Depends on Phase 2 - **BLOCKS phases 4-9** (approval is foundation for all sensitive actions)
- **User Stories 2-6 (Phases 4-8)**: Depend on Phase 2 + Phase 3 (US1) - Can run in parallel after US1 complete
- **Skills Integration (Phase 9)**: Depends on Phases 3-8 (all user stories)
- **Polish (Phase 10)**: Depends on all phases - final validation

### User Story Dependencies

```
Phase 1: Setup
    │
    ▼
Phase 2: Foundational (Models)
    │
    ▼
Phase 3: US1 - Approval Workflow (P1) ← MVP Foundation
    │
    ├───────┬───────┬───────┬───────┐
    ▼       ▼       ▼       ▼       ▼
Phase 4  Phase 5  Phase 6  Phase 7  Phase 8
US2      US3      US4      US5      US6
WhatsApp Gmail    Planning LinkedIn Scheduler
(P2)     (P2)     (P2)     (P3)     (P3)
    │       │       │       │       │
    └───────┴───────┴───────┴───────┘
                    │
                    ▼
            Phase 9: Skills Integration
                    │
                    ▼
            Phase 10: Polish
```

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. Models before services (completed in Phase 2)
3. Services before watchers/CLI
4. Core implementation before integration
5. Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002, T003 can run in parallel
- **Phase 2**: All model tasks (T005-T014) can run in parallel; all tests (T015-T019) can run in parallel
- **Phases 4-8**: After US1 complete, can work on US2-US6 in parallel if team capacity allows
- **Phase 9**: All skill verification tasks (T084-T088) can run in parallel
- **Phase 10**: T090, T091, T094, T095 can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 - Approval Workflow
4. **STOP and VALIDATE**: Test approval workflow independently
5. Deploy/demo if ready - this is the minimum viable Silver tier

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Approval) → Test → **MVP Ready!**
3. Add US2 (WhatsApp) → Test → Communication monitoring
4. Add US3 (Gmail MCP) → Test → Email automation
5. Add US4 (Planning) → Test → Task transparency
6. Add US5 (LinkedIn) → Test → Social presence
7. Add US6 (Scheduler) → Test → Full automation
8. Skills + Polish → **Silver Tier Complete!**

### Sequential Implementation (Recommended)

Given the dependency structure and that US1 is foundation for all others:

1. P1: Approval Workflow (US1) - Required for all sensitive actions
2. P2: WhatsApp (US2), Gmail (US3), Planning (US4) - Core productivity
3. P3: LinkedIn (US5), Scheduler (US6) - Growth features

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US1 (Approval) is the critical path - all other stories depend on it
