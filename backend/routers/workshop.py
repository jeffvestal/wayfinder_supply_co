# backend/routers/workshop.py
"""
Workshop-specific endpoints for tracking progress and component status.
"""

from fastapi import APIRouter, HTTPException
import httpx
import os
from typing import Dict, List, Optional

router = APIRouter()

KIBANA_URL = os.getenv("STANDALONE_KIBANA_URL", os.getenv("KIBANA_URL", "http://kubernetes-vm:30001"))
ELASTICSEARCH_APIKEY = os.getenv("STANDALONE_ELASTICSEARCH_APIKEY", os.getenv("ELASTICSEARCH_APIKEY", ""))


def get_headers() -> Dict[str, str]:
    """Get standard headers for Kibana API calls."""
    return {
        "Authorization": f"ApiKey {ELASTICSEARCH_APIKEY}",
        "Content-Type": "application/json",
        "kbn-xsrf": "true",
        "x-elastic-internal-origin": "kibana",
    }


async def check_workflow_exists(workflow_name: str) -> bool:
    """Check if a workflow exists by name."""
    try:
        url = f"{KIBANA_URL}/api/workflows/search"
        headers = get_headers()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json={"limit": 100, "page": 1, "query": ""}
            )
            
            if response.status_code == 200:
                data = response.json()
                workflows = data.get("results", [])
                for wf in workflows:
                    if wf.get("name") == workflow_name:
                        return wf.get("enabled", False)
            return False
    except Exception:
        return False


async def check_tool_exists(tool_id: str) -> bool:
    """Check if a tool exists by ID."""
    try:
        url = f"{KIBANA_URL}/api/agent_builder/tools"
        headers = get_headers()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                tools = data.get("results", [])
                for tool in tools:
                    if tool.get("id") == tool_id:
                        return True
            return False
    except Exception:
        return False


async def check_agent_exists(agent_id: str) -> bool:
    """Check if an agent exists by ID."""
    try:
        url = f"{KIBANA_URL}/api/agent_builder/agents"
        headers = get_headers()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Check both 'data' and 'results' keys for compatibility
                agents = data.get("data", []) or data.get("results", [])
                for agent in agents:
                    if agent.get("name") == agent_id or agent.get("id") == agent_id:
                        return True
            return False
    except Exception:
        return False


@router.get("/workshop/status")
async def get_workshop_status():
    """
    Check status of all workshop components (workflows, tools, agents).
    Returns a status object showing what exists and what users need to build.
    """
    # Define expected components
    workflows_to_check = [
        {"name": "check_trip_safety", "user_built": False},
        {"name": "get_user_affinity", "user_built": False},
        {"name": "get_customer_profile", "user_built": True},
    ]
    
    tools_to_check = [
        {"id": "tool-search-product-search", "user_built": False},
        {"id": "tool-esql-get-user-affinity", "user_built": False},
        {"id": "tool-workflow-get-customer-profile", "user_built": True},
    ]
    
    agents_to_check = [
        {"id": "wayfinder-search-agent", "user_built": False},
        {"id": "trip-planner-agent", "user_built": True},
    ]
    
    # Check workflows
    workflows_status = []
    for wf in workflows_to_check:
        exists = await check_workflow_exists(wf["name"])
        workflows_status.append({
            "name": wf["name"],
            "exists": exists,
            "user_built": wf["user_built"],
        })
    
    # Check tools
    tools_status = []
    for tool in tools_to_check:
        exists = await check_tool_exists(tool["id"])
        tools_status.append({
            "id": tool["id"],
            "exists": exists,
            "user_built": tool["user_built"],
        })
    
    # Check agents
    agents_status = []
    for agent in agents_to_check:
        exists = await check_agent_exists(agent["id"])
        agents_status.append({
            "id": agent["id"],
            "exists": exists,
            "user_built": agent["user_built"],
        })
    
    # Calculate summary
    all_items = workflows_status + tools_status + agents_status
    complete = sum(1 for item in all_items if item["exists"])
    total = len(all_items)
    
    return {
        "workflows": workflows_status,
        "tools": tools_status,
        "agents": agents_status,
        "summary": {
            "complete": complete,
            "total": total,
            "percentage": round((complete / total * 100) if total > 0 else 0, 1),
        },
    }

