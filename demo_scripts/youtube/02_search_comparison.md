# YouTube Video: Search Comparison - Why Agentic Matters

**Target Duration:** 5-7 minutes
**Audience:** Developers on Elastic Community YouTube channel
**Focus:** Side-by-side comparison of Lexical vs Hybrid vs Agentic search

---

## Section A: Verbal Script

### Intro (0:00-0:45)

"Not all search is created equal.

You've probably heard terms like 'lexical search,' 'semantic search,' 'hybrid search,' and now 'agentic search.' But what do they actually mean? And more importantly, when should you use each one?

Today I'm going to show you a side-by-side comparison using three different queries. You'll see exactly where each search type excels and where it falls short.

Let's run the experiments."

### Key Points (0:45-5:30)

**Point 1: The Three Search Types (0:45-1:30)**

"First, let me define our contestants:

Lexical search - also called BM25 or keyword search - matches exact terms. It's fast, well-understood, and great when users know exactly what they want.

Hybrid search combines lexical with semantic search using ELSER. It understands meaning, not just keywords. 'Waterproof hiking boots' and 'shoes that keep feet dry on trails' return similar results.

Agentic search uses an AI agent with reasoning capabilities and access to tools. It doesn't just search - it thinks about your intent, fetches external data, and synthesizes a personalized response.

Let's see how they compare."

**Point 2: Experiment 1 - Keyword Match (1:30-2:30)**

"Our first query is: 'ultralight backpacking tent.'

This is a keyword-heavy query - the user knows exactly what they want. Let me run it through all three search modes.

Lexical search: finds tents with 'ultralight' and 'backpacking' in the title or description. Solid results.

Hybrid search: similar results, maybe slightly reranked because it understands the semantic relationship between the terms.

Agentic search: the agent searches, but doesn't add much value here. It's overkill for a simple keyword lookup.

Verdict: For keyword queries, lexical and hybrid are essentially tied. Agentic is unnecessary overhead."

**Point 3: Experiment 2 - Conceptual Query (2:30-3:45)**

"Now let's try: 'gear to keep my feet dry on slippery mountain trails.'

No product is literally named 'feet dry slippery trails.' This requires understanding intent.

Lexical search: struggles. It might match 'dry' or 'trails' but misses the conceptual connection. Returns random camping gear.

Hybrid search: this is where ELSER shines. It understands we want waterproof hiking boots, gaiters, trekking poles with good grip. The semantic understanding bridges the gap between query and product descriptions.

Agentic search: also good results, but again, for a pure search query, hybrid is sufficient.

Verdict: Hybrid wins decisively for conceptual queries. This is why semantic search matters."

**Point 4: Experiment 3 - Task-Based Query (3:45-5:00)**

"Final experiment: 'I'm planning a 3-day backpacking trip to Yosemite in March. What tent should I bring?'

This isn't a search query - it's a task. The user needs reasoning.

Lexical search: returns tents. Any tents. It doesn't know about Yosemite, March weather, or trip duration.

Hybrid search: slightly better - might surface 3-season tents - but still just pattern matching against the product catalog.

Agentic search: now we see the difference. The agent reasons: 'Yosemite in March means cold temperatures and possible snow. I should check weather conditions.' It calls a workflow to get current forecasts. It considers the 3-day duration - lightweight matters. It searches for tents rated for those specific conditions.

The result isn't just a list of tents - it's a recommendation with reasoning: 'Based on March conditions in Yosemite, I recommend this 3-season tent rated to 20°F...'

Verdict: For task-based queries requiring reasoning, agentic search is the only real solution."

**Point 5: Summary (5:00-5:30)**

"So when should you use each type?

Lexical: Known-item search, SKU lookups, exact matches. Fast and simple.

Hybrid: Discovery and exploration. Users browsing, asking conceptual questions. The sweet spot for most e-commerce.

Agentic: Complex tasks requiring reasoning, personalization, or external data. Trip planning, recommendations, anything that needs to 'think.'

The good news? You don't have to choose just one. Elastic supports all three, and you can combine them based on the query type."

### Wrap-Up (5:30-6:00)

"That's the search comparison. Lexical for keywords, hybrid for concepts, agentic for tasks.

In the next video, I'll show you how personalization works - how the same query returns different results for different users based on their browsing history.

See you there."

---

## Section C: Full Demo Flow with Timestamps

**0:00-0:15** - Title card
- "Search Comparison: Lexical vs Hybrid vs Agentic"

**0:15-0:45** - Hook
- Face cam explaining the alphabet soup of search terms
- "Let me show you what each one actually does"

**0:45-1:30** - Open Wayfinder and explain search modes
- Navigate to the app
- Open the Search Panel (slide-out from right)
- Show the three tabs: Chat (Agentic), Hybrid, Lexical
- "Same product catalog, three different search approaches"

**1:30-2:00** - Experiment 1 Setup: Keyword Query
- "First query: a simple keyword search"
- Type: "ultralight backpacking tent"

**2:00-2:30** - Run Experiment 1
- Click Lexical tab, show results
- "Lexical finds tents with these exact keywords"
- Click Hybrid tab, show results
- "Hybrid is similar - semantic doesn't add much for exact keywords"
- Click Chat tab, show brief agent response
- "Agentic works but it's overkill"
- Verdict on screen: "Lexical ≈ Hybrid for keyword queries"

**2:30-3:00** - Experiment 2 Setup: Conceptual Query
- "Now let's try a conceptual query"
- Type: "gear to keep my feet dry on slippery mountain trails"

**3:00-3:45** - Run Experiment 2
- Click Lexical tab
- "Lexical struggles - no exact match for 'feet dry slippery'"
- Point at irrelevant results
- Click Hybrid tab
- "Hybrid understands the intent - waterproof boots, gaiters, trekking poles"
- Highlight relevant products
- Verdict on screen: "Hybrid wins for conceptual queries"

**3:45-4:15** - Experiment 3 Setup: Task Query
- "Final experiment - a task, not a search"
- Type: "I'm planning a 3-day backpacking trip to Yosemite in March. What tent should I bring?"

**4:15-5:00** - Run Experiment 3
- Click Lexical tab: "Just returns tents, no context"
- Click Hybrid tab: "Better, but still just matching"
- Click Chat tab
- "Now watch the agent think"
- Show thought trace expanding
- "It's checking weather conditions for Yosemite in March"
- "It's considering my preferences"
- "It's reasoning about the 3-day trip duration"
- Show recommendation with explanation
- Verdict on screen: "Agent excels for task-based queries"

**5:00-5:30** - Summary slide
- Show table:
  | Query Type | Winner |
  |------------|--------|
  | Keyword | Lexical ≈ Hybrid |
  | Conceptual | Hybrid |
  | Task-Based | Agentic |

**5:30-6:00** - Wrap up
- "Use the right tool for the right job"
- "Next: Personalization deep dive"
- End screen

---

## B-Roll / Screenshot Suggestions

1. **Search panel with three tabs** - Highlight the mode selector
2. **Lexical results for keyword query** - Clean list with exact matches
3. **Hybrid results for conceptual query** - Semantically relevant products
4. **Agent thought trace** - Expanded showing tool calls
5. **Side-by-side comparison** - Split screen showing all three results
6. **Summary table** - Query type vs winner chart

---

## Demo Mode Alternative

The app has a built-in Demo Mode that automates this comparison:

1. Open Search Panel
2. Switch to "Demo" tab
3. Select a scenario (Keyword, Semantic, or Use Case)
4. Click "Run Demo"
5. Watch it automatically run all three search types sequentially

This is an alternative flow if you want a more guided comparison without manually switching tabs.
