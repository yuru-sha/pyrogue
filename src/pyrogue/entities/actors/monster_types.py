"""Monster types and spawn rules module."""

from dataclasses import dataclass


@dataclass
class MonsterType:
    """Monster type class."""

    char: str  # Character representation (A-Z)
    name: str  # Monster name
    level: int  # Monster level
    hp: int  # Hit points
    attack: int  # Attack power
    defense: int  # Defense power
    exp: int  # Experience points
    min_floor: int  # Minimum floor level where this monster appears
    max_floor: int  # Maximum floor level where this monster appears
    spawn_weight: int  # Relative spawn weight (higher = more common)


# Spawn rules by floor
def get_spawn_count(floor: int) -> int:
    """Get number of monsters to spawn on the given floor."""
    base_count = 3
    additional = min((floor - 1) // 2, 5)  # Increases every 2 floors, max +5
    return base_count + additional


# Maximum monsters per room (based on floor level)
def get_max_monsters_per_room(floor: int) -> int:
    """Get maximum number of monsters allowed in a single room."""
    return min(2 + floor // 3, 6)  # Starts at 2, increases by 1 every 3 floors, max 6


# モンスターの定義
# (char, name, level, hp, attack, defense, exp_value, view_range, color, ai_pattern)
# 経験値は「レベル*10 + HP + 攻撃力*2 + 防御力*3」をベースに調整
MONSTER_STATS: dict[str, tuple[str, str, int, int, int, int, int, int, tuple[int, int, int], str]] = {
    # A-Z順でオリジナルRogueに忠実に実装（AIパターン付き）
    "AQUATOR": (
        "A",
        "Aquator",
        5,
        18,
        10,
        4,
        122,  # 5*10 + 18 + 10*2 + 4*3 = 100
        6,
        (0, 150, 255),
        "basic",
    ),  # 水棲モンスター
    "BAT": (
        "B",
        "Bat",
        1,
        5,
        3,
        1,
        24,  # 1*10 + 5 + 3*2 + 1*3 = 24
        8,
        (150, 150, 150),
        "flee",
    ),  # 視界は広いが弱い、逃走型
    "CENTAUR": (
        "C",
        "Centaur",
        4,
        15,
        8,
        3,
        80,  # 4*10 + 15 + 8*2 + 3*3 = 80
        7,
        (160, 82, 45),
        "ranged",
    ),  # 弓攻撃
    "DRAGON": (
        "D",
        "Dragon",
        10,
        45,
        25,
        10,
        225,  # 10*10 + 45 + 25*2 + 10*3 = 225
        10,
        (255, 0, 0),
        "ranged",
    ),  # ブレス攻撃
    "EMU": (
        "E",
        "Emu",
        1,
        6,
        4,
        1,
        27,  # 1*10 + 6 + 4*2 + 1*3 = 27
        5,
        (139, 69, 19),
        "flee",
    ),  # 鳥類、逃走型
    "VENUS_FLYTRAP": (
        "F",
        "Venus Flytrap",
        8,
        25,
        5,
        8,
        139,  # 8*10 + 25 + 5*2 + 8*3 = 139
        2,
        (0, 255, 0),
        "basic",
    ),  # 植物
    "GRIFFIN": (
        "G",
        "Griffin",
        13,
        35,
        20,
        6,
        223,  # 13*10 + 35 + 20*2 + 6*3 = 223
        8,
        (255, 215, 0),
        "ranged",
    ),  # 飛行攻撃
    "HOBGOBLIN": (
        "H",
        "Hobgoblin",
        3,
        10,
        6,
        2,
        58,  # 3*10 + 10 + 6*2 + 2*3 = 58
        6,
        (200, 100, 0),
        "basic",
    ),  # バランス型
    "ICE_MONSTER": (
        "I",
        "Ice Monster",
        2,
        8,
        5,
        2,
        44,  # 2*10 + 8 + 5*2 + 2*3 = 44
        5,
        (173, 216, 230),
        "split",
    ),  # 分裂型
    "JABBERWOCK": (
        "J",
        "Jabberwock",
        15,
        60,
        30,
        12,
        306,  # 15*10 + 60 + 30*2 + 12*3 = 306
        9,
        (138, 43, 226),
        "basic",
    ),  # 最強級
    "KESTREL": (
        "K",
        "Kestrel",
        1,
        5,
        4,
        1,
        26,  # 1*10 + 5 + 4*2 + 1*3 = 26
        9,
        (139, 69, 19),
        "ranged",
    ),  # 鳥類、遠距離攻撃
    "LEPRECHAUN": (
        "L",
        "Leprechaun",
        7,
        12,
        2,
        3,
        95,  # 7*10 + 12 + 2*2 + 3*3 = 95
        6,
        (0, 255, 0),
        "item_thief",
    ),  # アイテム盗取
    "MEDUSA": (
        "M",
        "Medusa",
        8,
        25,
        12,
        5,
        144,  # 8*10 + 25 + 12*2 + 5*3 = 144
        7,
        (128, 0, 128),
        "basic",
    ),  # 石化攻撃
    "NYMPH": (
        "N",
        "Nymph",
        3,
        10,
        2,
        2,
        50,  # 3*10 + 10 + 2*2 + 2*3 = 50
        6,
        (255, 192, 203),
        "gold_thief",
    ),  # ゴールド盗取
    "ORC": (
        "O",
        "Orc",
        5,
        14,
        9,
        3,
        91,  # 5*10 + 14 + 9*2 + 3*3 = 91
        5,
        (0, 200, 0),
        "basic",
    ),  # 攻撃力と防御力が高め
    "PHANTOM": (
        "P",
        "Phantom",
        8,
        28,
        14,
        7,
        157,  # 8*10 + 28 + 14*2 + 7*3 = 157
        9,
        (128, 128, 255),
        "basic",
    ),  # 高防御
    "QUAGGA": (
        "Q",
        "Quagga",
        3,
        12,
        6,
        2,
        60,  # 3*10 + 12 + 6*2 + 2*3 = 60
        6,
        (139, 69, 19),
        "flee",
    ),  # シマウマ系、逃走型
    "RATTLESNAKE": (
        "R",
        "Rattlesnake",
        2,
        7,
        5,
        1,
        40,  # 2*10 + 7 + 5*2 + 1*3 = 40
        6,
        (139, 69, 19),
        "basic",
    ),  # 毒蛇
    "SNAKE": (
        "S",
        "Snake",
        2,
        6,
        6,
        1,
        41,  # 2*10 + 6 + 6*2 + 1*3 = 41
        5,
        (0, 255, 0),
        "basic",
    ),  # 攻撃力が高め
    "TROLL": (
        "T",
        "Troll",
        6,
        22,
        15,
        5,
        127,  # 6*10 + 22 + 15*2 + 5*3 = 127
        4,
        (200, 200, 0),
        "basic",
    ),  # 高HP、高攻撃
    "UR_VILE": (
        "U",
        "Ur-Vile",
        7,
        28,
        18,
        6,
        152,  # 7*10 + 28 + 18*2 + 6*3 = 152
        8,
        (75, 0, 130),
        "ranged",
    ),  # 魔法使い
    "VAMPIRE": (
        "V",
        "Vampire",
        8,
        30,
        16,
        7,
        163,  # 8*10 + 30 + 16*2 + 7*3 = 163
        8,
        (200, 0, 0),
        "level_drain",
    ),  # レベル下げ
    "WRAITH": (
        "W",
        "Wraith",
        5,
        20,
        12,
        4,
        106,  # 5*10 + 20 + 12*2 + 4*3 = 106
        7,
        (128, 128, 128),
        "level_drain",
    ),  # レベル下げ
    "XEROC": (
        "X",
        "Xeroc",
        7,
        25,
        15,
        5,
        140,  # 7*10 + 25 + 15*2 + 5*3 = 140
        7,
        (255, 255, 255),
        "split",
    ),  # 分裂型
    "YETI": (
        "Y",
        "Yeti",
        4,
        18,
        10,
        4,
        90,  # 4*10 + 18 + 10*2 + 4*3 = 90
        5,
        (255, 255, 255),
        "basic",
    ),  # 冷気攻撃
    "ZOMBIE": (
        "Z",
        "Zombie",
        6,
        18,
        9,
        4,
        100,  # 6*10 + 18 + 9*2 + 4*3 = 100
        3,
        (128, 128, 128),
        "basic",
    ),  # アンデッド
    # 幻覚系モンスター（オリジナル拡張）
    "DREAM_EATER": (
        "@",
        "Dream Eater",
        7,
        15,
        9,
        3,
        112,  # 7*10 + 15 + 9*2 + 3*3 = 112
        6,
        (255, 20, 147),
        "psychic",
    ),  # 精神攻撃
    "PHANTOM_FUNGUS": (
        "f",
        "Phantom Fungus",
        5,
        10,
        6,
        2,
        78,  # 5*10 + 10 + 6*2 + 2*3 = 78
        4,
        (138, 43, 226),
        "hallucinogenic",
    ),  # 胞子攻撃
}

# 階層ごとの出現モンスター定義
# キー: 階層、値: (モンスター名, 出現確率%)のリスト
FLOOR_MONSTERS: dict[int, list[tuple[str, int]]] = {
    # 序盤（B1-5F）: 弱いモンスター中心、段階的に難易度上昇
    1: [("BAT", 40), ("EMU", 30), ("KESTREL", 30)],
    2: [("BAT", 30), ("KESTREL", 30), ("SNAKE", 20), ("RATTLESNAKE", 20)],
    3: [("SNAKE", 30), ("RATTLESNAKE", 30), ("HOBGOBLIN", 40)],
    4: [("HOBGOBLIN", 40), ("ICE_MONSTER", 30), ("QUAGGA", 30)],
    5: [("ICE_MONSTER", 25), ("QUAGGA", 25), ("ORC", 30), ("NYMPH", 20)],
    # 中盤（B6-10F）: 中堅モンスター登場
    6: [("ORC", 30), ("CENTAUR", 30), ("YETI", 25), ("NYMPH", 15)],
    7: [("CENTAUR", 25), ("YETI", 25), ("WRAITH", 30), ("PHANTOM_FUNGUS", 20)],
    8: [("WRAITH", 30), ("AQUATOR", 30), ("LEPRECHAUN", 20), ("PHANTOM_FUNGUS", 20)],
    9: [("AQUATOR", 30), ("LEPRECHAUN", 20), ("TROLL", 30), ("ZOMBIE", 20)],
    10: [("TROLL", 30), ("ZOMBIE", 20), ("XEROC", 25), ("DREAM_EATER", 25)],
    # 上位中盤（B11-15F）: 上位モンスター登場
    11: [("XEROC", 30), ("DREAM_EATER", 20), ("MEDUSA", 30), ("UR_VILE", 20)],
    12: [("MEDUSA", 30), ("UR_VILE", 20), ("VENUS_FLYTRAP", 30), ("PHANTOM", 20)],
    13: [("VENUS_FLYTRAP", 25), ("PHANTOM", 25), ("VAMPIRE", 50)],
    14: [("VAMPIRE", 100)],  # Vampire専用階層
    15: [("VAMPIRE", 50), ("GRIFFIN", 50)],
    # 終盤（B16-20F）: 最強クラス段階的登場
    16: [("GRIFFIN", 100)],  # Griffin専用階層
    17: [("GRIFFIN", 50), ("DRAGON", 50)],
    18: [("DRAGON", 100)],  # Dragon専用階層
    19: [("DRAGON", 50), ("JABBERWOCK", 50)],
    20: [("JABBERWOCK", 100)],  # Jabberwock専用階層
    # 最深部（B21-26F）: 最強モンスター混成軍
    21: [("JABBERWOCK", 30), ("DRAGON", 30), ("GRIFFIN", 20), ("VAMPIRE", 20)],
    22: [("JABBERWOCK", 40), ("DRAGON", 40), ("GRIFFIN", 20)],
    23: [("JABBERWOCK", 50), ("DRAGON", 50)],
    24: [("JABBERWOCK", 60), ("DRAGON", 40)],
    25: [("JABBERWOCK", 70), ("DRAGON", 30)],
    26: [("JABBERWOCK", 80), ("DRAGON", 20)],  # 最終階層
}
