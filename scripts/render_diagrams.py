#!/usr/bin/env python3
"""Generate Excalidraw architecture diagrams and render to SVG via kroki.io

All diagrams use a dark background (#1e1e2e) with color-coded zones:
  Blue   (#4a9eed / #1e3a5f) — Frontend
  Purple (#8b5cf6 / #2d1b69) — Backend
  Green  (#22c55e / #1a4d2e) — Elastic Stack
  Orange (#f59e0b / #5c3d1a) — Google Cloud (Vertex AI)
  Yellow (#facc15 / #4d4510) — Jina AI (external, jina.ai)
  Teal   (#06b6d4 / #1a4d4d) — MCP Server
  Pink   (#ec4899)           — Auth credentials
  Red    (#ef4444 / #5c1a1a) — Fallback / Error
"""

import json
import random
import requests
import os

random.seed(42)

# ── Dark-mode palette ────────────────────────────────────────────────

BG       = "#1e1e2e"
TEXT     = "#e5e5e5"
MUTED    = "#a0a0a0"
SUBTLE   = "#555555"

BLUE_S   = "#4a9eed";  BLUE_F   = "#1e3a5f"
PURPLE_S = "#8b5cf6";  PURPLE_F = "#2d1b69"
GREEN_S  = "#22c55e";   GREEN_F  = "#1a4d2e"
ORANGE_S = "#f59e0b";  ORANGE_F = "#5c3d1a"
YELLOW_S = "#facc15";  YELLOW_F = "#4d4510"   # Jina AI
TEAL_S   = "#06b6d4";  TEAL_F   = "#1a4d4d"
PINK     = "#ec4899"
RED_S    = "#ef4444";   RED_F    = "#5c1a1a"


def seed():
    return random.randint(1, 2**31)


# ── Primitive helpers ────────────────────────────────────────────────

def rect(id, x, y, w, h, bg="transparent", stroke="#1e1e1e", sw=2,
         opacity=100, rounded=True, style="solid"):
    return {
        "type": "rectangle", "id": id, "x": x, "y": y, "width": w, "height": h,
        "angle": 0, "strokeColor": stroke, "backgroundColor": bg,
        "fillStyle": "solid", "strokeWidth": sw, "strokeStyle": style,
        "roughness": 1, "opacity": opacity, "groupIds": [], "frameId": None,
        "roundness": {"type": 3} if rounded else None,
        "seed": seed(), "version": 1, "versionNonce": seed(),
        "isDeleted": False, "boundElements": [], "updated": 1,
        "link": None, "locked": False,
    }


def text_el(id, x, y, txt, size=16, color=TEXT, container_id=None):
    lines = txt.split("\n")
    max_line = max(lines, key=len)
    return {
        "type": "text", "id": id, "x": x, "y": y,
        "width": len(max_line) * size * 0.55,
        "height": size * 1.4 * len(lines),
        "angle": 0, "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": None, "seed": seed(), "version": 1, "versionNonce": seed(),
        "isDeleted": False, "boundElements": None, "updated": 1,
        "link": None, "locked": False,
        "text": txt, "fontSize": size, "fontFamily": 1,
        "textAlign": "center", "verticalAlign": "middle",
        "containerId": container_id, "originalText": txt, "autoResize": True,
    }


def standalone_text(id, x, y, txt, size=16, color=TEXT):
    t = text_el(id, x, y, txt, size, color, container_id=None)
    t["textAlign"] = "left"
    t["verticalAlign"] = "top"
    return t


def labeled_rect(id, x, y, w, h, label, bg="transparent", stroke="#1e1e1e",
                 sw=2, opacity=100, rounded=True, font_size=16, font_color=TEXT):
    r = rect(id, x, y, w, h, bg, stroke, sw, opacity, rounded)
    tid = f"{id}_t"
    lines = label.split("\n")
    text_h = font_size * 1.4 * len(lines)
    t = text_el(tid, x + 10, y + h / 2 - text_h / 2,
                label, font_size, font_color, container_id=id)
    r["boundElements"] = [{"id": tid, "type": "text"}]
    return [r, t]


def arrow_el(id, x, y, pts, stroke=TEXT, sw=2, style="solid", end_head="arrow"):
    return {
        "type": "arrow", "id": id, "x": x, "y": y,
        "width": abs(pts[-1][0] - pts[0][0]),
        "height": abs(pts[-1][1] - pts[0][1]),
        "angle": 0, "strokeColor": stroke, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": sw, "strokeStyle": style,
        "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": {"type": 2},
        "seed": seed(), "version": 1, "versionNonce": seed(),
        "isDeleted": False, "boundElements": [], "updated": 1,
        "link": None, "locked": False,
        "points": pts, "endArrowhead": end_head, "startArrowhead": None,
        "startBinding": None, "endBinding": None,
    }


def labeled_arrow(id, x, y, pts, label, stroke=TEXT, sw=2, style="solid",
                  end_head="arrow", font_size=14, font_color=None):
    a = arrow_el(id, x, y, pts, stroke, sw, style, end_head)
    tid = f"{id}_t"
    mx = x + (pts[0][0] + pts[-1][0]) / 2 - len(label) * font_size * 0.25
    my = y + (pts[0][1] + pts[-1][1]) / 2 - font_size * 1.2
    t = text_el(tid, mx, my, label, font_size, font_color or MUTED, container_id=id)
    a["boundElements"] = [{"id": tid, "type": "text"}]
    return [a, t]


def lifeline(id, x, y_start, length):
    return arrow_el(id, x, y_start, [[0, 0], [0, length]],
                    stroke=SUBTLE, sw=1, style="dashed", end_head=None)


def dark_scene(elements, width=1100, height=650):
    """Wrap elements in a dark-background scene."""
    bg = rect("_bg", -10, -10, width + 20, height + 20,
              bg=BG, stroke="transparent", sw=0, opacity=100, rounded=False)
    return {
        "type": "excalidraw", "version": 2, "source": "wayfinder",
        "elements": [bg] + elements,
        "appState": {"viewBackgroundColor": BG},
    }


# ── Legend helper ────────────────────────────────────────────────────

