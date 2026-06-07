---
type: blog-outline
title: "Give Your AI Reviewer a Memory: Using Past Incidents and OTel Traces to Catch Bugs at PR Time"
status: draft-outline
category: content
created: 2026-06-07
tags: [blog, otel, agent-builder, rca, pr-review, search-labs]
target: Search Labs blog (or DevOps/SRE outlet)
audience: Developers, platform engineers, SREs
---

# Blog Outline: Give Your AI Reviewer a Memory

## Working Title
**"Give Your AI Reviewer a Memory: Using Past Incidents and OTel Traces to Catch Bugs at PR Time"**

Alt titles:
- "The PR That Should Have Been Caught: AI Code Review Grounded in Production Telemetry"
- "Your AI Reviewer Has Amnesia. Here's How to Fix It."
- "From RCA to PR: Closing the Loop Between Incidents and Code Review"

---

## One-Sentence Pitch
Most teams treat incident postmortems and OTel traces as historical artifacts — this post shows how to wire them into your AI code reviewer so it recognizes a pattern that caused a production outage the next time that pattern appears in a PR.

---

## Hook / Cold Open (~200 words)

Open with the scenario:

> A developer opens a PR. Title: "perf: split inventory read/write for query plan cache efficiency." One file changed. The description talks about prepared statement cache hit rates. The diff looks clean. In most orgs, this is a merge-on-sight PR.
>
> What the diff doesn't say: six weeks ago, a nearly identical change caused a reservation oversell incident at 2am. The postmortem named the pattern — non-atomic read-modify-write on a shared counter — and the OTel traces showed the fingerprint exactly: two concurrent requests, both reading stock=1, both writing stock=0, result: two successful reservations, one unit.
>
> Your AI reviewer read the codebase. It did not read the postmortem. It did not read the traces. It approved the PR.

Frame the gap: **code awareness ≠ operational awareness.** Today's AI reviewers know syntax, patterns, and docs. They don't know what broke prod.

---

## Section 1: The Incident Pattern Problem (~400 words)

### 1.1 RCAs live in the wrong place
- Incident postmortems end up in Confluence, Linear, Notion, PagerDuty — nowhere near the code review loop
- OTel traces are in your APM backend — query-able, but nobody queries them at PR time
- Engineers who worked the incident know the pattern; engineers who didn't have no way to inherit that knowledge

### 1.2 What "institutional memory" actually means for code review
- Not: "the model was trained on code that had this bug"
- Yes: "the model was shown your specific incident data, your specific trace, at query time"
- The distinction matters: training-time knowledge is frozen, retrieval-time knowledge is current and attributable

### 1.3 The TOCTOU class of bugs — why they're invisible to static review
- Brief primer: Time-Of-Check-To-Time-Of-Use race conditions
- Why they don't appear in the diff: the removed guard (`AND quantity >= N`) looks like a simplification, not a race
- Why they do appear in traces: concurrent spans show both requests reading the same value before either writes — the causal chain is there in the telemetry
- The reviewer needs to know what to look for before it can flag it

---

## Section 2: The Architecture (~500 words)

### 2.1 The four-box picture
```
PR opens → GitHub Action → Elastic Workflow → Agent Builder agent
                                                    ↓
                                          OTel traces index (ES|QL)
                                          Incident postmortems index (semantic search)
                                                    ↓
                                          Bot comment on PR
```

- No human in the loop for the detection step
- ~45 seconds from PR open to comment posted

### 2.2 Two sources of memory

**Source 1: OTel traces**
- Stored in Elasticsearch (`traces-apm.*` index)
- The agent runs ES|QL queries: find spans matching the changed endpoint/function over the past N weeks, filter for anomalous durations or concurrency signatures
- Returns raw span data: timestamps, durations, HTTP route, service name, span count per trace
- Example query: `FROM traces-apm.wayfinder-default | WHERE http.route == "/api/v1/checkout/reserve" AND span.duration.us > 3000000`
- The agent cited a 6.2-second span from 6 weeks prior — that span was the incident

