# VHS Tape: Test Suite
# Records: Running the full test suite (821 tests)
# Output: demo/output/02-tests.gif

Output demo/output/02-tests.gif
Set Shell "zsh"
Set FontSize 15
Set Width 1200
Set Height 800
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms

Sleep 500ms

Type "# Run the full test suite — 821 tests across all tiers"
Enter
Sleep 1s

Type "uv run pytest --tb=short -q"
Enter
Sleep 60s

Type ""
Enter
Type "# All tests passing! Let's check coverage:"
Enter
Sleep 500ms

Type "uv run pytest --cov=ai_employee --cov-report=term-missing -q 2>&1 | tail -30"
Enter
Sleep 90s

Sleep 2s
