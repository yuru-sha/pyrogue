"""
部屋ビルダー - 部屋生成専用コンポーネント。

このモジュールは、ダンジョンの部屋生成に特化したビルダーです。
3x3グリッドでの部屋配置、サイズ計算、特別部屋の判定を担当します。
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from pyrogue.constants import ProbabilityConstants
from pyrogue.utils import game_logger


@dataclass
class Room:
    """
    部屋を表すデータクラス。
    """

    x: int
    y: int
    width: int
    height: int
    is_special: bool = False
    room_type: str = None
    connected_rooms: set = None
    doors: list = None
    id: int = None

    def __post_init__(self):
        if self.connected_rooms is None:
            self.connected_rooms = set()
        if self.doors is None:
            self.doors = []

    def center(self) -> tuple[int, int]:
        """部屋の中心座標を取得。"""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def is_connected_to(self, other_room: Room) -> bool:
        """他の部屋と接続されているかチェック。"""
        return other_room.id in self.connected_rooms if other_room.id else False

    def add_connection(self, other_room: Room) -> None:
        """他の部屋との接続を追加。"""
        if other_room.id:
            self.connected_rooms.add(other_room.id)
            other_room.connected_rooms.add(self.id)

    def add_door(self, x: int, y: int) -> None:
        """ドアを追加。"""
        self.doors.append((x, y))

    @property
    def inner(self) -> list[tuple[int, int]]:
        """部屋の内部座標リストを取得（後方互換性のため）。"""
        inner_positions = []
        for y in range(self.y + 1, self.y + self.height - 1):
            for x in range(self.x + 1, self.x + self.width - 1):
                inner_positions.append((x, y))
        return inner_positions


class RoomBuilder:
    """
    部屋生成専用のビルダークラス。

    3x3グリッドシステムでの部屋配置、適切なサイズ計算、
    Gone Room（通路のみのセル）の管理を担当します。

    Attributes:
        width: ダンジョンの幅
        height: ダンジョンの高さ
        floor: 現在の階層
        grid_width: グリッドの幅（通常は3）
        grid_height: グリッドの高さ（通常は3）
        room_counter: 部屋ID用のカウンター

    """

    def __init__(self, width: int, height: int, floor: int) -> None:
        """
        部屋ビルダーを初期化。

        Args:
            width: ダンジョンの幅
            height: ダンジョンの高さ
            floor: 階層番号

        """
        self.width = width
        self.height = height
        self.floor = floor
        self.grid_width = 3
        self.grid_height = 3
        self.room_counter = 0

        # グリッドセルのサイズを計算
        self.cell_width = width // self.grid_width
        self.cell_height = height // self.grid_height

        game_logger.debug(
            f"RoomBuilder initialized: {self.grid_width}x{self.grid_height} grid, "
            f"cell size: {self.cell_width}x{self.cell_height}"
        )

    def create_room_grid(self) -> list[Room]:
        """
        3x3グリッドで部屋を生成。

        Returns:
            生成された部屋のリスト

        """
        rooms = []

        for grid_y in range(self.grid_height):
            for grid_x in range(self.grid_width):
                # Gone Room（通路のみ）の判定
                if self._should_create_gone_room():
                    game_logger.debug(f"Gone room at grid ({grid_x}, {grid_y})")
                    continue

                room = self._generate_room_at_grid(grid_x, grid_y)
                if room:
                    rooms.append(room)

        game_logger.info(f"Generated {len(rooms)} rooms on floor {self.floor}")
        return rooms

    def _should_create_gone_room(self) -> bool:
        """
        Gone Room（通路のみのセル）を作成するかどうかを判定。

        Returns:
            Gone Roomを作成する場合True

        """
        return random.random() < ProbabilityConstants.GONE_ROOM_CHANCE

    def _generate_room_at_grid(self, grid_x: int, grid_y: int) -> Room:
        """
        指定されたグリッド位置に部屋を生成。

        Args:
            grid_x: グリッドのX座標
            grid_y: グリッドのY座標

        Returns:
            生成された部屋

        """
        # グリッドセル内での部屋の位置とサイズを計算
        cell_start_x = grid_x * self.cell_width
        cell_start_y = grid_y * self.cell_height

        # 部屋のサイズをランダムに決定（セルサイズの50-80%）
        min_room_width = max(4, self.cell_width // 2)
        max_room_width = max(min_room_width + 1, int(self.cell_width * 0.8))
        min_room_height = max(4, self.cell_height // 2)
        max_room_height = max(min_room_height + 1, int(self.cell_height * 0.8))

        room_width = random.randint(min_room_width, max_room_width)
        room_height = random.randint(min_room_height, max_room_height)

        # 部屋の位置をセル内でランダムに決定
        max_room_x = cell_start_x + self.cell_width - room_width - 1
        max_room_y = cell_start_y + self.cell_height - room_height - 1

        room_x = random.randint(cell_start_x + 1, max(cell_start_x + 1, max_room_x))
        room_y = random.randint(cell_start_y + 1, max(cell_start_y + 1, max_room_y))

        # 境界チェック
        room_x = max(1, min(room_x, self.width - room_width - 1))
        room_y = max(1, min(room_y, self.height - room_height - 1))
        room_width = min(room_width, self.width - room_x - 1)
        room_height = min(room_height, self.height - room_y - 1)

        # 部屋を作成
        self.room_counter += 1
        room = Room(
            x=room_x,
            y=room_y,
            width=room_width,
            height=room_height,
            id=self.room_counter
        )

        game_logger.debug(
            f"Generated room {room.id} at grid ({grid_x}, {grid_y}): "
            f"position ({room.x}, {room.y}), size {room.width}x{room.height}"
        )

        return room

    def get_room_grid_position(self, room: Room) -> tuple[int, int]:
        """
        部屋のグリッド位置を取得。

        Args:
            room: 対象の部屋

        Returns:
            (grid_x, grid_y) のタプル

        """
        grid_x = room.x // self.cell_width
        grid_y = room.y // self.cell_height

        # 境界チェック
        grid_x = max(0, min(grid_x, self.grid_width - 1))
        grid_y = max(0, min(grid_y, self.grid_height - 1))

        return grid_x, grid_y

    def get_adjacent_grid_positions(self, grid_pos: tuple[int, int]) -> list[tuple[int, int]]:
        """
        隣接するグリッド位置を取得。

        Args:
            grid_pos: 基準となるグリッド位置

        Returns:
            隣接するグリッド位置のリスト

        """
        grid_x, grid_y = grid_pos
        adjacent = []

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                new_x = grid_x + dx
                new_y = grid_y + dy

                if (0 <= new_x < self.grid_width and
                    0 <= new_y < self.grid_height):
                    adjacent.append((new_x, new_y))

        return adjacent

    def find_room_at_grid(self, rooms: list[Room], grid_x: int, grid_y: int) -> Room | None:
        """
        指定されたグリッド位置の部屋を検索。

        Args:
            rooms: 部屋のリスト
            grid_x: グリッドのX座標
            grid_y: グリッドのY座標

        Returns:
            見つかった部屋、または None

        """
        for room in rooms:
            room_grid_x, room_grid_y = self.get_room_grid_position(room)
            if room_grid_x == grid_x and room_grid_y == grid_y:
                return room
        return None

    def calculate_room_dimensions(
        self,
        grid_pos: tuple[int, int],
        is_special: bool = False
    ) -> tuple[int, int, int, int]:
        """
        グリッド位置に基づいて部屋の寸法を計算。

        Args:
            grid_pos: グリッド位置
            is_special: 特別な部屋かどうか

        Returns:
            (x, y, width, height) のタプル

        """
        grid_x, grid_y = grid_pos
        cell_start_x = grid_x * self.cell_width
        cell_start_y = grid_y * self.cell_height

        if is_special:
            # 特別な部屋はより大きく
            room_width = max(6, int(self.cell_width * 0.9))
            room_height = max(6, int(self.cell_height * 0.9))
        else:
            # 通常の部屋
            min_width = max(4, self.cell_width // 2)
            max_width = max(min_width + 1, int(self.cell_width * 0.8))
            min_height = max(4, self.cell_height // 2)
            max_height = max(min_height + 1, int(self.cell_height * 0.8))

            room_width = random.randint(min_width, max_width)
            room_height = random.randint(min_height, max_height)

        # 位置を計算
        max_x = cell_start_x + self.cell_width - room_width - 1
        max_y = cell_start_y + self.cell_height - room_height - 1

        room_x = random.randint(cell_start_x + 1, max(cell_start_x + 1, max_x))
        room_y = random.randint(cell_start_y + 1, max(cell_start_y + 1, max_y))

        # 境界チェック
        room_x = max(1, min(room_x, self.width - room_width - 1))
        room_y = max(1, min(room_y, self.height - room_height - 1))
        room_width = min(room_width, self.width - room_x - 1)
        room_height = min(room_height, self.height - room_y - 1)

        return room_x, room_y, room_width, room_height

    def reset(self) -> None:
        """ビルダーの状態をリセット。"""
        self.room_counter = 0

    def get_statistics(self) -> dict:
        """部屋生成の統計情報を取得。"""
        return {
            "grid_dimensions": f"{self.grid_width}x{self.grid_height}",
            "cell_size": f"{self.cell_width}x{self.cell_height}",
            "rooms_generated": self.room_counter,
            "floor": self.floor,
        }
