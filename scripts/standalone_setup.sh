#!/bin/bash
# standalone_setup.sh - Configure Agent Builder for standalone demo

set -e

# Parse arguments
LOAD_DATA=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --load-data)
            LOAD_DATA=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--load-data]"
            echo "  --load-data  Load data into cluster (for serverless clusters that can't restore snapshots)"
            exit 1
            ;;
    esac
done

echo "=============================================="
echo "Wayfinder Supply Co. - Standalone Demo Setup"
echo "=============================================="

# Check required env vars
if [ -z "$STANDALONE_ELASTICSEARCH_URL" ] || [ -z "$STANDALONE_ELASTICSEARCH_APIKEY" ] || [ -z "$STANDALONE_KIBANA_URL" ]; then
    echo "ERROR: Required environment variables not set"
    echo ""
    echo "Please set the following variables:"
    echo "  STANDALONE_ELASTICSEARCH_URL"
    echo "  STANDALONE_ELASTICSEARCH_APIKEY"
    echo "  STANDALONE_KIBANA_URL"
    echo ""
    echo "You can set them in a .env file or export them before running this script."
    exit 1
fi

echo "Elasticsearch URL: $STANDALONE_ELASTICSEARCH_URL"
echo "Kibana URL: $STANDALONE_KIBANA_URL"
if [ "$LOAD_DATA" = true ]; then
    echo "Mode: Loading data (serverless cluster)"
fi
echo ""

# Load data if --load-data flag is set
if [ "$LOAD_DATA" = true ]; then
    echo "=============================================="
    echo "Loading Data into Cluster"
    echo "=============================================="
    echo ""
    echo "This will create indices and load product/clickstream data."
    echo "Make sure generated_products/products.json exists."
    echo ""
    
    # Temporarily set SNAPSHOT_* vars from STANDALONE_* vars
    # This allows data loading scripts to use the demo cluster
    export SNAPSHOT_ELASTICSEARCH_URL="$STANDALONE_ELASTICSEARCH_URL"
    export SNAPSHOT_ELASTICSEARCH_APIKEY="$STANDALONE_ELASTICSEARCH_APIKEY"
    
    # Create indices
    echo "1. Creating indices and mappings..."
    python scripts/setup_elastic.py
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create indices"
        exit 1
    fi
    
    # Load products
    echo ""
    echo "2. Loading product data..."
    if [ ! -f "generated_products/products.json" ]; then
        echo "ERROR: generated_products/products.json not found"
        echo "Please generate products first or ensure the file exists."
        exit 1
    fi
    python scripts/seed_products.py --products generated_products/products.json
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to load products"
        exit 1
    fi
    
    # Load clickstream
    echo ""
    echo "3. Loading clickstream data..."
    python scripts/seed_clickstream.py
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to load clickstream data"
        exit 1
    fi
    
    echo ""
    echo "Data loading complete!"
    echo ""
fi

# Deploy workflows
echo "=============================================="
echo "Configuring Agent Builder"
echo "=============================================="
echo ""
echo "1. Deploying Workflows..."
python scripts/deploy_workflows.py --workflows-dir config/workflows

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy workflows"
    exit 1
fi

# Create agents and tools
echo ""
echo "2. Creating Agents and Tools..."
python scripts/create_agents.py

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create agents and tools"
    exit 1
fi

echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
if [ "$LOAD_DATA" = true ]; then
    echo "✓ Indices created and data loaded"
fi
echo "✓ Workflows deployed"
echo "✓ Agents and tools created"
echo ""
echo "Next steps:"
echo "  1. Start the services: docker-compose up -d"
echo "  2. Open http://localhost:3000 in your browser"
echo "  3. Try the Trip Planner to test the agents"
echo ""

