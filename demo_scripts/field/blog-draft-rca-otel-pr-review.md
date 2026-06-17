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

The postmortem names the pattern in plain language: "non-atomic read-modify-write on the reservation endpoint." The traces show the causal chain at microsecond resolution: two concurrent spans, identical read values, colliding writes — assuming your instrumentation captures the relevant field values as span attributes at read time. That's your institutional memory, and it's already stored. It's just not connected to your code review loop.

### Training-time knowledge vs. retrieval-time knowledge

There's a meaningful distinction worth drawing here. When an AI model "knows" something from training, that knowledge is frozen at the training cutoff, it covers general patterns from public data, and you can't audit what it's drawing on. When an agent retrieves something at query time from your indexed postmortems and traces, that knowledge is current, it covers your specific systems, and every claim is attributable to a specific document or span ID.

Not from training data — from your data. That distinction matters when you're deciding whether to trust a reviewer's flag.

### Why TOCTOU bugs are invisible to static review

The incident in this walkthrough involved a TOCTOU race condition. Here's what that means without the acronym: your code checks a condition (is there enough inventory?), and then separately acts on it (reserve the inventory). If two requests run at the same time, both can pass the check before either one completes the write. Both see `stock=1`. Both write `stock=0`. Both return "success" — a lost update: the second write overwrites the first, and both reservations are recorded as successful. You've sold the same item twice.

The reason this class of bug doesn't show up in diffs: the change that introduces it usually looks like a simplification. The original code had an atomic guard — a single database operation that checked and updated in one step. The new code splits those into two operations because it looks cleaner, or because someone optimized the read path for caching. The removed guard is a one-line deletion. It doesn't look dangerous. It looks like cleanup.

Where TOCTOU does show up is in traces. Concurrent spans on the same endpoint, both reading the same field value before either write completes — the causal chain is in the telemetry, if you know what to look for. The reviewer needs to know what to look for before it can flag anything.

---

## The architecture

Here's the system, end to end:

```
PR opens → GitHub Action → Agent Builder agent
                                    |
                          OTel traces index (ES|QL)
                          Incident postmortems index (semantic search)
                                    |
                          Bot comment posted to PR
```

No human in the detection loop. Here's what each piece does.

### Two sources of memory

The agent gets grounded by two data sources.

**OTel traces.** Stored in Elasticsearch under the `traces-apm.*` index pattern. The agent runs ES|QL queries to find spans matching the changed endpoint over the past N weeks, filtered for anomalous durations or concurrency signatures. The query returns raw span data: timestamps, durations, HTTP route, service name, span count per trace.

The ES|QL query that found the incident trace in this demo:

```esql
FROM traces-apm.wayfinder-default
| WHERE http.route == "/api/v1/checkout/reserve"
  AND span.duration.us > 3000000
  AND @timestamp > NOW() - 60 days
| SORT span.duration.us DESC
| LIMIT 20
```

That query returned a 6.2-second span from six weeks prior. That span was the incident.

Field names vary by APM agent and version — verify yours first: `FROM traces-apm.* | LIMIT 1 | KEEP *`. Common alternatives to `http.route`: `transaction.name`, `url.path`.

ES|QL is a pipelined query language built into Elasticsearch — similar in spirit to SQL but designed for log and observability data. You pipe `FROM` into `WHERE` into `SORT` into `LIMIT`. The agent constructs and executes these at review time; it doesn't rely on precomputed results.

**Incident postmortems.** Indexed as documents — Confluence exports, PagerDuty postmortem PDFs, GitHub issues, whatever your team writes. The agent uses semantic search against this index to find issue numbers, root cause descriptions, and affected endpoints. In this walkthrough, the agent surfaced Issue #47 from six weeks prior and quoted its root cause description verbatim in the PR comment.

### Tools fetch facts. Skills carry judgment.

This is where the architecture gets interesting. The ES|QL queries are *tools* — they fetch facts. What actually happened in prod, which spans ran, what durations were recorded. The tools are grounded: the agent can only claim what the query returns. It cannot fabricate a span ID or duration that isn't in the index — though the causal interpretation of retrieved spans is still agent-generated.

