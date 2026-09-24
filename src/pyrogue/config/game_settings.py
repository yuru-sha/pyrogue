"""TCOD display dimensions."""

from dataclasses import dataclass, field


@dataclass
class DisplayConfig:
    """TCOD screen and map dimensions."""

    SCREEN_WIDTH: int = 80
    SCREEN_HEIGHT: int = 52
    MAP_WIDTH: int = 80
    MAP_HEIGHT: int = 45
    FONT_WIDTH: int = 10
    FONT_HEIGHT: int = 10
    MIN_SCREEN_WIDTH: int = 80
    MIN_SCREEN_HEIGHT: int = 52


@dataclass
class GameConfig:
    """Application display settings."""

    display: DisplayConfig = field(default_factory=DisplayConfig)


CONFIG = GameConfig()
