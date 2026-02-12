#!/usr/bin/env python3
"""Generate Excalidraw diagrams and render to SVG/PNG via kroki.io"""

import json
import random
import requests
import os

random.seed(42)

def seed():
    return random.randint(1, 2**31)

def rect(id, x, y, w, h, bg="transparent", stroke="#1e1e1e", sw=2, opacity=100, rounded=True, style="solid"):
    return {
        "type": "rectangle", "id": id, "x": x, "y": y, "width": w, "height": h,
        "angle": 0, "strokeColor": stroke, "backgroundColor": bg,
        "fillStyle": "solid", "strokeWidth": sw, "strokeStyle": style,
        "roughness": 1, "opacity": opacity, "groupIds": [], "frameId": None,
        "roundness": {"type": 3} if rounded else None,
        "seed": seed(), "version": 1, "versionNonce": seed(),
        "isDeleted": False, "boundElements": [], "updated": 1, "link": None, "locked": False
    }

def text_el(id, x, y, txt, size=16, color="#1e1e1e", container_id=None):
    return {
        "type": "text", "id": id, "x": x, "y": y,
        "width": len(txt) * size * 0.55, "height": size * 1.4,
        "angle": 0, "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": None, "seed": seed(), "version": 1, "versionNonce": seed(),
        "isDeleted": False, "boundElements": None, "updated": 1, "link": None, "locked": False,
        "text": txt, "fontSize": size, "fontFamily": 1,
        "textAlign": "center", "verticalAlign": "middle",
        "containerId": container_id, "originalText": txt, "autoResize": True
    }

def standalone_text(id, x, y, txt, size=16, color="#1e1e1e"):
    t = text_el(id, x, y, txt, size, color, container_id=None)
    t["textAlign"] = "left"
    t["verticalAlign"] = "top"
    return t

def labeled_rect(id, x, y, w, h, label, bg="transparent", stroke="#1e1e1e", sw=2,
                 opacity=100, rounded=True, font_size=16, font_color="#1e1e1e"):
    r = rect(id, x, y, w, h, bg, stroke, sw, opacity, rounded)
    tid = f"{id}_t"
    t = text_el(tid, x + 10, y + h / 2 - font_size * 0.7, label, font_size, font_color, container_id=id)
    r["boundElements"] = [{"id": tid, "type": "text"}]
    return [r, t]

def arrow_el(id, x, y, pts, stroke="#1e1e1e", sw=2, style="solid", end_head="arrow"):
    w = pts[-1][0] - pts[0][0]
    h = pts[-1][1] - pts[0][1]
    return {
        "type": "arrow", "id": id, "x": x, "y": y,
        "width": abs(w), "height": abs(h),
        "angle": 0, "strokeColor": stroke, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": sw, "strokeStyle": style,
        "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": {"type": 2},
        "seed": seed(), "version": 1, "versionNonce": seed(),
        "isDeleted": False, "boundElements": [], "updated": 1, "link": None, "locked": False,
        "points": pts, "endArrowhead": end_head, "startArrowhead": None,
        "startBinding": None, "endBinding": None
    }

def labeled_arrow(id, x, y, pts, label, stroke="#1e1e1e", sw=2, style="solid",
                  end_head="arrow", font_size=14, font_color=None):
    a = arrow_el(id, x, y, pts, stroke, sw, style, end_head)
    tid = f"{id}_t"
    mx = x + (pts[0][0] + pts[-1][0]) / 2 - len(label) * font_size * 0.25
    my = y + (pts[0][1] + pts[-1][1]) / 2 - font_size * 1.2
    t = text_el(tid, mx, my, label, font_size, font_color or stroke, container_id=id)
    a["boundElements"] = [{"id": tid, "type": "text"}]
    return [a, t]

def lifeline(id, x, y_start, length):
    return arrow_el(id, x, y_start, [[0, 0], [0, length]],
                    stroke="#c0c0c0", sw=1, style="dashed", end_head=None)

def scene(elements):
    return {"type": "excalidraw", "version": 2, "source": "wayfinder",
            "elements": elements, "appState": {"viewBackgroundColor": "#ffffff"}}

# ── Diagram 1: Vision Pipeline Sequence ──────────────────────────────

def build_sequence_diagram():
    els = []

    # Title
    els.append(standalone_text("title", 250, 5, "Vision Pipeline — Sequence Flow", 26, "#1e1e1e"))

    # Participants: (id, label, x_center, color)
    participants = [
        ("user",    "User",          100,  "#a5d8ff", "#4a9eed"),
        ("fe",      "Frontend",      270,  "#b2f2bb", "#22c55e"),
        ("be",      "Backend",       440,  "#d0bfff", "#8b5cf6"),
        ("jina",    "Jina VLM",      610,  "#ffd8a8", "#f59e0b"),
        ("agent",   "Agent Builder", 790,  "#ffc9c9", "#ef4444"),
        ("imagen",  "Imagen",        960,  "#c3fae8", "#06b6d4"),
    ]

    for pid, label, cx, bg, stroke in participants:
        w = 140
        els.extend(labeled_rect(f"{pid}H", cx - w/2, 55, w, 42, label,
                                bg=bg, stroke=stroke, font_size=16))
        els.append(lifeline(f"{pid}L", cx, 97, 520))

    # Messages: (y, from_cx, to_cx, label, color, dashed)
    messages = [
        (150, 100,  270,  "Upload photo + optional prompt",            "#4a9eed", False),
        (190, 270,  440,  "POST /api/chat (image + text)",             "#1e1e1e", False),
        (230, 440,  610,  "Analyze terrain/conditions",                "#f59e0b", False),
        (270, 610,  440,  "Text description",                          "#f59e0b", True),
        (310, 440,  790,  "Enhanced prompt with vision context",       "#ef4444", False),
        (350, 790,  440,  "SSE stream (reasoning, tools, products)",   "#ef4444", True),
        (390, 440,  270,  "SSE stream (same as today)",                "#22c55e", True),
        (430, 270,  440,  "POST /api/vision/preview (image + product)","#1e1e1e", False),
        (470, 440,  960,  "Generate product-in-scene",                 "#06b6d4", False),
        (510, 960,  440,  "Generated image",                           "#06b6d4", True),
        (550, 440,  270,  "Base64 image",                              "#22c55e", True),
        (590, 270,  100,  "Shows recommendations + preview image",     "#4a9eed", True),
    ]

    for i, (y, fx, tx, label, color, dashed) in enumerate(messages):
        mid = f"m{i+1}"
        dx = tx - fx
        els.extend(labeled_arrow(mid, fx, y, [[0, 0], [dx, 0]], label,
                                 stroke=color, sw=2,
                                 style="dashed" if dashed else "solid",
                                 font_size=14, font_color="#1e1e1e"))

    return scene(els)


