#!/usr/bin/env python3
"""Generate ~750 incident OTel traces for Wayfinder Supply Co demo.

Incident window: 2026-04-07 14:00–17:30 UTC (DEMO_DATE - 42d).
PostgreSQL deadlock errors, inventory.reserve spans 4000–6500ms, root returns HTTP 504.
"""

import argparse
import json
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEMO_DATE_DEFAULT = "2026-05-19"
INCIDENT_OFFSET_DAYS = 42
INCIDENT_START_HOUR = 14   # 14:00 UTC
INCIDENT_END_HOUR = 17
INCIDENT_END_MINUTE = 30   # 17:30 UTC
TARGET_TRACES = 750
SPANS_PER_TRACE = 5


def parse_args():
    p = argparse.ArgumentParser(description="Generate incident OTel traces (deadlock window)")
    p.add_argument("--demo-date", default=os.environ.get("DEMO_DATE", DEMO_DATE_DEFAULT))
    p.add_argument("--output", default="generated_traces/incident_traces.jsonl")
    p.add_argument("--count", type=int, default=TARGET_TRACES)
    p.add_argument("--seed", type=int, default=99)
    return p.parse_args()


def new_trace_id():
    return uuid.uuid4().hex


def new_span_id():
    return uuid.uuid4().hex[:16]


def format_ts(dt, extra_us=0):
    """Format datetime as date_nanos ISO string (nanosecond precision)."""
    total_us = int(dt.timestamp() * 1_000_000) + extra_us
    sec = total_us // 1_000_000
    us = total_us % 1_000_000
    base = datetime.fromtimestamp(sec, tz=timezone.utc)
    return base.strftime(f"%Y-%m-%dT%H:%M:%S.{us * 1000:09d}Z")


def reserve_duration_us(rng, seen_durs):
    """Duration for incident inventory.reserve span. 4000–6500ms + jitter. Guaranteed unique."""
    while True:
        base_ms = rng.uniform(4000, 6500)
        jitter = rng.gauss(0, 150)
        candidate = int(max(3_500_000, (base_ms + jitter) * 1000))
        if candidate not in seen_durs:
            seen_durs.add(candidate)
            return candidate
        for delta in range(1, 500):
            for c in (candidate + delta, candidate - delta):
                if c >= 3_500_000 and c not in seen_durs:
                    seen_durs.add(c)
                    return c


def make_deadlock_stmt(rng):
    """PostgreSQL deadlock error text with varied process/transaction IDs.

    Contains 'lock', 'deadlock', 'concurrent' — required for MATCH() query.
    """
    pid1 = rng.randint(12000, 15000)
    pid2 = rng.randint(12000, 15000)
    while pid2 == pid1:
        pid2 = rng.randint(12000, 15000)
    tid1 = rng.randint(9000, 11000)
    tid2 = rng.randint(9000, 11000)
    page = rng.randint(0, 8191)
    offset = rng.randint(1, 255)
    sku_num = rng.randint(1, 15)
    wh = rng.randint(1, 5)
    qty = rng.randint(1, 5)
    return (
        f"UPDATE inventory SET quantity = quantity - {qty} "
        f"WHERE sku = 'WF-BACKPACK-{sku_num:03d}' AND warehouse_id = {wh}; "
        f"ERROR: deadlock detected\n"
        f"DETAIL: Process {pid1} waits for ShareLock on transaction {tid1}; "
        f"blocked by process {pid2}.\n"
        f"Process {pid2} waits for ShareLock on transaction {tid2}; "
        f"blocked by process {pid1}.\n"
        f"HINT: See server log for query details. "
        f"Concurrent update conflict on inventory table.\n"
        f"CONTEXT: while updating tuple ({page},{offset}) in relation \"inventory\""
    )