**Source 2: Incident postmortems / RCAs**
- Indexed as documents (Confluence pages, PagerDuty postmortems, GitHub issues)
- Agent uses semantic search or keyword search against this index
- Surfaces issue numbers, root cause language, affected endpoints
- In the demo: agent surfaces Issue #N from 6 weeks prior, quoting its root cause description

### 2.3 Skills encode judgment, tools fetch facts
- ES|QL tools: grounded retrieval — the agent can only claim what the query returns
- Skills (reusable instruction blocks): encode the *patterns to look for* — TOCTOU, non-atomic read-modify-write, lock contention
- Separation of concerns: the skill tells the agent what a race condition looks like; the tool tells the agent what actually happened in prod
- Editable, versionable, shareable across every agent the team builds

### 2.4 The workflow layer
- GitHub Action is minimal: one step, one HTTP call to an Elastic Workflow
- Elastic Workflow: two steps — `invoke_agent` (calls Agent Builder with PR metadata), `log_outcome`
- Every run is logged and auditable in Kibana Workflows → Executions
- 51 seconds wall-clock from GitHub trigger to agent response (from a real run)

### 2.5 The fix loop (VS Code / Copilot Agent Mode)
- The bot comment names the pattern and cites the evidence
- Developer opens VS Code, types in natural language: "I got a PR comment saying this matches a trace pattern from 6 weeks ago. Pull those traces and help me understand the fix."
- Copilot Agent Mode calls the same Elastic MCP server, runs the same ES|QL query, returns the same trace data
- Developer says "yes" — Copilot applies the fix (adds back the atomic guard), writes a regression test, runs it
- MCP config is committed to the repo (`.vscode/mcp.json`) — every developer gets it automatically

---

## Section 3: What Made the Detection Work (~300 words)

### 3.1 The agent named the pattern, not the keyword
- The diff never says "race condition", "TOCTOU", or "deadlock"
- The bot comment names "TOCTOU" and "non-atomic read-modify-write"
- Why: the Skill encoded what these patterns look like structurally; the agent matched the diff structure to the skill's description
- This is the semantic jump: from syntax (a removed WHERE clause) to semantics (a check eliminated before a write)

### 3.2 The evidence is grounded, not hallucinated
- Every claim in the bot comment is backed by a retrieved document or trace span
- Trace ID, span duration, HTTP route, incident issue number — all pulled at query time
- The agent cannot invent a trace that doesn't exist; the ES|QL query either returns rows or it doesn't
- This matters for trust: you can click the trace ID and see the raw data

### 3.3 The concurrency harness as a sanity check
- After the fix: run 20 parallel reservation requests against stock of 1
- Result: exactly 1 succeeds, 19 get `reserved: false` — atomic behavior confirmed
- Before the fix: multiple succeed — oversell reproduced
- The harness is what the agent is doing conceptually, but with institutional memory across a 6-week window instead of a synthetic load

---

## Section 4: Generalization — This Pattern Works Anywhere (~300 words)

### 4.1 The stack is interchangeable
- The key elements: a vector/search store, an agentic workflow layer, a way to trigger review on PR open
- Elasticsearch is used here, but the architecture applies to any searchable store
- The agent framework is Agent Builder, but the pattern works with any tool-using LLM
- MCP makes the "fetch traces in VS Code" step portable: works in Claude Desktop, Cursor, any MCP-aware client

### 4.2 What to index
- OTel traces (APM spans): the highest-signal source — actual runtime behavior under concurrency
- Incident postmortems: RCA language, root cause descriptions, affected endpoints
- On-call runbooks: known workarounds often hint at known failure patterns
- Resolved GitHub issues: "fixed in #N" traces the bug forward and backward

### 4.3 What Skills to encode
- Race conditions / TOCTOU
- N+1 query patterns
- Missing auth checks at new routes
- Schema migration patterns that cause lock contention
- Any class of bug that your team has seen more than once

### 4.4 What the reviewer still can't do
- It cannot run the code; it reasons from traces and diffs
- It cannot know about patterns you haven't had incidents for yet
- It is a signal, not a gatekeeper — you still need engineers to read the comment and decide

---

## Section 5: Getting Started (~200 words)