def legend_row(prefix, y, items):
    """items = [(label, fill, stroke), ...]"""
    els = []
    x = 20
    for i, (label, fill, stroke) in enumerate(items):
        rid = f"{prefix}_l{i}"
        els.append(rect(rid, x, y, 16, 16, bg=fill, stroke=stroke, sw=1, opacity=100, rounded=False))
        els.append(standalone_text(f"{rid}_t", x + 22, y - 1, label, 14, MUTED))
        x += 22 + len(label) * 14 * 0.55 + 20
    return els


# =====================================================================
# Diagram 1 — High-Level Architecture
# =====================================================================

def build_high_level():
    els = []
    els.append(standalone_text("title", 220, 8,
        "Wayfinder Supply Co. -- High-Level Architecture", 24, TEXT))

    # Zone backgrounds
    els.append(rect("z_fe", 10, 55, 200, 350, bg=BLUE_F, stroke=BLUE_S, sw=1, opacity=30))
    els.append(standalone_text("z_fe_t", 55, 62, "Frontend", 16, BLUE_S))

    els.append(rect("z_be", 270, 55, 200, 350, bg=PURPLE_F, stroke=PURPLE_S, sw=1, opacity=30))
    els.append(standalone_text("z_be_t", 305, 62, "Backend (FastAPI)", 16, PURPLE_S))

    els.append(rect("z_es", 530, 55, 220, 350, bg=GREEN_F, stroke=GREEN_S, sw=1, opacity=30))
    els.append(standalone_text("z_es_t", 585, 62, "Elastic Stack", 16, GREEN_S))

    # Jina AI zone (separate from Google — runs on jina.ai)
    els.append(rect("z_jina", 810, 55, 220, 70, bg=YELLOW_F, stroke=YELLOW_S, sw=1, opacity=30))
    els.append(standalone_text("z_jina_t", 875, 62, "Jina AI", 16, YELLOW_S))

    # Google Cloud zone (Vertex AI only)
    els.append(rect("z_ext", 810, 135, 220, 140, bg=ORANGE_F, stroke=ORANGE_S, sw=1, opacity=30))
    els.append(standalone_text("z_ext_t", 835, 142, "Google Cloud (Vertex AI)", 16, ORANGE_S))

    els.append(rect("z_mcp", 810, 290, 220, 115, bg=TEAL_F, stroke=TEAL_S, sw=1, opacity=30))
    els.append(standalone_text("z_mcp_t", 870, 297, "MCP Server", 16, TEAL_S))

    # Frontend boxes
    for i, lbl in enumerate(["React / Vite", "Trip Planner", "Search Panel",
                              "Settings Page", "Vision Preview"]):
        y = 90 + i * 58
        els.extend(labeled_rect(f"fe{i}", 30, y, 160, 45, lbl,
                                bg=BLUE_F, stroke=BLUE_S, sw=2, font_size=15))

    # Backend boxes
    for i, lbl in enumerate(["Chat Router", "Vision Router", "Products Router",
                              "Credential Mgr", "API Key Auth"]):
        y = 90 + i * 58
        els.extend(labeled_rect(f"be{i}", 290, y, 160, 45, lbl,
                                bg=PURPLE_F, stroke=PURPLE_S, sw=2, font_size=15))

    # Elastic boxes
    for i, lbl in enumerate(["Elasticsearch 9.x", "Kibana",
                              "Agent Builder", "Workflows", "ELSER (Semantic)"]):
        y = 90 + i * 58
        els.extend(labeled_rect(f"es{i}", 550, y, 180, 45, lbl,
                                bg=GREEN_F, stroke=GREEN_S, sw=2, font_size=15))

    # Jina AI box
    els.extend(labeled_rect("ext_jina", 830, 85, 180, 45, "Jina VLM",
                            bg=YELLOW_F, stroke=YELLOW_S, sw=2, font_size=15))

    # Google Cloud boxes
    for i, lbl in enumerate(["Gemini + Grounding", "Imagen 3"]):
        y = 165 + i * 58
        els.extend(labeled_rect(f"ext{i}", 830, y, 180, 45, lbl,
                                bg=ORANGE_F, stroke=ORANGE_S, sw=2, font_size=15))

    # MCP boxes
    els.extend(labeled_rect("mcp0", 830, 325, 180, 35, "CRM / Persona",
                            bg=TEAL_F, stroke=TEAL_S, sw=2, font_size=15))
    els.extend(labeled_rect("mcp1", 830, 368, 180, 35, "Weather (Mock)",
                            bg=TEAL_F, stroke=TEAL_S, sw=2, font_size=15))

    # Arrows
    els.extend(labeled_arrow("a1", 190, 200, [[0, 0], [80, 0]], "HTTP / SSE",
                             stroke=TEXT, font_color=MUTED))
    els.extend(labeled_arrow("a2", 450, 120, [[0, 0], [100, 0]], "API Key",
                             stroke=TEXT, font_color=MUTED))
    els.extend(labeled_arrow("a3", 450, 235, [[0, 0], [100, 0]], "SSE Proxy",
                             stroke=TEXT, font_color=MUTED))
    # backend -> Jina (dashed, yellow)
    els.append(arrow_el("a4", 450, 155, [[0, 0], [380, -45]], stroke=YELLOW_S, sw=2, style="dashed"))
    # backend -> Google (dashed, orange)
    els.append(arrow_el("a5", 450, 165, [[0, 0], [380, 25]],  stroke=ORANGE_S, sw=2, style="dashed"))
    els.append(arrow_el("a6", 450, 175, [[0, 0], [380, 50]],  stroke=ORANGE_S, sw=2, style="dashed"))
    # workflow callbacks
    els.extend(labeled_arrow("a7", 640, 325, [[0, 0], [-190, -140]],
        "workflow\ncallback", stroke=GREEN_S, style="dashed", font_color=MUTED))
    els.extend(labeled_arrow("a8", 730, 325, [[0, 0], [100, 20]],
        "workflow\ncallback", stroke=GREEN_S, style="dashed", font_color=MUTED))

    # Legend
    els.extend(legend_row("lg", 430, [
        ("Frontend", BLUE_F, BLUE_S),
        ("Backend", PURPLE_F, PURPLE_S),
        ("Elastic", GREEN_F, GREEN_S),
        ("Google Cloud", ORANGE_F, ORANGE_S),
        ("Jina AI", YELLOW_F, YELLOW_S),
        ("MCP", TEAL_F, TEAL_S),
    ]))

    return dark_scene(els, 1060, 470)


