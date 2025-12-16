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

Throughout this workshop, you've created different types of agentic tools:
1. **Workflow** - `get_customer_profile`
	 - Connects to MCP server for CRM data
3. **Tool** - `tool-workflow-get-customer-profile`
	- Makes workflow available to agents
4. **Agent** - `trip-planner-agent`
	- Orchestrates all tools to plan trips

Now let's see them work together!

---

## Step 1: Test in Wayfinder UI

1. Open the [button label="Wayfinder UI"](tab-0) tab
	> [!NOTE]
	> If you need more screen space, you can  open the Wayfinder store in a new tab by clicking
	>
	> the second tab [button label="UI (Popout)"](tab-1)

2. Click on **Trip Planner**
	![CleanShot 2025-12-16 at 11.26.33@2x.png](../assets/CleanShot%202025-12-16%20at%2011.26.33%402x.png)

3. Try a trip planning query.In the chat box at the bottom enter:
   ```
   I'm planning a 3-day backpacking trip to Banff next weekend. What gear do I need?
   ```
	 Click `Send`
	 ![CleanShot 2025-12-16 at 11.30.37@2x.png](../assets/CleanShot%202025-12-16%20at%2011.30.37%402x.png)

4. **View our Plan** <br>
Just like chatting with our agent in Kibana, this custom Trip Planner will give varying answers (Because its the same agent!).
But, you should see a similar trip plan
![CleanShot 2025-12-16 at 11.33.26@2x.png](../assets/CleanShot%202025-12-16%20at%2011.33.26%402x.png)

4. **Review the Thought Trace** <br>
Also just as we did in Kibana, we can view the thought trace of the agent. Here click on `Completed xx steps`
You'll see some of the following calls
   - ✅ `check_trip_safety` workflow called (weather data)
   - ✅ `get_customer_profile` workflow called (your workflow!)
   - ✅ `get_user_affinity` tool called (preferences)
   - ✅ `product_search` tool called multiple times (gear recommendations)
   - ✅ Agent synthesizing the response
	![CleanShot 2025-12-16 at 11.36.42@2x.png](../assets/CleanShot%202025-12-16%20at%2011.36.42%402x.png)

6. **E-Commerce tie-in**<br>
Our Agent and tools built a helpful trip itineary for our customer. However, ultimately as an e-commerce store we are selling products. <br>
Our trip planner extracts
	1. product suggests, which we sell. Users can click on the + in the small card to add the item to the cart
	 ![CleanShot 2025-12-16 at 11.40.03@2x.png](../assets/CleanShot%202025-12-16%20at%2011.40.03%402x.png)
	1. Daily trip itinary details
	![CleanShot 2025-12-16 at 11.42.55@2x.png](../assets/CleanShot%202025-12-16%20at%2011.42.55%402x.png)


---

## Step 3: Test Personalization

1. Switch to different user personas using the user switcher (top right)

2. Try the same query with different users:
   - **Jordan Explorer** (new user) - Should get general recommendations
   - **Alex Hiker** (Platinum, ultralight) - Should see premium, lightweight gear
   - **Casey Campground** (Business) - Should see bulk pricing options

3. Notice how your `get_customer_profile` workflow provides different data for each user!

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


## Congratulations! 🎉

You've completed the Wayfinder Supply Co. workshop and built a complete agentic search system. You now understand how to:

- Create workflows that connect to external systems
- Build tools that make workflows available to agents
- Design agents that orchestrate multiple capabilities
- Integrate everything into a working application

**You're ready to build your own agentic search experiences!**

