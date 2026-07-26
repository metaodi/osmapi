.DEFAULT_GOAL := help
.PHONY: build coverage deps format help lint test docs

build:  ## Build the wheel and the source distribution
	rm -rf dist
	uv build

coverage:  ## Run tests with coverage
	uv run coverage erase
	uv run coverage run --include=osmapi/* -m pytest -ra
	uv run coverage report -m

deps:  ## Install dependencies
	uv sync
	uv run pre-commit install

docs:  ## Generate documentation
	uv run pdoc -o docs osmapi

format:  ## Format source code (black codestyle)
	uv run black osmapi examples tests

lint:  ## Linting of source code
	uv run black --check --diff osmapi examples tests
	uv run flake8 --statistics --show-source .
	uv run mypy osmapi

test:  ## Run tests (run in UTF-8 mode in Windows)
	uv run python -Xutf8 -m pytest --cov=osmapi tests/

help: SHELL := /bin/bash
help: ## Show help message
	@IFS=$$'\n' ; \
	help_lines=(`fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##/:/'`); \
	printf "%s\n\n" "Usage: make [task]"; \
	printf "%-20s %s\n" "task" "help" ; \
	printf "%-20s %s\n" "------" "----" ; \
	for help_line in $${help_lines[@]}; do \
		IFS=$$':' ; \
		help_split=($$help_line) ; \
		help_command=`echo $${help_split[0]} | sed -e 's/^ *//' -e 's/ *$$//'` ; \
		help_info=`echo $${help_split[2]} | sed -e 's/^ *//' -e 's/ *$$//'` ; \
		printf '\033[36m'; \
		printf "%-20s %s" $$help_command ; \
		printf '\033[0m'; \
		printf "%s\n" $$help_info; \
	done
