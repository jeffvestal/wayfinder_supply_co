# Session Bucket 1 — Wayfinder App Code
## MS Build 2026 Demo

---
## ✅ COMPLETE — 2026-04-17

| Task | Status | Notes |
|------|--------|-------|
| Task 1: inventory.reserve() + OTel | Done | `backend/services/inventory_service.py`, `backend/services/telemetry.py`, `backend/routers/inventory.py`; 4 OTel packages; FastAPIInstrumentor wired in `main.py` |
| Task 2: .vscode/mcp.json | Done | `.gitignore` updated with `!.vscode/mcp.json` exception |
| Task 3: Demo PR branch | Done | `demo/inventory-refactor` pushed to GitHub; `drafts/demo-pr-script.md` has presenter notes + concurrency proof |

**Remaining unstaged changes** (pre-existing vision/settings work from prior sessions — not part of this bucket):
`backend/routers/settings.py`, `backend/routers/vision.py`, `backend/services/credential_manager.py`, `backend/services/vision_service.py`, frontend files — commit separately when ready.

---

### Context
Wayfinder Supply Co is an Elastic + Google/GitHub demo app (fictional outdoor retailer). This session adds
the `inventory.reserve()` code path that will be the subject of the demo's PR review agent scenario.

**Branch**: `feature/msft-build-2026` (off `feature/jina-vlm-vision`)
**Repo**: `/Users/jeffvestal/repos/wayfinder_supply_co`
**Backend**: Python / FastAPI in `backend/`

### What the Demo Needs
A developer opens a PR that introduces a subtle non-atomic read-modify-write bug in `inventory.reserve()`.
An Elastic agent reviews the PR, finds a matching historical incident in Elasticsearch, and posts a PR comment.
The code path must be:
- Realistic and OTel-instrumented (spans visible in Elastic Observability)
- The bug must NOT mention "deadlock" or the failure mode anywhere in the diff (semantic matching must do the work)

---

### Task 1 — Add `inventory.reserve()` service

**File to create**: `backend/services/inventory_service.py`

Implement a reservation service that:
- Checks available stock (simulated DB query)
- Reserves quantity (simulated DB write)
- Instruments with OpenTelemetry spans:
  - Parent span: `inventory.reserve` with attributes `inventory.quantity_requested`, `inventory.quantity_available`, `http.route = /api/v1/checkout/reserve`
  - Child span: `db.query` with attribute `db.statement` (SELECT query string)
  - Child span: `db.write` with attribute `db.statement` (UPDATE/INSERT string)
- Should be Cloud Run compatible (no local-only dependencies)
- Use the OTel setup already present in the backend (check `backend/main.py` and existing services for the pattern)

**File to create/extend**: `backend/routers/inventory.py`
- `POST /api/v1/checkout/reserve` endpoint
- Request body: `{ product_id, quantity, user_id }`
- Response: `{ reserved: bool, quantity_available: int, reservation_id: str }`

**Wire into**: `backend/main.py` — include the new router

---

### Task 2 — Add `.vscode/mcp.json`

**File to create**: `.vscode/mcp.json`

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

---

### Task 3 — Craft the Demo PR

**Goal**: A hand-crafted git commit on a short-lived branch `demo/inventory-refactor` that introduces the subtle bug.

The commit should:
- Modify `inventory.reserve()` to change from a single atomic DB write to a non-atomic read-then-write
- Look like a natural "performance refactor" (e.g., "split query for better cache hit rate")
- The diff must NOT contain: "deadlock", "race condition", "concurrent", "lock contention", "atomic"
- The OTel span attributes stay the same — the bug is in the logic, not the instrumentation

This branch should be pushed to GitHub (not merged) so the demo GitHub Action can be triggered against it.

Document the exact commit message and PR title to use in `drafts/demo-pr-script.md`.

---

### Full Build Plan Reference
`/Users/jeffvestal/repos/kuchi-kopi/drafts/msft-build-2026-build-plan-v1.md` — Phases 1A and component [1] and [8]

### Do Not Touch
- Jina VLM / vision analysis (already in this branch, keep it)
- Gemini grounding / weather (keep it)
- Imagen 3 / Visualize (already removed from this branch — do not re-add)
