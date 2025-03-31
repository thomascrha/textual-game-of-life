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
	@if [ ! -d ".venv" ]; then \
		$(PYTHON) -m venv .venv; \
	fi

setup: create_venv ## Create and activate the virtual environment
	# check if textual is installed
	if ! $(PYTHON) -m pip show textual > /dev/null 2>&1; then \
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

# Clean up Python cache
clean: ## Remove Python cache files and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".tox" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +

