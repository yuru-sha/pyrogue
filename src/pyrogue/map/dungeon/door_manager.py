"""
ドア管理コンポーネント - ドア配置専用。

このモジュールは、ダンジョンのドア配置に特化したマネージャーです。
通常のドア、隠しドア、特別部屋用ドアの配置と種類決定を担当します。
"""

from __future__ import annotations

import random

import numpy as np

from pyrogue.constants import ProbabilityConstants
from pyrogue.map.dungeon.corridor_builder import Corridor
from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Door, SecretDoor
from pyrogue.utils import game_logger


class DoorManager:
    """
    ドア配置専用のマネージャークラス。

    通常のドア、隠しドア、特別部屋用ドアの配置、
    ドア種類の決定、配置位置の検証を担当します。
    """

    def __init__(self) -> None:
        """ドアマネージャーを初期化。"""
        self.placed_doors = []

    def place_doors(
        self,
        rooms: list[Room],
        corridors: list[Corridor],
        tiles: np.ndarray
    ) -> None:
        """
        ドアを配置。

        Args:
            rooms: 部屋のリスト
            corridors: 通路のリスト
            tiles: ダンジョンのタイル配列

        """
        self.placed_doors = []

        # 新しいアプローチ: 通路から部屋への接続点を直接探す
        for room in rooms:
            door_positions = self._find_corridor_to_room_connections(room, corridors, tiles)

            # 各部屋に最大2個のドアまでに制限
            door_positions = door_positions[:2]

            for x, y in door_positions:
                door_type = self._determine_door_type(room, (x, y))
                self._place_door_at_position(x, y, door_type, room, tiles)

        game_logger.info(f"Placed {len(self.placed_doors)} doors")

    def _find_corridor_to_room_connections(
        self,
        room: Room,
        corridors: list[Corridor],
        tiles: np.ndarray
    ) -> list[tuple[int, int]]:
        """
        通路から部屋への接続点を直接探す。

        Args:
            room: 対象の部屋
            corridors: 通路のリスト
            tiles: ダンジョンのタイル配列

        Returns:
            ドア配置位置のリスト

        """
        door_positions = []

        # 各通路の各座標について、部屋の内部に隣接しているかチェック
        for corridor in corridors:
            for corridor_x, corridor_y in corridor.points:
                # 通路座標の4方向をチェック
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    adj_x, adj_y = corridor_x + dx, corridor_y + dy

                    # 隣接位置が部屋の内部かチェック
                    if (adj_x, adj_y) in room.inner:
                        # 通路座標をドア位置として追加
                        if (corridor_x, corridor_y) not in door_positions:
                            door_positions.append((corridor_x, corridor_y))
                        break  # この通路座標は既に処理したので次へ

        return door_positions

    def _is_room_boundary(self, x: int, y: int, room: Room) -> bool:
        """
        指定座標が部屋の境界（壁）かチェック。

        Args:
            x: X座標
            y: Y座標
            room: 部屋

        Returns:
            部屋の境界の場合True

        """
        # 部屋の境界矩形内にあり、かつ内部ではない
        return (room.x <= x <= room.x + room.width - 1 and
                room.y <= y <= room.y + room.height - 1 and
                (x, y) not in room.inner)

    def _find_door_positions(
        self,
        room: Room,
        corridors: list[Corridor],
        tiles: np.ndarray
    ) -> list[tuple[int, int]]:
        """
        部屋のドア配置位置を見つける。

        Args:
            room: 対象の部屋
            corridors: 通路のリスト
            tiles: ダンジョンのタイル配列

        Returns:
            ドア配置位置のリスト

        """
        door_positions = []

        # 部屋の境界をチェック
        for wall_pos in self._get_room_wall_positions(room):
            if self._should_place_door_at(wall_pos, room, corridors, tiles):
                door_positions.append(wall_pos)

        return door_positions

    def _get_room_wall_positions(self, room: Room) -> list[tuple[int, int]]:
        """
        部屋の壁の位置を取得。

        Args:
            room: 対象の部屋

        Returns:
            壁の位置のリスト

        """
        wall_positions = []

        # 北壁と南壁
        for x in range(room.x, room.x + room.width):
            wall_positions.append((x, room.y))  # 北壁
            wall_positions.append((x, room.y + room.height - 1))  # 南壁

        # 西壁と東壁（角は除外）
        for y in range(room.y + 1, room.y + room.height - 1):
            wall_positions.append((room.x, y))  # 西壁
            wall_positions.append((room.x + room.width - 1, y))  # 東壁

        return wall_positions

    def _should_place_door_at(
        self,
        position: tuple[int, int],
        room: Room,
        corridors: list[Corridor],
        tiles: np.ndarray
    ) -> bool:
        """
        指定位置にドアを配置すべきかチェック。

        壁の両側をチェックし、片側が部屋の内部、もう片側が通路の場合のみTrue。

        Args:
            position: チェック位置（壁の座標）
            room: 部屋
            corridors: 通路のリスト
            tiles: ダンジョンのタイル配列

        Returns:
            ドアを配置すべき場合True

        """
        from pyrogue.map.tile import Floor

        x, y = position

        # 壁に対して垂直な方向（2つの対向する方向）をチェック
        directions = [
            [(0, 1), (0, -1)],  # 南北
            [(1, 0), (-1, 0)]   # 東西
        ]

        for dir_pair in directions:
            room_side = None
            corridor_side = None

            for dx, dy in dir_pair:
                adj_x, adj_y = x + dx, y + dy

                # 境界チェック
                if not (0 <= adj_x < tiles.shape[1] and 0 <= adj_y < tiles.shape[0]):
                    continue

                if not isinstance(tiles[adj_y, adj_x], Floor):
                    continue

                # 部屋の内部かチェック
                if (adj_x, adj_y) in room.inner:
                    room_side = (adj_x, adj_y)
                # 通路かチェック
                elif self._is_corridor_tile(adj_x, adj_y, room, corridors):
                    corridor_side = (adj_x, adj_y)

            # 片側が部屋内部、もう片側が通路の場合はドア配置
            if room_side is not None and corridor_side is not None:
                return True

        return False

    def _is_corridor_tile(
        self,
        x: int,
        y: int,
        room: Room,
        corridors: list[Corridor]
    ) -> bool:
        """
        指定座標が通路のタイルかチェック。

        Args:
            x: X座標
            y: Y座標
            room: 部屋
            corridors: 通路のリスト

        Returns:
            通路のタイルの場合True

        """
        # 部屋の内部にある場合は通路ではない
        if (room.x < x < room.x + room.width - 1 and
            room.y < y < room.y + room.height - 1):
            return False

        # 通路の座標リストに含まれているかチェック
        for corridor in corridors:
            if (x, y) in corridor.points:
                return True

        return False

    def _is_corridor_connection(
        self,
        position: tuple[int, int],
        corridors: list[Corridor]
    ) -> bool:
        """
        位置が通路との接続点かチェック。

        Args:
            position: チェック位置
            corridors: 通路のリスト

        Returns:
            通路との接続点の場合True

        """
        x, y = position

        # 隣接する位置に通路があるかチェック
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            adj_x, adj_y = x + dx, y + dy

            for corridor in corridors:
                if (adj_x, adj_y) in corridor.points:
                    return True

        return False

    def _is_main_door_position(self, position: tuple[int, int], room: Room) -> bool:
        """
        位置がメインドア位置（部屋の中央壁）かチェック。

        Args:
            position: チェック位置
            room: 部屋

        Returns:
            メインドア位置の場合True

        """
        x, y = position

        # 各壁の中央付近かチェック
        center_x = room.x + room.width // 2
        center_y = room.y + room.height // 2

        # 北壁または南壁の中央
        if ((y == room.y or y == room.y + room.height - 1) and
            abs(x - center_x) <= 1):
            return True

        # 西壁または東壁の中央
        if ((x == room.x or x == room.x + room.width - 1) and
            abs(y - center_y) <= 1):
            return True

        return False

    def _determine_door_type(self, room: Room, position: tuple[int, int]) -> type:
        """
        ドアの種類を決定。

        Args:
            room: 部屋
            position: ドア位置

        Returns:
            ドアクラス（Door または SecretDoor）

        """
        # 特別な部屋は通常のドア
        if room.is_special:
            return Door

        # 隠しドアの確率判定
        if random.random() < ProbabilityConstants.SECRET_DOOR_CHANCE:
            return SecretDoor

        return Door

    def _place_door_at_position(
        self,
        x: int,
        y: int,
        door_type: type,
        room: Room,
        tiles: np.ndarray
    ) -> None:
        """
        指定位置にドアを配置。

        Args:
            x: X座標
            y: Y座標
            door_type: ドアの種類
            room: 部屋
            tiles: ダンジョンのタイル配列

        """
        if self._validate_door_placement(x, y, tiles):
            door = door_type()
            tiles[y, x] = door
            room.add_door(x, y)
            self.placed_doors.append((x, y, door_type.__name__))

            game_logger.debug(
                f"Placed {door_type.__name__} at ({x}, {y}) for room {room.id}"
            )

    def _validate_door_placement(self, x: int, y: int, tiles: np.ndarray) -> bool:
        """
        ドア配置の有効性を検証。

        Args:
            x: X座標
            y: Y座標
            tiles: ダンジョンのタイル配列

        Returns:
            有効な配置の場合True

        """
        from pyrogue.map.tile import Floor, Wall

        height, width = tiles.shape

        # 境界チェック
        if x < 0 or y < 0 or x >= width or y >= height:
            return False

        # 既にドアが配置されているかチェック
        current_tile = tiles[y, x]
        if isinstance(current_tile, (Door, SecretDoor)):
            return False

        # 壁または床（通路）の位置でなければドアは配置できない
        if not isinstance(current_tile, (Wall, Floor)):
            return False

        return True

    def get_door_at_position(self, x: int, y: int, tiles: np.ndarray) -> Door | SecretDoor | None:
        """
        指定位置のドアを取得。

        Args:
            x: X座標
            y: Y座標
            tiles: ダンジョンのタイル配列

        Returns:
            見つかったドア、または None

        """
        if (0 <= x < tiles.shape[1] and 0 <= y < tiles.shape[0]):
            tile = tiles[y, x]
            if isinstance(tile, (Door, SecretDoor)):
                return tile
        return None

    def count_doors_by_type(self) -> dict:
        """
        種類別のドア数をカウント。

        Returns:
            ドア種類とその数の辞書

        """
        door_counts = {}
        for _, _, door_type in self.placed_doors:
            door_counts[door_type] = door_counts.get(door_type, 0) + 1
        return door_counts

    def reset(self) -> None:
        """マネージャーの状態をリセット。"""
        self.placed_doors = []

    def get_statistics(self) -> dict:
        """ドア配置の統計情報を取得。"""
        door_counts = self.count_doors_by_type()

        return {
            "total_doors": len(self.placed_doors),
            "door_types": door_counts,
            "secret_door_ratio": door_counts.get("SecretDoor", 0) / max(1, len(self.placed_doors)),
        }
