#!/usr/bin/env python3
"""Register an MCP type tool in the Search Agent Builder pointing to the O11y cluster MCP server.

The O11y cluster exposes built-in observability tools via its Agent Builder MCP endpoint,
including platform_core_execute_esql — which the Search agent can use to query
traces-apm.wayfinder-default for slow checkout spans and deadlock incidents.

Architecture: Search Agent → mcp tool → .mcp Kibana connector → O11y MCP server → execute_esql → traces-apm.wayfinder-default

Steps this script performs:
  1. Create (or recreate) a .mcp Kibana connector pointing to the O11y MCP endpoint
  2. Create (or recreate) the Agent Builder MCP tool referencing that connector
  3. Wire the tool to trip-planner-agent

Usage:
    python3 scripts/add_otel_agent_tool.py

Requires in .env:
    STANDALONE_KIBANA_URL           — Search project Kibana (tool is registered here)
    STANDALONE_ELASTICSEARCH_APIKEY — Search project API key
    OBSERVABILITY_KIBANA_URL        — O11y project Kibana URL (MCP server host)
    OBSERVABILITY_ELASTIC_APIKEY    — O11y project API key (used as MCP server auth header)
"""

import os
import sys
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Search project — where the tool is registered
KIBANA_URL = os.getenv("STANDALONE_KIBANA_URL", "").rstrip("/")
API_KEY = os.getenv("STANDALONE_ELASTICSEARCH_APIKEY") or os.getenv("ELASTICSEARCH_APIKEY", "")

# O11y project — the MCP server the tool points to
O11Y_KIBANA_URL = os.getenv("OBSERVABILITY_KIBANA_URL", "").rstrip("/")
O11Y_API_KEY = os.getenv("OBSERVABILITY_ELASTIC_APIKEY") or os.getenv("ELASTIC_API_KEY", "")

KIBANA_HEADERS = {
    "Authorization": f"ApiKey {API_KEY}",
    "Content-Type": "application/json",
    "kbn-xsrf": "true",
    "x-elastic-internal-origin": "kibana",
}

CONNECTOR_NAME = "O11y MCP Server"
TOOL_ID = "tool-mcp-o11y-incident-analysis"
TOOL_NAME_ON_SERVER = "platform_core_execute_esql"
TRIP_PLANNER_AGENT_ID = "trip-planner-agent"


