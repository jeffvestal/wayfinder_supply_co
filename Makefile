.PHONY: help setup generate seed deploy validate clean test

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
	rm -rf public/images/products/*.jpg
	rm -rf public/images/products/*.png
	rm -rf backend/__pycache__ mcp_server/__pycache__ scripts/__pycache__
	rm -rf backend/**/__pycache__ mcp_server/**/__pycache__
	@echo "Clean complete!"


