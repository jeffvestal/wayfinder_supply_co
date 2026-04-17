#!/usr/bin/env python3
"""Validate generated OTel trace JSONL files before indexing.

Usage:
    python scripts/validate_traces.py generated_traces/baseline_traces.jsonl generated_traces/incident_traces.jsonl
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEMO_DATE = datetime(2026, 5, 19, tzinfo=timezone.utc)
INCIDENT_DATE = DEMO_DATE - timedelta(days=42)  # 2026-04-07
BASELINE_END = INCIDENT_DATE - timedelta(days=1)  # 2026-04-06
BASELINE_START = BASELINE_END - timedelta(days=30)  # 2026-03-07

INCIDENT_START = INCIDENT_DATE.replace(hour=14, minute=0, second=0, microsecond=0)
INCIDENT_END = INCIDENT_DATE.replace(hour=17, minute=30, second=0, microsecond=0)

BASELINE_P99_MAX_US = 200_000   # 200ms
INCIDENT_DUR_MIN_US = 3_500_000  # 3500ms
INCIDENT_DUR_MAX_US = 7_500_000  # 7500ms


def load_file(path):
    docs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


def get_dur_us(doc):
    return doc.get("span", {}).get("duration", {}).get("us")


def get_ts(doc):
    ts_str = doc.get("@timestamp", "")
    if not ts_str:
        return None
    # Strip nanoseconds past microsecond precision for parsing
    ts_clean = ts_str.rstrip("Z")
    # Truncate to microseconds (6 decimal places)
    if "." in ts_clean:
        base, frac = ts_clean.split(".", 1)
        frac = frac[:6].ljust(6, "0")
        ts_clean = f"{base}.{frac}"
    try:
        return datetime.fromisoformat(ts_clean + "+00:00")
    except ValueError:
        return None


def span_name(doc):
    return doc.get("span", {}).get("name", "")


def check(label, passed, detail=""):
    mark = "PASS" if passed else "FAIL"
    line = f"  [{mark}] {label}"
    if detail:
        line += f"  ({detail})"
    print(line)
    return passed


def percentile(sorted_values, pct):
    if not sorted_values:
        return 0
    idx = int(len(sorted_values) * pct / 100)
    return sorted_values[min(idx, len(sorted_values) - 1)]


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_traces.py <baseline.jsonl> [<incident.jsonl>]")
        sys.exit(1)

    baseline_path = Path(sys.argv[1])
    incident_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    print(f"\n=== Loading files ===")
    baseline_docs = load_file(baseline_path)
    print(f"  Baseline: {len(baseline_docs):,} span docs from {baseline_path}")

    incident_docs = []
    if incident_path:
        incident_docs = load_file(incident_path)
        print(f"  Incident: {len(incident_docs):,} span docs from {incident_path}")

    all_docs = baseline_docs + incident_docs
    failures = 0

    print(f"\n=== Uniqueness checks ===")

    # trace.id is shared across all spans in a trace — check baseline/incident don't collide
    bl_trace_ids = set(d.get("trace", {}).get("id") for d in baseline_docs if d.get("trace", {}).get("id"))
    inc_trace_ids = set(d.get("trace", {}).get("id") for d in incident_docs if d.get("trace", {}).get("id"))
    overlap = bl_trace_ids & inc_trace_ids
    if not check("No trace.id collision between baseline and incident",
                 len(overlap) == 0,
                 f"{len(overlap)} collisions; {len(bl_trace_ids):,} baseline, {len(inc_trace_ids):,} incident unique trace IDs"):
        failures += 1

    span_ids = [d.get("span", {}).get("id") for d in all_docs if d.get("span", {}).get("id")]
    if not check("span.id values are unique",
                 len(span_ids) == len(set(span_ids)),
                 f"{len(span_ids) - len(set(span_ids))} duplicates across {len(span_ids):,} total"):
        failures += 1

    print(f"\n=== Baseline timestamp range ===")
    bl_ts = [get_ts(d) for d in baseline_docs]
    bl_ts_valid = [t for t in bl_ts if t is not None]
    out_of_range = [t for t in bl_ts_valid if not (BASELINE_START <= t <= BASELINE_END)]
    if not check(f"Baseline @timestamp in [{BASELINE_START.date()} → {BASELINE_END.date()}]",
                 len(out_of_range) == 0,
                 f"{len(out_of_range)} out of range, {len(bl_ts) - len(bl_ts_valid)} unparseable"):
        failures += 1

    if incident_docs:
        print(f"\n=== Incident timestamp range ===")
        # Validate root span timestamps only — child spans may complete just after 17:30
        inc_roots = [d for d in incident_docs if span_name(d) == "POST /checkout"]
        inc_ts = [get_ts(d) for d in inc_roots]
        inc_ts_valid = [t for t in inc_ts if t is not None]
        out_of_window = [t for t in inc_ts_valid if not (INCIDENT_START <= t <= INCIDENT_END)]
        if not check(f"Incident root span @timestamp in [{INCIDENT_START.isoformat()} → {INCIDENT_END.isoformat()}]",
                     len(out_of_window) == 0,
                     f"{len(out_of_window)} root spans out of window, {len(inc_roots)} roots checked"):
            failures += 1

    print(f"\n=== Duration checks ===")

    bl_reserve = [d for d in baseline_docs if span_name(d) == "inventory.reserve"]
    bl_durs = sorted([get_dur_us(d) for d in bl_reserve if get_dur_us(d)])
    if bl_durs:
        p99_us = percentile(bl_durs, 99)
        p99_ms = p99_us / 1000
        if not check(f"Baseline inventory.reserve p99 < 200ms",
                     p99_us < BASELINE_P99_MAX_US,
                     f"p99={p99_ms:.1f}ms, count={len(bl_durs):,}"):
            failures += 1
    else:
        print("  [SKIP] No baseline inventory.reserve spans found")

    if incident_docs:
        inc_reserve = [d for d in incident_docs if span_name(d) == "inventory.reserve"]
        inc_durs = [get_dur_us(d) for d in inc_reserve if get_dur_us(d)]
        out = [d for d in inc_durs if not (INCIDENT_DUR_MIN_US <= d <= INCIDENT_DUR_MAX_US)]
        min_dur = min(inc_durs) / 1000 if inc_durs else 0
        max_dur = max(inc_durs) / 1000 if inc_durs else 0
        if not check(f"Incident inventory.reserve durations in [3500ms, 7500ms]",
                     len(out) == 0,
                     f"{len(out)} out of range, min={min_dur:.0f}ms, max={max_dur:.0f}ms"):
            failures += 1

    print(f"\n=== Jitter / uniqueness check ===")

    all_reserve_durs = [get_dur_us(d) for d in (bl_reserve if bl_durs else []) + (inc_reserve if incident_docs else []) if get_dur_us(d)]
    dup_count = len(all_reserve_durs) - len(set(all_reserve_durs))
    if not check("No duplicate inventory.reserve span.duration.us values",
                 dup_count == 0,
                 f"{dup_count} duplicates in {len(all_reserve_durs):,} spans"):
        failures += 1

    print(f"\n{'=' * 40}")
    if failures == 0:
        print("All checks PASSED.")
    else:
        print(f"{failures} check(s) FAILED.")

    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
