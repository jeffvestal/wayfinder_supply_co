---
type: blog-draft
title: "Give your AI reviewer a memory: using past incidents and OTel traces to catch bugs at PR time"
status: draft
category: content
audience: developer
target: search-labs
archetype: "tutorial-with-architecture / practitioner-pattern"
created: 2026-06-07
updated: 2026-06-07
tags: [otel, agent-builder, esql, rca, pr-review, agentic-search, mcp, toctou]
word_count: ~2400
---

# Give your AI reviewer a memory: using past incidents and OTel traces to catch bugs at PR time

A developer opens a PR. Title: "perf: split inventory read/write for query plan cache efficiency." One file changed. The description talks about prepared statement cache hit rates. The diff looks clean. In most orgs, this is a merge-on-sight PR.

What the diff doesn't say: six weeks ago, a nearly identical change caused a reservation oversell incident at 2am. The postmortem named the pattern exactly — non-atomic read-modify-write on a shared counter. The OTel traces showed the fingerprint: two concurrent requests, both reading `stock=1`, both writing `stock=0`, result: two successful reservations, one unit of inventory.

Your AI reviewer read the codebase. It did not read the postmortem. It did not read the traces. It approved the PR.

**Your AI reviewer has amnesia.**

The fix isn't a better model. It's wiring the right data to the reviewer at query time — your incidents, your traces, your patterns. This post walks through how to do that.

---

## The gap between code awareness and operational awareness

Today's AI code reviewers are genuinely good at what they do. They catch style violations, flag missing null checks, spot N+1 queries by pattern recognition, and surface API misuse. What they can't do is tell you whether the change in front of them matches a failure pattern your team lived through six weeks ago.

That's not a model capability problem. It's a data access problem.

### Where incident knowledge actually lives

After a production incident, the institutional memory ends up in three places: the postmortem document (Confluence, Notion, PagerDuty, a GitHub issue), the OTel traces from the incident window (sitting in your APM backend), and the heads of the engineers who worked the incident. The first two are queryable. The third walks out the door.

The postmortem names the pattern in plain language: "non-atomic read-modify-write on the reservation endpoint." The traces show the causal chain at microsecond resolution: two concurrent spans, identical read values, colliding writes. That's your institutional memory, and it's already stored. It's just not connected to your code review loop.

### Training-time knowledge vs. retrieval-time knowledge

There's a meaningful distinction worth drawing here. When an AI model "knows" something from training, that knowledge is frozen at the training cutoff, it covers general patterns from public data, and you can't audit what it's drawing on. When an agent retrieves something at query time from your indexed postmortems and traces, that knowledge is current, it covers your specific systems, and every claim is attributable to a specific document or span ID.

Not from training data — from your data. That distinction matters when you're deciding whether to trust a reviewer's flag.

### Why TOCTOU bugs are invisible to static review

The incident in this walkthrough involved a TOCTOU race condition. Here's what that means without the acronym: your code checks a condition (is there enough inventory?), and then separately acts on it (reserve the inventory). If two requests run at the same time, both can pass the check before either one completes the write. Both see `stock=1`. Both write `stock=0`. Both return "success." You've sold the same item twice.

The reason this class of bug doesn't show up in diffs: the change that introduces it usually looks like a simplification. The original code had an atomic guard — a single database operation that checked and updated in one step. The new code splits those into two operations because it looks cleaner, or because someone optimized the read path for caching. The removed guard is a one-line deletion. It doesn't look dangerous. It looks like cleanup.

Where TOCTOU does show up is in traces. Concurrent spans on the same endpoint, both reading the same field value before either write completes — the causal chain is in the telemetry, if you know what to look for. The reviewer needs to know what to look for before it can flag anything.

---

## The architecture

Here's the system, end to end:

```
PR opens → GitHub Action → Elastic Workflow → Agent Builder agent
                                                    |
                                          OTel traces index (ES|QL)
                                          Incident postmortems index (semantic search)
                                                    |
                                          Bot comment posted to PR
```

No human in the detection loop. Roughly 45 seconds from PR open to comment posted. Here's what each piece does.

### Two sources of memory

The agent gets grounded by two data sources.

**OTel traces.** Stored in Elasticsearch under the `traces-apm.*` index pattern. The agent runs ES|QL queries to find spans matching the changed endpoint over the past N weeks, filtered for anomalous durations or concurrency signatures. The query returns raw span data: timestamps, durations, HTTP route, service name, span count per trace.

