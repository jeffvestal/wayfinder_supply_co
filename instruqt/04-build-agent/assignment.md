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
  path: /app/chat
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

## Step 1: Navigate to Agent Builder

1. Click the [button label="Kibana Agent Builder"](tab-0) tab

2. In the left sidebar, click **Agents**
   <!-- SCREENSHOT: Kibana left sidebar with "Agents" highlighted -->

3. You'll see a list of existing agents (some may be pre-created)
   <!-- SCREENSHOT: Agents list view -->

---

## Step 2: Create a New Agent

1. Click the **Create agent** button in the upper right
   <!-- SCREENSHOT: "Create agent" button location -->

2. You'll see the agent creation form

---

## Step 3: Configure Basic Information

Fill in the basic agent information:

| Field | Value |
|-------|-------|
| **Agent ID** | `trip-planner-agent` |
| **Name** | `Trip Planner Agent` |
| **Description** | `Main orchestrator agent that plans trips and recommends gear based on location, weather, customer profile, and preferences.` |

<!-- SCREENSHOT: Agent creation form with basic fields filled in -->

---

## Step 4: Add Agent Instructions

The instructions tell the agent how to behave. In the **Instructions** field, paste:

```
You are the Wayfinder Supply Co. Adventure Logistics Agent. Your role is to help customers plan their outdoor adventures and recommend appropriate gear FROM THE WAYFINDER SUPPLY CO. CATALOG ONLY.

## CRITICAL RULE: CATALOG-ONLY RECOMMENDATIONS

**NEVER recommend products from external brands like Mountain Hardwear, Big Agnes, Patagonia, North Face, REI, etc.**

You MUST:
1. ALWAYS use the product_search tool BEFORE making any gear recommendations
2. ONLY recommend products that are returned by the product_search tool
3. Include the EXACT product name and price from the search results
4. If the catalog doesn't have a suitable product, say "We don't currently carry [item type] but recommend looking for one with [specs]"

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
- If covered: true → Proceed with full trip planning
- If covered: false → Respond warmly and suggest similar covered destinations

## TRIP PLANNING STEPS

1. **Safety Check**: Use check_trip_safety workflow to get weather conditions
2. **Customer Profile**: Use get_customer_profile workflow for purchase history and loyalty tier
3. **Personalization**: Use get_user_affinity for gear preferences
4. **SEARCH CATALOG FIRST**: Use product_search for each gear category
5. **Build Recommendations**: From search results only
6. **Synthesis**: Create trip plan with weather, gear, itinerary, and safety notes

Format responses as clean Markdown. For each product:
- **[Product Name]** - $[Price] (why it fits)

Always prioritize safety and use ONLY Wayfinder catalog products in recommendations.
```

<!-- SCREENSHOT: Instructions text area with content -->

---

## Step 5: Assign Tools

Now assign the tools your agent can use:

1. In the **Tools** section, click **Add tools** or use the tool selector
   <!-- SCREENSHOT: Tools section with Add button -->

2. Select these tools (check the boxes):
   - ✅ `tool-search-product-search` (Product catalog search)
   - ✅ `tool-workflow-check-trip-safety` (Weather and safety)
   - ✅ `tool-workflow-get-customer-profile` (Your workflow from Challenge 3!)
   - ✅ `tool-esql-get-user-affinity` (User preferences)

   <!-- SCREENSHOT: Tool selection dialog with all four tools checked -->

3. Click **Add** or **Save** to confirm tool selection

---

## Step 6: Save the Agent

1. Review your configuration:
   - ID: `trip-planner-agent`
   - Name: `Trip Planner Agent`
   - Description: Mentions trip planning, weather, customer profile
   - Instructions: Full system prompt
   - Tools: 4 tools assigned

2. Click **Save agent** (or **Create**)
   <!-- SCREENSHOT: Save button highlighted -->

3. You should see a success message!

---

## Step 7: Test the Agent

1. Find your `trip-planner-agent` in the agents list

2. Click **Test** or open the agent's detail page and look for a test/chat interface
   <!-- SCREENSHOT: Test button or chat interface location -->

3. Try this query:
   ```
   I'm planning a 3-day backpacking trip to Yosemite next weekend. What gear do I need?
   ```

4. Watch the agent work! You should see:
   - 🔍 Calling `check_trip_safety` for weather
   - 👤 Calling `get_customer_profile` for user data
   - ❤️ Calling `get_user_affinity` for preferences
   - 🎒 Calling `product_search` multiple times for gear
   - ✍️ Synthesizing everything into a recommendation

   <!-- SCREENSHOT: Agent test results showing tool calls and final response -->

---

## Understanding Agent Behavior

Your agent follows this decision-making process:

1. **Receives user query**: "Planning trip to Yosemite..."
2. **Reads instructions**: Knows to check safety first
3. **Calls check_trip_safety**: Gets weather conditions
4. **Calls get_customer_profile**: Gets loyalty tier and history
5. **Calls get_user_affinity**: Understands gear preferences
6. **Calls product_search**: Finds relevant gear (multiple times)
7. **Synthesizes response**: Combines all data into personalized recommendations

The agent uses its instructions to decide:
- Which tools to call
- In what order
- How to interpret results
- What to include in the final response

---

## Verification Checklist

Your agent should:
- ✅ Be created and visible in Agent Builder
- ✅ Have all 4 tools assigned
- ✅ Have complete instructions
- ✅ Successfully respond to trip planning queries
- ✅ Call tools in the correct order
- ✅ Only recommend catalog products

Once verified, click **Check** to proceed to the final challenge: **Testing everything together**!

---

## Troubleshooting

**Agent not appearing?**
- Refresh the page
- Check that you clicked Save
- Verify there were no validation errors

**Tools not showing in selection?**
- Verify each tool exists in the Tools section
- For `get_customer_profile`, ensure you completed Challenge 3

**Agent not calling tools?**
- Check that tools are properly assigned
- Review the instructions - they guide tool selection
- Test each tool individually to ensure they work

**Agent recommending external brands?**
- Strengthen the instructions about catalog-only
- Ensure product_search tool is assigned and working

---

## Next Steps

In the final challenge, you'll test your complete system - workflow, tool, and agent - working together in the full Wayfinder application!

The Trip Planner in the Wayfinder UI uses this exact agent. You've just built the intelligence behind the app! 🎉
