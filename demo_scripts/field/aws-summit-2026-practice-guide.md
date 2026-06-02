---
type: final
title: "AWS Summit NYC 2026 — Practice Guide"
status: active
category: content
priority: high
created: 2026-06-02
updated: 2026-06-02
tags: [aws-summit-2026, practice, talk, elastic-bedrock-memory]
---

# AWS Summit NYC 2026 — Practice Guide

**Talk:** From Stateless to Stateful: Architecting Agent Memory with Elastic and Bedrock
**Duration:** 60 minutes, solo
**Audience:** AWS Summit builders — developers and architects
**Format:** Talk + Navattic demo recording

---

## The Talk in One Paragraph

AI agents have amnesia. Every session starts at zero — no memory of what decisions were made, what failed, what the team already figured out. Stuffing everything into the context window is the brute-force workaround. It's expensive, slow, and still has a ceiling. The right fix is persistent, semantic, external memory — and Elasticsearch is already the right store for it. In this session you'll see how to wire Amazon Bedrock (via Kiro) to Elastic Agent Builder's native MCP endpoint, giving your agents cross-session recall of architectural decisions, past bugs, and institutional knowledge — at any scale, with no custom middleware.

---

## What's Unique / Why This Is Different

**Not a chatbot on docs.** The agent recalls actual decisions your team made — stored in Elasticsearch, retrieved with Jina semantic search. It returns the right answer even when the exact words don't match.

**No custom MCP server to build or operate.** Elastic Agent Builder exposes a native MCP endpoint. Point your IDE at it. Done.

**Jina semantic embeddings, zero pipeline.** One field type — `semantic_text` — auto-vectorizes at ingest. No embedding pipeline to build, maintain, or monitor.

**Cross-session, cross-machine, cross-team.** The memory store is Elasticsearch. Any agent, any machine, any team member — same memory.

**Observable and auditable.** Every agent call is logged in Kibana Conversations. Every tool call shows what was queried and what was returned. Not a black box.

---

## Why the Audience Should Care

They're developers at AWS Summit. They're building with Bedrock, Kiro, or both. They've seen demos where AI summarizes docs or generates boilerplate. This shows something different: an agent that *remembers what your team decided* and *explains the rationale* — not from training data, from your data.

The practical unlocks:
- **Onboarding:** a new team member can ask the agent "what auth approach did we decide on?" and get the right answer with the reason.
- **Context recovery:** returning from a week off, ask "what did we work on last session?" and pick up exactly where you left off.
- **Institutional memory:** senior engineer leaves. The decisions stay.

**The line to land:** *"Your agents remember what you tell them. They don't remember what you decided last week. This is how you fix that."*

---

## Talk Structure and Timing

| Section | Slides | Time | Notes |
|---------|--------|------|-------|
| Intro + agenda | 1–3 | 3 min | Light — don't linger |
| The Amnesia Problem | 4–7 | 8 min | This is where you hook them |
| Memory-as-a-Service | 8–12 | 10 min | Architecture + Jina |
| How It's Built | 13–18 | 10 min | Indices, tools, MCP config |
| Demo | 19 | 1 min | Intro + Navattic plays (~10 min) |
| Demo recap | 20–22 | 5 min | What happened + design decisions |
| Build It Yourself | 23–25 | 5 min | Repo + quickstart |
| Close + Q&A | 26 | 8 min | CTA + questions |
| **Total** | | **~60 min** | |

---

## Section-by-Section Practice Script

### Slides 1–3: Intro (3 min)

**Saying:**
> "Sixty minutes from now, you're going to have the full architecture — the code, the pattern, the repo — to give your AI agents persistent memory. Not longer context windows. Actual memory. Let's get into it."

> *(agenda slide)*
> "Five sections. We'll spend most of our time on the architecture and the demo. Questions at the end — but if something's unclear, flag me in the aisle."

**They should think:** *This is going somewhere concrete.*

---

### Slides 4–7: The Amnesia Problem (8 min)

**Slide 5 — "Every AI agent starts with amnesia"**

**Saying:**
> "By default, every AI agent you build is stateless. The session ends, the memory goes with it. Ask it tomorrow what you decided today — it has no idea."

> "The workaround everyone reaches for: make the context window bigger. Stuff everything in. Add a retrieval-augmented generation step, pull in docs, add conversation history — eventually the context is enormous and the model still has to process every token of it to answer a simple question."

**Slide 6 — "The context window trap"**

**Saying:**
> "Let's put numbers on this. A one-million-token context costs ten to one hundred times more per query than a targeted memory lookup. Every token in context is read on every forward pass. Ninety-five percent of what you stuffed in is noise for this particular question. And when the session ends — it's gone. There's no persistence. You can't semantically query a flat wall of text."

> "This isn't a criticism of long-context models. They're impressive. But they're not memory. They're a very large working surface."

**Slide 7 — "Enterprise scale reality"**

