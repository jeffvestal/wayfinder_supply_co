# Wayfinder Supply Co.

Elastic + Google Better Together demo. Fictional outdoor retailer with AI-powered trip planner, image analysis (Jina VLM), real-time weather grounding (Gemini + Google Search), and product visualization (Imagen 3). Showcases Elastic Agentic Search.

**Owner:** Jeff Vestal · **Status:** Stable v1.1

## Architecture

- **Backend:** Python (FastAPI) in `backend/`
- **Frontend:** Served by backend on port 8000
- **MCP Server:** `mcp_server/` — exposes CRM tools (customer profiles, trip safety, ground conditions) to Elastic Agent Builder workflows
- **Elasticsearch:** Elastic Cloud cluster (not local). Local dev uses ngrok tunnels so Cloud-side workflows can reach the local MCP/backend.
- **GCP Cloud Run:** Production/demo deployment path — separate from local dev

## Two Deployment Modes

### Local Dev (with ngrok)
Elastic workflows live in Elastic Cloud. Local services need ngrok tunnels so the Cloud can call back to them.

```bash
# First run (loads data + starts everything including tunnels):
./scripts/start_local.sh --load-data

# Subsequent runs:
./scripts/start_local.sh
```

Without tunnels, tools like `check_trip_safety`, `get_customer_profile`, and `ground_conditions` will fail.

### GCP Cloud Run (production demo)
See `docs/DEPLOYMENT.md` for full Cloud Run deploy steps. Use `gcp-microsite-deploy` skill if deploying a static variant.

## Key Directories

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI app, agents, search logic |
| `mcp_server/` | MCP server exposing CRM tools to Agent Builder |
| `frontend/` | UI served by backend |
| `scripts/` | Setup, seeding, workflow deploy, start scripts |
| `config/` | Workflow configs, product generation config |
| `generated_products/` | Output from data generation scripts |
| `demo_scripts/field/` | Talk tracks for live demos (1min, 5min, 15min variants) |
| `docs/` | Architecture, deployment, API reference, workshop guide |
| `instruqt/` | Instruqt workshop challenge configs |

## Common Tasks

```bash
make setup       # Install dependencies
make generate    # Generate product data
make seed        # Seed Elasticsearch
make deploy      # Deploy workflows + create agents
make dev         # Start all services (dev mode)
make validate    # Validate setup
```

## Active Demo Work — MS Build 2026

**Branch:** `feature/msft-build-2026`

**What it is:** Click-through Navattic demo for MS Build 2026 showcasing Elastic Agent Builder doing automated PR security review (detects TOCTOU race condition, cites OTel trace evidence, posts GitHub bot comment).

**Key files:**
- `demo_scripts/field/navattic-shot-sheet.md` — **the shot sheet** — 8 scenes, ~30 Navattic steps, complete hotspot copy. This is the primary recording reference.
- `demo_scripts/field/msbuild_recording_guide.md` — full narrative/talk track behind the shot sheet
- `control.sh` — single demo control script: `setup`, `stage`, `reset`
- `scripts/msbuild_harness.py` — concurrency harness for Scene 7

**Flow summary:** PR opens → GitHub Action → Elastic Workflow → Agent Builder (ES|QL tools + Skills) → bot comment with TOCTOU diagnosis → VS Code Copilot fix via MCP → harness confirms atomic behavior.

## Demo Scripts (for live delivery)

`demo_scripts/field/` — pick by time and audience:
- `micro_1min.md` — 1-min teaser
- `short_5min_ui_focus.md` / `short_5min_backend_focus.md` — 5-min variants
- `builder_15min.md` — 15-min deep dive (dev/architect audience)
- `google-next-lightning-talk.md` — conference format

## Commit Convention

No strong convention observed — use descriptive messages.
