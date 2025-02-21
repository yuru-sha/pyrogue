.PHONY: all install run clean format lint test help dev debug release venv

# デフォルトのPythonインタプリタ
PYTHON = python3.12
VENV = .venv
VENV_BIN = $(VENV)/bin

# パッケージマネージャー
UV = uv

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

venv: ## 仮想環境を作成
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/$(PYTHON) -m pip install uv

setup: venv ## プロジェクトの初期セットアップを実行
	mkdir -p $(DATA_DIR)/fonts $(LOGS_DIR)
	$(VENV_BIN)/$(UV) pip install -r requirements-dev.txt

install: ## 依存関係をインストール
	$(VENV_BIN)/$(UV) pip install -r requirements-dev.txt

run: ## ゲームを実行（リリースモード）
	$(VENV_BIN)/$(PYTHON) -m pyrogue.main

dev: ## 開発モードでゲームを実行（デバッグログ有効）
	DEBUG=1 $(VENV_BIN)/$(PYTHON) -m pyrogue.main

debug: dev ## devのエイリアス

clean: ## 一時ファイルとキャッシュを削除
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".tox" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +

clean-logs: ## ログファイルを削除
	rm -f $(LOGS_DIR)/*.log*

format: ## コードをフォーマット
	$(VENV_BIN)/black $(SRC_DIR) $(TEST_DIR)
	$(VENV_BIN)/isort $(SRC_DIR) $(TEST_DIR)

lint: ## リンターとタイプチェックを実行
	$(VENV_BIN)/black --check $(SRC_DIR) $(TEST_DIR)
	$(VENV_BIN)/isort --check-only $(SRC_DIR) $(TEST_DIR)
	$(VENV_BIN)/pylint $(SRC_DIR)
	$(VENV_BIN)/mypy $(SRC_DIR)

test: ## テストを実行
	$(VENV_BIN)/pytest $(TEST_DIR) -v

watch-format: ## ファイル変更を監視してフォーマットを実行
	find $(SRC_DIR) $(TEST_DIR) -name "*.py" | entr make format

watch-test: ## ファイル変更を監視してテストを実行
	find $(SRC_DIR) $(TEST_DIR) -name "*.py" | entr make test

watch-run: ## ファイル変更を監視してゲームを再起動
	find $(SRC_DIR) -name "*.py" | entr -r make dev

release: clean format lint test ## リリースビルドを作成（全てのチェックを実行）
	$(VENV_BIN)/$(PYTHON) -m build