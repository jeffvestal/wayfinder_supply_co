# Field Demo: Short - Backend Focus (5 Minutes)

**Duration:** 5 minutes
**Time Split:** 1 min UI / 4 min Agent Builder + Workflows
**Audience:** Technical decision makers, architects
**Focus:** Technical elevator pitch - how it's built, not just what it does

---

## Goals

1. Quickly establish what the application does (1 minute UI demo)
2. Show Agent Builder: agents, tools, system prompts
3. Show Workflows: YAML definitions, MCP integration, external APIs
4. Demonstrate the Agent Builder + Workflows partnership (brain + hands)

---

## Pre-Demo Setup

- Wayfinder Trip Planner open (quick demo)
- Kibana Agent Builder tab open
- Kibana Workflows tab open
- Optionally: workflow YAML file ready to show

---

## Demo Script

### Scene 1: Quick UI Context (0:00-1:00)

**Talk Track:**
1. "Let me show you what we're building toward."
2. "This is an AI-powered trip planner for an outdoor gear store."
3. "Watch the thought trace - you can see the AI reasoning."
4. "Checking weather, looking up preferences, searching products."
5. "Personalized recommendations based on real data."
6. "Now let me show you how this is built."

**Notes/Action:**
1. Have Trip Planner open
2. Type: "I'm planning a trip to Yosemite in March"
3. Click Send
4. Let it run ~20 seconds showing thought trace
5. Show results briefly
6. Switch to Kibana

**Screenshot:** Trip Planner with thought trace, then Kibana

---

### Scene 2: Agent Builder - The Brain (1:00-2:30)

**Talk Track:**
1. "This is Elastic's Agent Builder."
2. "Here's our trip-planner-agent."
3. "Two key parts: the system prompt and the tools."
4. "The system prompt is plain English instructions."
   - "'You are a trip planning assistant for Wayfinder Supply Co.'"
   - "'Recommend gear appropriate for the destination and conditions.'"
5. "No code - just natural language."
6. "The tools are four capabilities:"
   - "product_search - semantic search"
   - "get_user_affinity - ES|QL clickstream query"
   - "Two workflow tools for external APIs"
7. "The agent decides which tools to call based on the question."

**Notes/Action:**
1. Show Agent Builder main page
2. Click trip-planner-agent
3. Show system prompt (scroll briefly)
4. Show tools panel
5. Point at each tool type

**Screenshot:** Agent Builder interface, system prompt, tools panel

---

### Scene 3: Workflows - The Hands (2:30-4:00)

**Talk Track:**
1. "Now Workflows - equally important."
2. "Agent Builder is the brain - it decides what to do."
3. "Workflows are the hands - they actually do it."
4. "Here's check_trip_safety."
5. "It's YAML - declarative, version-controlled, readable."
6. "Inputs: what the workflow accepts - location and dates."
7. "Steps: what it does - an HTTP call to our MCP server."
8. "MCP - Model Context Protocol - is the standard for AI tool integration."
9. "Our MCP server wraps the weather API."
10. "Same pattern for get_customer_profile - calls CRM."
11. "This architecture lets you integrate any external system:"
    - "Salesforce"
    - "ServiceNow"
    - "Your internal APIs"

**Notes/Action:**
1. Navigate to Management → Workflows
2. Click check_trip_safety
3. Show YAML structure
4. Point at inputs section
5. Point at steps section
6. Point at HTTP body with MCP call
7. Show get_customer_profile briefly

**Screenshot:** Workflow YAML editor showing structure

---

### Scene 4: The Architecture (4:00-4:30)

**Talk Track:**
1. "The architecture:"
   - "Agent Builder is the brain - AI reasoning, tool selection"
   - "Workflows are the hands - external API calls, data federation"
   - "Elasticsearch is the memory - products, clickstream"
2. "The agent decides 'I need weather data' → calls workflow tool → workflow hits MCP → MCP calls weather API → data flows back."
3. "All observable, all auditable, all in Elastic."

**Notes/Action:**
1. Can show diagram or explain verbally

**Screenshot:** Architecture diagram (optional)

---

### Scene 5: Close (4:30-5:00)

**Talk Track:**
1. "Questions about the architecture?"
2. "Happy to show you the 15-minute deep dive where we build an agent from scratch."

**Notes/Action:**
1. .

**Screenshot:** .

---

## Recap

This demo proves the technical architecture:

1. **Agent Builder** provides AI orchestration with configurable prompts and tools
2. **Workflows** enable external API integration via MCP protocol
3. **Elasticsearch** serves as the data foundation (products, clickstream, any data)
4. **The combination** creates agentic search: AI + real data + external systems

Key message: **Agent Builder is the brain, Workflows are the hands, Elasticsearch is the memory.**

---

## Technical Quick Reference

**Tool Types:**

| Type | Use Case | Example |
|------|----------|---------|
| `index_search` | Semantic/hybrid search | Product catalog |
| `esql` | Complex aggregations | Clickstream preferences |
| `workflow` | External API calls | Weather, CRM |

**Workflow Step Types:** `http`, `elasticsearch.search`, `elasticsearch.esql.query`, `console`, `if`

**MCP Protocol:** JSON-RPC 2.0 with `tools/call` method

---

## Common Technical Questions

**"Can we use our own LLM?"**
> "Agent Builder currently uses Elastic's hosted models or OpenAI. The architecture is designed to be model-agnostic over time."

**"How do Workflows handle errors?"**
> "YAML supports `on-failure` blocks with retry logic, delays, and fallback steps."

**"What about security for external APIs?"**
> "Workflows support headers for auth tokens. Use Elastic's secrets management or environment variables for API keys."

**"How does this scale?"**
> "Agent Builder runs in Kibana. Workflows execute in the Elastic cluster. Both scale with your Elastic deployment."
