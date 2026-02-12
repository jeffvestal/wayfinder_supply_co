# YouTube Video: Full Walkthrough - End-to-End Journey

**Target Duration:** 10 minutes
**Audience:** Developers on Elastic Community YouTube channel
**Focus:** Complete demo from store browse to trip planning to architecture overview

---

## Section A: Verbal Script

### Intro (0:00-0:45)

"You've seen the individual pieces: the Trip Planner, search comparison, personalization, and workflows. Now let's put it all together.

In this video, I'll walk you through the complete Wayfinder Supply Co. experience - from a customer's perspective and from an architect's perspective. You'll see how browsing the store feeds personalization, how the Trip Planner orchestrates multiple tools, and how Agent Builder and Workflows work together behind the scenes.

Let's start the journey."

### Key Points (0:45-9:00)

**Point 1: The Customer Journey - Browsing (0:45-2:00)**

"Meet Sarah Martinez. She's planning a backpacking trip and came to Wayfinder Supply Co. looking for gear.

She starts by browsing. Here's the homepage - a curated collection of outdoor products. Sarah clicks on a few items: an ultralight sleeping bag, a carbon fiber trekking pole, a minimalist first aid kit.

Every click is tracked. In the background, we're logging events to our clickstream index: user ID, action type, product ID, and importantly - the product's tags. Sarah just clicked on three 'ultralight' tagged products.

This isn't surveillance - it's the foundation of personalization. The more we understand Sarah's preferences, the better recommendations we can make."

**Point 2: The Customer Journey - Trip Planner (2:00-4:00)**

"Now Sarah opens the Trip Planner. She types: 'I'm planning a 3-day backpacking trip to Yosemite in March. What gear should I bring?'

Watch the agent work. It's not just searching - it's reasoning.

First, it calls check_trip_safety - a workflow that hits our weather service. March in Yosemite means cold temperatures, possibly snow. The agent now knows to recommend cold-weather gear.

Second, it calls get_user_affinity - an ES|QL query against the clickstream we just populated. It finds that Sarah prefers ultralight gear based on her browsing. The agent will boost lightweight options.

Third, it calls get_customer_profile - another workflow to our CRM. Sarah is a Gold member with 2 years of purchase history. She already owns trekking poles. The agent won't recommend those again.

Finally, it searches the product catalog with all this context: cold-weather rated, ultralight tagged, not including gear she already owns.

The result: personalized, context-aware recommendations with clear reasoning. Not 'here are some tents' but 'Based on March conditions in Yosemite, your ultralight preference, and gear you already own, I recommend...'"

**Point 3: Behind the Scenes - Agent Builder (4:00-6:00)**

"Let me show you what powers this. Switch to Kibana.

Here's the Agent Builder. The trip-planner-agent has:
- A system prompt defining its persona and behavior
- A list of tools it can use

The tools:
- product_search: semantic search on our Elasticsearch product catalog
- get_user_affinity: ES|QL query against clickstream
- check_trip_safety: workflow tool calling weather MCP
- get_customer_profile: workflow tool calling CRM MCP

The agent decides which tools to call based on the user's question. It's not a fixed pipeline - it's dynamic reasoning.

If someone asks 'Do you have rain jackets?' - it just searches. No need for weather data.

If someone asks 'What should I bring to Yosemite in March?' - it calls weather, clickstream, CRM, and search. Full context.

This is the power of agentic search: the AI decides the retrieval strategy, not a hardcoded pipeline."

**Point 4: Behind the Scenes - Workflows (6:00-7:30)**

"Now let's look at the workflows. Navigate to Management → Workflows.

Here's check_trip_safety. It's YAML that:
1. Takes inputs: location and dates
2. Makes an HTTP call to our MCP server
3. Returns weather conditions

The MCP server is a separate service - could be running anywhere. It exposes tools via the Model Context Protocol standard. Our workflow calls it, gets structured data back, and returns that to the agent.

Here's get_customer_profile. Same pattern: takes user_id, calls CRM MCP, returns profile data.

The beauty of this architecture: the agent doesn't know or care that these are HTTP calls. It just calls a tool. The workflow handles the integration complexity."

**Point 5: The Architecture (7:30-8:30)**

"Let me show you the full architecture:

```
User → React Frontend → FastAPI Backend → Agent Builder
                                               ↓
                                         Agent Reasoning
                                               ↓
                              ┌────────────────┼────────────────┐
                              ↓                ↓                ↓
                        ES Search        ES|QL Query      Workflows
                              ↓                ↓                ↓
                        Products         Clickstream      MCP Server
                                                               ↓
                                                    Weather API / CRM API
```

The frontend streams responses via Server-Sent Events - you see the agent thinking in real-time.

The backend proxies requests to Kibana's Agent Builder API.

Agent Builder orchestrates everything: reasoning, tool calls, response generation.

Tools connect to Elasticsearch (search and ES|QL) or Workflows (external APIs).

This is enterprise-ready architecture. Elasticsearch for data, Agent Builder for AI, Workflows for integration."

