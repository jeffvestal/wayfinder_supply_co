#!/usr/bin/env python3
"""
Generate synthetic healthy baseline OTel traces for the inventory-reserve code path.

Per build plan Phase 1B: gamma(2, 20) shape, avg ≈ 40ms, p99 ≈ 137ms, ±15% jitter,
daytime (9am-6pm PT) peak, low traffic nights/weekends, DEMO_DATE - {35,5} days window.

Usage:
  python3 scripts/generate_baseline_traces.py [--count 50000] [--out generated_traces/baseline_traces.jsonl]

Output: JSONL, one span per line. 5 spans per trace.
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


def _time_of_day_multiplier(hour_pt: int, weekday: int) -> float:
    """Peak 9am-6pm PT weekdays; quiet weekends/nights."""
    if weekday >= 5:
        return 0.3
    if 9 <= hour_pt < 18:
        return 1.0
    if 6 <= hour_pt < 9 or 18 <= hour_pt < 22:
        return 0.5
    return 0.15


def iter_baseline(count: int):
    start_window = demo_date() - timedelta(days=35)
    end_window = demo_date() - timedelta(days=5)
    total_seconds = (end_window - start_window).total_seconds()

    generated = 0
    while generated < count:
        t = start_window + timedelta(seconds=random.uniform(0, total_seconds))
        hour_pt = (t.hour - 7) % 24  # UTC → PT (rough, ignores DST)
        weight = _time_of_day_multiplier(hour_pt, t.weekday())
        if random.random() > weight:
            continue

        # gamma(2, 20) → mean 40ms; clip to a sane upper bound
        dur_ms = min(random.gammavariate(2, 20), 350)
        dur_ms *= random.uniform(0.85, 1.15)  # ±15% jitter
        dur_us = int(dur_ms * 1000)

        tid = trace_id()
        root, root_sid = root_span(
            tid=tid,
            start=t,
            duration_us=dur_us,
            http_route=TARGET_ROUTE,
            http_status=200,
        )
        yield root
        for child in child_spans(
            tid=tid,
            parent_sid=root_sid,
            root_start_ns=int(t.timestamp() * 1e9),
            root_duration_us=dur_us,
            http_route=TARGET_ROUTE,
            db_statement=(
                "UPDATE inventory SET quantity = quantity - 1 "
                "WHERE product_id = 'BOOT-001' AND quantity >= 1 RETURNING reservation_id"
            ),
        ):
            yield child
        generated += 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=50_000, help="number of traces (not spans)")
    ap.add_argument("--out", default=str(OUTPUT_DIR / "baseline_traces.jsonl"))
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    path = Path(args.out)
    n = write_jsonl(path, iter_baseline(args.count))
    print(f"wrote {n} spans to {path}  ({n // 5} traces)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
