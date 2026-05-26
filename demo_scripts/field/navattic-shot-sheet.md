---
type: final
title: "MS Build 2026 — Navattic Shot Sheet"
status: recording-complete
category: content
priority: high
created: 2026-05-26
updated: 2026-05-26
tags: [msbuild-2026, navattic, demo, wayfinder, shot-sheet]
---

# MS Build 2026 — Wayfinder Navattic Shot Sheet

**Recording target:** Click-through demo for MS Build 2026 session
**Source script:** `demo_scripts/field/msbuild_recording_guide.md`
**Branch:** `feature/msft-build-2026`
**Total shots:** ~30 steps across 8 scenes

### Kibana:
https://wayfinder-supply-co-aa4128.kb.us-central1.gcp.elastic.cloud

### GitHub PR:
URL printed by `./control.sh setup` — use that URL.

---

## Pre-Recording Setup

- [ ] Run `./control.sh setup` — starts services, checks trace data, creates fresh PR
- [ ] Verify bot comment posted on the PR URL printed by setup
- [ ] Browser tabs ready: GitHub PR + Kibana Agent Builder + Kibana Workflows (left nav)
- [ ] VS Code open on `demo/inventory-refactor`, `backend/services/inventory_service.py` visible
- [ ] Copilot Agent Mode panel open (`Cmd+Shift+I`), chat cleared

---

## Navattic Notes

- Each shot below = one Navattic step. Build in Navattic Demo Builder UI.
- Hotspot text in **Highlight / Hotspot** column = copy-paste tooltip text directly.
- Auto-advance 2s steps = streaming/loading states — wire as sequential static frames.
- For wait steps: capture two screenshots (loading state + complete). Wire sequentially.

---

## Scene 1 — Architecture (static slide)

**App:** Slide deck | **Captures:** 1

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | Static architecture diagram | ✅ Cap 1a | Annotate full pipeline arrow: "PR opens → GitHub Action → Elastic Workflow → Agent Builder → OTel traces → comment posted. No human in the loop." |

---

## Scene 2 — Open the PR (GitHub)

**Before recording:** `./control.sh stage` — prints two URLs, use them in order

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | Open **Cap 2a URL** (compare page) — diff visible, green "Create pull request" button | ✅ Cap 2a | Highlight diff panel + button: "One file changed. A performance optimization to the inventory reservation logic. The kind of PR that gets merged on sight." |
| --- | --- | --- | --- |
| 2 | Navigate to **Cap 2b URL** (pre-filled PR form) — title + body already filled in | ✅ Cap 2b | Hotspot on title: "Read the title: 'Performance optimization.' Nothing alarming. Single file change. This is the PR that should have been caught before it ever merged." |
| --- | --- | --- | --- |
| 3 | Click **Create pull request** (submit) | | |
| --- | --- | --- | --- |
| 4 | PR page loads → click **Files changed** tab | | |
| --- | --- | --- | --- |
| 5 | Scroll to `inventory_service.py` diff. Find line 54 (left/red): `WHERE product_id = '...' AND quantity >= {quantity}` | ✅ Cap 2c | Hotspot on `AND quantity >= {quantity}` (red/removed line): "This condition. Gone. The stock guard is removed — the database no longer checks if inventory is sufficient before decrementing. This is a TOCTOU vulnerability. Concurrent requests all pass the check before any write completes." |

---

## Scene 3 — Bot comment appears (GitHub PR)

**Before recording:** No reset — use the PR from Scene 2. Wait ~30s after Scene 2 ends.
**App:** Browser → GitHub PR → Conversation tab

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | PR Conversation tab, Checks section showing action running, no bot comment yet | ✅ Cap 3a — auto-advance 2s | Highlight Checks status: "GitHub Action fired. Calling Elastic Workflow → Agent Builder. About 45 seconds." |
| --- | --- | --- | --- |
| 2 | Reload page after ~45s — bot comment partially visible | ✅ Cap 3b — auto-advance 2s | |
| --- | --- | --- | --- |
| 3 | Scroll down slightly — incident evidence section visible (trace ID, endpoint, latency) | ✅ Cap 3c — auto-advance 2s | |
| --- | --- | --- | --- |
| 4 | Full bot comment rendered | ✅ Cap 3d | Hotspot on trace evidence: "Real OTel data. Not hallucinated — retrieved from the traces index at query time." Hotspot on "TOCTOU": "Pattern named. That word isn't in the diff. The agent recognized the structural pattern and named it from its skill knowledge." |

