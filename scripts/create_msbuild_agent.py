#!/usr/bin/env python3
"""
Create the MS Build 2026 PR-review agent and its three parameterized ES|QL tools.

Creates (idempotent — deletes existing by id first):
  - tool-esql-find-similar-traces        find traces matching service + endpoint
  - tool-esql-find-latency-spikes        find spans over a p99 threshold
  - tool-esql-search-incidents           search indexed GitHub Issues for postmortems
  - agent: msbuild-pr-review-agent       with reasoning prompt from build plan Phase 2C

Does NOT create GitHub MCP connector or Azure OpenAI connector — those are configured once
in Kibana (Stack Management → Connectors) and referenced by name/id by the agent. Wire them
in the Agent Builder UI after this script runs.

Usage:
  python3 scripts/create_msbuild_agent.py
  python3 scripts/create_msbuild_agent.py --issues-index github-issues-wayfinder
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Optional

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
TRACES_INDEX = os.getenv("MSBUILD_TRACES_INDEX", "traces-apm.wayfinder-default")


def _delete(path: str) -> None:
    # Use ?force=true to ensure deletion even if tool is in use
    url = f"{KIBANA_URL}{path}" if "?" in path else f"{KIBANA_URL}{path}?force=true"
    r = requests.delete(url, headers=HEADERS, timeout=30)
    if r.status_code in (200, 204):
        print(f"  ↻ deleted {path}")
    elif r.status_code != 404:
        print(f"  ⚠ delete {path}: {r.status_code} {r.text[:100]}")


def _create_esql_tool(tool_id: str, description: str, query: str, params: dict) -> Optional[str]:
    _delete(f"/api/agent_builder/tools/{tool_id}")
    body = {
        "id": tool_id,
        "type": "esql",
        "description": description,
        "configuration": {"query": query, "params": params},
    }
    r = requests.post(f"{KIBANA_URL}/api/agent_builder/tools", headers=HEADERS, json=body, timeout=30)
    if r.status_code in (200, 201):
        print(f"  ✓ tool: {tool_id}")
        return tool_id
    # Legacy retry: swap string→keyword param types
    if r.status_code == 400 and "types that failed validation" in r.text:
        legacy = {k: {**v, "type": "keyword"} for k, v in params.items()}
        body["configuration"]["params"] = legacy
        r = requests.post(f"{KIBANA_URL}/api/agent_builder/tools", headers=HEADERS, json=body, timeout=30)
        if r.status_code in (200, 201):
            print(f"  ✓ tool: {tool_id} (legacy param types)")
            return tool_id
    print(f"  ✗ tool {tool_id}: HTTP {r.status_code}  {r.text[:300]}")
    return None


def _create_agent(name: str, instructions: str, tool_ids: list[str], skill_ids: Optional[list[str]] = None) -> Optional[str]:
    _delete(f"/api/agent_builder/agents/{AGENT_ID}")
    config: dict = {"instructions": instructions, "tools": [{"tool_ids": tool_ids}]}
    if skill_ids:
        config["skill_ids"] = skill_ids
    body = {
        "id": AGENT_ID,
        "name": name,
        "description": "MS Build 2026 PR-review agent. Reviews PRs against OTel traces and historical postmortems; posts a PR comment with evidence when a known pattern matches.",
        "configuration": config,
    }
    r = requests.post(f"{KIBANA_URL}/api/agent_builder/agents", headers=HEADERS, json=body, timeout=30)
    if r.status_code in (200, 201):
        agent_id = r.json().get("id") or AGENT_ID
        print(f"  ✓ agent: {agent_id}")
        return agent_id
    print(f"  ✗ agent: HTTP {r.status_code}  {r.text[:400]}")
    return None


INSTRUCTIONS = """You are an AI pull-request reviewer for the Wayfinder Supply Co. codebase. You have access to production OTel telemetry and historical incident postmortems. Your job is to spot a PR that reintroduces a known failure pattern and post a PR comment with concrete evidence before the change merges.

## When invoked on a PR

1. Use the GitHub connector tools to fetch the PR diff and the list of changed files. Read the actual diff — do not guess from the title.
2. Identify the HTTP route or service function the PR modifies (e.g. `/api/v1/checkout/reserve`, `inventory.reserve`). Call that the **target endpoint**.
3. Call the three ES tools to correlate:
   - `find_similar_traces` — for the target endpoint, check whether prior slow/erroring traces exist.
   - `find_latency_spikes` — look for spans on the target endpoint whose duration exceeds a healthy p99 (default 3000000 microseconds).
   - `search_incidents` — search indexed GitHub postmortem issues for patterns that describe what the diff is actually doing. Use pattern terms (e.g. "read-modify-write", "non-atomic update", "lock contention"), not symptom keywords from the diff.
