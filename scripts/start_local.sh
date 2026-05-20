#!/bin/bash
# start_local.sh - Launch Wayfinder Supply Co. for standalone demo with ngrok tunnels
#
# This script:
# 1. Validates prerequisites (ngrok, Docker, .env)
# 2. Starts Docker Compose services
# 3. Waits for services to be healthy
# 4. Launches ngrok tunnels so Elastic Cloud workflows can reach local services
# 5. Redeploys workflows and agents with the ngrok tunnel URLs
#
# Prerequisites:
#   - ngrok installed and authenticated (ngrok config add-authtoken <token>)
#   - Docker and docker compose available
#   - .env file configured with STANDALONE_* credentials
#
# Usage:
#   ./scripts/start_local.sh [--load-data] [--skip-tunnel] [--rebuild]

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

# Parse arguments
LOAD_DATA=false
SKIP_TUNNEL=false
REBUILD=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --load-data)
            LOAD_DATA=true
            shift
            ;;
        --skip-tunnel)
            SKIP_TUNNEL=true
            shift
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Launch Wayfinder Supply Co. for standalone demo with ngrok tunnels."
            echo ""
            echo "Options:"
            echo "  --load-data     Load/reload data into Elasticsearch before starting"
            echo "  --skip-tunnel   Skip ngrok tunnel (workflows won't work from Elastic Cloud)"
            echo "  --rebuild       Force rebuild Docker images before starting"
            echo "  --help, -h      Show this help"
            echo ""
            echo "Prerequisites:"
            echo "  - ngrok installed: brew install ngrok"
            echo "  - ngrok authenticated: ngrok config add-authtoken <token>"
            echo "  - .env configured with STANDALONE_* credentials"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Run '$0 --help' for usage"
            exit 1
            ;;
    esac
done

echo -e "${BOLD}${CYAN}=============================================="
echo -e "  Wayfinder Supply Co. - Local Demo Launcher"
echo -e "==============================================${NC}"
echo ""

# ============================================================
# Step 1: Validate prerequisites
# ============================================================
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check .env
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: .env file not found${NC}"
    echo "Copy .env.example to .env and configure STANDALONE_* variables"
    exit 1
fi

# Load env
export $(grep -v '^#' .env | grep -v '^\s*$' | xargs 2>/dev/null) || true

if [ -z "$STANDALONE_ELASTICSEARCH_URL" ] || [ -z "$STANDALONE_ELASTICSEARCH_APIKEY" ] || [ -z "$STANDALONE_KIBANA_URL" ]; then
    echo -e "${RED}ERROR: Required STANDALONE_* variables not set in .env${NC}"
    echo "Required: STANDALONE_ELASTICSEARCH_URL, STANDALONE_ELASTICSEARCH_APIKEY, STANDALONE_KIBANA_URL"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} .env configured"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: docker not found${NC}"
    echo "Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
if ! docker info &> /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker daemon not running${NC}"
    echo "Start Docker Desktop or the Docker daemon"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Docker available"

# Check ngrok (unless skipping tunnel)
if [ "$SKIP_TUNNEL" = false ]; then
    if ! command -v ngrok &> /dev/null; then
        echo -e "${RED}ERROR: ngrok not found${NC}"
        echo "Install: brew install ngrok"
        echo "Authenticate: ngrok config add-authtoken <your-token>"
        echo "Or run with --skip-tunnel to skip (workflows won't work from Elastic Cloud)"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} ngrok available"
fi

echo ""

# ============================================================
# Step 2: Start Docker services
# ============================================================
echo -e "${BOLD}${CYAN}Starting Docker services...${NC}"

if [ "$REBUILD" = true ]; then
    echo -e "${YELLOW}Rebuilding images...${NC}"
    docker compose build
fi

docker compose up -d

echo -e "${GREEN}✓${NC} Docker services started"
echo ""

# ============================================================
# Step 3: Wait for services to be healthy
# ============================================================
echo -e "${BLUE}Waiting for services to be ready...${NC}"

# Wait for MCP server
echo -n "  MCP server (port 8001)..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
        echo -e " ${GREEN}ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e " ${RED}timeout${NC}"
        echo -e "${RED}MCP server failed to start. Check: docker compose logs mcp-server${NC}"
        exit 1
    fi
    sleep 1
done

# Wait for backend
echo -n "  Backend (port 8000)..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo -e " ${GREEN}ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e " ${RED}timeout${NC}"
        echo -e "${RED}Backend failed to start. Check: docker compose logs backend${NC}"
        exit 1
    fi
    sleep 1
