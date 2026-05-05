# Session Bucket 3 — Synthetic OTel Trace Data
## MS Build 2026 Demo

### Status: COMPLETE — 2026-04-17

| Task | Status | Notes |
|------|--------|-------|
| Baseline trace generator | ✅ Done | `scripts/generate_baseline_traces.py` — 50k traces, 250k docs |
| Incident trace generator | ✅ Done | `scripts/generate_incident_traces.py` — 750 traces, 3,750 docs |
| Index script | ✅ Done | `scripts/index_traces.py` → `traces-apm.wayfinder-default` |
| Validation script | ✅ Done | `scripts/validate_traces.py` — 7-check suite |
| ES\|QL smoke tests | ✅ Done | `scripts/verify_esql_search.py` — both queries PASS |
| Backend router | ✅ Reverted | `backend/routers/observability.py` deleted — not needed |
| Agent Builder wire-up | ✅ Done | `scripts/add_otel_agent_tool.py` — fully repeatable idempotent script |
| Data indexed | ✅ Done | 253,750 docs in `traces-apm.wayfinder-default`, 0 errors |
| Tool wired to agent | ✅ Done | `tool-mcp-o11y-incident-analysis` on `trip-planner-agent` |

**Trigger the demo**: ask Trip Planner *"why is checkout so slow on April 7?"*

**To reset for demo**: `python3 scripts/add_otel_agent_tool.py` (re-creates connector + tool + wires agent)

**To re-index from scratch**: `python3 scripts/generate_baseline_traces.py && python3 scripts/generate_incident_traces.py && python3 scripts/index_traces.py --recreate generated_traces/baseline_traces.jsonl generated_traces/incident_traces.jsonl`

---

### Architecture (final)

```
Trip Planner Agent (Search project)
  → tool-mcp-o11y-incident-analysis  [type: mcp]
    → .mcp Kibana connector (O11y MCP Server)
      → O11y Kibana /api/agent_builder/mcp
        → platform_core_execute_esql
          → traces-apm.wayfinder-default (253,750 docs)
```

**Key fields added vs original design:**
- `processor.event`: `"transaction"` (root spans) / `"span"` (children)
- `event.duration`: nanoseconds (span.duration.us × 1000)
- `db.statement_semantic`: semantic_text — kept for semantic search demo beat

**ES|QL demo queries (both verified working):**
```esql
-- Slow checkout detection
FROM traces-apm.wayfinder-default
| WHERE http.route == "/api/v1/checkout/reserve"
  AND event.duration > 3000000000
  AND @timestamp >= "2026-04-07T00:00:00Z"
| SORT @timestamp DESC | LIMIT 10

-- Deadlock detection (semantic)
FROM traces-apm.wayfinder-default
| WHERE MATCH(db.statement, "lock deadlock concurrent")
| SORT @timestamp DESC | LIMIT 5
```

---

### Context
Wayfinder Supply Co is an Elastic + GitHub demo app (fictional outdoor retailer).
This session generates synthetic OpenTelemetry trace data and indexes it into Elasticsearch.

The demo needs two datasets in ES:
1. **Baseline traces** — 2-4 weeks of healthy `inventory.reserve` spans before the incident
2. **Incident traces** — a 3.5-hour window ~42 days before the demo showing p99 spikes + lock errors

The agent will query this data with ES|QL to find the historical pattern that matches the demo PR.

**Demo date**: MS Build 2026 — assume `2026-05-19` as DEMO_DATE. Pin all timestamps to `DEMO_DATE - N days`.
**Incident window**: `DEMO_DATE - 42 days` = `2026-04-07` 14:00–17:30 UTC

---

### Trace Structure

The trace path is: `frontend → checkout-service → inventory-service → postgres`

Key span: `inventory.reserve` (in inventory-service)
- `http.route`: `/api/v1/checkout/reserve`
- `inventory.quantity_requested`: integer (1-5)
- `inventory.quantity_available`: integer (varies)
- `db.statement`: SQL string (SELECT + UPDATE)
- Child spans: `db.query` (SELECT) and `db.write` (UPDATE/INSERT)

---

### Task 1 — Baseline Trace Generator Script

