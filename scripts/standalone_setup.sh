#!/bin/bash
# standalone_setup.sh - Configure Agent Builder for standalone demo

set -e

# Auto-load .env file if it exists
if [ -f .env ]; then
    echo "Loading environment from .env..."
    export $(grep -v '^#' .env | grep -E '^STANDALONE_' | xargs 2>/dev/null) || true
elif [ -f "$(dirname "$0")/../.env" ]; then
    echo "Loading environment from .env..."
    export $(grep -v '^#' "$(dirname "$0")/../.env" | grep -E '^STANDALONE_' | xargs 2>/dev/null) || true
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# Parse arguments
LOAD_DATA=false
DATA_ONLY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --load-data)
            LOAD_DATA=true
            shift
            ;;
        --data-only)
            LOAD_DATA=true
            DATA_ONLY=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--load-data] [--data-only]"
            echo "  --load-data  Load data into cluster, then deploy workflows and agents"
            echo "  --data-only  Load data only (skip workflows and agents)"
            exit 1
            ;;
    esac
done

echo -e "${BOLD}${CYAN}=============================================="
echo -e "  Wayfinder Supply Co. - Standalone Demo Setup"
echo -e "==============================================${NC}"
echo ""

# Check required env vars
if [ -z "$STANDALONE_ELASTICSEARCH_URL" ] || [ -z "$STANDALONE_ELASTICSEARCH_APIKEY" ] || [ -z "$STANDALONE_KIBANA_URL" ]; then
    echo -e "${RED}ERROR: Required environment variables not set${NC}"
    echo ""
    echo "Please set the following variables:"
    echo -e "  ${YELLOW}STANDALONE_ELASTICSEARCH_URL${NC}"
    echo -e "  ${YELLOW}STANDALONE_ELASTICSEARCH_APIKEY${NC}"
    echo -e "  ${YELLOW}STANDALONE_KIBANA_URL${NC}"
    echo ""
    echo "You can set them in a .env file or export them before running this script."
    exit 1
fi

echo -e "${BLUE}Elasticsearch URL:${NC} $STANDALONE_ELASTICSEARCH_URL"
echo -e "${BLUE}Kibana URL:${NC} $STANDALONE_KIBANA_URL"
if [ "$DATA_ONLY" = true ]; then
    echo -e "${YELLOW}Mode:${NC} Data only (skipping workflows and agents)"
elif [ "$LOAD_DATA" = true ]; then
    echo -e "${YELLOW}Mode:${NC} Loading data + configuring agents"
fi
echo ""

# Load data if --load-data flag is set
if [ "$LOAD_DATA" = true ]; then
    echo -e "${BOLD}${CYAN}=============================================="
    echo -e "  Loading Data into Cluster"
    echo -e "==============================================${NC}"
    echo ""
    echo "This will create indices and load product/clickstream data."
    echo -e "Make sure ${YELLOW}generated_products/products.json${NC} exists."
    echo ""
    
    # Temporarily set SNAPSHOT_* vars from STANDALONE_* vars
    # This allows data loading scripts to use the demo cluster
    export SNAPSHOT_ELASTICSEARCH_URL="$STANDALONE_ELASTICSEARCH_URL"
    export SNAPSHOT_ELASTICSEARCH_APIKEY="$STANDALONE_ELASTICSEARCH_APIKEY"
    
    # Create indices
    echo -e "${BLUE}1. Creating indices and mappings...${NC}"
    if python scripts/setup_elastic.py; then
        echo -e "${GREEN}   ✓ Indices created${NC}"
    else
        echo -e "${RED}   ✗ Failed to create indices${NC}"
        FAILURES=$((FAILURES + 1))
    fi
    
    # Load products
    echo ""
    echo -e "${BLUE}2. Loading product data...${NC}"
    if [ ! -f "generated_products/products.json" ]; then
        echo -e "${RED}   ✗ generated_products/products.json not found${NC}"
        echo "   Please generate products first or ensure the file exists."
        FAILURES=$((FAILURES + 1))
    else
        if python scripts/seed_products.py --products generated_products/products.json; then
            echo -e "${GREEN}   ✓ Products loaded${NC}"
        else
            echo -e "${RED}   ✗ Failed to load products${NC}"
            FAILURES=$((FAILURES + 1))
        fi
    fi
    
    # Load clickstream
    echo ""
    echo -e "${BLUE}3. Loading clickstream data...${NC}"
    if python scripts/seed_clickstream.py; then
        echo -e "${GREEN}   ✓ Clickstream data loaded${NC}"
    else
        echo -e "${RED}   ✗ Failed to load clickstream data${NC}"
        FAILURES=$((FAILURES + 1))
    fi
    
    echo ""
fi

# Deploy workflows and agents (skip if --data-only)
if [ "$DATA_ONLY" = false ]; then
    echo -e "${BOLD}${CYAN}=============================================="
    echo -e "  Configuring Agent Builder"
    echo -e "==============================================${NC}"
    echo ""
    echo -e "${BLUE}1. Deploying Workflows...${NC}"
    if python scripts/deploy_workflows.py --workflows-dir config/workflows; then
        echo -e "${GREEN}   ✓ Workflows deployed${NC}"
    else
        echo -e "${RED}   ✗ Failed to deploy workflows${NC}"
        FAILURES=$((FAILURES + 1))
    fi

    # Create agents and tools
    echo ""
    echo -e "${BLUE}2. Creating Agents and Tools...${NC}"
    if python scripts/create_agents.py; then
        echo -e "${GREEN}   ✓ Agents and tools created${NC}"
    else
        echo -e "${RED}   ✗ Failed to create agents and tools${NC}"
        FAILURES=$((FAILURES + 1))
    fi
    echo ""
fi

echo -e "${BOLD}${CYAN}=============================================="

if [ $FAILURES -eq 0 ]; then
    echo -e "  ${GREEN}✓ Setup Complete!${NC}"
    echo -e "==============================================${NC}"
    echo ""
    if [ "$LOAD_DATA" = true ]; then
        echo -e "${GREEN}✓${NC} Indices created and data loaded"
    fi
    if [ "$DATA_ONLY" = false ]; then
        echo -e "${GREEN}✓${NC} Workflows deployed"
        echo -e "${GREEN}✓${NC} Agents and tools created"
        echo ""
        echo -e "${BOLD}Next steps:${NC}"
        echo -e "  1. Start the services: ${YELLOW}docker-compose up -d${NC}"
        echo -e "  2. Open ${CYAN}http://localhost:8000${NC} in your browser"
        echo -e "  3. Try the Trip Planner to test the agents"
    fi
else
    echo -e "  ${RED}✗ Setup Failed with $FAILURES error(s)${NC}"
    echo -e "==============================================${NC}"
    echo ""
    echo -e "${YELLOW}Please review the errors above and fix them before proceeding.${NC}"
    exit 1
fi
echo ""
