#!/bin/bash
# control.sh — MS Build 2026 demo control
#
# Usage:
#   ./control.sh setup    # cold start: services down, first run of the day
#   ./control.sh reset    # between Navattic takes (services already running)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

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
PR_BODY_FILE="$SCRIPT_DIR/scripts/_demo_pr_body.md"
GITHUB_REPO="jeffvestal/wayfinder_supply_co"
KIBANA_URL="https://wayfinder-supply-co-aa4128.kb.us-central1.gcp.elastic.cloud"

# ============================================================
# Shared helpers
# ============================================================

_load_env() {
    if [ ! -f .env ]; then
        echo -e "${RED}ERROR: .env not found${NC}"
        exit 1
    fi
    set -a; source .env; set +a 2>/dev/null || true
}

_check_prereqs() {
    if ! command -v gh &> /dev/null; then
        echo -e "${RED}ERROR: gh CLI not found — brew install gh${NC}"; exit 1
    fi
    if ! gh auth status &> /dev/null 2>&1; then
        echo -e "${RED}ERROR: gh not authenticated — gh auth login${NC}"; exit 1
    fi
    echo -e "  ${GREEN}✓${NC} gh authenticated"

    if ! command -v docker &> /dev/null || ! docker info &> /dev/null 2>&1; then
        echo -e "${RED}ERROR: Docker not running${NC}"; exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Docker running"

    if [ ! -f "$PR_BODY_FILE" ]; then
        echo -e "${RED}ERROR: PR body file not found: $PR_BODY_FILE${NC}"; exit 1
    fi
    echo -e "  ${GREEN}✓${NC} PR body file present"

    if ! gh api "repos/$GITHUB_REPO/branches/$DEMO_HEAD" &> /dev/null 2>&1; then
        echo -e "${RED}ERROR: Branch '$DEMO_HEAD' not found on GitHub${NC}"; exit 1
    fi
    echo -e "  ${GREEN}✓${NC} $DEMO_HEAD branch on GitHub"
}

_wait_backend() {
    local max=30 waited=0
    echo -n "  Waiting for backend..."
    while ! curl -sf http://localhost:8000/health > /dev/null 2>&1; do
        if [ $waited -ge $max ]; then
            echo -e " ${RED}timeout${NC}"
            echo -e "${RED}Backend failed. Check: docker compose logs backend${NC}"
            exit 1
        fi
        sleep 1; waited=$((waited + 1))
    done
    echo -e " ${GREEN}ready${NC} (${waited}s)"
}

