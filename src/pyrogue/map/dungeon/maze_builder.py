"""
迷路階層生成システム。

部屋なしの複雑な通路のみで構成される迷路ダンジョンを生成する。
セルラーオートマタとデッドエンド除去を組み合わせて自然な迷路を作成。
"""

from __future__ import annotations

import random

import numpy as np

from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Floor, Wall
from pyrogue.utils import game_logger


class MazeBuilder:
    """
    迷路階層生成ビルダー。

    部屋なしの複雑な通路のみで構成される迷路ダンジョンを生成する。
    セルラーオートマタとデッドエンド除去を組み合わせて自然な迷路を作成。
    """

    def __init__(self, width: int, height: int, complexity: float = 0.75) -> None:
        """
        迷路ビルダーを初期化。

        Args:
        ----
            width: ダンジョンの幅
            height: ダンジョンの高さ
            complexity: 迷路の複雑さ（0.0-1.0）。高いほど入り組んだ迷路になる

        """
        self.width = width
        self.height = height
        self.complexity = complexity
        self.rooms: list[Room] = []  # 迷路には部屋は存在しないが、互換性のため

        game_logger.info(f"MazeBuilder initialized: {width}x{height}, complexity={complexity}")

    def build_dungeon(self, tiles: np.ndarray) -> list[Room]:
        """
        迷路階層を生成。

        Args:
        ----
            tiles: タイル配列

        Returns:
        -------
            空の部屋リスト（迷路には部屋が存在しない）

        """
        # 1. 全体を壁で埋める
        self._fill_with_walls(tiles)

        # 2. 基本的な迷路パターンを生成
        self._generate_base_maze(tiles)

        # 3. セルラーオートマタで迷路を自然化
        self._apply_cellular_automata(tiles)

        # 4. デッドエンドを部分的に除去
        self._remove_dead_ends(tiles)

        # 5. 連結性を保証
        self._ensure_connectivity(tiles)

        # 6. 最終的な清掃
        self._clean_maze(tiles)

        game_logger.info("Maze dungeon built: no rooms, complex corridors only")
        return self.rooms  # 空リスト

    def _fill_with_walls(self, tiles: np.ndarray) -> None:
        """全体を壁で埋める。"""
        for y in range(self.height):
            for x in range(self.width):
                tiles[y, x] = Wall()

    def _generate_base_maze(self, tiles: np.ndarray) -> None:
        """基本的な迷路パターンを生成。"""
        # 格子状のベースパターンを作成
        # 奇数座標に通路を配置（古典的な迷路アルゴリズム）
        for y in range(1, self.height - 1, 2):
            for x in range(1, self.width - 1, 2):
                tiles[y, x] = Floor()

                # ランダムに隣接するセルに通路を延伸
                directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
                random.shuffle(directions)

                # 拡張確率を複雑度に基づいて調整
                extension_probability = self.complexity * 0.25  # 複雑度を25%に抑制

                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if (
                        1 <= nx < self.width - 1
                        and 1 <= ny < self.height - 1
                        and random.random() < extension_probability
                    ):
                        # 通路と中間点を床に
                        tiles[ny, nx] = Floor()
                        tiles[y + dy // 2, x + dx // 2] = Floor()

    def _apply_cellular_automata(self, tiles: np.ndarray) -> None:
        """セルラーオートマタで迷路を自然化。"""
        iterations = 2  # イテレーション数を減らす

        for _ in range(iterations):
            new_tiles = np.copy(tiles)

            for y in range(1, self.height - 1):
                for x in range(1, self.width - 1):
                    # 隣接する8方向の壁の数をカウント
                    wall_count = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            if isinstance(tiles[ny, nx], Wall):
                                wall_count += 1

                    # セルラーオートマタのルール（より保守的に）
                    if isinstance(tiles[y, x], Wall):
                        # 壁の場合：隣接する壁が非常に少なければ通路に
                        if wall_count < 3:
                            new_tiles[y, x] = Floor()
                    else:
                        # 通路の場合：隣接する壁が多ければ壁に
                        if wall_count > 7:
                            new_tiles[y, x] = Wall()

            tiles[:] = new_tiles

    def _remove_dead_ends(self, tiles: np.ndarray) -> None:
        """デッドエンドを部分的に除去。"""
        dead_end_removal_rate = max(0.6, 1.0 - self.complexity)  # 最低60%は除去

        changed = True
        while changed:
            changed = False

            for y in range(1, self.height - 1):
                for x in range(1, self.width - 1):
                    if isinstance(tiles[y, x], Floor):
                        # 隣接する床タイルの数をカウント
                        floor_neighbors = 0
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nx, ny = x + dx, y + dy
                            if isinstance(tiles[ny, nx], Floor):
                                floor_neighbors += 1

                        # デッドエンド（隣接する床が1つだけ）を除去
                        if floor_neighbors == 1 and random.random() < dead_end_removal_rate:
                            tiles[y, x] = Wall()
                            changed = True

    def _ensure_connectivity(self, tiles: np.ndarray) -> None:
        """連結性を保証。"""
        # フラッドフィルで最大の連結成分を見つける
        visited = np.zeros((self.height, self.width), dtype=bool)
        components = []

        for y in range(self.height):
            for x in range(self.width):
                if isinstance(tiles[y, x], Floor) and not visited[y, x]:
                    component = self._flood_fill(tiles, visited, x, y)
                    if component:
                        components.append(component)

        if not components:
            return

        # 最大連結成分を特定
        largest_component = max(components, key=len)

        # 小さな孤立成分を最大成分に接続を試行
        for component in components:
            if component != largest_component and len(component) >= 3:
                self._connect_component_to_largest(tiles, component, largest_component)

        # 接続できなかった小さな成分は壁に変換
        for y in range(self.height):
            for x in range(self.width):
                if isinstance(tiles[y, x], Floor) and (x, y) not in largest_component:
                    # 再度連結性をチェック
                    if not self._is_connected_to_largest(tiles, x, y, largest_component):
                        tiles[y, x] = Wall()

    def _flood_fill(self, tiles: np.ndarray, visited: np.ndarray, start_x: int, start_y: int) -> list[tuple[int, int]]:
        """フラッドフィルで連結成分を取得。"""
        component = []
        stack = [(start_x, start_y)]

        while stack:
            x, y = stack.pop()
            if x < 0 or x >= self.width or y < 0 or y >= self.height or visited[y, x] or isinstance(tiles[y, x], Wall):
                continue

            visited[y, x] = True
            component.append((x, y))

            # 4方向に探索
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                stack.append((x + dx, y + dy))

        return component

    def _clean_maze(self, tiles: np.ndarray) -> None:
        """最終的な清掃処理。"""
        # 境界を確実に壁にする
        for y in range(self.height):
            tiles[y, 0] = Wall()
            tiles[y, self.width - 1] = Wall()

        for x in range(self.width):
            tiles[0, x] = Wall()
            tiles[self.height - 1, x] = Wall()

        # 孤立した床タイルを壁に変換
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if isinstance(tiles[y, x], Floor):
                    # 隣接する床タイルの数をカウント
                    floor_neighbors = 0
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if isinstance(tiles[ny, nx], Floor):
                            floor_neighbors += 1

                    # 完全に孤立した床タイルを壁に変換
                    if floor_neighbors == 0:
                        tiles[y, x] = Wall()

    def _connect_component_to_largest(
        self,
        tiles: np.ndarray,
        component: list[tuple[int, int]],
        largest_component: list[tuple[int, int]],
    ) -> None:
        """小さな成分を最大成分に接続を試行。"""
        import random

        # コンポーネントからランダムに点を選択
        comp_point = random.choice(component)

        # 最大成分の最寄りの点を見つける
        min_distance = float("inf")
        closest_point = None

        for large_point in largest_component:
            distance = abs(comp_point[0] - large_point[0]) + abs(comp_point[1] - large_point[1])
            if distance < min_distance:
                min_distance = distance
                closest_point = large_point

        if closest_point and min_distance <= 4:  # 距離が4以下なら接続を試行
            self._create_simple_path(tiles, comp_point, closest_point)

    def _create_simple_path(self, tiles: np.ndarray, start: tuple[int, int], end: tuple[int, int]) -> None:
        """2点間に簡単なパスを作成。"""
        x1, y1 = start
        x2, y2 = end

        # 水平移動
        if x1 != x2:
            step = 1 if x2 > x1 else -1
            for x in range(x1, x2, step):
                if 1 <= x < self.width - 1 and 1 <= y1 < self.height - 1:
                    tiles[y1, x] = Floor()

        # 垂直移動
        if y1 != y2:
            step = 1 if y2 > y1 else -1
            for y in range(y1, y2, step):
                if 1 <= x2 < self.width - 1 and 1 <= y < self.height - 1:
                    tiles[y, x2] = Floor()

    def _is_connected_to_largest(
        self,
        tiles: np.ndarray,
        x: int,
        y: int,
        largest_component: list[tuple[int, int]],
    ) -> bool:
        """指定位置が最大成分に接続されているかチェック。"""
        # 簡易チェック：隣接する4方向に最大成分の点があるか
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) in largest_component:
                return True
        return False

    def reset(self) -> None:
        """ビルダーの状態をリセット。"""
        self.rooms = []

    def get_statistics(self) -> dict:
        """生成統計を取得。"""
        return {
            "builder_type": "Maze",
            "complexity": self.complexity,
            "room_count": 0,
            "corridor_only": True,
        }
