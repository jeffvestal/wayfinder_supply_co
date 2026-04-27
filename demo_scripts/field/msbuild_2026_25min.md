# MS Build 2026 Session — 25 Minute Live Demo

**Title:** Give Your AI Reviewer a Memory: Production-Aware PRs with Copilot, Elastic, and Azure AI
**Duration:** 25 min (≈3 min slides + 22 min live + 2 min close)
**Audience:** Developers, platform engineers, SREs
**Speaker:** Jeff Vestal

---

## Pre-Stage Checklist (run in order, ~15 min before showtime)

1. **Run the harness**: `make msbuild-harness-all` — must exit 0. If any tier fails, abort and switch to pre-recorded backup (`msbuild_2026_prerecorded.md`).
2. **Fire a warmup PR**: open a draft PR on `demo/inventory-refactor` → close it. This wakes Cloud Run + Workflow cold paths.
3. **Freeze ingest**: in Kibana → GitHub Connector → disable scheduled sync. Prevents surprise re-indexing on stage.
4. **Pre-warm backend**: `curl $WAYFINDER_BACKEND_URL/health` — must return 200.
5. **Tabs open, ordered L→R**:
   - GitHub: the Wayfinder repo, `feature/msft-build-2026` branch
   - GitHub: the (as-yet-unopened) Compare page for `demo/inventory-refactor` → `feature/msft-build-2026`
   - VS Code with Wayfinder checked out, `.vscode/mcp.json` already trusted, Agent Mode panel open
   - Kibana → Discover on `traces-apm.wayfinder-default` (as the safety net for “show me the trace”)
   - Slide deck (on clicker, not main screen)
6. **Verify bot account**: the agent posts comments as `elastic-agent-review[bot]` — not Jeff. Do a 5-second pre-check on the warmup PR comment.
7. **Have backup ready**: pre-recorded MP4 cued up and mirrored. If wifi drops, stop talking live, switch to recording, narrate over it.

---

## Scene 1 — Cold Open (0:00–1:00)

**Talk Track:**
1. "Your AI code reviewer has amnesia."
2. "It knows your codebase. It reads every PR."
3. "But it has no idea what took down production at 2am three months ago — and that is the exact pattern about to ship again."
4. "Today I'm going to show you how to give Copilot a memory."

**Screen:** Slide 1 — title.

**Fallback:** none (this is all speaker).

---

## Scene 2 — Architecture (1:00–2:00)

**Talk Track:**
1. "Here's the shape. One diagram, four boxes."
2. "Developer opens a PR in GitHub. A GitHub Action fires and calls an Elastic Workflow. The Workflow invokes an Agent Builder agent. The agent has two sources of memory: OTel traces, and historical incident postmortems. It reads the diff, correlates against both, and if it sees a pattern it has seen before, it posts a comment on the PR."
3. "Then we switch to VS Code, Copilot Agent Mode, and the same trace data — the same MCP server — helps the developer write the fix."
4. "Azure AI Foundry powers the reasoning. GitHub, Elastic, Azure — together."

**Screen:** Slide 2 — architecture diagram (4 boxes + arrows).

**Fallback:** skip talk #3 if running long; diagram speaks for itself.

---

## Scene 3 — Open the PR (2:00–5:00)

**Talk Track:**
1. "I've got a branch called `demo/inventory-refactor`. One file changed. Let me open the PR."
2. _(click PR create)_ "Title: `perf: split inventory read/write for query plan cache efficiency`. Looks like a reasonable perf tweak."
3. _(show diff)_ "Here's the change. The original code used a single atomic `UPDATE … WHERE quantity >= N`. The refactor splits it into a read, then an unconditional write with a pre-computed value."
4. "Read it carefully. No one says 'race condition'. No one says 'deadlock'. The PR description talks about prepared statement cache hit rates."
5. "In code review culture, this is a merge-on-sight PR. It is also a production incident waiting to happen."

**Screen state:** GitHub PR page, diff tab, `inventory_service.py` change visible.

**Actions:**
1. Click **Create pull request**.
2. Scroll to the diff section. Highlight the removed `AND quantity >= {n}` guard.

**Fallback:** if PR create fails (GitHub outage), use the pre-opened warmup PR from step 2 of pre-stage.

---

## Scene 4 — Agent Responds (5:00–9:00)

**Talk Track:**
1. "Watch the Checks section. The Elastic Agent Review action just fired."
2. _(action goes green)_ "Now we wait. The GitHub Action has posted to an Elastic Workflow. The Workflow calls our Agent Builder agent. The agent is reading the diff right now."
3. _(comment appears)_ "There we go. Let's read what the agent said."
4. _(read the comment aloud, pulling out these beats)_
   - "It found Issue #N — our incident from six weeks ago."
   - "It cites specific trace evidence: span duration of 6.2 seconds, HTTP route `/api/v1/checkout/reserve`, dates matching the incident window."
   - "It names the **pattern**: non-atomic read-modify-write. Not the keyword. The pattern."
5. "That is the jump that matters. The diff never says 'race' or 'deadlock'. The PR body talks about caching. The agent matched the *semantic pattern*, not the words."

