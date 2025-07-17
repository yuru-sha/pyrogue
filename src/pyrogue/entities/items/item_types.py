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


# Weapon definitions - 階層に応じた段階的出現（強化版）
WEAPONS = [
    WeaponType(101, ")", "Dagger", 1, 8, 120, 5, 3, (-1, 4)),  # 序盤専用・初期装備（強化）
    WeaponType(102, ")", "Mace", 1, 10, 100, 8, 4, (-1, 4)),  # 序盤メイン武器（強化）
    WeaponType(103, ")", "Long Sword", 5, 20, 80, 15, 6, (-1, 5)),  # 中盤メイン武器（強化）
    WeaponType(104, ")", "Short Bow", 8, 22, 70, 15, 5, (0, 4)),  # 中盤～終盤（バランス調整）
    WeaponType(105, ")", "Battle Axe", 12, 26, 60, 25, 9, (-2, 6)),  # 終盤武器（大幅強化）
    WeaponType(106, ")", "Two-Handed Sword", 18, 26, 40, 40, 12, (-3, 8)),  # 最終武器（大幅強化）
]

# Armor definitions - 階層に応じた段階的出現（強化版）
ARMORS = [
    ArmorType(201, "[", "Leather Armor", 1, 8, 100, 20, 3, (0, 3)),  # 序盤専用・初期装備（強化）
    ArmorType(202, "[", "Studded Leather", 3, 12, 90, 25, 4, (0, 4)),  # 序盤～中盤移行（強化）
    ArmorType(203, "[", "Ring Mail", 5, 15, 80, 30, 6, (-1, 4)),  # 中盤序盤（強化）
    ArmorType(204, "[", "Scale Mail", 8, 18, 70, 40, 8, (-2, 5)),  # 中盤メイン（強化）
    ArmorType(205, "[", "Chain Mail", 10, 22, 60, 50, 10, (-2, 6)),  # 中盤～終盤（強化）
    ArmorType(206, "[", "Splint Mail", 15, 26, 50, 60, 12, (-3, 7)),  # 終盤防具（強化）
    ArmorType(207, "[", "Banded Mail", 18, 26, 40, 70, 14, (-3, 8)),  # 高級防具（強化）
    ArmorType(208, "[", "Plate Mail", 20, 26, 30, 80, 16, (-4, 10)),  # 最高級防具（大幅強化）
]

# Ring definitions（効果強化版）
RINGS = [
    RingType(501, "=", "Ring of Protection", 3, 26, 50, 200, "protection", (-1, 5)),  # 負の効果軽減、正の効果強化
    RingType(502, "=", "Ring of Add Strength", 3, 26, 50, 200, "strength", (0, 4)),  # 負の効果除去、効果向上
    RingType(503, "=", "Ring of Sustain Strength", 3, 26, 40, 180, "sustain", (0, 1)),  # 微小な追加効果
    RingType(504, "=", "Ring of Searching", 3, 26, 40, 150, "search", (1, 4)),  # 効果向上
    RingType(505, "=", "Ring of See Invisible", 3, 26, 40, 150, "see_invisible", (0, 1)),  # 微小な追加効果
    RingType(506, "=", "Ring of Regeneration", 5, 26, 30, 250, "regeneration", (0, 2)),  # レア指輪に効果追加
]

# Scroll definitions
SCROLLS = [
    ScrollType(401, "?", "Scroll of Identify", 1, 26, 100, 50, "identify"),
    ScrollType(402, "?", "Scroll of Light", 1, 26, 90, 50, "light"),
    ScrollType(403, "?", "Scroll of Remove Curse", 1, 26, 80, 60, "remove_curse"),
    ScrollType(404, "?", "Scroll of Enchant Weapon", 2, 26, 70, 80, "enchant_weapon"),
    ScrollType(405, "?", "Scroll of Enchant Armor", 2, 26, 70, 80, "enchant_armor"),
    ScrollType(406, "?", "Scroll of Teleport", 3, 26, 60, 100, "teleport"),
    ScrollType(407, "?", "Scroll of Magic Mapping", 4, 26, 50, 120, "magic_mapping"),
]

