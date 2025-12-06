#!/bin/bash
# Complete setup script - generates data and creates placeholders

set -e

echo "Wayfinder Supply Co. - Complete Setup"
echo "======================================"

# Generate sample products
echo ""
echo "1. Generating sample product data..."
python3 scripts/generate_sample_data.py

# Create placeholder images
echo ""
echo "2. Creating placeholder product images..."
if command -v python3 &> /dev/null && python3 -c "import PIL" 2>/dev/null; then
    python3 scripts/create_placeholder_images.py
else
    echo "  ⚠️  PIL/Pillow not installed, skipping image generation"
    echo "  Install with: pip install Pillow"
    echo "  Or run: python scripts/create_placeholder_images.py"
fi

# Install frontend dependencies
echo ""
echo "3. Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
else
    echo "  ✓ Frontend dependencies already installed"
fi
cd ..

# Verify frontend builds
echo ""
echo "4. Verifying frontend builds..."
cd frontend
if npm run build 2>&1 | grep -q "built in"; then
    echo "  ✓ Frontend builds successfully"
else
    echo "  ⚠️  Frontend build had warnings (check output above)"
fi
cd ..

echo ""
echo "======================================"
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Set environment variables (ELASTICSEARCH_URL, KIBANA_URL, ELASTICSEARCH_APIKEY)"
echo "  2. Run: python scripts/setup_elastic.py"
echo "  3. Run: python scripts/seed_products.py"
echo "  4. Run: python scripts/seed_clickstream.py"
echo "  5. Run: python scripts/deploy_workflows.py"
echo "  6. Run: python scripts/create_agents.py"
echo "======================================"


