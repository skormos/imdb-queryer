COMPOSE  := docker compose
PIPELINE := $(COMPOSE) --profile pipeline run --rm --no-deps --build
DB_USER  ?= imdbreadonly

SHELL_SCRIPTS := $(wildcard postgres/initdb/*.sh) loader/load.sh
SHELLCHECK_IMAGE := koalaman/shellcheck:v0.10.0
TEST_IMAGE := imdb-python-tests

.DEFAULT_GOAL := help

# The pipeline steps (download -> parse -> load) must run in order; never run targets in parallel, even with -j.
.NOTPARALLEL:

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

## --- Running -------------------------------------------------------------

.PHONY: up
up: ## Start Postgres and pgAdmin with whatever data is already loaded
	$(COMPOSE) up -d --wait db
	$(COMPOSE) up -d pgadmin
	@echo "Postgres: localhost:$$($(COMPOSE) port db 5432 | head -1 | cut -d: -f2)"
	@echo "pgAdmin:  http://localhost:$$($(COMPOSE) port pgadmin 80 | head -1 | cut -d: -f2)"

.PHONY: down
down: ## Stop everything (all data is kept)
	$(COMPOSE) --profile pipeline down --remove-orphans

.PHONY: logs
logs: ## Follow the db and pgAdmin logs
	$(COMPOSE) logs -f db pgadmin

.PHONY: psql
psql: ## Open psql in the db container (DB_USER=imdbowner to write)
	$(COMPOSE) exec db psql -U $(DB_USER) -d imdbdb

## --- Data pipeline ---------------------------------------------------------

.PHONY: refresh
refresh: download-fresh load ## Download fresh IMDB files, then parse and load them

.PHONY: load
load: parse ## Parse (if needed) and load the existing downloads, swapping them in
	$(COMPOSE) up -d --wait db
	$(PIPELINE) loader

.PHONY: download
download: ## Download any IMDB files that are missing
	$(PIPELINE) downloader

.PHONY: download-fresh
download-fresh: ## Re-download all IMDB files (old files are kept until each new one completes)
	$(PIPELINE) downloader --force

.PHONY: parse
parse: ## Parse downloads that are newer than their parsed output
	$(PIPELINE) parser

.PHONY: check-enums
check-enums: ## Check the downloaded title.basics for unknown title types/genres
	$(PIPELINE) parser --check-enums

## --- Development -----------------------------------------------------------

.PHONY: test
test: ## Run the Python unit tests
	docker build -q -f python.Dockerfile --target test -t $(TEST_IMAGE) . >/dev/null
	docker run --rm -v "$(CURDIR):/work:ro" $(TEST_IMAGE) python -m pytest

.PHONY: lint
lint: ## Run shellcheck on the shell scripts
	docker run --rm -v "$(CURDIR):/mnt:ro" -w /mnt $(SHELLCHECK_IMAGE) $(SHELL_SCRIPTS)

## --- Danger ----------------------------------------------------------------

# Volumes `destroy` removes. pgadmin-data is deliberately not listed, so saved queries survive.
DATA_VOLUMES := postgres-data sources-data

.PHONY: destroy
destroy: ## Remove containers, the database and downloads (keeps pgAdmin queries and settings)
	@printf "This deletes the database and all downloads (pgAdmin settings are kept). Type 'yes' to continue: "; \
	read ans; [ "$$ans" = "yes" ] || { echo "Aborted."; exit 1; }
	$(COMPOSE) --profile pipeline down --remove-orphans
	@project=$$($(COMPOSE) config --format json | grep -m1 '"name"' | cut -d'"' -f4); \
	for vol in $(DATA_VOLUMES); do \
		ids=$$(docker volume ls -q --filter label=com.docker.compose.project=$$project --filter label=com.docker.compose.volume=$$vol); \
		if [ -n "$$ids" ]; then docker volume rm $$ids; else echo "$$vol: no volume, skipping"; fi; \
	done

.PHONY: destroy-all
destroy-all: ## Remove all containers AND volumes, including pgAdmin queries and settings
	@printf "This deletes the database, all downloads AND pgAdmin saved queries/settings. Type 'yes' to continue: "; \
	read ans; [ "$$ans" = "yes" ] || { echo "Aborted."; exit 1; }
	$(COMPOSE) --profile pipeline down -v --remove-orphans