The patterns the agent looks for — TOCTOU, non-atomic read-modify-write, lock contention — are encoded in *Skills*. A Skill in Elastic Agent Builder is a reusable instruction block: structured guidance you write once and attach to agents. You can think of it as the agent's trained eye. It describes what a race condition looks like structurally, so the agent knows what to watch for when it reads a diff.

Tools fetch facts. Skills carry judgment.

The practical implication: when you encounter a new class of incident, you don't retrain anything. You write a new Skill, attach it, and every agent on your team that uses it picks up the new detection capability. Skills are editable and shareable — store them in Git alongside your agent configuration to version them.

### The workflow layer

The GitHub Action is minimal — one step, one HTTP POST to the Agent Builder API with PR metadata (diff, changed files, commit message). The action sends the full diff as part of the invocation payload. For large PRs, pre-filter to files touching your high-risk paths — sending a 5,000-line diff risks truncating the relevant section and producing a false negative.

The GitHub Action calls the Agent Builder API directly — one HTTP POST, streaming SSE response, PR comment posted by the action itself. Wall-clock time: 51 seconds from GitHub trigger to bot comment posted, measured on a GitHub-hosted `ubuntu-latest` runner with Elastic Cloud in us-central1. Budget 60–120 seconds for production SLA planning.

If you want every invocation auditable step-by-step in the Workflows UI, with built-in retry logic and execution history, you can add Elastic Workflow as an orchestration layer between the Action and Agent Builder. The workflow receives PR metadata from the Action, invokes the agent, and logs the outcome:


```yaml
version: "1"
name: elastic-agent-pr-review
enabled: true

triggers:
  - type: manual
    inputs:
      - name: pr_number
        type: string
        required: true
      - name: pr_title
        type: string
        required: true
      - name: repo
        type: string
        required: true
        description: "owner/repo"
      - name: diff_url
        type: string
        required: true
      - name: head_sha
        type: string
        required: true

steps:
  - name: invoke_agent
    type: http
    with:
      url: "YOUR_KIBANA_URL/api/agent_builder/converse/async"
      method: POST
      headers:
        Content-Type: application/json
        Authorization: "ApiKey YOUR_API_KEY"
        kbn-xsrf: "true"
      body: |
        {
          "agent_id": "YOUR_AGENT_ID",
          "input": "Review PR #{{ inputs.pr_number }} in {{ inputs.repo }}. Title: {{ inputs.pr_title }}. Diff URL: {{ inputs.diff_url }}. Head SHA: {{ inputs.head_sha }}. Fetch the diff, correlate against OTel traces and historical incident postmortems, and post a PR comment with evidence if a known pattern matches."
        }
    on-failure:
      retry:
        max-attempts: 2
        delay: 5s

  - name: log_outcome
    type: console
    with:
      message: "PR review completed for {{ inputs.repo }}#{{ inputs.pr_number }}"
```

The action itself is intentionally thin — the intelligence lives in the agent, not in CI configuration. For simpler setups, skip the workflow layer and call the Agent Builder API directly (as shown below).

