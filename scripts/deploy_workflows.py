#!/usr/bin/env python3
"""
Deploy Elastic Workflows from YAML files.
"""

import os
import yaml
import requests
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

KIBANA_URL = os.getenv("STANDALONE_KIBANA_URL", os.getenv("KIBANA_URL", "http://kubernetes-vm:30001"))
ES_APIKEY = os.getenv("STANDALONE_ELASTICSEARCH_APIKEY", os.getenv("ELASTICSEARCH_APIKEY", ""))

if not ES_APIKEY:
    raise ValueError("STANDALONE_ELASTICSEARCH_APIKEY (or ELASTICSEARCH_APIKEY) environment variable is required")

HEADERS = {
    "Authorization": f"ApiKey {ES_APIKEY}",
    "Content-Type": "application/json",
    "kbn-xsrf": "true",
    "x-elastic-internal-origin": "kibana",  # Required for workflows API
}


def delete_workflow(workflow_id: str, workflow_name: str) -> bool:
    """Delete a workflow if it exists."""
    url = f"{KIBANA_URL}/api/workflows"
    response = requests.delete(url, headers=HEADERS, json={"ids": [workflow_id]})
    if response.status_code in [200, 204]:
        data = response.json()
        if data.get("deleted", 0) > 0:
            print(f"  ↻ Deleted existing workflow: {workflow_name}")
        return True
    elif response.status_code == 404:
        return True  # Doesn't exist, that's fine
    return False


# Default URLs used in Instruqt environment
INSTRUQT_MCP_URL = "http://host-1:8002/mcp"
INSTRUQT_BACKEND_URL = "http://host-1:8002"


