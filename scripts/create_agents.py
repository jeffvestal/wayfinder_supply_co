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

# Default MCP URL used in Instruqt environment
INSTRUQT_MCP_URL = "http://host-1:8002/mcp"
INSTRUQT_BACKEND_URL = "http://host-1:8002"


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
The user message may be prefixed with context tags:
- `[User ID: user_id]` — Identifies the current user (e.g., `user_member`, `user_new`, `user_business`).
- `[Vision Context: description]` — If present, contains an AI analysis of a photo the user uploaded showing terrain, weather, and conditions.

1. Always look for the User ID tag. Use this `user_id` value for any tool calls that require a `user_id` parameter, specifically `get_customer_profile` and `get_user_affinity`.
2. If no User ID is provided, assume `user_new`.
3. If Vision Context is present, use the terrain/conditions description to inform your gear recommendations. Prioritize products suitable for the described environment (e.g., snow gear for snowy terrain, rain gear for wet conditions).

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

When a customer asks about a trip, you MUST use the ground_conditions tool to get real-time weather and trail conditions:

- The ground_conditions tool uses Google Search grounding to find current, real-world conditions
- **MANDATORY**: If ground_conditions returns data (HTTP 200), you MUST incorporate the weather/conditions information into your response. Never ignore or skip successfully returned weather data.
- Use the returned weather data to inform gear recommendations (e.g., cold-weather gear for snow, rain gear for wet conditions)
- Include a weather/conditions summary section in every trip plan response

## TRIP PLANNING STEPS — SPEED IS CRITICAL

Minimize tool calls. Use broad queries instead of many narrow ones.

1. **Conditions Check**: Use ground_conditions workflow to get real-time weather and trail conditions. **REQUIRED for every trip planning request.**

2. **Customer Profile + Personalization**: Use get_customer_profile to retrieve purchase history and loyalty tier. Use get_user_affinity to understand gear preferences.

3. **SEARCH CATALOG — ONE BROAD SEARCH**: Before making ANY gear recommendations:
   - Use product_search ONCE with a broad query combining the trip needs (e.g., "winter camping gear sleeping bag tent backpack" rather than separate searches for each category)
   - Do NOT make separate product_search calls for each gear category — this is too slow
   - One broad search returns all relevant products across categories
   
4. **Build Recommendations**: From the search results:
   - Select products that match the trip requirements
   - Include the exact product name and price from the catalog
   - Note items the customer already owns (from purchase_history)

5. **Synthesis**: Create a trip plan with:
   - Trip overview with location and dates
   - **Weather & Conditions** — ALWAYS include a dedicated section with the real-time weather data returned by ground_conditions. Summarize temperature, precipitation, wind, and any alerts. This information is critical for the user's safety.
   - **Recommended Gear from Wayfinder Catalog** - ONLY products from search results:
     - Product Name - $XX.XX (include exact price)
     - Brief explanation why this product fits, referencing weather conditions where relevant
   - **Day-by-day itinerary** — REQUIRED structure:
     - Determine the trip duration from the user's request. Interpret vague phrases: "about a week" = 7 days, "a few days" = 3, "long weekend" = 3, "a weekend" = 2. Use the exact number when specified.
     - You MUST create a separate section for EACH day using Markdown headers: "### Day 1: [Descriptive Title]", "### Day 2: [Descriptive Title]", etc.
     - Under each day header, list 2-5 specific activities as Markdown bullet points (using - prefix). Each bullet should be a short, actionable item (one sentence). Do NOT write paragraphs.
     - Example:
       ### Day 3: Vall de Sorteny Nature Park
       - Hike the lower-elevation botanical garden trail
       - Picnic lunch at the river overlook
       - Return to Ordino for dinner
     - Do NOT collapse a multi-day trip into a single overview — every day gets its own section
   - Safety notes informed by the weather conditions
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
The user message may be prefixed with context tags:
- `[User ID: user_id]` — Identifies the current user (e.g., `user_member`, `user_new`, `user_business`).
- `[Vision Context: product_type - description]` — If present, contains an AI analysis of a product the user photographed.
- `[Product Category: category]` — If present, the exact catalog category the product belongs to.

