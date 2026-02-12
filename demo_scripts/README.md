# Wayfinder Supply Co. Demo Scripts

Demo content for YouTube videos and field engineer presentations showcasing Elastic's Agentic Search capabilities.

## Quick Links

| Demo Type | Duration | File | Audience |
|-----------|----------|------|----------|
| **YouTube: Trip Planner** | 5-7 min | [youtube/01_trip_planner.md](youtube/01_trip_planner.md) | Developers |
| **YouTube: Search Comparison** | 5-7 min | [youtube/02_search_comparison.md](youtube/02_search_comparison.md) | Developers |
| **YouTube: Personalization** | 5-7 min | [youtube/03_personalization.md](youtube/03_personalization.md) | Developers |
| **YouTube: Workflows** | 8-10 min | [youtube/04_workflows.md](youtube/04_workflows.md) | Developers |
| **YouTube: Full Walkthrough** | 10 min | [youtube/05_full_walkthrough.md](youtube/05_full_walkthrough.md) | Developers |
| **Field: Micro** | 1 min | [field/micro_1min.md](field/micro_1min.md) | Executives |
| **Field: Short (UI Focus)** | 5 min | [field/short_5min_ui_focus.md](field/short_5min_ui_focus.md) | Business stakeholders |
| **Field: Short (Backend Focus)** | 5 min | [field/short_5min_backend_focus.md](field/short_5min_backend_focus.md) | Technical decision makers |
| **Field: Builder** | 15 min | [field/builder_15min.md](field/builder_15min.md) | Developers/Architects |

---

## Prerequisites

Before presenting any demo, ensure:

1. **Wayfinder is running** - `docker-compose up -d` or Instruqt environment
2. **Data is loaded** - Products, clickstream, and user personas exist
3. **Agent Builder is configured** - `trip-planner-agent` is deployed with all tools
4. **Workflows are deployed** - `check_trip_safety` and `get_customer_profile` workflows

### Quick Validation

```bash
# Check backend health
curl http://localhost:8000/api/health

# Check products exist
curl http://localhost:8000/api/products | jq '.total'

# Test agent (should stream response)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "user_new"}'
```

---

## The Core Story

All demos share the same foundational narrative:

### The Problem
> "Standard search can't answer: 'I'm planning a 3-day backpacking trip to Yosemite in March.' Because the answer depends on weather conditions, your purchase history, your preferences, and which products actually fit your needs."

### The Solution
> "Agentic search doesn't just find keywords - it reasons about your intent, federates data from multiple sources, and recommends exactly what you need."

### The Demo Query
Use this query across all demos for consistency:
> **"I'm planning a 3-day backpacking trip to Yosemite in March. What gear should I bring?"**

---

## Key Talking Points

### Agent Builder + Workflows (Equal Billing)

| Component | Role | What It Does |
|-----------|------|--------------|
| **Agent Builder** | The AI brain | Reasoning, intent understanding, tool orchestration |
| **Workflows** | The hands | External API calls, MCP integration, data federation |

The magic: Agent decides "I need weather data" → calls workflow tool → workflow hits MCP server → returns real conditions → agent incorporates into recommendation.

### The Four Tools

| Tool | Type | Purpose |
|------|------|---------|
| `product_search` | Index Search | Semantic search on product catalog |
| `get_user_affinity` | ES\|QL | Query clickstream for user preferences |
| `check_trip_safety` | Workflow | Get weather/road conditions via MCP |
| `get_customer_profile` | Workflow | Get CRM data (loyalty tier, purchase history) |

### Demo Personas

| Persona | ID | Characteristics |
|---------|-----|-----------------|
| Sarah Martinez | `ultralight_backpacker_sarah` | Ultralight enthusiast, experienced backpacker |
| Alex Hiker | `user_member` | Experienced member, expedition gear preferences |
| New Visitor | `user_new` | No history, generic recommendations |

---

## Demo Mode Scenarios

The app includes a built-in Demo Mode with three scenarios:

| Scenario | Query | Best Search Type |
|----------|-------|------------------|
| **Keyword Match** | "ultralight backpacking tent" | Lexical ≈ Hybrid |
| **Conceptual** | "gear to keep my feet dry on slippery mountain trails" | Hybrid Wins |
| **Task-Based** | "I'm planning a 3-day backpacking trip in Yosemite" | Agent Excels |

---

## Kibana URLs

For backend demos, navigate to:

- **Agent Builder**: Kibana → AI Assistants → Agent Builder
- **Agents list**: `/app/agent_builder/agents`
- **Tools list**: `/app/agent_builder/tools`
- **Workflows**: Kibana → Management → Workflows

---

## Recording Tips (YouTube)

- **Resolution**: 1920x1080 minimum
- **Browser**: Use Chrome with a clean profile
- **Font size**: Increase terminal font to 16pt+ for readability
- **Cursor**: Use a cursor highlighter tool
- **Pace**: Pause briefly before and after each click
- **Audio**: Use external mic, not laptop mic
- **Screen recording**: OBS or ScreenFlow recommended

---

## Field Demo Tips

- **Pre-load the page**: Have Trip Planner open before starting
- **Use a known-good query**: Test the demo query before presenting
- **Have Kibana ready**: Keep Agent Builder tab open but minimized
- **Anticipate questions**: Know the architecture diagram from AGENTS.md
- **Handle failures gracefully**: If the agent times out, explain the architecture while waiting
