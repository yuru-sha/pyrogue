"""
ゲーム用ログ設定モジュール。

このモジュールは、PyRogueゲームの包括的なログシステムを提供します。
JSON形式のログ、ファイルローテーション、カスタムログレベル、
NumPyオブジェクトのシリアル化などの機能を提供します。

Example:
-------
    >>> from pyrogue.utils import game_logger
    >>> game_logger.info("Game started", {"player": "test"})
    >>> game_logger.error("Critical error", {"error_code": 500})

"""

from __future__ import annotations

import logging
from pathlib import Path

from pyrogue.config.env import get_debug_mode, get_log_directory, get_log_level


def setup_game_logger() -> logging.Logger:
    """
    シンプルなゲームロガーを設定。

    Returns
    -------
        設定されたロガーインスタンス

    """
    logger = logging.getLogger("pyrogue")

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Set log level based on environment variable
    debug_mode = get_debug_mode()
    log_level = get_log_level()

    # Map string log level to logging constants
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # Use specified log level or fallback to DEBUG/INFO based on debug mode
    if log_level.upper() in level_mapping:
        logger.setLevel(level_mapping[log_level.upper()])
    else:
        logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Create logs directory from environment variable
    log_dir = Path(get_log_directory())
    log_dir.mkdir(parents=True, exist_ok=True)

    # Simple file handler
    handler = logging.FileHandler(log_dir / "game.log", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
