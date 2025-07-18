"""Item types and spawn rules module."""

import random
from dataclasses import dataclass


@dataclass
class ItemType:
    """Item type class."""

    item_id: int  # Unique item identifier
    char: str  # Character representation
    name: str  # Item name
    min_floor: int  # Minimum floor level where this item appears
    max_floor: int  # Maximum floor level where this item appears
    spawn_weight: int  # Relative spawn weight (higher = more common)
    value: int  # Gold value


@dataclass
class WeaponType(ItemType):
    """Weapon type class."""

    base_damage: int  # Base damage
    bonus_range: tuple[int, int]  # Range of possible bonuses (min, max)


@dataclass
class ArmorType(ItemType):
    """Armor type class."""

    base_defense: int  # Base defense
    bonus_range: tuple[int, int]  # Range of possible bonuses (min, max)


@dataclass
class RingType(ItemType):
    """Ring type class."""

    effect: str  # Ring effect type
    power_range: tuple[int, int]  # Range of effect power (min, max)


@dataclass
class ScrollType(ItemType):
    """Scroll type class."""

    effect: str  # Scroll effect type


@dataclass
class PotionType(ItemType):
    """Potion type class."""

    effect: str  # Potion effect type
    power_range: tuple[int, int]  # Range of effect power (min, max)


@dataclass
class FoodType(ItemType):
    """Food type class."""

    nutrition: int  # Nutrition value


@dataclass
class WandType(ItemType):
    """Wand type class."""

    effect: str  # Wand effect type
    charges_range: tuple[int, int]  # Range of charges (min, max)
    damage_range: tuple[int, int]  # Range of damage/effect power (min, max)


# Weapon definitions - オリジナルRogue準拠のバランス調整版
WEAPONS = [
    WeaponType(101, ")", "Dagger", 1, 10, 120, 8, 3, (-1, 4)),  # 序盤武器: 基本ダメージ適正化
    WeaponType(102, ")", "Mace", 1, 12, 100, 15, 5, (-1, 4)),  # 序盤主力武器
    WeaponType(103, ")", "Long Sword", 3, 20, 80, 25, 7, (-1, 5)),  # 中盤主力武器
    WeaponType(104, ")", "Short Bow", 5, 22, 70, 20, 6, (0, 4)),  # 中盤遠距離武器
    WeaponType(105, ")", "Battle Axe", 8, 24, 60, 40, 10, (-2, 6)),  # 終盤武器
    WeaponType(106, ")", "Two-Handed Sword", 12, 26, 40, 60, 14, (-3, 8)),  # 最終武器
]

# Armor definitions - オリジナルRogue準拠の防御力バランス版
ARMORS = [
    ArmorType(201, "[", "Leather Armor", 1, 10, 100, 25, 2, (0, 3)),  # 序盤防具: 基本防御力適正化
    ArmorType(202, "[", "Studded Leather", 2, 12, 90, 30, 4, (0, 4)),  # 序盤～中盤防具
    ArmorType(203, "[", "Ring Mail", 3, 15, 80, 35, 6, (-1, 4)),  # 中盤序盤防具
    ArmorType(204, "[", "Scale Mail", 5, 18, 70, 45, 8, (-1, 5)),  # 中盤主力防具
    ArmorType(205, "[", "Chain Mail", 7, 22, 60, 55, 10, (-2, 6)),  # 中盤～終盤防具
    ArmorType(206, "[", "Splint Mail", 10, 24, 50, 70, 12, (-2, 7)),  # 終盤防具
    ArmorType(207, "[", "Banded Mail", 13, 26, 40, 85, 15, (-3, 8)),  # 高級防具
    ArmorType(208, "[", "Plate Mail", 16, 26, 30, 100, 18, (-4, 10)),  # 最高級防具
]

# Ring definitions - オリジナルRogue準拠の効果バランス版
RINGS = [
    RingType(501, "=", "Ring of Protection", 3, 26, 50, 200, "protection", (-2, 4)),  # オリジナルRogue準拠の効果範囲
    RingType(502, "=", "Ring of Add Strength", 3, 26, 50, 200, "strength", (-1, 3)),  # 負の効果も含む（呪われた指輪）
    RingType(503, "=", "Ring of Sustain Strength", 3, 26, 40, 180, "sustain", (0, 0)),  # 純粋な状態保持効果
    RingType(504, "=", "Ring of Searching", 3, 26, 40, 150, "search", (1, 3)),  # 適正な探索効果
    RingType(505, "=", "Ring of See Invisible", 3, 26, 40, 150, "see_invisible", (0, 0)),  # 純粋な視認効果
    RingType(506, "=", "Ring of Regeneration", 5, 26, 30, 250, "regeneration", (0, 1)),  # レア指輪の適正効果
]

# Scroll definitions - オリジナルRogue準拠の出現頻度バランス版
SCROLLS = [
    ScrollType(401, "?", "Scroll of Identify", 1, 26, 80, 50, "identify"),  # やや希少化
    ScrollType(402, "?", "Scroll of Light", 1, 26, 100, 50, "light"),  # 基本巻物は高頻度
    ScrollType(403, "?", "Scroll of Remove Curse", 1, 26, 70, 60, "remove_curse"),  # やや希少化
    ScrollType(404, "?", "Scroll of Enchant Weapon", 2, 26, 50, 80, "enchant_weapon"),  # 希少化
    ScrollType(405, "?", "Scroll of Enchant Armor", 2, 26, 50, 80, "enchant_armor"),  # 希少化
    ScrollType(406, "?", "Scroll of Teleport", 3, 26, 70, 100, "teleport"),  # 中盤以降で使いやすく
    ScrollType(407, "?", "Scroll of Magic Mapping", 4, 26, 40, 120, "magic_mapping"),  # レア巻物化
]

