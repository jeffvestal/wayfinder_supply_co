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

KIBANA_URL = os.getenv("STANDALONE_KIBANA_URL", os.getenv("KIBANA_URL", "http://kubernetes-vm:30001"))
ES_APIKEY = os.getenv("STANDALONE_ELASTICSEARCH_APIKEY", os.getenv("ELASTICSEARCH_APIKEY", ""))

if not ES_APIKEY:
    raise ValueError("STANDALONE_ELASTICSEARCH_APIKEY (or ELASTICSEARCH_APIKEY) environment variable is required")

HEADERS = {
    "Authorization": f"ApiKey {ES_APIKEY}",
    "Content-Type": "application/json",
    "kbn-xsrf": "true",
    "x-elastic-internal-origin": "kibana",  # Required for internal Kibana APIs
}

# Track failures for exit code
FAILURES = 0

# Retry configuration for transient errors
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 3  # seconds
RETRYABLE_STATUS_CODES = [502, 503, 504, 429]


def request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    """Make an HTTP request with retry logic for transient failures."""
    retry_delay = INITIAL_RETRY_DELAY
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.request(method, url, timeout=60, **kwargs)
            
            if response.status_code in RETRYABLE_STATUS_CODES:
                if attempt < MAX_RETRIES - 1:
                    print(f"  ⚠ Transient error ({response.status_code}), retrying in {retry_delay}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 30)  # Exponential backoff, max 30s
                    continue
            
            return response
            
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES - 1:
                print(f"  ⚠ Request timeout, retrying in {retry_delay}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)
                continue
            raise
        except requests.exceptions.ConnectionError:
            if attempt < MAX_RETRIES - 1:
                print(f"  ⚠ Connection error, retrying in {retry_delay}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)
                continue
            raise
    
    return response  # Return last response if all retries failed


def delete_agent(agent_id: str) -> bool:
    """Delete an agent if it exists."""
    url = f"{KIBANA_URL}/api/agent_builder/agents/{agent_id}"
    response = request_with_retry("DELETE", url, headers=HEADERS)
    if response.status_code in [200, 204]:
        print(f"  ↻ Deleted existing agent: {agent_id}")
        return True
    elif response.status_code == 404:
        return True  # Doesn't exist, that's fine
    return False


def delete_tool(tool_id: str) -> bool:
    """Delete a tool if it exists."""
    url = f"{KIBANA_URL}/api/agent_builder/tools/{tool_id}"
    response = request_with_retry("DELETE", url, headers=HEADERS)
    if response.status_code in [200, 204]:
        print(f"  ↻ Deleted existing tool: {tool_id}")
        return True
    elif response.status_code == 404:
        return True  # Doesn't exist, that's fine
    return False


def delete_workflow(workflow_id: str) -> bool:
    """Delete a workflow if it exists."""
    url = f"{KIBANA_URL}/api/workflows/{workflow_id}"
    response = request_with_retry("DELETE", url, headers=HEADERS)
    if response.status_code in [200, 204]:
        print(f"  ↻ Deleted existing workflow: {workflow_id}")
        return True
    elif response.status_code == 404:
        return True  # Doesn't exist, that's fine
    return False


def create_agent(agent_id: str, name: str, description: str, 
                 instructions: str, tool_ids: List[str]) -> Optional[str]:
    """Create an agent with correct API structure. Deletes existing agent first."""
    global FAILURES
    url = f"{KIBANA_URL}/api/agent_builder/agents"
    
    # Delete existing agent first (script is source of truth)
    delete_agent(agent_id)
    
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
    
    response = request_with_retry("POST", url, headers=HEADERS, json=agent_config)
    
    if response.status_code in [200, 201]:
        data = response.json()
        created_agent_id = data.get("id") or agent_id
        print(f"✓ Created agent: {name} (ID: {created_agent_id})")
        return created_agent_id
    else:
        print(f"✗ Failed to create agent '{name}': {response.status_code}")
        print(f"  Response: {response.text}")
        FAILURES += 1
        return None


def create_trip_planner_agent(tool_ids: List[str]) -> Optional[str]:
    """Create the main Trip Planner agent."""
    instructions = """You are the Wayfinder Supply Co. Adventure Logistics Agent. Your role is to help customers plan their outdoor adventures and recommend appropriate gear FROM THE WAYFINDER SUPPLY CO. CATALOG ONLY.

## USER CONTEXT
The user message may be prefixed with a `[User ID: user_id]` tag. 
1. Always look for this tag to identify the current user (e.g., `user_member`, `user_new`, `user_business`).
2. Use this `user_id` value for any tool calls that require a `user_id` parameter, specifically `get_customer_profile` and `get_user_affinity`.
3. If no User ID is provided, assume `user_new`.

## CRITICAL RULE: CATALOG-ONLY RECOMMENDATIONS

**NEVER recommend products from external brands like Mountain Hardwear, Big Agnes, Patagonia, North Face, REI, etc.**

You MUST:
1. ALWAYS use the product_search tool BEFORE making any gear recommendations
2. ONLY recommend products that are returned by the product_search tool
3. Include the EXACT product name and price from the search results
4. If the catalog doesn't have a suitable product, say "We don't currently carry [item type] but recommend looking for one with [specs]"

Wayfinder Supply Co. brands include: Wayfinder Supply, Summit Pro, TrailBlazer, and other house brands.

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
- If `covered: false` → Respond warmly and suggest similar covered destinations

## TRIP PLANNING STEPS

1. **Safety Check**: Use check_trip_safety workflow to get weather conditions and road alerts.

2. **Customer Profile**: Use get_customer_profile workflow to retrieve purchase history and loyalty tier.

3. **Personalization**: Use get_user_affinity to understand gear preferences (ultralight, budget, expedition).

4. **SEARCH CATALOG FIRST**: Before making ANY gear recommendations:
   - Use product_search to find "sleeping bags" for the trip conditions
   - Use product_search to find "tents" suitable for the season
   - Use product_search to find "backpacks" matching user preferences
   - Use product_search for any other needed categories
   
5. **Build Recommendations**: From the search results:
   - Select products that match the trip requirements
   - Include the exact product name and price from the catalog
   - Note items the customer already owns (from purchase_history)

6. **Synthesis**: Create a trip plan with:
   - Trip overview with location and dates
   - Weather summary and conditions
   - **Recommended Gear from Wayfinder Catalog** - ONLY products from search results:
     - Product Name - $XX.XX (include exact price)
     - Brief explanation why this product fits
   - Day-by-day itinerary
   - Safety notes
   - Loyalty perks (Platinum: free shipping, Business: bulk pricing)

Format your response as clean Markdown. For each recommended product, use this format:
- **[Product Name]** - $[Price] (why it fits)

Example: **Summit Pro Apex Expedition 20 Sleeping Bag** - $865.72 (rated to 20°F, perfect for winter camping)

If a product category has no matches in our catalog, say: "Note: We're expanding our [category] selection. Check back soon!"

Always prioritize safety and use ONLY Wayfinder catalog products in recommendations."""
    
    return create_agent(
        agent_id="trip-planner-agent",
        name="Trip Planner Agent",
        description="Main orchestrator agent that plans trips and recommends gear based on location, weather, customer profile, and preferences.",
        instructions=instructions,
        tool_ids=tool_ids
    )


def create_wayfinder_search_agent(tool_ids: List[str]) -> Optional[str]:
    """Create the general search agent for product recommendations."""
    instructions = """You are the Wayfinder Supply Co. Search Assistant. Help customers find outdoor gear from our catalog.

## USER CONTEXT
The user message may be prefixed with a `[User ID: user_id]` tag. 
1. Always look for this tag to identify the current user (e.g., `user_member`, `user_new`, `user_business`).
2. Use this `user_id` value for the `get_user_affinity` tool call if a `user_id` parameter is required.
3. If no User ID is provided, assume `user_new`.

## YOUR ROLE
- Search the product catalog to find gear that matches customer needs
- Provide helpful product recommendations with prices
- Answer questions about our products

## TOOLS
- product_search: Search the Wayfinder product catalog
- get_user_affinity: Get user preferences from browsing history

## IMPORTANT
- ONLY recommend products from the Wayfinder Supply Co. catalog
- Include product names and prices in your responses
- For trip planning questions, tell the user: "For full trip planning with weather and itinerary, check out our Trip Planner feature!"

Keep responses concise and helpful."""
    
    return create_agent(
        agent_id="wayfinder-search-agent",
        name="Wayfinder Search Assistant",
        description="Simple product search agent for finding gear in the catalog.",
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


def create_context_extractor_agent() -> Optional[str]:
    """Create the Context Extractor agent that parses trip queries into structured JSON."""
    instructions = """You extract trip information from user messages. Return ONLY valid JSON, no other text.

Extract:
- destination: The place/location name only (e.g., "Yosemite", "Rocky Mountains", "Patagonia")
- dates: When they're going (e.g., "next weekend", "December 14-16", "3 days", "this summer")
- activity: What they're doing (e.g., "backpacking", "camping", "hiking", "skiing")

Rules:
- destination: Extract only the location name, not surrounding words like "in" or "to"
- dates: Keep the user's original phrasing (e.g., "next weekend", "3 days", "December 14-16")
- activity: Use the primary activity mentioned (e.g., "backpacking", "camping", "hiking")

If a field can't be determined from the message, use null for that field.

Example input: "Planning a 3-day backpacking trip in Yosemite next weekend"
Example output: {"destination": "Yosemite", "dates": "next weekend", "activity": "backpacking"}

Example input: "Going camping"
Example output: {"destination": null, "dates": null, "activity": "camping"}

ONLY return the JSON object. No explanation, no markdown formatting, no code blocks, no extra text. Just the raw JSON."""
    
    return create_agent(
        agent_id="context-extractor-agent",
        name="Trip Context Extractor",
        description="Extracts destination, dates, and activity from user trip queries. Returns structured JSON only.",
        instructions=instructions,
        tool_ids=[]  # No tools needed - just parsing
    )


def create_response_parser_agent() -> Optional[str]:
    """Create the Response Parser agent that extracts structured data from trip plans."""
    instructions = """You extract structured data from trip planning responses. Return ONLY valid JSON, no other text.

Extract:
- products: Array of recommended products with name, price, category, and reason
- itinerary: Array of days with day number, title, distance, and activities
- safety_notes: Array of safety warnings and tips
- weather: Object with high, low, and conditions

JSON Schema:
{
  "products": [
    {"name": "Product Name", "price": 123.45, "category": "sleeping bag", "reason": "why recommended"}
  ],
  "itinerary": [
    {"day": 1, "title": "Day title", "distance": "4.7 miles", "activities": ["activity 1", "activity 2"]}
  ],
  "safety_notes": ["note 1", "note 2"],
  "weather": {"high": 45, "low": 28, "conditions": "Partly cloudy"}
}

Rules:
- Extract ALL products mentioned with their exact names and prices
- Parse prices as numbers (remove $ symbol)
- Include brand names in product names (e.g., "Summit Pro Apex Expedition 20 Sleeping Bag")
- If a field cannot be determined, use null or empty array
- ONLY return the JSON object. No explanation, no markdown, no extra text."""
    
    return create_agent(
        agent_id="response-parser-agent",
        name="Trip Response Parser",
        description="Extracts structured JSON from trip plan responses including products, itinerary, and safety info.",
        instructions=instructions,
        tool_ids=[]  # No tools needed - just parsing
    )


def create_itinerary_extractor_agent() -> Optional[str]:
    """Create the Itinerary Extractor agent that extracts structured day-by-day itinerary from trip plans."""
    instructions = """You extract a structured day-by-day itinerary from trip planning responses. Return ONLY valid JSON, no other text.

Extract the itinerary as an array of days. Each day should have:
- day: Day number (1, 2, 3, etc.)
- title: A descriptive title for the day (e.g., "Valley to Snow Creek", "Exploration Day", "Return Journey")
- activities: Array of specific activities/actions for that day

JSON Schema:
{
  "days": [
    {
      "day": 1,
      "title": "Day 1 Title",
      "activities": [
        "Start early from valley floor",
        "Gain elevation gradually with snowshoes",
        "Camp below treeline for wind protection"
      ]
    },
    {
      "day": 2,
      "title": "Day 2 Title",
      "activities": [
        "Practice winter camping skills",
        "Short radius exploration",
        "Return to established camp"
      ]
    }
  ]
}

Rules:
- Look for explicit day markers: "Day 1:", "Day 2:", "First day", "Second day", etc.
- Extract activities as individual items from bullet points, numbered lists, or sentences
- Each activity should be a complete, actionable item
- If the trip plan mentions a multi-day trip but doesn't break it down by days, infer logical day breaks based on the content
- If no day-by-day breakdown exists, create a single day entry with all activities
- ONLY return the JSON object. No explanation, no markdown code blocks, no extra text."""
    
    return create_agent(
        agent_id="itinerary-extractor-agent",
        name="Itinerary Extractor",
        description="Extracts structured day-by-day itinerary from trip plan responses. Returns JSON only.",
        instructions=instructions,
        tool_ids=[]  # No tools needed - just parsing
    )


def create_esql_tool(name: str, query: str, description: str, params: Optional[Dict] = None) -> Optional[str]:
    """Create an ES|QL tool and return its ID. Deletes existing tool first."""
    global FAILURES
    url = f"{KIBANA_URL}/api/agent_builder/tools"
    
    # Generate a unique ID for the tool
    tool_id = f"tool-esql-{name.replace('_', '-')}"
    
    # Delete existing tool first (script is source of truth)
    delete_tool(tool_id)
    
    tool_config = {
        "id": tool_id,
        "type": "esql",
        "description": description,
        "configuration": {
            "query": query,
            "params": params or {}  # Required by API
        }
    }
    
    response = request_with_retry("POST", url, headers=HEADERS, json=tool_config)
    
    if response.status_code in [200, 201]:
        data = response.json()
        created_id = data.get("id") or data.get("tool_id") or tool_id
        print(f"✓ Created ES|QL tool: {name} (ID: {created_id})")
        return created_id
    else:
        print(f"✗ Failed to create ES|QL tool (ID: {tool_id}): {response.status_code}")
        print(f"  Response: {response.text}")
        FAILURES += 1
        return None


def create_workflow_tool(name: str, workflow_id: str, description: str) -> Optional[str]:
    """Create a workflow tool and return its ID. Deletes existing tool first."""
    global FAILURES
    url = f"{KIBANA_URL}/api/agent_builder/tools"
    
    # Generate a unique ID for the tool
    tool_id = f"tool-workflow-{name.replace('_', '-')}"
    
    # Delete existing tool first (script is source of truth)
    delete_tool(tool_id)
    
    tool_config = {
        "id": tool_id,
        "type": "workflow",
        "description": description,
        "configuration": {
            "workflow_id": workflow_id
        }
    }
    
    response = request_with_retry("POST", url, headers=HEADERS, json=tool_config)
    
    if response.status_code in [200, 201]:
        data = response.json()
        created_id = data.get("id") or data.get("tool_id") or tool_id
        print(f"✓ Created workflow tool: {name} (ID: {created_id})")
        return created_id
    else:
        print(f"✗ Failed to create workflow tool (ID: {tool_id}): {response.status_code}")
        print(f"  Response: {response.text}")
        FAILURES += 1
        return None


def create_index_search_tool(name: str, index: str, description: str) -> Optional[str]:
    """Create an index search tool and return its ID. Deletes existing tool first."""
    global FAILURES
    url = f"{KIBANA_URL}/api/agent_builder/tools"
    
    # Generate a unique ID for the tool
    tool_id = f"tool-search-{name.replace('_', '-')}"
    
    # Delete existing tool first (script is source of truth)
    delete_tool(tool_id)
    
    tool_config = {
        "id": tool_id,
        "type": "index_search",
        "description": description,
        "configuration": {
            "pattern": index  # API expects 'pattern', not 'index'
        }
    }
    
    response = request_with_retry("POST", url, headers=HEADERS, json=tool_config)
    
    if response.status_code in [200, 201]:
        data = response.json()
        created_id = data.get("id") or data.get("tool_id") or tool_id
        print(f"✓ Created index search tool: {name} (ID: {created_id})")
        return created_id
    else:
        print(f"✗ Failed to create index search tool (ID: {tool_id}): {response.status_code}")
        print(f"  Response: {response.text}")
        FAILURES += 1
        return None


def get_workflow_id_by_name(workflow_name: str) -> Optional[str]:
    """Get workflow ID by name from list of workflows."""
    url = f"{KIBANA_URL}/api/workflows"
    list_response = request_with_retry("GET", url, headers=HEADERS)
    if list_response.status_code == 200:
        workflows = list_response.json().get("data", [])
        for wf in workflows:
            if wf.get("name") == workflow_name:
                return wf.get("id")
    return None


def deploy_workflow(workflow_yaml_path: str) -> Optional[str]:
    """Deploy a workflow from YAML file. Deletes existing workflow first."""
    global FAILURES
    import yaml
    
    # Read the raw YAML content as a string - API expects {"yaml": "..."}
    with open(workflow_yaml_path, 'r') as f:
        yaml_content = f.read()
    
    # Also parse it to get the name for logging
    workflow_data = yaml.safe_load(yaml_content)
    workflow_name = workflow_data.get("name", "unknown")
    
    # Delete existing workflow first (script is source of truth)
    existing_id = get_workflow_id_by_name(workflow_name)
    if existing_id:
        delete_workflow(existing_id)
    
    url = f"{KIBANA_URL}/api/workflows"
    
    # API expects {"yaml": "<yaml_string>"}
    response = request_with_retry("POST", url, headers=HEADERS, json={"yaml": yaml_content})
    
    if response.status_code in [200, 201]:
        data = response.json()
        workflow_id = data.get("id") or data.get("workflow_id")
        print(f"✓ Deployed workflow: {workflow_name} (ID: {workflow_id})")
        return workflow_id
    else:
        print(f"✗ Failed to deploy workflow '{workflow_name}': {response.status_code}")
        print(f"  Response: {response.text}")
        FAILURES += 1
        return None


def main() -> int:
    """Main function. Returns number of failures (0 = success)."""
    import argparse
    parser = argparse.ArgumentParser(description="Create Wayfinder Supply Co. Agents, Tools, and Workflows")
    parser.add_argument(
        "--skip-workflows",
        nargs="*",
        default=[],
        help="Workflow names to skip (e.g., get_customer_profile)"
    )
    parser.add_argument(
        "--skip-tools",
        nargs="*",
        default=[],
        help="Tool names to skip (e.g., tool-workflow-get-customer-profile)"
    )
    parser.add_argument(
        "--skip-agents",
        nargs="*",
        default=[],
        help="Agent names to skip (e.g., trip-planner-agent)"
    )
    args = parser.parse_args()
    
    print("Creating Wayfinder Supply Co. Agents and Workflows...")
    print("=" * 60)
    if args.skip_workflows:
        print(f"Skipping workflows: {', '.join(args.skip_workflows)}")
    if args.skip_tools:
        print(f"Skipping tools: {', '.join(args.skip_tools)}")
    if args.skip_agents:
        print(f"Skipping agents: {', '.join(args.skip_agents)}")
    
    # Determine the correct path to config/workflows
    # Works whether run from repo root or from scripts directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)  # Go up one level from scripts/
    
    # Check multiple possible locations for workflow config
    possible_paths = [
        os.path.join(repo_root, "config", "workflows"),  # ../config/workflows (from scripts/)
        os.path.join(script_dir, "..", "config", "workflows"),  # Same, relative
        "config/workflows",  # From repo root
        "/opt/workshop-assets/config/workflows",  # Instruqt absolute path
    ]
    
    workflow_dir = None
    for path in possible_paths:
        if os.path.exists(path):
            workflow_dir = path
            print(f"Found workflow config at: {workflow_dir}")
            break
    
    if not workflow_dir:
        print("ERROR: Could not find workflow config directory!")
        print(f"Searched: {possible_paths}")
        return
    
    # Step 1: Deploy workflows first (get workflow IDs)
    print("\n1. Deploying Workflows...")
    
    workflows = {
        "check_trip_safety": f"{workflow_dir}/check_trip_safety.yaml",
        "get_customer_profile": f"{workflow_dir}/get_customer_profile.yaml",
        "get_user_affinity": f"{workflow_dir}/get_user_affinity.yaml"
    }
    
    workflow_ids = {}
    for name, path in workflows.items():
        if name in args.skip_workflows:
            print(f"⊘ Skipping workflow: {name}")
            continue
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
    
    # Create ES|QL tool - query with user_id parameter
    esql_query = """FROM user-clickstream
| WHERE user_id == ?user_id AND meta_tags IS NOT NULL
| STATS count = COUNT(*) BY meta_tags
| SORT count DESC
| LIMIT 5"""
    esql_tool_id = create_esql_tool(
        name="get_user_affinity",
        query=esql_query,
        description="Get top gear preference tags from user browsing behavior in clickstream data",
        params={"user_id": {"type": "keyword", "description": "The user ID to look up browsing history for"}}
    )
    if esql_tool_id:
        tool_ids.append(esql_tool_id)
    time.sleep(1)
    
    # Create workflow tools
    workflow_tool_ids = {}
    for name, workflow_id in workflow_ids.items():
        # Skip creating workflow tool for get_user_affinity - we use the ES|QL tool instead
        if name == "get_user_affinity":
            continue
        tool_name = f"tool-workflow-{name.replace('_', '-')}"
        if tool_name in args.skip_tools:
            print(f"⊘ Skipping tool: {tool_name}")
            continue
        descriptions = {
            "check_trip_safety": "Get weather conditions and road alerts for a trip destination",
            "get_customer_profile": "Retrieve customer profile including purchase history and loyalty tier"
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
    context_extractor_id = create_context_extractor_agent()
    time.sleep(1)
    
    response_parser_id = create_response_parser_agent()
    time.sleep(1)
    
    itinerary_extractor_id = create_itinerary_extractor_agent()
    time.sleep(1)
    
    # Create wayfinder-search-agent (always created, not skipped)
    wayfinder_search_id = create_wayfinder_search_agent(tool_ids=tool_ids)
    time.sleep(1)
    
    trip_planner_id = None
    if "trip-planner-agent" not in args.skip_agents:
        trip_planner_id = create_trip_planner_agent(tool_ids=tool_ids)
        time.sleep(1)
    else:
        print("⊘ Skipping agent: trip-planner-agent")
    
    trip_itinerary_id = create_trip_itinerary_agent()
    time.sleep(1)
    
    print("\n" + "=" * 60)
    if FAILURES > 0:
        print(f"Setup FAILED with {FAILURES} error(s)!")
    else:
        print("Setup Complete!")
    print(f"Context Extractor Agent ID: {context_extractor_id}")
    print(f"Response Parser Agent ID: {response_parser_id}")
    print(f"Itinerary Extractor Agent ID: {itinerary_extractor_id}")
    print(f"Wayfinder Search Agent ID: {wayfinder_search_id}")
    print(f"Trip Planner Agent ID: {trip_planner_id}")
    print(f"Trip Itinerary Agent ID: {trip_itinerary_id}")
    print(f"Created {len(tool_ids)} tools")
    print("=" * 60)
    
    # Return proper exit code
    return FAILURES


if __name__ == "__main__":
    import sys
    failures = main()
    sys.exit(failures if failures else 0)

