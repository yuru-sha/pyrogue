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

import logging
import os
from pathlib import Path


def setup_game_logger() -> logging.Logger:
    """
    シンプルなゲームロガーを設定。

    Returns:
        設定されたロガーインスタンス

    """
    logger = logging.getLogger("pyrogue")

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Set debug mode based on environment variable
    debug_mode = os.getenv("DEBUG", "0") == "1"
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Create logs directory
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Simple file handler
    handler = logging.FileHandler(log_dir / "game.log", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Add console handler for debug mode
    if debug_mode:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


class GameLogger:
    """
    簡素化されたゲームロガークラス。

    標準のloggingライブラリをベースにしたシンプルなインターフェースです。
    """

    def __init__(self) -> None:
        self.logger = setup_game_logger()

    def debug(self, message: str, extra: dict | None = None) -> None:
        """DEBUGレベルのメッセージをログ出力。"""
        extra_str = f" - {extra}" if extra else ""
        self.logger.debug(f"{message}{extra_str}")

    def info(self, message: str, extra: dict | None = None) -> None:
        """INFOレベルのメッセージをログ出力。"""
        extra_str = f" - {extra}" if extra else ""
        self.logger.info(f"{message}{extra_str}")

    def warning(self, message: str, extra: dict | None = None) -> None:
        """WARNINGレベルのメッセージをログ出力。"""
        extra_str = f" - {extra}" if extra else ""
        self.logger.warning(f"{message}{extra_str}")

    def error(self, message: str, extra: dict | None = None) -> None:
        """ERRORレベルのメッセージをログ出力。"""
        extra_str = f" - {extra}" if extra else ""
        self.logger.error(f"{message}{extra_str}")


# Create a singleton instance
game_logger = GameLogger()
