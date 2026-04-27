#!/usr/bin/env python3
"""
Generate synthetic incident-window OTel traces showing PostgreSQL deadlock pattern.

Per build plan Phase 1B: DEMO_DATE - 42d, 14:00-17:30 UTC, 4000-6500ms spans, ±500ms jitter,
db.statement contains deadlock error text, root HTTP 504, http.route /api/v1/checkout/reserve.

Usage:
  python3 scripts/generate_incident_traces.py [--count 750] [--out generated_traces/incident_traces.jsonl]
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import timedelta
from pathlib import Path

from _trace_lib import (
    OUTPUT_DIR,
    TARGET_ROUTE,
    child_spans,
    demo_date,
    root_span,
    trace_id,
    write_jsonl,
)

DEADLOCK_STMT_TEMPLATES = [
    "UPDATE inventory SET quantity = {qty} WHERE product_id = 'BOOT-001' "
    "-- ERROR: deadlock detected, Process {pid} waits for ShareLock on transaction {txid}",
    "UPDATE inventory SET quantity = {qty} WHERE product_id = 'BOOT-001' "
    "-- ERROR: canceling statement due to lock timeout after {to_ms}ms on inventory_pkey",
    "UPDATE inventory SET quantity = {qty} WHERE product_id = 'BOOT-001' "
    "-- ERROR: could not serialize access due to concurrent update on row {rowid}",
]


def _stmt() -> str:
    tmpl = random.choice(DEADLOCK_STMT_TEMPLATES)
    return tmpl.format(
        qty=random.randint(1, 10),
        pid=random.randint(10000, 99999),
        txid=random.randint(5000, 12000),
        to_ms=random.randint(3500, 4200),
        rowid=random.randint(1, 5000),
    )


def iter_incident(count: int):
    incident_start = demo_date() - timedelta(days=42)
    incident_start = incident_start.replace(hour=14, minute=0, second=0, microsecond=0)
    incident_end = incident_start.replace(hour=17, minute=30)
    window_seconds = (incident_end - incident_start).total_seconds()

    for _ in range(count):
        t = incident_start + timedelta(seconds=random.uniform(0, window_seconds))
        # 4000-6500ms with ±500ms jitter around the midpoint of the band per-trace
        base_ms = random.uniform(4000, 6500)
        dur_ms = base_ms + random.uniform(-500, 500)
        dur_ms = max(3500, dur_ms)  # clip; don't go below the lock timeout
        dur_us = int(dur_ms * 1000)

        tid = trace_id()
        root, root_sid = root_span(
            tid=tid,
            start=t,
            duration_us=dur_us,
            http_route=TARGET_ROUTE,
            http_status=504,
        )
        yield root
        for child in child_spans(
            tid=tid,
            parent_sid=root_sid,
            root_start_ns=int(t.timestamp() * 1e9),
            root_duration_us=dur_us,
            http_route=TARGET_ROUTE,
            db_statement=_stmt(),
        ):
            yield child


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=750, help="incident trace count")
    ap.add_argument("--out", default=str(OUTPUT_DIR / "incident_traces.jsonl"))
    ap.add_argument("--seed", type=int, default=1337)
    args = ap.parse_args()

    random.seed(args.seed)
    path = Path(args.out)
    n = write_jsonl(path, iter_incident(args.count))
    print(f"wrote {n} spans to {path}  ({n // 5} traces)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
