# Error Recovery & Watchdog Service Contract

**Version**: 1.0.0 | **Created**: 2026-02-21

## Overview

Services for handling errors gracefully, managing retries, and monitoring system health.

---

# Part 1: Error Recovery Service

## Interface: ErrorRecoveryService

### Error Classification

#### classify_error

Classify an error for appropriate handling.

**Input**:
```python
def classify_error(error: Exception) -> ErrorCategory
```

**Output**: ErrorCategory enum
- `TRANSIENT`: Network, timeout - retry with backoff
- `AUTHENTICATION`: Token expired - pause and alert
- `LOGIC`: Invalid data - quarantine item
- `DATA`: Corrupted file - quarantine and alert
- `SYSTEM`: Disk full, etc. - halt and alert

---

### Retry Methods

#### with_retry (decorator)

Decorator for automatic retry with exponential backoff.

**Input**:
```python
@with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_errors: list[type] = None
)
def some_operation():
    pass
```

**Behavior**:
1. Execute function
2. On exception, classify error
3. If TRANSIENT: wait with backoff, retry
4. If other: raise immediately
5. After max_attempts: raise with retry info

---

#### execute_with_retry

Explicit retry wrapper for callbacks.

**Input**:
```python
def execute_with_retry(
    operation: Callable,
    args: tuple = (),
    kwargs: dict = {},
    max_attempts: int = 3,
    base_delay: float = 1.0
) -> tuple[bool, Any, Optional[Exception]]
```

**Output**: (success, result, last_error)

---

### Queue Methods

#### queue_for_retry

Queue a failed operation for later retry.

**Input**:
```python
def queue_for_retry(
    service: str,
    operation: str,
    parameters: dict,
    error: str
) -> str  # Returns queue ID
```

---

#### process_retry_queue

Process queued operations for a service.

**Input**:
```python
def process_retry_queue(
    service: str = None  # None = all services
) -> dict
```

**Output**:
```python
{
    "processed": int,
    "succeeded": int,
    "failed": int,
    "remaining": int
}
```

---

### Degraded State Methods

#### enter_degraded_mode

Mark a component as degraded.

**Input**:
```python
def enter_degraded_mode(
    component: str,
    reason: str
) -> None
```

---

#### exit_degraded_mode

Mark a component as healthy.

**Input**:
```python
def exit_degraded_mode(component: str) -> None
```

---

#### get_system_health

Get overall system health status.

**Input**:
```python
def get_system_health() -> dict
```

**Output**:
```python
{
    "status": str,  # "healthy", "degraded", "critical"
    "healthy_components": list[str],
    "degraded_components": dict[str, dict],
    "critical_failures": list[str]
}
```

---

#### can_execute_operation

Check if operation can proceed with current health.

**Input**:
```python
def can_execute_operation(
    required_components: list[str]
) -> bool
```

---

# Part 2: Watchdog Service

## Interface: WatchdogService

### Process Management

#### register_process

Register a process to be monitored.

**Input**:
```python
def register_process(
    name: str,
    command: list[str],
    is_critical: bool = False,
    restart_delay: int = 5,
    max_restarts: int = 3
) -> None
```

---

#### start_process

Start a registered process.

**Input**:
```python
def start_process(name: str) -> int  # Returns PID
```

**Errors**:
- `ProcessNotRegisteredError`: Unknown process name
- `ProcessAlreadyRunningError`: Process already active

---

#### stop_process

Stop a running process.

**Input**:
```python
def stop_process(
    name: str,
    graceful: bool = True,
    timeout: int = 30
) -> bool
```

---

#### restart_process

Restart a process.

**Input**:
```python
def restart_process(name: str) -> int  # Returns new PID
```

---

### Monitoring Methods

#### check_process

Check if a process is running.

**Input**:
```python
def check_process(name: str) -> ProcessStatus
```

**Output**:
```python
{
    "name": str,
    "status": str,  # "running", "stopped", "crashed"
    "pid": Optional[int],
    "uptime_seconds": Optional[int],
    "restart_count": int,
    "last_restart": Optional[datetime]
}
```

---

#### check_all_processes

Check status of all registered processes.

**Input**:
```python
def check_all_processes() -> list[ProcessStatus]
```

---

#### run_health_check_loop

Start the watchdog monitoring loop.

**Input**:
```python
def run_health_check_loop(
    check_interval: int = 60,  # seconds
    on_failure: Callable = None
) -> None
```

**Behavior**:
1. Loop every `check_interval` seconds
2. Check all registered processes
3. Restart crashed processes (respecting max_restarts)
4. Log heartbeat
5. Update Dashboard
6. Call `on_failure` callback if critical process down

---

### Heartbeat Methods

#### record_heartbeat

Record a heartbeat from a component.

**Input**:
```python
def record_heartbeat(component: str) -> None
```

---

#### check_heartbeats

Check for stale heartbeats.

**Input**:
```python
def check_heartbeats(
    max_age_seconds: int = 300  # 5 minutes
) -> list[str]  # Components with stale heartbeats
```

---

# Part 3: Audit Service

## Interface: AuditService

### Logging Methods

#### log_action

Log an action to the audit log.

**Input**:
```python
def log_action(
    action_type: str,
    actor: str,
    target: str,
    parameters: dict = None,
    approval_status: str = "not_required",
    approved_by: str = None,
    result: str = "success",
    error_message: str = None,
    correlation_id: str = None,
    duration_ms: int = None
) -> AuditEntry
```

---

#### log_action_decorator (decorator)

Decorator for automatic action logging.

**Input**:
```python
@log_action_decorator(
    action_type: str,
    actor: str = "claude_code"
)
def some_operation(target, **params):
    pass
```

---

### Query Methods

#### query_logs

Query audit logs with filters.

**Input**:
```python
def query_logs(
    start_date: date = None,
    end_date: date = None,
    action_type: str = None,
    actor: str = None,
    result: str = None,
    correlation_id: str = None,
    limit: int = 1000
) -> list[AuditEntry]
```

---

#### get_action_summary

Get summary of actions for a period.

**Input**:
```python
def get_action_summary(
    start_date: date,
    end_date: date
) -> dict
```

**Output**:
```python
{
    "total_actions": int,
    "by_type": dict[str, int],
    "by_actor": dict[str, int],
    "by_result": dict[str, int],
    "success_rate": float,
    "avg_duration_ms": float
}
```

---

### Archival Methods

#### archive_old_logs

Archive logs older than retention period.

**Input**:
```python
def archive_old_logs(
    retention_days: int = 90
) -> dict
```

**Output**:
```python
{
    "archived_count": int,
    "archive_size_bytes": int,
    "date_range": str
}
```

---

#### query_archive

Query archived logs.

**Input**:
```python
def query_archive(
    start_date: date,
    end_date: date,
    action_type: str = None
) -> list[AuditEntry]
```

---

## Events

| Event | When | Payload |
|-------|------|---------|
| `error_classified` | Error categorized | category, error |
| `retry_attempted` | Retry in progress | attempt, delay |
| `retry_exhausted` | Max retries reached | operation, error |
| `component_degraded` | Entered degraded | component, reason |
| `component_recovered` | Exited degraded | component |
| `process_started` | Watcher started | name, pid |
| `process_crashed` | Watcher crashed | name, error |
| `process_restarted` | Auto-restart | name, new_pid |
| `max_restarts_exceeded` | Won't restart | name |
| `heartbeat_stale` | Missing heartbeat | component |
| `action_logged` | Audit entry created | action_type |
| `logs_archived` | Old logs archived | count |
