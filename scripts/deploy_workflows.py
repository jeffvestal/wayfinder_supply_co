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

KIBANA_URL = os.getenv("KIBANA_URL", "http://kubernetes-vm:30001")
ES_APIKEY = os.getenv("ELASTICSEARCH_APIKEY", "")

if not ES_APIKEY:
    raise ValueError("ELASTICSEARCH_APIKEY environment variable is required")

HEADERS = {
    "Authorization": f"ApiKey {ES_APIKEY}",
    "Content-Type": "application/json",
    "kbn-xsrf": "true",
}


def deploy_workflow(workflow_yaml_path: str) -> Optional[str]:
    """Deploy a workflow from YAML file and return its ID."""
    workflow_path = Path(workflow_yaml_path)
    
    if not workflow_path.exists():
        print(f"✗ Workflow file not found: {workflow_yaml_path}")
        return None
    
    with open(workflow_path, 'r') as f:
        workflow_data = yaml.safe_load(f)
    
    url = f"{KIBANA_URL}/api/workflows"
    
    # Check if workflow already exists
    list_response = requests.get(url, headers=HEADERS)
    if list_response.status_code == 200:
        workflows = list_response.json().get("data", [])
        for wf in workflows:
            if wf.get("name") == workflow_data["name"]:
                existing_id = wf.get("id")
                print(f"⚠ Workflow '{workflow_data['name']}' already exists (ID: {existing_id}), updating...")
                # Update existing workflow
                update_url = f"{url}/{existing_id}"
                response = requests.put(update_url, headers=HEADERS, json=workflow_data)
                if response.status_code in [200, 201]:
                    print(f"✓ Updated workflow: {workflow_data['name']} (ID: {existing_id})")
                    return existing_id
                else:
                    print(f"✗ Failed to update workflow: {response.status_code}")
                    print(f"  Response: {response.text}")
                    return None
    
    # Create new workflow
    response = requests.post(url, headers=HEADERS, json=workflow_data)
    
    if response.status_code in [200, 201]:
        data = response.json()
        workflow_id = data.get("id") or data.get("workflow_id")
        print(f"✓ Deployed workflow: {workflow_data['name']} (ID: {workflow_id})")
        return workflow_id
    else:
        print(f"✗ Failed to deploy workflow '{workflow_data['name']}': {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Deploy Elastic Workflows")
    parser.add_argument(
        "--workflows-dir",
        default="config/workflows",
        help="Directory containing workflow YAML files"
    )
    args = parser.parse_args()
    
    workflows_dir = Path(args.workflows_dir)
    
    if not workflows_dir.exists():
        print(f"✗ Workflows directory not found: {workflows_dir}")
        return
    
    print("Deploying Elastic Workflows...")
    print("=" * 60)
    
    workflow_files = list(workflows_dir.glob("*.yaml")) + list(workflows_dir.glob("*.yml"))
    
    if not workflow_files:
        print(f"⚠ No workflow files found in {workflows_dir}")
        return
    
    success_count = 0
    workflow_ids = {}
    for workflow_file in sorted(workflow_files):
        workflow_id = deploy_workflow(str(workflow_file))
        if workflow_id:
            success_count += 1
            workflow_ids[workflow_file.stem] = workflow_id
    
    print("\n" + "=" * 60)
    print(f"Deployed {success_count}/{len(workflow_files)} workflows")
    if workflow_ids:
        print("\nWorkflow IDs:")
        for name, wf_id in workflow_ids.items():
            print(f"  {name}: {wf_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()

