#!/usr/bin/env python3
"""
Bulk-index trace JSONL into Elasticsearch with an explicit mapping
(dynamic:false, db.statement → text + db.statement_semantic → semantic_text).

SAFE BY DEFAULT: writes to a throwaway verify index `traces-apm.wayfinder-verify-<ts>`.
Use --production to write to `traces-apm.wayfinder-default` (asks confirmation).

Usage:
  python3 scripts/index_traces.py --files generated_traces/baseline_traces.jsonl generated_traces/incident_traces.jsonl
  python3 scripts/index_traces.py --files ... --production
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Iterable

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from _trace_lib import DEFAULT_INDEX, INDEX_MAPPING, VERIFY_INDEX_PREFIX


def _env() -> tuple[str, str]:
    url = os.getenv("OBSERVABILITY_ELASTIC_URL") or os.getenv("ELASTIC_URL")
    key = os.getenv("OBSERVABILITY_ELASTIC_APIKEY") or os.getenv("ELASTIC_API_KEY")
    if not (url and key):
        print("✗ need OBSERVABILITY_ELASTIC_URL + OBSERVABILITY_ELASTIC_APIKEY", file=sys.stderr)
        sys.exit(2)
    return url.rstrip("/"), key


def _ensure_index(url: str, key: str, index: str) -> None:
    h = {"Authorization": f"ApiKey {key}", "Content-Type": "application/json"}
    r = requests.head(f"{url}/{index}", headers=h)
    if r.status_code == 200:
        print(f"  index {index} already exists")
        return
    r = requests.put(f"{url}/{index}", headers=h, json=INDEX_MAPPING)
    if r.status_code not in (200, 201):
        print(f"✗ failed to create {index}: {r.status_code} {r.text[:500]}", file=sys.stderr)
        sys.exit(3)
    print(f"  created index {index}")


def _bulk_batches(lines: Iterable[str], index: str, batch_size: int):
    buf: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        buf.append(json.dumps({"index": {"_index": index}}))
        buf.append(line)
        if len(buf) >= batch_size * 2:
            yield "\n".join(buf) + "\n"
            buf = []
    if buf:
        yield "\n".join(buf) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", nargs="+", required=True)
    ap.add_argument("--index", default=None, help="override target index")
    ap.add_argument("--production", action="store_true", help=f"write to {DEFAULT_INDEX}")
    ap.add_argument("--batch-size", type=int, default=500)
    args = ap.parse_args()

    if args.index:
        index = args.index
    elif args.production:
        print(f"⚠ --production writes to {DEFAULT_INDEX}. Type 'yes' to confirm:")
        if input().strip().lower() != "yes":
            print("aborted")
            return 1
        index = DEFAULT_INDEX
    else:
        index = f"{VERIFY_INDEX_PREFIX}-{int(time.time())}"

    url, key = _env()
    print(f"indexing into {url}/{index}")
    _ensure_index(url, key, index)

    h = {"Authorization": f"ApiKey {key}", "Content-Type": "application/x-ndjson"}

    total_ok = 0
    total_err = 0
    for fpath in args.files:
        p = Path(fpath)
        if not p.exists():
            print(f"  ! missing {fpath}, skipping")
            continue
        with p.open() as f:
            for payload in _bulk_batches(f, index, args.batch_size):
                r = requests.post(f"{url}/_bulk", headers=h, data=payload)
                if r.status_code >= 300:
                    print(f"  ! batch HTTP {r.status_code}: {r.text[:200]}")
                    total_err += 1
                    continue
                body = r.json()
                items = body.get("items", [])
                errs = sum(1 for it in items if next(iter(it.values())).get("error"))
                total_ok += len(items) - errs
                total_err += errs
                if body.get("errors"):
                    # Print first error for visibility
                    for it in items:
                        op = next(iter(it.values()))
                        if op.get("error"):
                            print(f"  ! first error: {op['error'].get('type')}: {op['error'].get('reason','')[:200]}")
                            break

    print(f"indexed ok={total_ok} err={total_err}")
    print(f"index: {index}")
    return 0 if total_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
