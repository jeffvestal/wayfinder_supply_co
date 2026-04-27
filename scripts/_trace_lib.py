"""Shared helpers for the MS Build trace generation/indexing scripts."""

from __future__ import annotations

import json
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "generated_traces"

DEFAULT_INDEX = "traces-apm.wayfinder-default"
VERIFY_INDEX_PREFIX = "traces-apm.wayfinder-verify"
TARGET_ROUTE = "/api/v1/checkout/reserve"
SERVICE_NAME = "wayfinder-inventory"


def demo_date() -> datetime:
    val = os.environ.get("DEMO_DATE", "2026-05-19")
    y, m, d = (int(x) for x in val.split("-"))
    return datetime(y, m, d, tzinfo=timezone.utc)


def ns(dt: datetime) -> int:
    """Epoch nanoseconds."""
    return int(dt.timestamp() * 1_000_000_000)


def new_ids() -> tuple[str, str]:
    """(trace_id, root_span_id) — 32 + 16 hex per OTel."""
    return uuid.uuid4().hex + uuid.uuid4().hex[:0] + uuid.uuid4().hex[:0][:0] + uuid.uuid4().hex[:0], uuid.uuid4().hex[:16]


def trace_id() -> str:
    return (uuid.uuid4().hex + uuid.uuid4().hex)[:32]


def span_id() -> str:
    return uuid.uuid4().hex[:16]


def child_spans(
    tid: str,
    parent_sid: str,
    root_start_ns: int,
    root_duration_us: int,
    http_route: str,
    db_statement: str,
    processor_event_child: str = "span",
) -> list[dict]:
    """Produce the 4 child spans of a reserve trace (app hop, db.query, db.write, post)."""
    out = []
    # Slice the root duration across child spans with jitter.
    cuts = sorted([random.uniform(0.05, 0.95) for _ in range(3)])
    slices_us = [
        int(cuts[0] * root_duration_us),
        int((cuts[1] - cuts[0]) * root_duration_us),
        int((cuts[2] - cuts[1]) * root_duration_us),
        int((1 - cuts[2]) * root_duration_us),
    ]
    starts = [root_start_ns]
    for s_us in slices_us[:-1]:
        starts.append(starts[-1] + s_us * 1000)
    names = ["checkout.handler", "db.query", "db.write", "response.compose"]
    db_stmts = [
        None,
        f"SELECT quantity FROM inventory WHERE product_id = 'BOOT-001'",
        db_statement,
        None,
    ]
    for i, (name, start_ns, dur_us) in enumerate(zip(names, starts, slices_us)):
        doc: dict = {
            "@timestamp": datetime.fromtimestamp(start_ns / 1e9, tz=timezone.utc).isoformat(),
            "trace": {"id": tid},
            "span": {
                "id": span_id(),
                "name": name,
                "duration": {"us": dur_us},
            },
            "parent": {"id": parent_sid if i == 0 else None},
            "service": {"name": SERVICE_NAME},
            "http": {"route": http_route},
            "event": {"duration": dur_us * 1000},
            "processor": {"event": processor_event_child},
        }
        if db_stmts[i]:
            doc["db"] = {"statement": db_stmts[i], "statement_semantic": db_stmts[i]}
        out.append(doc)
    return out


def root_span(
    tid: str,
    start: datetime,
    duration_us: int,
    http_route: str,
    http_status: int = 200,
    processor_event: str = "transaction",
) -> tuple[dict, str]:
    sid = span_id()
    doc = {
        "@timestamp": start.isoformat(),
        "trace": {"id": tid},
        "span": {
            "id": sid,
            "name": "POST /api/v1/checkout/reserve",
            "duration": {"us": duration_us},
        },
        "service": {"name": SERVICE_NAME},
        "http": {"route": http_route, "response": {"status_code": http_status}},
        "event": {"duration": duration_us * 1000},
        "processor": {"event": processor_event},
    }
    return doc, sid


def write_jsonl(path: Path, rows: Iterator[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, default=str) + "\n")
            n += 1
    return n


# Explicit mapping — dynamic:false, db.statement text + semantic twin, long durations.
INDEX_MAPPING: dict = {
    "mappings": {
        "dynamic": False,
        "properties": {
            "@timestamp": {"type": "date"},
            "trace": {"properties": {"id": {"type": "keyword"}}},
            "span": {
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "duration": {"properties": {"us": {"type": "long"}}},
                }
            },
            "parent": {"properties": {"id": {"type": "keyword"}}},
            "service": {"properties": {"name": {"type": "keyword"}}},
            "http": {
                "properties": {
                    "route": {"type": "keyword"},
                    "response": {"properties": {"status_code": {"type": "short"}}},
                }
            },
            "db": {
                "properties": {
                    "statement": {"type": "text"},
                    "statement_semantic": {"type": "semantic_text"},
                }
            },
            "event": {"properties": {"duration": {"type": "long"}}},
            "processor": {"properties": {"event": {"type": "keyword"}}},
        },
    }
}