# =====================================================================
# Diagram 2 — Elastic + Jina + Google Integration
# =====================================================================

def build_integration():
    els = []
    els.append(standalone_text("title", 150, 8,
        "Elastic + Jina + Google -- Integration Architecture", 24, TEXT))

    # User zone
    els.append(rect("z_u", 10, 55, 170, 165, bg=BLUE_F, stroke=BLUE_S, sw=1, opacity=35))
    els.append(standalone_text("z_u_t", 45, 62, "User Browser", 15, BLUE_S))
    els.extend(labeled_rect("u1", 25, 90, 140, 35, "Trip Planner",
                            bg=BLUE_F, stroke=BLUE_S, font_size=14))
    els.extend(labeled_rect("u2", 25, 135, 140, 35, "Search Panel",
                            bg=BLUE_F, stroke=BLUE_S, font_size=14))
    els.extend(labeled_rect("u3", 25, 180, 140, 35, "Image Upload",
                            bg=BLUE_F, stroke=BLUE_S, font_size=14))

    # Jina zone (jina.ai — separate from Google Cloud)
    els.append(rect("z_j", 240, 50, 200, 175, bg=YELLOW_F, stroke=YELLOW_S, sw=1, opacity=30))
    els.append(standalone_text("z_j_t", 300, 57, "Jina AI", 18, YELLOW_S))
    els.extend(labeled_rect("j1", 260, 85, 160, 50, "VLM (Vision)\nTerrain Analysis",
                            bg=YELLOW_F, stroke=YELLOW_S, font_size=14))
    els.extend(labeled_rect("j2", 260, 145, 160, 50, "VLM (Vision)\nProduct Structured",
                            bg=YELLOW_F, stroke=YELLOW_S, font_size=14))
    els.append(standalone_text("j_note", 265, 200, "JSON: type, category,\nkey_terms, description", 12, MUTED))

    # Elastic zone
    els.append(rect("z_el", 500, 50, 250, 320, bg=GREEN_F, stroke=GREEN_S, sw=1, opacity=30))
    els.append(standalone_text("z_el_t", 540, 57, "Elastic (Orchestrator)", 18, GREEN_S))
    for i, lbl in enumerate(["Agent Builder\nTrip Planner Agent",
                              "ground_conditions WF",
                              "get_customer_profile WF",
                              "product_search Tool",
                              "get_user_affinity (ES|QL)"]):
        y = 88 + i * 53
        h = 48 if i == 0 else 40
        els.extend(labeled_rect(f"el{i}", 520, y, 210, h, lbl,
                                bg=GREEN_F, stroke=GREEN_S, font_size=14))

    # GCP zone
    els.append(rect("z_gcp", 810, 50, 250, 245, bg=ORANGE_F, stroke=ORANGE_S, sw=1, opacity=30))
    els.append(standalone_text("z_gcp_t", 850, 57, "Google Cloud (Vertex AI)", 18, ORANGE_S))
    els.extend(labeled_rect("g1", 835, 90, 200, 50, "Gemini 2.0 Flash\n+ Google Search",
                            bg=ORANGE_F, stroke=ORANGE_S, font_size=14))
    els.append(standalone_text("g1_note", 840, 148, "Real-time weather,\ntrail conditions", 13, MUTED))
    els.extend(labeled_rect("g2", 835, 190, 200, 50, "Imagen 3\nProduct Visualization",
                            bg=ORANGE_F, stroke=ORANGE_S, font_size=14))
    els.append(standalone_text("g2_note", 840, 248, "Scene generation,\nstyle reference", 13, MUTED))

    # MCP zone
    els.append(rect("z_mcp2", 810, 305, 250, 55, bg=TEAL_F, stroke=TEAL_S, sw=1, opacity=30))
    els.extend(labeled_rect("mcp2", 835, 313, 200, 38, "MCP: CRM / Persona",
                            bg=TEAL_F, stroke=TEAL_S, font_size=14))

    # Arrows
    els.extend(labeled_arrow("ia1", 165, 108, [[0, 0], [95, 0]], "terrain",
                             stroke=YELLOW_S, font_color=TEXT))
    els.extend(labeled_arrow("ia1b", 165, 170, [[0, 0], [95, 0]], "product",
                             stroke=YELLOW_S, font_color=TEXT))
    els.extend(labeled_arrow("ia2", 420, 110, [[0, 0], [100, 0]], "context",
                             stroke=TEXT, font_color=MUTED))
    els.extend(labeled_arrow("ia2b", 420, 170, [[0, 0], [100, 0]], "structured",
                             stroke=TEXT, font_color=MUTED))
    els.extend(labeled_arrow("ia3", 165, 150, [[0, 0], [355, -35]], "SSE stream",
                             stroke=TEXT, font_color=MUTED))
    els.extend(labeled_arrow("ia4", 730, 175, [[0, 0], [105, -60]], "weather",
                             stroke=ORANGE_S, font_color=TEXT))
    els.extend(labeled_arrow("ia5", 730, 180, [[0, 0], [105, 35]], "image gen",
                             stroke=ORANGE_S, font_color=TEXT, style="dashed"))
    els.extend(labeled_arrow("ia6", 730, 235, [[0, 0], [105, 95]], "persona",
                             stroke=TEAL_S, font_color=TEXT, style="dashed"))

    # Data flow summary
    els.append(standalone_text("flow_t", 10, 395, "Data Flow Summary", 18, TEXT))
    for i, line in enumerate([
        "1. Trip Planner: photo -> Jina VLM terrain analysis -> description injected into Agent context",
        "2. Search Panel: photo -> Jina VLM structured JSON -> category filter + semantic/lexical search",
        "3. Agent Builder orchestrates trip -> ground_conditions workflow -> Gemini + Google Search for live weather",
        "4. Agent searches product catalog (ELSER semantic) -> recommends gear from Wayfinder catalog only",
        "5. User clicks Visualize -> Imagen 3 generates product-in-scene preview with style reference",
    ]):
        els.append(standalone_text(f"flow{i}", 10, 425 + i * 22, line, 14, MUTED))

    els.extend(legend_row("lg2", 555, [
        ("Jina AI", YELLOW_F, YELLOW_S),
        ("Google Cloud", ORANGE_F, ORANGE_S),
        ("Elastic", GREEN_F, GREEN_S),
        ("MCP", TEAL_F, TEAL_S),
        ("User", BLUE_F, BLUE_S),
    ]))

    return dark_scene(els, 1090, 595)


