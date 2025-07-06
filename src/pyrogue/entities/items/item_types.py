"""Item types and spawn rules module."""

import random
from dataclasses import dataclass


@dataclass
class ItemType:
    """Item type class."""

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


# Weapon definitions
WEAPONS = [
    WeaponType(")", "Mace", 1, 26, 100, 8, 2, (-1, 3)),
    WeaponType(")", "Long Sword", 2, 26, 80, 15, 4, (-1, 4)),
    WeaponType(")", "Short Bow", 3, 26, 70, 15, 3, (0, 3)),
    WeaponType(")", "Battle Axe", 4, 26, 60, 25, 6, (-2, 5)),
    WeaponType(")", "Two-Handed Sword", 6, 26, 40, 40, 8, (-3, 6)),
]

# Armor definitions
ARMORS = [
    ArmorType("[", "Leather Armor", 1, 26, 100, 20, 2, (0, 2)),
    ArmorType("[", "Studded Leather", 2, 26, 90, 25, 3, (0, 3)),
    ArmorType("[", "Ring Mail", 3, 26, 80, 30, 4, (-1, 3)),
    ArmorType("[", "Scale Mail", 4, 26, 70, 40, 5, (-2, 4)),
    ArmorType("[", "Chain Mail", 5, 26, 60, 50, 6, (-2, 4)),
    ArmorType("[", "Splint Mail", 6, 26, 50, 60, 7, (-3, 5)),
    ArmorType("[", "Banded Mail", 7, 26, 40, 70, 8, (-3, 5)),
    ArmorType("[", "Plate Mail", 8, 26, 30, 80, 9, (-4, 6)),
]

# Ring definitions
RINGS = [
    RingType("=", "Ring of Protection", 3, 26, 50, 200, "protection", (-2, 3)),
    RingType("=", "Ring of Add Strength", 3, 26, 50, 200, "strength", (-1, 3)),
    RingType("=", "Ring of Sustain Strength", 3, 26, 40, 180, "sustain", (0, 0)),
    RingType("=", "Ring of Searching", 3, 26, 40, 150, "search", (1, 3)),
    RingType("=", "Ring of See Invisible", 3, 26, 40, 150, "see_invisible", (0, 0)),
    RingType("=", "Ring of Regeneration", 5, 26, 30, 250, "regeneration", (0, 0)),
]

# Scroll definitions
SCROLLS = [
    ScrollType("?", "Scroll of Identify", 1, 26, 100, 50, "identify"),
    ScrollType("?", "Scroll of Light", 1, 26, 90, 50, "light"),
    ScrollType("?", "Scroll of Remove Curse", 1, 26, 80, 60, "remove_curse"),
    ScrollType("?", "Scroll of Enchant Weapon", 2, 26, 70, 80, "enchant_weapon"),
    ScrollType("?", "Scroll of Enchant Armor", 2, 26, 70, 80, "enchant_armor"),
    ScrollType("?", "Scroll of Teleport", 3, 26, 60, 100, "teleport"),
    ScrollType("?", "Scroll of Magic Mapping", 4, 26, 50, 120, "magic_mapping"),
]

# Potion definitions
POTIONS = [
    PotionType("!", "Potion of Healing", 1, 26, 100, 50, "healing", (10, 15)),
    PotionType(
        "!", "Potion of Extra Healing", 2, 26, 80, 100, "extra_healing", (20, 30)
    ),
    PotionType("!", "Potion of Strength", 2, 26, 70, 80, "strength", (1, 2)),
    PotionType(
        "!", "Potion of Restore Strength", 2, 26, 70, 80, "restore_strength", (0, 0)
    ),
    PotionType("!", "Potion of Haste Self", 3, 26, 60, 100, "haste_self", (5, 10)),
    PotionType("!", "Potion of See Invisible", 3, 26, 50, 100, "see_invisible", (0, 0)),
    PotionType("!", "Potion of Poison", 1, 26, 60, 30, "poison", (5, 10)),
    PotionType("!", "Potion of Paralysis", 2, 26, 40, 40, "paralysis", (3, 5)),
    PotionType("!", "Potion of Confusion", 1, 26, 50, 35, "confusion", (4, 6)),
]

# Food definitions
FOODS = [
    FoodType("%", "Food Ration", 1, 26, 100, 30, 900),
    FoodType("%", "Slime Mold", 1, 26, 80, 20, 600),
]

# Special item: Amulet of Yendor
AMULET = ItemType("&", "The Amulet of Yendor", 26, 26, 100, 1000)


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
        get_available_items(floor, WEAPONS)
        + get_available_items(floor, ARMORS)
        + get_available_items(floor, RINGS)
    )
    items.extend(random.choices(valuable_items, k=item_count))

    return items
