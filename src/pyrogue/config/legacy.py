"""
PyRogueゲームの設定定数。

このモジュールは後方互換性のため保持されています。
新しいコードでは pyrogue.constants を使用してください。
"""

from dataclasses import dataclass, field

# 新しい定数モジュールから値をインポート
from pyrogue.constants import (
    CombatConstants,
    GameConstants,
    HungerConstants,
    ItemConstants,
    ProbabilityConstants,
)


@dataclass
class DisplayConfig:
    """表示およびレンダリングの設定。"""

    SCREEN_WIDTH: int = GameConstants.DUNGEON_WIDTH
    SCREEN_HEIGHT: int = GameConstants.DUNGEON_HEIGHT + GameConstants.STATUS_PANEL_HEIGHT
    MAP_WIDTH: int = GameConstants.DUNGEON_WIDTH
    MAP_HEIGHT: int = GameConstants.MAP_DISPLAY_HEIGHT
    FONT_WIDTH: int = 10
    FONT_HEIGHT: int = 10
    MIN_SCREEN_WIDTH: int = GameConstants.DUNGEON_WIDTH
    MIN_SCREEN_HEIGHT: int = GameConstants.DUNGEON_HEIGHT + GameConstants.STATUS_PANEL_HEIGHT


@dataclass
class PlayerConfig:
    """プレイヤーキャラクターの設定。"""

    INITIAL_HP: int = GameConstants.PLAYER_INITIAL_HP
    INITIAL_ATTACK: int = 5
    INITIAL_DEFENSE: int = 3
    EXPERIENCE_MULTIPLIER: int = CombatConstants.EXP_PER_LEVEL_BASE
    MAX_HUNGER: int = HungerConstants.MAX_HUNGER
    LEVEL_UP_HP_BONUS: int = CombatConstants.HP_GAIN_PER_LEVEL
    LEVEL_UP_ATTACK_BONUS: int = 2
    LEVEL_UP_DEFENSE_BONUS: int = 1


@dataclass
class MonsterConfig:
    """モンスターの設定。"""

    SPAWN_CHANCE: float = 0.8
    MAX_MONSTERS_PER_ROOM: int = 3
    MOVE_CHANCE: float = ProbabilityConstants.MONSTER_MOVE_CHANCE


@dataclass
class ItemConfig:
    """アイテムの設定。"""

    SPAWN_CHANCE: float = 0.7
    MAX_ITEMS_PER_ROOM: int = 2
    MAX_INVENTORY_SIZE: int = ItemConstants.MAX_INVENTORY_SIZE


@dataclass
class GameConfig:
    """メインゲーム設定。"""

    display: DisplayConfig = field(default_factory=DisplayConfig)
    player: PlayerConfig = field(default_factory=PlayerConfig)
    monster: MonsterConfig = field(default_factory=MonsterConfig)
    item: ItemConfig = field(default_factory=ItemConfig)


# グローバル設定インスタンス
CONFIG = GameConfig()
