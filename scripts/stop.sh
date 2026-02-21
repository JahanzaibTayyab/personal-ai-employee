#!/bin/bash
# ─── AI Employee Stop Script ─────────────────────────────────────
# Stops all AI Employee PM2 processes.
#
# Usage:
#   ./scripts/stop.sh              # Stop all
#   ./scripts/stop.sh file-watcher # Stop specific process

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  AI Employee — Stopping Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if ! command -v pm2 &> /dev/null; then
    echo "PM2 not found. Nothing to stop."
    exit 0
fi

if [ -n "$1" ]; then
    echo "Stopping $1..."
    pm2 stop "$1" 2>/dev/null || true
else
    echo "Stopping all AI Employee services..."
    pm2 stop file-watcher gmail-watcher approval-watcher whatsapp-watcher web-dashboard 2>/dev/null || true
fi

echo ""
pm2 status
echo ""
echo -e "${GREEN}Services stopped.${NC}"
echo "  To restart: ./scripts/start.sh"
echo "  To delete from PM2: pm2 delete all"
