.PHONY: help dev prod setup-dev setup-prod build-dev build-prod up-dev up-prod down-dev down-prod logs test clean

# Colors for better visibility
BLUE=\033[0;34m
GREEN=\033[0;32m
RED=\033[0;31m
NC=\033[0m # No Color

# Docker compose files
DC_DEV=docker-compose.yml
DC_PROD=docker-compose.prod.yml

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@awk '/^[a-zA-Z0-9_-]+:.*?## .*$$/ {printf "  ${BLUE}%-20s${NC} %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development commands
setup-dev: ## Setup development environment
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "${GREEN}Created .env file from template${NC}"; \
	fi
	make build-dev
	make up-dev
	make migrate-dev

build-dev: ## Build development services
	docker-compose -f $(DC_DEV) build

up-dev: ## Start development services
	docker-compose -f $(DC_DEV) up -d

down-dev: ## Stop development services
	docker-compose -f $(DC_DEV) down

# Production commands
setup-prod: ## Setup production environment
	@if [ ! -f .env.prod ]; then \
		cp .env.example .env.prod; \
		echo "${RED}Please update .env.prod with secure credentials${NC}"; \
		exit 1; \
	fi
	make build-prod
	make up-prod
	make migrate-prod

build-prod: ## Build production services
	docker-compose -f $(DC_PROD) build

up-prod: ## Start production services
	docker-compose -f $(DC_PROD) up -d

down-prod: ## Stop production services
	docker-compose -f $(DC_PROD) down

# Common commands
logs: ## View logs
	@if [ "$(env)" = "prod" ]; then \
		docker-compose -f $(DC_PROD) logs -f; \
	else \
		docker-compose -f $(DC_DEV) logs -f; \
	fi

migrate-dev: ## Run migrations (development)
	docker-compose -f $(DC_DEV) run --rm web python manage.py migrate

migrate-prod: ## Run migrations (production)
	docker-compose -f $(DC_PROD) run --rm web python manage.py migrate

test: ## Run tests
	docker-compose -f $(DC_DEV) run --rm web python manage.py test

clean: ## Clean up all containers and volumes
	docker-compose -f $(DC_DEV) down -v --remove-orphans
	docker-compose -f $(DC_PROD) down -v --remove-orphans
	docker builder prune -f

# Development utilities
shell-dev: ## Start a shell in development web container
	docker-compose -f $(DC_DEV) exec web bash

shell-prod: ## Start a shell in production web container
	docker-compose -f $(DC_PROD) exec web bash

lint: ## Run linting
	docker-compose -f $(DC_DEV) run --rm web flake8 .

format: ## Format code
	docker-compose -f $(DC_DEV) run --rm web black .

# Health checks
health-dev: ## Check development services health
	@echo "Checking development services health..."
	@docker-compose -f $(DC_DEV) ps

health-prod: ## Check production services health
	@echo "Checking production services health..."
	@docker-compose -f $(DC_PROD) ps

# SSL management
ssl-create: ## Create self-signed SSL certificate for development
	@mkdir -p ssl
	@openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout ssl/privkey.pem \
		-out ssl/fullchain.pem \
		-subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

ssl-check: ## Check SSL certificate expiration
	@if [ -f ssl/fullchain.pem ]; then \
		openssl x509 -in ssl/fullchain.pem -text -noout | grep -A 2 "Validity"; \
	else \
		echo "${RED}SSL certificate not found${NC}"; \
	fi

# Deployment management
deploy-prod: ## Deploy to production
	@echo "${GREEN}Deploying to production...${NC}"
	make build-prod
	make migrate-prod
	make up-prod
	@echo "${GREEN}Deployment complete${NC}"

deploy-rollback: ## Rollback to previous version
	@echo "${RED}Rolling back to previous version...${NC}"
	docker-compose -f $(DC_PROD) down
	docker-compose -f $(DC_PROD) up -d --scale web=2 --no-recreate db redis
	@echo "${GREEN}Rollback complete${NC}"

# Monitoring
monitor-prod: ## Monitor production services
	@echo "Checking services status..."
	@docker-compose -f $(DC_PROD) ps
	@echo "\nChecking resource usage..."
	@docker stats --no-stream $(docker-compose -f $(DC_PROD) ps -q)

# Backup
backup-db: ## Backup production database
	@echo "Creating database backup..."
	@docker-compose -f $(DC_PROD) exec db pg_dump -U $(DB_USER) -d $(DB_NAME) | gzip > backup-$(shell date +%Y%m%d%H%M%S).sql.gz

# Multi-architecture builds
buildx-setup: ## Setup Docker BuildX for multi-architecture builds
	@docker buildx create --name multiarch-builder --use || true
	@docker buildx inspect --bootstrap

buildx-build: ## Build multi-architecture images
	@echo "${GREEN}Building multi-architecture images...${NC}"
	@docker buildx build \
		--platform linux/amd64,linux/arm64,linux/arm/v7 \
		--tag $(REGISTRY)/reconpoint-web:latest \
		--push \
		.