# =====================================================================
# Diagram 3 — Vision Pipeline (Detailed)
# =====================================================================

def build_vision_pipeline():
    els = []
    els.append(standalone_text("title", 310, 8,
        "Vision Pipeline -- Detailed Flow", 24, TEXT))

    # Phase 1a — Trip Planner path (terrain analysis)
    els.append(standalone_text("p1", 10, 48,
        "Phase 1a: Terrain Analysis -- Trip Planner (Jina VLM)", 18, YELLOW_S))
    boxes1a = [
        ("v_usr", 10, 80, 130, 50, "User Uploads\nTerrain Photo", BLUE_F, BLUE_S),
        ("v_rsz", 195, 80, 140, 50, "Frontend Resize\nmax 2048px", BLUE_F, BLUE_S),
        ("v_ana", 390, 75, 160, 60, "POST /api/chat\nanalyze_image()\nterrain prompt", PURPLE_F, PURPLE_S),
        ("v_jina", 610, 80, 160, 50, "Jina VLM API\nTerrain Analysis", YELLOW_F, YELLOW_S),
        ("v_ctx", 830, 75, 185, 60, "[Vision Context:...]\nInjected into\nAgent prompt", GREEN_F, GREEN_S),
    ]
    for id, x, y, w, h, lbl, bg, stroke in boxes1a:
        els.extend(labeled_rect(id, x, y, w, h, lbl, bg=bg, stroke=stroke, font_size=13))
    els.append(arrow_el("va1", 140, 105, [[0, 0], [55, 0]], stroke=TEXT))
    els.extend(labeled_arrow("va2", 335, 105, [[0, 0], [55, 0]], "base64",
                             stroke=TEXT, font_color=MUTED))
    els.append(arrow_el("va3", 550, 105, [[0, 0], [60, 0]], stroke=YELLOW_S))
    els.append(arrow_el("va4", 770, 105, [[0, 0], [60, 0]], stroke=GREEN_S))

    # Phase 1b — Product Search path (structured analysis)
    els.append(standalone_text("p1b", 10, 152,
        "Phase 1b: Product Search -- Search Panel (Jina VLM Structured)", 18, YELLOW_S))
    boxes1b = [
        ("vs_usr", 10, 185, 130, 50, "User Uploads\nProduct Photo", BLUE_F, BLUE_S),
        ("vs_rsz", 195, 185, 140, 50, "Frontend Resize\n+ base64 encode", BLUE_F, BLUE_S),
        ("vs_be", 390, 180, 160, 60, "Chat or Hybrid\nanalyze_image\n_structured()", PURPLE_F, PURPLE_S),
        ("vs_jina", 610, 185, 160, 50, "Jina VLM API\nStructured JSON", YELLOW_F, YELLOW_S),
        ("vs_out", 830, 178, 185, 64, "product_type, category\nsubcategory, key_terms\ndescription", YELLOW_F, YELLOW_S),
    ]
    for id, x, y, w, h, lbl, bg, stroke in boxes1b:
        els.extend(labeled_rect(id, x, y, w, h, lbl, bg=bg, stroke=stroke, font_size=13))
    els.append(arrow_el("vb1", 140, 210, [[0, 0], [55, 0]], stroke=TEXT))
    els.append(arrow_el("vb2", 335, 210, [[0, 0], [55, 0]], stroke=TEXT))
    els.append(arrow_el("vb3", 550, 210, [[0, 0], [60, 0]], stroke=YELLOW_S))
    els.append(arrow_el("vb4", 770, 210, [[0, 0], [60, 0]], stroke=YELLOW_S))
    # Retry annotation
    els.append(standalone_text("retry_n", 610, 240,
        "Retries 502/503/429 (15s, 30s backoff)", 12, MUTED))

    # Phase 2
    els.append(standalone_text("p2", 10, 265,
        "Phase 2: Weather Grounding (Google Gemini + Search)", 18, GREEN_S))
    boxes2 = [
        ("v_ag", 10, 300, 155, 50, "Agent Builder\ncalls tool", GREEN_F, GREEN_S),
        ("v_wf", 225, 300, 175, 50, "ground_conditions\nWorkflow", GREEN_F, GREEN_S),
        ("v_gep", 470, 300, 155, 50, "Backend\n/vision/ground", PURPLE_F, PURPLE_S),
        ("v_gem", 695, 295, 175, 60, "Gemini 2.0 Flash\n+ Google Search\nGrounding", ORANGE_F, ORANGE_S),
        ("v_wout", 940, 300, 110, 50, "Weather\nCard in UI", GREEN_F, GREEN_S),
    ]
    for id, x, y, w, h, lbl, bg, stroke in boxes2:
        els.extend(labeled_rect(id, x, y, w, h, lbl, bg=bg, stroke=stroke, font_size=14))
    els.append(arrow_el("va5", 165, 325, [[0, 0], [60, 0]], stroke=TEXT))
    els.extend(labeled_arrow("va6", 400, 325, [[0, 0], [70, 0]], "HTTP",
                             stroke=TEXT, font_color=MUTED))
    els.append(arrow_el("va7", 625, 325, [[0, 0], [70, 0]], stroke=ORANGE_S))
    els.append(arrow_el("va8", 870, 325, [[0, 0], [70, 0]], stroke=GREEN_S))

    # Phase 3
    els.append(standalone_text("p3", 10, 378,
        "Phase 3: Product Visualization (Imagen 3)", 18, PURPLE_S))
    els.extend(labeled_rect("v_btn", 10, 415, 130, 50, "User Clicks\n\"Visualize\"",
                            bg=BLUE_F, stroke=BLUE_S, font_size=14))
    els.extend(labeled_rect("v_pep", 200, 415, 155, 50, "Backend\n/vision/preview",
                            bg=PURPLE_F, stroke=PURPLE_S, font_size=14))
    els.append(arrow_el("va9", 140, 440, [[0, 0], [60, 0]], stroke=TEXT))

    els.extend(labeled_rect("v_p1", 440, 405, 200, 55,
        "Pass 1: Scene Generation\nImagen text-to-image\nfrom Jina description",
        bg=ORANGE_F, stroke=ORANGE_S, font_size=13))
    els.append(arrow_el("va10", 355, 430, [[0, 0], [85, -15]], stroke=ORANGE_S))

    els.extend(labeled_rect("v_p2", 710, 400, 220, 65,
        "Pass 2: Product Composite\n+ Enhanced Prompting\n+ Style Reference (catalog img)\n+ Wearable Detection",
        bg=ORANGE_F, stroke=ORANGE_S, font_size=13))
    els.append(arrow_el("va11", 640, 432, [[0, 0], [70, 0]], stroke=ORANGE_S))

    els.extend(labeled_rect("v_fb", 440, 480, 200, 45,
        "Fallback: Single-pass\ncomposite generation",
        bg=RED_F, stroke=RED_S, font_size=13))
    els.append(arrow_el("va_fb", 355, 450, [[0, 0], [85, 40]],
                        stroke=RED_S, sw=2, style="dashed"))

    els.extend(labeled_rect("v_out", 1000, 410, 120, 50,
        "Preview Image\nin UI + lightbox",
        bg=BLUE_F, stroke=BLUE_S, font_size=14))
    els.append(arrow_el("va12", 930, 432, [[0, 0], [70, 0]], stroke=TEXT))

    # Insight cards
    els.append(standalone_text("p4", 10, 550, "UI Cards", 18, TEXT))
    els.extend(labeled_rect("ic1", 10, 580, 175, 45, "Vision Analysis\n(structured data)",
                            bg=PURPLE_F, stroke=PURPLE_S, font_size=13))
    els.extend(labeled_rect("ic2", 205, 580, 175, 45, "Weather Grounding\nFormatted card",
                            bg=ORANGE_F, stroke=ORANGE_S, font_size=13))
    els.extend(labeled_rect("ic3", 400, 580, 165, 45, "Imagen Prompt\nShow Prompt btn",
                            bg=PURPLE_F, stroke=PURPLE_S, font_size=13))
    els.extend(labeled_rect("ic4", 585, 580, 175, 45, "Vision Error\n(cold start / 503)",
                            bg=RED_F, stroke=RED_S, font_size=13))

    els.extend(legend_row("lg3", 650, [
        ("Frontend", BLUE_F, BLUE_S),
        ("Backend", PURPLE_F, PURPLE_S),
        ("Jina AI", YELLOW_F, YELLOW_S),
        ("Google Cloud", ORANGE_F, ORANGE_S),
        ("Elastic", GREEN_F, GREEN_S),
        ("Fallback / Error", RED_F, RED_S),
    ]))

    return dark_scene(els, 1150, 695)


