#!/bin/bash
# Initialize Silver Tier AI Employee Vault structure
# Usage: ./scripts/init_vault_silver.sh [VAULT_PATH]
# Extends Bronze tier vault with approval workflow, planning, and scheduling folders

set -e

VAULT_PATH="${1:-$HOME/AI_Employee_Vault}"

echo "Initializing Silver Tier AI Employee Vault at: $VAULT_PATH"

# First, run Bronze tier initialization
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/init_vault.sh" ]; then
    bash "$SCRIPT_DIR/init_vault.sh" "$VAULT_PATH"
fi

# Create Silver tier directories
echo ""
echo "Adding Silver tier folders..."

# Approval workflow folders
mkdir -p "$VAULT_PATH/Pending_Approval"
mkdir -p "$VAULT_PATH/Approved"
mkdir -p "$VAULT_PATH/Rejected"

# Planning folder
mkdir -p "$VAULT_PATH/Plans"

# WhatsApp actions folder
mkdir -p "$VAULT_PATH/Needs_Action/WhatsApp"

# LinkedIn folders
mkdir -p "$VAULT_PATH/Social/LinkedIn/posts"

# Scheduling folders
mkdir -p "$VAULT_PATH/Briefings"
mkdir -p "$VAULT_PATH/Schedules"

# Create engagement.md for LinkedIn if not exists
if [ ! -f "$VAULT_PATH/Social/LinkedIn/engagement.md" ]; then
    cat > "$VAULT_PATH/Social/LinkedIn/engagement.md" << 'EOF'
# LinkedIn Engagement Log

This file tracks engagement metrics for LinkedIn posts.

## Recent Engagement

| Date | Post | Type | Author | Content | Follow-up Required |
|------|------|------|--------|---------|-------------------|
| - | - | - | - | - | - |

---
*Auto-updated by AI Employee*
EOF
    echo "Created Social/LinkedIn/engagement.md"
fi

echo ""
echo "Silver tier folders added:"
echo "  - Pending_Approval/"
echo "  - Approved/"
echo "  - Rejected/"
echo "  - Plans/"
echo "  - Needs_Action/WhatsApp/"
echo "  - Social/LinkedIn/posts/"
echo "  - Briefings/"
echo "  - Schedules/"
echo ""
echo "Silver tier vault ready!"
echo ""
echo "Silver tier commands:"
echo "  - Watch approvals: uv run ai-employee watch-approvals --vault $VAULT_PATH"
echo "  - Watch WhatsApp: uv run ai-employee watch-whatsapp --vault $VAULT_PATH"
echo "  - Start scheduler: uv run ai-employee scheduler --vault $VAULT_PATH"
