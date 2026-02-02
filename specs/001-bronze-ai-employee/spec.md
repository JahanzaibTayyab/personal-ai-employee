# Feature Specification: Bronze Tier Personal AI Employee

**Feature Branch**: `001-bronze-ai-employee`
**Created**: 2026-02-03
**Status**: Draft
**Input**: User description: "Bronze Tier Personal AI Employee - Foundation layer for autonomous Digital FTE system using Claude Code and Obsidian"

## Overview

The Bronze tier represents the **Minimum Viable Deliverable** for the Personal AI Employee hackathon. It establishes the foundational layer that enables an AI agent to read from and write to a local knowledge base (Obsidian vault), respond to external triggers via a Watcher script, and operate within a structured folder-based workflow system. This foundation enables future Silver, Gold, and Platinum tier enhancements.

**Estimated Implementation Time**: 8-12 hours

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View AI Employee Dashboard (Priority: P1)

As a user, I want to open my Obsidian vault and immediately see a real-time summary of my AI Employee's status, including pending tasks, recent activity, and system health, so that I can understand what my AI Employee is working on at a glance.

**Why this priority**: The Dashboard is the primary interface between the user and the AI Employee. Without it, users cannot monitor or understand the system's state. It provides immediate value by centralizing all AI Employee activity visibility.

**Independent Test**: Can be fully tested by opening Obsidian and verifying the Dashboard.md displays current status information. Delivers immediate value as a monitoring interface even before automation is connected.

**Acceptance Scenarios**:

1. **Given** the Obsidian vault is set up with the AI Employee folder structure, **When** I open Dashboard.md, **Then** I see sections for: current status, pending items count, recent activity log, and system health indicators
2. **Given** there are items in the /Needs_Action folder, **When** I view Dashboard.md, **Then** the pending items count reflects the actual number of files in /Needs_Action
3. **Given** the AI Employee has processed tasks today, **When** I view Dashboard.md, **Then** I see a timestamped log of recent AI activities

---

### User Story 2 - Automatic File Detection and Processing Queue (Priority: P1)

As a user, I want new files dropped into a monitored folder to be automatically detected and queued for AI processing, so that my AI Employee can respond to events without manual intervention.

**Why this priority**: This is the core "Perception" capability that makes the AI Employee autonomous rather than manually triggered. Without file watching, the system is just a static knowledge base.

**Independent Test**: Can be tested by dropping a test file into the monitored folder and verifying it appears in /Needs_Action with proper metadata. Delivers the foundational automation capability.

**Acceptance Scenarios**:

1. **Given** the File System Watcher is running, **When** I drop a new file into the /Drop folder, **Then** the file is copied to /Needs_Action within 60 seconds with a corresponding .md metadata file
2. **Given** a file is detected by the Watcher, **When** the metadata file is created, **Then** it includes: original filename, file size, timestamp, and file type
3. **Given** the Watcher encounters a file it cannot process, **When** an error occurs, **Then** the error is logged and the file is moved to /Quarantine folder

---

### User Story 3 - AI Processing of Queued Items (Priority: P1)

As a user, I want Claude Code to automatically read items from my /Needs_Action folder and process them according to my Company Handbook rules, so that my AI Employee can autonomously handle routine tasks.

**Why this priority**: This is the core "Reasoning" capability that transforms detected files into actionable outcomes. It connects the Watcher input to meaningful AI-driven processing.

**Independent Test**: Can be tested by manually placing a task file in /Needs_Action and running Claude Code to verify it reads the file, applies handbook rules, and creates appropriate output in /Done.

**Acceptance Scenarios**:

1. **Given** there is a file in /Needs_Action, **When** Claude Code is triggered, **Then** it reads the file content and references Company_Handbook.md for processing rules
2. **Given** Claude Code processes a file successfully, **When** processing completes, **Then** the original file is moved from /Needs_Action to /Done with a completion timestamp
3. **Given** Claude Code processes a file, **When** a decision or action is taken, **Then** an entry is added to the activity log in Dashboard.md

---

### User Story 4 - Define Operating Rules via Company Handbook (Priority: P2)

As a user, I want to define rules and guidelines in a Company Handbook that govern how my AI Employee should behave, so that I can customize the AI's responses and decision-making to match my preferences.

**Why this priority**: The Company Handbook enables personalization and control over AI behavior. While important, the system can function with default behaviors initially, making this P2.

**Independent Test**: Can be tested by adding a rule to Company_Handbook.md and verifying Claude Code references and follows that rule during processing.

**Acceptance Scenarios**:

