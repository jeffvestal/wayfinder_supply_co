#!/usr/bin/env python3
"""
Test all API endpoints to ensure they're working correctly.
"""

import requests
import json
import sys
from typing import Dict, Tuple

BASE_URL = "http://localhost:8000"
MCP_URL = "http://localhost:8001"


def test_endpoint(method: str, url: str, expected_status: int = 200, **kwargs) -> Tuple[bool, str]:
    """Test an endpoint and return (success, message)."""
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        if response.status_code == expected_status:
            return True, f"✓ {method} {url} - Status: {response.status_code}"
        else:
            return False, f"✗ {method} {url} - Expected {expected_status}, got {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, f"✗ {method} {url} - Error: {str(e)}"


def main():
    print("Testing Wayfinder Supply Co. API Endpoints...")
    print("=" * 60)
    
    tests = []
    
    # Backend health
    print("\n1. Testing Backend Health...")
    success, msg = test_endpoint("GET", f"{BASE_URL}/health")
    tests.append((success, msg))
    print(f"  {msg}")
    
    # Chat health
    success, msg = test_endpoint("GET", f"{BASE_URL}/api/chat/health")
    tests.append((success, msg))
    print(f"  {msg}")
    
    # Products list
    print("\n2. Testing Product Endpoints...")
    success, msg = test_endpoint("GET", f"{BASE_URL}/api/products?limit=5")
    tests.append((success, msg))
    print(f"  {msg}")
    
    # Product search
    success, msg = test_endpoint("GET", f"{BASE_URL}/api/products/search?q=sleeping%20bag&limit=5")
    tests.append((success, msg))
    tests.append((success, msg))
    print(f"  {msg}")
    
    # Cart endpoints
    print("\n3. Testing Cart Endpoints...")
    success, msg = test_endpoint("GET", f"{BASE_URL}/api/cart?user_id=user_new")
    tests.append((success, msg))
    print(f"  {msg}")
    
    # Add to cart
    success, msg = test_endpoint(
        "POST",
        f"{BASE_URL}/api/cart?user_id=user_new",
        json={"product_id": "test-product", "quantity": 1},
        expected_status=200
    )
    tests.append((success, msg))
    print(f"  {msg}")
    
    # MCP Server
    print("\n4. Testing MCP Server...")
    success, msg = test_endpoint("GET", f"{MCP_URL}/health")
    tests.append((success, msg))
    print(f"  {msg}")
    
    # MCP tool call
    mcp_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_trip_conditions_tool",
            "arguments": {
                "location": "Rockies",
                "dates": "January 15, 2024"
            }
        },
        "id": "test-1"
    }
    success, msg = test_endpoint("POST", f"{MCP_URL}/mcp", json=mcp_request)
    tests.append((success, msg))
    print(f"  {msg}")
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for s, _ in tests if s)
    total = len(tests)
    print(f"Tests: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())


