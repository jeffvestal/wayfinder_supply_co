# MS Build 2026 — Branch Setup Plan

## Goal
Create `feature/msft-build-2026` off `feature/jina-vlm-vision`, remove Imagen 3 / Visualize, verify app runs.

## Step 1 — Create Branch
```bash
git checkout feature/jina-vlm-vision
git checkout -b feature/msft-build-2026
```

## Step 2 — Remove Imagen 3 / Visualize

### Delete entire file
- `frontend/src/components/VisionPreview.tsx` — delete file

### frontend/src/components/TripPlanner.tsx
- Line 13: remove `import { VisionPreview } from './VisionPreview'`
- Lines 1360-1377: remove VisionPreview conditional render block

### frontend/src/lib/api.ts
- Lines 616-641: remove `generatePreview()` function

### frontend/src/types/index.ts
- Line 51: remove `generated_preview?: string;`

### frontend/src/components/SettingsPage.tsx
- Lines 193-195: remove Imagen 3 status display
- Line 280: remove "Vertex AI / Imagen 3" section header
- Line 342: remove Cloud AI Platform API doc link

### backend/routers/vision.py
- Lines 31-44: remove `PreviewRequest` and `PreviewResponse` models
- Lines 111-137: remove `@router.post("/vision/preview")` endpoint

### backend/services/vision_service.py
- Lines 346-540: remove `generate_preview()` function only
  - Keep: `analyze_image()`, `analyze_image_structured()`, `ground_conditions()`

## Step 3 — Verify
- `cd backend && python -m py_compile routers/vision.py services/vision_service.py`
- `cd frontend && npm run build` (or type-check)
- Start dev server, confirm image upload / Jina VLM analysis still works, Visualize button is gone

## What Stays (must not touch)
| Endpoint | Used By |
|---|---|
| `/vision/warm` | warmup |
| `/vision/preanalyze` | chat.py, products.py |
| `/vision/analyze` | chat.py, products.py |
| `/vision/ground` | weather grounding |
| `analyze_image()` | chat, products, trip planner |
| `analyze_image_structured()` | chat, products |
| `ground_conditions()` | weather |

## Next Steps After Removal (Phase 1)
- [ ] Add `inventory.reserve()` service (OTel instrumented)
- [ ] Add `.github/workflows/elastic-agent-review.yml`
- [ ] Add `.vscode/mcp.json`
- [ ] Create GitHub Issues (postmortems) in repo
- [ ] Create hand-crafted "demo PR" with subtle non-atomic read-modify-write bug

## Demo Reset / Repeatability

**Goal:** Run the demo multiple times for testing and practice.

### What needs resetting between runs
| State | Reset method |
|---|---|
| GitHub PR + agent review comment | Delete PR, create fresh one |
| In-memory inventory stock | Restart backend container |
| In-memory cart state | Restart backend container (same restart) |
| Elasticsearch (both clusters) | **No reset needed** — read-only during demo |

### Scripts (added to `feature/msft-build-2026`)
- `scripts/demo_reset.sh` — main reset script (also serves as first-run start)
- `scripts/_demo_pr_body.md` — innocent-sounding PR body (no race/deadlock keywords)

### Demo run sequence
```bash
# One-time: start services, ngrok, deploy ES workflows
./scripts/start_local.sh

# Before EACH run (first or reset):
./scripts/demo_reset.sh
# → closes existing PR → restarts backend → creates fresh PR
# → polls until GitHub Action triggers
# → prints 3 browser tab URLs: PR, Action run, app
```

### Testing checklist
- [ ] Run `demo_reset.sh` twice — second run closes first PR cleanly, no errors
- [ ] Backend health returns 200 after restart
- [ ] New PR created at `demo/inventory-refactor → feature/msft-build-2026`
- [ ] GitHub Action run appears within ~30s
- [ ] Elastic Agent posts review comment (~30-60s after action starts)
- [ ] Oversell bug confirmed: two concurrent `/reserve` requests both return `"reserved": true`

Full build plan: `/Users/jeffvestal/repos/kuchi-kopi/drafts/msft-build-2026-build-plan-v1.md`
