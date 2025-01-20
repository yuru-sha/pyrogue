"""Monster types and spawn rules module."""
from dataclasses import dataclass
from typing import List, Dict, Tuple

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

# Monster definitions based on original Rogue
MONSTER_TYPES = [
    MonsterType('B', 'Bat', 1, 3, 2, 1, 2, 1, 8, 100),
    MonsterType('R', 'Rat', 1, 3, 2, 1, 2, 1, 8, 100),
    MonsterType('K', 'Kobold', 1, 4, 3, 1, 3, 1, 10, 80),
    MonsterType('S', 'Snake', 2, 5, 3, 2, 4, 2, 12, 70),
    MonsterType('G', 'Goblin', 2, 5, 4, 2, 4, 2, 12, 70),
    MonsterType('H', 'Hobgoblin', 3, 7, 5, 3, 6, 3, 14, 60),
    MonsterType('O', 'Orc', 4, 9, 6, 4, 8, 4, 16, 50),
    MonsterType('Z', 'Zombie', 4, 10, 5, 5, 8, 4, 16, 50),
    MonsterType('T', 'Troll', 6, 15, 8, 6, 15, 6, 20, 40),
    MonsterType('Y', 'Yeti', 7, 18, 10, 7, 20, 7, 22, 35),
    MonsterType('W', 'Wraith', 8, 20, 12, 8, 25, 8, 24, 30),
    MonsterType('D', 'Dragon', 10, 30, 15, 10, 40, 10, 26, 20),
]

# Spawn rules by floor
def get_spawn_count(floor: int) -> int:
    """Get number of monsters to spawn on the given floor."""
    base_count = 3
    additional = min((floor - 1) // 2, 5)  # Increases every 2 floors, max +5
    return base_count + additional

def get_available_monsters(floor: int) -> List[MonsterType]:
    """Get list of monsters that can appear on the given floor."""
    return [m for m in MONSTER_TYPES if m.min_floor <= floor <= m.max_floor]

# Maximum monsters per room (based on floor level)
def get_max_monsters_per_room(floor: int) -> int:
    """Get maximum number of monsters allowed in a single room."""
    return min(2 + floor // 3, 6)  # Starts at 2, increases by 1 every 3 floors, max 6

# モンスターの定義
# (char, name, level, hp, attack, defense, exp_value, view_range, color)
MONSTER_STATS: Dict[str, Tuple[str, str, int, int, int, int, int, int, Tuple[int, int, int]]] = {
    # 弱いモンスター（レベル1-5）
    "BAT": ("B", "Bat", 1, 4, 2, 1, 2, 8, (150, 150, 150)),  # 視界は広いが弱い
    "RAT": ("R", "Rat", 1, 5, 3, 1, 3, 6, (139, 69, 19)),    # 標準的な弱モンスター
    "SNAKE": ("S", "Snake", 2, 6, 4, 1, 4, 5, (0, 255, 0)),  # 攻撃力が高め
    "KOBOLD": ("K", "Kobold", 3, 8, 4, 2, 5, 7, (150, 75, 0)),  # バランス型
    "GOBLIN": ("G", "Goblin", 4, 10, 5, 2, 6, 6, (0, 255, 0)),  # バランス型
    "ORC": ("O", "Orc", 5, 12, 6, 3, 8, 5, (0, 200, 0)),     # 攻撃力と防御力が高め

    # 中級モンスター（レベル6-10）
    "TROLL": ("T", "Troll", 6, 20, 8, 4, 12, 4, (200, 200, 0)),  # 高HP、高攻撃
    "HOBGOBLIN": ("H", "Hobgoblin", 7, 15, 7, 5, 10, 6, (200, 100, 0)),  # バランス型
    "WORM": ("W", "Worm", 8, 25, 6, 6, 11, 3, (255, 150, 150)),  # 高HP、低視界
    "IMP": ("I", "Imp", 9, 12, 9, 3, 13, 7, (255, 0, 0)),    # 高攻撃、低防御
    "NYMPH": ("N", "Nymph", 10, 14, 8, 4, 14, 6, (255, 192, 203)),  # バランス型

    # 強いモンスター（レベル11-15）
    "VAMPIRE": ("V", "Vampire", 11, 30, 12, 6, 20, 8, (200, 0, 0)),  # 全体的に高性能
    "WRAITH": ("W", "Wraith", 12, 25, 14, 5, 22, 7, (128, 128, 128)),  # 高攻撃
    "DRAGON": ("D", "Dragon", 13, 40, 15, 8, 25, 10, (255, 0, 0)),  # 最強クラス
    "ETTIN": ("E", "Ettin", 14, 35, 13, 7, 23, 6, (200, 200, 200)),  # 高HP、高攻撃
    "PHANTOM": ("P", "Phantom", 15, 28, 11, 9, 21, 9, (128, 128, 255))  # 高防御
}

# 階層ごとの出現モンスター定義
# キー: 階層、値: (モンスター名, 出現確率%)のリスト
FLOOR_MONSTERS: Dict[int, List[Tuple[str, int]]] = {
    1: [("BAT", 40), ("RAT", 60)],
    2: [("BAT", 30), ("RAT", 40), ("SNAKE", 30)],
    3: [("RAT", 30), ("SNAKE", 35), ("KOBOLD", 35)],
    4: [("SNAKE", 25), ("KOBOLD", 40), ("GOBLIN", 35)],
    5: [("KOBOLD", 30), ("GOBLIN", 40), ("ORC", 30)],
    6: [("GOBLIN", 30), ("ORC", 40), ("TROLL", 30)],
    7: [("ORC", 25), ("TROLL", 35), ("HOBGOBLIN", 40)],
    8: [("TROLL", 30), ("HOBGOBLIN", 35), ("WORM", 35)],
    9: [("HOBGOBLIN", 25), ("WORM", 35), ("IMP", 40)],
    10: [("WORM", 25), ("IMP", 35), ("NYMPH", 40)],
    11: [("IMP", 20), ("NYMPH", 35), ("VAMPIRE", 45)],
    12: [("NYMPH", 20), ("VAMPIRE", 40), ("WRAITH", 40)],
    13: [("VAMPIRE", 25), ("WRAITH", 35), ("DRAGON", 40)],
    14: [("WRAITH", 30), ("DRAGON", 35), ("ETTIN", 35)],
    15: [("DRAGON", 30), ("ETTIN", 35), ("PHANTOM", 35)],
    # 16階以降は15階と同じ設定を使用
} 