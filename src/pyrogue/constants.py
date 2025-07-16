"""
ゲーム定数モジュール。

このモジュールは、PyRogue全体で使用される定数値を集約管理します。
マジックナンバーの削減と設定の一元化を目的としています。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GameConstants:
    """ゲーム全般の定数。"""

    # ダンジョンサイズ
    DUNGEON_WIDTH: int = 80
    DUNGEON_HEIGHT: int = 45
    MAP_DISPLAY_HEIGHT: int = 43  # UI用の余白を考慮

    # 階層関連
    MAX_FLOORS: int = 26  # オリジナルRogueと同じ

    # プレイヤー初期値
    PLAYER_INITIAL_HP: int = 20
    PLAYER_INITIAL_LEVEL: int = 1
    PLAYER_INITIAL_GOLD: int = 0
    PLAYER_INITIAL_HUNGER: int = 100

    # FOV関連
    DEFAULT_FOV_RADIUS: int = 8
    MAX_FOV_RADIUS: int = 20

    # UI関連
    STATUS_PANEL_HEIGHT: int = 7
    MESSAGE_LOG_SIZE: int = 3


@dataclass(frozen=True)
class ProbabilityConstants:
    """確率に関する定数。"""

    # ダンジョン生成確率
    GONE_ROOM_CHANCE: float = 0.25  # "gone room"（通路のみ）の確率
    SECRET_DOOR_CHANCE: float = 0.15  # 隠し扉の確率
    SPECIAL_ROOM_CHANCE: float = 0.33  # 特別な部屋の確率
    DEAD_END_SECRET_DOOR_CHANCE: float = 0.25  # 行き止まりの隠し扉確率

    # モンスター関連
    MONSTER_MOVE_CHANCE: float = 0.7  # モンスターが移動する確率
    MONSTER_SPAWN_BASE_CHANCE: float = 0.1  # 基本スポーン確率

    # AI行動関連
    MONSTER_FLEE_THRESHOLD: float = 0.3  # モンスターが逃走するHP閾値
    MONSTER_SPECIAL_ATTACK_CHANCE: float = 0.3  # 特殊攻撃発動確率
    MONSTER_SPLIT_CHANCE: float = 0.3  # 分裂確率
    MONSTER_RANGED_ATTACK_HIT_RATE: float = 0.8  # 遠距離攻撃命中率

    # アイテム関連
    ITEM_SPAWN_BASE_CHANCE: float = 0.05  # 基本アイテムスポーン確率
    CURSED_ITEM_CHANCE: float = 0.1  # 呪われたアイテムの確率

    # トラップ関連
    TRAP_SPAWN_CHANCE: float = 0.05  # トラップスポーン確率
    TRAP_DETECTION_BASE_CHANCE: float = 0.3  # 基本トラップ発見確率
    TRAP_DISARM_BASE_CHANCE: float = 0.6  # 基本トラップ解除確率

    # ステータス異常関連
    POISON_RECOVERY_CHANCE: float = 0.1  # 毒からの自然回復確率
    PARALYSIS_RECOVERY_CHANCE: float = 0.2  # 麻痺からの自然回復確率
    CONFUSION_RECOVERY_CHANCE: float = 0.15  # 混乱からの自然回復確率


@dataclass(frozen=True)
class CombatConstants:
    """戦闘に関する定数。"""

    # ダメージ計算
    BASE_ATTACK_DAMAGE: int = 1
    CRITICAL_HIT_MULTIPLIER: float = 2.0
    CRITICAL_HIT_CHANCE: float = 0.05

    # 隣接判定
    ADJACENT_DISTANCE_THRESHOLD: float = 1.5  # 隣接とみなす距離の閾値

    # 戦闘効果
    HALLUCINATION_EFFECT_CHANCE: float = 0.3  # 幻覚効果発動確率
    GOLD_DROP_CHANCE: float = 0.3  # 金貨ドロップ確率

    # レベルアップ
    EXP_PER_LEVEL_BASE: int = 100
    EXP_LEVEL_MULTIPLIER: float = 1.5
    HP_GAIN_PER_LEVEL: int = 5

    # 攻撃・防御
    MIN_DAMAGE: int = 1
    DEFENSE_REDUCTION_FACTOR: float = 0.5


@dataclass(frozen=True)
class ItemConstants:
    """アイテムに関する定数。"""

    # インベントリ
    MAX_INVENTORY_SIZE: int = 26  # A-Zのアルファベット数
    STACK_SIZE_LIMIT: int = 99  # スタック可能アイテムの最大数

    # 装備強化
    MAX_ENCHANTMENT_LEVEL: int = 10
    MIN_ENCHANTMENT_LEVEL: int = -5
    ENCHANTMENT_BONUS_MULTIPLIER: int = 1

    # アイテム種別による基本値
    POTION_BASE_VALUE: int = 50
    SCROLL_BASE_VALUE: int = 100
    WEAPON_BASE_VALUE: int = 150
    ARMOR_BASE_VALUE: int = 200
    RING_BASE_VALUE: int = 250


@dataclass(frozen=True)
class HungerConstants:
    """満腹度に関する定数。"""

    # 満腹度レベル
    MAX_HUNGER: int = 100
    FULL_THRESHOLD: int = 80  # 満腹状態（ボーナス効果）
    CONTENT_THRESHOLD: int = 60  # 満足状態（通常）
    HUNGRY_THRESHOLD: int = 30  # 空腹状態（軽微なペナルティ）
    VERY_HUNGRY_THRESHOLD: int = 15  # 非常に空腹（中程度のペナルティ）
    STARVING_THRESHOLD: int = 5  # 飢餓状態（重大なペナルティ）

    # 満腹度減少
    HUNGER_DECREASE_RATE: int = 1  # ターンあたりの減少量
    HUNGER_DECREASE_INTERVAL: int = 8  # 減少間隔（ターン）- より頻繁に

    # 餓死ダメージ
    STARVING_DAMAGE: int = 1
    STARVING_DAMAGE_INTERVAL: int = 3  # ダメージ間隔（ターン）- より頻繁に
    VERY_HUNGRY_DAMAGE_INTERVAL: int = 8  # 非常に空腹時のダメージ間隔

    # 飢餓ペナルティ
    HUNGRY_ATTACK_PENALTY: int = 1  # 空腹時の攻撃力ペナルティ
    VERY_HUNGRY_ATTACK_PENALTY: int = 2  # 非常に空腹時の攻撃力ペナルティ
    STARVING_ATTACK_PENALTY: int = 4  # 飢餓時の攻撃力ペナルティ

    HUNGRY_DEFENSE_PENALTY: int = 1  # 空腹時の防御力ペナルティ
    VERY_HUNGRY_DEFENSE_PENALTY: int = 2  # 非常に空腹時の防御力ペナルティ
    STARVING_DEFENSE_PENALTY: int = 3  # 飢餓時の防御力ペナルティ

    # 飢餓ボーナス
    FULL_HP_REGEN_CHANCE: float = 0.05  # 満腹時のHP自然回復確率



@dataclass(frozen=True)
class DisplayConstants:
    """表示に関する定数。"""

    # 色定義（RGB）
    COLOR_WHITE: tuple[int, int, int] = (255, 255, 255)
    COLOR_BLACK: tuple[int, int, int] = (0, 0, 0)
    COLOR_RED: tuple[int, int, int] = (255, 0, 0)
    COLOR_GREEN: tuple[int, int, int] = (0, 255, 0)
    COLOR_BLUE: tuple[int, int, int] = (0, 0, 255)
    COLOR_YELLOW: tuple[int, int, int] = (255, 255, 0)
    COLOR_CYAN: tuple[int, int, int] = (0, 255, 255)
    COLOR_MAGENTA: tuple[int, int, int] = (255, 0, 255)
    COLOR_GRAY: tuple[int, int, int] = (128, 128, 128)
    COLOR_DARK_GRAY: tuple[int, int, int] = (64, 64, 64)

    # 文字定義
    CHAR_PLAYER: str = "@"
    CHAR_WALL: str = "#"
    CHAR_FLOOR: str = "."
    CHAR_DOOR: str = "+"
    CHAR_STAIRS_UP: str = "<"
    CHAR_STAIRS_DOWN: str = ">"
    CHAR_GOLD: str = "$"
    CHAR_UNKNOWN: str = "?"


@dataclass(frozen=True)
class FileConstants:
    """ファイル・パスに関する定数。"""

    # セーブファイル
    SAVE_FILE_NAME: str = "pyrogue_save.json"
    SAVE_FILE_DIR: str = "saves"

    # フォント
    FONT_FILE: str = "assets/fonts/dejavu10x10_gs_tc.png"

    # ログファイル
    LOG_FILE_DIR: str = "logs"
    LOG_FILE_NAME: str = "pyrogue.log"


# 便利な関数
def get_exp_for_level(level: int) -> int:
    """指定レベルに必要な経験値を計算。"""
    base = CombatConstants.EXP_PER_LEVEL_BASE
    multiplier = CombatConstants.EXP_LEVEL_MULTIPLIER
    return int(base * (multiplier ** (level - 1)))


def get_hunger_status(hunger: int) -> str:
    """満腹度から状態文字列を取得。"""
    if hunger <= HungerConstants.STARVING_THRESHOLD:
        return "Starving"
    if hunger <= HungerConstants.HUNGRY_THRESHOLD:
        return "Hungry"
    return "Fed"


def is_max_floor(floor: int) -> bool:
    """最深階かどうかを判定。"""
    return floor >= GameConstants.MAX_FLOORS
