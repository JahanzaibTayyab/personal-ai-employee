# Feature Specification: Silver Tier - Functional Assistant

**Feature Branch**: `002-silver-ai-employee`
**Created**: 2026-02-03
**Status**: Draft
**Input**: User description: "Silver Tier: Functional Assistant - Enhance the Bronze tier AI Employee with multi-channel watchers (WhatsApp, LinkedIn), LinkedIn auto-posting for sales lead generation, Claude reasoning loop with Plan.md files, Email MCP server, human-in-the-loop approval workflow, and cron-based scheduling"

## Overview

The Silver Tier elevates the Bronze tier AI Employee from a basic monitoring system to a functional assistant capable of multi-channel communication monitoring, proactive social media engagement, intelligent planning, and safe execution of sensitive actions through human approval workflows.

## Clarifications

### Session 2026-02-03

- Q: What happens when an approval request expires after 24 hours? → A: Auto-reject with notification (treat as rejected, alert user via Dashboard)
- Q: What method should be used for LinkedIn integration? → A: Official LinkedIn API only (requires developer app, ToS compliant)
- Q: How should sensitive credentials be stored? → A: Environment variables with .env file (standard, gitignored)
- Q: How should concurrent approvals be handled? → A: Sequential with queue (process one at a time in detection order)
- Q: Should we build custom Email MCP or use existing? → A: Use existing `google_workspace_mcp` package (taylorwilsdon/google_workspace_mcp, 1,283 stars)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Human-in-the-Loop Approval Workflow (Priority: P1)

As a business owner, I want sensitive actions (emails, social posts, payments) to require my explicit approval before execution, so that the AI Employee never takes irreversible actions without my consent.

**Why this priority**: Safety and trust are paramount. Without approval workflows, the system cannot be trusted with any sensitive operations. This is the foundation for all other Silver tier features.

**Independent Test**: Can be fully tested by triggering an action that requires approval, verifying the approval file appears in /Pending_Approval, then moving it to /Approved and confirming the action executes.

**Acceptance Scenarios**:

1. **Given** the AI Employee identifies an email needs to be sent, **When** it prepares the email action, **Then** it creates an approval request file in /Pending_Approval/ with all details (recipient, subject, body, attachments)
2. **Given** an approval file exists in /Pending_Approval/, **When** the user moves it to /Approved/, **Then** the system executes the approved action within 60 seconds
3. **Given** an approval file exists in /Pending_Approval/, **When** the user moves it to /Rejected/, **Then** the system logs the rejection and does not execute the action
4. **Given** an approval file has been pending for more than 24 hours, **When** the system checks pending items, **Then** it flags the item as stale on the Dashboard

---

### User Story 2 - WhatsApp Message Monitoring (Priority: P2)

As a business owner, I want to monitor my WhatsApp messages for urgent business communications, so that I never miss important client inquiries or time-sensitive requests.

**Why this priority**: WhatsApp is a primary communication channel for many businesses. Monitoring it extends the AI Employee's reach beyond email.

**Independent Test**: Can be fully tested by sending a WhatsApp message containing an urgent keyword, verifying it appears as an action item in /Needs_Action, and confirming the Dashboard reflects the new item.

**Acceptance Scenarios**:

1. **Given** the WhatsApp watcher is running, **When** a message arrives containing configured keywords (e.g., "urgent", "invoice", "payment", "help"), **Then** the system creates an action file in /Needs_Action/WhatsApp/
2. **Given** a WhatsApp message is detected, **When** the action file is created, **Then** it includes sender name, message content, timestamp, and detected keywords
3. **Given** the WhatsApp session expires, **When** the watcher detects the session loss, **Then** it alerts the user via Dashboard and pauses monitoring
4. **Given** multiple urgent messages arrive within 5 minutes, **When** processing them, **Then** each message creates a separate action file with unique identifiers

---

### User Story 3 - Gmail Integration via Google Workspace MCP (Priority: P2)

As a business owner, I want the AI Employee to draft and send emails on my behalf (with my approval), so that routine correspondence is handled efficiently.

**Why this priority**: Email is the most common business action. Integrating with the existing `google_workspace_mcp` package provides full Gmail management without building custom infrastructure.