**Saying:**
> "Real enterprise workloads mean thousands of sessions, millions of turns, multiple agents, multiple team members, all working on the same project. You need memory that persists across sessions and machines. You need memory you can query with a natural language question. You need memory that scales to millions of stored interactions without degrading. And you need it to be auditable — you need to know what the agent recalled and why."

> "Context windows aren't that. Elasticsearch is."

**They should think:** *I've hit this wall. Context stuffing is a workaround, not a solution.*

---

### Slides 8–12: Memory-as-a-Service (10 min)

**Slide 9 — "Memory taxonomy"**

**Saying:**
> "Think about what agents actually need to remember. Three types. Episodic: what happened — the conversation turns, the actions taken. Semantic: what was decided — the 'why' behind architectural choices, the facts extracted from sessions. Procedural: how things work — established workflows, project conventions, the patterns your team follows."

> "All three live in Elasticsearch. Queried with Jina semantic embeddings and ES|QL."

**Slide 10 — "Why Elasticsearch?"**

**Saying:**
> "Elasticsearch is already where enterprise data lives. Logs, documents, vectors, structured records. It's the right store for agent memory because: Jina semantic embeddings mean 'which database did we choose?' returns the right answer even if the exact words don't match. Hybrid search — semantic plus BM25 — means you get fuzzy recall and keyword precision from the same query. ES|QL means structured recall: 'list all sessions from last month.' And you probably already have it. No new infrastructure."

**Slide 11 — "Architecture overview"**

**Saying:**
> "The full stack is three boxes. Kiro — Amazon Bedrock, free tier, Claude Sonnet — is the agentic IDE. Elastic Agent Builder is the memory server. It exposes a native MCP endpoint at your Kibana URL. Kiro speaks directly to it — no custom MCP server, no middleware to build or operate. Agent Builder executes the memory tools against Elasticsearch and returns results."

> *(point at diagram)*
> "Kiro. Agent Builder. Elasticsearch. That's it."

**Slide 12 — "Jina powers semantic recall"**

**Saying:**
> "A quick note on the embedding layer, because this is where the magic happens. Elastic's `semantic_text` field type uses Jina v5 embeddings by default. You declare one field. At ingest, Jina vectorizes the content automatically. At query time, Agent Builder calls `nlQuery` with a natural language question — Jina encodes it, Elasticsearch runs the vector search, fuses it with BM25. You get back the semantically closest documents."

> "The developer asks: 'which database did we choose and why?' The answer comes back: Aurora PostgreSQL, session 3, because DynamoDB's eventual consistency failed cart total accuracy. Not because those exact words were in the question — because the meaning matched."

**They should think:** *This is how semantic search actually works in practice. One field type, automatic.*

---

### Slides 13–18: How It's Built (10 min)

**Slide 14 — "Three indices"**

**Saying:**
> "Three indices. Conversation-history stores every turn — role, content, topic tags, session ID, timestamp. Knowledge-facts stores decisions, bug fixes, requirements — the 'why' behind choices. Session-metadata stores session IDs, start and end times, project summaries, topic lists."

> "Each index has a `semantic_text` field. Jina embeddings auto-generated at ingest. You don't touch them — they're just there."

**Slide 15 — "Semantic search"**

**Saying:**
> "The `search-knowledge-facts` tool is an `index_search` type. You give it a description, a pattern — `knowledge-facts` — and Agent Builder handles the semantic search. The agent sends an nlQuery. Jina encodes it. Elasticsearch returns the top results. No query DSL, no manual embedding, no retrieval pipeline to maintain."

**Slide 16 — "ES|QL"**

**Saying:**
> "Not all recall is semantic. Sometimes you need exact structured answers. What did we work on recently? List all sessions. For that, ES|QL tools. `FROM conversation-history | SORT timestamp DESC | LIMIT 20 | KEEP session_id, timestamp, role, content`. Plain SQL-style query. The agent calls this when it needs time-ordered data, not semantic similarity."

**Slide 17 — "Agent Builder tools"**

**Saying:**
> "Four tools in the agent: search-conversation-history, search-knowledge-facts, get-recent-conversations, list-sessions. Two semantic search, two ES|QL. Configured once in Kibana. Exposed via MCP to any IDE that supports the protocol. Create the tools programmatically — the repo has the script."

**Slide 18 — "MCP wiring"**

**Saying:**
> "The MCP config is literally three lines of JSON. URL: your Kibana URL plus `/api/agent_builder/mcp`. Authorization header: API key. Two more headers required by the Kibana API. Drop this into Kiro's MCP settings, restart Kiro, and your agent has four memory tools available."

> "There's no custom server. No middleware. The endpoint is built into Elastic Agent Builder."

**They should think:** *I could set this up this afternoon.*

---

### Slide 19 + Demo: Let's See It (~11 min)

**Before Navattic plays:**

**Saying:**
> "Let me show you what this looks like in practice. The scenario: I'm a developer who's been building a checkout service. Ten sessions over two weeks. Decisions made, bugs fixed, architecture choices locked in. Watch what happens when I ask the agent about the project."

> *(transition to Navattic)*

