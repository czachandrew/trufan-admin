.PHONY: help build up down restart logs shell db-shell migrate seed test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker containers
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "Services started. API available at http://localhost:8000"
	@echo "API docs at http://localhost:8000/api/v1/docs"

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

logs-api: ## View API logs only
	docker-compose logs -f api

shell: ## Open shell in API container
	docker-compose exec api /bin/bash

db-shell: ## Open PostgreSQL shell
	docker-compose exec db psql -U trufan -d trufan

redis-shell: ## Open Redis CLI
	docker-compose exec redis redis-cli

migrate: ## Run database migrations
	docker-compose exec api alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create message="description")
	docker-compose exec api alembic revision --autogenerate -m "$(message)"

migrate-down: ## Rollback last migration
	docker-compose exec api alembic downgrade -1

seed: ## Seed database with sample data
	docker-compose exec api python /app/../scripts/seed_data.py

test: ## Run tests
	docker-compose exec api pytest

test-cov: ## Run tests with coverage
	docker-compose exec api pytest --cov=app --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	docker-compose exec api pytest-watch

lint: ## Run code linting
	docker-compose exec api flake8 app
	docker-compose exec api black --check app

format: ## Format code with black
	docker-compose exec api black app

clean: ## Remove containers, volumes, and generated files
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/htmlcov
	rm -rf backend/.pytest_cache
	rm -rf backend/.coverage

setup: build up migrate seed ## Complete setup (build, start, migrate, seed)
	@echo ""
	@echo "=========================================="
	@echo "TruFan Backend Setup Complete!"
	@echo "=========================================="
	@echo ""
	@echo "API is running at: http://localhost:8000"
	@echo "API docs: http://localhost:8000/api/v1/docs"
	@echo ""
	@echo "Sample login credentials:"
	@echo "  Admin: admin@trufan.com / Admin123!"
	@echo "  Customer: customer1@example.com / Customer123!"
	@echo ""

dev: ## Start development environment
	docker-compose up

health: ## Check service health
	@echo "Checking API health..."
	@curl -s http://localhost:8000/health | python -m json.tool

install-local: ## Install dependencies locally
	cd backend && pip install -r requirements.txt

run-local: ## Run API locally (without Docker)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