**Independent Test**: Can be fully tested by requesting the AI to draft an email, verifying the draft appears for approval, approving it, and confirming the email is sent via the Google Workspace MCP.

**Acceptance Scenarios**:

1. **Given** an email action is approved, **When** the Google Workspace MCP receives the send request, **Then** it sends the email via Gmail API
2. **Given** an email needs to be drafted, **When** the AI Employee creates the draft, **Then** the draft includes to, cc, bcc, subject, body, and optional attachments
3. **Given** an email send fails, **When** the MCP encounters an error, **Then** it logs the error, moves the action to /Quarantine/, and alerts via Dashboard
4. **Given** the Google OAuth credentials are invalid or expired, **When** the MCP attempts to send, **Then** it fails gracefully and prompts for re-authentication via Dashboard

---

### User Story 4 - Claude Reasoning Loop with Plan.md (Priority: P2)

As a business owner, I want the AI Employee to break down complex tasks into step-by-step plans, so that I can understand and approve multi-step operations before they begin.

**Why this priority**: Complex tasks require transparency. Plan.md files provide visibility into the AI's reasoning and allow intervention before execution.

**Independent Test**: Can be fully tested by requesting a multi-step task, verifying a Plan.md file is created with clear steps, and confirming each step can be individually tracked.

**Acceptance Scenarios**:

1. **Given** a multi-step task is identified, **When** the reasoning loop processes it, **Then** it creates a Plan.md file in /Plans/ with numbered steps, dependencies, and required approvals
2. **Given** a Plan.md exists, **When** a step requires external action, **Then** it creates an approval request in /Pending_Approval/ before execution
3. **Given** a step in the plan fails, **When** the failure is detected, **Then** the plan is paused, the failure is logged, and the Dashboard is updated
4. **Given** all steps in a plan are completed, **When** the plan finishes, **Then** it moves to /Done/ with a completion summary

---

### User Story 5 - LinkedIn Monitoring and Auto-Posting (Priority: P3)

As a business owner, I want to automatically post business content on LinkedIn and monitor engagement, so that I maintain an active social presence that generates sales leads.

**Why this priority**: Social media presence drives business growth, but it's not as time-critical as communication monitoring or safety features.

**Independent Test**: Can be fully tested by scheduling a LinkedIn post, approving it, verifying it appears on LinkedIn, and checking that engagement metrics are captured.

**Acceptance Scenarios**:

1. **Given** a LinkedIn post is scheduled, **When** the posting time arrives, **Then** the system creates an approval request with post content preview
2. **Given** a LinkedIn post is approved, **When** the posting MCP executes, **Then** the post appears on LinkedIn within 5 minutes
3. **Given** LinkedIn engagement occurs (likes, comments), **When** the watcher detects new activity, **Then** it logs engagement metrics in /Social/LinkedIn/engagement.md
4. **Given** a LinkedIn comment mentions keywords (inquiry, interested, pricing), **When** detected, **Then** an action item is created for follow-up

---

### User Story 6 - Scheduled Tasks via Cron (Priority: P3)

As a business owner, I want routine tasks to run automatically on a schedule, so that daily briefings and weekly audits happen without manual intervention.

**Why this priority**: Automation of routine tasks is valuable but depends on other features being in place first.

**Independent Test**: Can be fully tested by configuring a scheduled task, waiting for the schedule to trigger, and verifying the task executed and logged correctly.

**Acceptance Scenarios**:

1. **Given** a daily briefing is scheduled for 8:00 AM, **When** the time arrives, **Then** the system generates a briefing in /Briefings/ and updates Dashboard
2. **Given** a weekly audit is scheduled for Sunday 9:00 PM, **When** the time arrives, **Then** the system analyzes the week's activities and creates an audit report
3. **Given** a scheduled task fails, **When** the failure is detected, **Then** the system logs the error and retries once after 5 minutes
4. **Given** the system was offline during a scheduled time, **When** it comes back online, **Then** it runs missed scheduled tasks within 10 minutes (configurable)

---

### Edge Cases

