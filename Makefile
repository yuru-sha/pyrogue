.PHONY: help setup setup-dev test test-cli clean clean-pyc clean-build run pre-commit-install pre-commit-run ci-checks qa-all qa-after-refactor qa-after-feature

# デフォルトのPythonインタプリタ
PYTHON_INTERPRETER ?= python3.12
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
UV_INTERPRETER ?= uv

# デフォルトターゲット
help:
	@echo "Available targets:"
	@echo "  setup          : Create virtual environment and install dependencies"
	@echo "  setup-dev      : Install development dependencies"
	@echo "  test           : Run pytest tests"
	@echo "  test-cli       : Run CLI mode functional tests"
	@echo "  pre-commit-install : Install pre-commit hooks"
	@echo "  pre-commit-run     : Run pre-commit on all files"
	@echo "  clean          : Remove python artifacts and build directories"
	@echo "  clean-pyc      : Remove .pyc files"
	@echo "  clean-build    : Remove build artifacts"
	@echo "  run            : Run the CLI application (example: make run ARGS=\"your-command --option\")"
	@echo "  ci-checks        : Run all CI checks locally (pre-commit + test)"
	@echo "  qa-all         : Run comprehensive QA checks (all tests + CLI test)"
	@echo "  qa-after-refactor : Run QA checks after refactoring"
	@echo "  qa-after-feature  : Run QA checks after adding new features"

# Environment and Dependency Management
setup: $(VENV_DIR)/.setup-check ## Create virtual environment and install base dependencies by creating a marker file

$(VENV_DIR)/.setup-check:
	@echo "Cleaning up existing virtual environment in $(VENV_DIR)..."make
	@rm -rf $(VENV_DIR)
	@echo "Creating virtual environment and installing dependencies using uv..."
	@$(UV_INTERPRETER) sync
	@echo "Base setup complete. Marking with .setup-check"
	@touch $(VENV_DIR)/.setup-check

setup-dev: $(VENV_DIR)/.setup-dev-check ## Install development and optional dependencies by creating a marker file

$(VENV_DIR)/.setup-dev-check: $(VENV_DIR)/.setup-check
	@echo "Installing development dependencies..."
	@$(UV_INTERPRETER) sync --extra dev
	@echo "Development setup complete. Marking with .setup-dev-check"
	@touch $(VENV_DIR)/.setup-dev-check

# テスト
test:
	@echo "Running pytest tests"
	@ENABLE_CREATE_ALL=1 $(UV_INTERPRETER) run pytest

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
	@PYTHONPATH=src $(UV_INTERPRETER) run -m pyrogue.main $(ARGS)

# CI関連
ci-checks: test
	@echo "Running all pre-commit hooks..."
	@$(UV_INTERPRETER) run pre-commit run --all-files
	@echo "All CI checks completed successfully!"

# pre-commit
pre-commit-install:
	@echo "Installing pre-commit hooks..."
	@$(UV_INTERPRETER) run pre-commit install

pre-commit-run:
	@echo "Running pre-commit on all files..."
	@$(UV_INTERPRETER) run pre-commit run --all-files

# 品質保証タスク
qa-all:
	@echo "🔍 Running comprehensive QA checks..."
	@echo "📊 Step 1: Unit tests"
	@$(MAKE) test
	@echo "🖥️  Step 2: CLI functional tests"
	@$(MAKE) test-cli
	@echo "✅ Step 3: Code quality checks"
	@$(MAKE) ci-checks
	@echo "🎉 All QA checks completed successfully!"

qa-after-refactor:
	@echo "🔧 Running QA checks after refactoring..."
	@echo "📊 Step 1: Unit tests (checking for regressions)"
	@$(MAKE) test
	@echo "🖥️  Step 2: CLI functional tests (critical for refactoring)"
	@$(MAKE) test-cli
	@echo "✅ Step 3: Code quality checks"
	@$(MAKE) ci-checks
	@echo "🎉 Refactoring QA checks completed! All functionality preserved."

qa-after-feature:
	@echo "🆕 Running QA checks after adding new features..."
	@echo "📊 Step 1: Unit tests (including new feature tests)"
	@$(MAKE) test
	@echo "🖥️  Step 2: CLI functional tests (ensuring integration)"
	@$(MAKE) test-cli
	@echo "✅ Step 3: Code quality checks"
	@$(MAKE) ci-checks
	@echo "🎉 New feature QA checks completed! Ready for production."
