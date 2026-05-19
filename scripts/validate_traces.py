#!/usr/bin/env python3
"""
Validate indexed traces (7 checks):
  1. Non-zero doc count
  2. @timestamp range falls inside [DEMO_DATE - 60d, DEMO_DATE + 1d]
  3. traces-per-trace_id ≈ 5 (one root + four children)
  4. baseline p99 latency < 500ms
  5. incident-window has >0 spans with duration > 3000ms
  6. db.statement field is populated on >0 non-root spans
  7. http.route is present on every doc (required for ES|QL demo query 1)

Usage:
  python3 scripts/validate_traces.py [--index traces-apm.wayfinder-verify-NNN]
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


def _check(name: str, ok: bool, detail: str = "") -> bool:
    mark = "✓" if ok else "✗"
    print(f"  {mark} {name}  {detail}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=DEFAULT_INDEX)
    args = ap.parse_args()

    url, key = _env()
    h = {"Authorization": f"ApiKey {key}", "Content-Type": "application/json"}
    index = args.index
    results: list[bool] = []

    # 1. doc count
    r = requests.get(f"{url}/{index}/_count", headers=h)
    count = r.json().get("count", 0) if r.status_code == 200 else 0
    results.append(_check("doc count > 0", count > 0, f"count={count}"))

    # 2. timestamp range
    lo = (demo_date() - timedelta(days=60)).isoformat()
    hi = (demo_date() + timedelta(days=1)).isoformat()
    q = {
        "size": 0,
        "aggs": {
            "mn": {"min": {"field": "@timestamp"}},
            "mx": {"max": {"field": "@timestamp"}},
        },
    }
    r = requests.post(f"{url}/{index}/_search", headers=h, json=q)
    if r.status_code == 200:
        aggs = r.json().get("aggregations", {})
        mn = aggs.get("mn", {}).get("value_as_string", "")
        mx = aggs.get("mx", {}).get("value_as_string", "")
        in_range = mn >= lo and mx <= hi
        results.append(_check("timestamps within demo window", in_range, f"[{mn} .. {mx}]"))
    else:
        results.append(_check("timestamps within demo window", False, f"query HTTP {r.status_code}"))

    # 3. spans-per-trace ≈ 5
    q = {
        "size": 0,
        "aggs": {
            "traces": {
                "terms": {"field": "trace.id", "size": 200},
                "aggs": {"nspans": {"value_count": {"field": "span.id"}}},
            },
        },
    }
    r = requests.post(f"{url}/{index}/_search", headers=h, json=q)
    if r.status_code == 200:
        buckets = r.json().get("aggregations", {}).get("traces", {}).get("buckets", [])
        if buckets:
            avg = sum(b["nspans"]["value"] for b in buckets) / len(buckets)
            results.append(_check("avg spans per trace ≈ 5", 4 <= avg <= 6, f"avg={avg:.2f}"))
        else:
            results.append(_check("avg spans per trace ≈ 5", False, "no buckets"))
    else:
        results.append(_check("avg spans per trace ≈ 5", False, f"HTTP {r.status_code}"))

    # 4. baseline p99 < 500ms (exclude incident window)
    incident_lo = (demo_date() - timedelta(days=43)).isoformat()
    incident_hi = (demo_date() - timedelta(days=41)).isoformat()
    q = {
        "size": 0,
        "query": {
            "bool": {
                "must": [{"term": {"http.route": "/api/v1/checkout/reserve"}}],
                "must_not": [{"range": {"@timestamp": {"gte": incident_lo, "lte": incident_hi}}}],
                "filter": [{"term": {"processor.event": "transaction"}}],
            }
        },
        "aggs": {"p99": {"percentiles": {"field": "span.duration.us", "percents": [99]}}},
    }
    r = requests.post(f"{url}/{index}/_search", headers=h, json=q)
    if r.status_code == 200:
        pct = r.json().get("aggregations", {}).get("p99", {}).get("values", {})
        p99_us = list(pct.values())[0] if pct else None
        if p99_us is None:
            results.append(_check("baseline p99 < 500ms", False, "no data"))
        else:
            p99_ms = p99_us / 1000
            results.append(_check("baseline p99 < 500ms", p99_ms < 500, f"p99={p99_ms:.1f}ms"))
    else:
        results.append(_check("baseline p99 < 500ms", False, f"HTTP {r.status_code}"))

    # 5. incident window has slow spans
    # Note: Serverless ES rejects `size` in _count body — use query-only body
    q = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": incident_lo, "lte": incident_hi}}},
                    {"range": {"span.duration.us": {"gt": 3_000_000}}},
                ]
            }
        },
    }
    r = requests.post(f"{url}/{index}/_count", headers=h, json=q)
    n = r.json().get("count", 0) if r.status_code == 200 else 0
    results.append(_check("incident window has spans >3000ms", n > 0, f"n={n}"))

    # 6. db.statement populated
    q = {"query": {"exists": {"field": "db.statement"}}}
    r = requests.post(f"{url}/{index}/_count", headers=h, json=q)
    n = r.json().get("count", 0) if r.status_code == 200 else 0
    results.append(_check("db.statement populated", n > 0, f"n={n}"))

    # 7. http.route present on every doc
    q = {"query": {"bool": {"must_not": [{"exists": {"field": "http.route"}}]}}}
    r = requests.post(f"{url}/{index}/_count", headers=h, json=q)
    missing = r.json().get("count", 0) if r.status_code == 200 else -1
    results.append(_check("http.route on every doc", missing == 0, f"missing={missing}"))

    passed = all(results)
    print(f"\n{'PASS' if passed else 'FAIL'}: {sum(results)}/{len(results)} checks")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
