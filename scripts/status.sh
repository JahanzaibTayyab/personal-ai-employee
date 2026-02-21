#!/bin/bash
# ─── AI Employee Status Script ────────────────────────────────────
# Shows status of all AI Employee services and vault health.
#
# Usage:
#   ./scripts/status.sh

VAULT="${AI_VAULT:-$HOME/AI_Employee_Vault}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  AI Employee — System Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# PM2 Status
echo -e "${YELLOW}Process Manager (PM2):${NC}"
if command -v pm2 &> /dev/null; then
    pm2 jlist 2>/dev/null | python3 -c "
import json, sys
try:
    procs = json.load(sys.stdin)
    names = ['file-watcher','gmail-watcher','approval-watcher','whatsapp-watcher','web-dashboard']
    found = {p['name']: p for p in procs if p['name'] in names}
    for name in names:
        if name in found:
            p = found[name]
            status = p['pm2_env']['status']
            restarts = p['pm2_env']['restart_time']
            uptime = p['pm2_env'].get('pm_uptime', 0)
            color = '\033[0;32m' if status == 'online' else '\033[0;31m'
            print(f'  {color}{status:8s}\033[0m  {name:20s}  restarts: {restarts}')
        else:
            print(f'  \033[0;33mnot set \033[0m  {name:20s}')
except:
    print('  No AI Employee processes found in PM2')
" 2>/dev/null || echo "  PM2 is installed but no processes found"
else
    echo -e "  ${RED}PM2 not installed${NC} — install with: npm install -g pm2"
fi

echo ""

# Vault Status
echo -e "${YELLOW}Vault Health:${NC}"
if [ -d "$VAULT" ]; then
    echo -e "  Path: ${GREEN}$VAULT${NC}"

    inbox=$(find "$VAULT/Inbox" -type f 2>/dev/null | wc -l | tr -d ' ')
    needs_action=$(find "$VAULT/Needs_Action" -type f 2>/dev/null | wc -l | tr -d ' ')
    done_count=$(find "$VAULT/Done" -type f 2>/dev/null | wc -l | tr -d ' ')
    quarantine=$(find "$VAULT/Quarantine" -type f 2>/dev/null | wc -l | tr -d ' ')
    pending=$(find "$VAULT/Pending_Approval" -type f 2>/dev/null | wc -l | tr -d ' ')
    plans=$(find "$VAULT/Plans" -type f 2>/dev/null | wc -l | tr -d ' ')
    briefings=$(find "$VAULT/Briefings" -type f 2>/dev/null | wc -l | tr -d ' ')
    tasks=$(find "$VAULT/Active_Tasks" -type f 2>/dev/null | wc -l | tr -d ' ')

    echo "  Inbox:            $inbox"
    echo "  Needs Action:     $needs_action"
    echo "  Done:             $done_count"
    echo "  Quarantine:       $quarantine"
    echo "  Pending Approval: $pending"
    echo "  Active Plans:     $plans"
    echo "  Briefings:        $briefings"
    echo "  Active Tasks:     $tasks"
else
    echo -e "  ${RED}Vault not found at $VAULT${NC}"
    echo "  Initialize: uv run ai-employee init --vault $VAULT"
fi

echo ""

# Web Dashboard
echo -e "${YELLOW}Web Dashboard:${NC}"
PORT="${AI_WEB_PORT:-8000}"
if curl -s "http://127.0.0.1:$PORT/api/health" > /dev/null 2>&1; then
    echo -e "  ${GREEN}Running${NC} at http://127.0.0.1:$PORT"
else
    echo -e "  ${RED}Not running${NC} on port $PORT"
fi

echo ""

# Recent logs
echo -e "${YELLOW}Recent Activity (last 5 log entries):${NC}"
TODAY=$(date +%Y-%m-%d)
LOG_FILE="$VAULT/Logs/claude_${TODAY}.log"
if [ -f "$LOG_FILE" ]; then
    tail -5 "$LOG_FILE" 2>/dev/null | while IFS= read -r line; do
        echo "  $line"
    done
else
    echo "  No activity logs for today"
fi

echo ""
