#!/usr/bin/env python3
"""
Deploy the MS Build PR-review workflow to the Elastic observability cluster.

Wraps `deploy_workflow()` from deploy_workflows.py but:
- Targets the MS Build o11y cluster (STANDALONE_KIBANA_URL env)
- Substitutes KIBANA_URL_PLACEHOLDER and MSBUILD_AGENT_ID_PLACEHOLDER in the YAML
- Prints the HTTP trigger URL + API key format for GH secret setup

Usage:
  python3 scripts/deploy_msbuild_workflow.py
  python3 scripts/deploy_msbuild_workflow.py --agent-id <id>    # override agent id
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_YAML = REPO_ROOT / "config" / "workflows" / "elastic-agent-pr-review.yaml"


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"ApiKey {api_key}",
        "Content-Type": "application/json",
        "kbn-xsrf": "true",
        "x-elastic-internal-origin": "kibana",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent-id", default=os.getenv("MSBUILD_AGENT_ID", ""))
    ap.add_argument("--kibana-url", default=os.getenv("STANDALONE_KIBANA_URL", ""))
    ap.add_argument("--api-key", default=os.getenv("STANDALONE_ELASTICSEARCH_APIKEY", os.getenv("ELASTICSEARCH_APIKEY", "")))
    args = ap.parse_args()

    missing: list[str] = []
    if not args.agent_id:
        missing.append("--agent-id or MSBUILD_AGENT_ID (run scripts/create_msbuild_agent.py first)")
    if not args.kibana_url:
        missing.append("--kibana-url or STANDALONE_KIBANA_URL")
    if not args.api_key:
        missing.append("--api-key or STANDALONE_ELASTICSEARCH_APIKEY")
    if missing:
        print("✗ missing:", *missing, sep="\n  ")
        return 2
    if not WORKFLOW_YAML.exists():
        print(f"✗ workflow YAML missing: {WORKFLOW_YAML}")
        return 3

    raw = WORKFLOW_YAML.read_text()
    # Remove the 'id:' line from the YAML — the API treats it as a uniqueness key
    # and a prior failed deploy can poison the registry, blocking future creates.
    # The server will assign a system UUID; we use that as the canonical workflow id.
    yaml_content = "\n".join(line for line in raw.splitlines() if not line.startswith("id:"))
    yaml_content = yaml_content.replace("KIBANA_URL_PLACEHOLDER", args.kibana_url.rstrip("/"))
    yaml_content = yaml_content.replace("MSBUILD_AGENT_ID_PLACEHOLDER", args.agent_id)
    yaml_content = yaml_content.replace("WAYFINDER_API_KEY", args.api_key)

    # Upload
    url = f"{args.kibana_url.rstrip('/')}/api/workflows"

    # Delete existing workflow by name (same approach as deploy_workflows.py)
    list_r = requests.get(url, headers=_headers(args.api_key), timeout=15)
    if list_r.status_code == 200:
        for wf in list_r.json().get("results", []):
            if wf.get("name") == "elastic-agent-pr-review":
                existing_id = wf["id"]
                d = requests.delete(url, headers=_headers(args.api_key), json={"ids": [existing_id]}, timeout=15)
                if d.status_code in (200, 204):
                    print(f"  ↻ removed existing workflow (system id: {existing_id})")

    r = requests.post(url, headers=_headers(args.api_key), json={"yaml": yaml_content}, timeout=30)
    if r.status_code not in (200, 201):
        print(f"✗ deploy failed: HTTP {r.status_code}")
        print(f"  body: {r.text[:1000]}")
        return 4

    data = r.json()
    # Single-workflow POST returns the workflow object directly (not a "created" list)
    if isinstance(data, dict) and data.get("id"):
        wf_id = data["id"]
    else:
        created = data.get("created", [])
        if not created:
            print(f"✗ no workflow created: {json.dumps(data)[:500]}")
            return 5
        wf_id = created[0].get("id")
    print(f"✓ deployed workflow: id={wf_id}")

    # Print HTTP trigger URL — exact path varies by Elastic version; the Kibana UI shows it.
    # Common shape (9.4): /api/workflows/executions?workflow_id=<id> or a dedicated trigger URL per workflow.
    trigger_hint_url = f"{args.kibana_url.rstrip('/')}/api/workflows/{wf_id}/trigger"
    print()
    print(f"  HTTP trigger URL (verify in Kibana UI):")
    print(f"    {trigger_hint_url}")
    print()
    print(f"  To set repo secrets:")
    print(f"    gh secret set ELASTIC_WORKFLOW_URL --body '{trigger_hint_url}'")
    print(f"    gh secret set ELASTIC_WORKFLOW_KEY --body 'ApiKey <base64>'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
