.PHONY: run clean help test random

# Set up environment variables
PYTHON = .venv/bin/python3
PYTHONPATH = PYTHONPATH=./

# Default target
help:
	@echo "Textual Game of Life"
	@echo "===================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Run the application
run: setup ## Run the game with default settings
	$(PYTHONPATH) $(PYTHON) -m src.textual_game_of_life

# Run with random initial state
random: ## Run the game with random initial state
	$(PYTHONPATH) $(PYTHON) -m src.textual_game_of_life --random

create_venv: ## Create a virtual environment
	@if [ ! -d "./.venv" ]; then \
		python -m venv .venv; \
	fi

setup: create_venv ## Create and activate the virtual environment
	@if ! $(PYTHON) -m pip show textual > /dev/null 2>&1; then \
		$(PYTHON) -m pip install --upgrade pip; \
		$(PYTHON) -m pip install .; \
	fi

# Run with custom parameters
run-custom: ## Run with custom parameters (make run-custom W=30 H=30 S=0.3 B=2)
	$(PYTHONPATH) $(PYTHON) -m src.textual_game_of_life \
		$(if $(W),--width=$(W),) \
		$(if $(H),--height=$(H),) \
		$(if $(S),--speed=$(S),) \
		$(if $(B),--brush-size=$(B),) \
		$(if $(L),--load=$(L),)

build: setup ## Build the package (sdist and wheel)
	# Reinstall pip from scratch to avoid compatibility issues with Python 3.13
	rm -rf build dist .egg-info
	curl -sS https://bootstrap.pypa.io/get-pip.py | $(PYTHON)
	$(PYTHON) -m pip install --upgrade build twine setuptools wheel
	$(PYTHON) -m build

tag-version: ## Tag the current branch with the version from pyproject.toml
	@VERSION=$$(grep -m 1 'version = ' pyproject.toml | sed 's/version = //;s/"//g'); \
	echo "Tagging current branch with version v$$VERSION"; \
	git tag -a "v$$VERSION" -m "Version $$VERSION"; \
	git push origin "v$$VERSION"; \
	echo "✓ Tag v$$VERSION created and pushed"

pypi-manual: build tag-version ## Build, Tag and Upload the package to PyPI (requires PyPI token)
	@echo "Uploading to PyPI..."
	$(PYTHON) -m twine upload dist/*
	@echo "Package published to PyPI!"

pypi: tag-version ## Tag and trigger GitHub Actions to publish to PyPI
	@echo "Tagged version pushed. GitHub Actions will publish to PyPI automatically."
	@echo "Check the Actions tab in your repository for progress."
