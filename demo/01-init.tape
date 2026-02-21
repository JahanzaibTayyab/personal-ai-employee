# VHS Tape: Vault Initialization
# Records: ai-employee init creating the vault structure
# Output: demo/output/01-init.gif

Output demo/output/01-init.gif
Set Shell "zsh"
Set FontSize 16
Set Width 1200
Set Height 700
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms

Sleep 500ms

Type "# Initialize the AI Employee Vault"
Enter
Sleep 1s

Type "uv run ai-employee init --vault /tmp/demo_vault"
Enter
Sleep 3s

Type ""
Enter
Type "# Vault structure created! Let's see what's inside:"
Enter
Sleep 500ms

Type "tree /tmp/demo_vault -L 2 --dirsfirst"
Enter
Sleep 3s

Type ""
Enter
Type "# The vault is our AI Employee's knowledge base"
Enter
Type "# Every folder has a purpose — Inbox, Done, Plans, Briefings..."
Enter
Sleep 2s

Type ""
Enter
Type "# Let's populate it with demo data"
Enter
Sleep 500ms

Type "./scripts/demo_setup.sh /tmp/demo_vault"
Enter
Sleep 4s

Type ""
Enter
Type "# Now let's see the full vault with data:"
Enter
Sleep 500ms

Type "tree /tmp/demo_vault -L 3 --dirsfirst | head -60"
Enter
Sleep 4s

Sleep 2s