# =====================================================================
# Diagram 4 — Security and Authentication
# =====================================================================

def build_security():
    els = []
    els.append(standalone_text("title", 260, 8,
        "Security and Authentication Flow", 24, TEXT))

    # Section 1: IAP
    els.append(standalone_text("s1", 10, 50,
        "1. User Access (Cloud Run + IAP)", 18, BLUE_S))
    els.extend(labeled_rect("s1_u", 10, 85, 130, 45, "User Browser",
                            bg=BLUE_F, stroke=BLUE_S))
    els.extend(labeled_rect("s1_iap", 210, 80, 175, 55, "Google IAP\n@elastic.co SSO",
                            bg=ORANGE_F, stroke=ORANGE_S))
    els.extend(labeled_rect("s1_fe", 460, 85, 155, 45, "Frontend (React)",
                            bg=BLUE_F, stroke=BLUE_S))
    els.append(arrow_el("s1a1", 140, 107, [[0, 0], [70, 0]], stroke=TEXT))
    els.extend(labeled_arrow("s1a2", 385, 107, [[0, 0], [75, 0]], "verified",
                             stroke=GREEN_S, font_color=MUTED))
    els.append(standalone_text("s1_note", 210, 142,
        "Only @elastic.co Google accounts can access", 13, MUTED))

    # Section 2: API Key
    els.append(standalone_text("s2", 10, 175,
        "2. Frontend -> Backend (API Key)", 18, PURPLE_S))
    els.extend(labeled_rect("s2_fe", 10, 210, 155, 45, "Frontend",
                            bg=BLUE_F, stroke=BLUE_S))
    els.extend(labeled_rect("s2_mw", 270, 205, 175, 55, "ApiKeyMiddleware\nvalidates header",
                            bg=PURPLE_F, stroke=PURPLE_S, font_size=14))
    els.extend(labeled_rect("s2_rt", 520, 210, 145, 45, "API Routers",
                            bg=PURPLE_F, stroke=PURPLE_S))
    els.extend(labeled_arrow("s2a1", 165, 232, [[0, 0], [105, 0]], "X-Api-Key",
                             stroke=TEXT, font_color=PINK))
    els.extend(labeled_arrow("s2a2", 445, 232, [[0, 0], [75, 0]], "pass",
                             stroke=GREEN_S, font_color=MUTED))
    els.append(standalone_text("s2_n1", 270, 266,
        "WAYFINDER_API_KEY env var; skipped if unset (local dev)", 13, MUTED))
    els.append(standalone_text("s2_n2", 270, 283,
        "VITE_WAYFINDER_API_KEY baked into frontend at build time", 13, MUTED))

    # Section 3: Workflow -> Backend
    els.append(standalone_text("s3", 10, 310,
        "3. Workflow -> Backend / MCP (API Key)", 18, GREEN_S))
    els.extend(labeled_rect("s3_wf", 10, 345, 175, 50, "Elastic Workflow\n(from Cloud)",
                            bg=GREEN_F, stroke=GREEN_S, font_size=14))
    els.extend(labeled_rect("s3_mw", 285, 345, 170, 50, "Backend / MCP\nApiKeyMiddleware",
                            bg=PURPLE_F, stroke=PURPLE_S, font_size=14))
    els.extend(labeled_arrow("s3a1", 185, 370, [[0, 0], [100, 0]], "X-Api-Key",
                             stroke=TEXT, font_color=PINK))
    els.append(standalone_text("s3_n", 285, 402,
        "Key stored as workflow const (not in code/git)", 13, MUTED))

    # Section 4: Backend -> ES
    els.append(standalone_text("s4", 10, 430,
        "4. Backend -> Elastic (ES API Key)", 18, GREEN_S))
    els.extend(labeled_rect("s4_be", 10, 465, 155, 45, "Backend",
                            bg=PURPLE_F, stroke=PURPLE_S))
    els.extend(labeled_rect("s4_es", 285, 465, 170, 45, "ES / Kibana / Agent",
                            bg=GREEN_F, stroke=GREEN_S))
    els.extend(labeled_arrow("s4a1", 165, 487, [[0, 0], [120, 0]], "ApiKey header",
                             stroke=TEXT, font_color=PINK))

    # Section 5: External APIs
    els.append(standalone_text("s5", 530, 310,
        "5. Backend -> External APIs", 18, ORANGE_S))
    els.extend(labeled_rect("s5_be", 530, 345, 130, 45, "Backend",
                            bg=PURPLE_F, stroke=PURPLE_S))
    els.extend(labeled_rect("s5_j", 745, 330, 155, 48, "Jina VLM\n(jina.ai)",
                            bg=YELLOW_F, stroke=YELLOW_S))
    els.extend(labeled_rect("s5_v", 745, 385, 155, 38, "Vertex AI",
                            bg=ORANGE_F, stroke=ORANGE_S))
    els.append(arrow_el("s5a1", 660, 360, [[0, 0], [85, -10]], stroke=YELLOW_S))
    els.append(arrow_el("s5a2", 660, 375, [[0, 0], [85, 20]], stroke=ORANGE_S))
    els.append(standalone_text("s5_j_a", 750, 376, "Bearer JINA_API_KEY", 13, PINK))
    els.append(standalone_text("s5_v_a", 750, 426, "GCP Service Account\nOAuth2 token", 13, PINK))

    # Section 6: Credential priority
    els.append(standalone_text("s6", 530, 470,
        "6. Credential Manager (Priority)", 18, TEXT))
    els.append(standalone_text("s6_1", 530, 498,
        "1st: UI Settings (in-memory, runtime override)", 14, TEXT))
    els.append(standalone_text("s6_2", 530, 518,
        "2nd: Environment variables (.env file)", 14, MUTED))
    els.append(standalone_text("s6_3", 530, 538,
        "3rd: ADC (Application Default Credentials)", 14, MUTED))

    els.extend(legend_row("lg4", 570, [
        ("Frontend", BLUE_F, BLUE_S),
        ("Backend", PURPLE_F, PURPLE_S),
        ("Elastic", GREEN_F, GREEN_S),
        ("Google Cloud", ORANGE_F, ORANGE_S),
        ("Jina AI", YELLOW_F, YELLOW_S),
    ]))
    els.append(standalone_text("lg4_pink", 10, 595,
        "Pink text = authentication credentials / headers", 13, PINK))

    return dark_scene(els, 940, 620)


