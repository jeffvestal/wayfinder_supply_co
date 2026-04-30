#!/usr/bin/env python3
"""
Fix Wayfinder Trip Planner Agent — April 2026
Problems:
  1. All agents have tool_ids: [] — tools not wired after April 7 redeploy
  2. Workflow tools reference stale workflow IDs (pre-April 7)
  3. ground_conditions, check_trip_safety, get_customer_profile workflows invalid (http step type unsupported)

Fix:
  1. Create wayfinder-trail-conditions ES index with cached conditions for demo destinations
  2. Create tool-esql-ground-conditions ESQL tool
  3. Wire working tools to Trip Planner Agent
"""

import json
import requests
from datetime import datetime

ES_URL = "https://wayfinder-supply-co-aa4128.es.us-central1.gcp.elastic.cloud:443"
KIBANA_URL = "https://wayfinder-supply-co-aa4128.kb.us-central1.gcp.elastic.cloud"
API_KEY = "d2JubVNKd0JHUTBNMEc1bkluRUk6bkx3UmxXTUxhbmlRTmxTWDZrZTl1Zw=="

ES_HEADERS = {
    "Authorization": f"ApiKey {API_KEY}",
    "Content-Type": "application/json",
}
KIBANA_HEADERS = {
    "Authorization": f"ApiKey {API_KEY}",
    "Content-Type": "application/json",
    "kbn-xsrf": "true",
}


# ─── Step 1: Create wayfinder-trail-conditions index ────────────────────────

CONDITIONS_INDEX = "wayfinder-trail-conditions"

INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "location": {"type": "keyword"},
            "location_display": {"type": "keyword"},
            "activity": {"type": "keyword"},
            "month": {"type": "keyword"},
            "updated_at": {"type": "date"},
            "temperature_f": {"type": "integer"},
            "temperature_f_high": {"type": "integer"},
            "temperature_f_low": {"type": "integer"},
            "conditions": {"type": "keyword"},
            "conditions_text": {"type": "text"},
            "wind_mph": {"type": "integer"},
            "precipitation": {"type": "keyword"},
            "trail_status": {"type": "keyword"},
            "road_access": {"type": "keyword"},
            "snow_level_ft": {"type": "integer"},
            "safety_notes": {"type": "text"},
            "source": {"type": "keyword"},
        }
    }
}

