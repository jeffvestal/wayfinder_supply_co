#!/usr/bin/env python3
"""
Fetch open GitHub issues from the Wayfinder Supply Co repo and index them
into Elasticsearch (github-issues-wayfinder) with semantic_text for hybrid search.

Uses the gh CLI for GitHub access and STANDALONE_ELASTICSEARCH_* env vars for ES.

Usage:
  python3 scripts/seed_github_issues.py
  python3 scripts/seed_github_issues.py --limit 50
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

INDEX = "github-issues-wayfinder"

MAPPING = {
    "mappings": {
        "properties": {
            "number":     {"type": "integer"},
            "title":      {"type": "text"},
            "body":       {"type": "text"},
            "labels":     {"type": "keyword"},
            "state":      {"type": "keyword"},
            "created_at": {"type": "date"},
            "url":        {"type": "keyword"},
            "semantic_body": {
                "type": "semantic_text",
                "inference_id": ".jina-embeddings-v5-text-small",
            },
        }
    }
}


def _es_headers(key: str) -> dict:
    return {"Authorization": f"ApiKey {key}", "Content-Type": "application/json"}


def ensure_index(es_url: str, key: str) -> None:
    r = requests.get(f"{es_url}/{INDEX}", headers=_es_headers(key), timeout=10)
    if r.status_code == 200:
        print(f"  ✓ index {INDEX} already exists")
        return
    r2 = requests.put(f"{es_url}/{INDEX}", headers=_es_headers(key), json=MAPPING, timeout=15)
    if r2.status_code in (200, 201):
        print(f"  ✓ created index {INDEX}")
    else:
        print(f"  ✗ failed to create index: {r2.text[:300]}")
        sys.exit(1)


def fetch_issues(repo: str, limit: int) -> list[dict]:
    result = subprocess.run(
        ["gh", "issue", "list", "--repo", repo, "--state", "all",
         "--limit", str(limit), "--json", "number,title,body,labels,state,createdAt,url"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def index_issues(es_url: str, key: str, issues: list[dict]) -> None:
    bulk_lines = []
    for issue in issues:
        doc = {
            "number":     issue["number"],
            "title":      issue["title"],
            "body":       issue.get("body") or "",
            "labels":     [l["name"] for l in issue.get("labels", [])],
            "state":      issue["state"],
            "created_at": issue["createdAt"],
            "url":        issue["url"],
            "semantic_body": f"{issue['title']}\n\n{issue.get('body') or ''}",
        }
        bulk_lines.append(json.dumps({"index": {"_index": INDEX, "_id": str(issue["number"])}}))
        bulk_lines.append(json.dumps(doc))

    body = "\n".join(bulk_lines) + "\n"
    r = requests.post(
        f"{es_url}/_bulk",
        headers={**_es_headers(key), "Content-Type": "application/x-ndjson"},
        data=body.encode(),
        timeout=60,
    )
    if r.status_code not in (200, 201):
        print(f"  ✗ bulk index failed: {r.text[:300]}")
        sys.exit(1)
    result = r.json()
    errors = [i for i in result.get("items", []) if i.get("index", {}).get("error")]
    print(f"  ✓ indexed {len(issues)} issues ({len(errors)} errors)")
    for e in errors:
        print(f"    error: {e}")


def verify_search(es_url: str, key: str) -> None:
    import time; time.sleep(2)
    query = {
        "query": {
            "semantic": {
                "field": "semantic_body",
                "query": "inventory reserve concurrent lock contention"
            }
        },
        "_source": ["number", "title"],
        "size": 5
    }
    r = requests.post(f"{es_url}/{INDEX}/_search", headers=_es_headers(key), json=query, timeout=30)
    if r.status_code != 200:
        print(f"  ⚠ semantic search test failed: {r.status_code} {r.text[:200]}")
        return
    hits = r.json().get("hits", {}).get("hits", [])
    print(f"  Semantic search 'inventory reserve concurrent lock contention' → {len(hits)} hits:")
    for h in hits:
        print(f"    #{h['_source']['number']}: {h['_source']['title'][:80]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.getenv("GITHUB_REPO", "jeffvestal/wayfinder_supply_co"))
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()

    es_url = (os.getenv("STANDALONE_ELASTICSEARCH_URL") or "").rstrip("/")
    key = os.getenv("STANDALONE_ELASTICSEARCH_APIKEY", "")
    if not es_url or not key:
        print("✗ STANDALONE_ELASTICSEARCH_URL and STANDALONE_ELASTICSEARCH_APIKEY required")
        sys.exit(1)

    print(f"Fetching issues from {args.repo}...")
    issues = fetch_issues(args.repo, args.limit)
    print(f"  fetched {len(issues)} issues")

    print(f"\nEnsuring index {INDEX}...")
    ensure_index(es_url, key)

    print(f"\nIndexing {len(issues)} issues...")
    index_issues(es_url, key, issues)

    print(f"\nVerifying semantic search...")
    verify_search(es_url, key)
    print("\nDone.")


if __name__ == "__main__":
    main()
