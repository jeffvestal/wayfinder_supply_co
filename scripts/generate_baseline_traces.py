#!/usr/bin/env python3
"""Generate ~50,000 baseline OTel traces for Wayfinder Supply Co demo.

Baseline window: 30 days before the incident (2026-03-08 → 2026-04-06).
Realistic daytime/weekday load pattern; inventory.reserve avg ~40ms, p99 < 200ms.
"""

import argparse
import json
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEMO_DATE_DEFAULT = "2026-05-19"
INCIDENT_OFFSET_DAYS = 42  # incident = DEMO_DATE - 42d = 2026-04-07
BASELINE_DAYS = 30
TARGET_TRACES = 50_000
SPANS_PER_TRACE = 5

SKUS = [
    "WF-TRAIL-BOOT-001",
    "WF-SLEEPING-BAG-002",
    "WF-TENT-003",
    "WF-BACKPACK-004",
    "WF-JACKET-005",
    "WF-HEADLAMP-006",
    "WF-WATER-FILTER-007",
    "WF-TREKKING-POLES-008",
    "WF-CAMP-STOVE-009",
    "WF-FIRST-AID-010",
    "WF-CRAMPONS-011",
    "WF-GAITERS-012",
    "WF-INSULATED-FLASK-013",
    "WF-SUNGLASSES-014",
    "WF-COMPASS-015",
]

WAREHOUSES = [1, 2, 3, 4, 5]


def parse_args():
    p = argparse.ArgumentParser(description="Generate baseline OTel traces")
    p.add_argument("--demo-date", default=os.environ.get("DEMO_DATE", DEMO_DATE_DEFAULT))
    p.add_argument("--output", default="generated_traces/baseline_traces.jsonl")
    p.add_argument("--count", type=int, default=TARGET_TRACES)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def new_trace_id():
    return uuid.uuid4().hex  # 32 hex chars


def new_span_id():
    return uuid.uuid4().hex[:16]  # 16 hex chars


def hour_weight(dt_utc):
    """Business-hours weight. Peak 9am-6pm PDT (UTC-7)."""
    pdt_hour = (dt_utc.hour - 7) % 24
    if 9 <= pdt_hour <= 17:
        return 1.0
    if 7 <= pdt_hour < 9 or 18 <= pdt_hour <= 20:
        return 0.4
    return 0.08


def sample_timestamp(rng, window_start_ts, window_end_ts):
    """Rejection-sample a timestamp weighted by business hours and weekday."""
    while True:
        ts = rng.uniform(window_start_ts, window_end_ts)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        weight = hour_weight(dt) * (0.3 if dt.weekday() >= 5 else 1.0)
        if rng.random() < weight:
            return dt


def format_ts(dt, extra_us=0):
    """Format datetime as date_nanos ISO string (nanosecond precision)."""
    total_us = int(dt.timestamp() * 1_000_000) + extra_us
    sec = total_us // 1_000_000
    us = total_us % 1_000_000
    base = datetime.fromtimestamp(sec, tz=timezone.utc)
    return base.strftime(f"%Y-%m-%dT%H:%M:%S.{us * 1000:09d}Z")


def reserve_duration_us(rng, seen_durs):
    """Duration for inventory.reserve span. Avg ~40ms, p99 < 200ms. Guaranteed unique."""
    while True:
        base_ms = rng.gammavariate(2, 20)
        jitter = rng.gauss(0, base_ms * 0.15)
        candidate = int(max(1_000, min((base_ms + jitter) * 1000, 195_000)))
        if candidate not in seen_durs:
            seen_durs.add(candidate)
            return candidate
        # Collision: walk ±1µs until unique
        for delta in range(1, 500):
            for c in (candidate + delta, candidate - delta):
                if 1_000 <= c <= 195_000 and c not in seen_durs:
                    seen_durs.add(c)
                    return c


def make_db_stmt(sku, warehouse, qty):
    return (
        f"SELECT sku, quantity, reserved_until FROM inventory "
        f"WHERE sku = '{sku}' AND warehouse_id = {warehouse} FOR UPDATE NOWAIT; "
        f"UPDATE inventory SET quantity = quantity - {qty}, "
        f"reserved_until = NOW() + INTERVAL '15 minutes' "
        f"WHERE sku = '{sku}' AND warehouse_id = {warehouse}"
    )


