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
MONSTER_STATS: dict[
    str, tuple[str, str, int, int, int, int, int, int, tuple[int, int, int], str]
] = {
    # A-Z順でオリジナルRogueに忠実に実装（AIパターン付き）
    "AQUATOR": ("A", "Aquator", 4, 15, 9, 3, 8, 6, (0, 150, 255), "basic"),  # 水棲モンスター
    "BAT": ("B", "Bat", 1, 4, 5, 1, 2, 8, (150, 150, 150), "flee"),  # 視界は広いが弱い、逃走型
    "CENTAUR": ("C", "Centaur", 6, 18, 12, 4, 12, 7, (160, 82, 45), "ranged"),  # 弓攻撃
    "DRAGON": ("D", "Dragon", 13, 40, 20, 8, 25, 10, (255, 0, 0), "ranged"),  # ブレス攻撃
    "EMU": ("E", "Emu", 2, 8, 7, 2, 5, 5, (139, 69, 19), "flee"),  # 鳥類、逃走型
    "VENUS_FLYTRAP": ("F", "Venus Flytrap", 5, 20, 8, 6, 10, 2, (0, 255, 0), "basic"),  # 植物
    "GRIFFIN": ("G", "Griffin", 8, 25, 14, 5, 15, 8, (255, 215, 0), "ranged"),  # 飛行攻撃
    "HOBGOBLIN": ("H", "Hobgoblin", 7, 15, 11, 5, 10, 6, (200, 100, 0), "basic"),  # バランス型
    "ICE_MONSTER": ("I", "Ice Monster", 3, 12, 8, 3, 6, 5, (173, 216, 230), "split"),  # 分裂型
    "JABBERWOCK": ("J", "Jabberwock", 15, 45, 22, 10, 30, 9, (138, 43, 226), "basic"),  # 最強級
    "KESTREL": ("K", "Kestrel", 2, 6, 6, 1, 4, 9, (139, 69, 19), "ranged"),  # 鳥類、遠距離攻撃
    "LEPRECHAUN": ("L", "Leprechaun", 4, 10, 6, 2, 7, 6, (0, 255, 0), "item_thief"),  # アイテム盗取
    "MEDUSA": ("M", "Medusa", 10, 22, 15, 6, 18, 7, (128, 0, 128), "basic"),  # 石化攻撃
    "NYMPH": ("N", "Nymph", 9, 14, 12, 4, 14, 6, (255, 192, 203), "gold_thief"),  # ゴールド盗取
    "ORC": ("O", "Orc", 5, 12, 10, 3, 8, 5, (0, 200, 0), "basic"),  # 攻撃力と防御力が高め
    "PHANTOM": ("P", "Phantom", 12, 28, 15, 9, 21, 9, (128, 128, 255), "basic"),  # 高防御
    "QUAGGA": ("Q", "Quagga", 3, 10, 7, 2, 5, 6, (139, 69, 19), "flee"),  # シマウマ系、逃走型
    "RATTLESNAKE": ("R", "Rattlesnake", 1, 5, 6, 1, 3, 6, (139, 69, 19), "basic"),  # 毒蛇
    "SNAKE": ("S", "Snake", 2, 6, 7, 1, 4, 5, (0, 255, 0), "basic"),  # 攻撃力が高め
    "TROLL": ("T", "Troll", 11, 30, 16, 6, 18, 4, (200, 200, 0), "basic"),  # 高HP、高攻撃
    "UR_VILE": ("U", "Ur-Vile", 14, 35, 19, 8, 24, 8, (75, 0, 130), "ranged"),  # 魔法使い
    "VAMPIRE": ("V", "Vampire", 11, 30, 16, 6, 20, 8, (200, 0, 0), "level_drain"),  # レベル下げ
    "WRAITH": ("W", "Wraith", 12, 25, 18, 5, 22, 7, (128, 128, 128), "level_drain"),  # レベル下げ
    "XEROC": ("X", "Xeroc", 9, 18, 13, 4, 16, 7, (255, 255, 255), "split"),  # 分裂型
    "YETI": ("Y", "Yeti", 8, 22, 12, 5, 14, 5, (255, 255, 255), "basic"),  # 冷気攻撃
    "ZOMBIE": ("Z", "Zombie", 6, 16, 10, 4, 11, 3, (128, 128, 128), "basic"),  # アンデッド

    # 幻覚系モンスター（オリジナル拡張）
    "DREAM_EATER": ("@", "Dream Eater", 7, 15, 9, 3, 12, 6, (255, 20, 147), "psychic"),  # 精神攻撃
    "PHANTOM_FUNGUS": ("f", "Phantom Fungus", 5, 10, 6, 2, 8, 4, (138, 43, 226), "hallucinogenic"),  # 胞子攻撃
}

# 階層ごとの出現モンスター定義
# キー: 階層、値: (モンスター名, 出現確率%)のリスト
FLOOR_MONSTERS: dict[int, list[tuple[str, int]]] = {
    1: [("BAT", 50), ("RATTLESNAKE", 50)],
    2: [("BAT", 30), ("RATTLESNAKE", 35), ("KESTREL", 35)],
    3: [("KESTREL", 30), ("SNAKE", 35), ("EMU", 35)],
    4: [("SNAKE", 25), ("EMU", 30), ("QUAGGA", 25), ("AQUATOR", 20)],
    5: [("QUAGGA", 25), ("AQUATOR", 25), ("ICE_MONSTER", 20), ("LEPRECHAUN", 20), ("PHANTOM_FUNGUS", 10)],
    6: [("LEPRECHAUN", 20), ("ORC", 30), ("VENUS_FLYTRAP", 25), ("ZOMBIE", 15), ("PHANTOM_FUNGUS", 10)],
    7: [("ORC", 25), ("ZOMBIE", 25), ("CENTAUR", 25), ("HOBGOBLIN", 15), ("DREAM_EATER", 10)],
    8: [("CENTAUR", 20), ("HOBGOBLIN", 25), ("GRIFFIN", 25), ("YETI", 20), ("DREAM_EATER", 10)],
    9: [("GRIFFIN", 25), ("YETI", 25), ("XEROC", 25), ("NYMPH", 25)],
    10: [("XEROC", 20), ("NYMPH", 30), ("MEDUSA", 30), ("TROLL", 20)],
    11: [("MEDUSA", 25), ("TROLL", 30), ("VAMPIRE", 30), ("WRAITH", 15)],
    12: [("VAMPIRE", 30), ("WRAITH", 35), ("PHANTOM", 25), ("UR_VILE", 10)],
    13: [("WRAITH", 25), ("PHANTOM", 30), ("UR_VILE", 25), ("DRAGON", 20)],
    14: [("UR_VILE", 30), ("DRAGON", 35), ("JABBERWOCK", 35)],
    15: [("DRAGON", 40), ("JABBERWOCK", 60)],
    # 16階以降は15階と同じ設定を使用
}
