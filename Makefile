.PHONY: help setup setup-dev test test-cli verify clean clean-pyc clean-build run pre-commit-install pre-commit-run ci-checks qa-all qa-after-refactor qa-after-feature

UV_INTERPRETER ?= uv

# デフォルトターゲット
help:
	@echo "Available targets:"
	@echo "  setup          : Create virtual environment and install dependencies"
	@echo "  setup-dev      : Install development dependencies"
	@echo "  test           : Run pytest tests"
	@echo "  test-cli       : Run CLI mode functional tests"
	@echo "  verify         : Run the complete deterministic verification gate"
	@echo "  pre-commit-install : Install pre-commit hooks"
	@echo "  pre-commit-run     : Run pre-commit on all files"
	@echo "  clean          : Remove python artifacts and build directories"
	@echo "  clean-pyc      : Remove .pyc files"
	@echo "  clean-build    : Remove build artifacts"
	@echo "  run            : Run the CLI application (example: make run ARGS=\"your-command --option\")"
	@echo "  ci-checks        : Run the complete verification gate"
	@echo "  qa-all         : Alias for the complete verification gate"
	@echo "  qa-after-refactor : Run QA checks after refactoring"
	@echo "  qa-after-feature  : Run QA checks after adding new features"

# Environment and Dependency Management
setup: ## Install base dependencies without replacing the existing environment
	@$(UV_INTERPRETER) sync --locked

setup-dev: ## Install development dependencies from the lockfile
	@$(UV_INTERPRETER) sync --locked --extra dev

# テスト
test:
	@echo "Running pytest tests"
	@ENABLE_CREATE_ALL=1 $(UV_INTERPRETER) run --locked --extra dev pytest -q

test-cli:
	@echo "Running CLI mode functional tests"
	@./scripts/cli_test.sh

# クリーンアップ
clean: clean-pyc clean-build
	@echo "Cleaning complete."

clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -rf {} +

clean-build:
	@rm -rf build/
	@rm -rf dist/
	@rm -rf .eggs/
	@rm -f .coverage
	@rm -rf htmlcov/
	@rm -rf .pytest_cache

# アプリケーション実行
run:
	@PYTHONPATH=src $(UV_INTERPRETER) run --locked -m pyrogue.main $(ARGS)

verify:
	@echo "Running secret pattern scan"
	@./scripts/check_secrets.sh
	@echo "Running Ruff checks"
	@$(UV_INTERPRETER) run --locked --extra dev ruff check src tests
	@$(UV_INTERPRETER) run --locked --extra dev ruff format --check src tests
	@echo "Running mypy"
	@$(UV_INTERPRETER) run --locked --extra dev mypy src/pyrogue/core/rogue_game.py src/pyrogue/core/game_state.py
	@echo "Compiling Python sources"
	@$(UV_INTERPRETER) run --locked --extra dev python -m compileall -q src tests
	@$(MAKE) test
	@$(MAKE) test-cli

# CI関連
ci-checks: verify
	@echo "All CI checks completed successfully!"

# pre-commit
pre-commit-install:
	@echo "Installing pre-commit hooks..."
	@$(UV_INTERPRETER) run --locked --extra dev pre-commit install

pre-commit-run:
	@echo "Running pre-commit on all files..."
	@$(UV_INTERPRETER) run --locked --extra dev pre-commit run --all-files

# 品質保証タスク
qa-all:
	@$(MAKE) verify

qa-after-refactor:
	@$(MAKE) verify

qa-after-feature:
	@$(MAKE) verify
