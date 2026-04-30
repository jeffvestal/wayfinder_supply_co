# MS Build 2026 — Remaining TODO
_Last updated: 2026-04-27_

## Block 1: Deploy the Elastic pieces
_(do in order — dependencies)_

- [ ] Run `python3 scripts/create_msbuild_agent.py` — create Agent Builder agent + 3 ES|QL tools (or verify already exists in Kibana)
- [ ] Run `python3 scripts/add_otel_agent_tool.py` — register OTel MCP tool on the agent
- [ ] Run `python3 scripts/deploy_msbuild_workflow.py` — deploy the Elastic Workflow

## Block 2: Wire GitHub side
_(can parallel with Block 1 after step 1)_

- [ ] Confirm GitHub MCP connector in Agent Builder has read (PR diff) + write (post comment) scope
- [ ] Confirm/configure Elastic GitHub Connector to ingest Wayfinder Issues → `github-issues-wayfinder` ES index
- [ ] Verify ES|QL semantic search on issues index returns #5/#6 for query: `inventory reserve concurrent lock contention`

## Block 3: Validate Azure + VS Code

- [ ] Confirm Azure OpenAI connector in Agent Builder accepts Azure AI Foundry endpoint _(load-bearing for abstract — 30 min spike)_
- [ ] Hit `{KIBANA_URL}/api/agent_builder/mcp`, list tools, confirm ES search/query tools work from VS Code Copilot Agent Mode

## Block 4: End-to-end validation

- [ ] Run `demo_reset.sh` twice — confirm clean PR close + reopen cycle, no errors
- [ ] Run `python3 scripts/msbuild_harness.py all` — L1 + L2 + L3 all green

## Block 5: Presentation assets
_(hard deadlines)_

- [ ] **May 5** — Session outline submitted
- [ ] Architecture diagram slide (one clean diagram)
- [ ] **May 19** — Full slides deck uploaded
- [ ] Pre-recorded demo backup (conference wifi insurance)

## Optional / bonus

- [ ] Try elastic-ramen as bonus demo beat — terminal investigation → syncs back to Kibana (already on Serverless, should just connect)
