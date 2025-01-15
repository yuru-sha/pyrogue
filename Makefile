.PHONY: all install run clean format lint test help dev debug release

# デフォルトのPythonインタプリタ
PYTHON = python3.12

# Poetry関連のコマンド
POETRY = poetry
POETRY_RUN = $(POETRY) run

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

setup: ## プロジェクトの初期セットアップを実行
	mkdir -p $(DATA_DIR)/fonts $(LOGS_DIR)
	$(POETRY) install

install: ## 依存関係をインストール
	$(POETRY) install

run: ## ゲームを実行（リリースモード）
	$(POETRY_RUN) python -m pyrogue.main

dev: ## 開発モードでゲームを実行（デバッグログ有効）
	DEBUG=1 $(POETRY_RUN) python -m pyrogue.main

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
	$(POETRY_RUN) black $(SRC_DIR) $(TEST_DIR)
	$(POETRY_RUN) isort $(SRC_DIR) $(TEST_DIR)

lint: ## リンターとタイプチェックを実行
	$(POETRY_RUN) black --check $(SRC_DIR) $(TEST_DIR)
	$(POETRY_RUN) isort --check-only $(SRC_DIR) $(TEST_DIR)
	$(POETRY_RUN) pylint $(SRC_DIR)
	$(POETRY_RUN) mypy $(SRC_DIR)

test: ## テストを実行
	$(POETRY_RUN) pytest $(TEST_DIR) -v

watch-format: ## ファイル変更を監視してフォーマットを実行
	find $(SRC_DIR) $(TEST_DIR) -name "*.py" | entr make format

watch-test: ## ファイル変更を監視してテストを実行
	find $(SRC_DIR) $(TEST_DIR) -name "*.py" | entr make test

watch-run: ## ファイル変更を監視してゲームを再起動
	find $(SRC_DIR) -name "*.py" | entr -r make dev

release: clean format lint test ## リリースビルドを作成（全てのチェックを実行）
	$(POETRY) build 