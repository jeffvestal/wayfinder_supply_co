# YouTube Video: Personalization - Clickstream-Based Boosting

**Target Duration:** 5-7 minutes
**Audience:** Developers on Elastic Community YouTube channel
**Focus:** How user preferences from clickstream data affect search results

---

## Section A: Verbal Script

### Intro (0:00-0:45)

"Same search, different results. That's personalization.

When two users search for 'backpacking gear,' they shouldn't get identical results. An ultralight enthusiast wants lightweight, minimalist equipment. A family camper wants durable, budget-friendly options.

Today I'm going to show you how Wayfinder Supply Co. uses Elasticsearch clickstream data to personalize search results in real-time. No user profiles to configure, no preferences to set - just behavior-driven personalization.

Let's see it in action."

### Key Points (0:45-5:00)

**Point 1: The Problem with Generic Search (0:45-1:30)**

"Traditional search treats every user the same. You search for 'tent' and get the same results whether you're a seasoned mountaineer or a first-time camper.

This is a missed opportunity. If you know what a user has been browsing, clicking, and adding to their cart, you can infer their preferences. An ultralight backpacker who's been viewing lightweight sleeping bags probably wants lightweight tents too.

The challenge is doing this at query time, in real-time, without pre-computing user profiles. That's where ES|QL and Elasticsearch come in."

**Point 2: How Clickstream Personalization Works (1:30-2:30)**

"Here's the architecture:

Every time a user views a product, clicks 'Add to Cart,' or interacts with the site, we log that event to a clickstream index in Elasticsearch. Each event captures the user ID, the action, and importantly - the product's tags: ultralight, budget, expedition, family, etc.

When a search query comes in, the agent calls an ES|QL tool called get_user_affinity. This tool aggregates the user's recent clickstream events and identifies their top preference tags.

Then, during product search, we apply a function_score query that boosts products matching those tags. Ultralight user? Ultralight products rank higher. Budget-conscious user? Budget options surface first.

No machine learning models, no cold-start problem, no batch processing. Just real-time aggregation and query-time boosting."

**Point 3: Live Demo - User Comparison (2:30-4:00)**

"Let me show you this in action. I'll run the same search as two different users.

First, I'm logged in as Sarah Martinez - she's an ultralight backpacker. Her clickstream shows she's been browsing lightweight sleeping bags, minimalist shelters, and carbon fiber trekking poles.

I'll search: 'backpacking gear.'

Look at the results. Ultralight tent at the top. Lightweight sleeping bag. Minimalist cooking kit. These all have the 'ultralight' tag, which matches Sarah's affinity.

Now let me switch users. I'll log in as a new visitor with no history.

Same search: 'backpacking gear.'

Different results. The products are still relevant - they're still backpacking gear - but they're not personalized. No preference boosting, just relevance ranking.

Here's the key insight: both result sets are valid. But Sarah's results are better *for Sarah*. That's personalization."

**Point 4: The ES|QL Query Under the Hood (4:00-5:00)**

"Let me show you what's actually happening. The get_user_affinity tool runs this ES|QL query:

```
FROM user-clickstream
| WHERE user_id == 'sarah_id'
| STATS count = COUNT(*) BY meta_tags
| SORT count DESC
| LIMIT 5
```

This returns the top 5 tags that Sarah has interacted with most. Maybe: ultralight (15 events), expedition (8 events), lightweight (6 events).

These tags are then passed to the product search, which applies boosting:

```json
{
  \"function_score\": {
    \"functions\": [{
      \"filter\": { \"terms\": { \"tags\": [\"ultralight\", \"expedition\"] } },
      \"weight\": 1.5
    }]
  }
}
```

Products with matching tags get a 1.5x relevance boost. Simple, fast, and transparent."

### Wrap-Up (5:00-5:30)

"That's clickstream-based personalization:
- Log user events to Elasticsearch
- Aggregate preferences with ES|QL at query time
- Apply function_score boosting during search

No complex recommendation models, no data pipelines, no cold-start problem. Just Elasticsearch doing what it does best - fast aggregations and flexible queries.

In the next video, I'll show you how to build the workflows that power the agent's external data access.

See you there."

---

## Section C: Full Demo Flow with Timestamps

**0:00-0:15** - Title card
- "Personalization: Real-Time Clickstream Boosting"

**0:15-0:45** - Hook
- "Same search, different results"
- Show two side-by-side result sets (can be edited together in post)

**0:45-1:30** - Explain the problem
- Face cam or diagram
- "Generic search treats everyone the same"
- Show architecture: User → Clickstream → Aggregation → Boosted Search

**1:30-2:00** - Open Wayfinder and show persona selector
- Navigate to the app
- Show the user dropdown in the header
- "I can switch between different user personas"
- Explain Sarah Martinez: "Ultralight backpacker, experienced"
- Explain New Visitor: "No history, clean slate"

**2:00-2:30** - Search as Sarah
- Ensure Sarah Martinez is selected
- Open Search Panel → Hybrid tab
- Type: "backpacking gear"
- Show results
- "Notice the ultralight products ranking high"
- Point out product tags: "See 'ultralight' tag on these products"

**2:30-3:00** - Search as New Visitor
- Switch to New Visitor / Guest
- Same search: "backpacking gear"
- Show different results
- "Same query, different ranking"
- "No personalization - just relevance"

**3:00-3:30** - Side-by-side comparison
- If possible, show both result sets side by side (post-production split screen)
- Point out specific differences
- "Sarah sees the Ultralight Shelter first. Guest sees a different tent."

**3:30-4:00** - Show clickstream in Kibana (optional deep dive)
- Navigate to Kibana → Discover
- Select `user-clickstream` index
- Filter by Sarah's user ID
- Show events: view_item, add_to_cart
- Point at meta_tags field
- "This is the raw data driving personalization"

**4:00-4:30** - Show the ES|QL query
- Can show in Dev Tools or as a code block on screen
- Walk through the aggregation:
  - WHERE filters to user
  - STATS aggregates by tags
  - SORT puts most common first
  - LIMIT returns top preferences

**4:30-5:00** - Show the boosted search query
- Show the function_score structure
- "Products matching user tags get boosted"
- "No machine learning, just Elasticsearch"

**5:00-5:30** - Wrap up
- Recap the three steps
- "Next: Building Workflows"
- End screen

---

## B-Roll / Screenshot Suggestions

1. **Persona selector dropdown** - Show the user switching UI
2. **Sarah's results** - Ultralight products with tags visible
3. **Guest's results** - Generic ranking without personalization
4. **Side-by-side comparison** - Split screen of both result sets
5. **Clickstream in Kibana Discover** - Raw event data with meta_tags
6. **ES|QL query in Dev Tools** - The aggregation query
7. **Architecture diagram** - Clickstream → ES|QL → function_score → Results

---

## Key Data Points to Mention

**Clickstream Index Schema:**
```json
{
  "@timestamp": "date",
  "user_id": "keyword",
  "action": "keyword",  // view_item, add_to_cart, purchase
  "product_id": "keyword",
  "meta_tags": ["keyword"]  // ultralight, budget, expedition
}
```

**User Personas in Demo:**
- `ultralight_backpacker_sarah` - Ultralight & expedition preferences
- `family_camper_mike` - Family & budget preferences
- `user_new` - No history (baseline comparison)