def deploy_workflow(workflow_yaml_path: str, mcp_url: Optional[str] = None, backend_url: Optional[str] = None, api_key: Optional[str] = None) -> Optional[str]:
    """Deploy a workflow from YAML file and return its ID. Deletes existing workflow first.
    
    Args:
        workflow_yaml_path: Path to the workflow YAML file
        mcp_url: Optional MCP server URL to substitute for the default Instruqt MCP URL
        backend_url: Optional backend URL to substitute for the default Instruqt backend URL
        api_key: Optional API key to inject into workflow consts and HTTP step headers
    """
    workflow_path = Path(workflow_yaml_path)
    
    if not workflow_path.exists():
        print(f"✗ Workflow file not found: {workflow_yaml_path}")
        return None
    
    # Read the raw YAML content as a string - API expects {"yaml": "..."}
    with open(workflow_path, 'r') as f:
        yaml_content = f.read()
    
    # Substitute MCP URL if provided (replace Instruqt default with standalone URL)
    # Must be done BEFORE backend_url substitution since MCP URL is a subset of backend URL
    if mcp_url and INSTRUQT_MCP_URL in yaml_content:
        yaml_content = yaml_content.replace(INSTRUQT_MCP_URL, mcp_url)
        print(f"  → Using MCP URL: {mcp_url}")
    
    # Substitute backend URL for non-MCP workflows (e.g., ground_conditions calls /api/vision/ground)
    if backend_url and INSTRUQT_BACKEND_URL in yaml_content:
        yaml_content = yaml_content.replace(INSTRUQT_BACKEND_URL, backend_url)
        print(f"  → Using backend URL: {backend_url}")
    
    # Inject API key via string replacement (preserves YAML formatting)
    # Workflow files use "WAYFINDER_API_KEY" as a placeholder in X-Api-Key headers
    INSTRUQT_API_KEY_PLACEHOLDER = "WAYFINDER_API_KEY"
    if api_key and INSTRUQT_API_KEY_PLACEHOLDER in yaml_content:
        yaml_content = yaml_content.replace(INSTRUQT_API_KEY_PLACEHOLDER, api_key)
        print(f"  → Injected API key into HTTP headers")
    
    # Also parse it to get the name for logging
    workflow_data = yaml.safe_load(yaml_content)
    workflow_name = workflow_data.get("name", workflow_path.stem)
    
    url = f"{KIBANA_URL}/api/workflows"

    # Delete existing workflow first (script is source of truth)
    list_response = requests.get(url, headers=HEADERS)
    if list_response.status_code == 200:
        data = list_response.json()
        workflows = data.get("results", []) or data.get("data", [])
        for wf in workflows:
            if wf.get("name") == workflow_name:
                existing_id = wf.get("id")
                delete_workflow(existing_id, workflow_name)

    # Create new workflow - API expects {"workflows": [{"yaml": "<yaml_string>"}]}
    response = requests.post(url, headers=HEADERS, json={"workflows": [{"yaml": yaml_content}]})

    if response.status_code in [200, 201]:
        data = response.json()
        created = data.get("created", [])
        if created:
            workflow_id = created[0].get("id")
            print(f"✓ Deployed workflow: {workflow_name} (ID: {workflow_id})")
            return workflow_id
        failed = data.get("failed", [])
        if failed:
            print(f"✗ Failed to deploy workflow '{workflow_name}': {failed}")
            return None
    else:
        print(f"✗ Failed to deploy workflow '{workflow_name}': {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def main() -> int:
    """Main function. Returns number of failures (0 = success)."""
    import argparse
    parser = argparse.ArgumentParser(description="Deploy Elastic Workflows")
    parser.add_argument(
        "--workflows-dir",
        default="config/workflows",
        help="Directory containing workflow YAML files"
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Workflow names to exclude from deployment (e.g., get_customer_profile)"
    )
    parser.add_argument(
        "--mcp-url",
        default=None,
        help="MCP server URL to use in workflows (default: keeps Instruqt URL http://host-1:8002/mcp)"
    )
    parser.add_argument(
        "--backend-url",
        default=None,
        help="Backend URL for workflows that call the backend (default: keeps Instruqt URL http://host-1:8002)"
    )
    parser.add_argument(
        "--wayfinder-api-key",
        default=None,
        help="Wayfinder API key to inject into workflow consts and HTTP headers (or from WAYFINDER_API_KEY env)"
    )
    args = parser.parse_args()
    
    # Resolve API key from flag or env
    if not args.wayfinder_api_key:
        args.wayfinder_api_key = os.getenv("WAYFINDER_API_KEY")
    
    workflows_dir = Path(args.workflows_dir)
    
    if not workflows_dir.exists():
        print(f"✗ Workflows directory not found: {workflows_dir}")
        return 1
    
    print("Deploying Elastic Workflows...")
    print("=" * 60)
    
    workflow_files = list(workflows_dir.glob("*.yaml")) + list(workflows_dir.glob("*.yml"))
    
    if not workflow_files:
        print(f"⚠ No workflow files found in {workflows_dir}")
        return 1
    
    if args.mcp_url:
        print(f"MCP URL override: {args.mcp_url}")
    if args.backend_url:
        print(f"Backend URL override: {args.backend_url}")
    if args.wayfinder_api_key:
        print(f"Wayfinder API key: {'*' * 4}{args.wayfinder_api_key[-4:]}")
    
    success_count = 0
    skipped_count = 0
    workflow_ids = {}
    for workflow_file in sorted(workflow_files):
        workflow_name = workflow_file.stem
        if workflow_name in args.exclude:
            print(f"⊘ Skipping {workflow_name} (excluded)")
            skipped_count += 1
            continue
        workflow_id = deploy_workflow(str(workflow_file), mcp_url=args.mcp_url, backend_url=args.backend_url, api_key=args.wayfinder_api_key)
        if workflow_id:
            success_count += 1
            workflow_ids[workflow_file.stem] = workflow_id
    
    failures = len(workflow_files) - success_count - skipped_count
    
    print("\n" + "=" * 60)
    print(f"Deployed {success_count}/{len(workflow_files)} workflows")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} workflow(s)")
    if workflow_ids:
        print("\nWorkflow IDs:")
        for name, wf_id in workflow_ids.items():
            print(f"  {name}: {wf_id}")
    print("=" * 60)
    
    return failures


if __name__ == "__main__":
    import sys
    failures = main()
    sys.exit(failures if failures else 0)

