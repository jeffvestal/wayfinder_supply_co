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

Full build plan: `/Users/jeffvestal/repos/kuchi-kopi/drafts/msft-build-2026-build-plan-v1.md`