**Re-take:** `./control.sh reset` → wait ~60s for bot comment

---

## Scene 4 — GitHub Actions proof (GitHub)

**App:** Browser → GitHub PR → Checks tab → click into the run

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | Click **Checks** tab → click into `pr-review` run — Actions summary page | ✅ Cap 4a | Hotspot on "succeeded in Xs": "Real GitHub Action. Real run. Not a shortcut — every PR that opens against this repo triggers this." |
| --- | --- | --- | --- |
| 2 | Click into **trigger-elastic-review** job → expand "Call Elastic Agent Builder + Post PR Comment" step → logs visible | ✅ Cap 4b | Hotspot on step name: "One step. Call the agent, get a response, post the comment — that's the entire integration." Hotspot on comment URL in logs: "That link is the bot comment on the PR. Clickable proof." |
| --- | --- | --- | --- |
| 3 | Click **Usage** tab (left sidebar under Run details) | ✅ Cap 4c | "Billable time, runner type, triggered by PR open. Every run is logged and auditable." |
| --- | --- | --- | --- |
| 4 | Click **Workflow file** tab (left sidebar under Run details) | ✅ Cap 4d | Hotspot on the YAML: "This is the entire integration. One job, one step. PR opens → Elastic gets called." |

---

## Scene 5 — Kibana: Agent Builder as a platform (Kibana)

**App:** Browser → `https://wayfinder-supply-co-aa4128.kb.us-central1.gcp.elastic.cloud`
**Beats:** 5 | **Captures:** 14 (5a–5n) | **Target runtime:** ~6 min

**Before recording:** Beat 4 live chat will populate Conversations; Beat 5 shows those runs (intentional — live proof).

### Beat 1 — Grounding: "The bot isn't guessing" (~45s)

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | Agent Builder home — `msbuild-pr-review-agent` visible in agent list | ✅ Cap 5a | Hotspot on agent row: "One agent. Lives in Kibana. No separate deployment, no infra team. Anyone on the team can see it, edit it, audit it." |
| --- | --- | --- | --- |
| 2 | Click into agent → **Edit** → System Instructions field visible, 3 ES\|QL tools listed below | ✅ Cap 5b | Hotspot on instructions: "The agent's entire charter — plain text. Editable by anyone." Hotspot on tools: "Tools = grounded retrieval. The agent can only claim what these queries return. No hallucination, no guessing." |
| --- | --- | --- | --- |
| 3 | Click **Edit in library** on `tool-esql-find-similar-traces` → ES\|QL query body visible | ✅ Cap 5c | Hotspot on query: "This is the query that found the 6-week-old trace. Plain ES\|QL. Versioned. Reviewable. Not a black box." |

### Beat 2 — Expertise: "Tools fetch facts. Skills carry judgment" (~45s)

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 4 | Navigate to **AI → Skills** (left nav) — `PR Race Condition Analysis` visible in list | ✅ Cap 5d | "Skills = reusable expertise. Define once, attach to any agent in Kibana. This one encodes the TOCTOU, non-atomic read-modify-write, and lock-contention patterns." |
| --- | --- | --- | --- |
| 5 | Click `PR Race Condition Analysis` — instruction body open, TOCTOU section visible | ✅ Cap 5e | Hotspot on TOCTOU paragraph: "This is how expertise gets encoded. Not in a model weight — here. Plain text. Editable. Versionable. Shareable across every agent your team builds. The agent named 'TOCTOU' because this skill told it what to look for." |
| --- | --- | --- | --- |
| 6 | Back to agent edit page → **Skills** section — `skill-pr-race-condition-analysis` shown as attached | ✅ Cap 5f | "This agent uses it. Any new agent the team creates can attach the same skill — the expertise travels with it." |

### Beat 3 — Orchestration: "This is what GitHub fires" (~1 min)