**Screen state:** PR Conversation tab, agent comment expanded.

**Timing:** agent should respond in 30-120s. If it takes longer, stall with Scene 4-stall below.

**Scene 4-stall (if agent slow):**
1. "While this runs, let me show you what's under the hood." → switch tab to Kibana → Agent Builder → show the agent configuration (tools list, the three ES|QL tools).
2. When comment appears on PR, switch back and resume from talk #3.

**Fallback:** if comment never appears, switch to pre-recorded backup for this scene only.

---

## Scene 5 — VS Code Handoff (9:00–14:00)

**Talk Track:**
1. "The comment told me what the pattern is. Now I need to fix it. Let me bring Copilot into the conversation."
2. _(switch to VS Code, open Agent Mode panel)_ "I've got Copilot Agent Mode configured to talk to our Elastic MCP server — that config lives in `.vscode/mcp.json`, committed to the repo, so every developer on the team gets it for free."
3. _(type first prompt)_ "I got a PR comment on this inventory.reserve change saying it matches a trace pattern from six weeks ago. Pull those traces and help me understand what I need to fix."
4. _(Copilot invokes Elastic MCP tool; trace data returned)_ "Copilot just called our MCP server, ran an ES|QL query, got the actual trace spans back."
5. _(type second prompt)_ "Okay. What change do I need to make to avoid this pattern?"
6. _(Copilot proposes fix — atomic UPDATE)_ "That is the fix. Apply it." _(apply)_
7. "MCP is an open standard. This same Elastic MCP server works in Claude Desktop, in Cursor, in any MCP-aware client. Configure once, use everywhere."

**Screen state:** VS Code, Copilot Agent Mode panel open on right, `inventory_service.py` in main editor.

**Fallback:** if Copilot balks or returns nothing useful, narrate the expected result off the pre-rehearsed prompt and manually apply the known-good fix from clipboard.

---

## Scene 6 — Traces Confirm (14:00–16:00)

**Talk Track:**
1. "One more thing. Let me re-run the concurrency test."
2. _(switch to terminal, run `make msbuild-harness-l1` on the fixed branch)_
3. "Twenty parallel requests, stock of one. With the fix, exactly one wins. The other nineteen get `reserved: false`. That is the correct answer."
4. _(briefly show the harness output)_
5. "And if I were to re-run against the buggy branch: multiple reservations succeed, oversell reproduced. This is the test that would have caught the bug at PR time — and it is what the agent is effectively doing, but with institutional memory instead of a synthetic load."

**Screen state:** terminal with harness output; briefly flash Kibana latency chart if time permits.

**Fallback:** if harness fails live, skip to Scene 7.

---

## Scene 7 — Close (16:00–18:00)

**Talk Track:**
1. "Three things to take away."
2. "One: your AI reviewer should have memory. Code awareness is table stakes. Telemetry + postmortems is the unlock."
3. "Two: the pattern is general. Any agent, any source of memory, any review surface — PRs, designs, incident tickets."
4. "Three: MCP makes this portable. The Elastic MCP server worked in a GitHub Action flow and in VS Code Copilot Agent Mode without re-wiring anything."
5. "GitHub Copilot. Elastic. Azure AI. Together — a reviewer with memory. Thanks."

**Screen state:** close slide with logos + session hashtag.

---

## Timing Budget

| Scene | Planned | Hard cap |
|---|---|---|
| 1 Cold open | 1:00 | 1:15 |
| 2 Architecture | 1:00 | 1:15 |
| 3 Open PR | 3:00 | 3:30 |
| 4 Agent responds | 4:00 | 5:30 (agent latency buffer) |
| 5 VS Code handoff | 5:00 | 6:00 |
| 6 Traces confirm | 2:00 | 2:30 |
| 7 Close | 2:00 | 2:30 |
| Q&A / slack | 7:00 | — |

If agent latency blows through Scene 4 cap, drop Scene 6 entirely — it is the most expendable beat.

---

## Commands You Will Type Live

Copy-paste ready. Have these in a scratch file on the second monitor.

```bash
# Scene 3 — open PR (pre-canned command; or use UI)
gh pr create \
  --base feature/msft-build-2026 \
  --head demo/inventory-refactor \
  --title "perf: split inventory read/write for query plan cache efficiency" \
  --body "Pre-compute the new quantity value so the UPDATE is parameterized consistently, improving prepared statement cache hit rate under high throughput."

# Scene 6 — concurrency proof on the fixed branch
git checkout feature/msft-build-2026
./scripts/start_local.sh   # if backend not already running
python3 scripts/msbuild_harness.py l1
```

---

## Prompts for VS Code Agent Mode (Scene 5)

Type verbatim:

1. `I got a PR comment on this inventory.reserve change saying it matches a trace pattern from 6 weeks ago. Pull those traces and help me understand what I need to fix.`
2. `What change do I need to make to avoid this pattern?`

If Copilot drifts, steer with: `Use the Elastic MCP tools. Query traces-apm.wayfinder-default for http.route "/api/v1/checkout/reserve" where span duration exceeds 3 seconds.`