- What happens when WhatsApp Web session expires or is logged out from another device?
- How does the system handle LinkedIn rate limiting or temporary blocks?
- What if multiple approval files are approved simultaneously?
- How does the system behave when the /Pending_Approval folder is not accessible?
- What happens if Gmail send partially succeeds (sent to some recipients, failed for others)?
- How are scheduled tasks handled across timezone changes (DST)?
- What if a Plan.md references files that have been moved or deleted?

## Requirements *(mandatory)*

### Functional Requirements

#### Approval Workflow

- **FR-001**: System MUST create approval request files in /Pending_Approval/ for all sensitive actions (emails, social posts, actions over configurable thresholds)
- **FR-002**: System MUST monitor /Approved/ folder for approved actions and execute them within 60 seconds of detection
- **FR-003**: System MUST monitor /Rejected/ folder and log rejections without executing the action
- **FR-004**: System MUST include expiration timestamps in approval files (default: 24 hours)
- **FR-004a**: System MUST auto-reject expired approval requests and notify user via Dashboard
- **FR-004b**: System MUST process concurrent approvals sequentially in detection order (queue-based)
- **FR-005**: System MUST support approval categories: email, social_post, payment, file_operation, custom

#### WhatsApp Watcher

- **FR-006**: System MUST monitor WhatsApp Web for new messages using browser automation
- **FR-007**: System MUST filter messages by configurable keywords (default: urgent, asap, invoice, payment, help, pricing)
- **FR-008**: System MUST create action files with sender info, message content, timestamp, and matched keywords
- **FR-009**: System MUST detect session expiration and alert via Dashboard
- **FR-010**: System MUST support persistent browser sessions to avoid repeated QR code scans

#### Gmail Integration (via google_workspace_mcp)

- **FR-011**: System MUST integrate with `google_workspace_mcp` package for Gmail operations (draft, send, search, list)
- **FR-012**: System MUST configure Google Workspace MCP with OAuth 2.0 credentials for Gmail access
- **FR-013**: System MUST support email attachments via the MCP's built-in attachment handling
- **FR-014**: System MUST log all email operations with timestamps and outcomes
- **FR-014a**: System MUST handle partial email send failures by:
  - Logging success/failure status per recipient
  - Moving action to /Quarantine/ if ANY recipient fails
  - Including detailed error report in quarantine file (which recipients succeeded, which failed, error messages)
  - Alerting user via Dashboard with recipient-level status
- **FR-015**: System MUST handle OAuth token refresh automatically via the MCP's built-in token management

#### Reasoning Loop & Planning

- **FR-016**: System MUST analyze incoming tasks and generate Plan.md files for multi-step operations
- **FR-017**: System MUST include in Plan.md: objective, numbered steps, dependencies, approval requirements, success criteria
- **FR-018**: System MUST track plan execution status (pending, in_progress, completed, failed, paused)
- **FR-019**: System MUST pause plan execution when an approval is required or a step fails
- **FR-019a**: System MUST validate Plan.md file references before step execution by:
  - Checking all referenced file paths exist before starting a step
  - If reference is missing: pause plan, mark step as "blocked", log missing reference
  - Dashboard shows "Plan blocked: missing file [path]" warning
  - User can manually resolve (restore file or edit plan) and resume
- **FR-020**: System MUST update Dashboard with active plan status

#### LinkedIn Integration

- **FR-021**: System MUST support scheduling LinkedIn posts with configurable posting times
- **FR-022**: System MUST monitor LinkedIn for engagement metrics (likes, comments, shares)
- **FR-023**: System MUST detect business-relevant comments using keyword matching
- **FR-024**: System MUST create action items for high-priority LinkedIn interactions
- **FR-025**: System MUST respect LinkedIn rate limits (max 25 posts per day)

#### Scheduling

- **FR-026**: System MUST support cron-style scheduling for recurring tasks
- **FR-027**: System MUST support one-time scheduled tasks with specific datetime
- **FR-028**: System MUST log all scheduled task executions with outcomes
- **FR-029**: System MUST handle missed schedules due to system downtime (configurable: skip, run immediately, or queue)
- **FR-030**: System MUST support scheduling in user's local timezone

#### Agent Skills