The ES|QL query that found the incident trace in this demo:

```esql
FROM traces-apm.wayfinder-default
| WHERE http.route == "/api/v1/checkout/reserve"
  AND span.duration.us > 3000000
  AND @timestamp > now() - 60d
| SORT span.duration.us DESC
| LIMIT 20
```

That query returned a 6.2-second span from six weeks prior. That span was the incident.

ES|QL is a pipelined query language built into Elasticsearch — similar in spirit to SQL but designed for log and observability data. You pipe `FROM` into `WHERE` into `SORT` into `LIMIT`. The agent constructs and executes these at review time; it doesn't rely on precomputed results.

**Incident postmortems.** Indexed as documents — Confluence exports, PagerDuty postmortem PDFs, GitHub issues, whatever your team writes. The agent uses semantic search against this index to find issue numbers, root cause descriptions, and affected endpoints. In this walkthrough, the agent surfaced Issue #47 from six weeks prior and quoted its root cause description verbatim in the PR comment.

### Tools fetch facts. Skills carry judgment.

This is where the architecture gets interesting. The ES|QL queries are *tools* — they fetch facts. What actually happened in prod, which spans ran, what durations were recorded. The tools are grounded: the agent can only claim what the query returns. It cannot invent a trace that doesn't exist.

The patterns the agent looks for — TOCTOU, non-atomic read-modify-write, lock contention — are encoded in *Skills*. A Skill in Elastic Agent Builder is a reusable instruction block: structured guidance you write once and attach to agents. You can think of it as the agent's trained eye. It describes what a race condition looks like structurally, so the agent knows what to watch for when it reads a diff.

Tools fetch facts. Skills carry judgment.

The practical implication: when you encounter a new class of incident, you don't retrain anything. You write a new Skill, attach it, and every agent on your team that uses it picks up the new detection capability. Skills are editable, versionable, and shareable.

### The workflow layer

The GitHub Action is minimal — one step, one HTTP POST to an Elastic Workflow endpoint with PR metadata (diff, changed files, commit message).

Elastic Workflow is the orchestration layer: it defines the sequence of steps, invokes the Agent Builder agent, and logs the outcome. Every execution is auditable in the Workflows UI. In practice, the workflow has two steps: `invoke_agent` (sends the PR diff and changed endpoints to the agent) and `log_outcome` (records the result). Wall-clock time in a real run: 51 seconds from GitHub trigger to agent response.

The GitHub Action stub:

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
          # POST PR metadata to Elastic Workflow endpoint
          # Post agent response as GitHub PR comment
```

The action itself is simple on purpose. The intelligence lives in the agent and its data sources, not in CI configuration.

### The fix loop

The bot comment doesn't just flag the problem — it names the pattern, cites the trace ID and span duration, and references the incident issue number. A developer who gets that comment has everything they need to understand what's being flagged.

From there, the fix path in this demo uses VS Code with GitHub Copilot Agent Mode connected to the same Elastic MCP server. The developer types: "I got a PR comment saying this matches a trace pattern from 6 weeks ago. Pull those traces and help me understand the fix." Copilot Agent Mode calls the MCP server, runs the same ES|QL query, returns the same trace data. The developer reviews, confirms, and Copilot applies the fix — restores the atomic guard, writes a regression test.

The MCP server config is committed to the repo in `.vscode/mcp.json`, so every developer on the team gets it automatically. Mention GitHub and Copilot here because that's what the demo uses, but this step is fully portable: any MCP-aware client (Claude Desktop, Cursor, or a custom tool) can connect to the same server and run the same queries.

---

## What made the detection work

The bot comment named "TOCTOU" and "non-atomic read-modify-write." The diff never used those words. The developer who wrote the PR didn't describe it as a race condition. How did the agent get there?

### Pattern matching, not keyword matching

The Skill told the agent what a TOCTOU race looks like structurally: a separated read-and-conditional-write where a single atomic read-modify-write previously existed. When the agent read the diff, it matched the structural description — a `WHERE quantity >= N` guard removed, with the read and write now on separate lines — to that pattern. The jump from syntax to semantics was the Skill's job, not the model's general knowledge.

This matters because the same kind of structural description works for other bug classes. An N+1 query pattern, a missing auth check on a new route, a schema migration that causes lock contention — each of these can be described structurally in a Skill. The model doesn't need to have seen your specific code before. It needs to know what the shape of the problem looks like.

### The evidence is grounded, not hallucinated

Every claim in the bot comment is backed by a retrieved artifact:

```
PR Review Bot flagged:
- Pattern: TOCTOU / non-atomic read-modify-write
- Matched trace: span ID a3f82b1c, duration 6.2s, route /api/v1/checkout/reserve
- Incident reference: Issue #47 (2025-04-22): "Reservation oversell under concurrent load"
- Root cause from postmortem: "Read and write split across two queries; atomic guard removed in f3a9c2b"
```

The trace ID is real — you can click it and see the raw span. The issue number is real. The agent cannot invent a trace span that isn't in the index. ES|QL either returns rows or it returns nothing. This is why retrieval-grounded review is more trustworthy than model knowledge alone: the evidence is auditable.

### The concurrency harness as proof

After the fix is applied, you need to confirm it actually works. The harness runs 20 parallel reservation requests against a single unit of inventory:

```
Running 20 concurrent requests against stock=1...
  1 / 20 requests succeeded (reserved: true)
 19 / 20 requests received reserved: false
