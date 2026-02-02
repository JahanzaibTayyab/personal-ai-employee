# Tasks: Bronze Tier Personal AI Employee

**Input**: Design documents from `/specs/001-bronze-ai-employee/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested - test tasks omitted. Add TDD tasks if needed.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Python src layout**: `src/ai_employee/` at repository root
- **Tests**: `tests/unit/`, `tests/integration/`
- **Skills**: `.claude/skills/<skill-name>/SKILL.md`
- **Agents**: `.claude/agents/<agent-name>.md`

---

## Available Agents & Skills Reference

### Global Agents (use via Task tool)

| Agent | When to Use |
|-------|-------------|
| `architect` | Before starting each phase - architectural decisions, system design |
| `tdd-guide` | When writing tests first - enforces RED-GREEN-REFACTOR cycle |
| `code-reviewer` | After completing each task/phase - quality, security review |
| `security-reviewer` | For credential handling, input validation, OAuth setup |
| `build-error-resolver` | When `uv sync` or pytest fails |
| `e2e-runner` | For end-to-end testing with Playwright |
| `refactor-cleaner` | For dead code cleanup after implementation |
| `doc-updater` | For updating documentation and codemaps |

### Global Skills (invoke via /skill-name)

| Skill | When to Use |
|-------|-------------|
| `/coding-standards` | Reference Python best practices |
| `/backend-patterns` | Reference service layer, repository patterns |
| `/security-review` | Security checklist before commits |
| `/tdd-workflow` | TDD methodology guidance |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization with UV package manager and src layout

**Use Agent**: `architect` - Review project structure before implementation

- [ ] T001 Initialize Python project with UV: `uv init --package ai-employee`
- [ ] T002 Add core dependencies: `uv add watchdog pyyaml`
- [ ] T003 [P] Add dev dependencies: `uv add --dev pytest pytest-cov ruff`
- [ ] T004 [P] Add optional Gmail dependencies: `uv add google-auth google-api-python-client --optional gmail`
- [ ] T005 Create package structure: `src/ai_employee/__init__.py`
- [ ] T006 [P] Create watchers module: `src/ai_employee/watchers/__init__.py`
- [ ] T007 [P] Create models module: `src/ai_employee/models/__init__.py`
- [ ] T008 [P] Create services module: `src/ai_employee/services/__init__.py`
- [ ] T009 [P] Create CLI module: `src/ai_employee/cli/__init__.py`
- [ ] T010 [P] Create tests structure: `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`
- [ ] T011 Configure ruff linting in `pyproject.toml`

**After Phase**: Run `code-reviewer` agent to validate project structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

**Use Agents**:
- `architect` - Design data models and utilities
- `tdd-guide` - Write tests first for models (optional)
- `code-reviewer` - Review after each model implementation

**Reference Skills**: `/coding-standards`, `/backend-patterns`

- [ ] T012 Implement ActionItem dataclass model in `src/ai_employee/models/action_item.py`
- [ ] T013 [P] Implement ActivityLogEntry dataclass model in `src/ai_employee/models/activity_log.py`
- [ ] T014 [P] Implement WatcherEvent dataclass model in `src/ai_employee/models/watcher_event.py`
- [ ] T015 Implement YAML frontmatter parser utility in `src/ai_employee/utils/frontmatter.py`
- [ ] T016 [P] Implement JSON lines logger utility in `src/ai_employee/utils/jsonl_logger.py`
- [ ] T017 Create base watcher abstract class in `src/ai_employee/watchers/base.py`
- [ ] T018 [P] Create vault path configuration in `src/ai_employee/config.py`

**After Phase**: Run `code-reviewer` agent - Foundation must be solid before user stories

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - View AI Employee Dashboard (Priority: P1) MVP

**Goal**: Users can open Obsidian and see real-time AI Employee status on Dashboard.md

**Independent Test**: Open Obsidian, verify Dashboard.md displays current status, pending count, recent activity

**Use Agents**:
- `tdd-guide` - Write dashboard service tests first (optional)
- `code-reviewer` - After implementing dashboard service

### Implementation for User Story 1

- [ ] T019 [US1] Create DashboardState dataclass in `src/ai_employee/models/dashboard.py`
- [ ] T020 [US1] Implement Dashboard template generator in `src/ai_employee/services/dashboard.py`
- [ ] T021 [US1] Add pending items count logic (reads `/Needs_Action/` folder) in `src/ai_employee/services/dashboard.py`
- [ ] T022 [US1] Add recent activity parser (reads from `/Logs/claude_*.log`) in `src/ai_employee/services/dashboard.py`
- [ ] T023 [US1] Add watcher status indicator logic in `src/ai_employee/services/dashboard.py`
- [ ] T024 [US1] Add warnings section (error threshold detection) in `src/ai_employee/services/dashboard.py`
- [ ] T025 [US1] Create `/update-dashboard` skill in `.claude/skills/update-dashboard/SKILL.md`

**After Phase**: Run `code-reviewer` agent to validate dashboard implementation

**Checkpoint**: User Story 1 complete - Dashboard.md can be generated and shows system status

---

## Phase 4: User Story 2 - Automatic File Detection and Processing Queue (Priority: P1) MVP

**Goal**: Files dropped into /Drop are automatically detected and queued in /Needs_Action within 60 seconds

**Independent Test**: Drop test.txt into /Drop folder, verify FILE_test.txt.md appears in /Needs_Action with metadata

**Use Agents**:
- `architect` - Design watcher event flow
- `tdd-guide` - Write watcher tests first (optional)
- `security-reviewer` - Review file handling for path traversal risks
- `code-reviewer` - After watcher implementation

### Implementation for User Story 2

- [ ] T026 [US2] Implement FileSystemWatcher class in `src/ai_employee/watchers/filesystem.py`
- [ ] T027 [US2] Add watchdog Observer integration in `src/ai_employee/watchers/filesystem.py`
- [ ] T028 [US2] Implement file copy to /Needs_Action with metadata in `src/ai_employee/watchers/filesystem.py`
- [ ] T029 [US2] Add YAML frontmatter generation for action items in `src/ai_employee/watchers/filesystem.py`
- [ ] T030 [US2] Implement watcher event logging to `/Logs/watcher_*.log` in `src/ai_employee/watchers/filesystem.py`
- [ ] T031 [US2] Add error handling and /Quarantine move logic in `src/ai_employee/watchers/filesystem.py`
- [ ] T032 [US2] Implement CLI entry point for watcher in `src/ai_employee/cli/main.py`
- [ ] T033 [US2] Add `[project.scripts]` entry point in `pyproject.toml` for `ai-employee` command
- [ ] T034 [US2] Create `/check-watcher-health` skill in `.claude/skills/check-watcher/SKILL.md`

**After Phase**: Run `code-reviewer` + `security-reviewer` agents

**Checkpoint**: User Story 2 complete - File watcher detects and queues files automatically

---

## Phase 5: User Story 3 - AI Processing of Queued Items (Priority: P1) MVP

**Goal**: Claude Code reads items from /Needs_Action, applies handbook rules, moves to /Done with logging

**Independent Test**: Place test item in /Needs_Action, run /process-inbox, verify item moved to /Done with log entry

**Use Agents**:
- `architect` - Design processor service architecture
- `tdd-guide` - Write processor tests first (optional)
- `code-reviewer` - After processor implementation

**Reference Skills**: `/backend-patterns` for service layer design

### Implementation for User Story 3

- [ ] T035 [US3] Implement ItemProcessor service in `src/ai_employee/services/processor.py`
- [ ] T036 [US3] Add handbook rule reader in `src/ai_employee/services/processor.py`
- [ ] T037 [US3] Implement file move from /Needs_Action to /Done in `src/ai_employee/services/processor.py`
- [ ] T038 [US3] Add activity logging to `/Logs/claude_*.log` in `src/ai_employee/services/processor.py`
- [ ] T039 [US3] Implement Dashboard.md auto-update after processing in `src/ai_employee/services/processor.py`
- [ ] T040 [US3] Create `/process-inbox` skill in `.claude/skills/process-inbox/SKILL.md`
- [ ] T041 [US3] Create inbox-processor agent in `.claude/agents/inbox-processor.md`

**After Phase**: Run `code-reviewer` agent

**Checkpoint**: User Story 3 complete - Claude Code can process queued items end-to-end

---

## Phase 6: User Story 4 - Define Operating Rules via Company Handbook (Priority: P2)

**Goal**: Users can define rules in Company_Handbook.md that govern AI behavior

**Independent Test**: Add rule to handbook, process item, verify rule was applied

**Use Agents**:
- `tdd-guide` - Write handbook parser tests first (optional)
- `code-reviewer` - After handbook service implementation

### Implementation for User Story 4

- [ ] T042 [US4] Implement HandbookParser service in `src/ai_employee/services/handbook.py`
- [ ] T043 [US4] Add rule extraction logic (parse ### Rule N: sections) in `src/ai_employee/services/handbook.py`
- [ ] T044 [US4] Add priority keyword detection from handbook rules in `src/ai_employee/services/handbook.py`
- [ ] T045 [US4] Add conflict resolution (first rule wins) in `src/ai_employee/services/handbook.py`
- [ ] T046 [US4] Integrate HandbookParser into ItemProcessor in `src/ai_employee/services/processor.py`
- [ ] T047 [US4] Create default Company_Handbook.md template in `templates/Company_Handbook.md`

**After Phase**: Run `code-reviewer` agent

**Checkpoint**: User Story 4 complete - Handbook rules affect processing behavior

---

## Phase 7: User Story 5 - Gmail Watcher Integration (Priority: P2)

**Goal**: Important/unread Gmail emails are automatically queued as action items

**Independent Test**: Send test email marked important, verify EMAIL_*.md appears in /Needs_Action/Email/

**Use Agents**:
- `security-reviewer` - **CRITICAL** for OAuth credential handling
- `architect` - Design Gmail polling architecture
- `tdd-guide` - Write Gmail watcher tests with mocks (optional)
- `code-reviewer` - After Gmail watcher implementation

**Reference Skills**: `/security-review` for credential handling

### Implementation for User Story 5

- [ ] T048 [US5] Implement GmailWatcher class in `src/ai_employee/watchers/gmail.py`
- [ ] T049 [US5] Add OAuth2 credential loading from environment in `src/ai_employee/watchers/gmail.py`
- [ ] T050 [US5] Implement Gmail API polling (unread + important filter) in `src/ai_employee/watchers/gmail.py`
- [ ] T051 [US5] Add processed message ID tracking (prevent duplicates) in `src/ai_employee/watchers/gmail.py`
- [ ] T052 [US5] Create EMAIL_*.md action files with frontmatter in `src/ai_employee/watchers/gmail.py`
- [ ] T053 [US5] Add watcher event logging for Gmail in `src/ai_employee/watchers/gmail.py`
- [ ] T054 [US5] Add Gmail watcher CLI subcommand in `src/ai_employee/cli/main.py`

**After Phase**: Run `security-reviewer` + `code-reviewer` agents (credentials handling is critical)

**Checkpoint**: User Story 5 complete - Gmail emails auto-queue as action items

---

## Phase 8: User Story 6 - Agent Skills Implementation (Priority: P2)

**Goal**: All AI functionality accessible via slash commands with modular skill files

**Independent Test**: Invoke /process-inbox, /update-dashboard, /check-watcher-health and verify each works

**Use Agents**:
- `code-reviewer` - Validate skill file format and instructions
- `doc-updater` - Update README with skill documentation

### Implementation for User Story 6

- [ ] T055 [US6] Finalize /process-inbox skill with complete instructions in `.claude/skills/process-inbox/SKILL.md`
- [ ] T056 [P] [US6] Finalize /update-dashboard skill with complete instructions in `.claude/skills/update-dashboard/SKILL.md`
- [ ] T057 [P] [US6] Finalize /check-watcher-health skill with complete instructions in `.claude/skills/check-watcher/SKILL.md`
- [ ] T058 [US6] Create watcher-monitor agent in `.claude/agents/watcher-monitor.md`
- [ ] T059 [US6] Add skill usage documentation to README

**After Phase**: Run `doc-updater` agent to finalize documentation

**Checkpoint**: User Story 6 complete - All AI functionality is modular and skill-based

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements affecting multiple user stories

**Use Agents**:
- `refactor-cleaner` - Remove dead code, consolidate utilities
- `security-reviewer` - Final security audit
- `doc-updater` - Update all documentation
- `e2e-runner` - Run end-to-end validation (optional)

- [ ] T060 [P] Create vault initialization script in `scripts/init_vault.sh`
- [ ] T061 [P] Create sample .env.example file in repository root
- [ ] T062 Validate quickstart.md flow end-to-end
- [ ] T063 [P] Add type hints validation with mypy in CI
- [ ] T064 Run `refactor-cleaner` agent for code cleanup
- [ ] T065 Run `security-reviewer` agent for final security audit
- [ ] T066 Run `doc-updater` agent to update CLAUDE.md with final structure

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase
  - US1, US2, US3 (P1 stories) - Prioritize completing first
  - US4, US5, US6 (P2 stories) - Complete after P1 stories
- **Polish (Phase 9)**: Depends on desired user stories being complete

### User Story Dependencies

| Story | Depends On | Can Run In Parallel With |
|-------|------------|--------------------------|
| US1 (Dashboard) | Foundational | US2, US3 |
| US2 (File Watcher) | Foundational | US1, US3 |
| US3 (AI Processing) | Foundational, partial US1 (dashboard update) | US1, US2 |
| US4 (Handbook) | US3 (integrates with processor) | US5, US6 |
| US5 (Gmail) | Foundational | US4, US6 |
| US6 (Skills) | US1, US2, US3 (skills reference these) | US4, US5 |

### Within Each User Story

- Models before services
- Services before CLI/skills
- Core implementation before integration

### Agent Usage Flow Per Phase

```
┌─────────────────────────────────────────────────────────┐
│  START PHASE                                            │
├─────────────────────────────────────────────────────────┤
│  1. architect agent     → Design decisions              │
│  2. tdd-guide agent     → Write tests first (optional)  │
│  3. IMPLEMENT           → Write code                    │
│  4. code-reviewer agent → Quality check                 │
│  5. security-reviewer   → If handling credentials/input │
│  6. build-error-resolver → If build fails               │
├─────────────────────────────────────────────────────────┤
│  END PHASE → Move to next                               │
└─────────────────────────────────────────────────────────┘
```

### Parallel Opportunities

**Setup Phase (all [P] tasks):**
```
T003, T004 (dependencies)
T006, T007, T008, T009, T010 (module structure)
```

**Foundational Phase:**
```
T013, T014 (models)
T016, T018 (utilities)
```

**User Story 6:**
```
T055, T056, T057 (skill files)
```

---

## Parallel Example: Setup Phase

```bash
# Launch dependency additions together:
Task: "Add dev dependencies: uv add --dev pytest pytest-cov ruff"
Task: "Add optional Gmail dependencies: uv add google-auth google-api-python-client --optional gmail"

