---
name: check-watcher-health
description: Verify that the file watcher is running and healthy. Use when user asks about watcher status or to diagnose issues.
allowed-tools: Read, Bash, Glob, Grep
---

## Instructions

Check the health and status of the AI Employee file watcher.

### Steps

1. **Identify the vault path**:
   - Check environment variable `VAULT_PATH` or use default `~/AI_Employee_Vault`

2. **Check for watcher process**:
   - Run: `ps aux | grep "ai-employee watch" | grep -v grep`
   - If found, watcher process is running

3. **Check watcher log file**:
   - Look for `/Logs/watcher_YYYY-MM-DD.log` (today's date)
   - Check if file exists
   - Check file modification time

4. **Analyze recent events**:
   - Read last 10 lines of watcher log
   - Look for:
     - `"event_type": "started"` - Watcher started
     - `"event_type": "created"` - Files detected
     - `"event_type": "error"` - Errors occurred

5. **Check Drop folder**:
   - List files in `/Drop/` folder
   - If files exist and watcher is "running", there may be an issue

6. **Report status**:

```
## Watcher Health Report

**Status**: [Running/Stopped/Unknown]
**Process**: [Found/Not Found]
**Last Activity**: [TIMESTAMP or "No recent activity"]
**Today's Events**: [COUNT]
**Errors Today**: [COUNT]
**Drop Folder**: [EMPTY/N files pending]

### Recent Events
[Last 5 events from log]

### Recommendations
[Any issues found and suggested actions]
```

### Arguments

$ARGUMENTS - Optional vault path override

### Common Issues

1. **Watcher not running**: Start with `uv run ai-employee watch --vault [PATH]`
2. **Files stuck in Drop**: Watcher may have crashed, check logs and restart
3. **High error rate**: Check Quarantine folder for problematic files
4. **No log file**: Watcher hasn't been started today
