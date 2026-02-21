# Ralph Wiggum Service Contract

**Version**: 1.0.0 | **Created**: 2026-02-21

## Overview

Service for managing autonomous multi-step task execution using the Ralph Wiggum loop pattern.

---

## Interface: RalphWiggumService

### Methods

#### start_task

Start a new autonomous task.

**Input**:
```python
def start_task(
    prompt: str,
    completion_strategy: Literal["promise", "file_movement"] = "promise",
    completion_promise: str = "TASK_COMPLETE",
    max_iterations: int = 10
) -> TaskState
```

**Output**: TaskState with status="in_progress"

**Errors**:
- `TaskAlreadyActiveError`: Another task is already running
- `InvalidPromptError`: Prompt is empty or too long

---

#### get_task_state

Get current state of active task.

**Input**:
```python
def get_task_state(task_id: str) -> Optional[TaskState]
```

**Output**: TaskState or None if not found

---

#### pause_task

Pause task for approval.

**Input**:
```python
def pause_task(task_id: str, approval_id: str) -> TaskState
```

**Output**: TaskState with status="paused"

**Errors**:
- `TaskNotFoundError`: Task doesn't exist
- `InvalidStateError`: Task not in "in_progress" state

---

#### resume_task

Resume paused task after approval.

**Input**:
```python
def resume_task(task_id: str) -> TaskState
```

**Output**: TaskState with status="in_progress"

**Errors**:
- `TaskNotFoundError`: Task doesn't exist
- `InvalidStateError`: Task not in "paused" state
- `ApprovalPendingError`: Approval not yet granted

---

#### complete_task

Mark task as completed.

**Input**:
```python
def complete_task(task_id: str) -> TaskState
```

**Output**: TaskState with status="completed"

---

#### fail_task

Mark task as failed.

**Input**:
```python
def fail_task(task_id: str, error_message: str) -> TaskState
```

**Output**: TaskState with status="failed"

---

#### increment_iteration

Increment iteration counter and update context.

**Input**:
```python
def increment_iteration(task_id: str, context: str) -> TaskState
```

**Output**: Updated TaskState

**Errors**:
- `MaxIterationsExceededError`: Iteration count exceeds max_iterations

---

## Stop Hook Contract

### check_completion

Called by Claude Code Stop hook to determine if exit should be allowed.

**Script**: `.claude/hooks/ralph-wiggum-stop.sh`

**Behavior**:
1. Check if active task exists in `/Active_Tasks/`
2. If no active task: EXIT 0 (allow exit)
3. If task status is "completed" or "failed": EXIT 0 (allow exit)
4. If task status is "paused": EXIT 0 (allow exit, waiting for approval)
5. Otherwise:
   - Output the prompt + context to stdout
   - EXIT 1 (block exit, re-inject prompt)

**Exit Codes**:
- `0`: Allow Claude Code to exit
- `1`: Block exit, continue task

---

## Events

| Event | When | Payload |
|-------|------|---------|
| `task_started` | New task begins | task_id, prompt |
| `task_iterated` | Iteration completed | task_id, iteration |
| `task_paused` | Waiting for approval | task_id, approval_id |
| `task_resumed` | Approval received | task_id |
| `task_completed` | Task finished | task_id, iterations_used |
| `task_failed` | Task errored | task_id, error |
| `max_iterations_reached` | Hit limit | task_id, max_iterations |
