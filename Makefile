SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

UV ?= uv
# Targets whose milestone has not landed yet fail loudly instead of pretending.
todo = @echo "make $@: not implemented yet (lands in $(1), see docs/PLAN.md)" >&2; exit 1

.PHONY: help setup lint fmt test check smoke-gemini gcp-setup gcp-budget \
        resolve ingest spotcheck fixtures index mcp-dev agent-dev eval-smoke eval-full \
        deploy-mcp deploy-agent deploy-web

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

setup: ## Install Python 3.12 + all workspace deps (locked) and the git hooks
	$(UV) sync --all-packages --locked
	$(UV) run pre-commit install

lint: ## ruff (lint + format check) and pyright
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(UV) run pyright

fmt: ## Auto-fix lint and formatting
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

test: ## Unit tests (integration tests: uv run pytest -m integration)
	$(UV) run pytest

check: lint test ## lint + test + every pre-commit hook on all files
	$(UV) run pre-commit run --all-files

smoke-gemini: ## One tiny call per profile model at its endpoint location (needs ADC)
	$(UV) run python -m scripts.smoke_gemini

gcp-setup: ## Idempotent APIs, Artifact Registry, bucket, SAs (DRY_RUN=1 to preview)
	bash infra/setup.sh

gcp-budget: ## Monthly budget alert at 50/90/100% (DRY_RUN=1 to preview)
	bash infra/budget.sh

resolve: ## Re-resolve acts.yaml on Fedlex -> corpus/manifest.lock.json (AS_OF=YYYY-MM-DD)
	$(UV) run python -m ingest.resolve $(if $(AS_OF),--as-of $(AS_OF))

ingest: ## Locked corpus -> data/articles.jsonl + corpus/stats.md (download is cached)
	$(UV) run python -m ingest.download
	$(UV) run python -m ingest.parse

spotcheck: ## Compare random articles with Fedlex's HTML rendering (N=10)
	$(UV) run python -m ingest.spotcheck --n $(or $(N),10)

fixtures: ## Re-cut the parser test fixtures from the cached corpus
	$(UV) run python -m ingest.tests.make_fixtures

index: ## Embed + build data/index.sqlite
	$(call todo,M2)

mcp-dev: ## Run the swiss-law MCP server locally
	$(call todo,M2)

agent-dev: ## adk web UI for the agents in agents/
	$(UV) run adk web agents

eval-smoke: ## 20-case smoke eval -> evals/reports/
	$(call todo,M3)

eval-full: ## Full golden + adversarial eval
	$(call todo,M4)

deploy-mcp: ## Cloud Run deploy of the MCP server (asks first; GCP.md §4)
	$(call todo,M2)

deploy-agent: ## Agent Runtime deploy (asks first; GCP.md §4)
	$(call todo,M5)

deploy-web: ## Cloud Run deploy of the web UI (asks first; GCP.md §4)
	$(call todo,M6)
