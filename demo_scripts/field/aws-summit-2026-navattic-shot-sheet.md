---
type: final
title: "AWS Summit NYC 2026 — Navattic Shot Sheet"
status: pre-recording
category: content
priority: high
created: 2026-06-02
updated: 2026-06-02
tags: [aws-summit-2026, navattic, demo, elastic-bedrock-memory, shot-sheet]
---

# AWS Summit NYC 2026 — Navattic Shot Sheet

**Recording target:** Click-through demo for "From Stateless to Stateful" session
**Source script:** `demo_scripts/field/aws-summit-2026-practice-guide.md`
**Repo:** `github.com/jeffvestal/elastic-bedrock-memory`
**Total shots:** ~25 steps across 6 scenes
**Demo runtime:** ~10 minutes in Navattic

### Kibana (Agent Builder):
https://bedrock-memory-demo-e86908.kb.us-east-1.aws.elastic.cloud

### Kiro:
Kiro CLI open with checkout-service project, `~/.kiro/settings/mcp.json` wired to Agent Builder

---

## Pre-Recording Setup

- [ ] Kiro CLI running — checkout-service project open in sidebar
- [ ] `~/.kiro/settings/mcp.json` contains the elastic-memory server config (already done)
- [ ] Kiro chat panel open and cleared
- [ ] Browser open to Kibana Agent Builder — `checkout-service-memory` agent visible
- [ ] Font size bumped for recording — 16px minimum in both Kiro and Kibana
- [ ] Window: 1920×1080 or 16:9 equivalent — no menubar/dock visible in crop
- [ ] Test one tool call before recording to confirm MCP is live

---

## Navattic Notes

- Each shot below = one Navattic step.
- **Highlight / Hotspot** column = copy-paste tooltip text.
- Auto-advance steps = streaming/loading states — wire as sequential static frames.
- For tool call steps: capture two screenshots (tool call firing + response complete). Wire sequentially.

---

## Scene 1 — Architecture (static slide)

**App:** Slide deck | **Captures:** 1

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | Architecture diagram — Kiro → MCP → Agent Builder → Elasticsearch | ✅ Cap 1a | Annotate full chain: "Kiro (Bedrock) calls the Elastic Agent Builder MCP endpoint directly. No custom server. Agent Builder handles tool execution against Elasticsearch. This is the entire integration." |

---

## Scene 2 — Stateless failure (Kiro, no MCP)

**Purpose:** Show what happens without memory. Short. Make the amnesia real.

**Before recording:** Temporarily remove elastic-memory from mcp.json so Kiro has no memory tools, OR just narrate this as slide content — Navattic step is a static screenshot of the empty/wrong Kiro response.

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | Kiro chat panel — question typed (not sent): `What database did we choose for the cart service, and why?` | ✅ Cap 2a | Hotspot on typed question: "A developer, back after a week off, asking about a decision made in a previous session. Reasonable question." |
| --- | --- | --- | --- |
| 2 | Kiro response — generic/incorrect: no memory, says it doesn't have access to previous conversations | ✅ Cap 2b | Hotspot on response: "Stateless by default. Every session starts at zero. The decision was made — it's just not here." |

---

## Scene 3 — Wire the memory (mcp.json)

