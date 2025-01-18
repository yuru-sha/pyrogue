"""Logging configuration for the game."""
from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


class JsonFormatter(logging.Formatter):
    """JSON format for log messages."""
    def format(self, record: logging.LogRecord) -> str:
        """Format the record as JSON."""
        # Basic log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        
        # Add extra fields if they exist
        if hasattr(record, "extra"):
            log_data["extra"] = self._convert_numpy(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)

    def _convert_numpy(self, obj: Any) -> Any:
        """Convert numpy types to Python native types."""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._convert_numpy(item) for item in obj]
        return obj


class GameLogger:
    """Game logger class."""
    
    # Custom log levels
    TRACE = 5
    FATAL = 60
    
    def __init__(self):
        """Initialize the logger."""
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
            encoding="utf-8"
        )
        game_handler.setFormatter(JsonFormatter())
        game_handler.setLevel(logging.DEBUG)
        
        # Configure error.log handler (ERROR, FATAL)
        error_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "error.log",
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5,  # Keep 5 backup files
            encoding="utf-8"
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
    
    def _log(self, level: int, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log a message with the specified level."""
        self.logger.log(level, message, extra={"extra": extra} if extra else None)
    
    def trace(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log a TRACE level message."""
        self._log(self.TRACE, message, extra)
    
    def debug(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log a DEBUG level message."""
        self._log(logging.DEBUG, message, extra)
    
    def info(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log an INFO level message."""
        self._log(logging.INFO, message, extra)
    
    def warning(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log a WARNING level message."""
        self._log(logging.WARNING, message, extra)
    
    def error(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log an ERROR level message."""
        self._log(logging.ERROR, message, extra)
    
    def fatal(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log a FATAL level message."""
        self._log(self.FATAL, message, extra)


# Create a singleton instance
game_logger = GameLogger()