✓ atomic behavior confirmed
```

Before the fix, multiple requests succeed — oversell reproduced. After, exactly one succeeds. This is the same logic the agent is applying conceptually when it looks for concurrent spans with identical read values. The harness makes it concrete and reproducible.

---

## This pattern works with any stack

The architecture above uses Elasticsearch, Elastic Agent Builder, and GitHub Actions. None of those are requirements.

The key elements are:

1. A searchable store for traces and postmortems (any APM backend with a query API works)
2. A tool-using agent that can call that API at review time (LangChain, LlamaIndex, any framework that supports tool use)
3. A way to encode patterns as reusable instructions (a system prompt, a tool description, a skill file — whatever your framework calls it)
4. A trigger on PR open that calls the agent with the diff

MCP is worth singling out here. If your agent exposes its tools via an MCP server, any MCP-aware client can reuse those same tools in developer workflow contexts — VS Code, Claude Desktop, Cursor. You write the query logic once and it's available everywhere. That's the portability argument for MCP: define the data interface once, connect any client.

### What to index

Start with OTel traces. They're the highest-signal source — actual runtime behavior under concurrency, with microsecond timestamps and causal relationships between spans. You're likely collecting them already if you run any APM tooling.

Add postmortems when you have them in indexable form. Even a flat-text export from Confluence is enough to get semantic search working. On-call runbooks and resolved GitHub issues are useful too — runbooks often describe known failure modes, and resolved issues trace bugs forward and backward through your codebase's history.

### What Skills to encode

Think about your incident history. What patterns have you seen more than once? That list is your Skill backlog.

Common candidates:
- TOCTOU / non-atomic read-modify-write (inventory, reservations, rate limiting, permission checks)
- N+1 query patterns (new ORM usage, missing batch fetch)
- Missing auth checks at newly added routes
- Schema migrations that cause table-level lock contention
- Retry logic without idempotency guarantees

Write one Skill per pattern. Keep them short and structural — describe what the code shape looks like, not what to call it. Attach each Skill to every agent that reviews PRs, designs, or incident tickets.

### What the reviewer still cannot do

Worth naming the limits clearly:

- It cannot run the code. It reasons from diffs and telemetry, not execution.
- It cannot know about patterns that haven't appeared in incidents yet. Novel bugs won't match existing Skills.
- It is a signal, not a gatekeeper. Engineers still read the comment and decide. A high-confidence flag from a grounded agent is useful input; it's not a merge block.

Code awareness is table stakes. Telemetry + postmortems is the unlock. But the reviewer is still a reviewer, not an authority.

---

## Getting started

What you actually need to build this:

1. **OTel traces in a queryable store.** Elasticsearch is one option; any APM backend that exposes a query API works. Start with the last 60 days of traces for your highest-traffic endpoints.

2. **Postmortems in indexed text form.** Confluence export, PagerDuty postmortem PDFs, GitHub issues — anything that can be chunked and vector-indexed alongside keyword search. Even 10-15 documents is enough to validate the pattern.

3. **A tool-using agent.** Elastic Agent Builder is what the demo uses, but LangChain, LlamaIndex, or any framework that supports tools and system prompts works here. The agent needs two tools: one to query traces, one to search postmortems.

4. **A PR trigger.** GitHub Action, GitLab CI, Bitbucket pipe — anything that fires on `pull_request: [opened]` and can POST to an HTTP endpoint. The action itself can be 10 lines.

The fastest path to a working prototype: skip postmortems initially. Start with OTel traces only. Write one ES|QL query that fetches recent spans for your highest-risk endpoint. Write one Skill that describes your most common incident pattern. Wire the GitHub Action. Run it against a test PR. Iterate from there as you accumulate more incident data.

If you want to work through the full setup hands-on, the Wayfinder Supply Co. demo repo is the reference implementation: [repo link]. An Instruqt lab is also in progress: [lab link when published].

---

## Three things to take away

Your team already did the hard work. The incident happened. The postmortem was written. The traces are stored. The only thing missing is a path from those artifacts to the next PR that would repeat the mistake.

**Code awareness is table stakes. Telemetry + postmortems is the unlock.** A reviewer that only reads the diff is working with half the picture. The other half — what actually broke prod, under what conditions, with what causal signature — is in your telemetry. Wire it in.

**OTel traces are underutilized AI grounding data.** You're collecting them already. The fingerprint of every past incident is in there: concurrent spans, anomalous durations, colliding writes. Querying them at PR time turns telemetry from a post-incident tool into a pre-incident signal.

**Skills encode expertise once, apply everywhere.** Write the TOCTOU skill once. Attach it to every agent on your team that reviews PRs, analyzes incident tickets, or audits design docs. The institutional knowledge that lives in an engineer's head after an incident can be extracted, versioned, and made available to every review from that point forward.

The institutional memory was always there. Now it has a path into the loop.

---

## Appendix: technical details

### The ES|QL query

```esql
FROM traces-apm.wayfinder-default
| WHERE http.route == "/api/v1/checkout/reserve"
  AND span.duration.us > 3000000
  AND @timestamp > now() - 60d
