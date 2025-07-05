"""
PyRogueゲームの設定定数。
"""

from dataclasses import dataclass, field


@dataclass
class DisplayConfig:
    """表示およびレンダリングの設定。"""
    SCREEN_WIDTH: int = 80
    SCREEN_HEIGHT: int = 50
    MAP_WIDTH: int = 80
    MAP_HEIGHT: int = 43
    FONT_WIDTH: int = 10
    FONT_HEIGHT: int = 10
    MIN_SCREEN_WIDTH: int = 80
    MIN_SCREEN_HEIGHT: int = 50


@dataclass
class PlayerConfig:
    """プレイヤーキャラクターの設定。"""
    INITIAL_HP: int = 20
    INITIAL_ATTACK: int = 5
    INITIAL_DEFENSE: int = 3
    EXPERIENCE_MULTIPLIER: int = 100
    MAX_HUNGER: int = 100
    LEVEL_UP_HP_BONUS: int = 5
    LEVEL_UP_ATTACK_BONUS: int = 2
    LEVEL_UP_DEFENSE_BONUS: int = 1


@dataclass
class MonsterConfig:
    """モンスターの設定。"""
    SPAWN_CHANCE: float = 0.8
    MAX_MONSTERS_PER_ROOM: int = 3


@dataclass
class ItemConfig:
    """アイテムの設定。"""
    SPAWN_CHANCE: float = 0.7
    MAX_ITEMS_PER_ROOM: int = 2


@dataclass
class GameConfig:
    """メインゲーム設定。"""
    display: DisplayConfig = field(default_factory=DisplayConfig)
    player: PlayerConfig = field(default_factory=PlayerConfig)
    monster: MonsterConfig = field(default_factory=MonsterConfig)
    item: ItemConfig = field(default_factory=ItemConfig)


# グローバル設定インスタンス
CONFIG = GameConfig()
