#!/usr/bin/env python3
"""
Create the PR Race Condition Analysis skill and attach it to msbuild-pr-review-agent.

Idempotent — deletes existing skill by id first, then recreates and re-attaches.

Usage:
  python3 scripts/create_msbuild_skill.py
"""

from __future__ import annotations

import os
import sys

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

KIBANA_URL = os.getenv("STANDALONE_KIBANA_URL", os.getenv("KIBANA_URL", ""))
ES_APIKEY = os.getenv("STANDALONE_ELASTICSEARCH_APIKEY", os.getenv("ELASTICSEARCH_APIKEY", ""))

if not (KIBANA_URL and ES_APIKEY):
    print("✗ need STANDALONE_KIBANA_URL + STANDALONE_ELASTICSEARCH_APIKEY", file=sys.stderr)
    sys.exit(2)

HEADERS = {
    "Authorization": f"ApiKey {ES_APIKEY}",
    "Content-Type": "application/json",
    "kbn-xsrf": "true",
    "x-elastic-internal-origin": "kibana",
}

AGENT_ID = "msbuild-pr-review-agent"
SKILL_ID = "skill-pr-race-condition-analysis"

SKILL_CONTENT = """\
When analyzing a PR diff against historical OTel traces and incident postmortems, reason in terms of failure **patterns**, not keyword overlap.

## Key patterns to recognize

**Non-atomic read-modify-write**: A read-check-then-write sequence where concurrent requests can pass the check before either write completes. Signals: removed conditional UPDATE, SELECT-then-UPDATE split across statements, missing FOR UPDATE lock.

**TOCTOU (Time-of-Check to Time-of-Use)**: A guard condition is evaluated, then time passes before the protected resource is acted on — invalidating the check. Common in inventory, seat reservation, and booking systems. Signals: quantity/availability check separated from the decrement, removed `AND quantity >= N` in UPDATE WHERE clause.

**Missing serialization / lock contention**: Operations that should be atomic are split without a transaction or advisory lock. Signals: multi-step sequences on shared counters with no transaction boundary.

## Reasoning rule

When the diff looks like a "performance improvement" or "cache optimization," explicitly ask: does this remove an atomic guard? If yes, name the pattern in your comment — do not describe symptoms.
"""


def _get_agent() -> dict | None:
    r = requests.get(f"{KIBANA_URL}/api/agent_builder/agents/{AGENT_ID}", headers=HEADERS, timeout=30)
    if r.status_code == 200:
        return r.json()
    if r.status_code == 404:
        print(f"  ✗ agent {AGENT_ID} not found — run create_msbuild_agent.py first")
    else:
        print(f"  ✗ GET agent: HTTP {r.status_code}  {r.text[:200]}")
    return None


def _create_skill() -> bool:
    # Delete existing if present
    r = requests.delete(f"{KIBANA_URL}/api/agent_builder/skills/{SKILL_ID}?force=true", headers=HEADERS, timeout=30)
    if r.status_code in (200, 204):
        print(f"  ↻ deleted existing skill {SKILL_ID}")
    elif r.status_code != 404:
        print(f"  ⚠ delete skill: {r.status_code} {r.text[:100]}")

    body = {
        "id": SKILL_ID,
        "name": "PR Race Condition Analysis",
        "description": "Recognizes TOCTOU, non-atomic read-modify-write, and lock-contention patterns in PR diffs against historical OTel traces.",
        "content": SKILL_CONTENT,
    }
    r = requests.post(f"{KIBANA_URL}/api/agent_builder/skills", headers=HEADERS, json=body, timeout=30)
    if r.status_code in (200, 201):
        print(f"  ✓ skill: {SKILL_ID}")
        return True
    print(f"  ✗ skill: HTTP {r.status_code}  {r.text[:300]}")
    return False


def _attach_skill_to_agent(agent: dict) -> bool:
    config = agent.get("configuration", {})
    config["skill_ids"] = [SKILL_ID]
    payload = {
        "name": agent["name"],
        "description": agent["description"],
        "configuration": config,
    }
    r = requests.put(
        f"{KIBANA_URL}/api/agent_builder/agents/{AGENT_ID}",
        headers=HEADERS,
        json=payload,
        timeout=30,
    )
    if r.status_code == 200:
        print(f"  ✓ skill attached to agent: {AGENT_ID}")
        return True
    print(f"  ✗ attach skill: HTTP {r.status_code}  {r.text[:300]}")
    return False


def main() -> int:
    print(f"Kibana: {KIBANA_URL}")
    print()

    agent = _get_agent()
    if not agent:
        return 1

    if not _create_skill():
        return 2

    if not _attach_skill_to_agent(agent):
        return 3

    print()
    print("Done. In Kibana:")
    print(f"  AI → Agent Builder → {AGENT_ID} → Edit → Skills tab → '{SKILL_ID}' should appear")
    print(f"  AI → Skills → 'PR Race Condition Analysis' → verify body is readable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