def request_with_retry(method, url, max_retries=3, **kwargs):
    delay = 2
    for attempt in range(max_retries):
        try:
            r = requests.request(method, url, timeout=30, **kwargs)
            if r.status_code in (502, 503, 504, 429) and attempt < max_retries - 1:
                print(f"  ⚠ {r.status_code}, retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
                continue
            return r
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    return r


def get_or_create_mcp_connector():
    """Create (or recreate) the .mcp Kibana connector for the O11y MCP server."""
    print(f"\n=== .mcp Kibana connector: {CONNECTOR_NAME} ===")

    # Delete any existing connector with the same name
    r = request_with_retry("GET", f"{KIBANA_URL}/api/actions/connectors", headers=KIBANA_HEADERS)
    connectors = r.json() if r.status_code == 200 else []
    for c in connectors:
        if c.get("name") == CONNECTOR_NAME and c.get("connector_type_id") == ".mcp":
            cid = c["id"]
            request_with_retry("DELETE", f"{KIBANA_URL}/api/actions/connector/{cid}", headers=KIBANA_HEADERS)
            print(f"  ↻ Deleted existing connector: {cid}")

    # Create with auth header passed as config.headers (authType: none)
    # The .mcp connector's built-in apiKey/bearer authTypes don't match Kibana's ApiKey format,
    # so we pass the Authorization header directly in config.headers instead.
    connector_payload = {
        "name": CONNECTOR_NAME,
        "connector_type_id": ".mcp",
        "config": {
            "serverUrl": f"{O11Y_KIBANA_URL}/api/agent_builder/mcp",
            "hasAuth": False,
            "authType": "none",
            "headers": {
                "Authorization": f"ApiKey {O11Y_API_KEY}"
            },
        },
        "secrets": {},
    }

    r = request_with_retry("POST", f"{KIBANA_URL}/api/actions/connector", headers=KIBANA_HEADERS, json=connector_payload)
    print(f"  CREATE connector: {r.status_code}")
    if r.status_code not in (200, 201):
        print(f"  ✗ Failed: {r.text[:400]}")
        return None

    connector_id = r.json()["id"]
    print(f"  ✓ Connector created: {connector_id}")

    # Verify connection
    r2 = request_with_retry("POST", f"{KIBANA_URL}/api/actions/connector/{connector_id}/_execute",
                             headers=KIBANA_HEADERS, json={"params": {"subAction": "test"}})
    if r2.status_code == 200 and r2.json().get("data", {}).get("connected"):
        print(f"  ✓ Connector verified: connected to O11y MCP server")
    else:
        print(f"  ⚠ Connector test: {r2.status_code} {r2.text[:200]}")

    return connector_id


def create_mcp_tool(connector_id):
    print(f"\n=== Create MCP tool: {TOOL_ID} ===")

    # Delete existing tool if present
    r = request_with_retry("DELETE", f"{KIBANA_URL}/api/agent_builder/tools/{TOOL_ID}?force=true", headers=KIBANA_HEADERS)
    if r.status_code not in (200, 201, 204, 404):
        print(f"  ⚠ DELETE tool returned {r.status_code}: {r.text[:100]}")
    elif r.status_code != 404:
        print(f"  ↻ Deleted existing tool: {TOOL_ID}")
        time.sleep(1)

    tool_config = {
        "id": TOOL_ID,
        "type": "mcp",
        "description": (
            "Query the Observability cluster to investigate checkout service incidents. "
            "Use this to run ES|QL against traces-apm.wayfinder-default. "
            "To find slow checkouts: WHERE http.route == '/api/v1/checkout/reserve' AND event.duration > 3000000000. "
            "To find deadlocks: WHERE MATCH(db.statement, 'lock deadlock concurrent'). "
            "Use this tool when investigating checkout performance degradation or order failures."
        ),
        "tags": [],
        "configuration": {
            "connector_id": connector_id,
            "tool_name": TOOL_NAME_ON_SERVER,
        },
    }

    r = request_with_retry("POST", f"{KIBANA_URL}/api/agent_builder/tools", headers=KIBANA_HEADERS, json=tool_config)
    print(f"  CREATE tool: {r.status_code}")
    if r.status_code in (200, 201):
        print(f"  ✓ Tool created: {TOOL_ID}")
        return TOOL_ID
    else:
        print(f"  ✗ Failed: {r.text[:400]}")
        return None


def wire_tool_to_agent(tool_id):
    print(f"\n=== Wire {tool_id} to {TRIP_PLANNER_AGENT_ID} ===")

    r = request_with_retry("GET", f"{KIBANA_URL}/api/agent_builder/agents", headers=KIBANA_HEADERS)
    if r.status_code != 200:
        print(f"  ✗ Could not fetch agents: {r.status_code}")
        return

    agents = r.json().get("results", [])
    agent = next((a for a in agents if a.get("id") == TRIP_PLANNER_AGENT_ID), None)
    if not agent:
        print(f"  ✗ Agent not found: {TRIP_PLANNER_AGENT_ID}")
        return

    current_ids = agent.get("configuration", {}).get("tools", [{}])[0].get("tool_ids", [])
    print(f"  Current tools: {current_ids}")

    if tool_id in current_ids:
        print(f"  ✓ Tool already wired")
        return

    new_ids = current_ids + [tool_id]
    agent["configuration"]["tools"] = [{"tool_ids": new_ids}]

    # PUT only accepts name + configuration
    payload = {"name": agent["name"], "configuration": agent["configuration"]}
    r2 = request_with_retry("PUT", f"{KIBANA_URL}/api/agent_builder/agents/{TRIP_PLANNER_AGENT_ID}",
                             headers=KIBANA_HEADERS, json=payload)
    if r2.status_code in (200, 201):
        print(f"  ✓ Agent updated. Tools: {new_ids}")
    else:
        print(f"  ✗ Failed to update agent: {r2.text[:400]}")


if __name__ == "__main__":
    missing = []
    if not KIBANA_URL:
        missing.append("STANDALONE_KIBANA_URL")
    if not API_KEY:
        missing.append("STANDALONE_ELASTICSEARCH_APIKEY")
    if not O11Y_KIBANA_URL:
        missing.append("OBSERVABILITY_KIBANA_URL")
    if not O11Y_API_KEY:
        missing.append("OBSERVABILITY_ELASTIC_APIKEY")
    if missing:
        print(f"ERROR: Missing env vars: {', '.join(missing)}")
        sys.exit(1)

    connector_id = get_or_create_mcp_connector()
    if not connector_id:
        print("\nConnector creation failed.")
        sys.exit(1)

    tool_id = create_mcp_tool(connector_id)
    if not tool_id:
        print("\nTool creation failed.")
        sys.exit(1)

    wire_tool_to_agent(tool_id)
    print("\nDone. Test: ask Trip Planner 'why is checkout so slow on April 7?'")