# =====================================================================
# Diagram 5 — Cloud Run Deployment
# =====================================================================

def build_cloudrun():
    els = []
    els.append(standalone_text("title", 260, 8,
        "Cloud Run Deployment Architecture", 24, TEXT))

    # User
    els.extend(labeled_rect("cr_u", 10, 80, 130, 55, "User\n@elastic.co",
                            bg=BLUE_F, stroke=BLUE_S))

    # GCP zone
    els.append(rect("z_gcp2", 210, 45, 560, 440, bg=ORANGE_F, stroke=ORANGE_S, sw=1, opacity=20))
    els.append(standalone_text("z_gcp2_t", 220, 52,
        "Google Cloud (elastic-customer-eng / us-central1)", 16, ORANGE_S))

    # IAP
    els.extend(labeled_rect("cr_iap", 230, 80, 165, 50, "Identity-Aware\nProxy (IAP)",
                            bg=ORANGE_F, stroke=ORANGE_S, font_size=15))
    els.append(arrow_el("cra0", 140, 107, [[0, 0], [90, 0]], stroke=TEXT))

    # Cloud Run zone
    els.append(rect("z_cr", 460, 70, 290, 265, bg=PURPLE_F, stroke=PURPLE_S, sw=1, opacity=25))
    els.append(standalone_text("z_cr_t", 520, 77, "Cloud Run Services", 16, PURPLE_S))
    els.extend(labeled_arrow("cra1", 395, 105, [[0, 0], [65, 0]], "SSO OK",
                             stroke=GREEN_S, font_color=MUTED))

    els.extend(labeled_rect("cr_fe", 480, 105, 175, 50, "Frontend\nnginx + React",
                            bg=BLUE_F, stroke=BLUE_S, font_size=15))
    els.extend(labeled_rect("cr_be", 480, 175, 175, 50, "Backend\nFastAPI",
                            bg=PURPLE_F, stroke=PURPLE_S, font_size=15))
    els.extend(labeled_rect("cr_mcp", 480, 245, 175, 50, "MCP Server\nCRM / Persona",
                            bg=TEAL_F, stroke=TEAL_S, font_size=15))

    els.extend(labeled_arrow("cra2", 567, 155, [[0, 0], [0, 20]], "X-Api-Key",
                             stroke=TEXT, font_color=PINK, font_size=12))
    els.extend(labeled_arrow("cra3", 567, 225, [[0, 0], [0, 20]], "X-Api-Key",
                             stroke=TEXT, font_color=PINK, font_size=12))

    # Artifact Registry
    els.extend(labeled_rect("cr_ar", 680, 105, 60, 190, "Artifact\nRegistry",
                            bg=PURPLE_F, stroke=PURPLE_S, sw=1, opacity=40, font_size=12))

    # Vertex AI zone
    els.append(rect("z_vtx", 230, 355, 240, 120, bg=ORANGE_F, stroke=ORANGE_S, sw=1, opacity=30))
    els.append(standalone_text("z_vtx_t", 290, 362, "Vertex AI APIs", 16, ORANGE_S))
    els.extend(labeled_rect("cr_gem", 250, 390, 200, 35, "Gemini + Google Search",
                            bg=ORANGE_F, stroke=ORANGE_S, font_size=14))
    els.extend(labeled_rect("cr_img", 250, 435, 200, 35, "Imagen 3",
                            bg=ORANGE_F, stroke=ORANGE_S, font_size=14))
    els.extend(labeled_arrow("cra4", 480, 210, [[0, 0], [-110, 190]], "GCP SA",
                             stroke=ORANGE_S, style="dashed", font_color=MUTED))

    # Elastic Cloud zone
    els.append(rect("z_esc", 830, 45, 240, 280, bg=GREEN_F, stroke=GREEN_S, sw=1, opacity=30))
    els.append(standalone_text("z_esc_t", 890, 52, "Elastic Cloud", 16, GREEN_S))
    for i, lbl in enumerate(["Elasticsearch 9.x", "Kibana",
                              "Agent Builder", "Workflows"]):
        els.extend(labeled_rect(f"esc{i}", 855, 85 + i * 55, 195, 38, lbl,
                                bg=GREEN_F, stroke=GREEN_S, font_size=15))

    els.extend(labeled_arrow("cra5", 655, 195, [[0, 0], [200, -85]], "ES API Key",
                             stroke=GREEN_S, font_color=MUTED))
    els.extend(labeled_arrow("cra6", 655, 200, [[0, 0], [200, 10]], "SSE stream",
                             stroke=GREEN_S, font_color=MUTED))
    els.extend(labeled_arrow("cra7", 855, 265, [[0, 0], [-200, -50]], "HTTP callback",
                             stroke=GREEN_S, style="dashed", font_color=MUTED))
    els.extend(labeled_arrow("cra8", 855, 275, [[0, 0], [-200, 0]], "HTTP callback",
                             stroke=TEAL_S, style="dashed", font_color=MUTED))

    # Jina external (jina.ai — not in GCP)
    els.extend(labeled_rect("cr_jina", 10, 175, 165, 45, "Jina VLM API\n(jina.ai)",
                            bg=YELLOW_F, stroke=YELLOW_S, font_size=15))
    els.extend(labeled_arrow("cra9", 480, 195, [[0, 0], [-305, 0]], "Bearer API Key",
                             stroke=YELLOW_S, style="dashed", font_color=MUTED))

    els.extend(legend_row("lg5", 500, [
        ("Frontend", BLUE_F, BLUE_S),
        ("Backend / Infra", PURPLE_F, PURPLE_S),
        ("Elastic Cloud", GREEN_F, GREEN_S),
        ("Google Cloud", ORANGE_F, ORANGE_S),
        ("Jina AI", YELLOW_F, YELLOW_S),
        ("MCP", TEAL_F, TEAL_S),
    ]))
    els.append(standalone_text("lg5_note", 10, 525,
        "Dashed arrows = external API calls  |  Pink text = auth credentials", 13, MUTED))

    return dark_scene(els, 1100, 550)


