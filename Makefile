.PHONY: up down logs migrate test lint typecheck build requirements sh rebuild check-bins image-build

COMPOSE_FILE ?= docker-compose.yml

build: ## Build docker compose services
	docker compose -f $(COMPOSE_FILE) build

up: ## Start local stack
	docker compose -f $(COMPOSE_FILE) up -d

down: ## Stop local stack
	docker compose -f $(COMPOSE_FILE) down --remove-orphans

logs: ## Tail application logs
	docker compose -f $(COMPOSE_FILE) logs -f web

sh: ## Start an interactive shell in the web service
	docker compose -f $(COMPOSE_FILE) run --rm web sh

rebuild: ## Rebuild the web service without cache and restart it
	docker compose -f $(COMPOSE_FILE) build --no-cache web && docker compose -f $(COMPOSE_FILE) up -d web

check-bins: ## Verify required binaries and python packages inside the container
	docker compose -f $(COMPOSE_FILE) run --rm web sh -lc 'which python && which gunicorn && python -c "import fastapi, uvicorn, gunicorn; print(\'OK deps\')"'

migrate: ## Apply database migrations inside the web service
	docker compose -f $(COMPOSE_FILE) exec web alembic upgrade head

test: ## Run unit and integration tests
	poetry run pytest -q

lint: ## Run Ruff static analysis
	poetry run ruff check app tests

typecheck: ## Run mypy type checks
	poetry run mypy app

image-build: ## Build production image
	docker build -t dgii-ecf-web:latest -f Dockerfile .

requirements: ## Export locked dependencies for Docker builds
	poetry export --only main --without-hashes --format requirements.txt --output requirements.txt
