---
name: process-inbox
description: Process all pending items in /Needs_Action folder according to Company_Handbook.md rules. Use when user wants to process the inbox or after new items are detected.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

## Instructions

Process all files in the /Needs_Action folder according to Company_Handbook.md rules.

### Steps

1. **Read Company_Handbook.md**:
   - Load rules from `[VAULT_PATH]/Company_Handbook.md`
   - Extract rules from `### Rule N:` sections
   - Note priority keywords and special handling requirements

2. **List pending items**:
   - List all `.md` files in `/Needs_Action/` folder (including `/Needs_Action/Email/`)
   - Sort by creation time (oldest first - FIFO order)
   - Report count of pending items

3. **For each item**:
   a. **Read the item**:
      - Parse YAML frontmatter for metadata
      - Read content section

   b. **Apply handbook rules**:
      - Check for priority keywords in filename/content
      - Apply any special handling rules
      - Determine action to take

   c. **Process the item**:
      - Update status to "processing"
      - Perform required actions based on item type
      - Update status to "done"
      - Add `processed_at` timestamp

   d. **Move to Done**:
      - Move file from `/Needs_Action/` to `/Done/`
      - Preserve all metadata

   e. **Log the action**:
      - Append entry to `/Logs/claude_YYYY-MM-DD.log`
      - Include: timestamp, action_type, item_id, outcome, duration_ms

4. **Handle errors**:
   - If processing fails, move item to `/Quarantine/`
   - Add error field to frontmatter
   - Log the error

5. **Update Dashboard**:
   - After processing all items, update Dashboard.md
   - Use `/update-dashboard` skill or update directly

6. **Report results**:
   ```
   ## Processing Complete

   - **Items Processed**: [COUNT]
   - **Successful**: [COUNT]
   - **Failed**: [COUNT]
   - **Time Taken**: [DURATION]

   ### Processed Items
   | Item | Action | Result |
   |------|--------|--------|
   | [ITEM] | [ACTION] | [SUCCESS/FAILURE] |
   ```

### Arguments

$ARGUMENTS - Optional filter for specific files to process (e.g., "FILE_*.md" or "EMAIL_*.md")

### Example Log Entry

```json
{"timestamp": "2026-02-03T10:30:00Z", "action_type": "process", "item_id": "FILE_report.pdf.md", "outcome": "success", "duration_ms": 1234, "details": "Processed and moved to Done"}
```

### Error Handling

- If Company_Handbook.md is missing, use default rules
- If item has invalid frontmatter, quarantine it
- If move fails, log error but continue with other items
- Always update Dashboard even if some items failed