# =====================================================================
# Diagram 6 — Vision Product Search Flow
# =====================================================================

def build_vision_search():
    els = []
    els.append(standalone_text("title", 220, 8,
        "Vision Product Search -- Chat and Hybrid Modes", 24, TEXT))

    # --- Chat Mode path (top) ---
    els.append(standalone_text("cm_t", 10, 50, "Chat Mode (Agent-Based)", 18, PURPLE_S))

    boxes_chat = [
        ("cs_usr", 10, 82, 135, 50, "User Uploads\nProduct Photo", BLUE_F, BLUE_S),
        ("cs_rsz", 195, 82, 130, 50, "imageUtils.ts\nResize + b64", BLUE_F, BLUE_S),
        ("cs_api", 375, 77, 170, 60, "POST /api/chat\nanalyze_image\n_structured()", PURPLE_F, PURPLE_S),
        ("cs_jina", 600, 82, 150, 50, "Jina VLM\nStructured JSON", YELLOW_F, YELLOW_S),
        ("cs_ctx", 805, 77, 195, 60, "[Vision Context: type]\n[Product Category: cat]\n-> Agent Builder", GREEN_F, GREEN_S),
    ]
    for id, x, y, w, h, lbl, bg, stroke in boxes_chat:
        els.extend(labeled_rect(id, x, y, w, h, lbl, bg=bg, stroke=stroke, font_size=13))
    els.append(arrow_el("ca1", 145, 107, [[0, 0], [50, 0]], stroke=TEXT))
    els.append(arrow_el("ca2", 325, 107, [[0, 0], [50, 0]], stroke=TEXT))
    els.append(arrow_el("ca3", 545, 107, [[0, 0], [55, 0]], stroke=YELLOW_S))
    els.append(arrow_el("ca4", 750, 107, [[0, 0], [55, 0]], stroke=GREEN_S))

    # Agent tool call
    els.extend(labeled_rect("cs_tool", 805, 150, 195, 40, "product_search tool\ncategory-aware results",
                            bg=GREEN_F, stroke=GREEN_S, font_size=13))
    els.append(arrow_el("ca5", 902, 137, [[0, 0], [0, 13]], stroke=GREEN_S))

    # --- Hybrid Mode path (bottom) ---
    els.append(standalone_text("hm_t", 10, 210, "Hybrid Mode (Direct ES Search)", 18, BLUE_S))

    boxes_hybrid = [
        ("hs_usr", 10, 245, 135, 50, "User Uploads\nProduct Photo", BLUE_F, BLUE_S),
        ("hs_rsz", 195, 245, 130, 50, "imageUtils.ts\nResize + b64", BLUE_F, BLUE_S),
        ("hs_api", 375, 240, 170, 60, "POST /api/products\n/search/hybrid\nimage_base64", PURPLE_F, PURPLE_S),
        ("hs_jina", 600, 245, 150, 50, "Jina VLM\nStructured JSON", YELLOW_F, YELLOW_S),
    ]
    for id, x, y, w, h, lbl, bg, stroke in boxes_hybrid:
        els.extend(labeled_rect(id, x, y, w, h, lbl, bg=bg, stroke=stroke, font_size=13))
    els.append(arrow_el("ha1", 145, 270, [[0, 0], [50, 0]], stroke=TEXT))
    els.append(arrow_el("ha2", 325, 270, [[0, 0], [50, 0]], stroke=TEXT))
    els.append(arrow_el("ha3", 545, 270, [[0, 0], [55, 0]], stroke=YELLOW_S))

    # Three ES query branches from structured output
    els.extend(labeled_rect("hs_sem", 810, 225, 195, 38, "ELSER Semantic\ndescription field",
                            bg=GREEN_F, stroke=GREEN_S, font_size=13))
    els.extend(labeled_rect("hs_lex", 810, 270, 195, 38, "BM25 Lexical\nkey_terms field",
                            bg=GREEN_F, stroke=GREEN_S, font_size=13))
    els.extend(labeled_rect("hs_flt", 810, 315, 195, 38, "Category Filter\ncategory -> term filter",
                            bg=GREEN_F, stroke=GREEN_S, font_size=13))

    els.append(arrow_el("ha4a", 750, 255, [[0, 0], [60, -12]], stroke=GREEN_S))
    els.append(arrow_el("ha4b", 750, 270, [[0, 0], [60, 0]], stroke=GREEN_S))
    els.append(arrow_el("ha4c", 750, 285, [[0, 0], [60, 12]], stroke=GREEN_S, style="dashed"))

    # --- Error handling ---
    els.append(standalone_text("err_t", 10, 375, "Error Handling", 18, RED_S))
    els.extend(labeled_rect("err_503", 10, 410, 175, 50, "Jina 503\nCold Start",
                            bg=RED_F, stroke=RED_S, font_size=13))
    els.extend(labeled_rect("err_retry", 245, 410, 175, 50, "Retry w/ Backoff\n15s, 30s (3 attempts)",
                            bg=PURPLE_F, stroke=PURPLE_S, font_size=13))
    els.extend(labeled_rect("err_evt", 480, 410, 175, 50, "vision_error SSE\nor JSON response",
                            bg=PURPLE_F, stroke=PURPLE_S, font_size=13))
    els.extend(labeled_rect("err_card", 720, 410, 175, 50, "Amber Error Card\nin Search Panel UI",
                            bg=RED_F, stroke=RED_S, font_size=13))
    els.append(arrow_el("ea1", 185, 435, [[0, 0], [60, 0]], stroke=RED_S))
    els.extend(labeled_arrow("ea2", 420, 435, [[0, 0], [60, 0]], "still fails",
                             stroke=RED_S, font_color=MUTED))
    els.append(arrow_el("ea3", 655, 435, [[0, 0], [65, 0]], stroke=RED_S))

    els.extend(legend_row("lg6", 485, [
        ("Frontend", BLUE_F, BLUE_S),
        ("Backend", PURPLE_F, PURPLE_S),
        ("Jina AI", YELLOW_F, YELLOW_S),
        ("Elastic", GREEN_F, GREEN_S),
        ("Error", RED_F, RED_S),
    ]))

    return dark_scene(els, 1040, 525)


