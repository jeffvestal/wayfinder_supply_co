# Field Demo: Micro (1 Minute)

**Duration:** 60 seconds
**Audience:** Executives, "wow me"
**Focus:** Trip Planner streaming with visible thought trace - art of the possible

---

## Goals

1. Show that Elastic's AI Agent can understand complex, natural language queries
2. Demonstrate real-time streaming with visible AI reasoning (thought trace)
3. Prove the agent uses real data (weather, preferences, products) - not hallucination
4. Leave them wanting to know more

---

## Pre-Demo Setup

- Have Wayfinder open in browser at Trip Planner page
- Select persona: Sarah Martinez (ultralight backpacker)
- Clear any previous chat history
- Have Kibana open in a separate tab (don't show unless asked)

---

## Demo Script

### Scene 1: The Hook (0:00-0:10)

**Talk Track:**
1. "What if search could understand intent, not just keywords?"
2. "Let me show you."

**Notes/Action:**
1. Have Trip Planner visible, empty chat

**Screenshot:** Trip Planner empty state with chat input

---

### Scene 2: The Query (0:10-0:20)

**Talk Track:**
1. "I'll ask a question that's impossible for traditional search."
2. "This requires knowing weather conditions, my preferences, and what products fit my trip."

**Notes/Action:**
1. Type: "I'm planning a 3-day backpacking trip to Yosemite in March. What gear should I bring?"
2. Click Send

**Screenshot:** Query visible in input, send button highlighted

---

### Scene 3: The Magic (0:20-0:45)

**Talk Track:**
1. "Watch what happens."
2. "The agent is reasoning - you can see it thinking."
3. "It's checking weather for Yosemite..."
4. "Looking up my preferences..."
5. "Searching products with all that context..."

**Notes/Action:**
1. Point at thought trace as it streams
2. Show check_trip_safety tool call
3. Show get_user_affinity tool call
4. Show product_search tool call

**Screenshot:** Thought trace panel showing tool calls in progress

---

### Scene 4: The Result (0:45-0:55)

**Talk Track:**
1. "Personalized recommendations based on real data - not hallucination."
2. "March in Yosemite means cold temps - notice the cold-weather rated tent."
3. "It knew I prefer ultralight gear from my browsing history."

**Notes/Action:**
1. Point at product cards
2. Highlight tent product
3. Point at ultralight tags

**Screenshot:** Product recommendations with tags visible

---

### Scene 5: The Close (0:55-1:00)

**Talk Track:**
1. "This is Elastic's Agentic Search."
2. "Want to see how it's built?"

**Notes/Action:**
1. Pause for reaction

**Screenshot:** Full results view

---

## Recap

This demo proves three things in 60 seconds:

1. **Natural Language Understanding**: The agent understood a complex, multi-part question
2. **Real-Time Reasoning**: Visible thought trace shows the AI working, not just responding
3. **Data Federation**: Weather, preferences, and products combined for personalized results

The value: Search that thinks, not just matches.

---

## If They Ask Follow-Up Questions

**"How does it know the weather?"**
> "It calls an external weather service through an Elastic Workflow. The agent decides it needs that data, makes the call, and incorporates the results. Happy to show you how that's built."

**"Is this just ChatGPT?"**
> "No - this is Elastic's Agent Builder with native Elasticsearch integration. The data stays in your Elasticsearch cluster, the reasoning happens in Kibana, and it's fully observable."

**"Can this work with our data?"**
> "Absolutely. This demo uses product data in Elasticsearch. You can connect your catalog, your customer data, any external APIs through Workflows."

**"How hard is it to build?"**
> "Let me show you the 5-minute version where I walk through the backend..."
