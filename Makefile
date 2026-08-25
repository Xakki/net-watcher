SHELL := /bin/sh
COMPOSE := docker compose -p net-watcher -f compose.yaml
PORT ?= 18137
URL := http://127.0.0.1:$(PORT)

.PHONY: help config build test lint up down ps logs smoke verify publish-check

help: ## Show the supported local commands.
	@printf '%s\n' 'Net Watcher local commands:'
	@awk 'BEGIN {FS = ":.*## "} /^[a-z-]+:.*## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

config: ## Validate the fixed local Compose configuration.
	@NET_WATCHER_PORT=$(PORT) $(COMPOSE) config --quiet
	@printf 'Compose configuration is valid (127.0.0.1:%s).\n' '$(PORT)'

build: ## Build the pinned local container image.
	@NET_WATCHER_PORT=$(PORT) $(COMPOSE) build

test: ## Run the standard-library verifier mutation tests.
	@python3 -B -m unittest -v tests.test_verify_site

lint: ## Scan the complete future public repository boundary.
	@python3 -B tools/verify_site.py --repository
	@git diff --check

up: ## Start the local isolated service; never publishes.
	@NET_WATCHER_PORT=$(PORT) $(COMPOSE) up -d --build

# Removing only this explicit Compose project prevents selector drift.
down: ## Stop and remove only local Net Watcher resources.
	@NET_WATCHER_PORT=$(PORT) $(COMPOSE) down --remove-orphans

ps: ## Show only local Net Watcher containers.
	@NET_WATCHER_PORT=$(PORT) $(COMPOSE) ps

logs: ## Follow only the local web service logs.
	@NET_WATCHER_PORT=$(PORT) $(COMPOSE) logs --tail=100 -f web

smoke: ## Check health, content, and security headers locally.
	@NET_WATCHER_PORT=$(PORT) $(COMPOSE) up -d --wait web
	@curl --fail --silent --show-error '$(URL)/healthz' | grep -qx 'ok'
	@curl --fail --silent --show-error '$(URL)/' | grep -q 'Net Watcher'
	@curl --fail --silent --show-error --head '$(URL)/' | grep -qi '^Content-Security-Policy:'
	@curl --fail --silent --show-error --head '$(URL)/' | grep -qi '^X-Content-Type-Options: nosniff'
	@printf 'Smoke checks passed at %s.\n' '$(URL)'

verify: config test lint ## Run all local non-publication checks.
	@printf 'Local verification passed. Publication approval is separate.\n'

publish-check: verify ## Fail closed until tracked publication decisions are final.
	@python3 -B tools/verify_site.py --repository --publish