def build_trace(rng, root_ts, seen_durs):
    """Build all 5 spans for one healthy trace."""
    tid = new_trace_id()
    root_id = new_span_id()
    checkout_id = new_span_id()
    reserve_id = new_span_id()
    dbq_id = new_span_id()
    dbw_id = new_span_id()

    sku = rng.choice(SKUS)
    wh = rng.choice(WAREHOUSES)
    qty_req = rng.randint(1, 5)
    qty_avail = rng.randint(0, 50)
    db_stmt = make_db_stmt(sku, wh, qty_req)

    res_dur = reserve_duration_us(rng, seen_durs)
    dbq_dur = int(res_dur * rng.uniform(0.25, 0.35))
    dbw_dur = int(res_dur * rng.uniform(0.35, 0.45))
    chk_dur = int(res_dur * rng.uniform(1.05, 1.15))
    root_dur = int(chk_dur * rng.uniform(1.05, 1.12))

    # Span start offsets (microseconds from root start)
    net1 = int(rng.uniform(500, 2000))
    net2 = int(rng.uniform(300, 1000))
    db_start = int(rng.uniform(200, 800))
    db_gap = int(rng.uniform(200, 500))

    http_route = "/api/v1/checkout/reserve"
    http_fields = {"route": http_route, "response": {"status_code": 200}}
    status_ok = {"code": 1, "message": "OK"}
    tx = {"id": root_id, "type": "request"}

    def ts(offset):
        return format_ts(root_ts, offset)

    return [
        {
            "@timestamp": ts(0),
            "trace": {"id": tid},
            "span": {"id": root_id, "name": "POST /checkout", "type": "request", "subtype": "http", "action": "POST", "duration": {"us": root_dur}},
            "service": {"name": "frontend"},
            "http": http_fields,
            "status": status_ok,
            "transaction": tx,
        },
        {
            "@timestamp": ts(net1),
            "trace": {"id": tid},
            "span": {"id": checkout_id, "name": "checkout.process", "type": "request", "subtype": "http", "action": "POST", "duration": {"us": chk_dur}},
            "parent": {"id": root_id},
            "service": {"name": "checkout-service"},
            "http": http_fields,
            "status": status_ok,
            "transaction": tx,
        },
        {
            "@timestamp": ts(net1 + net2),
            "trace": {"id": tid},
            "span": {"id": reserve_id, "name": "inventory.reserve", "type": "request", "subtype": "grpc", "action": "reserve", "duration": {"us": res_dur}},
            "parent": {"id": checkout_id},
            "service": {"name": "inventory-service"},
            "http": http_fields,
            "status": status_ok,
            "transaction": tx,
            "inventory": {"quantity_requested": qty_req, "quantity_available": qty_avail},
        },
        {
            "@timestamp": ts(net1 + net2 + db_start),
            "trace": {"id": tid},
            "span": {"id": dbq_id, "name": "db.query", "type": "db", "subtype": "postgresql", "action": "query", "duration": {"us": dbq_dur}},
            "parent": {"id": reserve_id},
            "service": {"name": "inventory-service"},
            "http": http_fields,
            "status": status_ok,
            "transaction": tx,
            "db": {"statement": db_stmt, "statement_semantic": db_stmt, "type": "sql", "system": "postgresql"},
        },
        {
            "@timestamp": ts(net1 + net2 + db_start + dbq_dur + db_gap),
            "trace": {"id": tid},
            "span": {"id": dbw_id, "name": "db.write", "type": "db", "subtype": "postgresql", "action": "write", "duration": {"us": dbw_dur}},
            "parent": {"id": reserve_id},
            "service": {"name": "inventory-service"},
            "http": http_fields,
            "status": status_ok,
            "transaction": tx,
            "db": {"statement": db_stmt, "statement_semantic": db_stmt, "type": "sql", "system": "postgresql"},
        },
    ]


def main():
    args = parse_args()
    demo_date = datetime.strptime(args.demo_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    incident_date = demo_date - timedelta(days=INCIDENT_OFFSET_DAYS)
    baseline_end = incident_date - timedelta(days=1)           # 2026-04-06
    baseline_start = baseline_end - timedelta(days=BASELINE_DAYS)  # 2026-03-07

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    window_start = baseline_start.timestamp()
    window_end = baseline_end.timestamp()
    seen_durs: set = set()

    print(f"Demo date:     {demo_date.date()}")
    print(f"Incident date: {incident_date.date()}")
    print(f"Baseline:      {baseline_start.date()} → {baseline_end.date()}")
    print(f"Generating {args.count:,} traces (~{args.count * SPANS_PER_TRACE:,} span docs) ...")

    with output_path.open("w") as f:
        for i in range(args.count):
            root_ts = sample_timestamp(rng, window_start, window_end)
            for span in build_trace(rng, root_ts, seen_durs):
                f.write(json.dumps(span) + "\n")
            if (i + 1) % 5000 == 0:
                print(f"  {i + 1:,} / {args.count:,}")

    print(f"Done: {args.count:,} traces, {args.count * SPANS_PER_TRACE:,} span docs → {output_path}")


if __name__ == "__main__":
    main()
