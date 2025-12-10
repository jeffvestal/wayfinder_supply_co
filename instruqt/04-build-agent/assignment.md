---
slug: build-agent
id: fmn5tessjtya
type: challenge
title: Build an Agent
teaser: Create an AI agent that orchestrates workflows and tools to plan trips
tabs:
- id: ieur95euxyid
  title: Kibana Agent Builder
  type: service
  hostname: kubernetes-vm
  path: /app/agent_builder
  port: 30001
- id: rkawx4ic31pz
  title: Terminal
  type: terminal
  hostname: host-1
difficulty: advanced
timelimit: 1800
enhanced_loading: null
---

# Build an Agent

In this challenge, you'll create the **Trip Planner Agent** - the main orchestrator that uses all the tools and workflows to create personalized trip recommendations.

---

## What You'll Build

You'll create an agent that:
- Uses multiple tools (workflows, ES|QL, index search)
- Orchestrates trip planning steps
- Personalizes recommendations based on customer data
- Follows safety guidelines and catalog restrictions

---

## Understanding Agents

**Agents** are AI assistants that:
- Understand natural language queries
- Decide which tools to use
- Chain multiple tool calls together
- Synthesize results into helpful responses

**Key Components:**
- **Instructions**: System prompt that defines the agent's role and behavior
- **Tools**: Capabilities the agent can use (workflows, ES|QL, search)
- **Description**: What the agent does (used for agent selection)

---

## Step 1: Get Your Tool IDs

Before creating the agent, you need the IDs of all available tools:

1. Open the [button label="Terminal"](tab-1) tab

2. Get all tool IDs:

```bash
export KIBANA_URL="http://kubernetes-vm:30001"
export ES_APIKEY="${STANDALONE_ELASTICSEARCH_APIKEY}"

# Get all tools
TOOLS_RESPONSE=$(curl -s -X GET "$KIBANA_URL/api/agent_builder/tools" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana")

# Extract tool IDs
PRODUCT_SEARCH_ID=$(echo "$TOOLS_RESPONSE" | jq -r '.data[] | select(.id | contains("product-search")) | .id')
CHECK_TRIP_SAFETY_ID=$(echo "$TOOLS_RESPONSE" | jq -r '.data[] | select(.id | contains("check-trip-safety")) | .id')
GET_CUSTOMER_PROFILE_ID=$(echo "$TOOLS_RESPONSE" | jq -r '.data[] | select(.id | contains("get-customer-profile")) | .id')
GET_USER_AFFINITY_ID=$(echo "$TOOLS_RESPONSE" | jq -r '.data[] | select(.id | contains("get-user-affinity")) | .id')

echo "Product Search: $PRODUCT_SEARCH_ID"
echo "Check Trip Safety: $CHECK_TRIP_SAFETY_ID"
echo "Get Customer Profile: $GET_CUSTOMER_PROFILE_ID"
echo "Get User Affinity: $GET_USER_AFFINITY_ID"

# Create array of all tool IDs
TOOL_IDS="[\"$PRODUCT_SEARCH_ID\", \"$CHECK_TRIP_SAFETY_ID\", \"$GET_CUSTOMER_PROFILE_ID\", \"$GET_USER_AFFINITY_ID\"]"
echo "Tool IDs array: $TOOL_IDS"
```

Save these IDs - you'll need them when creating the agent!

---

## Step 2: Create Agent Instructions

The agent instructions define its behavior. Here's a scaffolded version - you'll fill in key sections:

**Create a file `agent_instructions.txt` with this content:**

```
You are the Wayfinder Supply Co. Adventure Logistics Agent. Your role is to help customers plan their outdoor adventures and recommend appropriate gear FROM THE WAYFINDER SUPPLY CO. CATALOG ONLY.

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

Always prioritize safety and use ONLY Wayfinder catalog products in recommendations.
```

---

## Step 3: Create the Agent

Create the agent using the Agent Builder API:

