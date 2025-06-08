"""Game states module."""
from enum import Enum, auto


class GameStates(Enum):
    """ゲームの状態を表すEnum"""

    MENU = auto()
    PLAYERS_TURN = auto()
    ENEMY_TURN = auto()
    PLAYER_DEAD = auto()
    SHOW_INVENTORY = auto()
    DROP_INVENTORY = auto()
    TARGETING = auto()
    LEVEL_UP = auto()
    CHARACTER_SCREEN = auto()
    EXIT = auto()