**After Navattic plays:**

*(brief pause)*

> "That's it. No context stuffing, no retrieval pipeline, no custom server. One config file. Persistent memory."

---

### Slides 20–22: Demo Recap (5 min)

**Slide 20 — "What just happened"**

**Saying:**
> "When I asked 'which database?' — the agent called search-knowledge-facts. Jina encoded the question. Elasticsearch returned the closest semantic match from the knowledge-facts index. The answer was Aurora PostgreSQL — with the reasoning, and the session it came from. It didn't hallucinate. It retrieved."

**Slide 21 — "Key design decisions"**

**Saying:**
> "A few things that made this work. `semantic_text` with Jina: no embedding pipeline — declare the field, ingest, done. Agent Builder as the MCP server: no proxy layer to build or deploy. ES|QL plus semantic search from the same cluster: structured and fuzzy recall in one place. Three-index schema: conversation turns, extracted facts, session metadata — each independently queryable."

**Slide 22 — "Scale properties"**

**Saying:**
> "This isn't a demo pattern — it's production-ready. Millions of conversation turns, stored and searchable in milliseconds. Multi-user: every agent on the team reads and writes the same memory store. Cross-session: pick up exactly where you left off, on any machine. Elasticsearch already handles this scale for search and observability workloads. Agent memory is just another index."

**They should think:** *I understand why it works, not just that it works.*

---

### Slides 23–25: Build It Yourself (5 min)

**Slide 24 — "The repo"**

**Saying:**
> "Everything I just showed you is in the repo. `github.com/jeffvestal/elastic-bedrock-memory`. Three setup scripts: create-indices, create-agent — that builds the Agent Builder agent and all four tools programmatically — and seed, which loads demo data. Plus the Kiro MCP config template."

> "Companion blog has the full walkthrough with architecture diagrams and code deep-dive. Link on the closing slide."

**Slide 25 — "5-minute quickstart"**

**Saying:**
> "Clone the repo. Configure your `.env` with ES URL, Kibana URL, API keys. Run the three setup scripts. Copy the Kiro MCP config. Restart Kiro. Ask your agent about the project."

> "If you have an Elastic Cloud account — which if you don't, free trial at cloud.elastic.co — the whole setup is about five minutes."

---

### Slide 26: Close + Q&A (8 min)

**Saying:**
> "Two URLs, both on the slide. The repo has everything you need to build this. The blog has everything you need to understand why it's built the way it is."

> "Quick recap: Bedrock handles the inference. Elastic handles the memory, the search, and the observability. They're not competing — they're composable. Wire them together and your agents remember what matters."

> "Questions."

---

## One-Line Story Per Section (for plane review)

| Section | One line |
|---------|----------|
| Intro | Memory is the missing layer. Today you're getting it. |
| Amnesia Problem | Stateless by default. Context windows are a workaround, not a solution. |
| Memory-as-a-Service | Elasticsearch is already the right store — you just haven't wired it to your agents yet. |
| How It's Built | Three indices, four tools, one config file. |
| Demo | The agent recalled a decision from two weeks ago, with the reasoning. |
| Recap | Semantic retrieval, not hallucination. The answer came from your data. |
| Build It | Clone, configure, run three scripts, restart Kiro. Five minutes. |

---

## What They Should Leave Thinking

**The problem you solved:** AI agents today are stateless. They know your codebase. They have no idea what your team decided in a meeting last Thursday, or why you chose PostgreSQL over DynamoDB, or what that 2am incident was about. The context window workaround is expensive, ephemeral, and doesn't scale.

**What you showed:** Elasticsearch as persistent agent memory, wired into Kiro via Elastic Agent Builder's native MCP endpoint. Jina semantic embeddings for natural-language recall. ES|QL for structured queries. A three-index schema that separates conversation turns, extracted facts, and session metadata.

**Why Elastic:** Agent Builder handles tool grounding, MCP serving, conversation logging, and audit trails — in Kibana, which they may already have. The MCP endpoint is built in. No custom server to write, deploy, or operate.

**The one thing to remember:** The agent answered "which database and why?" with the right answer and the right reason — from a decision made in a conversation it wasn't part of. That's the jump. From session-scoped to persistent. From context-stuffed to semantically queryable. That's what adding memory gives you.

---

## Quick Delivery Notes

- **Pace the amnesia problem section slowly.** Let it land before you solve it. The audience needs to feel the pain before you offer the fix.
- **On the architecture slide:** don't over-explain. Say the three boxes, say the arrow, move on. The demo proves it works.
- **During demo recap:** don't re-narrate what they just watched. Go one level deeper — the "why the answer was right" explanation.
- **Questions tend toward:** "what if I have a different IDE?" (Any MCP-compatible client works), "does this work with non-AWS Bedrock?" (Agent Builder MCP works with any LLM front-end), "what does it cost?" (Elastic Cloud serverless + Bedrock free tier for demo — production pricing depends on usage).
- **Don't go over time.** Cut from demo recap if running long — the build-it-yourself section is the one they came for.
