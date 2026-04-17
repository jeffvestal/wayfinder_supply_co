#!/bin/bash
# demo_reset.sh - Reset the MS Build 2026 demo between runs
#
# Handles both first-run setup and between-run resets:
#   1. Closes any existing demo PR
#   2. Restarts backend (resets in-memory inventory + cart state)
#   3. Creates a fresh PR (triggers GitHub Action → Elastic Agent review)
#   4. Polls until the Action run starts, then prints readiness checklist
#
# Prerequisites:
#   - services already running (./scripts/start_local.sh)
#   - gh CLI installed and authenticated (gh auth status)
#   - demo/inventory-refactor branch exists on GitHub
#
# Usage:
#   ./scripts/demo_reset.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DEMO_HEAD="demo/inventory-refactor"
DEMO_BASE="feature/msft-build-2026"
PR_TITLE="Inventory: pre-compute quantity for cache-friendly UPDATE"
PR_BODY_FILE="$SCRIPT_DIR/_demo_pr_body.md"
GITHUB_REPO="jeffvestal/wayfinder_supply_co"

echo -e "${BOLD}${CYAN}=============================================="
echo -e "  Wayfinder Demo Reset — MS Build 2026"
echo -e "==============================================${NC}"
echo ""

# ============================================================
# Prerequisites
# ============================================================
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v gh &> /dev/null; then
    echo -e "${RED}ERROR: gh CLI not found${NC}"
    echo "Install: brew install gh"
    echo "Auth:    gh auth login"
    exit 1
fi

if ! gh auth status &> /dev/null 2>&1; then
    echo -e "${RED}ERROR: gh CLI not authenticated${NC}"
    echo "Run: gh auth login"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} gh CLI authenticated"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: docker not found${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} docker available"

if [ ! -f "$PR_BODY_FILE" ]; then
    echo -e "${RED}ERROR: PR body file not found: $PR_BODY_FILE${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} PR body file present"

# Verify demo branch exists on remote
if ! gh api "repos/$GITHUB_REPO/branches/$DEMO_HEAD" &> /dev/null 2>&1; then
    echo -e "${RED}ERROR: Branch '$DEMO_HEAD' not found on GitHub${NC}"
    echo "This branch must exist before running the demo."
    echo "Check: gh api repos/$GITHUB_REPO/branches"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} $DEMO_HEAD branch exists on GitHub"
echo ""

# ============================================================
# Step 1: Close existing demo PR
# ============================================================
echo -e "${BLUE}Step 1: Checking for existing demo PR...${NC}"

EXISTING_PR=$(gh pr list \
    --repo "$GITHUB_REPO" \
    --head "$DEMO_HEAD" \
    --base "$DEMO_BASE" \
    --state open \
    --json number \
    --jq '.[0].number' 2>/dev/null || true)

if [ -n "$EXISTING_PR" ] && [ "$EXISTING_PR" != "null" ]; then
    echo -e "  Found open PR #$EXISTING_PR — closing..."
    gh pr close "$EXISTING_PR" \
        --repo "$GITHUB_REPO" \
        --comment "Demo reset — closing to create a fresh run." \
        2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} PR #$EXISTING_PR closed"
else
    echo -e "  ${GREEN}✓${NC} No existing demo PR"
fi
echo ""

# ============================================================
# Step 2: Restart backend (resets in-memory state)
# ============================================================
echo -e "${BLUE}Step 2: Restarting backend (resets inventory + cart state)...${NC}"

docker compose restart backend > /dev/null 2>&1

MAX_WAIT=30
WAITED=0
echo -n "  Waiting for backend health..."
while ! curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo -e " ${RED}timeout${NC}"
        echo -e "${RED}Backend failed to come back up. Check: docker compose logs backend${NC}"
        exit 1
    fi
    sleep 1
    WAITED=$((WAITED + 1))
done
echo -e " ${GREEN}ready${NC} (${WAITED}s)"
echo ""

# ============================================================
# Step 3: Create fresh demo PR
# ============================================================
echo -e "${BLUE}Step 3: Creating fresh demo PR...${NC}"