4. Reason in terms of **pattern**, not keyword overlap. The diff may look like a perf/cache refactor; the pattern may be a lost atomic guard. Name the pattern explicitly in your comment.
5. If you find a historical match, post a PR comment using the GitHub connector with:
   - The matched issue number and a one-sentence summary.
   - Specific trace evidence (issue #, endpoint, p99 duration, incident window dates).
   - A plain-English explanation of the pattern connection ("this diff removes the atomic conditional UPDATE; the prior incident happened because…").
   - A concrete suggested change (point at the correct atomic pattern), not a generic warning.
6. If no match is found, do not post a comment. Silence is correct when there is nothing to say.

## Rules

- Be specific. A generic "watch out for race conditions" comment is worthless and must not be posted.
- Cite at least one concrete trace field value (duration, route, timestamp) and at least one concrete issue number whenever you post.
- Never invent data. If a tool returns no results, say so internally and stop.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues-index", default=os.getenv("MSBUILD_ISSUES_INDEX", "github-issues-wayfinder"))
    ap.add_argument("--traces-index", default=TRACES_INDEX)
    args = ap.parse_args()

    print(f"Kibana: {KIBANA_URL}")
    print(f"Traces index: {args.traces_index}")
    print(f"Issues index: {args.issues_index}")
    print()

    tool_ids: list[str] = []

    # Tool 1 — find similar traces for the target endpoint
    tid = _create_esql_tool(
        tool_id="tool-esql-find-similar-traces",
        description="Find OTel traces on a given HTTP route in the last N days. Use to check whether the endpoint the PR touches has prior trace history.",
        query=(
            f'FROM {args.traces_index} '
            f'| WHERE http.route == ?endpoint '
            f'| SORT @timestamp DESC '
            f'| LIMIT 20'
        ),
        params={"endpoint": {"type": "string", "description": "HTTP route to match, e.g. /api/v1/checkout/reserve"}},
    )
    if tid:
        tool_ids.append(tid)

    # Tool 2 — latency spikes
    tid = _create_esql_tool(
        tool_id="tool-esql-find-latency-spikes",
        description="Find spans on a HTTP route whose span.duration.us exceeds a microsecond threshold. Use to surface slow or incident-window traces for the endpoint the PR touches.",
        query=(
            f'FROM {args.traces_index} '
            f'| WHERE http.route == ?endpoint AND span.duration.us > ?threshold_us '
            f'| SORT @timestamp DESC '
            f'| LIMIT 20'
        ),
        params={
            "endpoint": {"type": "string", "description": "HTTP route to match"},
            "threshold_us": {"type": "integer", "description": "Microsecond threshold; 3000000 = 3 seconds"},
        },
    )
    if tid:
        tool_ids.append(tid)

    # Tool 3 — search indexed postmortem issues
    tid = _create_esql_tool(
        tool_id="tool-esql-search-incidents",
        description="Full-text search of ingested GitHub Issues for incident/postmortem patterns. Query with pattern terms, not symptom keywords.",
        query=(
            f'FROM {args.issues_index} '
            f'| WHERE MATCH(body, ?query_terms) '
            f'| SORT _score DESC '
            f'| LIMIT 5'
        ),
        params={"query_terms": {"type": "string", "description": "Full-text query describing the code pattern"}},
    )
    if tid:
        tool_ids.append(tid)

    if len(tool_ids) != 3:
        print(f"\n✗ only {len(tool_ids)}/3 tools created — fix errors above before creating the agent")
        return 1

    # Re-attach skill if it already exists in Kibana
    skill_ids: list[str] = []
    r = requests.get(f"{KIBANA_URL}/api/agent_builder/skills/skill-pr-race-condition-analysis", headers=HEADERS, timeout=30)
    if r.status_code == 200:
        skill_ids = ["skill-pr-race-condition-analysis"]
        print(f"  ↳ skill found, will attach: skill-pr-race-condition-analysis")
    else:
        print(f"  ↳ skill not found — run create_msbuild_skill.py to add it")

    agent_id = _create_agent("MS Build PR Review Agent", INSTRUCTIONS, tool_ids, skill_ids or None)
    if not agent_id:
        return 2

    print()
    print(f"Next steps:")
    print(f"  1. export MSBUILD_AGENT_ID={agent_id}")
    print(f"  2. python3 scripts/create_msbuild_skill.py  (if skill not already attached)")
    print(f"  3. In Kibana, attach a GitHub MCP connector and Azure OpenAI connector to this agent.")
    print(f"  4. python3 scripts/deploy_msbuild_workflow.py  (uses MSBUILD_AGENT_ID from env)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
