"""
デッドエンド配置管理システム。

このモジュールは、ダンジョンに戦略的なデッドエンドを配置し、
探索の深度と緊張感を向上させます。
"""

from __future__ import annotations

import random
from typing import Any

from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Wall
from pyrogue.utils import game_logger


class DeadEndManager:
    """
    デッドエンド配置管理クラス。

    戦略的なデッドエンドを配置し、
    ダンジョンの探索性と緊張感を向上させます。
    """

    def __init__(self, width: int, height: int, floor: int = 1) -> None:
        """
        デッドエンド管理を初期化。

        Args:
        ----
            width: ダンジョンの幅
            height: ダンジョンの高さ
            floor: 階層番号（デッドエンドの配置戦略に影響）

        """
        self.width = width
        self.height = height
        self.floor = floor
        self.deadends_created = 0

        # 階層に応じたデッドエンド配置戦略
        self.deadend_strategy = self._determine_deadend_strategy(floor)

        # デッドエンドの配置履歴
        self.deadend_locations: list[tuple[int, int]] = []
        self.deadend_types: list[str] = []

        game_logger.debug(f"DeadEndManager initialized for floor {floor}")

    def place_strategic_deadends(self, rooms: list[Room], tiles: Any, tile_placer: callable) -> list[tuple[int, int]]:
        """
        戦略的なデッドエンドを配置。

        Args:
        ----
            rooms: 部屋のリスト
            tiles: タイル配列
            tile_placer: タイル配置関数

        Returns:
        -------
            配置されたデッドエンドの座標リスト

        """
        all_deadends = []

        # 部屋周辺のデッドエンドを配置
        for room in rooms:
            room_deadends = self._place_room_deadends(room, tiles, tile_placer)
            all_deadends.extend(room_deadends)

        # 孤立したデッドエンドを配置
        isolated_deadends = self._place_isolated_deadends(rooms, tiles, tile_placer)
        all_deadends.extend(isolated_deadends)

        # 特殊なデッドエンドを配置
        special_deadends = self._place_special_deadends(rooms, tiles, tile_placer)
        all_deadends.extend(special_deadends)

        game_logger.info(f"Placed {len(all_deadends)} strategic deadends")
        return all_deadends

    def _determine_deadend_strategy(self, floor: int) -> str:
        """
        階層に応じたデッドエンド配置戦略を決定。

        Args:
        ----
            floor: 階層番号

        Returns:
        -------
            デッドエンド配置戦略名

        """
        if floor <= 5:
            return "minimal"  # 浅い階層：最小限のデッドエンド
        if floor <= 10:
            return "moderate"  # 中間階層：適度なデッドエンド
        if floor <= 15:
            return "complex"  # 深い階層：複雑なデッドエンド
        if floor <= 20:
            return "intricate"  # 深層：入り組んだデッドエンド
        return "labyrinthine"  # 最深部：迷宮のようなデッドエンド

    def _place_room_deadends(self, room: Room, tiles: Any, tile_placer: callable) -> list[tuple[int, int]]:
        """
        部屋周辺にデッドエンドを配置。

        Args:
        ----
            room: 対象の部屋
            tiles: タイル配列
            tile_placer: タイル配置関数

        Returns:
        -------
            配置されたデッドエンドの座標リスト

        """
        deadends = []

        # 部屋の各辺にデッドエンドを配置する可能性をチェック
        potential_locations = self._find_potential_deadend_locations(room, tiles)

        # 戦略に応じて配置数を決定
        max_deadends = self._get_max_deadends_per_room()

        # 最適な位置を選択
        selected_locations = self._select_optimal_deadend_locations(potential_locations, max_deadends)

        # デッドエンドを実際に配置
        for location in selected_locations:
            deadend_type = self._determine_deadend_type(location, room)
            deadend_points = self._create_deadend(location, deadend_type, tiles, tile_placer)
            deadends.extend(deadend_points)

            self.deadend_locations.append(location)
            self.deadend_types.append(deadend_type)
            self.deadends_created += 1

        return deadends

    def _find_potential_deadend_locations(self, room: Room, tiles: list[list[Any]]) -> list[tuple[int, int, str]]:
        """
        部屋周辺のデッドエンド候補位置を検索。

        Args:
        ----
            room: 対象の部屋
            tiles: タイル配列

        Returns:
        -------
            候補位置のリスト（x, y, direction）

        """
        potential_locations = []

        # 各辺をチェック
        directions = [
            ("north", room.x, room.x + room.width, room.y - 1, 0, -1),
            ("south", room.x, room.x + room.width, room.y + room.height, 0, 1),
            ("west", room.y, room.y + room.height, room.x - 1, -1, 0),
            ("east", room.y, room.y + room.height, room.x + room.width, 1, 0),
        ]

        for direction, start, end, fixed_coord, dx, dy in directions:
            for i in range(start, end):
                if direction in ["north", "south"]:
                    x, y = i, fixed_coord
                else:
                    x, y = fixed_coord, i

                # 境界チェック
                if not (0 <= x < self.width and 0 <= y < self.height):
                    continue

                # 現在のタイルが壁で、デッドエンドを配置できるかチェック
                if isinstance(tiles[y][x], Wall) and self._can_place_deadend(x, y, dx, dy, tiles):
                    potential_locations.append((x, y, direction))

        return potential_locations

    def _can_place_deadend(self, x: int, y: int, dx: int, dy: int, tiles: Any) -> bool:
        """
        指定位置にデッドエンドを配置できるかチェック。

        Args:
        ----
            x: X座標
            y: Y座標
            dx: X方向のオフセット
            dy: Y方向のオフセット
            tiles: タイル配列

        Returns:
        -------
            配置可能かどうか

        """
        # デッドエンドの長さ
        deadend_length = random.randint(2, 4)

        # デッドエンドの経路が壁で囲まれているかチェック
        for i in range(1, deadend_length + 1):
            check_x = x + dx * i
            check_y = y + dy * i

            # 境界チェック
            if not (0 <= check_x < self.width and 0 <= check_y < self.height):
                return False

            # 現在のタイルが壁でない場合は配置不可
            if not isinstance(tiles[check_y][check_x], Wall):
                return False

        return True

    def _get_max_deadends_per_room(self) -> int:
        """
        部屋あたりの最大デッドエンド数を取得。

        Returns
        -------
            最大デッドエンド数

        """
        strategy_limits = {
            "minimal": 1,
            "moderate": 2,
            "complex": 3,
            "intricate": 4,
            "labyrinthine": 5,
        }

        return strategy_limits.get(self.deadend_strategy, 2)

    def _select_optimal_deadend_locations(
        self, potential_locations: list[tuple[int, int, str]], max_deadends: int
    ) -> list[tuple[int, int, str]]:
        """
        最適なデッドエンド位置を選択。

        Args:
        ----
            potential_locations: 候補位置のリスト
            max_deadends: 最大デッドエンド数

        Returns:
        -------
            選択された位置のリスト

        """
        if len(potential_locations) <= max_deadends:
            return potential_locations

        # 位置の多様性を考慮して選択
        selected = []
        used_directions = set()

        # 各方向から最低1つずつ選択（可能な場合）
        for direction in ["north", "south", "west", "east"]:
            direction_locations = [loc for loc in potential_locations if loc[2] == direction]
            if direction_locations and len(selected) < max_deadends:
                selected.append(random.choice(direction_locations))
                used_directions.add(direction)

        # 残りの位置をランダムに選択
        remaining_locations = [loc for loc in potential_locations if loc not in selected]
        while len(selected) < max_deadends and remaining_locations:
            selected.append(remaining_locations.pop(random.randint(0, len(remaining_locations) - 1)))

        return selected

    def _determine_deadend_type(self, location: tuple[int, int, str], room: Room) -> str:
        """
        デッドエンドのタイプを決定。

        Args:
        ----
            location: 配置位置
            room: 対象の部屋

        Returns:
        -------
            デッドエンドのタイプ

        """
        # 階層と戦略に応じてタイプを決定
        if self.deadend_strategy == "minimal":
            return "simple"
        if self.deadend_strategy == "moderate":
            return random.choice(["simple", "alcove"])
        if self.deadend_strategy == "complex":
            return random.choice(["simple", "alcove", "niche"])
        if self.deadend_strategy == "intricate":
            return random.choice(["alcove", "niche", "chamber"])
        # labyrinthine
        return random.choice(["niche", "chamber", "maze_stub"])

    def _create_deadend(
        self, location: tuple[int, int, str], deadend_type: str, tiles: list[list[Any]], tile_placer: callable
    ) -> list[tuple[int, int]]:
        """
        指定タイプのデッドエンドを作成。

        Args:
        ----
            location: 配置位置
            deadend_type: デッドエンドのタイプ
            tiles: タイル配列
            tile_placer: タイル配置関数

        Returns:
        -------
            作成されたデッドエンドの座標リスト

        """
        x, y, direction = location

        if deadend_type == "simple":
            return self._create_simple_deadend(x, y, direction, tiles, tile_placer)
        if deadend_type == "alcove":
            return self._create_alcove_deadend(x, y, direction, tiles, tile_placer)
        if deadend_type == "niche":
            return self._create_niche_deadend(x, y, direction, tiles, tile_placer)
        if deadend_type == "chamber":
            return self._create_chamber_deadend(x, y, direction, tiles, tile_placer)
        if deadend_type == "maze_stub":
            return self._create_maze_stub_deadend(x, y, direction, tiles, tile_placer)
        return self._create_simple_deadend(x, y, direction, tiles, tile_placer)

    def _create_simple_deadend(
        self, x: int, y: int, direction: str, tiles: list[list[Any]], tile_placer: callable
    ) -> list[tuple[int, int]]:
        """シンプルなデッドエンドを作成。"""
        points = []

        # 方向に応じたオフセット
        direction_offsets = {
            "north": (0, -1),
            "south": (0, 1),
            "west": (-1, 0),
            "east": (1, 0),
        }

        dx, dy = direction_offsets[direction]
        length = random.randint(2, 4)

        for i in range(length):
            new_x = x + dx * i
            new_y = y + dy * i

            if 0 <= new_x < self.width and 0 <= new_y < self.height:
                points.append((new_x, new_y))
                tile_placer(tiles, new_x, new_y, False)

        return points

    def _create_alcove_deadend(
        self, x: int, y: int, direction: str, tiles: list[list[Any]], tile_placer: callable
    ) -> list[tuple[int, int]]:
        """アルコーブ型デッドエンドを作成。"""
        points = []

        # 基本的なデッドエンドを作成
        base_points = self._create_simple_deadend(x, y, direction, tiles, tile_placer)
        points.extend(base_points)

        # 末端に小さな拡張を追加
        if base_points:
            end_x, end_y = base_points[-1]

            # 垂直方向に拡張
            if direction in ["north", "south"]:
                for offset in [-1, 1]:
                    new_x = end_x + offset
                    if 0 <= new_x < self.width and 0 <= end_y < self.height:
                        if isinstance(tiles[end_y][new_x], Wall):
                            points.append((new_x, end_y))
                            tile_placer(tiles, new_x, end_y, False)
            else:
                for offset in [-1, 1]:
                    new_y = end_y + offset
                    if 0 <= end_x < self.width and 0 <= new_y < self.height:
                        if isinstance(tiles[new_y][end_x], Wall):
                            points.append((end_x, new_y))
                            tile_placer(tiles, end_x, new_y, False)

        return points

    def _create_niche_deadend(
        self, x: int, y: int, direction: str, tiles: list[list[Any]], tile_placer: callable
    ) -> list[tuple[int, int]]:
        """ニッチ型デッドエンドを作成。"""
        points = []

        # 短いデッドエンドを作成
        direction_offsets = {
            "north": (0, -1),
            "south": (0, 1),
            "west": (-1, 0),
            "east": (1, 0),
        }

        dx, dy = direction_offsets[direction]

        # 短い通路
        for i in range(2):
            new_x = x + dx * i
            new_y = y + dy * i

            if 0 <= new_x < self.width and 0 <= new_y < self.height:
                points.append((new_x, new_y))
                tile_placer(tiles, new_x, new_y, False)

        # 末端に小さな部屋を作成
        if len(points) >= 2:
            end_x, end_y = points[-1]

            # 2x2の小部屋
            for offset_x in range(-1, 2):
                for offset_y in range(-1, 2):
                    new_x = end_x + offset_x
                    new_y = end_y + offset_y

                    if 0 <= new_x < self.width and 0 <= new_y < self.height and isinstance(tiles[new_y][new_x], Wall):
                        points.append((new_x, new_y))
                        tile_placer(tiles, new_x, new_y, False)

        return points

    def _create_chamber_deadend(
        self, x: int, y: int, direction: str, tiles: list[list[Any]], tile_placer: callable
    ) -> list[tuple[int, int]]:
        """チャンバー型デッドエンドを作成。"""
        points = []

        # 基本的なデッドエンドを作成
        base_points = self._create_simple_deadend(x, y, direction, tiles, tile_placer)
        points.extend(base_points)

        # 末端に大きな部屋を作成
        if base_points:
            end_x, end_y = base_points[-1]

            # 3x3の部屋
            for offset_x in range(-1, 2):
                for offset_y in range(-1, 2):
                    new_x = end_x + offset_x
                    new_y = end_y + offset_y

                    if 0 <= new_x < self.width and 0 <= new_y < self.height and isinstance(tiles[new_y][new_x], Wall):
                        points.append((new_x, new_y))
                        tile_placer(tiles, new_x, new_y, False)

        return points

    def _create_maze_stub_deadend(
        self, x: int, y: int, direction: str, tiles: list[list[Any]], tile_placer: callable
    ) -> list[tuple[int, int]]:
        """迷宮スタブ型デッドエンドを作成。"""
        points = []

        # 基本的なデッドエンドを作成
        base_points = self._create_simple_deadend(x, y, direction, tiles, tile_placer)
        points.extend(base_points)

        # 複数の分岐を追加
        if base_points and len(base_points) >= 2:
            branch_start = base_points[len(base_points) // 2]

            # 2-3個の短い分岐を追加
            for _ in range(random.randint(2, 3)):
                branch_direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                branch_x, branch_y = branch_start

                for i in range(1, 3):
                    new_x = branch_x + branch_direction[0] * i
                    new_y = branch_y + branch_direction[1] * i

                    if 0 <= new_x < self.width and 0 <= new_y < self.height and isinstance(tiles[new_y][new_x], Wall):
                        points.append((new_x, new_y))
                        tile_placer(tiles, new_x, new_y, False)

        return points

    def _place_isolated_deadends(
        self, rooms: list[Room], tiles: list[list[Any]], tile_placer: callable
    ) -> list[tuple[int, int]]:
        """孤立したデッドエンドを配置。"""
        deadends = []

        # 戦略に応じた配置数
        if self.deadend_strategy in ["complex", "intricate", "labyrinthine"]:
            num_isolated = random.randint(1, 3)
        else:
            num_isolated = 0

        for _ in range(num_isolated):
            # 空いている壁エリアを探す
            isolated_location = self._find_isolated_deadend_location(rooms, tiles)
            if isolated_location:
                deadend_type = self._determine_deadend_type(isolated_location, None)
                deadend_points = self._create_deadend(isolated_location, deadend_type, tiles, tile_placer)
                deadends.extend(deadend_points)

                self.deadend_locations.append(isolated_location[:2])
                self.deadend_types.append(deadend_type)
                self.deadends_created += 1

        return deadends

    def _place_special_deadends(
        self, rooms: list[Room], tiles: list[list[Any]], tile_placer: callable
    ) -> list[tuple[int, int]]:
        """特殊なデッドエンドを配置。"""
        deadends = []

        # 最深階層でのみ特殊デッドエンドを配置
        if self.deadend_strategy == "labyrinthine":
            # 特殊デッドエンドのロジックを実装
            pass

        return deadends

    def _find_isolated_deadend_location(self, rooms: list[Room], tiles: list[list[Any]]) -> tuple[int, int, str] | None:
        """孤立したデッドエンドの配置位置を検索。"""
        attempts = 50

        for _ in range(attempts):
            x = random.randint(5, self.width - 5)
            y = random.randint(5, self.height - 5)

            # 部屋から十分離れているかチェック
            if self._is_far_from_rooms(x, y, rooms, min_distance=5):
                # 適切な壁エリアかチェック
                if isinstance(tiles[y][x], Wall):
                    direction = random.choice(["north", "south", "west", "east"])
                    return (x, y, direction)

        return None

    def _is_far_from_rooms(self, x: int, y: int, rooms: list[Room], min_distance: int) -> bool:
        """指定位置が部屋から十分離れているかチェック。"""
        for room in rooms:
            room_center = room.center()
            distance = abs(x - room_center[0]) + abs(y - room_center[1])
            if distance < min_distance:
                return False
        return True

    def get_deadend_statistics(self) -> dict[str, Any]:
        """
        デッドエンド配置統計を取得。

        Returns
        -------
            統計情報の辞書

        """
        type_counts = {}
        for deadend_type in self.deadend_types:
            type_counts[deadend_type] = type_counts.get(deadend_type, 0) + 1

        return {
            "total_deadends": self.deadends_created,
            "strategy": self.deadend_strategy,
            "floor": self.floor,
            "deadend_types": type_counts,
            "deadend_locations": len(self.deadend_locations),
            "strategy_description": self._get_strategy_description(),
        }

    def _get_strategy_description(self) -> str:
        """戦略の説明を取得。"""
        descriptions = {
            "minimal": "最小限のデッドエンド - 初心者向け",
            "moderate": "適度なデッドエンド - バランス重視",
            "complex": "複雑なデッドエンド - 挑戦的",
            "intricate": "入り組んだデッドエンド - 高難易度",
            "labyrinthine": "迷宮のようなデッドエンド - 最高難易度",
        }

        return descriptions.get(self.deadend_strategy, "不明な戦略")