```bash
# Read instructions from file (or paste directly)
INSTRUCTIONS=$(cat agent_instructions.txt | jq -Rs .)

# Create the agent
curl -X POST "$KIBANA_URL/api/agent_builder/agents" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  -d "{
    \"id\": \"trip-planner-agent\",
    \"name\": \"Trip Planner Agent\",
    \"description\": \"Main orchestrator agent that plans trips and recommends gear based on location, weather, customer profile, and preferences.\",
    \"configuration\": {
      \"instructions\": $INSTRUCTIONS,
      \"tools\": [{
        \"tool_ids\": $TOOL_IDS
      }]
    }
  }"
```

**Key Fields:**
- `id`: Unique identifier (`trip-planner-agent`)
- `name`: Display name
- `description`: What the agent does
- `configuration.instructions`: The full instructions text
- `configuration.tools[0].tool_ids`: Array of tool IDs from Step 1

---

## Step 4: Verify the Agent

Check that your agent was created:

```bash
curl -s -X GET "$KIBANA_URL/api/agent_builder/agents" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  | jq '.data[] | select(.id=="trip-planner-agent")'
```

---

## Step 5: Test the Agent

1. Open the [button label="Kibana Agent Builder"](tab-0) tab

2. Navigate to **Machine Learning** → **Agent Builder** → **Agents**

3. Find your **Trip Planner Agent** and click **Test**

4. Try a query like:
   ```
   I'm planning a 3-day backpacking trip to Yosemite next weekend. What gear do I need?
   ```

5. Watch the agent:
   - Call `check_trip_safety` for weather
   - Call `get_customer_profile` for user data
   - Call `get_user_affinity` for preferences
   - Call `product_search` multiple times for gear
   - Synthesize everything into a recommendation

---

## Understanding Agent Behavior

Your agent follows this decision-making process:

1. **Receives user query**: "Planning trip to Yosemite..."
2. **Decides to check safety**: Calls `check_trip_safety` workflow
3. **Gets customer context**: Calls `get_customer_profile` workflow
4. **Understands preferences**: Calls `get_user_affinity` tool
5. **Searches catalog**: Calls `product_search` for each gear category
6. **Synthesizes**: Combines all data into personalized recommendations

The agent uses its instructions to decide:
- Which tools to call
- In what order
- How to interpret results
- What to include in the final response

---

## Understanding Other Agents

While you built the Trip Planner, the system also includes:

**Trip Itinerary Agent** - Content synthesis:
- Formats trip plans as markdown
- Applies loyalty perks
- Creates day-by-day itineraries
- No tools needed (just formatting)

**Context Extractor Agent** - Parsing:
- Extracts structured data from queries
- Returns JSON only
- Used by other agents for data extraction

---

## Verification

Your agent should:
- ✅ Be created and visible in Agent Builder
- ✅ Have all 4 tools assigned
- ✅ Have complete instructions
- ✅ Successfully respond to trip planning queries
- ✅ Use tools in the correct order
- ✅ Only recommend catalog products

Once verified, you're ready for the final challenge: **Testing everything together**!

---

## Troubleshooting

**Agent not appearing?**
- Check that all tool IDs are correct
- Verify instructions are properly formatted JSON
- Ensure you included the `x-elastic-internal-origin: kibana` header

**Agent not calling tools?**
- Verify tools are assigned correctly
- Check tool descriptions are clear (agents use these to decide)
- Review agent execution logs in Kibana

**Agent recommending wrong products?**
- Check instructions emphasize catalog-only rule
- Verify product_search tool is working
- Review tool call sequence in execution logs

**Need help?**
- Review agent examples in Agent Builder UI
- Check execution logs for debugging
- Check `docs/AGENT_CHEATSHEET.md` in the repo for reference (TODO: add as tab)

---

## Next Steps

In the final challenge, you'll test your complete system - workflow, tool, and agent - working together in the full Wayfinder application!

