#!/bin/bash
# ─── AI Employee Startup Script ──────────────────────────────────
# Starts all watchers and the web dashboard using PM2.
#
# Usage:
#   ./scripts/start.sh                   # Start everything
#   ./scripts/start.sh --only bronze     # Bronze tier only
#   ./scripts/start.sh --only silver     # Silver tier (includes Bronze)
#   ./scripts/start.sh --only dashboard  # Web dashboard only
#
# Prerequisites:
#   npm install -g pm2
#   uv sync --all-extras

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VAULT="${AI_VAULT:-$HOME/AI_Employee_Vault}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  AI Employee — Starting Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check prerequisites
if ! command -v pm2 &> /dev/null; then
    echo -e "${RED}PM2 not found. Install it:${NC}"
    echo "  npm install -g pm2"
    exit 1
fi

if ! command -v uv &> /dev/null; then
    echo -e "${RED}UV not found. Install it:${NC}"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check vault exists
if [ ! -d "$VAULT" ]; then
    echo -e "${YELLOW}Vault not found at $VAULT${NC}"
    echo -e "Initializing vault..."
    cd "$PROJECT_DIR" && uv run ai-employee init --vault "$VAULT"
    echo ""
fi

echo -e "  Vault:   ${GREEN}$VAULT${NC}"
echo -e "  Project: ${GREEN}$PROJECT_DIR${NC}"
echo ""

cd "$PROJECT_DIR"

TIER="${1:-all}"

case "$TIER" in
    --only)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: --only requires a tier argument (bronze|silver|gold|dashboard)${NC}"
            echo "Usage: $0 [--only bronze|silver|gold|dashboard]"
            exit 1
        fi
        TIER="$2"
        ;;
esac

case "$TIER" in
    bronze)
        echo -e "${YELLOW}Starting Bronze tier...${NC}"
        pm2 start ecosystem.config.cjs --only file-watcher
        pm2 start ecosystem.config.cjs --only gmail-watcher
        ;;
    silver)
        echo -e "${YELLOW}Starting Silver tier (includes Bronze)...${NC}"
        pm2 start ecosystem.config.cjs --only file-watcher
        pm2 start ecosystem.config.cjs --only gmail-watcher
        pm2 start ecosystem.config.cjs --only approval-watcher
        pm2 start ecosystem.config.cjs --only whatsapp-watcher
        pm2 start ecosystem.config.cjs --only web-dashboard
        ;;
    dashboard)
        echo -e "${YELLOW}Starting web dashboard only...${NC}"
        pm2 start ecosystem.config.cjs --only web-dashboard
        ;;
    all|gold)
        echo -e "${YELLOW}Starting all services (Gold tier)...${NC}"
        pm2 start ecosystem.config.cjs
        ;;
    *)
        echo -e "${RED}Unknown tier: $TIER${NC}"
        echo "Usage: $0 [--only bronze|silver|gold|dashboard]"
        exit 1
        ;;
esac

echo ""
pm2 status

echo ""
echo -e "${GREEN}${TIER^} services started.${NC}"
echo ""
echo -e "  Dashboard: ${BLUE}http://127.0.0.1:${AI_WEB_PORT:-8000}${NC}"
echo ""
echo -e "  ${YELLOW}Commands:${NC}"
echo "    pm2 status        # Check all processes"
echo "    pm2 logs          # View all logs"
echo "    pm2 logs <name>   # View specific process logs"
echo "    pm2 restart all   # Restart everything"
echo "    ./scripts/stop.sh # Stop everything"
echo ""
echo -e "  ${YELLOW}Survive reboots:${NC}"
echo "    pm2 save"
echo "    pm2 startup"