**Nav:** Kibana → Workflows (left nav, top-level)

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 7 | Kibana Workflows list — `elastic-agent-pr-review` visible | ✅ Cap 5g | Hotspot on workflow name: "This is the bridge. GitHub Action fires this workflow. It's the only thing between a PR open event and the Agent Builder." |
| --- | --- | --- | --- |
| 8 | Click into `elastic-agent-pr-review` — two steps visible: `invoke_agent` and `log_outcome` | ✅ Cap 5h | Hotspot on `invoke_agent` step: "One HTTP call. GitHub fires this. The workflow calls Agent Builder with the PR metadata. That's the entire integration — no custom infra, no middleware." |
| --- | --- | --- | --- |
| 9 | Click **Executions** tab — prior run visible: green checkmark, `invoke_agent` 51s, `log_outcome` 2ms, output "Agent response status: 200" | ✅ Cap 5i | Hotspot on green checkmark + status 200: "Every run logged. This fired on a real PR — 51 seconds from GitHub trigger to agent response. Auditable, replayable, observable." |

### Beat 4 — Live Chat: "Watch it reason" (~2 min)

**Nav:** Back to AI → Agent Builder → `msbuild-pr-review-agent` → Chat / Test panel

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 10 | Chat panel open, Chat 1 prompt typed (not sent): `I'm looking at a PR that removes the AND quantity >= check from the reserve() WHERE clause. Does that match any known patterns?` | ✅ Cap 5j | Hotspot on prompt: "A question a developer might actually ask. No query syntax, no dashboard." |
| --- | --- | --- | --- |
| 11 | Press Enter — tool calls firing, traces being retrieved | ✅ Cap 5k — auto-advance 2s | (none — let the retrieval speak for itself) |
| --- | --- | --- | --- |
| 12 | Full Chat 1 response visible — TOCTOU named, issue numbers cited, trace evidence | ✅ Cap 5l | Hotspot on "TOCTOU" + issue numbers: "It queried the traces, matched the pattern, named it — and cited the issue numbers. Same reasoning chain it ran on the real PR." |
| --- | --- | --- | --- |
| 13 | Chat 2 in same session: `What do you know about the /api/v1/checkout/reserve endpoint from the last 6 weeks?` → response with trace rows | ✅ Cap 5m | Hotspot on trace rows (timestamps, durations): "Raw OTel data, returned in natural language. Same data the bot cited in the PR comment. Different question, same grounded retrieval." |

