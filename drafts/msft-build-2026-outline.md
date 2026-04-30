# MS Build 2026 — Session Outline Draft
_As of: 2026-04-30_

---

## Session ID
_(MS Build assigns — leave blank or enter TBD)_

## Title
Give Your AI Reviewer a Memory: Production-Aware PRs with Copilot, Elastic, and Azure AI

---

## Goals
1. Understand how OTel traces and incident postmortems stored in Elasticsearch give Copilot production memory that raw code review lacks
2. Learn how a single Elastic MCP server connects to VS Code Copilot Agent Mode and GitHub Actions without re-wiring — configure once, works everywhere
3. Walk away with a working pattern for catching concurrency/race regressions at PR time using semantic pattern matching against real trace data

## Leave Behind Resources
1. GitHub repo: Wayfinder Supply Co — full demo code, MCP server, harness scripts, `.vscode/mcp.json` template (link TBD — confirm public before submission)
2. Elastic Agent Builder + Workflows quickstart docs — elastic.co/agent-builder
3. Architecture diagram (4-box: GitHub → Elastic Workflow → Agent Builder → Azure AI Foundry) — available in session slide deck

## Nurture (Marketing/Sales alignment)
Positions Copilot Agent Mode + MCP as the developer-facing entry point for Elastic intelligence; validates the GitHub + Elastic + Azure AI Foundry trio as a production-ready stack; supports Azure AI Foundry adoption by showing a real integration pattern developers can replicate in under a day.

---

## Session Flow — 25 Minutes

### Act One: The Problem — Your AI Reviewer Has Amnesia (~5 min)

| Session flow | Content type | Minutes | Speaker |
|---|---|---|---|
| Introduction — "Your AI code reviewer has amnesia" cold open | SPEAKER-ONLY | 1 | Jeff Vestal |
| Architecture overview — 4-box diagram: GitHub → Elastic Workflow → Agent Builder → Azure AI Foundry | GRAPHICS | 1 | Jeff Vestal |
| Open demo PR (`perf: split inventory read/write for query plan cache efficiency`) — walk through the diff, explain why it looks like a safe perf tweak | DEMO | 3 | Jeff Vestal |

### Act Two: Give Copilot a Memory (~13 min)

| Session flow | Content type | Minutes | Speaker |
|---|---|---|---|
| GitHub Action fires → Elastic Workflow invokes Agent Builder → PR comment appears citing trace evidence + historical incident match | DEMO | 4 | Jeff Vestal |
| Switch to VS Code Copilot Agent Mode — MCP tool call pulls live OTel traces from Elasticsearch, Copilot proposes the fix | DEMO | 5 | Jeff Vestal |
| Apply fix; run concurrency harness (20 parallel requests, stock of 1) + brief Kibana latency flash — exactly 1 reservation wins | DEMO | 4 | Jeff Vestal |

### Act Three: Key Event Takeaways (~3 min)

| Session flow | Content type | Minutes | Speaker |
|---|---|---|---|
| 3 takeaways: memory matters / MCP portability / pattern is general | SPEAKER-ONLY | 2 | Jeff Vestal |
| What's available: call out related sessions, repo link, elastic.co/agent-builder next steps | GRAPHICS | 1 | Jeff Vestal |

### Q&A (optional)

| Session flow | Content type | Minutes | Speaker |
|---|---|---|---|
| Audience Q&A through chat | Q&A | 4 | Jeff Vestal |

**Timing check: 5 + 13 + 3 = 21 min scripted + 4 min Q&A = 25 min**

---

## Fields Requiring Jeff's Input Before Submission

These are typically required by conference portals but were not visible in the outline template screenshot:

| Field | Value |
|---|---|
| **Abstract/Description** | _(~150 words — draft below)_ |
| **Audience level** | 300 (Developer / Platform Engineer / SRE) |
| **Track/Topic** | AI + GitHub Copilot (confirm with MS contact) |
| **Speaker bio** | Jeff Vestal, Staff Developer Advocate, Elastic |
| **Prerequisites** | Basic GitHub and VS Code familiarity; no Elastic experience required |
| **Session format** | Breakout (confirm: theater vs. breakout) |
| **Recording consent** | Jeff to confirm |
| **Co-presenters** | None (solo) |

### Abstract Draft
Your AI code reviewer reads every diff — but it has no memory of what took down production at 2am three months ago. In this session, you'll see how to fix that. We'll build a production-aware PR review pipeline using GitHub Copilot, Elastic Agent Builder, and Azure AI Foundry. A GitHub Action triggers an Elastic Workflow that invokes an AI agent with access to two sources of memory: OpenTelemetry traces and historical incident postmortems — both stored in Elasticsearch. The agent reads the diff, matches against known failure patterns, and posts a code review comment before a human ever opens the PR. Then we switch to VS Code Copilot Agent Mode, connected to the same Elastic MCP server, to investigate and fix the issue. One MCP server. Two entry points. A reviewer that remembers.
