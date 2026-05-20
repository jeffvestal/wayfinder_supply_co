#!/usr/bin/env python3
"""
Validate that the Wayfinder Supply Co. setup is complete and working.
"""

import os
import requests
from elasticsearch import Elasticsearch
from typing import List, Tuple

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

def get_env_vars(mode: str = "standalone"):
    """Get environment variables based on mode."""
    if mode == "snapshot":
        es_url = os.getenv("SNAPSHOT_ELASTICSEARCH_URL", os.getenv("ELASTICSEARCH_URL", "http://kubernetes-vm:30920"))
        es_apikey = os.getenv("SNAPSHOT_ELASTICSEARCH_APIKEY", os.getenv("ELASTICSEARCH_APIKEY", ""))
        kibana_url = None  # Not needed for snapshot mode
    else:  # standalone
        es_url = os.getenv("STANDALONE_ELASTICSEARCH_URL", os.getenv("ELASTICSEARCH_URL", "http://kubernetes-vm:30920"))
        es_apikey = os.getenv("STANDALONE_ELASTICSEARCH_APIKEY", os.getenv("ELASTICSEARCH_APIKEY", ""))
        kibana_url = os.getenv("STANDALONE_KIBANA_URL", os.getenv("KIBANA_URL", "http://kubernetes-vm:30001"))
    
    if not es_apikey:
        prefix = "SNAPSHOT_" if mode == "snapshot" else "STANDALONE_"
        raise ValueError(f"{prefix}ELASTICSEARCH_APIKEY (or ELASTICSEARCH_APIKEY) environment variable is required")
    
    headers = {
        "Authorization": f"ApiKey {es_apikey}",
        "Content-Type": "application/json",
        "kbn-xsrf": "true",
    }
    
    return es_url, es_apikey, kibana_url, headers


# Default to standalone mode for backward compatibility
ES_URL, ES_APIKEY, KIBANA_URL, HEADERS = get_env_vars("standalone")


def check_elasticsearch(es_url: str, es_apikey: str) -> Tuple[bool, List[str]]:
    """Check Elasticsearch connectivity and indices."""
    issues = []
    
    try:
        es = Elasticsearch(
            [es_url], 
            api_key=es_apikey, 
            request_timeout=10
        )
        
        # Check cluster health
        health = es.cluster.health()
        if health["status"] not in ["green", "yellow"]:
            issues.append(f"Elasticsearch cluster status: {health['status']}")
        
        # Check indices
        required_indices = ["product-catalog", "user-clickstream"]
        for index in required_indices:
            if not es.indices.exists(index=index):
                issues.append(f"Index '{index}' does not exist")
            else:
                count = es.count(index=index)["count"]
                if count == 0:
                    issues.append(f"Index '{index}' is empty")
        
        if not issues:
            return True, []
        return False, issues
        
    except Exception as e:
        return False, [f"Elasticsearch connection error: {str(e)}"]


def check_kibana(kibana_url: str, headers: dict) -> Tuple[bool, List[str]]:
    """Check Kibana connectivity."""
    issues = []
    
    if not kibana_url:
        return False, ["Kibana URL not configured for this mode"]
    
    try:
        response = requests.get(
            f"{kibana_url}/api/status",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            issues.append(f"Kibana status check failed: {response.status_code}")
            return False, issues
        
        return True, []
        
    except Exception as e:
        return False, [f"Kibana connection error: {str(e)}"]


def check_agents(kibana_url: str, headers: dict) -> Tuple[bool, List[str]]:
    """Check that required agents exist."""
    issues = []
    
    if not kibana_url:
        return False, ["Kibana URL not configured for this mode"]
    
    try:
        url = f"{kibana_url}/api/agent_builder/agents"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            issues.append(f"Failed to list agents: {response.status_code}")
            return False, issues
        
        agents = response.json().get("data", [])
        agent_names = [a.get("name") for a in agents]
        
        required_agents = ["trip-planner-agent", "trip-itinerary-agent"]
        for agent_name in required_agents:
            if agent_name not in agent_names:
                issues.append(f"Agent '{agent_name}' not found")
        
        if not issues:
            return True, []
        return False, issues
        
    except Exception as e:
        return False, [f"Agent check error: {str(e)}"]


def check_workflows(kibana_url: str, headers: dict) -> Tuple[bool, List[str]]:
    """Check that required workflows exist."""
    issues = []
    
    if not kibana_url:
        return False, ["Kibana URL not configured for this mode"]
    
    try:
        url = f"{kibana_url}/api/workflows"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            issues.append(f"Failed to list workflows: {response.status_code}")
            return False, issues
        
        workflows = response.json().get("data", [])
        workflow_names = [w.get("name") for w in workflows]
        
        required_workflows = [
            "check_trip_safety",
            "get_customer_profile",
            "get_user_affinity"
        ]
        
        for workflow_name in required_workflows:
            if workflow_name not in workflow_names:
                issues.append(f"Workflow '{workflow_name}' not found")
        
        if not issues:
            return True, []
        return False, issues
        
    except Exception as e:
        return False, [f"Workflow check error: {str(e)}"]


def check_mcp_server() -> Tuple[bool, List[str]]:
    """Check MCP server connectivity."""
    issues = []
    
    mcp_url = os.getenv("MCP_SERVER_URL", "http://host-1:8001")
    
    try:
        response = requests.get(
            f"{mcp_url}/health",
            timeout=5
        )
        
        if response.status_code != 200:
            issues.append(f"MCP server health check failed: {response.status_code}")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        return False, [f"MCP server connection error: {str(e)}"]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate Wayfinder Supply Co. setup")
    parser.add_argument(
        "--mode",
        choices=["snapshot", "standalone"],
        default="standalone",
        help="Validation mode: 'snapshot' for data loading cluster, 'standalone' for demo cluster (default)"
    )
    args = parser.parse_args()
    
    print("Validating Wayfinder Supply Co. Setup...")
    print(f"Mode: {args.mode}")
    print("=" * 60)
    
    # Get environment variables for the selected mode
    es_url, es_apikey, kibana_url, headers = get_env_vars(args.mode)
    
    checks = [
        ("Elasticsearch", lambda: check_elasticsearch(es_url, es_apikey)),
        ("Kibana", lambda: check_kibana(kibana_url, headers) if args.mode == "standalone" else (True, [])),
        ("Agents", lambda: check_agents(kibana_url, headers) if args.mode == "standalone" else (True, [])),
        ("Workflows", lambda: check_workflows(kibana_url, headers) if args.mode == "standalone" else (True, [])),
        ("MCP Server", check_mcp_server),
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        passed, issues = check_func()
        
        if passed:
            print(f"  ✓ {name} is healthy")
        else:
            all_passed = False
            print(f"  ✗ {name} has issues:")
            for issue in issues:
                print(f"    - {issue}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All checks passed! Setup is complete.")
    else:
        print("✗ Some checks failed. Please review the issues above.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