NEW_PR_URL=$(gh pr create \
    --repo "$GITHUB_REPO" \
    --head "$DEMO_HEAD" \
    --base "$DEMO_BASE" \
    --title "$PR_TITLE" \
    --body-file "$PR_BODY_FILE" \
    2>&1)

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to create PR${NC}"
    echo "$NEW_PR_URL"
    exit 1
fi

PR_URL="$NEW_PR_URL"
PR_NUMBER=$(echo "$PR_URL" | grep -oE '[0-9]+$')
echo -e "  ${GREEN}✓${NC} PR #$PR_NUMBER created"
echo ""

# ============================================================
# Step 4: Wait for GitHub Action to trigger
# ============================================================
echo -e "${BLUE}Step 4: Waiting for GitHub Action to trigger...${NC}"

MAX_WAIT=45
WAITED=0
ACTION_RUN_URL=""

while [ $WAITED -lt $MAX_WAIT ]; do
    sleep 3
    WAITED=$((WAITED + 3))

    RUN_INFO=$(gh run list \
        --repo "$GITHUB_REPO" \
        --workflow "elastic-agent-review.yml" \
        --limit 1 \
        --json databaseId,status,url \
        --jq '.[0]' 2>/dev/null || true)

    if [ -n "$RUN_INFO" ] && [ "$RUN_INFO" != "null" ]; then
        RUN_STATUS=$(echo "$RUN_INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null)
        RUN_ID=$(echo "$RUN_INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('databaseId',''))" 2>/dev/null)
        ACTION_RUN_URL="https://github.com/$GITHUB_REPO/actions/runs/$RUN_ID"

        if [ -n "$RUN_STATUS" ]; then
            echo -e "  ${GREEN}✓${NC} Action triggered (status: $RUN_STATUS)"
            break
        fi
    fi

    echo -n "  Still waiting... (${WAITED}s)"
    echo -ne "\r"
done

if [ -z "$ACTION_RUN_URL" ]; then
    echo -e "  ${YELLOW}⚠${NC}  Action run not detected within ${MAX_WAIT}s"
    echo -e "  ${YELLOW}Check manually: https://github.com/$GITHUB_REPO/actions${NC}"
    ACTION_RUN_URL="https://github.com/$GITHUB_REPO/actions"
fi
echo ""

# ============================================================
# Readiness checklist
# ============================================================
ACTIONS_URL="https://github.com/$GITHUB_REPO/actions"

echo -e "${BOLD}${CYAN}=============================================="
echo -e "  Demo Ready!"
echo -e "==============================================${NC}"
echo ""
echo -e "  ${BOLD}Open these browser tabs:${NC}"
echo ""
echo -e "  ${GREEN}[1]${NC} GitHub PR:"
echo -e "      ${CYAN}$PR_URL${NC}"
echo ""
echo -e "  ${GREEN}[2]${NC} GitHub Action run:"
echo -e "      ${CYAN}$ACTION_RUN_URL${NC}"
echo ""
echo -e "  ${GREEN}[3]${NC} Wayfinder app:"
echo -e "      ${CYAN}http://localhost:3000${NC}"
echo ""
echo -e "  ${BOLD}What to expect:${NC}"
echo -e "  • Action runs → calls Elastic Workflow → agent searches incident history"
echo -e "  • Agent posts a review comment on the PR (~30-60s after action starts)"
echo -e "  • No keywords like 'race condition' in the PR or comment — pure semantic match"
echo ""
echo -e "  ${BOLD}Verify bug is live (optional pre-demo check):${NC}"
echo -e "  ${YELLOW}curl -s -X POST http://localhost:8000/api/v1/checkout/reserve \\"
echo -e "    -H 'Content-Type: application/json' \\"
echo -e "    -d '{\"product_id\":\"BOOT-001\",\"quantity\":1,\"user_id\":\"u1\"}' &${NC}"
echo -e "  ${YELLOW}curl -s -X POST http://localhost:8000/api/v1/checkout/reserve \\"
echo -e "    -H 'Content-Type: application/json' \\"
echo -e "    -d '{\"product_id\":\"BOOT-001\",\"quantity\":1,\"user_id\":\"u2\"}' &${NC}"
echo -e "  Both should return ${YELLOW}\"reserved\": true${NC} (oversell = bug confirmed)"
echo ""
