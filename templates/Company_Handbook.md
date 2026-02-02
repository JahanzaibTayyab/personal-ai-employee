# Company Handbook

This handbook defines the rules and guidelines that govern how your AI Employee processes items. Edit these rules to customize the AI's behavior to match your preferences.

## Rules

### Rule 1: Priority Keywords
When processing items, check for these keywords and set priority:
- "urgent", "asap", "emergency" → priority: urgent
- "important", "priority" → priority: high
- "low priority", "when you can" → priority: low

### Rule 2: Large File Handling
Files larger than 10MB should be flagged for manual review and moved to Quarantine with a note.

### Rule 3: Default Behavior
Process all items in order received (FIFO - First In, First Out). Log all actions to the activity log.

### Rule 4: Email Handling
When processing emails:
- Summarize the key points
- Identify any action items requested
- Note the sender and date
- Flag if response is needed

### Rule 5: File Type Processing
- **Text files (.txt, .md)**: Extract content for processing
- **PDFs (.pdf)**: Note filename and metadata only
- **Images (.png, .jpg)**: Note filename and size
- **Data files (.csv, .json)**: Note structure and row/key count

### Rule 6: Error Recovery
If an error occurs during processing:
- Log the error with details
- Move the item to Quarantine
- Continue processing remaining items
- Report errors in the Dashboard warnings section

## Contact Information

**Owner**: [Your Name]
**Email**: [Your Email]
**Last Updated**: [Date]

## Notes

- Rules are applied in order (Rule 1 takes precedence over Rule 2, etc.)
- Add new rules by creating ### Rule N: sections
- The AI will re-read this handbook before each processing session
