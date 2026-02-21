---
name: ralph-loop
description: Start the Ralph Wiggum autonomous execution loop for multi-step task completion. Use when user wants to run a complex task autonomously, needs multi-step processing, or wants the AI to work through a task iteratively without constant intervention.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Ralph Wiggum Autonomous Loop

Execute a multi-step task autonomously using the Ralph Wiggum execution loop.
The loop runs up to N iterations (default 10), tracking state in /Active_Tasks/.

## Usage

```
/ralph-loop <task_description>
```

## Arguments

- `task_description` (required): Natural language description of the task to execute autonomously

## Examples

```
/ralph-loop "Process all inbox items and draft email replies"
/ralph-loop "Review files in Drop folder, categorize them, and update dashboard"
/ralph-loop "Prepare weekly briefing from recent activity logs"
```

## Workflow

1. **Initialize Task State**:
   - Create a TaskState in /Active_Tasks/{task_id}.json
   - Set status to in_progress, iteration to 1
   - Default: max 10 iterations, completion via "TASK_COMPLETE" promise

2. **Execute Loop** (for each iteration):
   a. Read the current task state from disk
   b. Analyze what needs to be done based on prompt and previous context
   c. Perform the next logical action toward completing the task
   d. Update context with what was accomplished
   e. Increment iteration counter
   f. Check: Is the task complete? If yes, signal completion.
   g. Check: Does this step require human approval? If yes, pause.

3. **Completion Detection**:
   - **Promise strategy** (default): Output "TASK_COMPLETE" when done
   - **File movement strategy**: Detect when target files have been moved

4. **Approval Integration**:
   - If a step requires human approval (e.g., sending email, payment):
     - Pause the task (status: paused)
     - Create approval request in /Pending_Approval/
     - Wait for approval before resuming
     - Use /approve-action to approve/reject

5. **Error Handling**:
   - If an iteration fails, log the error in context
   - If max iterations reached, fail the task with explanation
   - Failed tasks are moved to /Done/ for audit

6. **Task State Location**:
   - Active: /Active_Tasks/{task_id}.json
   - Completed/Failed: /Done/{task_id}.json

## Task State Fields

| Field | Description |
|-------|-------------|
| task_id | UUID identifier |
| prompt | Original task description |
| iteration | Current loop iteration (starts at 1) |
| max_iterations | Maximum allowed iterations |
| status | pending, in_progress, paused, completed, failed |
| completion_strategy | "promise" or "file_movement" |
| context | Last iteration output/notes |
| requires_approval | Whether paused for approval |
| approval_id | Link to approval request |

## Output

After task completion, report a summary with task ID, iterations used,
status, duration, and actions taken per iteration.

## Stop Hook

The Ralph Wiggum stop hook prevents Claude from exiting while a task is
in progress. If an active task exists:
- Completed/Failed tasks: exit allowed
- Paused tasks: exit allowed (waiting for human approval)
- In-progress tasks: exit blocked, task prompt re-injected