```yaml
name: elastic-pr-review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  trigger-elastic-review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - name: Call Elastic Agent Builder + Post PR Comment
        env:
          PR_NUMBER: ${{ github.event.pull_request.number }}
          PR_TITLE: ${{ github.event.pull_request.title }}
          REPO: ${{ github.repository }}
          DIFF_URL: ${{ github.event.pull_request.diff_url }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
          GH_TOKEN: ${{ github.token }}
          ELASTIC_KIBANA_URL: ${{ secrets.ELASTIC_KIBANA_URL }}
          ELASTIC_API_KEY: ${{ secrets.ELASTIC_API_KEY }}
          AGENT_ID: ${{ secrets.AGENT_ID }}
        run: |
          if [ -z "$ELASTIC_KIBANA_URL" ] || [ -z "$ELASTIC_API_KEY" ]; then
            echo "Elastic secrets not configured — skipping PR review"
            exit 0
          fi

          # Fetch diff, cap at 8KB to stay within agent context window
          diff_content=$(curl -sL "${DIFF_URL}" | head -c 8000 || echo "(diff unavailable)")

          payload=$(jq -n \
            --arg agent_id "$AGENT_ID" \
            --arg input "Review PR #${PR_NUMBER} in ${REPO}. Title: ${PR_TITLE}. Head SHA: ${HEAD_SHA}.\n\nDiff:\n${diff_content}\n\nSearch OTel traces and incident postmortems for patterns related to this change. Correlate findings and summarize risk." \
            '{agent_id: $agent_id, input: $input}')

          # Call Agent Builder streaming endpoint, parse SSE response
          agent_comment=$(curl -fsS --no-buffer \
            -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
            -H "Content-Type: application/json" \
            -H "kbn-xsrf: true" \
            -d "$payload" \
            "${ELASTIC_KIBANA_URL}/api/agent_builder/converse/async" \
            | grep '^data:' | sed 's/^data: //' | python3 -c "
          import sys, json
          parts, final = [], ''
          for line in sys.stdin:
              line = line.strip()
              if not line: continue
              try:
                  d = json.loads(line)
                  delta = d.get('data', {})
                  if 'message_content' in delta: final = delta['message_content']
                  elif 'text_chunk' in delta: parts.append(delta['text_chunk'])
              except: pass
          print((final or ''.join(parts)).strip())
          ")

          if [ -z "$agent_comment" ]; then
            echo "Agent returned no analysis — skipping PR comment"
            exit 0
          fi

          gh pr comment "$PR_NUMBER" --repo "$REPO" \
            --body "## Elastic Agent Builder — PR Review

          $agent_comment

          ---
          *Powered by [Elastic Agent Builder](https://elastic.co/agent-builder) + OTel traces*"
```

### The fix loop

The bot comment doesn't just flag the problem — it names the pattern, cites the trace ID and span duration, and references the incident issue number. A developer who gets that comment has everything they need to understand what's being flagged.

From there, the fix path in this demo uses VS Code with GitHub Copilot Agent Mode connected to the same Elastic MCP server. The developer types: "I got a PR comment saying this matches a trace pattern from 6 weeks ago. Pull those traces and help me understand the fix." Copilot Agent Mode calls the MCP server, runs the same ES|QL query, returns the same trace data. The developer reviews, confirms, and Copilot applies the fix — restores the atomic guard, writes a regression test.

The MCP server config is committed to the repo in `.vscode/mcp.json`, so every developer on the team gets it automatically:

```json
{
  "servers": {
    "elastic": {
      "type": "http",
      "url": "https://${input:kibanaUrl}/api/agent_builder/mcp",
      "headers": {
        "Authorization": "ApiKey ${input:elasticApiKey}"
      }
    }
  },
  "inputs": [
    { "id": "kibanaUrl", "description": "Kibana URL (no trailing slash)", "type": "promptString" },
    { "id": "elasticApiKey", "description": "Elastic API Key", "type": "promptString", "password": true }
  ]
}
```

VS Code prompts for the Kibana URL and API key on first use and caches them securely. Note: MCP in VS Code requires VS Code 1.99+ and GitHub Copilot with Agent Mode enabled (Copilot for Business/Enterprise). The `.vscode/mcp.json` file is silently ignored if those prerequisites aren't met — verify by checking for the tool picker in Copilot chat. Mention GitHub and Copilot here because that's what the demo uses, but this step is fully portable: any MCP-aware client (Claude Desktop, Cursor, or a custom tool) can connect to the same server and run the same queries.

---

## What made the detection work

The bot comment named "TOCTOU" and "non-atomic read-modify-write." The diff never used those words. The developer who wrote the PR didn't describe it as a race condition. How did the agent get there?

### Pattern matching, not keyword matching

Worth addressing the obvious objection: did the agent catch this because the Skill hardcoded TOCTOU? Yes — and that's exactly the point.

The Skill didn't exist before the incident. Writing it was part of the RCA process: the team experienced a specific failure pattern in production, documented it in the postmortem, and encoded it as a Skill so the same pattern would be flagged in code review going forward. A general model may have broad awareness of TOCTOU as a class of bug, but an explicit Skill is more reliable — it describes the pattern in your terms, applied to your code structure, and it's attached to every agent on your team from that point forward. The Skill is the RCA's lasting artifact. The incident turns into institutional memory that doesn't walk out the door when the engineer who worked it does.

That's the workflow this pattern enables: incidents feed into Skills, Skills prevent recurrence.

