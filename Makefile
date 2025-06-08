.PHONY: all install run clean clean-pyc clean-build format lint test help dev debug release venv

# デフォルトのPythonインタプリタ
PYTHON_INTERPRETER ?= python3.12
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
UV_INTERPRETER ?= uv

# ソースコードのディレクトリ
SRC_DIR = src/pyrogue
TEST_DIR = tests
DATA_DIR = data
LOGS_DIR = $(DATA_DIR)/logs

# 環境変数
export PYTHONPATH = $(SRC_DIR)

help:  ## このヘルプメッセージを表示
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

all: install format lint test  ## 全てのタスクを実行

# Environment and Dependency Management
setup: $(VENV_DIR)/.setup-check ## Create virtual environment and install base dependencies by creating a marker file

$(VENV_DIR)/.setup-check:
	@echo "Cleaning up existing virtual environment in $(VENV_DIR)..."
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


run: ## ゲームを実行（リリースモード）
	$(VENV_PYTHON) -m pyrogue.main

dev: ## 開発モードでゲームを実行（デバッグログ有効）
	DEBUG=1 $(VENV_PYTHON) -m pyrogue.main

debug: dev ## devのエイリアス

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
	@rm -rf .mypy_cache

clean-logs: ## ログファイルを削除
	rm -f $(LOGS_DIR)/*.log*

format: ## コードをフォーマット
	$(UV_INTERPRETER) run black $(SRC_DIR) $(TEST_DIR)
	$(UV_INTERPRETER) run isort $(SRC_DIR) $(TEST_DIR)

lint: ## リンターとタイプチェックを実行
	$(UV_INTERPRETER) run black --check $(SRC_DIR) $(TEST_DIR)
	$(UV_INTERPRETER) run isort --check-only $(SRC_DIR) $(TEST_DIR)
	$(UV_INTERPRETER) run pylint $(SRC_DIR)
	$(UV_INTERPRETER) run mypy $(SRC_DIR)

test: ## テストを実行
	$(UV_INTERPRETER) run pytest $(TEST_DIR) -v

release: clean format lint test ## リリースビルドを作成（全てのチェックを実行）
	$(VENV_PYTHON) -m build