1. **Given** Company_Handbook.md exists with defined rules, **When** Claude Code processes any item, **Then** it reads and applies the rules from the handbook
2. **Given** I add a new rule to the handbook (e.g., "Always prioritize messages containing 'urgent'"), **When** Claude Code processes items, **Then** it follows the new rule
3. **Given** the handbook contains conflicting rules, **When** Claude Code encounters a conflict, **Then** it logs the conflict and applies the rule listed first (priority by order)

---

### User Story 5 - Gmail Watcher Integration (Priority: P2)

As a user, I want my AI Employee to monitor my Gmail inbox for important/unread emails and create action items in my vault, so that urgent emails are automatically surfaced for attention.

**Why this priority**: Gmail is a common communication channel that benefits from AI monitoring. This is P2 because the File System Watcher provides the foundational pattern, and Gmail extends it to a specific use case.

**Independent Test**: Can be tested by sending a test email marked as important/unread and verifying an action file appears in /Needs_Action within the configured polling interval.

**Acceptance Scenarios**:

1. **Given** the Gmail Watcher is configured with valid credentials, **When** a new unread important email arrives, **Then** a markdown file is created in /Needs_Action/Email/ within 2 minutes
2. **Given** an email action file is created, **When** I view the file, **Then** it contains: sender, subject, timestamp, priority level, email snippet, and suggested actions checklist
3. **Given** an email has been processed into an action file, **When** the same email is checked again, **Then** it is not duplicated (tracked by message ID)

---

### User Story 6 - Agent Skills Implementation (Priority: P2)

As a user, I want all AI functionality to be implemented as Agent Skills that can be invoked via slash commands, so that I can easily trigger specific AI capabilities and extend the system with new skills.

**Why this priority**: Agent Skills provide modularity and extensibility. The hackathon explicitly requires "All AI functionality should be implemented as Agent Skills." This is P2 because basic functionality can work first, then be refactored into skills.

**Independent Test**: Can be tested by invoking a skill via slash command (e.g., /process-inbox) and verifying it executes the expected functionality.

**Acceptance Scenarios**:

1. **Given** Agent Skills are configured in the Claude Code environment, **When** I invoke a skill like /process-inbox, **Then** it processes all items in /Needs_Action
2. **Given** a skill completes execution, **When** I check the output, **Then** it includes a summary of actions taken
3. **Given** a skill encounters an error, **When** the error occurs, **Then** it is logged with sufficient detail for debugging

---

### Edge Cases

- What happens when the Obsidian vault is locked or inaccessible during Claude Code processing?
- How does the system handle extremely large files (>10MB) dropped into the watch folder?
- What happens when Gmail API rate limits are exceeded?
- How does the system behave when the /Needs_Action folder contains hundreds of unprocessed items?
- What happens when Company_Handbook.md is empty or malformed?
- How does the system handle network disconnection during Gmail polling?

## Requirements *(mandatory)*

### Functional Requirements

**Obsidian Vault Structure**

- **FR-001**: System MUST create an Obsidian vault with the following root folders: /Inbox, /Needs_Action, /Done, /Drop, /Quarantine, /Logs
- **FR-002**: System MUST include a Dashboard.md file at vault root displaying: pending item count, recent activity (last 10 items), and last update timestamp
- **FR-003**: System MUST include a Company_Handbook.md file at vault root containing editable rules for AI behavior
- **FR-004**: Dashboard.md MUST auto-update when Claude Code processes items (via file modification)

**Python Project Structure**

- **FR-005**: System MUST use UV as the Python package manager for all Python components
- **FR-006**: Python project MUST follow src directory layout (src/<package_name>/) for proper package organization
- **FR-007**: Project MUST include pyproject.toml for dependency management via UV

**File System Watcher**

- **FR-008**: System MUST include a Python Watcher script that monitors the /Drop folder for new files
- **FR-009**: Watcher MUST run continuously as a background process with configurable polling interval (default: 60 seconds)
- **FR-010**: Watcher MUST copy detected files to /Needs_Action and create accompanying .md metadata files
- **FR-011**: Watcher MUST handle common file types: .txt, .pdf, .docx, .png, .jpg, .csv, .json, .md
- **FR-012**: Watcher MUST log all detection events to /Logs/watcher_YYYY-MM-DD.log

**Gmail Watcher (Optional for Bronze - user can choose File System OR Gmail)**

- **FR-013**: System MAY include a Gmail Watcher that polls for unread important emails
- **FR-014**: Gmail Watcher MUST use OAuth2 credentials stored securely (environment variables or credential file outside vault)
- **FR-015**: Gmail Watcher MUST track processed email IDs to prevent duplicate action files
- **FR-016**: Gmail action files MUST include YAML frontmatter with: type, from, subject, received, priority, status

