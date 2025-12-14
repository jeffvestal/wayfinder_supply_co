---
slug: integration
id: rls4juj7y8pb
type: challenge
title: Bring It All Together
teaser: Test your complete system - workflow, tool, and agent working together
tabs:
- id: oy109wuivmhk
  title: Wayfinder UI
  type: service
  hostname: host-1
  path: /
  port: 8000
- id: cylatfkglxou
  title: UI (Pop-out)
  type: service
  hostname: host-1
  path: /
  port: 8000
  new_window: true
- id: vefhempgf5yq
  title: Kibana
  type: service
  hostname: kubernetes-vm
  path: /
  port: 30001
- id: vgf86cqnhjdv
  title: Terminal
  type: terminal
  hostname: host-1
difficulty: basic
timelimit: 900
enhanced_loading: null
---

# Bring It All Together

Congratulations! You've built all the components. Now let's test your complete system - workflow, tool, and agent - working together in the full Wayfinder application.

---

## What You've Built

Throughout this workshop, you've created:

1. **Workflow** (`get_customer_profile`) - Connects to MCP server for CRM data
2. **Tool** (`tool-workflow-get-customer-profile`) - Makes workflow available to agents
3. **Agent** (`trip-planner-agent`) - Orchestrates all tools to plan trips

Now let's see them work together!

---

## Step 1: Verify All Components

Before testing, let's verify everything is deployed:

1. Open the [button label="Terminal"](tab-2) tab

2. Check your workflow:

```bash
export KIBANA_URL="http://kubernetes-vm:30001"
export ES_APIKEY="${STANDALONE_ELASTICSEARCH_APIKEY}"

# Check workflow
curl -s -X GET "$KIBANA_URL/api/workflows" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  | jq '.data[] | select(.name=="get_customer_profile") | {name, id, enabled}'
```

3. Check your tool:

```bash
curl -s -X GET "$KIBANA_URL/api/agent_builder/tools" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  | jq '.data[] | select(.id=="tool-workflow-get-customer-profile") | {id, type, description}'
```

4. Check your agent:

```bash
curl -s -X GET "$KIBANA_URL/api/agent_builder/agents" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  | jq '.data[] | select(.id=="trip-planner-agent") | {id, name, tool_count: (.configuration.tools[0].tool_ids | length)}'
```

All three should be present and configured correctly!

---

## Step 2: Test in Wayfinder UI

1. Open the [button label="Wayfinder UI"](tab-0) tab

2. Navigate to **Trip Planner**

3. Try a trip planning query:
   ```
   I'm planning a 3-day backpacking trip to Banff next weekend. What gear do I need?
   ```

4. **Watch the Thought Trace** panel on the right - you should see:
   - ✅ `check_trip_safety` workflow called (weather data)
   - ✅ `get_customer_profile` workflow called (your workflow!)
   - ✅ `get_user_affinity` tool called (preferences)
   - ✅ `product_search` tool called multiple times (gear recommendations)
   - ✅ Agent synthesizing the response

5. Notice how your `get_customer_profile` workflow appears in the trace!

---

## Step 3: Test Personalization

1. Switch to different user personas using the user switcher (top right)

2. Try the same query with different users:
   - **Jordan Explorer** (new user) - Should get general recommendations
   - **Alex Hiker** (Platinum, ultralight) - Should see premium, lightweight gear
   - **Casey Campground** (Business) - Should see bulk pricing options

3. Notice how your `get_customer_profile` workflow provides different data for each user!

---

## Step 4: Verify Agent Behavior

1. Open the [button label="Kibana"](tab-1) tab

2. Navigate to **Machine Learning** → **Agent Builder** → **Agents**

3. Click on your **Trip Planner Agent**

4. Click **Test** and try a query

5. Review the execution:
   - Check that all tools are called
   - Verify the tool call sequence
   - Confirm the agent follows its instructions

---

## Step 5: Check Execution Logs

1. In Kibana, navigate to **Observability** → **Logs**

2. Filter for workflow executions:
   ```
   workflow.name: get_customer_profile
   ```

3. Review the logs to see:
   - Workflow execution details
   - MCP server calls
   - Customer profile data returned

---

## What You've Accomplished

You've successfully built a complete agentic search system:

✅ **Workflow** - Automated data retrieval from external systems
✅ **Tool** - Made workflow available to AI agents
✅ **Agent** - Orchestrated multiple tools to create intelligent responses
✅ **Integration** - All components working together seamlessly

---

## Understanding the Full Flow

Here's what happens when a user asks about a trip:

1. **User Query** → Frontend sends to Backend
2. **Backend** → Proxies to Agent Builder
3. **Agent** → Decides to call `check_trip_safety` workflow
4. **Workflow** → Calls MCP server for weather
5. **Agent** → Decides to call `get_customer_profile` workflow (your workflow!)
6. **Workflow** → Calls MCP server for CRM data
7. **Agent** → Calls `get_user_affinity` for preferences
8. **Agent** → Calls `product_search` multiple times for gear
9. **Agent** → Synthesizes all data into personalized recommendations
10. **Response** → Streams back to user via SSE

Your workflow is a critical part of this flow, providing customer context that enables personalization!

---

## Next Steps

Now that you've built the complete system, you can:

- **Extend workflows** - Add more steps, call additional APIs
- **Create more tools** - Wrap other workflows or create ES|QL tools
- **Enhance agents** - Add more sophisticated reasoning, chain multiple agents
- **Explore patterns** - Review other workflows and agents in the system

---

## Troubleshooting

**Workflow not appearing in trace?**
- Verify workflow is enabled: `curl ... | jq '.data[] | select(.name=="get_customer_profile") | .enabled'`
- Check agent has the tool assigned
- Review agent execution logs

**Agent not calling your workflow?**
- Verify tool is assigned to agent
- Check tool description is clear
- Review agent instructions mention customer profile

**Need help?**
- Check execution logs in Kibana
- Review workflow execution history
- Test workflow directly via API

---

## Congratulations! 🎉

You've completed the Wayfinder Supply Co. workshop and built a complete agentic search system. You now understand how to:

- Create workflows that connect to external systems
- Build tools that make workflows available to agents
- Design agents that orchestrate multiple capabilities
- Integrate everything into a working application

**You're ready to build your own agentic search experiences!**