_do_reset() {
    # Step 1: close existing demo PR
    echo -e "${BLUE}Closing existing demo PR (if any)...${NC}"
    EXISTING_PR=$(gh pr list \
        --repo "$GITHUB_REPO" \
        --head "$DEMO_HEAD" \
        --base "$DEMO_BASE" \
        --state open \
        --json number \
        --jq '.[0].number' 2>/dev/null || true)

    if [ -n "$EXISTING_PR" ] && [ "$EXISTING_PR" != "null" ]; then
        gh pr close "$EXISTING_PR" \
            --repo "$GITHUB_REPO" \
            --comment "Demo reset — closing to create a fresh run." \
            2>/dev/null || true
        echo -e "  ${GREEN}✓${NC} PR #$EXISTING_PR closed"
    else
        echo -e "  ${GREEN}✓${NC} No existing demo PR"
    fi

    # Step 2: restart backend
    echo -e "${BLUE}Restarting backend (resets inventory)...${NC}"
    docker compose restart backend > /dev/null 2>&1
    _wait_backend

    # Step 3: create fresh PR
    echo -e "${BLUE}Creating fresh demo PR...${NC}"
    if ! NEW_PR_URL=$(gh pr create \
        --repo "$GITHUB_REPO" \
        --head "$DEMO_HEAD" \
        --base "$DEMO_BASE" \
        --title "$PR_TITLE" \
        --body-file "$PR_BODY_FILE" 2>&1); then
        echo -e "${RED}ERROR: Failed to create PR${NC}"
        echo "$NEW_PR_URL"
        exit 1
    fi
    PR_URL="$NEW_PR_URL"
    PR_NUMBER=$(echo "$PR_URL" | grep -oE '[0-9]+$')
    echo -e "  ${GREEN}✓${NC} PR #$PR_NUMBER created"

    # Step 4: wait for GitHub Action to trigger
    echo -e "${BLUE}Waiting for GitHub Action to trigger...${NC}"
    local max=45 waited=0
    ACTION_RUN_URL=""
    while [ $waited -lt $max ]; do
        sleep 3; waited=$((waited + 3))
        RUN_INFO=$(gh run list \
            --repo "$GITHUB_REPO" \
            --workflow "pr-review.yml" \
            --limit 1 \
            --json databaseId,status \
            --jq '.[0]' 2>/dev/null || true)
        if [ -n "$RUN_INFO" ] && [ "$RUN_INFO" != "null" ]; then
            RUN_ID=$(echo "$RUN_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('databaseId',''))" 2>/dev/null)
            RUN_STATUS=$(echo "$RUN_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
            if [ -n "$RUN_ID" ]; then
                ACTION_RUN_URL="https://github.com/$GITHUB_REPO/actions/runs/$RUN_ID"
                echo -e "  ${GREEN}✓${NC} Action triggered (status: $RUN_STATUS)"
                break
            fi
        fi
        echo -ne "  Still waiting... (${waited}s)\r"
    done
    if [ -z "$ACTION_RUN_URL" ]; then
        echo -e "  ${YELLOW}⚠${NC}  Action not detected within ${max}s"
        ACTION_RUN_URL="https://github.com/$GITHUB_REPO/actions"
    fi
    echo ""
}

_print_ready() {
    echo -e "${BOLD}${CYAN}=============================================="
    echo -e "  DEMO READY"
    echo -e "==============================================${NC}"
    echo ""
    echo -e "  ${BOLD}BROWSER — open these tabs:${NC}"
    echo ""
    echo -e "  ${GREEN}[1]${NC} PR:      ${CYAN}${PR_URL}${NC}"
    echo -e "  ${GREEN}[2]${NC} Action:  ${CYAN}${ACTION_RUN_URL}${NC}"
    echo -e "  ${GREEN}[3]${NC} Kibana:  ${CYAN}${KIBANA_URL}${NC}"
    echo -e "             → AI → Agent Builder → msbuild-pr-review-agent"
    echo ""
    echo -e "  ${BOLD}VS CODE:${NC}"
    echo -e "  Branch: ${YELLOW}demo/inventory-refactor${NC}"
    echo -e "  File:   ${YELLOW}backend/services/inventory_service.py${NC}"
    echo ""
    echo -e "  Run in VS Code terminal:"
    echo -e "    ${CYAN}git checkout demo/inventory-refactor${NC}"
    echo ""
    echo -e "  ${BOLD}Copilot Agent Mode prompt:${NC}"
    echo -e "  ${YELLOW}I got a PR comment on this inventory.reserve change saying it"
    echo -e "  matches a trace pattern from 6 weeks ago. Pull those traces and"
    echo -e "  help me understand what I need to fix.${NC}"
    echo ""
    echo -e "${CYAN}==============================================${NC}"
}

# ============================================================
# Commands
# ============================================================

cmd_setup() {
    echo -e "${BOLD}${CYAN}=============================================="
    echo -e "  control.sh setup — cold start"
    echo -e "==============================================${NC}"
    echo ""

    echo -e "${BLUE}Checking prerequisites...${NC}"
    _load_env
    _check_prereqs
    echo ""

    # Start services
    echo -e "${BLUE}Starting Docker services...${NC}"
    docker compose up -d
    echo -e "  ${GREEN}✓${NC} Services started"
    echo ""

    # Wait for backend and MCP
    _wait_backend
    echo -n "  Waiting for MCP server..."
    for i in $(seq 1 30); do
        if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
            echo -e " ${GREEN}ready${NC}"; break
        fi
        if [ $i -eq 30 ]; then echo -e " ${RED}timeout${NC}"; exit 1; fi
        sleep 1
    done
    echo ""

    # Check trace data
    echo -e "${BLUE}Checking trace data...${NC}"
    ES_COUNT=$(curl -sf \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        "${ELASTIC_URL}/traces-apm.wayfinder-default/_count" \
        2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo "0")

    if [ "$ES_COUNT" -gt 200000 ] 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Trace data loaded (${ES_COUNT} docs)"
    else
        echo -e "  ${YELLOW}⚠${NC}  Trace data missing or low (count=${ES_COUNT}) — loading now..."
        make msbuild-traces
        make msbuild-index-traces
        echo -e "  ${GREEN}✓${NC} Trace data loaded"
    fi
    echo ""

    # Run reset logic
    _do_reset
    _print_ready
}

cmd_reset() {
    echo -e "${BOLD}${CYAN}=============================================="
    echo -e "  control.sh reset — between takes"
    echo -e "==============================================${NC}"
    echo ""

    echo -e "${BLUE}Checking prerequisites...${NC}"
    _load_env
    _check_prereqs
    echo ""

    _do_reset
    _print_ready
}

# ============================================================
# Entry point
# ============================================================

case "${1:-}" in
    setup)  cmd_setup ;;
    reset)  cmd_reset ;;
    *)
        echo "Usage: $0 <command>"
        echo ""
        echo "  setup   Cold start — starts Docker, checks data, resets demo"
        echo "  reset   Between takes — restarts backend, creates fresh PR"
        echo ""
        exit 1
        ;;
esac
