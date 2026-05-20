#!/bin/bash
# Run after Scene 6 — cleans up Copilot changes and switches to fixed branch
set -e
git restore backend/services/inventory_service.py 2>/dev/null || true
git clean -f backend/tests/test_inventory_service.py 2>/dev/null || true
git checkout feature/msft-build-2026
echo "✓ On feature/msft-build-2026. Ready for Scene 7."
echo "  Run: python3 scripts/msbuild_harness.py l1"
