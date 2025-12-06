#!/bin/bash
# Install all dependencies for Wayfinder Supply Co.

set -e

echo "Installing Wayfinder Supply Co. Dependencies..."
echo "================================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required but not installed"
    exit 1
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."

echo "  - Backend dependencies..."
cd backend
python3 -m venv venv || true
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

echo "  - MCP Server dependencies..."
cd mcp_server
python3 -m venv venv || true
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Install Node.js dependencies
echo ""
echo "Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Install Python YAML support (for scripts)
echo ""
echo "Installing script dependencies..."
pip3 install pyyaml requests

echo ""
echo "================================================"
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Set environment variables (see .env.example)"
echo "  2. Generate sample data: make generate"
echo "  3. Seed Elasticsearch: make seed"
echo "  4. Deploy workflows: make deploy"
echo "================================================"


