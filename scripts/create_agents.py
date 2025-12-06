#!/usr/bin/env python3
"""
Create Agent Builder agents via Kibana API.
"""

import os
import json
import requests
import time
from typing import Dict, Optional, List

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


def create_agent(agent_id: str, name: str, description: str, 
                 instructions: str, tool_ids: List[str]) -> Optional[str]:
    """Create an agent with correct API structure."""
    url = f"{KIBANA_URL}/api/agent_builder/agents"
    
    agent_config = {
        "id": agent_id,
        "name": name,
        "description": description,
        "configuration": {
            "instructions": instructions,
            "tools": [{
                "tool_ids": tool_ids
            }]
        }
    }
    
    response = requests.post(url, headers=HEADERS, json=agent_config)
    
    if response.status_code in [200, 201]:
        data = response.json()
        created_agent_id = data.get("id") or agent_id
        print(f"✓ Created agent: {name} (ID: {created_agent_id})")
        return created_agent_id
    elif response.status_code == 409:
        # Agent already exists, try to find it
        print(f"⚠ Agent '{name}' already exists, discovering...")
        list_response = requests.get(url, headers=HEADERS)
        if list_response.status_code == 200:
            agents = list_response.json().get("data", [])
            for agent in agents:
                if agent.get("name") == name or agent.get("id") == agent_id:
                    found_id = agent.get("id")
                    print(f"✓ Found existing agent: {name} (ID: {found_id})")
                    return found_id
    else:
        print(f"✗ Failed to create agent '{name}': {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def create_trip_planner_agent(tool_ids: List[str]) -> Optional[str]:
    """Create the main Trip Planner agent."""
    instructions = """You are the Wayfinder Supply Co. Adventure Logistics Agent. Your role is to help customers plan their outdoor adventures and recommend appropriate gear.

## LOCATION COVERAGE

Wayfinder has detailed trip coverage for 30 curated adventure destinations worldwide:

**North America**: Yosemite, Rocky Mountain NP, Yellowstone, Boundary Waters, Moab, Pacific Crest Trail, Banff, Whistler, Algonquin
**South/Central America**: Patagonia, Costa Rica, Chapada Diamantina (Brazil)
**Europe**: Swiss Alps, Scottish Highlands, Norwegian Fjords, Iceland
**Africa**: Mount Kilimanjaro, Kruger National Park, Atlas Mountains
**Asia**: Nepal Himalayas, Japanese Alps, Bali, MacRitchie (Singapore)
**Oceania**: New Zealand South Island, Australian Outback, Great Barrier Reef
**Middle East**: Wadi Rum (Jordan), Hatta (Dubai/UAE)

When a customer asks about a trip, FIRST use the check_trip_safety tool to validate location coverage:

- If `covered: true` → Proceed with full trip planning using the weather and activity data
- If `covered: false` → Respond warmly:
  "Great choice for adventure! Wayfinder doesn't have detailed coverage for [location] yet, but we're constantly expanding. Based on the region, you might enjoy [alternatives from response]. Would you like me to plan for one of those instead? Or I can still provide general guidance for [location] based on typical conditions for that region."

## TRIP PLANNING STEPS (for covered locations)

1. **Safety Check**: Use the check_trip_safety workflow tool to get weather conditions, seasonal activities, and road alerts.

2. **Customer Profile**: Use the get_customer_profile workflow tool to retrieve their purchase history and loyalty tier.

3. **Personalization**: Use the get_user_affinity ES|QL tool to understand their gear preferences (e.g., ultralight, budget, expedition).

4. **Gear Requirements**: Based on the weather conditions, determine what gear is needed:
   - If min_temp_f < 30: Recommend 0-degree or colder sleeping bags
   - If road_alert includes "traction" or "chain": Recommend tire chains
   - Match gear to the seasonal activities (e.g., skiing gear for winter, kayaking for summer)
   - Consider the user's affinity (e.g., prefer ultralight gear if that's their style)

5. **Check Ownership**: Compare required gear against the customer's purchase_history to see what they already own.

6. **Search Products**: Use the product search tool to find products that match:
   - Required temperature ratings
   - User's preferred style (from affinity)
   - Items not already owned

7. **Synthesis**: Create a comprehensive trip plan that includes:
   - Trip overview with location and dates
   - Weather summary and conditions
   - Recommended activities for the season
   - Gear checklist (split into "Already Owned" and "To Buy")
   - Day-by-day itinerary
   - Special considerations and safety notes
   - Loyalty perks (if applicable: Platinum gets free shipping, Business gets bulk pricing)
   - Cart link in format: /cart?add=item1,item2,item3

Format your response as clean Markdown with proper headings and lists. Make it visually appealing and easy to scan.

Always prioritize safety and provide clear explanations for your recommendations."""
    
    return create_agent(
        agent_id="trip-planner-agent",
        name="Trip Planner Agent",
        description="Main orchestrator agent that plans trips and recommends gear based on location, weather, customer profile, and preferences.",
        instructions=instructions,
        tool_ids=tool_ids
    )


def create_trip_itinerary_agent() -> Optional[str]:
    """Create the Trip Itinerary synthesis agent (optional, kept for future use)."""
    instructions = """You are the Wayfinder Supply Co. Trip Itinerary Specialist. Your role is to create beautiful, detailed trip plans based on gathered information.

When you receive trip information, create a comprehensive itinerary that includes:

1. **Trip Overview**: Destination, dates, and weather summary

2. **Gear Checklist**:
   - **Already Owned**: List items the customer already has (from purchase_history)
   - **Recommended to Buy**: List new items needed with brief explanations

3. **Day-by-Day Plan**: Create a realistic day-by-day itinerary for the trip

4. **Special Considerations**: Include any weather warnings, road conditions, or safety notes

5. **Loyalty Perks**: If the customer has a loyalty tier:
   - Platinum: Mention "✨ Free Overnight Shipping Applied"
   - Business: Mention bulk pricing and Net-30 terms

6. **Cart Link**: Generate a cart link in the format: `/cart?add=item1,item2,item3`

Format your response as clean Markdown with proper headings, lists, and emphasis. Make it visually appealing and easy to scan."""
    
    return create_agent(
        agent_id="trip-itinerary-agent",
        name="Trip Itinerary Agent",
        description="Synthesizes trip plans and creates formatted itineraries with gear checklists.",
        instructions=instructions,
        tool_ids=[]  # No tools needed for this agent
    )


def create_esql_tool(name: str, query: str, description: str) -> Optional[str]:
    """Create an ES|QL tool and return its ID."""
    url = f"{KIBANA_URL}/api/agent_builder/tools"
    
    tool_config = {
        "name": name,
        "type": "esql",
        "query": query,
        "description": description
    }
    
    response = requests.post(url, headers=HEADERS, json=tool_config)
    
    if response.status_code in [200, 201]:
        data = response.json()
        tool_id = data.get("id") or data.get("tool_id")
        print(f"✓ Created ES|QL tool: {name} (ID: {tool_id})")
        return tool_id
    elif response.status_code == 409:
        # Tool already exists, try to find it
        print(f"⚠ ES|QL tool '{name}' already exists, discovering...")
        list_response = requests.get(url, headers=HEADERS)
        if list_response.status_code == 200:
            tools = list_response.json().get("data", [])
            for tool in tools:
                if tool.get("name") == name:
                    tool_id = tool.get("id")
                    print(f"✓ Found existing ES|QL tool: {name} (ID: {tool_id})")
                    return tool_id
    else:
        print(f"✗ Failed to create ES|QL tool '{name}': {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def create_workflow_tool(name: str, workflow_id: str, description: str) -> Optional[str]:
    """Create a workflow tool and return its ID."""
    url = f"{KIBANA_URL}/api/agent_builder/tools"
    
    tool_config = {
        "name": name,
        "type": "workflow",
        "workflow_id": workflow_id,
        "description": description
    }
    
    response = requests.post(url, headers=HEADERS, json=tool_config)
    
    if response.status_code in [200, 201]:
        data = response.json()
        tool_id = data.get("id") or data.get("tool_id")
        print(f"✓ Created workflow tool: {name} (ID: {tool_id})")
        return tool_id
    elif response.status_code == 409:
        # Tool already exists, try to find it
        print(f"⚠ Workflow tool '{name}' already exists, discovering...")
        list_response = requests.get(url, headers=HEADERS)
        if list_response.status_code == 200:
            tools = list_response.json().get("data", [])
            for tool in tools:
                if tool.get("name") == name:
                    tool_id = tool.get("id")
                    print(f"✓ Found existing workflow tool: {name} (ID: {tool_id})")
                    return tool_id
    else:
        print(f"✗ Failed to create workflow tool '{name}': {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def create_index_search_tool(name: str, index: str, description: str) -> Optional[str]:
    """Create an index search tool and return its ID."""
    url = f"{KIBANA_URL}/api/agent_builder/tools"
    
    tool_config = {
        "name": name,
        "type": "index_search",
        "index": index,
        "description": description
    }
    
    response = requests.post(url, headers=HEADERS, json=tool_config)
    
    if response.status_code in [200, 201]:
        data = response.json()
        tool_id = data.get("id") or data.get("tool_id")
        print(f"✓ Created index search tool: {name} (ID: {tool_id})")
        return tool_id
    elif response.status_code == 409:
        # Tool already exists, try to find it
        print(f"⚠ Index search tool '{name}' already exists, discovering...")
        list_response = requests.get(url, headers=HEADERS)
        if list_response.status_code == 200:
            tools = list_response.json().get("data", [])
            for tool in tools:
                if tool.get("name") == name:
                    tool_id = tool.get("id")
                    print(f"✓ Found existing index search tool: {name} (ID: {tool_id})")
                    return tool_id
    else:
        print(f"✗ Failed to create index search tool '{name}': {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def deploy_workflow(workflow_yaml_path: str) -> Optional[str]:
    """Deploy a workflow from YAML file."""
    import yaml
    
    with open(workflow_yaml_path, 'r') as f:
        workflow_data = yaml.safe_load(f)
    
    url = f"{KIBANA_URL}/api/workflows"
    
    response = requests.post(url, headers=HEADERS, json=workflow_data)
    
    if response.status_code in [200, 201]:
        data = response.json()
        workflow_id = data.get("id") or data.get("workflow_id")
        print(f"✓ Deployed workflow: {workflow_data['name']} (ID: {workflow_id})")
        return workflow_id
    elif response.status_code == 409:
        print(f"⚠ Workflow '{workflow_data['name']}' already exists")
        # Try to get existing workflow ID
        list_response = requests.get(url, headers=HEADERS)
        if list_response.status_code == 200:
            workflows = list_response.json().get("data", [])
            for wf in workflows:
                if wf.get("name") == workflow_data["name"]:
                    return wf.get("id")
    else:
        print(f"✗ Failed to deploy workflow '{workflow_data['name']}': {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def main():
    print("Creating Wayfinder Supply Co. Agents and Workflows...")
    print("=" * 60)
    
    # Step 1: Deploy workflows first (get workflow IDs)
    print("\n1. Deploying Workflows...")
    workflow_dir = "config/workflows"
    
    workflows = {
        "check_trip_safety": f"{workflow_dir}/check_trip_safety.yaml",
        "get_customer_profile": f"{workflow_dir}/get_customer_profile.yaml",
        "get_user_affinity": f"{workflow_dir}/get_user_affinity.yaml"
    }
    
    workflow_ids = {}
    for name, path in workflows.items():
        if os.path.exists(path):
            workflow_id = deploy_workflow(path)
            if workflow_id:
                workflow_ids[name] = workflow_id
            time.sleep(1)  # Rate limiting
        else:
            print(f"⚠ Workflow file not found: {path}")
    
    # Step 2: Create tools (get tool IDs)
    print("\n2. Creating Tools...")
    tool_ids = []
    
    # Create ES|QL tool
    esql_query = """
FROM user-clickstream
| WHERE user_id == ?
| WHERE meta_tags IS NOT NULL
| EVAL tag = TO_STRING(meta_tags)
| STATS count = COUNT(*) BY tag
| SORT count DESC
| LIMIT 1
"""
    esql_tool_id = create_esql_tool(
        name="get_user_affinity",
        query=esql_query,
        description="Get user's gear preference affinity from browsing behavior"
    )
    if esql_tool_id:
        tool_ids.append(esql_tool_id)
    time.sleep(1)
    
    # Create workflow tools
    workflow_tool_ids = {}
    for name, workflow_id in workflow_ids.items():
        descriptions = {
            "check_trip_safety": "Get weather conditions and road alerts for a trip destination",
            "get_customer_profile": "Retrieve customer profile including purchase history and loyalty tier",
            "get_user_affinity": "Get user's gear preference affinity from browsing behavior"
        }
        tool_id = create_workflow_tool(
            name=name,
            workflow_id=workflow_id,
            description=descriptions.get(name, f"Workflow: {name}")
        )
        if tool_id:
            workflow_tool_ids[name] = tool_id
            tool_ids.append(tool_id)
        time.sleep(1)
    
    # Create index search tool
    index_tool_id = create_index_search_tool(
        name="product_search",
        index="product-catalog",
        description="Search the product catalog for gear recommendations"
    )
    if index_tool_id:
        tool_ids.append(index_tool_id)
    time.sleep(1)
    
    # Step 3: Create agents (reference tool IDs)
    print("\n3. Creating Agents...")
    trip_planner_id = create_trip_planner_agent(tool_ids=tool_ids)
    time.sleep(1)
    
    trip_itinerary_id = create_trip_itinerary_agent()
    time.sleep(1)
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print(f"Trip Planner Agent ID: {trip_planner_id}")
    print(f"Trip Itinerary Agent ID: {trip_itinerary_id}")
    print(f"Created {len(tool_ids)} tools")
    print("=" * 60)


if __name__ == "__main__":
    main()