def build_incident_trace(rng, root_ts, seen_durs):
    """Build all 5 spans for one incident trace (deadlock / HTTP 504)."""
    tid = new_trace_id()
    root_id = new_span_id()
    checkout_id = new_span_id()
    reserve_id = new_span_id()
    dbq_id = new_span_id()
    dbw_id = new_span_id()

    db_stmt = make_deadlock_stmt(rng)
    res_dur = reserve_duration_us(rng, seen_durs)

    # DB spans show cascading timeout: SELECT hung waiting for lock, UPDATE deadlocked
    dbq_dur = int(res_dur * rng.uniform(0.55, 0.65))
    dbw_dur = int(res_dur * rng.uniform(0.30, 0.40))
    chk_dur = int(res_dur * rng.uniform(1.02, 1.06))
    root_dur = int(chk_dur * rng.uniform(1.02, 1.05))

    net1 = int(rng.uniform(500, 2000))
    net2 = int(rng.uniform(300, 1000))
    db_start = int(rng.uniform(500, 2000))
    db_gap = int(rng.uniform(200, 500))

    lock_timeout_us = int(rng.gauss(3_800_000, 50_000))

    http_route = "/api/v1/checkout/reserve"
    http_fields = {"route": http_route, "response": {"status_code": 504}}
    error_status = {
        "code": 2,
        "message": "inventory reserve exceeded deadline: deadlock detected",
    }
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
            "status": error_status,
            "error": {"message": "Gateway timeout: inventory reserve exceeded 5000ms deadline"},
            "transaction": tx,
        },
        {
            "@timestamp": ts(net1),
            "trace": {"id": tid},
            "span": {"id": checkout_id, "name": "checkout.process", "type": "request", "subtype": "http", "action": "POST", "duration": {"us": chk_dur}},
            "parent": {"id": root_id},
            "service": {"name": "checkout-service"},
            "http": http_fields,
            "status": error_status,
            "transaction": tx,
        },
        {
            "@timestamp": ts(net1 + net2),
            "trace": {"id": tid},
            "span": {"id": reserve_id, "name": "inventory.reserve", "type": "request", "subtype": "grpc", "action": "reserve", "duration": {"us": res_dur}},
            "parent": {"id": checkout_id},
            "service": {"name": "inventory-service"},
            "http": http_fields,
            "status": error_status,
            "transaction": tx,
            "db": {"lock": {"timeout_us": lock_timeout_us}},
        },
        {
            "@timestamp": ts(net1 + net2 + db_start),
            "trace": {"id": tid},
            "span": {"id": dbq_id, "name": "db.query", "type": "db", "subtype": "postgresql", "action": "query", "duration": {"us": dbq_dur}},
            "parent": {"id": reserve_id},
            "service": {"name": "inventory-service"},
            "http": http_fields,
            "status": error_status,
            "transaction": tx,
            "db": {
                "statement": db_stmt,
                "statement_semantic": db_stmt,
                "type": "sql",
                "system": "postgresql",
                "lock": {"timeout_us": lock_timeout_us},
            },
        },
        {
            "@timestamp": ts(net1 + net2 + db_start + dbq_dur + db_gap),
            "trace": {"id": tid},
            "span": {"id": dbw_id, "name": "db.write", "type": "db", "subtype": "postgresql", "action": "write", "duration": {"us": dbw_dur}},
            "parent": {"id": reserve_id},
            "service": {"name": "inventory-service"},
            "http": http_fields,
            "status": error_status,
            "transaction": tx,
            "db": {
                "statement": db_stmt,
                "statement_semantic": db_stmt,
                "type": "sql",
                "system": "postgresql",
                "lock": {"timeout_us": lock_timeout_us},
            },
        },
    ]


def main():
    args = parse_args()
    demo_date = datetime.strptime(args.demo_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    incident_date = demo_date - timedelta(days=INCIDENT_OFFSET_DAYS)

    incident_start = incident_date.replace(
        hour=INCIDENT_START_HOUR, minute=0, second=0, microsecond=0
    )
    incident_end = incident_date.replace(
        hour=INCIDENT_END_HOUR, minute=INCIDENT_END_MINUTE, second=0, microsecond=0
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    window_start = incident_start.timestamp()
    window_end = incident_end.timestamp()
    seen_durs: set = set()

    print(f"Demo date:      {demo_date.date()}")
    print(f"Incident window: {incident_start.isoformat()} → {incident_end.isoformat()}")
    print(f"Generating {args.count:,} incident traces (~{args.count * SPANS_PER_TRACE:,} span docs) ...")

    with output_path.open("w") as f:
        for i in range(args.count):
            root_ts_float = rng.uniform(window_start, window_end)
            root_ts = datetime.fromtimestamp(root_ts_float, tz=timezone.utc)
            for span in build_incident_trace(rng, root_ts, seen_durs):
                f.write(json.dumps(span) + "\n")
            if (i + 1) % 150 == 0:
                print(f"  {i + 1:,} / {args.count:,}")

    print(f"Done: {args.count:,} traces, {args.count * SPANS_PER_TRACE:,} span docs → {output_path}")


if __name__ == "__main__":
    main()
