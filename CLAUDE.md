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

## Demo Scripts (for live delivery)

`demo_scripts/field/` — pick by time and audience:
- `micro_1min.md` — 1-min teaser
- `short_5min_ui_focus.md` / `short_5min_backend_focus.md` — 5-min variants
- `builder_15min.md` — 15-min deep dive (dev/architect audience)
- `google-next-lightning-talk.md` — conference format

## Commit Convention

No strong convention observed — use descriptive messages.
