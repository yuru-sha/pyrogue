"""
階段管理コンポーネント - 階段配置専用。

このモジュールは、ダンジョンの階段配置に特化したマネージャーです。
上り階段、下り階段の配置位置決定と配置処理を担当します。
"""

from __future__ import annotations

import random

import numpy as np

from pyrogue.constants import GameConstants
from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Floor, StairsDown, StairsUp
from pyrogue.utils import game_logger


class StairsManager:
    """
    階段配置専用のマネージャークラス。

    上り階段、下り階段の配置、位置決定、
    階層に応じた配置ルールの管理を担当します。

    Attributes
    ----------
        stairs_placed: 配置された階段の情報

    """

    def __init__(self) -> None:
        """階段マネージャーを初期化。"""
        self.stairs_placed: list[tuple[str, tuple[int, int], str]] = []

    def _find_safe_fallback_position(self, tiles: np.ndarray) -> tuple[int, int]:
        """
        安全なフォールバック位置を動的に検索。

        Args:
        ----
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            安全な座標のタプル (x, y)

        """
        height, width = tiles.shape

        # 中央付近から適切な床タイルを探す
        center_x, center_y = width // 2, height // 2

        # 中央付近の床タイルを探索
        search_radius = min(width, height) // 4
        for radius in range(1, search_radius + 1):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    x, y = center_x + dx, center_y + dy
                    if 1 <= x < width - 1 and 1 <= y < height - 1 and isinstance(tiles[y, x], Floor):
                        return (x, y)

        # 最終フォールバック: ダンジョン境界内の安全な位置
        fallback_x = max(2, min(width - 3, width // 4))
        fallback_y = max(2, min(height - 3, height // 4))
        return (fallback_x, fallback_y)

    def place_stairs(self, rooms: list[Room], floor: int, tiles: np.ndarray) -> tuple[tuple[int, int], tuple[int, int]]:
        """
        階段を配置。

        Args:
        ----
            rooms: 部屋のリスト
            floor: 階層番号
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            (上り階段位置, 下り階段位置) のタプル

        """
        self.stairs_placed = []

        # 上り階段の配置
        up_stairs_pos = self._place_up_stairs(rooms, floor, tiles)

        # 下り階段の配置
        down_stairs_pos = self._place_down_stairs(rooms, floor, tiles)

        game_logger.info(f"Placed stairs on floor {floor}: up at {up_stairs_pos}, down at {down_stairs_pos}")

        return up_stairs_pos, down_stairs_pos

    def place_stairs_for_maze(self, floor: int, tiles: np.ndarray) -> tuple[tuple[int, int], tuple[int, int]]:
        """
        迷路専用の階段配置。

        Args:
        ----
            floor: 階層番号
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            (上り階段位置, 下り階段位置) のタプル

        """
        self.stairs_placed = []

        # 迷路では部屋がないので、通路のFloorタイルから適切な位置を探す
        floor_positions = self._find_floor_positions(tiles)

        if not floor_positions:
            # フォールバック: 動的に安全な位置を検索
            up_pos = self._find_safe_fallback_position(tiles)
            down_pos = (tiles.shape[1] - 2, tiles.shape[0] - 2)
        else:
            # 上り階段: 最初の方の位置
            up_pos = floor_positions[0]
            # 下り階段: 最後の方の位置（距離を離す）
            down_pos = floor_positions[-1] if len(floor_positions) > 1 else floor_positions[0]

            # もし同じ位置なら、別の位置を探す
            if up_pos == down_pos and len(floor_positions) > 1:
                down_pos = floor_positions[len(floor_positions) // 2]

        # 上り階段を配置（1階は不要）
        if floor > 1:
            tiles[up_pos[1], up_pos[0]] = StairsUp()
            self.stairs_placed.append(("up", up_pos, "maze"))
            game_logger.debug(f"Placed up stairs at {up_pos} in maze")
        else:
            # 1階では上り階段の代わりにプレイヤー開始位置として記録
            game_logger.debug(f"Set player start position at {up_pos} on floor 1")

        # 下り階段を配置（最下層は不要）
        if floor < GameConstants.MAX_FLOORS:
            tiles[down_pos[1], down_pos[0]] = StairsDown()
            self.stairs_placed.append(("down", down_pos, "maze"))
            game_logger.debug(f"Placed down stairs at {down_pos} in maze")
        else:
            # 最下層では下り階段の代わりにエンディング位置として記録
            game_logger.debug(f"Set ending position at {down_pos} on floor {floor}")

        game_logger.info(f"Placed maze stairs on floor {floor}: up at {up_pos}, down at {down_pos}")

        return up_pos, down_pos

    def _find_floor_positions(self, tiles: np.ndarray) -> list[tuple[int, int]]:
        """
        Floorタイルの位置を検索。

        Args:
        ----
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            Floorタイルの位置リスト

        """
        positions = []
        for y in range(tiles.shape[0]):
            for x in range(tiles.shape[1]):
                if isinstance(tiles[y, x], Floor):
                    positions.append((x, y))
        return positions

    def _place_up_stairs(self, rooms: list[Room], floor: int, tiles: np.ndarray) -> tuple[int, int]:
        """
        上り階段を配置。

        Args:
        ----
            rooms: 部屋のリスト
            floor: 階層番号
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            上り階段の位置

        """
        # 1階では上り階段は不要
        if floor <= 1:
            return None

        # 上り階段用の部屋を選択
        up_stairs_room = self._select_stairs_room(rooms, "up", floor)

        if up_stairs_room:
            position = self._find_stairs_position(up_stairs_room, tiles)
            if position:
                tiles[position[1], position[0]] = StairsUp()
                self.stairs_placed.append(("up", position, up_stairs_room.id))
                game_logger.debug(f"Placed up stairs at {position} in room {up_stairs_room.id}")
                return position

        # フォールバック：最初の部屋の中央
        if rooms:
            fallback_room = rooms[0]
            center = fallback_room.center()
            tiles[center[1], center[0]] = StairsUp()
            self.stairs_placed.append(("up", center, fallback_room.id))
            return center

        return self._find_safe_fallback_position(tiles)  # 動的最終フォールバック

    def _place_down_stairs(self, rooms: list[Room], floor: int, tiles: np.ndarray) -> tuple[int, int]:
        """
        下り階段を配置。

        Args:
        ----
            rooms: 部屋のリスト
            floor: 階層番号
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            下り階段の位置

        """
        # 最深階では下り階段は不要
        if floor >= GameConstants.MAX_FLOORS:
            return None

        # 下り階段用の部屋を選択
        down_stairs_room = self._select_stairs_room(rooms, "down", floor)

        if down_stairs_room:
            position = self._find_stairs_position(down_stairs_room, tiles)
            if position:
                tiles[position[1], position[0]] = StairsDown()
                self.stairs_placed.append(("down", position, down_stairs_room.id))
                game_logger.debug(f"Placed down stairs at {position} in room {down_stairs_room.id}")
                return position

        # フォールバック：最後の部屋の中央
        if rooms:
            fallback_room = rooms[-1]
            center = fallback_room.center()
            tiles[center[1], center[0]] = StairsDown()
            self.stairs_placed.append(("down", center, fallback_room.id))
            return center

        return self._find_safe_fallback_position(tiles)  # 動的最終フォールバック

    def _select_stairs_room(self, rooms: list[Room], stairs_type: str, floor: int) -> Room | None:
        """
        階段配置用の部屋を選択。

        Args:
        ----
            rooms: 部屋のリスト
            stairs_type: 階段の種類（"up" または "down"）
            floor: 階層番号

        Returns:
        -------
            選択された部屋、または None

        """
        if not rooms:
            return None

        # 特別部屋とアミュレット部屋を除外
        suitable_rooms = [room for room in rooms if not room.is_special or room.room_type != "amulet_chamber"]

        if not suitable_rooms:
            suitable_rooms = rooms

        # 階段の種類に応じて選択ロジックを変更
        if stairs_type == "up":
            # 上り階段は最初の方の部屋に配置
            return self._select_room_by_criteria(suitable_rooms, "first")
        # 下り階段は最後の方の部屋に配置
        return self._select_room_by_criteria(suitable_rooms, "last")

    def _select_room_by_criteria(self, rooms: list[Room], criteria: str) -> Room:
        """
        基準に応じて部屋を選択。

        Args:
        ----
            rooms: 部屋のリスト
            criteria: 選択基準（"first", "last", "random", "largest"）

        Returns:
        -------
            選択された部屋

        """
        if criteria == "first":
            # 最初の3つの部屋からランダム選択
            candidate_rooms = rooms[: min(3, len(rooms))]
            return random.choice(candidate_rooms)

        if criteria == "last":
            # 最後の3つの部屋からランダム選択
            candidate_rooms = rooms[-min(3, len(rooms)) :]
            return random.choice(candidate_rooms)

        if criteria == "largest":
            # 最も大きい部屋を選択
            return max(rooms, key=lambda r: r.width * r.height)

        # "random"
        return random.choice(rooms)

    def _find_stairs_position(self, room: Room, tiles: np.ndarray) -> tuple[int, int] | None:
        """
        部屋内の階段配置位置を見つける。

        Args:
        ----
            room: 対象の部屋
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            階段位置、または None

        """
        # 部屋の中央付近から候補位置を選択
        center_x, center_y = room.center()

        # 中央から順に候補位置をチェック
        candidates = [
            (center_x, center_y),
            (center_x - 1, center_y),
            (center_x + 1, center_y),
            (center_x, center_y - 1),
            (center_x, center_y + 1),
        ]

        for x, y in candidates:
            if self._is_valid_stairs_position(x, y, room, tiles):
                return (x, y)

        # フォールバック：部屋内のランダム位置
        for _ in range(10):  # 最大10回試行
            x = random.randint(room.x + 1, room.x + room.width - 2)
            y = random.randint(room.y + 1, room.y + room.height - 2)

            if self._is_valid_stairs_position(x, y, room, tiles):
                return (x, y)

        return None

    def _is_valid_stairs_position(self, x: int, y: int, room: Room, tiles: np.ndarray) -> bool:
        """
        階段配置位置が有効かチェック。

        Args:
        ----
            x: X座標
            y: Y座標
            room: 部屋
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            有効な位置の場合True

        """
        # 部屋の境界内かチェック
        if x <= room.x or x >= room.x + room.width - 1 or y <= room.y or y >= room.y + room.height - 1:
            return False

        # 既に階段が配置されているかチェック
        current_tile = tiles[y, x]
        if isinstance(current_tile, (StairsUp, StairsDown)):
            return False

        # 部屋の内部（床）であることを確認
        from pyrogue.map.tile import Floor

        if not isinstance(current_tile, Floor):
            return False

        return True

    def get_stairs_positions(self) -> dict:
        """
        配置された階段の位置を取得。

        Returns
        -------
            階段種類と位置の辞書

        """
        positions = {}
        for stairs_type, position, room_id in self.stairs_placed:
            positions[stairs_type] = {"position": position, "room_id": room_id}
        return positions

    def validate_stairs_placement(self, tiles: np.ndarray) -> bool:
        """
        階段配置の妥当性を検証。

        Args:
        ----
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            妥当な配置の場合True

        """
        up_stairs_count = 0
        down_stairs_count = 0

        height, width = tiles.shape
        for y in range(height):
            for x in range(width):
                tile = tiles[y, x]
                if isinstance(tile, StairsUp):
                    up_stairs_count += 1
                elif isinstance(tile, StairsDown):
                    down_stairs_count += 1

        # 階段が適切に配置されているかチェック
        # 1階以外では上り階段が1つ、最深階以外では下り階段が1つ必要
        return up_stairs_count <= 1 and down_stairs_count <= 1

    def reset(self) -> None:
        """マネージャーの状態をリセット。"""
        self.stairs_placed = []

    def _place_maze_stairs(
        self,
        floor_positions: list[tuple[int, int]],
        tiles: np.ndarray,
        stairs_type: str,
        avoid_position: tuple[int, int] | None = None,
    ) -> tuple[int, int] | None:
        """
        迷路内の階段を配置。

        Args:
        ----
            floor_positions: 利用可能な床位置のリスト
            tiles: ダンジョンのタイル配列
            stairs_type: 階段の種類（"up" または "down"）
            avoid_position: 避けるべき位置

        Returns:
        -------
            階段位置、または None

        """
        # 階段配置に適した位置を選択
        # 迷路の場合、デッドエンドや角の位置を優先
        preferred_positions = []

        for x, y in floor_positions:
            # 回避位置をチェック
            if avoid_position and (x, y) == avoid_position:
                continue

            # 隣接する床タイルの数をカウント
            adjacent_floors = 0
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < tiles.shape[1] and 0 <= ny < tiles.shape[0] and isinstance(tiles[ny, nx], Floor):
                    adjacent_floors += 1

            # デッドエンド（隣接する床が1つ）を優先
            if adjacent_floors == 1:
                preferred_positions.append((x, y))

        # 優先位置がない場合は通常の床位置を使用
        if not preferred_positions:
            preferred_positions = [pos for pos in floor_positions if pos != avoid_position]

        if not preferred_positions:
            return None

        # ランダムに選択
        position = random.choice(preferred_positions)

        # 階段を配置
        if stairs_type == "up":
            tiles[position[1], position[0]] = StairsUp()
        else:
            tiles[position[1], position[0]] = StairsDown()

        self.stairs_placed.append((stairs_type, position, "maze"))
        return position

    def get_statistics(self) -> dict:
        """階段配置の統計情報を取得。"""
        return {
            "stairs_placed": len(self.stairs_placed),
            "stairs_info": [
                {"type": stairs_type, "position": position, "room_id": room_id}
                for stairs_type, position, room_id in self.stairs_placed
            ],
        }
