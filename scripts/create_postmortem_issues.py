#!/usr/bin/env python3
"""
Create / update the two postmortem GitHub Issues the MS Build demo agent searches.

Idempotent: looks for an existing open issue with the same title before creating.
Uses the `gh` CLI so auth / repo detection comes from the user's environment.

Issues (from MS Build build plan Phase 1C):
  #1  [INCIDENT] inventory-service: checkout degradation
  #2  [POST-MORTEM] inventory.reserve race condition — lessons learned

Dates are anchored to DEMO_DATE - 42 days so the story lines up with the incident trace window.

Usage:
  python3 scripts/create_postmortem_issues.py                # create if missing
  python3 scripts/create_postmortem_issues.py --force        # always create a fresh pair
  python3 scripts/create_postmortem_issues.py --print        # print bodies without touching GitHub
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _trace_lib import demo_date


def _incident_window() -> tuple[str, str]:
    start = (demo_date() - timedelta(days=42)).replace(hour=14, minute=0, second=0, microsecond=0)
    end = start.replace(hour=17, minute=30)
    return start.strftime("%Y-%m-%d %H:%M"), end.strftime("%H:%M UTC")


def issue_one() -> tuple[str, str, list[str]]:
    start, end = _incident_window()
    title = f"[INCIDENT] inventory-service: checkout degradation {start}–{end}"
    body = f"""## Summary
~23% of `/api/v1/checkout/reserve` requests returned HTTP 504 between {start} and {end}.
PostgreSQL lock contention on the inventory table caused cascading timeouts under concurrent load (>50 rps).

## Impact
- Checkout success rate dropped from 99.7% → 76.9%
- p99 latency on `inventory.reserve`: 137ms → 6.2s peak
- 847 lock-contention events in 3.5 hours

## Detection
Elastic Observability alerted on `http.route:"/api/v1/checkout/reserve"` p99 > 2000ms. OTel traces show `db.write` span durations 4-6s with lock-timeout errors on the `db.statement` field.

## Root Cause
A recent refactor split the atomic `UPDATE ... WHERE quantity >= ?` into two operations:
1. `SELECT quantity FROM inventory WHERE product_id = ?`
2. `UPDATE inventory SET quantity = ? WHERE product_id = ?` (unconditional)

Between (1) and (2), concurrent requests can observe the same `quantity`, each reserves, and the final `UPDATE` overwrites intermediate decrements. The resulting contention on the row-level lock caused cascading timeouts.

## Fix
Reverted to a single conditional `UPDATE inventory SET quantity = quantity - ? WHERE product_id = ? AND quantity >= ?`. Atomic guard prevents oversell and eliminates the read-then-write window.

## Evidence
- ES\\|QL query:
  ```
  FROM traces-apm.wayfinder-default
  | WHERE http.route == "/api/v1/checkout/reserve"
    AND event.duration > 3000000000
  ```
- Kibana Observability APM dashboard (inventory-service, incident window)

## Prevention
- Added load test to CI covering 100 concurrent reservation requests
- Added semantic alert on `db.statement` containing deadlock/lock-timeout patterns
"""
    labels = ["incident", "postmortem", "p1"]
    return title, body, labels


def issue_two() -> tuple[str, str, list[str]]:
    title = "[POST-MORTEM] inventory.reserve race condition — lessons learned"
    body = """## What broke
A read-modify-write pattern in `inventory.reserve()` without transaction isolation: the code `SELECT`ed the quantity, computed `new_quantity = current - n` in application code, then wrote back the absolute value with an unconditional `UPDATE`. Under concurrent load the read window allowed two requests to observe the same stock, both reserve, and the final write to clobber an earlier decrement.

## Why it wasn't caught
- Unit tests issue requests serially; the race only appears under concurrency (>50 rps on a single hot product_id).
- The PR description framed the change as a query-plan-cache optimization. No reviewer flagged the loss of the `WHERE quantity >= n` guard.
- Integration tests stub the database and don't exercise real lock behaviour.

## Metrics at peak
- p99 latency: 6.2s
- Error rate: 23%
- Lock contention events: 847 over 3.5 hours

## Code pattern to avoid
```python
# DO NOT: read-then-unconditional-write
current = db.execute("SELECT quantity FROM inventory WHERE product_id = ?", pid)
new = current - qty
db.execute("UPDATE inventory SET quantity = ? WHERE product_id = ?", new, pid)
```

## Code pattern to use
```python
# Atomic: conditional UPDATE; fails cleanly if stock is gone at write time
rows = db.execute(
    "UPDATE inventory SET quantity = quantity - ? "
    "WHERE product_id = ? AND quantity >= ? RETURNING reservation_id",
    qty, pid, qty,
)
```

## Detection gap
Semantic alerting on span attribute patterns (e.g. `db.statement` containing lock-timeout / deadlock text OR span durations shifting above a learned baseline) would have fired inside the first 5 minutes of the incident.

## Related
- Incident report: #ISSUE_1_NUMBER
"""
    labels = ["postmortem", "engineering"]
    return title, body, labels


def _find_existing(title: str) -> str | None:
    r = subprocess.run(
        ["gh", "issue", "list", "--state", "all", "--search", f'"{title}" in:title', "--json", "number,title"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return None
    try:
        for it in json.loads(r.stdout or "[]"):
            if it["title"] == title:
                return str(it["number"])
    except Exception:
        pass
    return None


def _create(title: str, body: str, labels: list[str]) -> str | None:
    args = ["gh", "issue", "create", "--title", title, "--body", body]
    for lbl in labels:
        args += ["--label", lbl]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ✗ create failed: {r.stderr.strip()}")
        return None
    line = (r.stdout.strip().splitlines() or [""])[-1]
    num = line.rsplit("/", 1)[-1]
    return num


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="always create a fresh pair (even if title match exists)")
    ap.add_argument("--print", dest="print_only", action="store_true", help="print bodies, do not create")
    args = ap.parse_args()

    t1, b1, l1 = issue_one()
    t2, b2, _l2 = issue_two()

    if args.print_only:
        print("=" * 60, t1, "=" * 60, b1, sep="\n")
        print("=" * 60, t2, "=" * 60, b2, sep="\n")
        return 0

    # Issue 1
    existing = None if args.force else _find_existing(t1)
    if existing:
        print(f"  · issue 1 already present: #{existing}")
        num1 = existing
    else:
        print("  → creating issue 1")
        num1 = _create(t1, b1, l1)
        if not num1:
            return 1
        print(f"    created #{num1}")

    # Issue 2 — substitute back-reference to issue 1
    b2 = b2.replace("#ISSUE_1_NUMBER", f"#{num1}")
    t2_labels = ["postmortem", "engineering"]
    existing = None if args.force else _find_existing(t2)
    if existing:
        print(f"  · issue 2 already present: #{existing}")
    else:
        print("  → creating issue 2")
        num2 = _create(t2, b2, t2_labels)
        if not num2:
            return 1
        print(f"    created #{num2}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