| SORT span.duration.us DESC
| LIMIT 20
```

This query filters spans by HTTP route and duration threshold (3 seconds, expressed in microseconds), then sorts by duration descending to surface the worst offenders first. The `now() - 60d` window covers the six-week lookback. Adjust the route, duration threshold, and window for your stack.

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

### The GitHub Action (trimmed)

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
          # POST PR metadata to Elastic Workflow endpoint
          # Post agent response as GitHub PR comment
```

Full YAML is in the repo. The action itself is intentionally thin — intelligence lives in the agent, not in CI configuration.

### SEO Q&A pairs

**Q: How do you use OpenTelemetry traces for AI code review?**
A: Index your OTel span data in a searchable store like Elasticsearch, then give an AI agent a query tool that retrieves recent spans for changed endpoints at PR time. The agent can identify anomalous duration patterns or concurrency signatures that match past incidents.

**Q: What is a TOCTOU race condition and how does it appear in code reviews?**
A: TOCTOU (Time-Of-Check-To-Time-Of-Use) is a race where a check and the action based on that check happen as separate, non-atomic operations. In a diff, it often looks like a simplification — a guard condition is removed. In traces, it shows up as concurrent spans reading the same value before either write completes.

**Q: What is Elastic Agent Builder?**
A: Agent Builder is the Elastic feature for creating tool-using AI agents. You define the agent's instructions, give it tools (like ES|QL queries), and attach Skills (reusable instruction blocks that encode domain-specific judgment). The agent can be invoked from workflows, APIs, or CI pipelines.

**Q: What is ES|QL?**
A: ES|QL is a pipelined query language built into Elasticsearch, designed for log and observability data. It uses a `FROM | WHERE | SORT | LIMIT` structure similar to SQL. AI agents can construct and execute ES|QL queries as tool calls.

**Q: How do you ground AI code review in your own incident history?**
A: Index your postmortems and OTel traces in Elasticsearch (or any searchable store), write an agent that queries those indexes when reviewing a PR diff, and encode your known incident patterns as Skills or system prompt instructions. The agent retrieves specific evidence — trace IDs, span durations, incident issue numbers — rather than reasoning from general training knowledge.

**Q: Can this architecture work without Elastic?**
A: Yes. The key elements are a searchable store for traces and postmortems, a tool-using agent framework, and a CI trigger on PR open. Elasticsearch and Elastic Agent Builder are used here, but the pattern applies to any stack with those three components.

**Q: What is an Elastic Workflow?**
A: Elastic Workflow is an orchestration layer within Elastic that lets you define multi-step automated processes. In this use case, the workflow receives the PR metadata from a GitHub Action, invokes the Agent Builder agent, and logs the result. Every execution is auditable in the Elastic Workflows UI.