done

echo ""

# ============================================================
# Step 4: Load data (optional)
# ============================================================
if [ "$LOAD_DATA" = true ]; then
    echo -e "${BOLD}${CYAN}Loading data...${NC}"
    # Use standalone_setup.sh in data-only mode
    bash "$SCRIPT_DIR/standalone_setup.sh" --data-only
    echo ""
fi

# ============================================================
# Step 5: Start ngrok tunnels
# ============================================================
if [ "$SKIP_TUNNEL" = true ]; then
    echo -e "${YELLOW}Skipping ngrok tunnel (--skip-tunnel)${NC}"
    echo -e "${YELLOW}Workflows calling MCP/backend will not work from Elastic Cloud${NC}"
    echo ""
    
    # Deploy with Docker-internal URLs (works if Elastic is also local)
    MCP_URL="http://mcp-server:8001/mcp"
    BACKEND_URL=""
else
    echo -e "${BOLD}${CYAN}Starting ngrok tunnels...${NC}"
    
    # Kill any existing ngrok processes
    pkill -f "ngrok" 2>/dev/null || true
    sleep 1
    
    # Check if ngrok config exists for multi-tunnel setup
    NGROK_CONFIG="$REPO_ROOT/config/ngrok.yml"
    # Find ngrok's default config (contains authtoken)
    # Extract path from "Valid configuration file at /path/to/ngrok.yml"
    NGROK_DEFAULT_CONFIG=$(ngrok config check 2>&1 | sed -n 's/.*Valid configuration file at //p' | head -1)
    if [ -z "$NGROK_DEFAULT_CONFIG" ] || [ ! -f "$NGROK_DEFAULT_CONFIG" ]; then
        # Common default locations (macOS, Linux, legacy)
        if [ -f "$HOME/Library/Application Support/ngrok/ngrok.yml" ]; then
            NGROK_DEFAULT_CONFIG="$HOME/Library/Application Support/ngrok/ngrok.yml"
        elif [ -f "$HOME/.config/ngrok/ngrok.yml" ]; then
            NGROK_DEFAULT_CONFIG="$HOME/.config/ngrok/ngrok.yml"
        elif [ -f "$HOME/.ngrok2/ngrok.yml" ]; then
            NGROK_DEFAULT_CONFIG="$HOME/.ngrok2/ngrok.yml"
        fi
    fi
    
    if [ -f "$NGROK_CONFIG" ]; then
        echo -e "  Using config: ${CYAN}$NGROK_CONFIG${NC}"
        # Must include BOTH the default config (has authtoken) and our tunnel config
        if [ -n "$NGROK_DEFAULT_CONFIG" ] && [ -f "$NGROK_DEFAULT_CONFIG" ]; then
            ngrok start --config "$NGROK_DEFAULT_CONFIG" --config "$NGROK_CONFIG" --all --log=stdout > /tmp/ngrok-wayfinder.log 2>&1 &
        else
            ngrok start --config "$NGROK_CONFIG" --all --log=stdout > /tmp/ngrok-wayfinder.log 2>&1 &
        fi
        NGROK_PID=$!
    else
        # Single tunnel for MCP server (most common need)
        echo -e "  Tunneling MCP server (port 8001)..."
        ngrok http 8001 --log=stdout > /tmp/ngrok-wayfinder.log 2>&1 &
        NGROK_PID=$!
    fi
    
    # Cleanup on exit
    trap "echo ''; echo -e '${YELLOW}Shutting down ngrok...${NC}'; kill $NGROK_PID 2>/dev/null; echo -e '${GREEN}Done${NC}'" EXIT
    
    # Wait for ngrok to start and expose its API
    echo -n "  Waiting for ngrok..."
    for i in $(seq 1 15); do
        if curl -sf http://127.0.0.1:4040/api/tunnels > /dev/null 2>&1; then
            echo -e " ${GREEN}ready${NC}"
            break
        fi
        if [ $i -eq 15 ]; then
            echo -e " ${RED}timeout${NC}"
            echo -e "${RED}ngrok failed to start. Check /tmp/ngrok-wayfinder.log${NC}"
            echo -e "${YELLOW}Is ngrok authenticated? Run: ngrok config add-authtoken <token>${NC}"
            exit 1
        fi
        sleep 1
    done
    
    # Retrieve tunnel URLs from ngrok API
    TUNNELS_JSON=$(curl -sf http://127.0.0.1:4040/api/tunnels)
    
    # Parse tunnel URLs - handle both single and multi-tunnel setups
    MCP_TUNNEL_URL=$(echo "$TUNNELS_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tunnels = data.get('tunnels', [])
# For multi-tunnel: look for tunnel named 'mcp' or on port 8001
# For single tunnel: just take the first one
for t in tunnels:
    name = t.get('name', '')
    addr = t.get('config', {}).get('addr', '')
    if name == 'mcp' or ':8001' in addr or len(tunnels) == 1:
        print(t['public_url'])
        break
" 2>/dev/null)
    
    BACKEND_TUNNEL_URL=$(echo "$TUNNELS_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tunnels = data.get('tunnels', [])
for t in tunnels:
    name = t.get('name', '')
    addr = t.get('config', {}).get('addr', '')
    if name == 'backend' or ':8000' in addr:
        print(t['public_url'])
        break
" 2>/dev/null)
    
    if [ -z "$MCP_TUNNEL_URL" ]; then
        echo -e "${RED}ERROR: Could not determine ngrok tunnel URL${NC}"
        echo "Check: curl http://127.0.0.1:4040/api/tunnels"
        exit 1
    fi
    
    echo ""
    echo -e "  ${GREEN}MCP tunnel:${NC}     $MCP_TUNNEL_URL"
    MCP_URL="${MCP_TUNNEL_URL}/mcp"
    
    if [ -n "$BACKEND_TUNNEL_URL" ]; then
        echo -e "  ${GREEN}Backend tunnel:${NC} $BACKEND_TUNNEL_URL"
        BACKEND_URL="$BACKEND_TUNNEL_URL"
    else
        echo -e "  ${YELLOW}No backend tunnel${NC} (ground_conditions workflow will use MCP tunnel)"
        BACKEND_URL=""
    fi
    echo ""
fi

# ============================================================
# Step 6: Deploy workflows and agents with tunnel URLs
# ============================================================
echo -e "${BOLD}${CYAN}Deploying workflows and agents...${NC}"

BACKEND_URL_FLAG=""
if [ -n "$BACKEND_URL" ]; then
    BACKEND_URL_FLAG="--backend-url $BACKEND_URL"
fi

echo -e "  ${BLUE}Deploying workflows...${NC}"
python3 scripts/deploy_workflows.py --workflows-dir config/workflows --mcp-url "$MCP_URL" $BACKEND_URL_FLAG

echo ""
echo -e "  ${BLUE}Creating agents and tools...${NC}"
python3 scripts/create_agents.py --mcp-url "$MCP_URL" $BACKEND_URL_FLAG

echo ""

# ============================================================
# Step 7: Print status summary
# ============================================================
echo -e "${BOLD}${CYAN}=============================================="
echo -e "  Wayfinder Supply Co. - Ready!"
echo -e "==============================================${NC}"
echo ""
echo -e "  ${BOLD}Services:${NC}"
echo -e "    Frontend:  ${CYAN}http://localhost:3000${NC}"
echo -e "    Backend:   ${CYAN}http://localhost:8000${NC}"
echo -e "    MCP:       ${CYAN}http://localhost:8001${NC}"
echo ""
if [ "$SKIP_TUNNEL" = false ]; then
    echo -e "  ${BOLD}ngrok Tunnels:${NC}"
    echo -e "    MCP:       ${CYAN}$MCP_TUNNEL_URL${NC}"
    if [ -n "$BACKEND_TUNNEL_URL" ]; then
        echo -e "    Backend:   ${CYAN}$BACKEND_TUNNEL_URL${NC}"
    fi
    echo ""
    echo -e "  ${BOLD}Elastic Cloud → Local:${NC}"
    echo -e "    Workflows route through ngrok to reach local MCP/backend"
    echo ""
    echo -e "  ${YELLOW}Note: ngrok is running in the background.${NC}"
    echo -e "  ${YELLOW}Press Ctrl+C to stop ngrok. Docker services will keep running.${NC}"
    echo -e "  ${YELLOW}To stop Docker: docker compose down${NC}"
    echo ""
    
    # Keep script alive so the trap can clean up ngrok on Ctrl+C
    echo -e "${BOLD}Keeping ngrok alive. Press Ctrl+C to stop.${NC}"
    wait $NGROK_PID 2>/dev/null
else
    echo -e "  ${YELLOW}To stop: docker compose down${NC}"
fi
