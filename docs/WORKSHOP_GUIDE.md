# Wayfinder Supply Co. Workshop Guide

## Overview

This workshop demonstrates how to build an intelligent search experience using Elastic Agent Builder, Workflows, and semantic search. You'll learn how to:

- Federate data from multiple sources (Elasticsearch, CRM, Weather APIs)
- Personalize results based on user behavior
- Orchestrate workflows to synthesize complex information
- Build agents that make intelligent decisions

## Prerequisites

- Access to Elasticsearch 8.16+ with Agent Builder (tech preview)
- Kibana access with workflows feature enabled
- Basic understanding of Elasticsearch and Kibana

## Workshop Structure

### Challenge 1: Explore the Data

**Objective**: Understand the data structure and test basic search.

**Steps**:

1. **View Product Catalog**
   - Navigate to Kibana → Discover
   - Select `product-catalog` index
   - Explore product documents
   - Notice the `description.semantic` field (ELSER embeddings)

2. **View Clickstream Data**
   - Select `user-clickstream` index
   - Filter by `user_id: user_member`
   - Notice the `meta_tags` field showing user preferences

3. **Test Semantic Search**
   - Use Kibana Dev Tools to run:
   ```json
   GET product-catalog/_search
   {
     "query": {
       "match": {
         "description.semantic": "warm sleeping bag for winter camping"
       }
     }
   }
   ```

**Expected Outcome**: You understand the data structure and can see how semantic search works.

---

### Challenge 2: Build Your First Workflow

**Objective**: Create a workflow that calls the MCP server for weather data.

**Steps**:

1. **Navigate to Workflows**
   - Go to Management → Workflows
   - Click "Create workflow"

2. **Import Workflow**
   - Copy contents of `config/workflows/check_trip_safety.yaml`
   - Paste into workflow editor
   - Save as `check_trip_safety`

3. **Test the Workflow**
   - Click "Run workflow"
   - Input:
     - Location: "Rockies"
     - Dates: "January 15, 2024"
   - Observe the weather conditions returned

**Expected Outcome**: You have a working workflow that calls the MCP server.

---

### Challenge 3: Connect External Data

**Objective**: Create a workflow that retrieves customer profile from CRM.

**Steps**:

1. **Import CRM Workflow**
   - Create new workflow
   - Copy contents of `config/workflows/get_customer_profile.yaml`
   - Save as `get_customer_profile`

2. **Test the Workflow**
   - Run with `user_id: user_member`
   - Observe purchase history and loyalty tier

3. **Create Affinity Workflow**
   - Import `config/workflows/get_user_affinity.yaml`
   - Save as `get_user_affinity`
   - Test with `user_id: user_member`
   - Notice it returns "ultralight" preference

**Expected Outcome**: You have workflows that access CRM data and analyze user behavior.

---

### Challenge 4: Configure the Agent

**Objective**: Create and configure the Trip Planner agent.

**Steps**:

1. **Navigate to Agent Builder**
   - Go to Search → Agent Builder
   - Click "Create agent"

2. **Configure Trip Planner Agent**
   - Name: `trip-planner-agent`
   - Copy system prompt from `scripts/create_agents.py`
   - Add tools:
     - Index Search (product-catalog)
     - Workflow: check_trip_safety
     - Workflow: get_customer_profile
     - ES|QL: get_user_affinity query

3. **Create Itinerary Agent**
   - Create second agent: `trip-itinerary-agent`
   - Copy system prompt from `scripts/create_agents.py`
   - No tools needed (synthesis only)

4. **Test the Agent**
   - Use the chat interface
   - Ask: "I'm going camping in the Rockies this weekend"
   - Observe the agent's reasoning process

**Expected Outcome**: You have a working agent that orchestrates multiple tools.

---

### Challenge 5: Test the Experience

**Objective**: Use the full application end-to-end.

**Steps**:

1. **Access the Frontend**
   - Navigate to `http://host-1:3000`
   - Explore the storefront

2. **Test User Switching**
   - Use the user switcher in the header
   - Switch between:
     - Jordan Explorer (New Customer)
     - Alex Hiker (Platinum Member)
     - Casey Campground (Business)

3. **Test Chat Interface**
   - Click "Chat" tab
   - Ask about a trip:
     - "I'm going camping in the Rockies in January"
     - "Planning a summer hike in Yosemite"
   - Watch the Thought Trace panel show agent reasoning

4. **Test Cart Functionality**
   - Add products to cart from storefront
   - View cart and notice loyalty perks
   - Platinum members see free shipping
   - Business accounts see bulk discounts

**Expected Outcome**: You've experienced the full agentic search workflow.

---

## Troubleshooting

### Agent Not Responding

- Check that LLM connector is configured
- Verify agent tools are properly registered
- Check Kibana logs for errors

### Workflows Not Executing

- Verify MCP server is running: `http://host-1:8002/health`
- Check workflow inputs match expected format
- Review workflow execution logs in Kibana

### Products Not Showing

- Verify products are indexed: `GET product-catalog/_count`
- Check that semantic_text inference is working
- Ensure ELSER model is deployed

### Thought Trace Not Displaying

- Check browser console for errors
- Verify SSE connection to backend
- Ensure backend can connect to Kibana

---

## Next Steps

- Experiment with different trip scenarios
- Try modifying agent system prompts
- Create additional workflows for new use cases
- Explore the semantic search capabilities

## Resources

- [Elastic Workflows Reference](ELASTIC_WORKFLOWS_REFERENCE.md)
- [Instruqt Reference](INSTRUQT_REFERENCE.md)
- [Elastic Agent Builder Docs](https://www.elastic.co/docs/solutions/search/agent-builder)