# ── Diagram 2: Credential Strategy ───────────────────────────────────

def build_credential_diagram():
    els = []

    # Title
    els.append(standalone_text("title", 185, 0, "Credential Strategy — Resolution Flow", 24, "#1e1e1e"))

    # Zone backgrounds
    els.extend([
        rect("z1", 40, 60, 230, 250, bg="#dbe4ff", stroke="#4a9eed", sw=1, opacity=40),
        standalone_text("z1t", 68, 68, "Credential Sources", 16, "#2563eb"),
        rect("z2", 340, 100, 200, 180, bg="#e5dbff", stroke="#8b5cf6", sw=1, opacity=40),
        standalone_text("z2t", 385, 108, "Resolution", 16, "#6d28d9"),
        rect("z3", 610, 50, 210, 300, bg="#d3f9d8", stroke="#22c55e", sw=1, opacity=40),
        standalone_text("z3t", 665, 58, "Consumers", 16, "#15803d"),
    ])

    # Source boxes
    els.extend(labeled_rect("ui", 60, 110, 190, 55, "Settings Page (UI)",
                            bg="#a5d8ff", stroke="#4a9eed", font_size=16))
    els.append(standalone_text("ui_note", 75, 172, "in-memory, runtime override", 13, "#757575"))
    els.extend(labeled_rect("env", 60, 225, 190, 55, ".env file",
                            bg="#a5d8ff", stroke="#4a9eed", font_size=16))

    # Resolution box
    els.extend(labeled_rect("cm", 365, 155, 150, 70, "CredentialManager",
                            bg="#d0bfff", stroke="#8b5cf6", font_size=15))

    # Consumer boxes
    els.extend(labeled_rect("c_jina", 635, 95, 160, 50, "Jina VLM",
                            bg="#ffd8a8", stroke="#f59e0b", font_size=16))
    els.extend(labeled_rect("c_vertex", 635, 185, 160, 50, "Vertex AI",
                            bg="#c3fae8", stroke="#06b6d4", font_size=16))
    els.extend(labeled_rect("c_imagen", 635, 275, 160, 50, "Imagen 3",
                            bg="#ffc9c9", stroke="#ef4444", font_size=16))

    # Arrows: sources → CM
    els.extend(labeled_arrow("a1", 250, 137, [[0, 0], [115, 53]],
                             "priority 1", stroke="#4a9eed", font_size=14))
    els.extend(labeled_arrow("a2", 250, 252, [[0, 0], [115, -62]],
                             "priority 2", stroke="#4a9eed", font_size=14))

    # Arrows: CM → consumers
    els.append(arrow_el("a3", 515, 175, [[0, 0], [120, -55]], stroke="#8b5cf6", sw=2))
    els.append(arrow_el("a4", 515, 190, [[0, 0], [120, 20]],  stroke="#8b5cf6", sw=2))
    els.append(arrow_el("a5", 515, 205, [[0, 0], [120, 95]],  stroke="#8b5cf6", sw=2))

    return scene(els)


# ── Render & Save ────────────────────────────────────────────────────

def save_and_render(name, scene_data, output_dir):
    """Save .excalidraw file and render via kroki.io"""
    os.makedirs(output_dir, exist_ok=True)

    # Save .excalidraw JSON
    excalidraw_path = os.path.join(output_dir, f"{name}.excalidraw")
    with open(excalidraw_path, "w") as f:
        json.dump(scene_data, f, indent=2)
    print(f"  Saved {excalidraw_path}")

    body = json.dumps(scene_data)

    # Render SVG via kroki.io (expects text/plain for Excalidraw; only SVG supported)
    for fmt in ["svg"]:
        url = f"https://kroki.io/excalidraw/{fmt}"
        resp = requests.post(url, headers={"Content-Type": "text/plain"}, data=body)
        if resp.status_code == 200:
            out_path = os.path.join(output_dir, f"{name}.{fmt}")
            with open(out_path, "wb") as f:
                f.write(resp.content)
            print(f"  Saved {out_path} ({len(resp.content)} bytes)")
        else:
            print(f"  ERROR rendering {fmt}: {resp.status_code} - {resp.text[:200]}")


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "images")

    print("Building Vision Pipeline Sequence diagram...")
    save_and_render("vision_pipeline_sequence", build_sequence_diagram(), output_dir)

    print("\nBuilding Credential Strategy Flow diagram...")
    save_and_render("credential_strategy_flow", build_credential_diagram(), output_dir)

    print("\nDone!")