### What you need
1. OTel traces in a searchable store (Elasticsearch, any APM backend with a query API)
2. Postmortems/RCAs in text form — Confluence, Notion, GitHub Issues, PagerDuty — indexed alongside or separately
3. An agent framework that supports tool use (Agent Builder, LangChain, any tool-using LLM)
4. A trigger: GitHub Action, GitLab CI, Bitbucket pipe — anything that fires on PR open and can call an HTTP endpoint

### The fastest path
- Start with OTel traces only (postmortems are bonus)
- Write one ES|QL (or SQL/vector query) that fetches recent spans for the changed endpoint
- Write one Skill that describes your most common incident pattern
- Wire a GitHub Action to call the agent with the PR diff
- Iterate on Skills as you accumulate more incident patterns

### Try it (Instruqt lab)
- [Link to lab if published]
- Wayfinder Supply Co. repo: [repo link]

---

## Closing (~150 words)

The insight is simple: your team already did the work. The incident happened, the postmortem was written, the traces are stored. The only thing missing was a path from those artifacts to the next PR that would repeat the mistake.

This is what institutional memory means for AI-assisted development — not a model trained on millions of repositories, but an agent grounded in *your* incidents, *your* traces, *your* patterns.

Three takeaways:
1. **Code awareness is table stakes. Operational awareness is the unlock.** Your AI reviewer needs to know what broke prod, not just what the code looks like.
2. **OTel traces are underutilized AI grounding data.** You're collecting them already. The fingerprint of every past incident is in there.
3. **Skills encode expertise once, apply everywhere.** Write the race-condition skill once. Attach it to every agent that reviews PRs, designs, or incident tickets.

---

## Appendix: Technical Details for the Technically Curious

*Optional sidebar / expandable section for the blog — not in the main flow.*

### The ES|QL query that found the incident trace
```esql
FROM traces-apm.wayfinder-default
| WHERE http.route == "/api/v1/checkout/reserve"
  AND span.duration.us > 3000000
  AND @timestamp > now() - 60d
| SORT span.duration.us DESC
| LIMIT 20
```

### The GitHub Action (full YAML)
```yaml
name: elastic-pr-review
on:
  pull_request:
    types: [opened]
jobs:
  trigger-elastic-review:
    runs-on: ubuntu-latest
    steps:
      - name: Call Elastic Agent Builder + Post PR Comment
        run: |
          # call Elastic Workflow endpoint with PR metadata
          # post response as GitHub PR comment
```
*(trimmed — full YAML in repo)*

### The PR Race Condition Analysis Skill (excerpt)
```
TOCTOU (Time-Of-Check-To-Time-Of-Use):
A TOCTOU race occurs when a program checks a condition (e.g., sufficient
inventory) and then acts on it (e.g., decrement stock) as two separate,
non-atomic operations. Under concurrency, multiple threads/requests can
all pass the check before any write completes, leading to oversell,
double-booking, or privilege escalation.

Look for: separated read + conditional write where a single atomic
read-modify-write previously existed. Common in inventory, reservation,
rate-limiting, and permission-check code.
```

---

## Notes for Blog Writer Agent

- **Tone:** Practitioner-first. Not a product pitch — a pattern walkthrough. The reader should come away able to build this with any stack.
- **Elastic specifics:** Mention Agent Builder, ES|QL, MCP, Workflows by name but explain what each does so non-Elastic readers follow. Don't assume Kibana familiarity.
- **GitHub/Copilot specifics:** Mention but don't center — the pattern is stack-agnostic.
- **Length target:** 1800–2500 words for the main body (Sections 1–5 + close). Appendix is bonus.
- **Code blocks:** Include the ES|QL query, the harness output (`1 / 20 requests succeeded`, `✓ atomic behavior`), and the bot comment excerpt. These are the most concrete artifacts.
- **The TOCTOU explanation** in Section 1.3 needs to be accessible to a developer who hasn't seen the term before — one paragraph, concrete example, no jargon.
- **Do not write:** "In this blog post we will…" / "In conclusion…" / marketing language about Elastic products. Just build the argument.
- **Key phrases to preserve verbatim (from the demo script):**
  - "Your AI reviewer has amnesia."
  - "Code awareness is table stakes. Telemetry + postmortems is the unlock."
  - "Tools fetch facts. Skills carry judgment."
  - "Not from training data — from your data."