# Potion definitions - オリジナルRogue準拠の効果バランス版
POTIONS = [
    PotionType(301, "!", "Potion of Healing", 1, 26, 100, 50, "healing", (10, 20)),  # 基本回復量適正化
    PotionType(302, "!", "Potion of Extra Healing", 2, 26, 80, 100, "extra_healing", (20, 35)),  # 回復量適正化
    PotionType(303, "!", "Potion of Strength", 2, 26, 60, 80, "strength", (1, 2)),  # オリジナル準拠
    PotionType(304, "!", "Potion of Restore Strength", 2, 26, 60, 80, "restore_strength", (0, 0)),  # 状態回復
    PotionType(305, "!", "Potion of Haste Self", 3, 26, 50, 100, "haste_self", (5, 10)),  # レアポーション化
    PotionType(306, "!", "Potion of See Invisible", 3, 26, 40, 100, "see_invisible", (0, 0)),  # レアポーション化
    PotionType(307, "!", "Potion of Poison", 1, 26, 70, 30, "poison", (3, 8)),  # 毒効果適正化
    PotionType(308, "!", "Potion of Paralysis", 2, 26, 50, 40, "paralysis", (2, 4)),  # 麻痺効果適正化
    PotionType(309, "!", "Potion of Confusion", 1, 26, 60, 35, "confusion", (3, 6)),  # 混乱効果適正化
]

# Food definitions
FOODS = [
    FoodType(701, "%", "Food Ration", 1, 26, 100, 30, 900),
    FoodType(702, "%", "Slime Mold", 1, 26, 80, 20, 600),
]

# Wand definitions - オリジナルRogue準拠のバランス版
WANDS = [
    WandType(601, "/", "Wand of Magic Missiles", 2, 26, 70, 150, "magic_missile", (3, 8), (3, 8)),  # 基本攻撃ワンド
    WandType(602, "/", "Wand of Light", 1, 26, 80, 100, "light", (10, 20), (0, 0)),  # 基本ユーティリティ
    WandType(603, "/", "Wand of Lightning", 4, 26, 60, 200, "lightning", (4, 10), (6, 15)),  # 高威力ワンド
    WandType(604, "/", "Wand of Fire", 3, 26, 65, 180, "fire", (4, 10), (4, 12)),  # 中威力ワンド
    WandType(605, "/", "Wand of Cold", 3, 26, 65, 180, "cold", (4, 10), (4, 12)),  # 中威力ワンド
    WandType(606, "/", "Wand of Polymorph", 5, 26, 50, 220, "polymorph", (5, 15), (0, 0)),  # レアユーティリティ
    WandType(607, "/", "Wand of Teleport Monster", 4, 26, 55, 200, "teleport_monster", (5, 12), (0, 0)),  # 戦術ワンド
    WandType(608, "/", "Wand of Slow Monster", 3, 26, 60, 160, "slow_monster", (4, 10), (0, 0)),  # 戦術ワンド
    WandType(609, "/", "Wand of Haste Monster", 3, 26, 35, 140, "haste_monster", (4, 10), (0, 0)),  # 危険ワンド、希少化
    WandType(610, "/", "Wand of Sleep", 2, 26, 70, 120, "sleep", (6, 15), (0, 0)),  # 基本戦術ワンド
    WandType(611, "/", "Wand of Drain Life", 8, 26, 30, 300, "drain_life", (3, 8), (8, 20)),  # 最レアワンド
    WandType(612, "/", "Wand of Nothing", 1, 26, 40, 50, "nothing", (5, 15), (0, 0)),  # ダミーワンド
]


# Gold generation by floor - オリジナルRogue準拠の金貨系統
def get_gold_amount(floor: int) -> int:
    """Calculate gold amount for the given floor."""
    # オリジナルRogue準拠: 金貨量を適正化
    base = 5 + floor * 3  # 基本金貨量を増加
    variance = floor * 4  # バランスを増加
    return base + random.randint(0, variance)


# Item spawn rules - オリジナルRogue準拠のアイテム出現頻度
def get_item_spawn_count(floor: int) -> int:
    """Get number of items to spawn on the given floor."""
    # オリジナルRogue準拠: 基本アイテム数を適正化
    base_count = 3  # 基本アイテム数を増加
    additional = min((floor - 1) // 4, 3)  # 4階毎に増加、最大+3
    return base_count + additional


def get_available_items(floor: int, item_list: list[ItemType]) -> list[ItemType]:
    """Get list of items that can appear on the given floor."""
    return [i for i in item_list if i.min_floor <= floor <= i.max_floor]


# Special room item generation - オリジナルRogue準拠の宝物部屋
def get_treasure_room_items(floor: int) -> list[ItemType]:
    """Get items to spawn in a treasure room."""
    items = []
    # Gold (3-5 piles) - 宝物部屋は金貨が豊富
    gold_count = random.randint(3, 5)
    for _ in range(gold_count):
        gold_amount = get_gold_amount(floor) * 3  # 3倍の金貨量
        items.append(("$", gold_amount))

    # Valuable items (4-6 items) - 豪華なアイテム構成
    item_count = random.randint(4, 6)
    valuable_items = (
        get_available_items(floor, WEAPONS) + get_available_items(floor, ARMORS) + get_available_items(floor, RINGS)
    )
    items.extend(random.choices(valuable_items, k=item_count))

    return items
