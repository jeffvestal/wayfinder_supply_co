#!/usr/bin/env python3
"""ES|QL smoke tests for otel-traces-wayfinder index.

Verifies both queries from the demo spec return > 0 rows after indexing.

Usage:
    ELASTIC_URL=... ELASTIC_API_KEY=... python scripts/verify_esql_search.py
"""

import os
import sys

from elasticsearch import Elasticsearch

INDEX_NAME = "otel-traces-wayfinder"

QUERIES = [
    {
        "name": "Incident traces by slow duration (Query 1)",
        "query": (
            'FROM otel-traces-wayfinder\n'
            '| WHERE http.route == "/api/v1/checkout/reserve"\n'
            '  AND span.duration.us > 3000000\n'
            '  AND @timestamp >= "2026-04-07T00:00:00Z"\n'
            '  AND @timestamp <= "2026-04-08T00:00:00Z"\n'
            '| SORT @timestamp DESC\n'
            '| LIMIT 10'
        ),
        "min_rows": 1,
    },
    {
        "name": "Deadlock traces via MATCH on db.statement (Query 2)",
        "query": (
            'FROM otel-traces-wayfinder\n'
            '| WHERE MATCH(db.statement, "lock deadlock concurrent")\n'
            '| SORT @timestamp DESC\n'
            '| LIMIT 5'
        ),
        "min_rows": 1,
    },
]


def get_client():
    url = os.environ.get("ELASTIC_URL")
    api_key = os.environ.get("ELASTIC_API_KEY")
    if not url:
        sys.exit("ERROR: ELASTIC_URL env var is required")
    if not api_key:
        sys.exit("ERROR: ELASTIC_API_KEY env var is required")
    return Elasticsearch(url, api_key=api_key)


def run_esql(es, query_str):
    resp = es.esql.query(query=query_str)
    return resp.get("values", [])


def main():
    es = get_client()
    failures = 0

    print(f"ES|QL smoke tests: {INDEX_NAME}\n")

    for q in QUERIES:
        print(f"  {q['name']}")
        first_line = q["query"].splitlines()[0]
        print(f"  {first_line} ...")
        try:
            rows = run_esql(es, q["query"])
            count = len(rows)
            passed = count >= q["min_rows"]
            mark = "PASS" if passed else "FAIL"
            print(f"  [{mark}] {count} row(s) returned (need >= {q['min_rows']})")
            if not passed:
                failures += 1
        except Exception as exc:
            print(f"  [ERROR] {exc}")
            failures += 1
        print()

    if failures == 0:
        print("All smoke tests PASSED.")
    else:
        print(f"{failures} smoke test(s) FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