**Point 6: What You Can Build (8:30-9:00)**

"This pattern applies to any domain:
- E-commerce: personalized product recommendations
- Support: agent that checks ticket history and knowledge base
- Observability: agent that queries metrics and triggers runbooks
- Enterprise search: agent that federates across multiple data sources

The building blocks are the same:
1. Your data in Elasticsearch
2. Agent Builder for AI orchestration
3. Workflows for external system integration

You've seen how it works. Now go build your own."

### Wrap-Up (9:00-9:30)

"That's the complete Wayfinder Supply Co. experience:
- Clickstream capture for personalization
- AI agent with multi-tool reasoning
- Workflows for external data federation
- Elasticsearch as the foundation

Thanks for watching this series. If you want to try it yourself, check the links in the description for the workshop and GitHub repo.

Subscribe for more Elastic content. See you in the next one."

---

## Section C: Full Demo Flow with Timestamps

**0:00-0:15** - Title card
- "Wayfinder Supply Co: End-to-End Walkthrough"

**0:15-0:45** - Hook
- "Let's put it all together"
- Quick montage of clips from previous videos

**0:45-1:15** - Open Wayfinder as Sarah
- Navigate to http://localhost:8000
- Select Sarah Martinez persona
- "We're Sarah, an ultralight backpacker"

**1:15-2:00** - Browse products
- Click on homepage products
- View an ultralight sleeping bag - "This generates a clickstream event"
- View trekking poles - "Another event"
- View a lightweight tent - "Building her preference profile"
- "Every click = data point"

**2:00-2:30** - Open Trip Planner
- Click Trip Planner in nav
- "Now let's plan a trip"
- Type the demo query: "I'm planning a 3-day backpacking trip to Yosemite in March. What gear should I bring?"

**2:30-4:00** - Watch agent response
- Click send
- Narrate thought trace as it streams:
  - "Checking weather for Yosemite..."
  - "Querying Sarah's preferences from clickstream..."
  - "Looking up her customer profile..."
  - "Searching products with all that context..."
- Show final recommendations
- "Personalized, context-aware, reasoned recommendations"

**4:00-4:30** - Transition to Kibana
- "Let's see what's behind this"
- Open new tab, navigate to Kibana

**4:30-5:30** - Show Agent Builder
- Navigate to AI Assistants → Agent Builder
- Click on trip-planner-agent
- Show system prompt (scroll through)
- Show tools list
- "Four tools: search, ES|QL, two workflows"

**5:30-6:00** - Show tools detail
- Click on each tool briefly
- "product_search: semantic search"
- "get_user_affinity: ES|QL aggregation"
- "check_trip_safety: workflow to weather API"
- "get_customer_profile: workflow to CRM API"

**6:00-7:00** - Show Workflows
- Navigate to Management → Workflows
- Click check_trip_safety
- Show YAML
- "YAML definition, HTTP call to MCP, returns weather data"
- Click get_customer_profile
- "Same pattern for CRM data"

**7:00-7:30** - Show MCP server (brief)
- If time, switch to terminal or code
- Show mcp_server/main.py briefly
- "FastMCP server exposing weather and CRM tools"
- "Could be replaced with real APIs"

**7:30-8:30** - Architecture diagram
- Switch to slide/whiteboard showing full architecture
- Walk through each component
- "Frontend → Backend → Agent Builder → Tools → Data Sources"
- "Enterprise-ready architecture"

**8:30-9:00** - What you can build
- Show slide with other use cases
- "E-commerce, support, observability, enterprise search"
- "Same building blocks"

**9:00-9:30** - Wrap up
- Back to face cam
- "Links in description: workshop, GitHub, docs"
- "Subscribe for more"
- End screen with cards for other videos

---

## B-Roll / Screenshot Suggestions

1. **Homepage with product grid** - Clean shot of the store
2. **Product detail page** - Showing a click event context
3. **Trip Planner streaming** - Full response with thought trace
4. **Agent Builder interface** - Agent configuration page
5. **Tools list** - Four tools attached to agent
6. **Workflows list** - Both workflows in Kibana
7. **Workflow YAML** - Full check_trip_safety code
8. **Architecture diagram** - Full system overview
9. **Series thumbnails** - End card showing all 5 videos

---

## Links for Description

```
Wayfinder Supply Co. GitHub: https://github.com/elastic/wayfinder-supply-co
Instruqt Workshop: [workshop URL]
Elastic Agent Builder Docs: https://www.elastic.co/docs/current/agent-builder
Elastic Workflows Docs: https://www.elastic.co/docs/current/workflows
ELSER Documentation: https://www.elastic.co/guide/en/machine-learning/current/ml-nlp-elser.html
```

---

## Series Recap

This video concludes the 5-part series:

1. **Trip Planner** - The AI chat experience
2. **Search Comparison** - Lexical vs Hybrid vs Agentic
3. **Personalization** - Clickstream-based boosting
4. **Workflows** - Building the agent's hands
5. **Full Walkthrough** - End-to-end journey (this video)

Consider creating a playlist and linking all videos in end cards.