**Re-take for Beat 4:** Clear chat history, re-send both prompts. If Chat 1 doesn't name TOCTOU, use: `I'm looking at a PR that splits a read-check and write into separate statements on the inventory reserve() function. Does that match any known race condition patterns?`

### Beat 5 — Governance: "Every run is accountable" (~1 min)

**Note:** The Beat 4 chats will be the most recent Conversations entries — intentional. Point to them as live proof.

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 14 | Navigate to **Conversations** — list includes the just-run Beat 4 chats + prior PR review runs | ✅ Cap 5n | "Every interaction with this agent is logged here — the chats you just saw, and every PR that triggered it. Audit, replay, debug — nothing is hidden." |
| --- | --- | --- | --- |
| 15 | Click most recent run → expand tool call to show inputs + raw trace response + final output | ✅ Cap 5o | Hotspot on inputs: "Exactly what it queried." Hotspot on trace row: "Real OTel data. Not hallucinated — retrieved." Hotspot on output: "From a raw trace to a named TOCTOU pattern. Full chain — visible, auditable, reproducible." |

---

## Scene 6 — VS Code fix (Copilot Agent Mode)

**Before recording:** Check out `demo/inventory-refactor` in VS Code, open `backend/services/inventory_service.py`, open Copilot chat (`Cmd+Shift+I`), confirm "Agent" mode, clear chat history.

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | File open, Copilot Agent Mode panel empty | ✅ Cap 6a | Hotspot on status bar / `.vscode/mcp.json` ref: "`.vscode/mcp.json` is committed to the repo. Every developer gets the MCP connection automatically — no setup, no API key configuration." |
| --- | --- | --- | --- |
| 2 | Type prompt (don't send): `I got a PR comment on backend/services/inventory_service.py reserve() saying it matches a trace pattern from 6 weeks ago. Pull those traces and help me understand what I need to fix — only that file.` | ✅ Cap 6b | Hotspot on typed prompt: "Natural language. No dashboard. No API call. No ticket number." |
| --- | --- | --- | --- |
| 3 | Press Enter | | |
| --- | --- | --- | --- |
| 4 | Response streaming — MCP tool call visible in progress | ✅ Cap 6c — auto-advance 2s | Hotspot on tool call indicator: (none — let the tool call speak for itself) |
| --- | --- | --- | --- |
| 5 | Mid-stream: incident evidence section appearing | ✅ Cap 6d — auto-advance 2s | |
| --- | --- | --- | --- |
| 6 | Full response visible — ends with "If you want, I can patch `inventory_service.py` now…" | ✅ Cap 6e | Hotspot on final offer line: "Root cause named. Fix proposed. It's waiting for one word." |
| --- | --- | --- | --- |
| 7 | Type `yes` and press Enter | | |
| --- | --- | --- | --- |
| 8 | Fix applied, tests written, tests ran — "2 files changed / Keep / Undo" bar appears | ✅ Cap 6f | Hotspot on bar + test output: "Fixed the service. Wrote a regression test. Ran it. All passed. One word typed." |
| --- | --- | --- | --- |
| 9 | Click **Keep** → switch to Source Control panel | ✅ Cap 6g | Hotspot on diff: "One condition added back. The atomic guard. That's the fix. The same guard the PR removed." |

**Re-take:** `./scene7-prep.sh` (cleans up Copilot changes, switches branch) → `./control.sh reset` (fresh PR) → switch VS Code back to `demo/inventory-refactor`, clear Copilot chat

---

## Scene 7 — Harness confirms the fix (Terminal)

**Before recording:** After Scene 6, run from repo root (while still on `demo/inventory-refactor`):
```
./scene7-prep.sh
```
Discards Copilot changes, removes the test file, switches to `feature/msft-build-2026`.

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | Terminal with command typed (not run): `python3 scripts/msbuild_harness.py l1` | ✅ Cap 7a | Hotspot on command: "This is the concurrency harness. 20 simultaneous reservation requests — simulating 20 customers all trying to buy the last unit at once." |
| --- | --- | --- | --- |
| 2 | Run it — "firing 20 parallel reservations…" scrolling | ✅ Cap 7b — auto-advance 2s | |
| --- | --- | --- | --- |
| 3 | Final output shows PASS with these key lines: `firing 20 parallel reservations… / 1 / 20 requests succeeded (reserved: true) / ✓ atomic behavior: exactly 1 reservation succeeds  got 1, want 1 / PASS` | ✅ Cap 7c | Hotspot on the four key lines: "20 customers. 1 unit. Exactly 1 reservation succeeded. Nineteen got `reserved: false`. No oversell. This is the test that should have caught the bug at PR time — and now it will, automatically, on every future PR." |

**Re-take:** `docker compose restart backend`

---

## Scene 8 — Close / CTA (static slide)

**Captures:** 1 — three takeaway bullets + Instruqt lab link

| # | Action | Capture? | Highlight / Hotspot |
|---|--------|----------|---------------------|
| 1 | Closing slide with three takeaway bullets | ✅ Cap 8a | Hotspot bullet 1: "Elastic Agent Builder: production-grade AI orchestration, built into Kibana. No infra team required." Hotspot bullet 2: "OTel traces as AI grounding: the agent retrieved a 6-week-old incident and named its pattern. Not from training data — from your data." Hotspot bullet 3: "Skills encode expertise once, attach to any agent. The team's knowledge travels with every agent they build." |

---

## Re-take Cheat Sheet

| Scene | Reset command | Extra step |
|-------|---------------|------------|
| 2 — PR creation | `./control.sh stage` | Open the two URLs it prints in order |
| --- | --- | --- |
| 3 — Bot comment | `./control.sh reset` | Wait ~60s for bot comment |
| --- | --- | --- |
| 4 — Actions proof | `./control.sh reset` | Wait ~90s for action to complete |
| --- | --- | --- |
| 5 — Kibana | None | Re-navigate from Agent Builder home — Kibana state is read-only |
| --- | --- | --- |
| 6 — VS Code fix | `./scene7-prep.sh` then `./control.sh reset` | Switch VS Code back to `demo/inventory-refactor`, clear Copilot chat |
| --- | --- | --- |
| 7 — Harness | `docker compose restart backend` | Must be on `feature/msft-build-2026` |