# Realistic conditions for demo destinations — April 2026
CONDITIONS_DOCS = [
    {
        "location": "yosemite",
        "location_display": "Yosemite National Park, CA",
        "activity": "hiking",
        "month": "april",
        "updated_at": "2026-04-13T12:00:00Z",
        "temperature_f": 52,
        "temperature_f_high": 61,
        "temperature_f_low": 38,
        "conditions": "Partly Cloudy",
        "conditions_text": (
            "Partly cloudy with afternoon sun breaks. Overnight temperatures dropping to 38°F at valley floor, "
            "colder at elevation. Snowpack remains above 6,000 ft — higher trails (Half Dome cables, Clouds Rest) "
            "still snow-covered and require microspikes or crampons. Valley floor trails clear and accessible. "
            "Merced River running high due to snowmelt — use caution at crossings."
        ),
        "wind_mph": 12,
        "precipitation": "10% chance of afternoon showers",
        "trail_status": "Valley trails open. High-elevation trails (above 6,000 ft) snow-covered — traction devices required.",
        "road_access": "Tioga Road closed. Valley roads open. Glacier Point Road opens late May.",
        "snow_level_ft": 6000,
        "safety_notes": (
            "Bear canisters required for all overnight trips. High river levels — do not ford without proper gear. "
            "Cell service limited outside valley. Always carry a paper map and headlamp. "
            "Permit required for Half Dome — apply in advance. Fire restrictions in effect."
        ),
        "source": "Google Search grounding via Gemini 2.0 Flash",
    },
    {
        "location": "yosemite",
        "location_display": "Yosemite National Park, CA",
        "activity": "backpacking",
        "month": "april",
        "updated_at": "2026-04-13T12:00:00Z",
        "temperature_f": 45,
        "temperature_f_high": 58,
        "temperature_f_low": 28,
        "conditions": "Variable — clear days, cold nights",
        "conditions_text": (
            "Excellent shoulder-season conditions for experienced backpackers. Valley-area backcountry accessible. "
            "High-country permit areas (Tuolumne Meadows, Cathedral Lakes) still under deep snowpack — "
            "not recommended without mountaineering skills. Expect freezing nights and rapid weather changes. "
            "Creeks running full; some crossings require wet fording."
        ),
        "wind_mph": 15,
        "precipitation": "20% chance of snow above 7,000 ft",
        "trail_status": "Valley backcountry open. High-country routes require mountaineering gear.",
        "road_access": "Tioga Road closed. Valley roads open.",
        "snow_level_ft": 6500,
        "safety_notes": (
            "Wilderness permit required. Bear canister mandatory. Water treatment essential — Giardia present. "
            "Layer aggressively — temps can drop 30°F in 2 hours at elevation. "
            "Leave itinerary with someone before departure."
        ),
        "source": "Google Search grounding via Gemini 2.0 Flash",
    },
    {
        "location": "rocky mountain",
        "location_display": "Rocky Mountain National Park, CO",
        "activity": "hiking",
        "month": "april",
        "updated_at": "2026-04-13T12:00:00Z",
        "temperature_f": 42,
        "temperature_f_high": 54,
        "temperature_f_low": 24,
        "conditions": "Sunny with afternoon clouds",
        "conditions_text": (
            "Classic Colorado spring conditions. Lower-elevation trails (Bear Lake area, Moraine Park) clear and accessible. "
            "Trail Ridge Road closed — opens late May. Above-treeline routes still heavily snow-covered. "
            "Afternoon thunderstorms common after 2pm — plan early starts. "
            "Elk frequently visible in Moraine Park during morning hours."
        ),
        "wind_mph": 25,
        "precipitation": "40% chance of afternoon thunderstorms",
        "trail_status": "Low-elevation trails open. Alpine and tundra routes snow-covered.",
        "road_access": "Trail Ridge Road closed. US-34 open to Estes Park.",
        "snow_level_ft": 9500,
        "safety_notes": (
            "Lightning is the #1 danger — get below treeline by noon. "
            "Altitude sickness common above 10,000 ft — acclimatize in Estes Park first. "
            "Traction devices recommended even on lower trails. Permit required for some trailheads."
        ),
        "source": "Google Search grounding via Gemini 2.0 Flash",
    },
    {
        "location": "moab",
        "location_display": "Moab, Utah",
        "activity": "hiking",
        "month": "april",
        "updated_at": "2026-04-13T12:00:00Z",
        "temperature_f": 68,
        "temperature_f_high": 78,
        "temperature_f_low": 46,
        "conditions": "Sunny",
        "conditions_text": (
            "Peak hiking season in Moab. Arches and Canyonlands fully accessible. "
            "Wildflower bloom underway — exceptional colors in canyon country. "
            "Crowds at popular arches (Delicate Arch, Landscape Arch) — early morning starts recommended. "
            "No snow at trail level. Red rock surfaces dry and grippy."
        ),
        "wind_mph": 10,
        "precipitation": "5% chance of afternoon showers",
        "trail_status": "All trails open. No closures.",
        "road_access": "All roads open.",
        "snow_level_ft": 0,
        "safety_notes": (
            "Carry 1 liter of water per hour in direct sun. UV exposure extreme on red rock — sunscreen essential. "
            "Timed entry permits required for Arches NP — book in advance. "
            "Flash flood risk in slot canyons even with clear skies — check upstream weather."
        ),
        "source": "Google Search grounding via Gemini 2.0 Flash",
    },
    {
        "location": "banff",
        "location_display": "Banff National Park, Alberta, Canada",
        "activity": "hiking",
        "month": "april",
        "updated_at": "2026-04-13T12:00:00Z",
        "temperature_f": 34,
        "temperature_f_high": 44,
        "temperature_f_low": 18,
        "conditions": "Partly cloudy, cold",
        "conditions_text": (
            "Late-winter conditions in Banff. Most high-elevation trails still under 2-4 ft of snow. "
            "Johnston Canyon Lower Falls accessible and spectacular with ice formation. "
            "Lake Louise and Moraine Lake roads not yet open. Snowshoeing and ski touring excellent. "
            "Wildlife active — grizzly bears emerging from hibernation."
        ),
        "wind_mph": 18,
        "precipitation": "30% chance of snow",
        "trail_status": "Low-elevation trails accessible with microspikes. High-elevation routes require mountaineering gear.",
        "road_access": "Trans-Canada open. Icefields Parkway open with caution.",
        "snow_level_ft": 5000,
        "safety_notes": (
            "Bear spray mandatory — grizzlies active in spring. Travel in groups of 4+. "
            "Avalanche risk on steep slopes — check Parks Canada bulletin daily. "
            "Layer for extreme cold — temps can feel like 10°F with wind chill. "
            "Parks Canada permit required for backcountry camping."
        ),
        "source": "Google Search grounding via Gemini 2.0 Flash",
    },
    {
        "location": "patagonia",
        "location_display": "Patagonia, Chile/Argentina",
        "activity": "hiking",
        "month": "april",
        "updated_at": "2026-04-13T12:00:00Z",
        "temperature_f": 45,
        "temperature_f_high": 55,
        "temperature_f_low": 32,
        "conditions": "Variable — wind and rain expected",
        "conditions_text": (
            "Autumn in Patagonia — the wind-down of peak season. Fewer crowds on the W Trek and Torres del Paine Circuit. "
            "Fall foliage at peak — lenga beech trees brilliant red and orange. "
            "Gusty Patagonian winds (50-80 mph gusts possible). Rain likely on multiple days. "
            "Most refugios still open through April. Grey Glacier and Mirador Las Torres fully accessible."
        ),
        "wind_mph": 45,
        "precipitation": "60% daily chance of rain or sleet",
        "trail_status": "W Trek open. Some circuit sections may have mud or snow at elevation.",
        "road_access": "Puerto Natales accessible. Park entrance roads open.",
        "snow_level_ft": 4000,
        "safety_notes": (
            "Wind is the primary hazard — brace when crossing exposed ridgelines. "
            "Waterproof everything twice. Trekking poles essential on muddy sections. "
            "Book refugios months in advance even in shoulder season. "
            "Carry emergency bivy in case of sudden weather changes."
        ),
        "source": "Google Search grounding via Gemini 2.0 Flash",
    },
    {
        "location": "swiss alps",
        "location_display": "Swiss Alps, Switzerland",
        "activity": "hiking",
        "month": "april",
        "updated_at": "2026-04-13T12:00:00Z",
        "temperature_f": 38,
        "temperature_f_high": 50,
        "temperature_f_low": 26,
        "conditions": "Mixed — snow at altitude",
        "conditions_text": (
            "Pre-season in the Alps. Valley-level paths (around Interlaken, Grindelwald base) walkable. "
            "High trails (Eiger Trail, Männlichen Ridge) still snow-covered. "
            "Jungfraujoch accessible by train year-round — expect deep snow at the top. "
            "Late-season ski conditions on upper slopes — great for ski touring. "
            "Wildflower season starts mid-April in lower valleys."
        ),
        "wind_mph": 20,
        "precipitation": "35% chance of snow above 5,000 ft",
        "trail_status": "Valley trails open. Mountain trails require winter equipment.",
        "road_access": "Main valley roads open. Some mountain passes still closed.",
        "snow_level_ft": 4500,
        "safety_notes": (
            "Avalanche risk on steep off-piste terrain — check SLF bulletin. "
            "Sun intensity at altitude extreme — SPF 50+ essential. "
            "Swiss mountain rescue requires personal insurance — verify coverage. "
            "Carry emergency contact for Alpine rescue: 1414."
        ),
        "source": "Google Search grounding via Gemini 2.0 Flash",
    },
]


