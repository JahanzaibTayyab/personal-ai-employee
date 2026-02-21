#!/bin/bash
# ─── AI Employee Demo Recording Orchestrator ─────────────────────
# Sets up demo data, starts the web server, records terminal GIFs
# with VHS, and runs the Playwright browser walkthrough.
#
# Usage:
#   ./demo/record.sh                  # Run everything
#   ./demo/record.sh --vhs-only       # Only record terminal GIFs
#   ./demo/record.sh --browser-only   # Only run browser walkthrough
#   ./demo/record.sh --setup-only     # Only set up demo vault + server

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VAULT="/tmp/demo_vault"
PORT="${AI_WEB_PORT:-8000}"
OUTPUT_DIR="$SCRIPT_DIR/output"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

cleanup() {
    echo ""
    echo -e "${YELLOW}Cleaning up...${NC}"
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null || true
        echo "  Stopped web server (PID $SERVER_PID)"
    fi
}
trap cleanup EXIT

header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# ─── Parse args ──────────────────────────────────────────────────
MODE="${1:-all}"

mkdir -p "$OUTPUT_DIR"
cd "$PROJECT_DIR"

# ═══════════════════════════════════════════════════════════════════
# Phase 1: Set up demo vault
# ═══════════════════════════════════════════════════════════════════
setup_vault() {
    header "Phase 1: Setting up demo vault"
    bash scripts/demo_setup.sh "$VAULT"
}

# ═══════════════════════════════════════════════════════════════════
# Phase 2: Start web server
# ═══════════════════════════════════════════════════════════════════
start_server() {
    header "Phase 2: Starting web dashboard"

    # Kill any existing server on the port
    lsof -ti :"$PORT" | xargs kill 2>/dev/null || true
    sleep 1

    VAULT_PATH="$VAULT" uv run ai-employee web --host 127.0.0.1 --port "$PORT" &
    SERVER_PID=$!
    echo "  Web server starting (PID $SERVER_PID)..."

    # Wait for server to be ready
    for i in $(seq 1 30); do
        if curl -s "http://127.0.0.1:$PORT/api/health" > /dev/null 2>&1; then
            echo -e "  ${GREEN}Server ready at http://127.0.0.1:$PORT${NC}"
            return 0
        fi
        sleep 1
    done
    echo -e "  ${RED}Server failed to start!${NC}"
    return 1
}

# ═══════════════════════════════════════════════════════════════════
# Phase 3: Record terminal GIFs with VHS
# ═══════════════════════════════════════════════════════════════════
record_vhs() {
    header "Phase 3: Recording terminal GIFs with VHS"

    if ! command -v vhs &> /dev/null; then
        echo -e "${YELLOW}VHS not installed. Install with: brew install vhs${NC}"
        echo "  Skipping terminal recordings."
        return 0
    fi

    for tape in demo/01-init.tape demo/02-tests.tape demo/03-cli.tape demo/04-pm2.tape; do
        if [ -f "$tape" ]; then
            name=$(basename "$tape" .tape)
            echo -e "  ${YELLOW}Recording: $name${NC}"
            vhs "$tape" 2>&1 | tail -5 || echo "    (VHS recording had warnings)"
            echo ""
        fi
    done

    echo -e "  ${GREEN}Terminal recordings saved to $OUTPUT_DIR/${NC}"
}

# ═══════════════════════════════════════════════════════════════════
# Phase 4: Run Playwright browser walkthrough
# ═══════════════════════════════════════════════════════════════════
run_browser() {
    header "Phase 4: Running Playwright browser walkthrough"

    if ! python -c "import playwright" 2>/dev/null; then
        echo -e "${YELLOW}Playwright not installed. Install with:${NC}"
        echo "  pip install playwright && playwright install chromium"
        echo "  Skipping browser walkthrough."
        return 0
    fi

    echo "  Starting automated browser walkthrough..."
    echo "  (The browser will open — this is your demo. Screen-record it!)"
    echo ""

    python demo/browser_walkthrough.py --screenshots "$OUTPUT_DIR"
    echo ""
    echo -e "  ${GREEN}Browser walkthrough complete!${NC}"
}

# ═══════════════════════════════════════════════════════════════════
# Run based on mode
# ═══════════════════════════════════════════════════════════════════
case "$MODE" in
    --vhs-only)
        setup_vault
        record_vhs
        ;;
    --browser-only)
        setup_vault
        start_server
        run_browser
        ;;
    --setup-only)
        setup_vault
        start_server
        echo ""
        echo -e "${GREEN}Demo vault and server ready.${NC}"
        echo "  Dashboard: http://127.0.0.1:$PORT"
        echo ""
        echo "  Press Ctrl+C to stop the server."
        wait "$SERVER_PID"
        ;;
    all)
        setup_vault
        start_server
        record_vhs
        run_browser
        ;;
    *)
        echo "Usage: $0 [--vhs-only|--browser-only|--setup-only]"
        exit 1
        ;;
esac

# ═══════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════
header "Recording Complete!"

echo "  Output files in: $OUTPUT_DIR/"
echo ""
if [ -d "$OUTPUT_DIR" ]; then
    ls -lh "$OUTPUT_DIR/" 2>/dev/null | tail -20
fi
echo ""
echo -e "  ${YELLOW}Next steps:${NC}"
echo "    1. Open your screen recording (OBS/QuickTime)"
echo "    2. Follow demo/VIDEO_SCRIPT.md for narration"
echo "    3. Use the terminal GIFs + browser screenshots in your video"
echo ""
