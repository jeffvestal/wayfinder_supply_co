---
slug: explore-wayfinder
id: fcvl6itrtygc
type: challenge
title: Explore Wayfinder Supply Co.
teaser: Get familiar with the AI-powered outdoor gear store and trip planning assistant
tabs:
- id: cjygovddb1id
  title: Wayfinder UI
  type: service
  hostname: host-1
  path: /
  port: 8000
- id: popout-ui-01
  title: UI (Pop-out)
  type: service
  hostname: host-1
  path: /
  port: 8000
  new_window: true
- id: 0ukl1c9nexnd
  title: Architecture Diagram
  type: service
  hostname: host-1
  path: /architecture.html
  port: 8000
- id: wdzfceiayicy
  title: Kibana
  type: service
  hostname: kubernetes-vm
  path: /
  port: 30001
- id: ecubvuno5dj6
  title: Host-1 Terminal
  type: terminal
  hostname: host-1
- id: 3ma0vzwdlavt
  title: Kubernetes VM Terminal
  type: terminal
  hostname: kubernetes-vm
difficulty: basic
timelimit: 3600
enhanced_loading: null
---

# Welcome to Wayfinder Supply Co.

Wayfinder Supply Co. is an AI-powered outdoor gear retailer that demonstrates **Elastic Agentic Search** capabilities.

In this workshop, you'll explore how the system:
- **Federates data** from Elasticsearch, CRM, and Weather APIs
- **Personalizes recommendations** based on user behavior
- **Plans trips** with an AI agent that understands weather, gear, and customer context

---

## Explore the Store

1. Open the [button label="Wayfinder UI"](tab-0) tab

2. **Browse Products**: Scroll through the product catalog and notice the categories

3. **Try the Trip Planner**: Click **Trip Planner** in the navigation
   - Enter a destination like "Banff" or "Yosemite"
   - Ask: *"I'm planning a camping trip to Banff next weekend. What gear do I need?"*

4. **Watch the Agent Think**: Notice the **Thought Trace** panel on the right showing:
   - Tool calls to check weather conditions
   - Customer profile lookups
   - Product searches
   - How the agent orchestrates multiple data sources

5. **Test Personalization**: Use the user switcher (top right) to change between:
   - **Jordan Explorer** - New user, no history
   - **Alex Hiker** - Platinum member, ultralight preference
   - **Casey Campground** - Business buyer, bulk orders

   Notice how recommendations change based on user preferences and purchase history!

---

## Understand the Architecture

1. Open the [button label="Architecture Diagram"](tab-1) tab to see how all the components connect

2. **Key Components**:
   - **Frontend** (React) - User interface with chat and thought trace
   - **Backend Proxy** (FastAPI) - Routes requests to Agent Builder
   - **Agent Builder** - Orchestrates workflows and tools
   - **Workflows** - Connect to MCP server (CRM, Weather) and Elasticsearch
   - **Elasticsearch** - Product catalog and user clickstream data
   - **MCP Server** - Simulates external enterprise systems

---

## Explore the Backend

1. Open the [button label="Kibana"](tab-2) tab

2. Navigate to **Dev Tools** → **Console** to query the indices:
   ```
   GET product-catalog/_search
   {
     "size": 5
   }
   ```

3. Check the clickstream data:
   ```
   GET user-clickstream/_search
   {
     "size": 5,
     "query": {
       "match": {
         "user_id": "user_member"
       }
     }
   }
   ```

---

## Terminal Access

Use the terminal tabs for debugging:

- [button label="Host-1 Terminal"](tab-3) - Frontend, backend, and MCP server logs
- [button label="Kubernetes VM Terminal"](tab-4) - Elasticsearch and Kibana

### Useful Commands

**Check services on host-1:**
```bash
# Check if backend is running (serves both API and frontend)
curl -s localhost:8000/health

# View backend logs (includes frontend serving)
tail -n20 /var/log/backend.log

# View MCP server logs
tail -n20 /var/log/mcp-server.log

# Check running processes
ps aux | grep uvicorn
```

---

## What's Next?

You've just seen an AI agent orchestrate weather data, customer profiles, product searches, and behavioral insights to create personalized trip recommendations.

**In the next challenges, you'll build the components that make this possible:**
- **Challenge 2**: Build a workflow that connects to external systems
- **Challenge 3**: Create a tool that agents can use
- **Challenge 4**: Build an agent that orchestrates everything
- **Challenge 5**: Test your components in the full application

🎉 **Ready to build? Let's start with workflows!**

