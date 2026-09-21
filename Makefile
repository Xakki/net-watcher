SHELL := /bin/sh
COMPOSE := docker compose -p net-watcher -f compose.yaml
BIND ?= $(shell if [ -f ./.env ]; then . ./.env; fi; printf '%s' "$${NET_WATCHER_BIND:-172.17.0.1:10210}")
PORT := $(lastword $(subst :, ,$(BIND)))
HOST := $(firstword $(subst :, ,$(BIND)))
URL := http://$(HOST):$(PORT)

.PHONY: help config build test lint up down ps logs smoke verify publish-check

help: ## Show the supported local commands.
	@printf '%s\n' 'Net Watcher local commands:'
	@awk 'BEGIN {FS = ":.*## "} /^[a-z-]+:.*## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

config: ## Validate the fixed local Compose configuration.
	@NET_WATCHER_BIND=$(BIND) $(COMPOSE) config --quiet
	@printf 'Compose configuration is valid (%s).\n' '$(BIND)'

build: ## Build the pinned local container image.
	@NET_WATCHER_BIND=$(BIND) $(COMPOSE) build

test: ## Run all standard-library mutation tests.
	@python3 -B -m unittest -v tests.test_verify_site tests.test_stage2_request tests.test_broker_runtime

lint: ## Scan the complete tracked public boundary.
	@python3 -B tools/verify_site.py --repository
	@git diff --check

up: ## Start the local isolated service; never publishes.
	@NET_WATCHER_BIND=$(BIND) $(COMPOSE) up -d --build

down: ## Stop and remove only local Net Watcher resources.
	@NET_WATCHER_BIND=$(BIND) $(COMPOSE) down --remove-orphans

ps: ## Show only local Net Watcher containers.
	@NET_WATCHER_BIND=$(BIND) $(COMPOSE) ps

logs: ## Follow only the local web service logs.
	@NET_WATCHER_BIND=$(BIND) $(COMPOSE) logs --tail=100 -f web

smoke: ## Check health, content, and security headers locally.
	@NET_WATCHER_BIND=$(BIND) $(COMPOSE) up -d --wait web
	@curl --fail --silent --show-error '$(URL)/healthz' | grep -qx 'ok'
	@curl --fail --silent --show-error '$(URL)/' | grep -q 'Net Watcher'
	@curl --fail --silent --show-error --head '$(URL)/' | grep -qi '^Content-Security-Policy:'
	@curl --fail --silent --show-error --head '$(URL)/' | grep -qi '^X-Content-Type-Options: nosniff'
	@curl --fail --silent --show-error --head '$(URL)/audit.md' | grep -qi '^Content-Type: text/plain; charset=utf-8'
	@printf 'Smoke checks passed at %s.\n' '$(URL)'

verify: config test lint ## Run all local non-publication checks.
	@printf 'Local verification passed. Publication approval is separate.\n'

publish-check: verify ## Fail closed until tracked publication decisions are final.
	@python3 -B tools/verify_site.py --repository --publish
