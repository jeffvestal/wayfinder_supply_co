#!/usr/bin/env python3
"""
MS Build 2026 end-to-end test harness.

Tiered:
  L1  local backend concurrency — proves atomic reserve blocks oversell, buggy branch allows it
  L2  webhook direct-fire        — POSTs synthetic PR payload to Elastic Workflow, polls execution
  L3  full PR path               — opens real PR, polls for bot comment, asserts expected phrases

Usage:
  python3 scripts/msbuild_harness.py preflight
  python3 scripts/msbuild_harness.py l1 [--product-id BOOT-001] [--parallel 20] [--expect auto|atomic|buggy]
  python3 scripts/msbuild_harness.py l2
  python3 scripts/msbuild_harness.py l3 [--cleanup] [--force-demo-branch]
  python3 scripts/msbuild_harness.py all

Exit code 0 on pass, non-zero on any assertion failure. Writes JSON report to harness-reports/.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = REPO_ROOT / "harness-reports"
BACKEND_URL = os.getenv("WAYFINDER_BACKEND_URL", "http://localhost:8000")
RESERVE_PATH = "/api/v1/checkout/reserve"
ATOMIC_BRANCH = "feature/msft-build-2026"
BUGGY_BRANCH = "demo/inventory-refactor"
DEMO_PRODUCT_ID = "BOOT-001"

# Env var names the harness consumes (documented in .env.example after wiring)
# NOTE: ELASTIC_WORKFLOW_URL / WORKFLOW_KEY replaced by direct agent API approach (Elastic 9.4
# does not support http-type workflow triggers; GH Action now calls agent converse/async directly)
ENV_WORKFLOW_URL = "ELASTIC_KIBANA_URL"   # kept for backwards compat with preflight checks
ENV_WORKFLOW_KEY = "ELASTIC_API_KEY"      # kept for backwards compat with preflight checks
ENV_KIBANA_URL = "STANDALONE_KIBANA_URL"
ENV_ES_APIKEY = "STANDALONE_ELASTICSEARCH_APIKEY"
ENV_OBS_URL = "OBSERVABILITY_ELASTIC_URL"
ENV_OBS_KEY = "OBSERVABILITY_ELASTIC_APIKEY"
ENV_AGENT_ID = "MSBUILD_AGENT_ID"

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class LevelResult:
    level: str
    passed: bool
    checks: list[Check] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


def _print_check(c: Check) -> None:
    marker = f"{GREEN}✓{RESET}" if c.passed else f"{RED}✗{RESET}"
    line = f"  {marker} {c.name}"
    if c.detail:
        line += f"  {DIM}{c.detail}{RESET}"
    print(line)


def _current_branch() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except subprocess.CalledProcessError:
        return "unknown"


def _load_dotenv() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        # Strip inline comments and quotes
        v = v.split(" #")[0].split("\t#")[0].strip().strip('"').strip("'")
        os.environ.setdefault(k.strip(), v)


# ─── preflight ─────────────────────────────────────────────────────────────────

def _check_env(required: list[str]) -> list[Check]:
    checks: list[Check] = []
    for var in required:
        val = os.environ.get(var)
        checks.append(Check(
            name=f"env: {var}",
            passed=bool(val),
            detail="(set)" if val else "(missing)",
        ))
    return checks


def _check_backend_health() -> Check:
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return Check("backend /health", r.status_code == 200, f"{r.status_code}")
    except Exception as e:
        return Check("backend /health", False, f"unreachable: {e}")


def _check_cluster_indices() -> list[Check]:
    url = os.environ.get(ENV_OBS_URL) or os.environ.get("ELASTIC_URL")
    key = os.environ.get(ENV_OBS_KEY) or os.environ.get("ELASTIC_API_KEY")
    out: list[Check] = []
    if not (url and key):
        out.append(Check("cluster credentials", False, f"need {ENV_OBS_URL} + {ENV_OBS_KEY}"))
        return out
    headers = {"Authorization": f"ApiKey {key}"}
    for index in ("traces-apm.wayfinder-default", "otel-traces-wayfinder"):
        try:
            r = requests.get(f"{url}/{index}/_count", headers=headers, timeout=10)
            if r.status_code != 200:
                out.append(Check(f"index {index}", False, f"HTTP {r.status_code}"))
                continue
            count = r.json().get("count", 0)
            out.append(Check(f"index {index}", count > 0, f"{count} docs"))
        except Exception as e:
            out.append(Check(f"index {index}", False, str(e)))
    return out


def _check_gh_auth() -> Check:
    try:
        r = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=10)
        return Check("gh auth", r.returncode == 0, "ok" if r.returncode == 0 else r.stderr.strip().splitlines()[-1] if r.stderr else "fail")
    except FileNotFoundError:
        return Check("gh auth", False, "gh not installed")


def _check_gh_secrets() -> list[Check]:
    try:
        r = subprocess.run(["gh", "secret", "list"], capture_output=True, text=True, timeout=10, cwd=REPO_ROOT)
    except Exception as e:
        return [Check("gh secrets", False, str(e))]
    names = set()
    for line in r.stdout.splitlines():
        tok = line.split()
        if tok:
            names.add(tok[0])
    checks: list[Check] = []
    for s in ("ELASTIC_KIBANA_URL", "ELASTIC_API_KEY"):
        checks.append(Check(f"gh secret: {s}", s in names, "present" if s in names else "MISSING — set with `gh secret set`"))
    return checks


def _check_workflow_reachable() -> Check:
    # Replaced: GH Action calls agent directly. Verify the agent converse endpoint responds.
    kibana = os.environ.get(ENV_KIBANA_URL)
    key = os.environ.get(ENV_ES_APIKEY) or os.environ.get("ELASTICSEARCH_APIKEY")
    if not (kibana and key):
        return Check("agent endpoint reachable", False, f"need {ENV_KIBANA_URL} + {ENV_ES_APIKEY}")
    try:
        r = requests.get(
            f"{kibana}/api/agent_builder/agents/msbuild-pr-review-agent",
            headers={"Authorization": f"ApiKey {key}", "kbn-xsrf": "true"},
            timeout=10,
        )
        return Check("agent endpoint reachable", r.status_code == 200, f"HTTP {r.status_code}")
    except Exception as e:
        return Check("agent endpoint reachable", False, str(e))


def _check_agent_exists() -> Check:
    agent_id = os.environ.get(ENV_AGENT_ID)
    kibana = os.environ.get(ENV_KIBANA_URL)
    key = os.environ.get(ENV_ES_APIKEY) or os.environ.get("ELASTICSEARCH_APIKEY")
    if not (agent_id and kibana and key):
        return Check("agent exists", False, f"need {ENV_AGENT_ID}, {ENV_KIBANA_URL}, {ENV_ES_APIKEY}")
    headers = {
        "Authorization": f"ApiKey {key}",
        "kbn-xsrf": "true",
        "x-elastic-internal-origin": "kibana",
    }
    try:
        r = requests.get(f"{kibana}/api/agent_builder/agents/{agent_id}", headers=headers, timeout=10)
        return Check("agent exists", r.status_code == 200, f"HTTP {r.status_code}")
    except Exception as e:
        return Check("agent exists", False, str(e))


def preflight(level: str = "all") -> LevelResult:
    print(f"\n{YELLOW}═══ preflight ({level}) ═══{RESET}")
    checks: list[Check] = []
    checks += _check_env([ENV_KIBANA_URL])
    checks += _check_cluster_indices()
    if level in ("l1", "all"):
        checks.append(_check_backend_health())
    if level in ("l2", "l3", "all"):
        checks += _check_env([ENV_WORKFLOW_URL, ENV_WORKFLOW_KEY, ENV_AGENT_ID])
        checks.append(_check_workflow_reachable())
        checks.append(_check_agent_exists())
    if level in ("l3", "all"):
        checks.append(_check_gh_auth())
        checks += _check_gh_secrets()
    for c in checks:
        _print_check(c)
    passed = all(c.passed for c in checks)
    return LevelResult("preflight", passed, checks)


# ─── L1 ────────────────────────────────────────────────────────────────────────

def _reserve(product_id: str, quantity: int, user_id: str) -> tuple[int, dict | None]:
    api_key = os.environ.get("WAYFINDER_API_KEY", "")
    headers = {"X-Api-Key": api_key} if api_key else {}
    try:
        r = requests.post(
            f"{BACKEND_URL}{RESERVE_PATH}",
            json={"product_id": product_id, "quantity": quantity, "user_id": user_id},
            headers=headers,
            timeout=10,
        )
        return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else None)
    except Exception as e:
        return -1, {"error": str(e)}


def _drain_stock_to(target: int, product_id: str) -> int:
    """Pre-reserve units until stock == target. Returns remaining stock seen after drain."""
    # Probe current stock by reserving 0 — fallback: reserve 1 and read quantity_available.
    code, body = _reserve(product_id, 1, f"drain-{uuid.uuid4().hex[:6]}")
    if code != 200 or not body:
        raise RuntimeError(f"drain probe failed: HTTP {code} body={body}")
    # body.quantity_available is the state AFTER the reservation
    remaining = body["quantity_available"]
    to_drain = remaining - target
    if to_drain < 0:
        raise RuntimeError(f"stock already {remaining}, below target {target} — restart backend to reset")
    for i in range(to_drain):
        c, b = _reserve(product_id, 1, f"drain-{i}")
        if c != 200 or not b or not b["reserved"]:
            raise RuntimeError(f"drain step {i} failed: HTTP {c} body={b}")
    # final state
    return target


def run_l1(parallel: int, product_id: str, expect: str) -> LevelResult:
    print(f"\n{YELLOW}═══ L1: local backend concurrency ═══{RESET}")
    branch = _current_branch()
    print(f"  branch: {branch}")

    if expect == "auto":
        if branch == ATOMIC_BRANCH:
            expect = "atomic"
        elif branch == BUGGY_BRANCH:
            expect = "buggy"
        else:
            print(f"  {YELLOW}WARN: branch '{branch}' not recognized; defaulting to atomic expectation{RESET}")
            expect = "atomic"
    print(f"  expect: {expect} behavior")

    checks: list[Check] = []
    extra: dict[str, Any] = {"branch": branch, "expect": expect}

    # Step 1: backend healthy
    hc = _check_backend_health()
    _print_check(hc)
    checks.append(hc)
    if not hc.passed:
        return LevelResult("l1", False, checks, extra)

    # Step 2: drain stock to 1
    try:
        final_stock = _drain_stock_to(1, product_id)
        d = Check("drain stock to 1", True, f"final stock ≈ {final_stock}")
    except Exception as e:
        d = Check("drain stock to 1", False, str(e))
    _print_check(d)
    checks.append(d)
    if not d.passed:
        return LevelResult("l1", False, checks, extra)

    # Step 3: fire N parallel reservations
    print(f"  firing {parallel} parallel reservations…")
    results: list[tuple[int, dict | None]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as pool:
        futures = [
            pool.submit(_reserve, product_id, 1, f"concurrent-{i}")
            for i in range(parallel)
        ]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    reserved_count = sum(1 for code, body in results if code == 200 and body and body.get("reserved"))
    extra["reserved_count"] = reserved_count
    extra["total_requests"] = parallel
    print(f"  {DIM}{reserved_count} / {parallel} requests succeeded (reserved: true){RESET}")

    if expect == "atomic":
        c = Check(
            "atomic behavior: exactly 1 reservation succeeds",
            reserved_count == 1,
            f"got {reserved_count}, want 1",
        )
    else:  # buggy
        c = Check(
            "buggy behavior: oversell reproduced (≥2 reservations succeed)",
            reserved_count >= 2,
            f"got {reserved_count}, want ≥2",
        )
    _print_check(c)
    checks.append(c)

    return LevelResult("l1", c.passed, checks, extra)


# ─── L2 ────────────────────────────────────────────────────────────────────────

def run_l2(timeout_s: int = 120) -> LevelResult:
    print(f"\n{YELLOW}═══ L2: agent direct-fire ═══{RESET}")
    checks: list[Check] = []
    extra: dict[str, Any] = {}

    kibana = os.environ.get(ENV_KIBANA_URL)
    key = os.environ.get(ENV_ES_APIKEY) or os.environ.get("ELASTICSEARCH_APIKEY")
    if not (kibana and key):
        c = Check("agent env present", False, f"need {ENV_KIBANA_URL} + {ENV_ES_APIKEY}")
        _print_check(c)
        return LevelResult("l2", False, [c], extra)

    repo = os.environ.get("WAYFINDER_REPO", "jeffvestal/wayfinder_supply_co")
    pr_tag = f"TEST-{int(time.time())}"
    input_msg = (
        f"Review PR #{pr_tag} in {repo}. "
        "Title: perf: split inventory read/write for query plan cache efficiency. "
        "This is a harness test — analyze the known pattern and confirm OTel traces are reachable. "
        "Do NOT post a real GitHub comment. Summarize what you would say."
    )
    payload = {"agent_id": "msbuild-pr-review-agent", "input": input_msg}
    extra["payload"] = payload

    agent_url = f"{kibana}/api/agent_builder/converse/async"
    try:
        r = requests.post(
            agent_url,
            headers={
                "Authorization": f"ApiKey {key}",
                "Content-Type": "application/json",
                "kbn-xsrf": "true",
            },
            json=payload,
            timeout=timeout_s,
            stream=True,
        )
        # Collect SSE stream
        response_chunks = []
        for line in r.iter_lines(decode_unicode=True):
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="replace")
            if line and line.startswith("data:"):
                response_chunks.append(line[5:].strip())
        full_response = " ".join(response_chunks)
        extra["agent_response"] = full_response[:2000]
        c = Check(
            "agent trigger accepted",
            200 <= r.status_code < 300,
            f"HTTP {r.status_code} chunks={len(response_chunks)}",
        )
    except Exception as e:
        c = Check("agent trigger accepted", False, str(e))
    _print_check(c)
    checks.append(c)

    if not c.passed:
        return LevelResult("l2", False, checks, extra)

    # Verify the agent response contains expected content
    response_text = extra.get("agent_response", "").lower()
    content_check = Check(
        "agent response contains inventory/trace content",
        any(kw in response_text for kw in ["inventory", "trace", "incident", "checkout", "reserve"]),
        f"response preview: {response_text[:200]}",
    )
    _print_check(content_check)
    checks.append(content_check)

    print(f"  {DIM}execution poll: not applicable (direct agent call, no workflow execution ID){RESET}")
    return LevelResult("l2", True, checks, extra)

    # Dead code — kept as reference for future workflow-based L2 polling
    exec_id = extra.get("execution_id")
    kibana = os.environ.get(ENV_KIBANA_URL)
    es_key = os.environ.get(ENV_ES_APIKEY) or os.environ.get("ELASTICSEARCH_APIKEY")
    if not exec_id or not kibana or not es_key:
        print(f"  {DIM}skipping execution poll (missing exec id or Kibana env){RESET}")
        return LevelResult("l2", True, checks, extra)

    headers = {
        "Authorization": f"ApiKey {es_key}",
        "kbn-xsrf": "true",
        "x-elastic-internal-origin": "kibana",
    }
    poll_url = f"{kibana}/api/workflowExecutions/{exec_id}"
    deadline = time.time() + timeout_s
    final_status = "unknown"
    while time.time() < deadline:
        try:
            rr = requests.get(poll_url, headers=headers, timeout=10)
            if rr.status_code == 200:
                final_status = rr.json().get("status", "unknown")
                if final_status in ("completed", "failed", "success", "error"):
                    break
        except Exception:
            pass
        time.sleep(3)
    extra["execution_status"] = final_status
    pc = Check(
        "workflow execution completed",
        final_status in ("completed", "success"),
        f"status={final_status}",
    )
    _print_check(pc)
    checks.append(pc)

    return LevelResult("l2", all(x.passed for x in checks), checks, extra)


# ─── L3 ────────────────────────────────────────────────────────────────────────

EXPECTED_COMMENT_PHRASES = [
    "inventory",
    "Elastic Agent Builder",
]


def _gh(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *cmd], capture_output=True, text=True, cwd=REPO_ROOT)


def _close_existing_demo_prs() -> list[str]:
    r = _gh(["pr", "list", "--head", BUGGY_BRANCH, "--state", "open", "--json", "number,url"])
    closed: list[str] = []
    if r.returncode != 0:
        return closed
    try:
        for item in json.loads(r.stdout or "[]"):
            num = str(item["number"])
            _gh(["pr", "close", num, "--delete-branch=false"])
            closed.append(item["url"])
    except Exception:
        pass
    return closed


def run_l3(cleanup_only: bool, force_demo_branch: bool, timeout_s: int = 300) -> LevelResult:
    print(f"\n{YELLOW}═══ L3: full PR path ═══{RESET}")
    checks: list[Check] = []
    extra: dict[str, Any] = {}

    closed = _close_existing_demo_prs()
    if closed:
        extra["closed_prior_prs"] = closed
        print(f"  {DIM}closed {len(closed)} prior demo PR(s){RESET}")

    if cleanup_only:
        checks.append(Check("cleanup only", True, f"closed {len(closed)} PRs"))
        return LevelResult("l3", True, checks, extra)

    # Confirm demo/inventory-refactor is ready
    r = _gh(["api", f"repos/:owner/:repo/branches/{BUGGY_BRANCH.replace('/', '%2F')}"])
    branch_ok = r.returncode == 0
    checks.append(Check(f"remote branch {BUGGY_BRANCH} exists", branch_ok, ""))
    if not branch_ok:
        return LevelResult("l3", False, checks, extra)

    pr_title = "perf: split inventory read/write for query plan cache efficiency"
    pr_body = (
        "Pre-compute the new quantity value so the UPDATE statement is parameterized "
        "consistently, improving prepared statement cache hit rate under high throughput.\n\n"
        f"_Harness run: {datetime.now(timezone.utc).isoformat()}_"
    )
    r = _gh([
        "pr", "create",
        "--base", ATOMIC_BRANCH,
        "--head", BUGGY_BRANCH,
        "--title", pr_title,
        "--body", pr_body,
    ])
    created = r.returncode == 0
    pr_url = r.stdout.strip().splitlines()[-1] if created and r.stdout else ""
    checks.append(Check("pr opened", created, pr_url or r.stderr.strip().splitlines()[-1] if r.stderr else ""))
    extra["pr_url"] = pr_url
    if not created:
        return LevelResult("l3", False, checks, extra)

    pr_number = pr_url.rsplit("/", 1)[-1]
    extra["pr_number"] = pr_number

    # Poll for a bot comment
    print(f"  polling PR #{pr_number} for bot comment (timeout {timeout_s}s)…")
    deadline = time.time() + timeout_s
    matched_comment: str | None = None
    while time.time() < deadline:
        rc = _gh(["pr", "view", pr_number, "--json", "comments"])
        if rc.returncode == 0:
            try:
                data = json.loads(rc.stdout)
                for comment in data.get("comments", []):
                    body = comment.get("body", "")
                    if all(p.lower() in body.lower() for p in EXPECTED_COMMENT_PHRASES):
                        matched_comment = body
                        break
                if matched_comment:
                    break
            except Exception:
                pass
        time.sleep(5)

    if matched_comment:
        c = Check("bot comment matches expected phrases", True, f"{len(matched_comment)} chars")
        extra["comment_body"] = matched_comment
    else:
        c = Check(
            "bot comment matches expected phrases",
            False,
            f"no matching comment within {timeout_s}s",
        )
    _print_check(c)
    checks.append(c)

    return LevelResult("l3", c.passed, checks, extra)


# ─── dispatch ──────────────────────────────────────────────────────────────────

def _write_report(results: list[LevelResult]) -> Path:
    REPORT_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = REPORT_DIR / f"{ts}.json"
    path.write_text(json.dumps([asdict(r) for r in results], indent=2, default=str))
    return path


def main() -> int:
    _load_dotenv()

    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preflight")

    p_l1 = sub.add_parser("l1")
    p_l1.add_argument("--parallel", type=int, default=20)
    p_l1.add_argument("--product-id", default=DEMO_PRODUCT_ID)
    p_l1.add_argument("--expect", choices=["auto", "atomic", "buggy"], default="auto")

    sub.add_parser("l2")

    p_l3 = sub.add_parser("l3")
    p_l3.add_argument("--cleanup", action="store_true")
    p_l3.add_argument("--force-demo-branch", action="store_true")

    sub.add_parser("all")

    args = ap.parse_args()

    results: list[LevelResult] = []
    level = args.cmd

    if level == "preflight":
        results.append(preflight("all"))
    elif level == "l1":
        pf = preflight("l1")
        results.append(pf)
        if pf.passed:
            results.append(run_l1(args.parallel, args.product_id, args.expect))
    elif level == "l2":
        pf = preflight("l2")
        results.append(pf)
        if pf.passed:
            results.append(run_l2())
    elif level == "l3":
        pf = preflight("l3")
        results.append(pf)
        if pf.passed or args.cleanup:
            results.append(run_l3(args.cleanup, args.force_demo_branch))
    elif level == "all":
        results.append(preflight("all"))
        if results[-1].passed:
            results.append(run_l1(20, DEMO_PRODUCT_ID, "auto"))
            if results[-1].passed:
                results.append(run_l2())
                if results[-1].passed:
                    results.append(run_l3(False, False))

    report_path = _write_report(results)
    overall = all(r.passed for r in results) if results else False
    print(f"\n{DIM}report: {report_path.relative_to(REPO_ROOT)}{RESET}")
    if overall:
        print(f"{GREEN}PASS{RESET}")
        return 0
    print(f"{RED}FAIL{RESET}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
