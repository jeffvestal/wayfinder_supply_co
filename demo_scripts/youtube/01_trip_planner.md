# YouTube Video: Trip Planner - The AI Chat Experience

**Target Duration:** 5-7 minutes
**Audience:** Developers on Elastic Community YouTube channel
**Focus:** Demonstrate the Trip Planner's streaming AI chat with visible thought trace

---

## Section A: Verbal Script

### Intro (0:00-0:45)

"What if search could understand intent, not just keywords?

Traditional search engines are great at finding exact matches. Type 'tent' and you get tents. But what happens when you ask: 'I'm planning a 3-day backpacking trip to Yosemite in March - what gear should I bring?'

Standard search fails because the answer depends on weather conditions, your past purchases, your preferences, and which products actually fit your specific trip.

Today I'm going to show you Wayfinder Supply Co. - a demo application that showcases Elastic's Agentic Search capabilities. You'll see an AI agent that reasons about your intent, fetches data from multiple sources, and recommends exactly what you need.

Let's dive in."

### Key Points (0:45-5:00)

**Point 1: The Trip Planner Interface (0:45-1:30)**

"Here's our Trip Planner. It looks like a standard chat interface, but what's happening behind the scenes is anything but standard.

When I send a message, it goes to an AI agent built with Elastic's Agent Builder. This agent has access to tools - it can search products, check weather conditions, look up my purchase history, and understand my preferences from clickstream data.

Let me show you what that looks like in practice."

**Point 2: Sending a Query and Watching the Stream (1:30-3:00)**

"I'll ask: 'I'm planning a 3-day backpacking trip to Yosemite in March. What gear should I bring?'

Watch what happens. The response streams in real-time - you can see the agent is thinking. But here's the really interesting part: see this 'thinking' indicator? I can expand it to see exactly what the agent is doing.

It's reasoning: 'The user wants to go to Yosemite in March - I should check weather conditions.' Then it calls the check_trip_safety tool - that's a workflow that hits an external weather API.

Now it's calling get_user_affinity - that's an ES|QL query against our clickstream data to understand what kind of gear this user prefers.

And finally, it searches our product catalog with all that context. It's not just searching for 'tent' - it's searching for a tent that fits March conditions in Yosemite, matches my preferences, and complements gear I already own.

This is the power of agentic search: reasoning plus tools plus real data."

**Point 3: The Thought Trace (3:00-4:00)**

"Let me expand this thought trace panel. This is transparency you don't get with traditional AI chat.

Every step is logged: the reasoning, the tool calls, the parameters passed, and the results returned. You can see exactly why the agent recommended this tent over another one.

For developers, this is gold. When something doesn't work as expected, you can debug it. When it works perfectly, you can understand why and replicate it.

This isn't a black box - it's observable AI."

**Point 4: Product Recommendations (4:00-5:00)**

"Look at the recommendations. The agent didn't just search for 'tent' - it found a 3-season tent rated for the temperatures we'll encounter in Yosemite in March.

It knew from my clickstream that I prefer ultralight gear, so it boosted lightweight options. It checked my CRM profile and saw I already own trekking poles, so it didn't recommend those.

This is personalized, context-aware product discovery. Standard search can't do this."

### Wrap-Up (5:00-5:30)

"That's Elastic's Agentic Search in action. An AI agent with access to:
- Agent Builder for orchestration
- Workflows for external data federation
- Elasticsearch for product search and clickstream analysis

In the next videos, I'll show you how this compares to traditional search modes, how personalization works under the hood, and how to build these agents yourself.

Subscribe so you don't miss it. See you in the next one."

---

## Section C: Full Demo Flow with Timestamps

**0:00-0:15** - Title card / intro animation
- "Elastic Agentic Search: Trip Planner Demo"

**0:15-0:45** - Hook and problem statement
- Face cam or slide explaining the search limitation
- Example: "Plan my camping trip" is impossible for standard search

**0:45-1:00** - Open Wayfinder Supply Co.
- Navigate to `http://localhost:8000` (or demo URL)
- Show the homepage briefly - "This is our outdoor gear store"
- Click "Trip Planner" in the navigation

**1:00-1:30** - Tour the Trip Planner interface
- Point out the chat input
- Show the persona selector: "I'm logged in as Sarah Martinez, an ultralight backpacker"
- Note: "The agent will use my profile and preferences"

**1:30-2:00** - Type the demo query
- Type slowly: "I'm planning a 3-day backpacking trip to Yosemite in March. What gear should I bring?"
- "Watch what happens when I hit send"
- Click send

**2:00-3:00** - Watch streaming response
- Point at the "Thinking..." indicator
- "The agent is reasoning about my question"
- Click to expand the thought trace panel
- "Here we can see exactly what it's doing"
- Narrate each step as it appears:
  - "It's calling check_trip_safety - checking weather conditions"
  - "Now get_user_affinity - querying my clickstream preferences"
  - "And product_search - finding relevant gear"

**3:00-3:30** - Explore thought trace details
- Click on a tool call to expand it
- Show the parameters: location, dates
- Show the results: weather conditions returned
- "Full observability into the AI's decision making"

**3:30-4:30** - Review recommendations
- Scroll through the product cards
- "Notice it recommended a 3-season tent - perfect for March"
- "Lightweight options because it knows I prefer ultralight gear"
- Point out the "Add to Cart" buttons
- "These are real products from our Elasticsearch catalog"

**4:30-5:00** - Show another query (optional)
- "Let me ask a follow-up"
- Type: "What about a sleeping bag?"
- "It remembers the context - it'll recommend a bag for Yosemite in March"
- Show brief response

**5:00-5:30** - Wrap up
- Return to face cam or summary slide
- Call to action: "Next video: Search Comparison Demo"
- End screen with subscribe prompt

---

## B-Roll / Screenshot Suggestions

1. **Trip Planner full interface** - Clean shot showing chat input and empty state
2. **Streaming response** - Capture the "Thinking..." animation
3. **Expanded thought trace** - Show reasoning and tool calls
4. **Tool call detail** - Close-up of a check_trip_safety call with results
5. **Product recommendations** - Grid of recommended products with prices
6. **Architecture diagram** - User → Agent → Tools → Data Sources (from AGENTS.md)

---

## Common Questions to Address

**Q: Is this just ChatGPT with a search plugin?**
A: No - this uses Elastic's Agent Builder, which provides: (1) native Elasticsearch integration, (2) ES|QL tools for complex queries, (3) Workflows for external API orchestration, (4) full observability and logging.

**Q: How is this different from RAG?**
A: RAG retrieves documents and stuffs them into context. Agentic search reasons about what data it needs, uses multiple tools to fetch it, and synthesizes a response. The agent decides the retrieval strategy, not a static pipeline.

**Q: Can the agent make mistakes?**
A: Yes - that's why the thought trace exists. You can see exactly what it did and debug issues. This is observable AI, not a black box.