# Potion definitions
POTIONS = [
    PotionType(301, "!", "Potion of Healing", 1, 26, 120, 50, "healing", (15, 25)),  # 回復量と生成重み増加
    PotionType(302, "!", "Potion of Extra Healing", 2, 26, 100, 100, "extra_healing", (30, 45)),  # 回復量と生成重み増加
    PotionType(303, "!", "Potion of Strength", 2, 26, 70, 80, "strength", (1, 2)),
    PotionType(304, "!", "Potion of Restore Strength", 2, 26, 70, 80, "restore_strength", (0, 0)),
    PotionType(305, "!", "Potion of Haste Self", 3, 26, 60, 100, "haste_self", (5, 10)),
    PotionType(306, "!", "Potion of See Invisible", 3, 26, 50, 100, "see_invisible", (0, 0)),
    PotionType(307, "!", "Potion of Poison", 1, 26, 60, 30, "poison", (5, 10)),
    PotionType(308, "!", "Potion of Paralysis", 2, 26, 40, 40, "paralysis", (3, 5)),
    PotionType(309, "!", "Potion of Confusion", 1, 26, 50, 35, "confusion", (4, 6)),
]

# Food definitions
FOODS = [
    FoodType(701, "%", "Food Ration", 1, 26, 100, 30, 900),
    FoodType(702, "%", "Slime Mold", 1, 26, 80, 20, 600),
]

# Wand definitions - オリジナルRogue準拠
WANDS = [
    WandType(601, "/", "Wand of Magic Missiles", 2, 26, 80, 150, "magic_missile", (3, 8), (3, 8)),
    WandType(602, "/", "Wand of Light", 1, 26, 90, 100, "light", (10, 20), (0, 0)),
    WandType(603, "/", "Wand of Lightning", 4, 26, 70, 200, "lightning", (5, 12), (6, 15)),
    WandType(604, "/", "Wand of Fire", 3, 26, 75, 180, "fire", (4, 10), (4, 12)),
    WandType(605, "/", "Wand of Cold", 3, 26, 75, 180, "cold", (4, 10), (4, 12)),
    WandType(606, "/", "Wand of Polymorph", 5, 26, 60, 220, "polymorph", (5, 15), (0, 0)),
    WandType(607, "/", "Wand of Teleport Monster", 4, 26, 65, 200, "teleport_monster", (5, 12), (0, 0)),
    WandType(608, "/", "Wand of Slow Monster", 3, 26, 70, 160, "slow_monster", (4, 10), (0, 0)),
    WandType(609, "/", "Wand of Haste Monster", 3, 26, 50, 140, "haste_monster", (4, 10), (0, 0)),
    WandType(610, "/", "Wand of Sleep", 2, 26, 75, 120, "sleep", (6, 15), (0, 0)),
    WandType(611, "/", "Wand of Drain Life", 8, 26, 40, 300, "drain_life", (3, 8), (8, 20)),
    WandType(612, "/", "Wand of Nothing", 1, 26, 30, 50, "nothing", (5, 15), (0, 0)),
]


# Gold generation by floor
def get_gold_amount(floor: int) -> int:
    """Calculate gold amount for the given floor."""
    base = 2 + floor * 2  # Base amount increases with floor
    variance = floor * 3  # Variance increases with floor
    return base + random.randint(0, variance)


# Item spawn rules
def get_item_spawn_count(floor: int) -> int:
    """Get number of items to spawn on the given floor."""
    base_count = 2
    additional = min((floor - 1) // 3, 4)  # Increases every 3 floors, max +4
    return base_count + additional


def get_available_items(floor: int, item_list: list[ItemType]) -> list[ItemType]:
    """Get list of items that can appear on the given floor."""
    return [i for i in item_list if i.min_floor <= floor <= i.max_floor]


# Special room item generation
def get_treasure_room_items(floor: int) -> list[ItemType]:
    """Get items to spawn in a treasure room."""
    items = []
    # Gold (2-3 piles)
    gold_count = random.randint(2, 3)
    for _ in range(gold_count):
        gold_amount = get_gold_amount(floor) * 2  # Double gold in treasure rooms
        items.append(("$", gold_amount))

    # Valuable items (3-5 items)
    item_count = random.randint(3, 5)
    valuable_items = (
        get_available_items(floor, WEAPONS) + get_available_items(floor, ARMORS) + get_available_items(floor, RINGS)
    )
    items.extend(random.choices(valuable_items, k=item_count))

    return items
