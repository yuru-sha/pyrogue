"""Item types module."""
from typing import Dict, List, Tuple

# 武器の定義
# (名前, 攻撃力ボーナス, 出現階層, レア度)
WEAPONS: List[Tuple[str, int, int, int]] = [
    ("Dagger", 2, 1, 100),
    ("Short Sword", 3, 2, 80),
    ("Long Sword", 5, 4, 60),
    ("Great Sword", 7, 6, 40),
    ("Battle Axe", 8, 8, 30),
    ("Katana", 10, 10, 20),
]

# 防具の定義
# (名前, 防御力ボーナス, 出現階層, レア度)
ARMORS: List[Tuple[str, int, int, int]] = [
    ("Leather Armor", 2, 1, 100),
    ("Studded Leather", 3, 2, 80),
    ("Ring Mail", 4, 4, 60),
    ("Chain Mail", 5, 6, 40),
    ("Plate Mail", 7, 8, 30),
    ("Dragon Scale", 10, 10, 20),
]

# 指輪の定義
# (名前, 効果, ボーナス値, 出現階層, レア度)
RINGS: List[Tuple[str, str, int, int, int]] = [
    ("Ring of Protection", "defense", 1, 3, 50),
    ("Ring of Power", "attack", 1, 3, 50),
    ("Ring of Health", "hp", 10, 5, 40),
    ("Ring of Regeneration", "regeneration", 1, 7, 30),
    ("Ring of Accuracy", "accuracy", 2, 9, 20),
]

# 巻物の定義
# (名前, 効果, 出現階層, レア度)
SCROLLS: List[Tuple[str, str, int, int]] = [
    ("Scroll of Identify", "identify", 1, 100),
    ("Scroll of Teleport", "teleport", 2, 80),
    ("Scroll of Remove Curse", "remove_curse", 3, 70),
    ("Scroll of Enchant Weapon", "enchant_weapon", 4, 50),
    ("Scroll of Enchant Armor", "enchant_armor", 4, 50),
    ("Scroll of Magic Mapping", "magic_mapping", 5, 40),
]

# 薬の定義
# (名前, 効果, 効果値, 出現階層, レア度)
POTIONS: List[Tuple[str, str, int, int, int]] = [
    ("Potion of Healing", "heal", 20, 1, 100),
    ("Potion of Extra Healing", "heal", 40, 3, 70),
    ("Potion of Full Healing", "heal", 100, 5, 40),
    ("Potion of Gain Level", "gain_level", 1, 7, 30),
    ("Potion of Gain Strength", "gain_strength", 1, 9, 20),
]

# 食料の定義
# (名前, 満腹度回復量, 出現階層, レア度)
FOODS: List[Tuple[str, int, int, int]] = [
    ("Ration", 50, 1, 100),
    ("Apple", 20, 1, 80),
    ("Meat", 70, 3, 60),
    ("Royal Jelly", 100, 5, 40),
]

# 階層ごとの金貨生成量
# (最小値, 最大値)
GOLD_BY_FLOOR: Dict[int, Tuple[int, int]] = {
    1: (10, 50),
    2: (20, 70),
    3: (30, 90),
    4: (40, 110),
    5: (50, 130),
    6: (60, 150),
    7: (70, 170),
    8: (80, 190),
    9: (90, 210),
    10: (100, 230),
    # 11階以降は10階と同じ
}

# 特別な部屋のアイテム生成ルール
SPECIAL_ROOM_ITEMS = {
    "treasure": {
        "gold": (100, 250),  # 金貨の生成量（最小値、最大値）
        "items": 3,  # 通常アイテムの生成数
    },
    "armory": {
        "weapons": 2,  # 武器の生成数
        "armors": 2,   # 防具の生成数
    },
    "library": {
        "scrolls": 5,  # 巻物の生成数
    },
    "laboratory": {
        "potions": 5,  # 薬の生成数
    },
} 