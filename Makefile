.PHONY: help setup generate seed deploy validate clean test \
	msbuild-traces msbuild-index-traces msbuild-validate-traces msbuild-verify-esql \
	msbuild-issues msbuild-agent msbuild-workflow msbuild-deploy-all \
	msbuild-harness-preflight msbuild-harness-l1 msbuild-harness-l2 msbuild-harness-l3 msbuild-harness-all

help:
	@echo "Wayfinder Supply Co. - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Install all dependencies"
	@echo "  make generate       - Generate sample product data"
	@echo "  make seed           - Seed Elasticsearch with data"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy         - Deploy workflows and create agents"
	@echo "  make validate       - Validate setup"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Start all services in development mode"
	@echo "  make test           - Run validation tests"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Clean generated files"

setup:
	@echo "Setting up Python environments..."
	cd backend && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	cd mcp_server && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	@echo "Setting up Node.js dependencies..."
	cd frontend && npm install
	@echo "Setup complete!"

generate:
	@echo "Generating sample product data..."
	python3 scripts/generate_sample_data.py

seed:
	@echo "Seeding Elasticsearch..."
	python3 scripts/setup_elastic.py
	python3 scripts/seed_products.py
	python3 scripts/seed_clickstream.py
	@echo "Seeding complete!"

deploy:
	@echo "Deploying workflows..."
	python3 scripts/deploy_workflows.py
	@echo "Creating agents..."
	python3 scripts/create_agents.py
	@echo "Deployment complete!"

validate:
	@echo "Validating setup..."
	python3 scripts/validate_setup.py

dev:
	@echo "Starting development services..."
	docker-compose up

test: validate
	@echo "Running tests..."
	@echo "Tests complete!"

clean:
	@echo "Cleaning generated files..."
	rm -rf generated_products/*.json
	rm -rf frontend/public/images/products/*.jpg
	rm -rf frontend/public/images/products/*.png
	rm -rf backend/__pycache__ mcp_server/__pycache__ scripts/__pycache__
	rm -rf backend/**/__pycache__ mcp_server/**/__pycache__
	@echo "Clean complete!"

# ============================================
# MS Build 2026 demo targets
# ============================================

msbuild-traces:
	python3 scripts/generate_baseline_traces.py
	python3 scripts/generate_incident_traces.py

msbuild-index-traces:
	echo "yes" | python3 scripts/index_traces.py --files generated_traces/baseline_traces.jsonl generated_traces/incident_traces.jsonl --production

msbuild-validate-traces:
	python3 scripts/validate_traces.py

msbuild-verify-esql:
	python3 scripts/verify_esql_search.py

msbuild-issues:
	python3 scripts/create_postmortem_issues.py

msbuild-agent:
	python3 scripts/create_msbuild_agent.py

msbuild-workflow:
	python3 scripts/deploy_msbuild_workflow.py

# One-shot: traces + issues + agent + workflow. Assumes .env + GH auth configured.
msbuild-deploy-all: msbuild-traces msbuild-index-traces msbuild-validate-traces msbuild-issues msbuild-agent msbuild-workflow
	@echo "MS Build deploy complete. Set GH secrets next:"
	@echo "  gh secret set ELASTIC_WORKFLOW_URL --body '<url>'"
	@echo "  gh secret set ELASTIC_WORKFLOW_KEY --body 'ApiKey <b64>'"

msbuild-harness-preflight:
	python3 scripts/msbuild_harness.py preflight

msbuild-harness-l1:
	python3 scripts/msbuild_harness.py l1

msbuild-harness-l2:
	python3 scripts/msbuild_harness.py l2

msbuild-harness-l3:
	python3 scripts/msbuild_harness.py l3

msbuild-harness-all:
	python3 scripts/msbuild_harness.py all


