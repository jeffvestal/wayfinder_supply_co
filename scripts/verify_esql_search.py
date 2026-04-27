#!/usr/bin/env python3
"""
Run the two ES|QL demo queries against an index and assert non-empty results.

Queries (from MS Build memory):
  Q1: FROM {idx} | WHERE http.route == "/api/v1/checkout/reserve"
      AND event.duration > 3000000000 AND @timestamp >= DEMO_DATE-42d
  Q2: FROM {idx} | WHERE MATCH(db.statement, "lock deadlock concurrent")

Usage:
  python3 scripts/verify_esql_search.py [--index traces-apm.wayfinder-default]
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import timedelta

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from _trace_lib import DEFAULT_INDEX, demo_date


def _env() -> tuple[str, str]:
    url = os.getenv("OBSERVABILITY_ELASTIC_URL") or os.getenv("ELASTIC_URL")
    key = os.getenv("OBSERVABILITY_ELASTIC_APIKEY") or os.getenv("ELASTIC_API_KEY")
    if not (url and key):
        print("need OBSERVABILITY_ELASTIC_URL + _APIKEY", file=sys.stderr)
        sys.exit(2)
    return url.rstrip("/"), key


def _run(url: str, key: str, query: str) -> int:
    r = requests.post(
        f"{url}/_query",
        headers={"Authorization": f"ApiKey {key}", "Content-Type": "application/json"},
        json={"query": query},
    )
    if r.status_code != 200:
        print(f"  HTTP {r.status_code}: {r.text[:400]}")
        return -1
    body = r.json()
    values = body.get("values", [])
    return len(values)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=DEFAULT_INDEX)
    args = ap.parse_args()

    url, key = _env()
    incident_start = (demo_date() - timedelta(days=43)).isoformat()

    q1 = (
        f'FROM {args.index} | WHERE http.route == "/api/v1/checkout/reserve" '
        f'AND event.duration > 3000000000 AND @timestamp >= "{incident_start}" '
        f'| LIMIT 10'
    )
    q2 = f'FROM {args.index} | WHERE MATCH(db.statement, "lock deadlock concurrent") | LIMIT 10'

    print("Q1 (slow reserves during incident window):")
    print(f"  {q1}")
    n1 = _run(url, key, q1)
    print(f"  → rows: {n1}")

    print("Q2 (semantic match on db.statement for deadlock):")
    print(f"  {q2}")
    n2 = _run(url, key, q2)
    print(f"  → rows: {n2}")

    ok = n1 > 0 and n2 > 0
    print(f"\n{'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