- **FR-031**: System MUST provide /post-linkedin skill for creating and scheduling LinkedIn posts
- **FR-032**: System MUST provide /create-plan skill for generating Plan.md files from task descriptions
- **FR-033**: System MUST provide /send-email skill for drafting emails (creates approval request)
- **FR-034**: System MUST provide /approve-action skill for listing and approving pending actions
- **FR-035**: System MUST provide /schedule-task skill for configuring recurring tasks

#### Security

- **FR-036**: System MUST store all credentials via environment variables loaded from .env file
- **FR-037**: System MUST ensure .env file is gitignored and never committed to version control
- **FR-038**: System MUST NOT log or expose credentials in error messages, logs, or approval files

### Key Entities

- **ApprovalRequest**: Represents an action awaiting human approval (type, payload, created_at, expires_at, status)
- **Plan**: Represents a multi-step task breakdown (objective, steps, status, created_at, completed_at)
- **PlanStep**: Individual step within a plan (description, status, dependencies, requires_approval)
- **ScheduledTask**: Recurring or one-time scheduled operation (name, schedule, action, last_run, next_run)
- **WhatsAppMessage**: Detected urgent message (sender, content, keywords, timestamp, action_status)
- **LinkedInPost**: Scheduled or posted content (content, scheduled_time, posted_time, engagement_metrics)
- **LinkedInEngagement**: Engagement activity on posts (type, author, content, timestamp, requires_followup)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can approve or reject any pending action in under 30 seconds via file move
- **SC-002**: WhatsApp urgent messages are detected and filed within 2 minutes of receipt
- **SC-003**: Approved emails are sent within 5 minutes of approval
- **SC-004**: Complex tasks generate Plan.md files with clear, actionable steps within 1 minute
- **SC-005**: LinkedIn posts are published within 5 minutes of their scheduled time (when approved)
- **SC-006**: Scheduled tasks execute within 1 minute of their configured time
- **SC-007**: System achieves 99% uptime for watchers over a 7-day period, measured by:
  - Heartbeat log entry every 60 seconds per watcher
  - Downtime = gap > 5 minutes between heartbeats
  - Maximum allowed downtime: 100 minutes per 7-day period (168 hours × 1% = 1.68 hours)
  - Dashboard displays current uptime percentage per watcher
- **SC-008**: Zero sensitive actions execute without prior approval
- **SC-009**: All action outcomes (success/failure) are logged within 30 seconds
- **SC-010**: Plan.md files meet readability standards:
  - Written at 8th-grade reading level (Flesch-Kincaid)
  - No code blocks, technical jargon, or implementation details
  - Each step is a single actionable sentence starting with a verb
  - Steps requiring approval are clearly marked with "Requires Approval"
  - Progress indicators use plain symbols: done, waiting, failed, pending

## Assumptions

1. The Bronze tier foundation (vault structure, file watcher, Gmail watcher, Dashboard, handbook parsing) is complete and functional
2. Users have access to WhatsApp Web and can authenticate via QR code initially
3. Users have LinkedIn developer app credentials with posting permissions (official API)
4. Users have Google Cloud project with OAuth 2.0 credentials configured for Gmail API access
5. Users understand the file-based approval workflow (move files between folders)
6. The system runs on a machine with persistent browser session storage capability
7. Network connectivity is generally stable (brief outages are tolerable)
8. Users operate in a single primary timezone

## Dependencies

- Bronze Tier AI Employee (001-bronze-ai-employee) - vault structure, watchers, Dashboard
- Browser automation capability (Playwright) for WhatsApp
- LinkedIn API credentials (developer app with posting permissions)
- `google_workspace_mcp` package (pip: workspace-mcp) for Gmail integration
- Google Cloud OAuth 2.0 credentials (Desktop app type) for Gmail API access
- Cron or equivalent scheduling mechanism on the host system

## Out of Scope

- WhatsApp message sending (monitoring only in Silver tier)
- LinkedIn direct messaging
- Payment processing (deferred to Gold tier)
- Multi-user support or role-based access control
- End-to-end encryption of approval files
- Mobile app interface (file-based workflow only)
- Real-time notifications beyond Dashboard updates
