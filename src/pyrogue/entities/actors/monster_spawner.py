"""Monster spawner module."""

from __future__ import annotations

import random

import numpy as np

from pyrogue.map.tile import Door, Floor, SecretDoor

from .monster import Monster
from .monster_types import FLOOR_MONSTERS, MONSTER_STATS


class MonsterSpawner:
    """モンスターの生成と管理を行うクラス"""

    def __init__(self, dungeon_level: int, has_amulet: bool = False):
        self.dungeon_level = dungeon_level
        self.has_amulet = has_amulet  # 復路判定用
        self.monsters: list[Monster] = []
        self.occupied_positions: set[tuple[int, int]] = set()

    def spawn_monsters(self, dungeon_tiles: np.ndarray, rooms: list[any]) -> None:
        """
        モンスターを生成

        Args:
        ----
            dungeon_tiles: ダンジョンのタイル配列
            rooms: 部屋のリスト

        """
        # フロアサイズを基準としたモンスター数の計算
        height, width = dungeon_tiles.shape
        total_floor_tiles = self._count_floor_tiles(dungeon_tiles)

        if self.has_amulet:
            # ★★★ AMULET奪還のための全軍総攻撃 ★★★
            # モンスターたちがアミュレットを取り戻すために総結集！

            if self.dungeon_level <= 5:
                # B1F-B5F: 地上封鎖のための最大密度総攻撃
                density_ratio = 0.45  # フロアの45%を最強クラスで埋める
                monster_count = int(total_floor_tiles * density_ratio)
                monster_count = max(monster_count, 80)  # 最低80体の精鋭

            elif self.dungeon_level <= 10:
                # B6F-B10F: 第二波総攻撃
                density_ratio = 0.40  # フロアの40%を強敵で埋める
                monster_count = int(total_floor_tiles * density_ratio)
                monster_count = max(monster_count, 70)  # 最低70体の強敵

            else:
                # B11F-B15F: 深層追撃部隊
                density_ratio = 0.35  # フロアの35%を混成軍で埋める
                monster_count = int(total_floor_tiles * density_ratio)
                monster_count = max(monster_count, 60)  # 最低60体の混成軍

        else:
            # 通常時: 従来の計算方式
            base_count = random.randint(8, 15)
            level_bonus = min(10, self.dungeon_level // 2)
            monster_count = base_count + level_bonus

        # 迷路階層の場合（部屋がない場合）の対応
        if not rooms:
            self._spawn_monsters_in_maze(dungeon_tiles, monster_count)
            return

        if self.has_amulet:
            # 魔除け所持時: フロア全体にモンスターを敷き詰める
            self._spawn_monsters_everywhere(dungeon_tiles, monster_count)
        else:
            # 通常時: 部屋ベース配置
            for _ in range(monster_count):
                # ランダムな部屋を選択（特別な部屋は除外）
                available_rooms = [room for room in rooms if not room.is_special]
                if not available_rooms:
                    break

                room = random.choice(available_rooms)

                # 部屋の内部の座標から、まだモンスターがいない場所を選択
                available_positions = [
                    (x, y)
                    for x, y in room.inner
                    if isinstance(dungeon_tiles[y, x], Floor) and (x, y) not in self.occupied_positions
                ]

                if not available_positions:
                    continue

                pos = random.choice(available_positions)
                monster = self._create_monster(pos[0], pos[1])
                if monster:
                    self.monsters.append(monster)
                    self.occupied_positions.add(pos)

    def _create_monster(self, x: int, y: int) -> Monster | None:
        """指定された位置にモンスターを生成"""
        # 復路の場合は特別なモンスター出現ルールを適用
        if self.has_amulet:
            monster_table = self._get_return_journey_monsters()
        else:
            # 階層に応じたモンスター出現テーブルを取得
            level = min(self.dungeon_level, 26)  # 26階以降は26階の設定を使用
            monster_table = FLOOR_MONSTERS.get(level, FLOOR_MONSTERS[26])

        # 出現確率に基づいてモンスターを選択
        total = sum(prob for _, prob in monster_table)
        r = random.randint(1, total)
        cumulative = 0

        for monster_id, prob in monster_table:
            cumulative += prob
            if r <= cumulative:
                # モンスターのステータスを取得
                stats = MONSTER_STATS[monster_id]
                return Monster(
                    char=stats[0],
                    x=x,
                    y=y,
                    name=stats[1],
                    level=stats[2],
                    hp=stats[3],
                    max_hp=stats[3],
                    attack=stats[4],
                    defense=stats[5],
                    exp_value=stats[6],
                    view_range=stats[7],
                    color=stats[8],
                    ai_pattern=stats[9],
                )

        return None

    def _get_return_journey_monsters(self) -> list[tuple[str, int]]:
        """
        復路（アミュレット所持時）のモンスター出現テーブルを取得。

        ★★★ AMULET OF YENDOR奪還のための全軍総攻撃 ★★★
        モンスターたちが聖なるアミュレットを取り戻すために全勢力を結集！
        地上に近いほどより強力な最強クラスの軍勢が襲いかかる！

        Returns
        -------
            モンスター出現テーブル [(monster_id, probability), ...]

        """
        # ★ AMULET奪還作戦 ★
        # B1F-B5F: 【第一総攻撃】最強クラスの精鋭部隊による地上封鎖
        # B6F-B10F: 【第二総攻撃】深層精鋭の追撃部隊
        # B11F-B15F: 【深層追撃】全階層からの最強クラス混成軍

        if self.dungeon_level <= 5:
            # B1F-B5F: AMULET奪還のための最強クラスの総攻撃！地上に近いほど最凶
            return [
                ("JABBERWOCK", 60),  # 最強モンスター（大幅増加）
                ("DRAGON", 55),  # ドラゴン（大幅増加）
                ("GRIFFIN", 50),  # グリフィン（上位モンスター）
                ("PHANTOM", 45),  # ファントム（大幅増加）
                ("VAMPIRE", 45),  # ヴァンパイア（大幅増加）
                ("UR_VILE", 40),  # ウル・ヴィル（魔法使い）
                ("MEDUSA", 35),  # メデューサ（石化攻撃）
                ("TROLL", 30),  # トロル（大幅増加）
                ("WRAITH", 25),  # レイス（レベル下げ）
            ]
        if self.dungeon_level <= 10:
            # B6F-B10F: AMULET奪還のための第二波総攻撃！最強クラス中心
            return [
                ("JABBERWOCK", 50),  # 最強モンスター（中心）
                ("DRAGON", 50),  # ドラゴン（最強クラス中心）
                ("GRIFFIN", 45),  # グリフィン（大幅増加）
                ("PHANTOM", 40),  # ファントム（大幅増加）
                ("VAMPIRE", 40),  # ヴァンパイア（大幅増加）
                ("UR_VILE", 35),  # ウル・ヴィル（魔法使い）
                ("MEDUSA", 30),  # メデューサ（大幅増加）
                ("TROLL", 25),  # トロル（大幅増加）
                ("WRAITH", 20),  # レイス（大幅増加）
                ("XEROC", 15),  # ゼロック（分裂型）
            ]
        # B11F-B15F: AMULET奪還のための深層からの追撃！最強クラス混合
        return [
            ("JABBERWOCK", 40),  # 最強モンスター（深層維持）
            ("DRAGON", 35),  # ドラゴン（深層でも最強維持）
            ("GRIFFIN", 35),  # グリフィン（強化）
            ("PHANTOM", 30),  # ファントム（強化）
            ("VAMPIRE", 30),  # ヴァンパイア（強化）
            ("UR_VILE", 25),  # ウル・ヴィル（強化）
            ("MEDUSA", 25),  # メデューサ（強化）
            ("TROLL", 20),  # トロル（強化）
            ("WRAITH", 15),  # レイス（強化）
            ("CENTAUR", 10),  # ケンタウロス（従来の強敵）
        ]

    def _count_floor_tiles(self, dungeon_tiles: np.ndarray) -> int:
        """
        ダンジョン内の床タイル数をカウント。

        Args:
        ----
            dungeon_tiles: ダンジョンのタイル配列

        Returns:
        -------
            int: 床タイルの総数

        """
        floor_count = 0
        height, width = dungeon_tiles.shape

        for y in range(height):
            for x in range(width):
                # Floor, Door, SecretDoorを歩行可能なタイルとしてカウント
                if isinstance(dungeon_tiles[y, x], (Floor, Door, SecretDoor)):
                    floor_count += 1

        return floor_count

    def _spawn_monsters_everywhere(self, dungeon_tiles: np.ndarray, monster_count: int) -> None:
        """
        魔除け所持時: フロア全体の歩行可能エリアにモンスターを大量配置。

        Args:
        ----
            dungeon_tiles: ダンジョンのタイル配列
            monster_count: 配置するモンスター数

        """
        # 全ての歩行可能位置を取得
        walkable_positions = []
        height, width = dungeon_tiles.shape

        for y in range(height):
            for x in range(width):
                if isinstance(dungeon_tiles[y, x], (Floor, Door, SecretDoor)):
                    walkable_positions.append((x, y))

        # 物理的制限: 歩行可能タイルの90%まで
        max_possible = int(len(walkable_positions) * 0.9)
        monster_count = min(monster_count, max_possible)

        # ランダムに配置位置を選択
        random.shuffle(walkable_positions)

        # 大量配置実行
        placed_count = 0
        for pos in walkable_positions:
            if placed_count >= monster_count:
                break

            x, y = pos
            if (x, y) not in self.occupied_positions:
                monster = self._create_monster(x, y)
                if monster:
                    self.monsters.append(monster)
                    self.occupied_positions.add(pos)
                    placed_count += 1

    def _spawn_monsters_in_maze(self, dungeon_tiles: np.ndarray, monster_count: int) -> None:
        """
        迷路階層でモンスターを配置。

        部屋がない迷路階層では、床タイル（通路）にランダムにモンスターを配置します。

        Args:
        ----
            dungeon_tiles: ダンジョンのタイル配列
            monster_count: 配置するモンスター数

        """
        # 迷路の床タイル（通路）を全て取得
        floor_positions = []
        height, width = dungeon_tiles.shape

        for y in range(height):
            for x in range(width):
                if isinstance(dungeon_tiles[y, x], Floor):
                    floor_positions.append((x, y))

        # ★★★ 迷路でのAMULET奪還総攻撃 ★★★
        if self.has_amulet:
            if self.dungeon_level <= 5:
                # B1F-B5F迷路: 地上封鎖の最終防衛線
                monster_count = int(len(floor_positions) * 0.50)  # 50%を最強クラスで
                monster_count = max(monster_count, 120)  # 最低120体の精鋭軍
            elif self.dungeon_level <= 10:
                # B6F-B10F迷路: 第二波迷路総攻撃
                monster_count = int(len(floor_positions) * 0.45)  # 45%を強敵で
                monster_count = max(monster_count, 100)  # 最低100体の強敵軍
            else:
                # B11F-B15F迷路: 深層迷路追撃
                monster_count = int(len(floor_positions) * 0.40)  # 40%を混成軍で
                monster_count = max(monster_count, 80)  # 最低80体の混成軍
        # 通常時の迷路階層調整
        elif len(floor_positions) > monster_count * 3:
            monster_count = int(monster_count * 1.5)  # 1.5倍に増やす

        # 物理的制限: 全床タイルの90%まで（プレイヤーの移動スペース確保）
        max_possible = int(len(floor_positions) * 0.9)
        monster_count = min(monster_count, max_possible)

        # ランダムに配置位置を選択
        random.shuffle(floor_positions)

        # モンスターを配置
        for i in range(min(monster_count, len(floor_positions))):
            x, y = floor_positions[i]

            # 既に占有されていないかチェック
            if (x, y) not in self.occupied_positions:
                monster = self._create_monster(x, y)
                if monster:
                    self.monsters.append(monster)
                    self.occupied_positions.add((x, y))

    def update_monsters(self, player_x: int, player_y: int, dungeon_tiles: np.ndarray, fov_map: any) -> None:
        """
        全モンスターの更新処理

        Args:
        ----
            player_x: プレイヤーのX座標
            player_y: プレイヤーのY座標
            dungeon_tiles: ダンジョンのタイル配列
            fov_map: 視界計算用のマップ

        """
        # 死亡したモンスターを除去
        self.monsters = [m for m in self.monsters if not m.is_dead()]
        self.occupied_positions = {(m.x, m.y) for m in self.monsters}

        for monster in self.monsters:
            if not monster.is_hostile:
                continue

            if monster.can_see_player(player_x, player_y, fov_map):
                # プレイヤーが視界内にいる場合、プレイヤーに向かって移動
                dx, dy = monster.get_move_towards_player(player_x, player_y)
            # プレイヤーが視界内にいない場合、ランダムに移動（20%の確率）
            elif random.random() < 0.2:
                dx, dy = monster.get_random_move()
            else:
                continue

            # 移動先の座標
            new_x = monster.x + dx
            new_y = monster.y + dy

            # 移動先が有効か確認
            if (
                0 <= new_x < dungeon_tiles.shape[1]
                and 0 <= new_y < dungeon_tiles.shape[0]
                and (
                    isinstance(dungeon_tiles[new_y, new_x], Floor)
                    or (
                        isinstance(dungeon_tiles[new_y, new_x], (Door, SecretDoor))
                        and dungeon_tiles[new_y, new_x].door_state == "open"
                    )
                )
                and (new_x, new_y) not in self.occupied_positions
                and (new_x != player_x or new_y != player_y)
            ):
                # 現在位置を解放
                self.occupied_positions.remove((monster.x, monster.y))

                # 移動を実行
                monster.move(dx, dy)

                # 新しい位置を記録
                self.occupied_positions.add((monster.x, monster.y))

    def get_monster_at(self, x: int, y: int) -> Monster | None:
        """指定された位置にいるモンスターを取得"""
        for monster in self.monsters:
            if monster.x == x and monster.y == y:
                return monster
        return None

    def remove_monster(self, monster: Monster) -> None:
        """モンスターをリストから削除"""
        if monster in self.monsters:
            self.monsters.remove(monster)
            # 占有位置からも削除
            pos = (monster.x, monster.y)
            if pos in self.occupied_positions:
                self.occupied_positions.remove(pos)
