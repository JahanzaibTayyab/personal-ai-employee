# VHS Tape: CLI Commands
# Records: Various CLI commands showing functionality
# Output: demo/output/03-cli.gif

Output demo/output/03-cli.gif
Set Shell "zsh"
Set FontSize 16
Set Width 1200
Set Height 700
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms

Sleep 500ms

Type "# AI Employee CLI — all commands"
Enter
Sleep 500ms

Type "uv run ai-employee --help"
Enter
Sleep 2s

Type ""
Enter
Type "# Generate the Dashboard.md report"
Enter
Sleep 500ms

Type "uv run ai-employee dashboard --vault /tmp/demo_vault"
Enter
Sleep 3s

Type ""
Enter
Type "# View the generated dashboard:"
Enter
Sleep 500ms

Type "cat /tmp/demo_vault/Dashboard.md"
Enter
Sleep 4s

Type ""
Enter
Type "# Scheduler — view all scheduled tasks"
Enter
Sleep 500ms

Type "uv run ai-employee scheduler --vault /tmp/demo_vault list"
Enter
Sleep 3s

Type ""
Enter
Type "# Set up default schedules (daily briefing + weekly audit)"
Enter
Sleep 500ms

Type "uv run ai-employee scheduler --vault /tmp/demo_vault setup-defaults"
Enter
Sleep 3s

Type ""
Enter
Type "# List schedules again to see the new defaults"
Enter
Sleep 500ms

Type "uv run ai-employee scheduler --vault /tmp/demo_vault list"
Enter
Sleep 3s

Sleep 2s