# Launch module creation together:
Task: "Create watchers module: src/ai_employee/watchers/__init__.py"
Task: "Create models module: src/ai_employee/models/__init__.py"
Task: "Create services module: src/ai_employee/services/__init__.py"
Task: "Create CLI module: src/ai_employee/cli/__init__.py"
Task: "Create tests structure: tests/__init__.py, tests/unit/__init__.py"
```

---

## Implementation Strategy

### MVP First (P1 User Stories Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US1 - Dashboard
4. Complete Phase 4: US2 - File Watcher
5. Complete Phase 5: US3 - AI Processing
6. **STOP and VALIDATE**: Test end-to-end flow
7. Demo: Drop file → Watcher detects → Process with Claude → Dashboard updates

### Incremental Delivery

1. **Setup + Foundational** → Project structure ready
2. **Add US1** → Dashboard displays status (value: visibility)
3. **Add US2** → Files auto-detected (value: automation)
4. **Add US3** → AI processes items (value: intelligence)
5. **MVP Complete** - Bronze tier functional
6. **Add US4** → Handbook rules work (value: customization)
7. **Add US5** → Gmail integration (value: communication)
8. **Add US6** → Modular skills (value: extensibility)

### Suggested MVP Scope

**Minimum Viable Product (Bronze Hackathon):**
- Phase 1: Setup
- Phase 2: Foundational
- Phase 3: US1 - Dashboard
- Phase 4: US2 - File Watcher
- Phase 5: US3 - AI Processing

This delivers a working AI Employee that:
- Watches for files
- Queues them for processing
- Claude Code processes items
- Dashboard shows status

---

## Agent Cheat Sheet

| Task Type | Agent to Use | Command |
|-----------|--------------|---------|
| Start new phase | `architect` | Use Task tool with architect agent |
| Write tests first | `tdd-guide` | Use Task tool with tdd-guide agent |
| After writing code | `code-reviewer` | Use Task tool with code-reviewer agent |
| Handling credentials | `security-reviewer` | Use Task tool with security-reviewer agent |
| Build fails | `build-error-resolver` | Use Task tool with build-error-resolver agent |
| E2E testing | `e2e-runner` | Use Task tool with e2e-runner agent |
| Dead code cleanup | `refactor-cleaner` | Use Task tool with refactor-cleaner agent |
| Update docs | `doc-updater` | Use Task tool with doc-updater agent |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story is independently testable
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- UV auto-resolves latest versions - do not hardcode
- **Use agents proactively** - they catch issues early
