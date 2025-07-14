"""Monster spawner module."""

from __future__ import annotations

import random

import numpy as np

from pyrogue.map.tile import Door, Floor, SecretDoor

from .monster import Monster
from .monster_types import FLOOR_MONSTERS, MONSTER_STATS


class MonsterSpawner:
    """モンスターの生成と管理を行うクラス"""

    def __init__(self, dungeon_level: int):
        self.dungeon_level = dungeon_level
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
        # 階層に応じたモンスター数を決定（基本3-6体、階層が上がるごとに若干増加）
        base_count = random.randint(3, 6)
        level_bonus = min(4, self.dungeon_level // 3)  # 最大で4体まで追加
        monster_count = base_count + level_bonus

        # 迷路階層の場合（部屋がない場合）の対応
        if not rooms:
            self._spawn_monsters_in_maze(dungeon_tiles, monster_count)
            return

        # 通常の部屋ベース配置
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
        # 階層に応じたモンスター出現テーブルを取得
        level = min(self.dungeon_level, 15)  # 15階以降は15階の設定を使用
        monster_table = FLOOR_MONSTERS.get(level, FLOOR_MONSTERS[15])

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
        
        # 床タイルが少ない場合は配置数を調整
        if len(floor_positions) < monster_count:
            monster_count = len(floor_positions) // 2  # 密度を考慮
        
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