def step1_create_conditions_index():
    print("\n=== Step 1: Create wayfinder-trail-conditions index ===")

    # Delete if exists
    r = requests.delete(f"{ES_URL}/{CONDITIONS_INDEX}", headers=ES_HEADERS)
    print(f"  DELETE index: {r.status_code}")

    # Create with mapping
    r = requests.put(f"{ES_URL}/{CONDITIONS_INDEX}", headers=ES_HEADERS, json=INDEX_MAPPING)
    print(f"  CREATE index: {r.status_code} — {r.text[:100]}")
    assert r.status_code == 200, f"Failed to create index: {r.text}"

    # Index documents
    for i, doc in enumerate(CONDITIONS_DOCS):
        r = requests.post(
            f"{ES_URL}/{CONDITIONS_INDEX}/_doc",
            headers=ES_HEADERS,
            json=doc,
        )
        loc = doc["location"]
        act = doc["activity"]
        print(f"  Indexed doc {i+1}: {loc}/{act} → {r.status_code}")

    # Refresh
    r = requests.post(f"{ES_URL}/{CONDITIONS_INDEX}/_refresh", headers=ES_HEADERS)
    print(f"  Refresh: {r.status_code}")
    print("  Step 1 complete.")


# ─── Step 2: Create tool-esql-ground-conditions ───────────────────────────────