## SPEED IS CRITICAL — MINIMIZE TOOL CALLS

### When Vision Context IS present (image search):
1. **SKIP get_user_affinity** — the Vision Context already tells you exactly what to search for.
2. Call product_search ONCE. Include BOTH the product type AND the category in your query
   (e.g., "hiking boots in Hiking category" or "ski jacket in Winter Sports category").
   This ensures results are filtered to the correct category.
3. Present the top 4 matches with prices immediately. Do NOT search again.
4. Only recommend products from the category specified in [Product Category].

### Follow-up queries (user asks about a DIFFERENT product):
When the user's follow-up message asks for a different product type than the original search
(e.g., first search was "hiking boots", follow-up asks for "low cut shoes"):
1. Use the user's EXACT words for the product_search query — do NOT mix in terms from previous turns.
2. Keep the [Product Category] filter if present.
3. Example: If original search was "hiking boots" and user says "Do you have low cut shoes?",
   search for "low cut shoes in Hiking category" — NOT "low cut hiking boots".

### When Vision Context is NOT present (text search):
1. If User ID is provided, call get_user_affinity ONCE to get preferences.
2. Call product_search ONCE with the user's query.
3. Present results with prices.

## YOUR ROLE
- Search the product catalog to find gear that matches customer needs
- Provide helpful product recommendations with prices

## TOOLS
- product_search: Search the Wayfinder product catalog
- get_user_affinity: Get user preferences from browsing history (skip when Vision Context is present)

