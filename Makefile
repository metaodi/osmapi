.DEFAULT_GOAL := help
.PHONY: coverage deps help lint test docs

coverage:  ## Run tests with coverage
	python -m coverage erase
	python -m coverage run --include=osmapi/* -m pytest -ra
	python -m coverage report -m

deps:  ## Install dependencies
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt
	python -m pip install -r test-requirements.txt

docs:  ## Generate documentation
	python -m pdoc -o docs osmapi

format:  ## Format source code (black codestyle)
	python -m black osmapi

lint:  ## Linting of source code
	python -m black --check osmapi
	python -m flake8 --statistics --show-source .

test:  ## Run tests
	python -m pytest --cov=osmapi tests/

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