**Claude Code Integration**

- **FR-017**: Claude Code MUST be able to read all files in the Obsidian vault
- **FR-018**: Claude Code MUST be able to write/modify files in the Obsidian vault
- **FR-019**: Claude Code MUST reference Company_Handbook.md when processing items
- **FR-020**: Claude Code MUST move processed files from /Needs_Action to /Done
- **FR-021**: Claude Code MUST update Dashboard.md after processing items
- **FR-022**: Claude Code MUST log all actions to /Logs/claude_YYYY-MM-DD.log

**Agent Skills**

- **FR-023**: All repeatable AI functionality MUST be implemented as Claude Code Agent Skills
- **FR-024**: Skills MUST be invocable via slash commands (e.g., /process-inbox, /update-dashboard)
- **FR-025**: Skills MUST include: process-inbox (process /Needs_Action items), update-dashboard (refresh Dashboard.md), check-watcher-health (verify watcher is running)

**Error Handling**

- **FR-026**: System MUST handle file access errors gracefully without crashing the Watcher
- **FR-027**: System MUST move unprocessable files to /Quarantine with error metadata
- **FR-028**: System MUST alert user (via Dashboard.md warning section) when errors exceed threshold (>5 errors in 1 hour)

### Key Entities

- **Action Item**: A file requiring AI processing; attributes include: original filename, source (filesystem/email), created timestamp, status (pending/processing/done/quarantined), priority level
- **Activity Log Entry**: A record of AI action; attributes include: timestamp, action type, item processed, outcome, duration
- **Handbook Rule**: A directive governing AI behavior; attributes include: rule text, priority order, applicable contexts
- **Watcher Event**: A detection event from a Watcher; attributes include: source type (filesystem/gmail), timestamp, file/message identifier, metadata

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view a real-time dashboard summarizing AI Employee status within 5 seconds of opening Obsidian
- **SC-002**: Files dropped into the /Drop folder are detected and queued in /Needs_Action within 60 seconds
- **SC-003**: Claude Code successfully reads from and writes to the Obsidian vault with 100% reliability
- **SC-004**: Processed files are moved to /Done with complete audit trail (original file + processing log entry)
- **SC-005**: The system processes 50+ action items per day without manual intervention (once watchers and Claude Code are running)
- **SC-006**: Users can customize AI behavior by editing Company_Handbook.md and seeing changes reflected in subsequent processing
- **SC-007**: All AI functionality is accessible via at least 3 Agent Skills (slash commands)
- **SC-008**: System errors are logged and visible on Dashboard.md within 5 minutes of occurrence
- **SC-009**: Gmail Watcher (if implemented) creates action files for unread important emails within 2 minutes of email arrival
- **SC-010**: Watcher processes run continuously for 24+ hours without crashing under normal conditions

## Assumptions

1. User has Claude Code installed with an active subscription (Pro) or configured with Claude Code Router for alternative LLM
2. User has Obsidian v1.10.6+ installed
3. User has Python 3.13+ installed for Watcher scripts
4. User has UV package manager installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
5. User has a stable internet connection for API calls (Gmail, Claude)
6. For Gmail integration, user will complete OAuth2 setup and provide valid credentials
7. The Obsidian vault will be stored on a local filesystem (not network drive) for reliable file watching
8. User's machine has at least 8GB RAM and 20GB free disk space
9. Watcher scripts will be managed by the user (started/stopped manually or via PM2/supervisord for persistence)
10. Python project follows src directory layout: `src/ai_employee/` with pyproject.toml at root

## Out of Scope (Bronze Tier)

The following are explicitly NOT part of Bronze tier and are reserved for Silver/Gold/Platinum:

- WhatsApp integration
- Multiple Watcher scripts running simultaneously
- MCP servers for external actions (sending emails, clicking buttons)
- Human-in-the-Loop (HITL) approval workflow
- Scheduled tasks via cron
- Banking/payment integration
- Social media posting
- CEO Briefing generation
- Ralph Wiggum loop for autonomous multi-step task completion
- Cloud deployment (always-on)
- Odoo accounting integration

## Dependencies

- Claude Code CLI (installed and authenticated)
- Obsidian application
- Python 3.13+
- UV package manager (for Python dependency management)
- Python packages (managed via UV): watchdog, pathlib, logging
- (Optional) Google Cloud project with Gmail API enabled for Gmail Watcher
- (Optional) google-auth, google-api-python-client packages for Gmail (installed via UV)