## IMPORTANT
- ONLY recommend products from the Wayfinder Supply Co. catalog
- Include product names and prices in your responses
- Use AT MOST 2 tool calls total per request — speed matters for the user experience
- Do NOT make multiple product_search calls with different terms — one broad search is better than many narrow ones
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
        tool_ids=[]
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
        tool_ids=[]
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
- Look for explicit day markers: "Day 1:", "Day 2:", "### Day 1:", "First day", "Second day", etc.
- Extract activities as individual items from bullet points, numbered lists, or sentences
- Each activity in the activities array should be ONE specific action or event (one sentence). If the source text uses paragraphs instead of bullet points, split each paragraph into individual sentences and use each sentence as a separate activity.
- Aim for 2-5 activities per day. Do not put an entire paragraph as a single activity.
- IMPORTANT: Look for trip duration clues in the text (e.g., "a week", "7 days", "5-day trip", "3 days"). If the text describes a multi-day trip but lacks explicit day markers, you MUST infer logical day breaks to match the stated duration — do NOT collapse a week-long trip into a single day.
- Only create a single day entry if the trip is genuinely a single-day outing (day hike, day trip, etc.)
- ONLY return the JSON object. No explanation, no markdown code blocks, no extra text."""
    
    return create_agent(
        agent_id="itinerary-extractor-agent",
        name="Itinerary Extractor",
        description="Extracts structured day-by-day itinerary from trip plan responses. Returns JSON only.",
        instructions=instructions,
        tool_ids=[]
    )


def _swap_param_types(params: Dict, to_legacy: bool = True) -> Dict:
    """Swap param types between newer API format and legacy ES field types.
    
    Newer clusters accept: string, integer, float, boolean, date
    Older clusters accept: text, keyword, long, integer, double, float, boolean, date, object, nested
    """
    type_map = {"string": "keyword"} if to_legacy else {"keyword": "string"}
    swapped = {}
    for key, value in params.items():
        new_value = dict(value)
        if new_value.get("type") in type_map:
            new_value["type"] = type_map[new_value["type"]]
        swapped[key] = new_value
    return swapped


def create_esql_tool(name: str, query: str, description: str, params: Optional[Dict] = None) -> Optional[str]:
    """Create an ES|QL tool and return its ID. Deletes existing tool first.
    
    Handles API compatibility: tries newer param types (string) first,
    falls back to legacy ES field types (keyword) for older clusters.
    """
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
    elif response.status_code == 400 and params and "types that failed validation" in response.text:
        # Fallback: try legacy ES field types (keyword instead of string) for older clusters
        print(f"  ⚠ Retrying with legacy param types (keyword)...")
        legacy_params = _swap_param_types(params, to_legacy=True)
        tool_config["configuration"]["params"] = legacy_params
        
        response = request_with_retry("POST", url, headers=HEADERS, json=tool_config)
        if response.status_code in [200, 201]:
            data = response.json()
            created_id = data.get("id") or data.get("tool_id") or tool_id
            print(f"✓ Created ES|QL tool: {name} (ID: {created_id}) [legacy param types]")
            return created_id
    
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


def create_index_search_tool(name: str, index: str, description: str, custom_instructions: str = None) -> Optional[str]:
    """Create an index search tool and return its ID. Deletes existing tool first."""
    global FAILURES
    url = f"{KIBANA_URL}/api/agent_builder/tools"
    
    # Generate a unique ID for the tool
    tool_id = f"tool-search-{name.replace('_', '-')}"
    
    # Delete existing tool first (script is source of truth)
    delete_tool(tool_id)
    
    config = {
        "pattern": index  # API expects 'pattern', not 'index'
    }
    if custom_instructions:
        config["custom_instructions"] = custom_instructions
    
    tool_config = {
        "id": tool_id,
        "type": "index_search",
        "description": description,
        "configuration": config
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


def delete_existing_workflows_by_name(workflow_name: str):
    """Delete all workflows with the given name."""
    url = f"{KIBANA_URL}/api/workflows/search"
    list_response = request_with_retry("POST", url, headers=HEADERS, json={"limit": 100, "page": 1, "query": ""})
    if list_response.status_code == 200:
        data = list_response.json()
        workflows = data.get("results", []) or data.get("data", [])
        for wf in workflows:
            if wf.get("name") == workflow_name:
                delete_workflow(wf.get("id"))

def deploy_workflow(workflow_yaml_path: str, mcp_url: Optional[str] = None, backend_url: Optional[str] = None, api_key: Optional[str] = None) -> Optional[str]:
    """Deploy a workflow from YAML file. Deletes existing workflow first.
    
    Args:
        workflow_yaml_path: Path to the workflow YAML file
        mcp_url: Optional MCP server URL to substitute for the default Instruqt MCP URL
        backend_url: Optional backend URL to substitute for the default Instruqt backend URL
        api_key: Optional API key to inject into workflow consts and HTTP step headers
    """
    global FAILURES
    import yaml
    
    # Read the raw YAML content as a string - API expects {"yaml": "..."}
    with open(workflow_yaml_path, 'r') as f:
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
    
    # Inject API key into consts and HTTP step headers if provided
    if api_key:
        workflow_data_tmp = yaml.safe_load(yaml_content)
        if "consts" not in workflow_data_tmp:
            workflow_data_tmp["consts"] = {}
        workflow_data_tmp["consts"]["api_key"] = api_key
        for step in workflow_data_tmp.get("steps", []):
            if step.get("type") == "http":
                with_block = step.get("with", {})
                if "headers" not in with_block:
                    with_block["headers"] = {}
                with_block["headers"]["X-Api-Key"] = "{{consts.api_key}}"
                step["with"] = with_block
        yaml_content = yaml.dump(workflow_data_tmp, default_flow_style=False, sort_keys=False)
        print(f"  → Injected API key into consts and HTTP headers")
    
    # Also parse it to get the name for logging
    workflow_data = yaml.safe_load(yaml_content)
    workflow_name = workflow_data.get("name", "unknown")
    
    # Delete existing workflow(s) first (script is source of truth)
    delete_existing_workflows_by_name(workflow_name)
    
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
    
    # Step 1: Create agents first (so workflows can reference them)
    print("\n1. Creating Agents...")
    context_extractor_id = create_context_extractor_agent()
    time.sleep(1)
    
    response_parser_id = create_response_parser_agent()
    time.sleep(1)
    
    itinerary_extractor_id = create_itinerary_extractor_agent()
    time.sleep(1)
    
    # Step 2: Deploy workflows (now that agents exist)
    print("\n2. Deploying Workflows...")
    if args.mcp_url:
        print(f"MCP URL override: {args.mcp_url}")
    if args.backend_url:
        print(f"Backend URL override: {args.backend_url}")
    if args.wayfinder_api_key:
        print(f"Wayfinder API key: {'*' * 4}{args.wayfinder_api_key[-4:]}")
    
    workflows = {
        "get_customer_profile": f"{workflow_dir}/get_customer_profile.yaml",
        "get_user_affinity": f"{workflow_dir}/get_user_affinity.yaml",
        "extract_trip_entities": f"{workflow_dir}/extract_trip_entities.yaml",
    }
    
    # Optional vision workflow (only if file exists)
    ground_conditions_path = f"{workflow_dir}/ground_conditions.yaml"
    if os.path.exists(ground_conditions_path):
        workflows["ground_conditions"] = ground_conditions_path
    
    workflow_ids = {}
    for name, path in workflows.items():
        if name in args.skip_workflows:
            print(f"⊘ Skipping workflow: {name}")
            continue
        if os.path.exists(path):
            workflow_id = deploy_workflow(path, mcp_url=args.mcp_url, backend_url=args.backend_url, api_key=args.wayfinder_api_key)
            if workflow_id:
                workflow_ids[name] = workflow_id
            time.sleep(1)  # Rate limiting
        else:
            print(f"⚠ Workflow file not found: {path}")
    
    # Step 3: Create tools (reference workflow IDs)
    print("\n3. Creating Tools...")
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
        params={"user_id": {"type": "string", "description": "The user ID to look up browsing history for"}}
    )
    if esql_tool_id:
        tool_ids.append(esql_tool_id)
    time.sleep(1)
    
    # Create workflow tools
    workflow_tool_ids = {}
    for name, workflow_id in workflow_ids.items():
        # Skip creating workflow tool for get_user_affinity - we use the ES|QL tool instead
        # Also skip extract_trip_entities - it's used internally/manually, not as an agent tool
        if name in ["get_user_affinity", "extract_trip_entities"]:
            continue
        tool_name = f"tool-workflow-{name.replace('_', '-')}"
        if tool_name in args.skip_tools:
            print(f"⊘ Skipping tool: {tool_name}")
            continue
        descriptions = {
            "get_customer_profile": "Retrieve customer profile including purchase history and loyalty tier",
            "ground_conditions": "Get real-time ground, weather, and trail conditions using Google Search grounding"
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
    
    # Create index search tool with category filtering guidance
    product_search_instructions = (
        "The product-catalog index has a 'category' field with these exact values: "
        "Accessories, Apparel, Camping, Climbing, Cycling, Fishing, Hiking, "
        "Tropical & Safari, Water Sports, Winter Sports. "
        "When the agent's query mentions a specific category, ALWAYS filter results "
        "to that category using WHERE category == '<category>'. For example, if the "
        "query mentions 'Hiking', only return products where category == 'Hiking'. "
        "This prevents returning unrelated products like ski boots for hiking queries. "
        "When searching by product type (e.g. boots, shoes, jackets), prefer MATCH on "
        "the 'title' field rather than 'description' to avoid matching accessories that "
        "merely mention the activity. Use LIMIT 10 to keep results focused."
    )
    index_tool_id = create_index_search_tool(
        name="product_search",
        index="product-catalog",
        description="Search the product catalog for gear recommendations",
        custom_instructions=product_search_instructions
    )
    if index_tool_id:
        tool_ids.append(index_tool_id)
    time.sleep(1)
    
    # Step 4: Create main agents (reference tool IDs)
    print("\n4. Creating Main Agents...")
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

