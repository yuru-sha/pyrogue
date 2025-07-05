"""
ゲーム用ログ設定モジュール。

このモジュールは、PyRogueゲームの包括的なログシステムを提供します。
JSON形式のログ、ファイルローテーション、カスタムログレベル、
NumPyオブジェクトのシリアル化などの機能を提供します。

Example:
    >>> from pyrogue.utils import game_logger
    >>> game_logger.info("Game started", {"player": "test"})
    >>> game_logger.error("Critical error", {"error_code": 500})

"""

from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


class JsonFormatter(logging.Formatter):
    """
    ログメッセージ用JSONフォーマッター。

    ログメッセージを構造化されたJSON形式に変換し、
    タイムスタンプ、ログレベル、メッセージ、追加情報、例外情報を
    適切に可読性の高い形式で出力します。
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        ログレコードをJSON形式にフォーマット。

        Args:
            record: フォーマットするログレコード

        Returns:
            JSON形式のログ文字列

        """
        # Basic log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add extra fields if they exist
        if hasattr(record, "extra"):
            log_data["extra"] = self._convert_numpy(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)

    def _convert_numpy(self, obj: Any) -> Any:
        """
        NumPy型をPythonネイティブ型に変換。

        JSONシリアル化のため、NumPyの数値型や配列を
        標準のPython型に再帰的に変換します。

        Args:
            obj: 変換するオブジェクト

        Returns:
            変換されたオブジェクト

        """
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, dict):
            return {key: self._convert_numpy(value) for key, value in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._convert_numpy(item) for item in obj]
        return obj


class GameLogger:
    """
    ゲームロガークラス。

    ゲーム全体のログ管理を担当し、カスタムログレベル、
    ファイルローテーション、JSONフォーマットをサポートします。
    ゲームログとエラーログを別々に管理し、デバッグと分析を容易にします。

    Attributes:
        TRACE: 詳細なトレーシング用ログレベル (5)
        FATAL: 重大なエラー用ログレベル (60)
        logger: ログインスタンス
        log_dir: ログファイルの保存先ディレクトリ

    """

    # Custom log levels
    TRACE = 5
    FATAL = 60

    def __init__(self) -> None:
        """
        ロガーを初期化。

        カスタムログレベルの登録、ファイルハンドラーの設定、
        ログディレクトリの作成、ローテーションの初期化を行います。
        """
        # Register custom log levels
        logging.addLevelName(self.TRACE, "TRACE")
        logging.addLevelName(self.FATAL, "FATAL")

        # Create logger
        self.logger = logging.getLogger("pyrogue")
        self.logger.setLevel(logging.DEBUG)

        # Create logs directory
        self.log_dir = Path("data/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Configure game.log handler (DEBUG, INFO, WARN, TRACE)
        game_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "game.log",
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5,  # Keep 5 backup files
            encoding="utf-8",
        )
        game_handler.setFormatter(JsonFormatter())
        game_handler.setLevel(logging.DEBUG)

        # Configure error.log handler (ERROR, FATAL)
        error_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "error.log",
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5,  # Keep 5 backup files
            encoding="utf-8",
        )
        error_handler.setFormatter(JsonFormatter())
        error_handler.setLevel(logging.ERROR)

        # Add handlers to logger
        self.logger.addHandler(game_handler)
        self.logger.addHandler(error_handler)

        # Force initial rotation if files exist
        if (self.log_dir / "game.log").exists():
            game_handler.doRollover()
        if (self.log_dir / "error.log").exists():
            error_handler.doRollover()

        # Test log rotation
        self.info("Logger initialized", {"test": "rotation"})

    def _log(
        self, level: int, message: str, extra: dict[str, Any] | None = None
    ) -> None:
        """
        指定されたレベルでメッセージをログ出力。

        Args:
            level: ログレベル
            message: ログメッセージ
            extra: 追加情報の辞書

        """
        self.logger.log(level, message, extra={"extra": extra} if extra else None)

    def trace(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """
        TRACEレベルのメッセージをログ出力。

        Args:
            message: ログメッセージ
            extra: 追加情報の辞書

        """
        self._log(self.TRACE, message, extra)

    def debug(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """
        DEBUGレベルのメッセージをログ出力。

        Args:
            message: ログメッセージ
            extra: 追加情報の辞書

        """
        self._log(logging.DEBUG, message, extra)

    def info(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """
        INFOレベルのメッセージをログ出力。

        Args:
            message: ログメッセージ
            extra: 追加情報の辞書

        """
        self._log(logging.INFO, message, extra)

    def warning(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """
        WARNINGレベルのメッセージをログ出力。

        Args:
            message: ログメッセージ
            extra: 追加情報の辞書

        """
        self._log(logging.WARNING, message, extra)

    def error(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """
        ERRORレベルのメッセージをログ出力。

        Args:
            message: ログメッセージ
            extra: 追加情報の辞書

        """
        self._log(logging.ERROR, message, extra)

    def fatal(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """
        FATALレベルのメッセージをログ出力。

        Args:
            message: ログメッセージ
            extra: 追加情報の辞書

        """
        self._log(self.FATAL, message, extra)


# Create a singleton instance
game_logger = GameLogger()