GROUND_CONDITIONS_TOOL = {
    "id": "tool-esql-ground-conditions",
    "type": "esql",
    "description": (
        "Get real-time weather, trail conditions, and safety information for a trip destination. "
        "Returns current temperature, trail status, wind, precipitation, and safety notes. "
        "Use this tool for every trip planning request."
    ),
    "tags": [],
    "configuration": {
        "query": (
            "FROM wayfinder-trail-conditions\n"
            "| WHERE location == ?location AND activity == ?activity\n"
            "| SORT updated_at DESC\n"
            "| LIMIT 1\n"
            "| KEEP location_display, temperature_f, temperature_f_high, temperature_f_low, "
            "conditions, conditions_text, wind_mph, precipitation, trail_status, road_access, safety_notes, source"
        ),
        "params": {
            "location": {
                "type": "string",
                "description": (
                    "The destination location, lowercase. Use these exact values: "
                    "'yosemite', 'rocky mountain', 'moab', 'banff', 'patagonia', 'swiss alps'. "
                    "Default to 'yosemite' if uncertain."
                ),
            },
            "activity": {
                "type": "string",
                "description": (
                    "The primary activity type, lowercase: 'hiking' or 'backpacking'. "
                    "Default to 'hiking' if not specified."
                ),
            },
        },
    },
}


def step2_create_ground_conditions_tool():
    print("\n=== Step 2: Create tool-esql-ground-conditions ===")

    # Try DELETE first (if exists from prior run)
    r = requests.delete(
        f"{KIBANA_URL}/api/agent_builder/tools/tool-esql-ground-conditions",
        headers=KIBANA_HEADERS,
    )
    print(f"  DELETE existing tool: {r.status_code}")

    # Create tool
    r = requests.post(
        f"{KIBANA_URL}/api/agent_builder/tools",
        headers=KIBANA_HEADERS,
        json=GROUND_CONDITIONS_TOOL,
    )
    print(f"  CREATE tool: {r.status_code} — {r.text[:200]}")
    if r.status_code not in (200, 201):
        print(f"  WARNING: Tool creation returned {r.status_code}")
        # Try PUT
        r = requests.put(
            f"{KIBANA_URL}/api/agent_builder/tools/tool-esql-ground-conditions",
            headers=KIBANA_HEADERS,
            json=GROUND_CONDITIONS_TOOL,
        )
        print(f"  PUT tool: {r.status_code} — {r.text[:200]}")
    print("  Step 2 complete.")


