# VHS Tape: PM2 24/7 Operation
# Records: Starting/stopping services with PM2
# Output: demo/output/04-pm2.gif

Output demo/output/04-pm2.gif
Set Shell "zsh"
Set FontSize 15
Set Width 1200
Set Height 800
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms

Sleep 500ms

Type "# 24/7 Operation with PM2 Process Manager"
Enter
Sleep 1s

Type "# Start all services (Gold tier)"
Enter
Sleep 500ms

Type "AI_VAULT=/tmp/demo_vault ./scripts/start.sh --only gold"
Enter
Sleep 8s

Type ""
Enter
Type "# All 5 processes running! Let's check status:"
Enter
Sleep 500ms

Type "pm2 status"
Enter
Sleep 3s

Type ""
Enter
Type "# View recent logs from all processes:"
Enter
Sleep 500ms

Type "pm2 logs --lines 5 --nostream"
Enter
Sleep 3s

Type ""
Enter
Type "# System health check:"
Enter
Sleep 500ms

Type "AI_VAULT=/tmp/demo_vault ./scripts/status.sh"
Enter
Sleep 4s

Type ""
Enter
Type "# Survive reboots:"
Enter
Sleep 500ms

Type "# pm2 save && pm2 startup"
Enter
Sleep 2s

Type ""
Enter
Type "# Clean stop all services:"
Enter
Sleep 500ms

Type "./scripts/stop.sh"
Enter
Sleep 5s

Sleep 2s