**File to create**: `scripts/generate_baseline_traces.py`

Uses Gemini CLI (via subprocess) or generates traces directly in Python.

Requirements:
- Timestamps: Unix nanoseconds, covering `2026-04-07 - 30d` to `2026-04-06` (day before incident)
- `inventory.reserve` span: avg 45ms, p99 < 200ms, ±15% jitter — **no round numbers**
- Load pattern: daytime peaks 9am–6pm PT, low nights/weekends
- Vary attributes realistically per trace (quantity values, SQL vary slightly)
- Output format: OTLP JSON (array of `ResourceSpans`) OR Elasticsearch bulk API format
- Generate in batches, aim for 500–1000 total traces
- Include 2-3 child spans per service hop

Validate output:
- Check traceId/spanId are unique across all traces
- Check timestamp range is correct
- Check p99 < 200ms
- Check jitter is present (no two identical duration values)

**File to create**: `scripts/index_traces.py`

Indexes generated trace JSON into Elasticsearch.
- Read ES connection from environment: `ELASTIC_URL`, `ELASTIC_API_KEY`
- Target index: `otel-traces-wayfinder` (or `traces-apm-*` if using OTLP endpoint)
- Use ES bulk API
- Print count of indexed docs on success

---

### Task 2 — Incident Trace Generator Script

**File to create**: `scripts/generate_incident_traces.py`

Requirements:
- Timestamps: `2026-04-07` 14:00–17:30 UTC (Unix nanoseconds)
- `inventory.reserve` span: 4000ms–6500ms, ±500ms jitter — **no round numbers, no identical values**
- `db.statement` attribute must include PostgreSQL deadlock/lock error text:
  `ERROR: deadlock detected, Process 12847 waits for ShareLock on transaction 9234`
  (vary the process/transaction numbers per trace)
- Deep parent-child span nesting showing cascading timeouts
- Root frontend span returns HTTP 504
- Span events:
  - `db.lock.acquired` — should NOT appear (lock was never acquired)
  - `db.lock.timeout` — fires at ~3800ms (vary exact ms per trace)
- Generate 50–100 traces for the window

Reuse `scripts/index_traces.py` for indexing.

---

### Task 3 — Validation Script

**File to create**: `scripts/validate_traces.py`

Checks:
- All traceIds are unique
- All spanIds are unique
- Baseline timestamps fall within expected range
- Incident timestamps fall within `2026-04-07` 14:00–17:30 UTC
- Baseline p99 < 200ms
- Incident durations are 4000–7000ms range
- Jitter present: no two `inventory.reserve` spans have identical duration
- Prints a summary report

---

### Task 4 — ES|QL Smoke Test Script

**File to create**: `scripts/verify_esql_search.py`

After indexing, run two ES|QL queries and verify they return expected results:

**Query 1** (should return incident traces):
```esql
FROM otel-traces-wayfinder
| WHERE http.route == "/api/v1/checkout/reserve"
  AND span.duration.us > 3000000
  AND @timestamp >= "2026-04-07T00:00:00Z"
  AND @timestamp <= "2026-04-08T00:00:00Z"
| SORT @timestamp DESC
| LIMIT 10
```

**Query 2** (semantic match — agent will use this pattern):
```esql
FROM otel-traces-wayfinder
| WHERE MATCH(db.statement, "lock deadlock concurrent")
| SORT _score DESC
| LIMIT 5
```

Print result counts. Both should return > 0 rows.

---

### Important: Timestamp Pinning

**Do NOT use `NOW() - 42d` in generated data.** Pin to absolute timestamps based on `DEMO_DATE = 2026-05-19`.

If the demo date slips, re-run the generators with the updated date and re-index. The scripts should accept `DEMO_DATE` as an environment variable or CLI argument.

---

### Full Build Plan Reference
`/Users/jeffvestal/repos/kuchi-kopi/drafts/msft-build-2026-build-plan-v1.md` — Phase 1B, component [2]

### ES Connection
Scripts should read from env:
- `ELASTIC_URL` — e.g. `https://my-deployment.es.us-central1.gcp.cloud.es.io`
- `ELASTIC_API_KEY` — Base64 encoded `id:api_key`