# ── Render & Save ────────────────────────────────────────────────────

def svg_to_png(svg_path, png_path, scale=2):
    """Convert SVG to PNG using cairosvg (2x scale for retina clarity).

    Strips <mask> elements and mask= attributes before conversion because
    cairosvg mishandles the large mask rects that kroki.io/Excalidraw emits,
    causing the rendered image to be pushed off-canvas.
    """
    try:
        import re
        import cairosvg
        with open(svg_path, "r") as f:
            svg_text = f.read()
        # Strip mask elements and mask= attributes (cairosvg rendering bug)
        svg_text = re.sub(r"<mask[^>]*>.*?</mask>", "", svg_text, flags=re.DOTALL)
        svg_text = re.sub(r"<mask[^>]*/>", "", svg_text)
        svg_text = re.sub(r' mask="url\(#[^)]+\)"', "", svg_text)
        cairosvg.svg2png(bytestring=svg_text.encode("utf-8"),
                         write_to=png_path, scale=scale)
        size = os.path.getsize(png_path)
        print(f"  Saved {png_path} ({size:,} bytes)")
    except ImportError:
        print("  SKIP PNG: cairosvg not installed (pip install cairosvg)")
    except Exception as e:
        print(f"  ERROR PNG: {e}")


def save_and_render(name, scene_data, output_dir):
    """Save .excalidraw file, render SVG via kroki.io, convert to PNG."""
    os.makedirs(output_dir, exist_ok=True)

    # Save .excalidraw JSON
    excalidraw_path = os.path.join(output_dir, f"{name}.excalidraw")
    with open(excalidraw_path, "w") as f:
        json.dump(scene_data, f, indent=2)
    print(f"  Saved {excalidraw_path}")

    body = json.dumps(scene_data)

    # Render SVG via kroki.io
    svg_path = os.path.join(output_dir, f"{name}.svg")
    url = "https://kroki.io/excalidraw/svg"
    resp = requests.post(url, headers={"Content-Type": "text/plain"}, data=body)
    if resp.status_code == 200:
        with open(svg_path, "wb") as f:
            f.write(resp.content)
        print(f"  Saved {svg_path} ({len(resp.content):,} bytes)")

        # Convert SVG -> PNG (2x for retina)
        png_path = os.path.join(output_dir, f"{name}.png")
        svg_to_png(svg_path, png_path)
    else:
        print(f"  ERROR rendering SVG: {resp.status_code} - {resp.text[:200]}")


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "images")

    diagrams = [
        ("arch_high_level",      "High-Level Architecture",            build_high_level),
        ("arch_integration",     "Elastic + Jina + Google Integration", build_integration),
        ("arch_vision_pipeline", "Vision Pipeline (Detailed)",          build_vision_pipeline),
        ("arch_vision_search",   "Vision Product Search Flow",          build_vision_search),
        ("arch_security",        "Security and Authentication",         build_security),
        ("arch_cloud_run",       "Cloud Run Deployment",                build_cloudrun),
    ]

    for name, label, builder in diagrams:
        print(f"Building {label}...")
        save_and_render(name, builder(), output_dir)
        print()

    print("Done! All diagrams saved to docs/images/")
