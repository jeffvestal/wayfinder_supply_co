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
    url = f"{KIBANA_URL}/api/workflows/{workflow_id}"
    response = requests.delete(url, headers=HEADERS)
    if response.status_code in [200, 204]:
        print(f"  ↻ Deleted existing workflow: {workflow_name}")
        return True
    elif response.status_code == 404:
        return True  # Doesn't exist, that's fine
    return False


def deploy_workflow(workflow_yaml_path: str) -> Optional[str]:
    """Deploy a workflow from YAML file and return its ID. Deletes existing workflow first."""
    workflow_path = Path(workflow_yaml_path)
    
    if not workflow_path.exists():
        print(f"✗ Workflow file not found: {workflow_yaml_path}")
        return None
    
    # Read the raw YAML content as a string - API expects {"yaml": "..."}
    with open(workflow_path, 'r') as f:
        yaml_content = f.read()
    
    # Also parse it to get the name for logging
    workflow_data = yaml.safe_load(yaml_content)
    workflow_name = workflow_data.get("name", workflow_path.stem)
    
    url = f"{KIBANA_URL}/api/workflows"
    search_url = f"{url}/search"
    
    # Delete existing workflow first (script is source of truth)
    list_response = requests.post(search_url, headers=HEADERS, json={"limit": 100, "page": 1, "query": ""})
    if list_response.status_code == 200:
        data = list_response.json()
        workflows = data.get("results", []) or data.get("data", [])
        for wf in workflows:
            if wf.get("name") == workflow_name:
                existing_id = wf.get("id")
                delete_workflow(existing_id, workflow_name)
    
    # Create new workflow - API expects {"yaml": "<yaml_string>"}
    response = requests.post(url, headers=HEADERS, json={"yaml": yaml_content})
    
    if response.status_code in [200, 201]:
        data = response.json()
        workflow_id = data.get("id") or data.get("workflow_id")
        print(f"✓ Deployed workflow: {workflow_name} (ID: {workflow_id})")
        return workflow_id
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
    args = parser.parse_args()
    
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
    
    success_count = 0
    skipped_count = 0
    workflow_ids = {}
    for workflow_file in sorted(workflow_files):
        workflow_name = workflow_file.stem
        if workflow_name in args.exclude:
            print(f"⊘ Skipping {workflow_name} (excluded)")
            skipped_count += 1
            continue
        workflow_id = deploy_workflow(str(workflow_file))
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

