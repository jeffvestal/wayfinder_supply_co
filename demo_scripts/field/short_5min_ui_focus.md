# Field Demo: Short - UI Focus (5 Minutes)

**Duration:** 5 minutes
**Time Split:** 4 min UI / 1 min backend tease
**Audience:** Business stakeholders, "what can this do?"
**Focus:** Art of the possible - full Trip Planner experience with backend peek

---

## Goals

1. Show the complete customer journey: browse → plan → recommend
2. Demonstrate personalization in action (same query, different users = different results)
3. Prove the AI uses real external data (weather, CRM) - not hallucination
4. Tease the backend architecture to generate interest in deeper dive

---

## Pre-Demo Setup

- Wayfinder open at homepage
- Two browser tabs/windows ready: one for Sarah, one for Guest
- Kibana open in a minimized tab (for the tease)
- Clear chat history in both windows

---

## Demo Script

### Scene 1: The Problem (0:00-0:30)

**Talk Track:**
1. "Traditional search can't answer complex questions."
2. "If I search 'I'm planning a trip to Yosemite in March' - I get random camping gear."
3. "The search doesn't know about weather, my preferences, or what I already own."
4. "Let me show you what's possible with Elastic's Agentic Search."

**Notes/Action:**
1. Show any generic search briefly
2. Navigate to Wayfinder homepage

**Screenshot:** Wayfinder homepage with product grid

---

### Scene 2: The Store Experience (0:30-1:30)

**Talk Track:**
1. "This is Wayfinder Supply Co. - an outdoor gear retailer."
2. "Let me browse a few products as Sarah, an ultralight backpacker."
3. "Every click is captured - the system learns her preferences."
4. "Now let's plan a trip."

**Notes/Action:**
1. Select Sarah Martinez persona
2. Click on ultralight tent
3. Click on lightweight sleeping bag
4. Click on trekking poles
5. Click Trip Planner

**Screenshot:** Product detail pages showing clicks, then Trip Planner

---

### Scene 3: The Trip Planner (1:30-3:00)

**Talk Track:**
1. "I'll ask the same complex question that traditional search can't handle."
2. "Watch the agent think."
3. "It's checking weather conditions for Yosemite in March..."
4. "Looking up Sarah's preferences from her browsing..."
5. "Querying her purchase history - she already owns trekking poles..."
6. "Here are the recommendations."
7. "Cold-weather tent - because March in Yosemite is cold."
8. "Ultralight - because that's Sarah's preference."
9. "No trekking poles - because she already owns them."

**Notes/Action:**
1. Type: "I'm planning a 3-day backpacking trip to Yosemite in March. What gear should I bring?"
2. Click Send
3. Expand thought trace
4. Narrate each tool call as it appears
5. Point at results when complete

**Screenshot:** Thought trace showing tools, then product cards with explanations

---

### Scene 4: Personalization Proof (3:00-4:00)

**Talk Track:**
1. "Here's the real magic: personalization."
2. "Same question, different user - a guest with no history."
3. "Watch the recommendations."
4. "Different products. No personalization boost."
5. "Same AI, same catalog - but Sarah got recommendations tailored to her."

**Notes/Action:**
1. Switch to Guest window
2. Type same query
3. Click Send
4. Compare results side-by-side if possible

**Screenshot:** Guest results vs Sarah results comparison

---

### Scene 5: The Backend Tease (4:00-4:45)

**Talk Track:**
1. "Want to see how this is built?"
2. "This is Elastic's Agent Builder."
3. "The agent has tools:"
   - "Product search against Elasticsearch"
   - "Clickstream query for preferences"
   - "Workflows that call external APIs - weather, CRM"
4. "The agent decides which tools to use based on the question."
5. "That's agentic search: AI reasoning + Elasticsearch data + external integration."

**Notes/Action:**
1. Switch to Kibana
2. Show Agent Builder
3. Show agent list
4. Show tools panel briefly

**Screenshot:** Kibana Agent Builder with tools list

---

### Scene 6: Close (4:45-5:00)

**Talk Track:**
1. "Questions?"
2. "I'm happy to dive deeper into the architecture or show you how to build this."

**Notes/Action:**
1. Return to Trip Planner results

**Screenshot:** Full results view

---

## Recap

This demo shows the art of the possible:

1. **Customer Journey**: Browse → preferences captured → personalized recommendations
2. **AI Reasoning**: Visible thought process, not a black box
3. **Real Data**: Weather API, CRM integration, product catalog - all federated
4. **Personalization**: Same query yields different results for different users

The value proposition: **Search that understands context and personalizes results in real-time.**

---

## Common Questions

**"How accurate is it?"**
> "The recommendations come from your real product data in Elasticsearch. The AI decides what to search for and how to rank results, but the products are real. You control the data."

**"Does this require ML expertise?"**
> "No. Agent Builder is configuration, not code. You write system prompts in plain English, define tools, and connect workflows. No model training required."

**"How does it compare to ChatGPT + plugins?"**
> "Key differences: your data stays in Elasticsearch, the AI reasoning happens in your Kibana instance, you get full observability, and it's integrated with Elastic's search capabilities including ELSER semantic search."
