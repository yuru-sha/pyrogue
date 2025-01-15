"""Game logging system.

This module provides a logging system for the game, handling both game messages
and debug information in JSON format with log rotation.
"""
from __future__ import annotations

import atexit
import glob
import inspect
import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional

# FATALレベルを追加（ERRORより上のレベル）
FATAL = 100
logging.addLevelName(FATAL, "FATAL")

# TRACEレベルを追加（DEBUGより下のレベル）
TRACE = 5
logging.addLevelName(TRACE, "TRACE")

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for log messages."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON formatted log string.
        """
        # Get caller information
        frame = inspect.currentframe()
        caller = None
        try:
            while frame:
                if frame.f_code.co_filename not in (__file__, logging.__file__):
                    caller = frame
                    break
                frame = frame.f_back
        finally:
            del frame

        # Build the log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": os.path.basename(record.pathname),
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if available
        if hasattr(record, "extra"):
            log_entry["extra"] = record.extra

        return json.dumps(log_entry, ensure_ascii=False)

class GameLogger:
    """Game logger that handles both game messages and debug information."""

    def __init__(
        self,
        max_messages: int = 100,
        debug: bool = False,
    ) -> None:
        """Initialize the logger.

        Args:
            max_messages: Maximum number of messages to keep in memory.
            debug: Whether to enable debug logging.
        """
        self.messages: List[str] = []
        self.max_messages = max_messages
        self.debug_mode = debug

        # Create logs directory
        self.log_dir = Path("data/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = logging.getLogger("pyrogue")
        self.logger.setLevel(TRACE if debug else logging.INFO)

        # Create formatters
        json_formatter = JSONFormatter()

        # Setup game log handler (10MB, 5 backups)
        game_log_path = self.log_dir / "game.log"
        self.game_handler = RotatingFileHandler(
            game_log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        self.game_handler.setFormatter(json_formatter)
        self.game_handler.setLevel(TRACE)  # TRACE, DEBUG, INFO, WARNを記録
        self.logger.addHandler(self.game_handler)

        # Setup error log handler (10MB, 5 backups)
        error_log_path = self.log_dir / "error.log"
        self.error_handler = RotatingFileHandler(
            error_log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        self.error_handler.setFormatter(json_formatter)
        self.error_handler.setLevel(logging.ERROR)  # ERROR, FATALを記録
        self.logger.addHandler(self.error_handler)

        # Setup debug handler (if debug mode is enabled)
        if debug:
            debug_handler = logging.StreamHandler(sys.stdout)
            debug_handler.setFormatter(json_formatter)
            debug_handler.setLevel(TRACE)
            self.logger.addHandler(debug_handler)

    def trace(self, text: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a trace message.

        Args:
            text: The trace message.
            extra: Additional fields to include in the log.
        """
        if extra:
            self.logger.log(TRACE, text, extra={"extra": extra})
        else:
            self.logger.log(TRACE, text)

    def debug(self, text: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a debug message.

        Args:
            text: The debug message.
            extra: Additional fields to include in the log.
        """
        if self.debug_mode:
            if extra:
                self.logger.debug(text, extra={"extra": extra})
            else:
                self.logger.debug(text)

    def message(self, text: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Add a game message (INFO level).

        Args:
            text: The message text.
            extra: Additional fields to include in the log.
        """
        self.messages.append(text)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
        
        if extra:
            self.logger.info(text, extra={"extra": extra})
        else:
            self.logger.info(text)

    def warning(self, text: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a warning message.

        Args:
            text: The warning message.
            extra: Additional fields to include in the log.
        """
        if extra:
            self.logger.warning(text, extra={"extra": extra})
        else:
            self.logger.warning(text)

    def error(self, text: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log an error message.

        Args:
            text: The error message.
            extra: Additional fields to include in the log.
        """
        if extra:
            self.logger.error(text, extra={"extra": extra})
        else:
            self.logger.error(text)

    def fatal(self, text: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a fatal error message.

        Args:
            text: The fatal error message.
            extra: Additional fields to include in the log.
        """
        if extra:
            self.logger.log(FATAL, text, extra={"extra": extra})
        else:
            self.logger.log(FATAL, text)

    def get_messages(self, last_n: Optional[int] = None) -> List[str]:
        """Get the last N messages.

        Args:
            last_n: Number of messages to return. If None, returns all messages.

        Returns:
            List of messages.
        """
        if last_n is None:
            return self.messages.copy()
        return self.messages[-last_n:]

    def clear_messages(self) -> None:
        """Clear all messages from memory."""
        self.messages.clear()

# Global logger instance
game_logger = GameLogger(
    max_messages=100,
    debug=True,
)