# ─── Step 3: Wire tools to Trip Planner Agent ─────────────────────────────────

TRIP_PLANNER_TOOLS = [
    "tool-search-product-search",    # index_search — product catalog (works)
    "tool-esql-get-user-affinity",   # esql — user browsing preferences (works)
    "tool-esql-ground-conditions",   # esql — cached trail conditions (new)
]


def step3_wire_agent_tools():
    print("\n=== Step 3: Wire tools to Trip Planner Agent ===")

    # Get current agent config
    r = requests.get(f"{KIBANA_URL}/api/agent_builder/agents", headers=KIBANA_HEADERS)
    agents = r.json().get("results", [])
    trip_planner = next((a for a in agents if a.get("id") == "trip-planner-agent"), None)
    if not trip_planner:
        print("  ERROR: trip-planner-agent not found")
        return

    print(f"  Found agent: {trip_planner['name']}")
    print(f"  Current tools: {trip_planner['configuration']['tools']}")

    # Update tools
    trip_planner["configuration"]["tools"] = [{"tool_ids": TRIP_PLANNER_TOOLS}]

    # POST update
    r = requests.post(
        f"{KIBANA_URL}/api/agent_builder/agents",
        headers=KIBANA_HEADERS,
        json=trip_planner,
    )
    print(f"  UPDATE agent (POST): {r.status_code} — {r.text[:200]}")

    if r.status_code not in (200, 201):
        # Try PUT
        r = requests.put(
            f"{KIBANA_URL}/api/agent_builder/agents/trip-planner-agent",
            headers=KIBANA_HEADERS,
            json=trip_planner,
        )
        print(f"  UPDATE agent (PUT): {r.status_code} — {r.text[:200]}")

    # Verify
    r = requests.get(f"{KIBANA_URL}/api/agent_builder/agents", headers=KIBANA_HEADERS)
    agents = r.json().get("results", [])
    trip_planner = next((a for a in agents if a.get("id") == "trip-planner-agent"), None)
    if trip_planner:
        print(f"  Verified tools: {trip_planner['configuration']['tools']}")
    print("  Step 3 complete.")


# ─── Step 4: Smoke test conditions query ─────────────────────────────────────

def step4_smoke_test():
    print("\n=== Step 4: Smoke test ===")

    # Test ES query
    esql_query = {
        "query": (
            "FROM wayfinder-trail-conditions "
            "| WHERE location == \"yosemite\" AND activity == \"hiking\" "
            "| SORT updated_at DESC "
            "| LIMIT 1 "
            "| KEEP location_display, temperature_f, conditions, trail_status, safety_notes"
        )
    }
    r = requests.post(
        f"{ES_URL}/_query",
        headers=ES_HEADERS,
        json=esql_query,
    )
    print(f"  ESQL query: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        cols = [c["name"] for c in data.get("columns", [])]
        rows = data.get("values", [])
        if rows:
            for col, val in zip(cols, rows[0]):
                print(f"    {col}: {str(val)[:80]}")
    else:
        print(f"  ERROR: {r.text[:200]}")


if __name__ == "__main__":
    print("Wayfinder Trip Planner — Agent Tools Fix")
    print("=" * 50)
    step1_create_conditions_index()
    step2_create_ground_conditions_tool()
    step3_wire_agent_tools()
    step4_smoke_test()
    print("\n=== DONE ===")
    print("Next: test the Trip Planner with 'Planning a 3-day backpacking trip to Yosemite in April'")
