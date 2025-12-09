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
  port: 3000
- id: wayfinder-backend-api
  title: Backend API
  type: service
  hostname: host-1
  path: /
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

5. **Test Personalization**: Use the user switcher (top right) to change between:
   - **Jordan Explorer** - New user, no history
   - **Alex Hiker** - Platinum member, ultralight preference
   - **Casey Campground** - Business buyer, bulk orders

---

## Explore the Backend

1. Open the [button label="Kibana"](tab-1) tab

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

- [button label="Host-1 Terminal"](tab-2) - Frontend, backend, and MCP server logs
- [button label="Kubernetes VM Terminal"](tab-3) - Elasticsearch and Kibana

### Useful Commands

**Check services on host-1:**
```bash
docker ps
docker logs wayfinder-frontend
docker logs wayfinder-backend
```

**Check Elasticsearch health:**
```bash
curl -s localhost:9200/_cluster/health | jq
```

---

## What's Next?

Once you've explored the system, you understand how:
1. The frontend communicates with the backend proxy
2. The backend streams responses from Agent Builder
3. Workflows call the MCP server for weather and CRM data
4. The agent synthesizes everything into personalized recommendations

🎉 **You're ready to dive deeper into building your own agents and workflows!**

