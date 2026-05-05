# Session Bucket 2 — GitHub Infrastructure
## MS Build 2026 Demo

### Status: COMPLETE — 2026-04-17

| Task | Status | Notes |
|------|--------|-------|
| GitHub Action | ✅ Done | `.github/workflows/elastic-agent-review.yml` on `feature/msft-build-2026` |
| GitHub Issues | ✅ Done | #5 incident, #6 post-mortem (closes #5), #7 load test follow-up |
| Secrets Docs | ✅ Done | `docs/github-action-secrets.md` — covers key format, where to get both secrets |

**Pending before demo:** Configure `ELASTIC_WORKFLOW_KEY` and `ELASTIC_WORKFLOW_URL` repo secrets in GitHub → Settings → Secrets and variables → Actions.

---

### Context
Wayfinder Supply Co is an Elastic + GitHub demo app (fictional outdoor retailer).
This session sets up the GitHub-side infrastructure for the demo:
- A GitHub Action that fires when a PR is opened and triggers an Elastic Workflow
- 2-3 GitHub Issues in the Wayfinder repo that serve as historical incident postmortems
  (these get ingested into Elasticsearch via the Elastic GitHub Connector — the Agent searches ES, not GitHub directly)

**Repo**: `jeffvestal/wayfinder_supply_co` on GitHub (or check `git remote -v`)
**Branch for file commits**: `feature/msft-build-2026`

---

### Task 1 — GitHub Action

**File to create**: `.github/workflows/elastic-agent-review.yml`

```yaml
name: Elastic Agent PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  trigger-elastic-review:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Elastic Workflow
        run: |
          curl -X POST \
            -H "Authorization: ApiKey ${{ secrets.ELASTIC_WORKFLOW_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "pr_number": "${{ github.event.pull_request.number }}",
              "pr_title": "${{ github.event.pull_request.title }}",
              "repo": "${{ github.repository }}",
              "diff_url": "${{ github.event.pull_request.diff_url }}",
              "head_sha": "${{ github.event.pull_request.head.sha }}"
            }' \
            ${{ secrets.ELASTIC_WORKFLOW_URL }}
```

Notes:
- Uses `pull_request` (not `pull_request_target`) — secrets unavailable for first-time external contributor PRs, fine for demo (internal PRs only)
- Secrets needed in repo settings: `ELASTIC_WORKFLOW_KEY`, `ELASTIC_WORKFLOW_URL`
- Add a `docs/github-action-secrets.md` file describing what each secret is and how to obtain them (so Jeff can fill them in without digging through the build plan)

---

### Task 2 — GitHub Issues (Postmortems)

Create these issues in the Wayfinder GitHub repo via the `gh` CLI. These are the "institutional memory" the Elastic agent searches.

**Issue 1: Incident Report**
```
Title: [INCIDENT] inventory-service: checkout degradation 2026-03-06 14:00-17:30 UTC
Labels: incident, postmortem, p1
Body:
## Summary
~23% of checkout requests returned HTTP 504 during a 3.5-hour window.

## Root Cause
The `inventory.reserve()` function used a read-then-write pattern without transaction isolation.
Under concurrent load (>50 rps), two requests would both read the same available quantity,
both consider the reservation valid, and both write — resulting in overselling and PostgreSQL
lock contention on the inventory row.

## Timeline
- 14:00 UTC: p99 latency on /api/v1/checkout/reserve begins climbing
- 14:22 UTC: Elastic Observability alert fires (p99 > 2000ms)
- 15:40 UTC: Root cause identified via OTel trace span attributes
- 17:30 UTC: Fix deployed (SELECT FOR UPDATE pattern)

## Detection
Elastic Observability (OTel) alerted on p99 > 2000ms for `inventory.reserve` spans on `/api/v1/checkout/reserve`.
Trace span attributes showed `db.lock.timeout` events firing at ~3800ms across concurrent requests.

## Fix
Rewrote reservation to use `SELECT FOR UPDATE` (pessimistic locking).
Single atomic transaction: lock row → check quantity → write reservation.

## Metrics at Peak
- p99 latency: 6.2s
- Error rate: 23%
- Lock contention events: 847 in 3.5hr window

## Prevention
Added load test to CI covering 100 concurrent reservation requests.
```

**Issue 2: Post-Incident Review**
```
Title: [POST-MORTEM] inventory.reserve race condition — lessons learned 2026-03-06
Labels: postmortem, engineering
Body:
## What Broke
The `inventory.reserve()` function used a read-modify-write pattern split across two separate
database calls without transaction isolation. This is safe under single-threaded load but
produces a classic race condition when two requests execute concurrently:

Request A reads quantity=5 (available)
Request B reads quantity=5 (available)
Request A writes reservation, quantity becomes 4
Request B writes reservation, quantity becomes 3 — but it already sold to A

Under high concurrency, PostgreSQL detects the conflicting row locks and raises a deadlock error.

## Why It Wasn't Caught
Unit tests cover the single-request path only. Concurrency failures require load testing
at >50 rps to manifest reliably.

## Pattern to Avoid
```python
# WRONG — non-atomic read-modify-write
quantity = db.query("SELECT quantity FROM inventory WHERE product_id = ?", product_id)
if quantity >= requested:
    db.execute("UPDATE inventory SET quantity = quantity - ? WHERE product_id = ?", requested, product_id)
```

## Pattern to Use
```python
# CORRECT — atomic with pessimistic lock
with db.transaction():
    row = db.query("SELECT quantity FROM inventory WHERE product_id = ? FOR UPDATE", product_id)
    if row.quantity >= requested:
        db.execute("UPDATE inventory SET quantity = quantity - ? WHERE product_id = ?", requested, product_id)
```

## Detection Gap
Semantic alerting on span attribute patterns (e.g. `db.lock.timeout` events + p99 spike
on the same endpoint) would have caught this at 5 concurrent requests rather than 50.
Elastic Observability has this capability — it was not configured on this endpoint.

Closes #[Issue 1 number]
```

**Issue 3 (optional): Load test gap**
```
Title: Add concurrency load test for inventory.reserve endpoint
Labels: engineering, testing
Body:
Follow-up from the 2026-03-06 incident (#[Issue 1 number]).
Current CI has no test that exercises inventory.reserve under concurrent load.
Need a load test at >50 rps for at least 30 seconds to catch the read-modify-write race condition.
```

Create issues in this order (Issue 1 first, then Issue 2 referencing Issue 1's number).

---

### Task 3 — Secrets Documentation

Create `docs/github-action-secrets.md`:
- `ELASTIC_WORKFLOW_KEY`: ApiKey credential for authenticating to the Elastic Workflow HTTP trigger endpoint. Format: `ApiKey <base64-encoded-id:api_key>`. Obtain from Kibana → Stack Management → API Keys.
- `ELASTIC_WORKFLOW_URL`: Full HTTPS URL of the Elastic Workflow HTTP trigger endpoint. Obtain from the Workflow configuration in Kibana → Workflows.

---

### Full Build Plan Reference
`/Users/jeffvestal/repos/kuchi-kopi/drafts/msft-build-2026-build-plan-v1.md` — Phases 1C and 2A, components [3] and [4]