The Skill told the agent what a TOCTOU race looks like structurally: a separated read-and-conditional-write where a single atomic read-modify-write previously existed. When the agent read the diff, it matched the structural description — a `WHERE quantity >= N` guard removed, with the read and write now on separate lines — to that pattern. The Skill directed the model's attention to the structural pattern. The model's reasoning performed the semantic match — the Skill shapes what to look for, the model decides if it's present.

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

The trace ID is real — you can click it and see the raw span. The issue number is real. ES|QL either returns rows or returns nothing — the agent cannot fabricate a span ID or duration that isn't in the index. The causal interpretation of those spans is still agent-generated; treat the flag as a starting point for investigation, not a guaranteed finding. This is why retrieval-grounded review is more trustworthy than model knowledge alone: the evidence is auditable.

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

Start with OTel traces. They're the highest-signal source — actual runtime behavior under concurrency, with microsecond timestamps and causal relationships between spans. You're likely collecting them already if you run any APM tooling. Note: surfacing the concurrent read collision requires instrumentation at the DB or business-logic level, not just the HTTP boundary. If your spans only capture endpoint duration, the causal chain won't be visible — add explicit span attributes for the key field values at read time.

Add postmortems when you have them in indexable form. Even a flat-text export from Confluence is enough to get semantic search working — index with ELSER for semantic retrieval, chunking at ~500 tokens with 50-token overlap works well for typical postmortem length. On-call runbooks and resolved GitHub issues are useful too — runbooks often describe known failure modes, and resolved issues trace bugs forward and backward through your codebase's history.

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
- It will flag false positives. Slow spans from unrelated causes can match the duration filter, and diff patterns that structurally resemble a separated read-modify-write are sometimes intentional. The real levers are the ES|QL duration cutoff and how precisely your Skill describes the pattern. Engineers read the comment; they don't merge on it.

Code awareness is table stakes. Telemetry + postmortems is the unlock. But the reviewer is still a reviewer, not an authority.

---

## Getting started

What you actually need to build this:

1. **OTel traces in a queryable store.** Elasticsearch is one option; any APM backend that exposes a query API works. Start with the last 60 days of traces for your highest-traffic endpoints.

2. **Postmortems in indexed text form.** Confluence export, PagerDuty postmortem PDFs, GitHub issues — anything that can be chunked and vector-indexed alongside keyword search. Even 10-15 documents is enough to validate the pattern.

3. **A tool-using agent.** Elastic Agent Builder is what the demo uses, but LangChain, LlamaIndex, or any framework that supports tools and system prompts works here. The agent needs two tools: one to query traces, one to search postmortems.

4. **A PR trigger.** GitHub Action, GitLab CI, Bitbucket pipe — anything that fires on `pull_request: [opened]` and can POST to an HTTP endpoint. The action itself can be 10 lines.

The fastest path to a working prototype: skip postmortems initially. Start with OTel traces only. Write one ES|QL query that fetches recent spans for your highest-risk endpoint. Write one Skill that describes your most common incident pattern. Wire the GitHub Action. Run it against a test PR. Iterate from there as you accumulate more incident data.

An Instruqt lab walking through the full setup hands-on is in progress.

---

## Three things to take away

Your team already did the hard work. The incident happened. The postmortem was written. The traces are stored. The only thing missing is a path from those artifacts to the next PR that would repeat the mistake.

**Code awareness is table stakes. Telemetry + postmortems is the unlock.** A reviewer that only reads the diff is working with half the picture. The other half — what actually broke prod, under what conditions, with what causal signature — is in your telemetry. Wire it in.

**OTel traces are underutilized AI grounding data.** You're collecting them already. The fingerprint of every past incident is in there: concurrent spans, anomalous durations, colliding writes. Querying them at PR time turns telemetry from a post-incident tool into a pre-incident signal.

**Skills encode expertise once, apply everywhere.** Write the TOCTOU skill once. Attach it to every agent on your team that reviews PRs, analyzes incident tickets, or audits design docs. The institutional knowledge that lives in an engineer's head after an incident can be written down, shared as a Skill, and applied to every review from that point forward.

The institutional memory was always there. Now it has a path into the loop.
