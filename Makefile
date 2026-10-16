SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

UV ?= uv
# Targets whose milestone has not landed yet fail loudly instead of pretending.
todo = @echo "make $@: not implemented yet (lands in $(1), see docs/PLAN.md)" >&2; exit 1

.PHONY: help setup lint fmt test check smoke-gemini gcp-setup gcp-budget gcp-wif \
        resolve ingest spotcheck fixtures index index-e4 publish-index eval-retrieval mcp-dev mcp-coldstart agent-dev \
        eval-smoke eval-smoke-remote eval-full eval-multiturn silver review-golden check-cases \
        label-answers judge-study query-remote deploy-mcp deploy-agent deploy-web \
        web-install web-dev web-check gcp-web

help: ## List targets
	@grep -E '^[a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

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

gcp-wif: ## Workload Identity Federation for GitHub Actions -> swiss-nav-ci@ (DRY_RUN=1 to preview)
	bash infra/wif.sh

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

index: ## Embed (cached by content; billable on a cold cache) + build data/index.sqlite
	$(UV) run python -m ingest.index

index-e4: ## E4 experiment index: every tokenizer and vector space (billable on a cold cache)
	$(UV) run python -m ingest.index --experiment

publish-index: ## Upload data/index.sqlite for CI (by sha256) + write evals/ci_index.json (commit it)
	$(UV) run python -m scripts.ci_index publish

eval-retrieval: ## Retrieval eval of the served config (E4=1: the whole E4 grid) -> evals/reports/
	$(UV) run python -m evals.harness.retrieval_eval $(if $(E4),--e4 --index data/index_e4.sqlite --latency 20)

mcp-dev: ## swiss-law MCP server on http://127.0.0.1:8080/mcp (STDIO=1: stdio)
	$(UV) run python -m mcp_server.server $(if $(STDIO),,--http)

mcp-coldstart: ## Time connect + first searches against SWISS_LAW_MCP_URL (or URL=...; ADR-017)
	$(UV) run python -m scripts.cold_start $(URL)

agent-dev: ## adk web UI for the agents in agents/
	$(UV) run adk web agents

eval-smoke: ## 20-case smoke eval (agent + judge; billable, ~CHF 1) -> evals/reports/ (ARGS=...)
	$(UV) run python -m evals.harness.answer_eval --smoke $(ARGS)

eval-smoke-remote: ## The smoke eval against the deployed agent (AGENT_RUNTIME_ID; billable, ~CHF 1; ARGS=...)
	$(UV) run python -m evals.harness.answer_eval --smoke --target remote $(ARGS)

query-remote: ## One question to the deployed agent, streamed (Q="..."; ARGS=--traces checks Cloud Trace)
	$(UV) run python -m scripts.query_remote $(ARGS) "$(Q)"

eval-multiturn: ## 25 simulated conversations via ADK AgentEvaluator + rubric judge (billable, ~CHF 3; ARGS=...)
	$(UV) run python -m evals.harness.multiturn $(ARGS)

eval-full: ## Every case of golden (drafts until it exists); M4 adds adversarial.jsonl (ARGS=...)
	$(UV) run python -m evals.harness.answer_eval $(ARGS)

silver: ## Generate evals/datasets/silver.jsonl (~400 single-article cases; billable, < CHF 1; ARGS=--dry-run)
	$(UV) run python -m evals.harness.silver $(ARGS)

review-golden: ## Review drafted golden cases against the article text: accept/edit/reject (ARGS=...)
	$(UV) run python -m evals.harness.review $(ARGS)

label-answers: ## Human labels for the judge study: grade stored answers claim by claim (ARGS=...)
	$(UV) run python -m evals.harness.label $(ARGS)

judge-study: ## Grade stored answers with JUDGES=model@loc[:thinking],... vs human labels (billable; ARGS=--from F is free)
	$(UV) run python -m evals.harness.judge_study $(if $(JUDGES),--judges $(JUDGES)) $(ARGS)

check-cases: ## Schema, unique ids and expected citations of every eval case file (no model calls)
	$(UV) run python -m evals.harness.check_cases $(ARGS)

deploy-mcp: ## Build + push + Cloud Run deploy of the MCP server (ask first; DRY_RUN=1 to preview)
	bash infra/deploy_mcp.sh

deploy-agent: ## Stage + deploy navigator to Agent Runtime (ask first; DRY_RUN=1 to preview; GCP.md §4)
	bash infra/deploy_agent.sh

deploy-web: ## Build + push + Cloud Run deploy of the web UI (ask first; DRY_RUN=1 to preview; GCP.md §4)
	bash infra/deploy_web.sh

gcp-web: ## Firestore database, access-code secret, IAM for the web BFF (ask first; DRY_RUN=1; ROTATE=1)
	bash infra/web_setup.sh

# The lock comes from npm 11: npm 10 (bundled with Node 22) fails on its optional peer set.
NPM ?= npx -y npm@11.6.2

web-install: ## Install the web app's locked deps (web/node_modules)
	cd web && $(NPM) ci

web-check: ## web: eslint + prettier, tsc, vitest (what CI runs)
	cd web && $(NPM) run check

web-dev: ## Next.js dev server on :3000 against AGENT_RUNTIME_ID (memory quotas; code WEB_ACCESS_CODE or local-dev-code)
	set -a; source .env; set +a; cd web && \
	  ACCESS_CODE="$${WEB_ACCESS_CODE:-local-dev-code}" QUOTA_BACKEND=memory $(NPM) run dev