**App:** Text editor or Kiro settings | **Purpose:** Show config is 3 lines

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | `~/.kiro/settings/mcp.json` open — elastic-memory server config visible with url, Authorization, kbn-xsrf, Accept headers | ✅ Cap 3a | Hotspot on `"url"` line: "This is the Elastic Agent Builder MCP endpoint. Already built into the platform — no custom server to write or deploy." Hotspot on headers block: "API key auth. Three headers. That's the entire integration." |
| --- | --- | --- | --- |
| 2 | Kiro → restart / reload (or show the 4 tools appearing in Kiro's tool list) | ✅ Cap 3b | Hotspot on tool list: "4 tools visible: search-conversation-history, search-knowledge-facts, get-recent-conversations, list-sessions. All backed by Elasticsearch. All wired automatically from the config." |

---

## Scene 4 — Kiro with memory (THE BIG SCENE, ~6 min)

**App:** Kiro with elastic-memory MCP active | **Captures:** 10 | **Three questions**

### Question 1 — "Which database?" (~2 min)

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | Kiro chat — question typed: `What database did we choose for the cart service, and why?` | ✅ Cap 4a | Hotspot on question: "Same question as Scene 2. One config change between then and now." |
| --- | --- | --- | --- |
| 2 | Kiro — tool call firing: `search-knowledge-facts` with nlQuery visible | ✅ Cap 4b — auto-advance 2s | Hotspot on tool call: "Agent calling search-knowledge-facts. Jina encodes the question. Elasticsearch returns the semantically closest facts." |
| --- | --- | --- | --- |
| 3 | Full response — answer: Aurora PostgreSQL, reason: DynamoDB's eventual consistency failed cart total accuracy, session date cited | ✅ Cap 4c | Hotspot on database name: "Not hallucinated. Recalled from knowledge-facts index — the actual decision from session 3." Hotspot on reason: "It knows why. The rationale was stored alongside the decision when it was made." Hotspot on session reference: "Cross-session memory. This decision was made in a previous conversation, on a previous day." |

### Question 2 — "Auth approach?" (~2 min)

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 4 | Kiro chat — new question: `What auth approach did we decide on? Did we consider OAuth or JWT?` | ✅ Cap 4d | Hotspot on question: "Another architectural decision. A new team member joining the project might ask exactly this." |
| --- | --- | --- | --- |
| 5 | Tool call: `search-knowledge-facts` again — different nlQuery | ✅ Cap 4e — auto-advance 2s | (none — let the retrieval speak) |
| --- | --- | --- | --- |
| 6 | Full response — JWT with refresh tokens, OAuth considered but eliminated (complexity), session source cited | ✅ Cap 4f | Hotspot on JWT answer: "Right answer — from session data, not training data." Hotspot on OAuth elimination: "It knows what was considered and rejected, not just what was chosen." |

### Question 3 — "What did we last work on?" (~2 min)

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 7 | Kiro chat — new question: `Catch me up — what were we working on in the last session?` | ✅ Cap 4g | Hotspot on question: "End-of-day handoff question. Or Monday morning." |
| --- | --- | --- | --- |
| 8 | Tool call: `get-recent-conversations` — ES|QL query visible | ✅ Cap 4h — auto-advance 2s | Hotspot on ES|QL: "Structured query, not semantic search. ES|QL returns the most recent turns ordered by timestamp." |
| --- | --- | --- | --- |
| 9 | Full response — last session summary: Stripe integration for payment processing, webhook handler, idempotency key discussion | ✅ Cap 4i | Hotspot on session content: "Accurate recap of session 10 — the most recent seeded session. It knows what was worked on, not just what was decided." |
| --- | --- | --- | --- |
| 10 | Brief scroll to show session history (optional) — `list-sessions` tool result with all 10 sessions, dates, topics | ✅ Cap 4j | Hotspot on session list: "10 sessions. 2+ weeks of development history. Searchable, recallable, semantically queryable — all from this one chat panel." |

---

## Scene 5 — Kibana: under the hood (~2 min)

**App:** Browser → Kibana Agent Builder | **Purpose:** Show it's not magic — it's just an agent with tools**

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | Agent Builder home — `checkout-service-memory` agent in list | ✅ Cap 5a | Hotspot on agent row: "One agent. Lives in Kibana. No separate deployment. Team can see it, edit it, audit it." |
| --- | --- | --- | --- |
| 2 | Click into agent — system instructions visible, 4 tools listed below | ✅ Cap 5b | Hotspot on instructions: "System prompt: always use memory tools before answering. Never say 'I don't have access to previous conversations.'" Hotspot on tool list: "Tools = Elasticsearch. The agent can only return what the data says." |
| --- | --- | --- | --- |
| 3 | Click into `search-knowledge-facts` tool — type: index_search, pattern: knowledge-facts, description visible | ✅ Cap 5c | Hotspot on type: "index_search — Agent Builder handles the Jina semantic search automatically. Send a natural language query, get semantically matched documents." |
| --- | --- | --- | --- |
| 4 | Navigate to **Conversations** — the three questions from Scene 4 visible, tool calls expanded | ✅ Cap 5d | Hotspot on conversation list: "Every interaction logged. Every tool call shows what was queried and what was returned. Full audit trail." |

---

## Scene 6 — Close / CTA (static slide)

**Captures:** 1

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | Closing slide with repo URL + blog URL | ✅ Cap 6a | Hotspot on repo URL: "Clone it. 5-minute setup. Your agents have persistent memory." Hotspot on Elastic logo: "Bedrock handles the inference. Elastic handles the memory. Better together." |

---

## Re-take Cheat Sheet

| Scene | Reset | Note |
|-------|-------|------|
| 2 — Stateless | Clear Kiro chat | May need to temporarily remove mcp.json entry |
| 3 — Config | Re-open mcp.json | No reset needed — config is static |
| 4 — Memory questions | Clear Kiro chat | Re-run all three questions in order |
| 5 — Kibana | None | Re-navigate from Agent Builder home — read-only |
| Full retake | Clear Kiro chat + re-navigate Kibana | Seed data is persistent — no re-seeding needed |

---

## Narration Notes (for Navattic hotspot voice-over)

Keep hotspot narration **punchy and short** — one observation per hotspot, max 2 sentences. The demo is doing the showing; the hotspot is the "so what."

**Don't say:** "As you can see, the agent is now calling the search-knowledge-facts tool which is performing a semantic search using Jina embeddings against the knowledge-facts index..."

**Do say:** "Tool call. Jina encodes the question. Elasticsearch finds the closest facts."

Cadence: **show** → **name what's happening** → **say why it matters**.
