"""
TCOD BSPを使用したダンジョン生成システム。

TCOD(The Doryen Library)のBinary Space Partitioning機能を使用して、
高品質で安定したダンジョンを生成する。
"""

from __future__ import annotations

import random

import numpy as np
import tcod.bsp

from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Door, Floor, Wall
from pyrogue.utils import game_logger

# BSP生成の定数
DEFAULT_BSP_DEPTH = 5
DEFAULT_ROOM_MARGIN = 2
DEFAULT_ROOM_SIZE_VARIANCE = 6
MAX_ASPECT_RATIO = 1.5
MIN_SECTION_MULTIPLIER = 2
CORRIDOR_PADDING = 3


class BSPDungeonBuilder:
    """
    TCOD BSPを使用したダンジョン生成ビルダー。

    TCODライブラリの信頼性の高いBSPアルゴリズムを使用して、
    構造化されたダンジョンを生成する。
    """

    def __init__(self, width: int, height: int, min_section_size: int = 6) -> None:
        """
        TCOD BSPダンジョンビルダーを初期化。

        Args:
        ----
            width: ダンジョンの幅
            height: ダンジョンの高さ
            min_section_size: 部屋の最小サイズ

        """
        self.width = width
        self.height = height
        self.min_room_size = min_section_size  # 互換性のため
        self.rooms: list[Room] = []

        game_logger.info(
            f"TCOD BSP DungeonBuilder initialized: {width}x{height}, min_room_size={min_section_size}"
        )

    def build_dungeon(self, tiles: np.ndarray) -> list[Room]:
        """
        TCOD BSPを使用してダンジョンを生成。

        Args:
        ----
            tiles: タイル配列

        Returns:
        -------
            生成された部屋のリスト

        """
        # 1. TCOD BSPツリーを作成・分割
        bsp = tcod.bsp.BSP(x=0, y=0, width=self.width, height=self.height)
        bsp.split_recursive(
            depth=DEFAULT_BSP_DEPTH,
            min_width=self.min_room_size * MIN_SECTION_MULTIPLIER + CORRIDOR_PADDING,
            min_height=self.min_room_size * MIN_SECTION_MULTIPLIER + CORRIDOR_PADDING,
            max_horizontal_ratio=MAX_ASPECT_RATIO,
            max_vertical_ratio=MAX_ASPECT_RATIO,
        )

        # 2. 葉ノードに部屋を作成
        self._create_rooms_from_bsp(bsp, tiles)

        # 3. 部屋を接続
        self._connect_rooms_from_bsp(bsp, tiles)

        game_logger.info(f"TCOD BSP dungeon built: {len(self.rooms)} rooms")
        return self.rooms

    def _create_rooms_from_bsp(self, bsp: tcod.bsp.BSP, tiles: np.ndarray) -> None:
        """BSPツリーの葉ノードから部屋を作成。"""
        self.rooms = []
        room_id = 0

        # 葉ノードを巡回して部屋を作成
        for node in bsp.pre_order():
            if not node.children:  # 葉ノード
                room = self._create_room_in_node(node, room_id)
                if room:
                    self.rooms.append(room)
                    self._place_room_on_tiles(room, tiles)
                    # ノードにroom情報を保存（接続で使用）
                    node.room = room  # type: ignore[attr-defined]
                    room_id += 1

    def _create_room_in_node(self, node: tcod.bsp.BSP, room_id: int) -> Room | None:
        """BSPノード内に部屋を作成。"""
        # マージンを設定
        max_room_width = node.width - DEFAULT_ROOM_MARGIN * MIN_SECTION_MULTIPLIER
        max_room_height = node.height - DEFAULT_ROOM_MARGIN * MIN_SECTION_MULTIPLIER

        # 最小サイズチェック
        if max_room_width < self.min_room_size or max_room_height < self.min_room_size:
            return None

        # 部屋サイズを決定（ランダム性を持たせつつ適度なサイズに）
        room_width = random.randint(
            self.min_room_size,
            min(max_room_width, self.min_room_size + DEFAULT_ROOM_SIZE_VARIANCE),
        )
        room_height = random.randint(
            self.min_room_size,
            min(max_room_height, self.min_room_size + DEFAULT_ROOM_SIZE_VARIANCE),
        )

        # 部屋を中央寄りに配置
        room_x = node.x + (node.width - room_width) // 2
        room_y = node.y + (node.height - room_height) // 2

        # 境界チェック
        room_x = max(1, min(room_x, self.width - room_width - 1))
        room_y = max(1, min(room_y, self.height - room_height - 1))

        return Room(
            id=room_id, x=room_x, y=room_y, width=room_width, height=room_height
        )

    def _place_room_on_tiles(self, room: Room, tiles: np.ndarray) -> None:
        """部屋をタイル配列に配置。"""
        # 部屋の境界を壁に
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= x < self.width and 0 <= y < self.height:
                    tiles[y, x] = Wall()

        # 部屋内部を床に
        for y in range(room.y + 1, room.y + room.height - 1):
            for x in range(room.x + 1, room.x + room.width - 1):
                if 0 <= x < self.width and 0 <= y < self.height:
                    tiles[y, x] = Floor()

    def _connect_rooms_from_bsp(self, bsp: tcod.bsp.BSP, tiles: np.ndarray) -> None:
        """BSPツリーの構造に従って部屋を接続。"""
        # post_orderで巡回することで、葉から根へと接続を構築
        for node in bsp.post_order():
            if node.children:  # 非葉ノード
                child1, child2 = node.children

                # 各子ノードから部屋を見つけて接続
                room1 = self._find_room_in_subtree(child1)
                room2 = self._find_room_in_subtree(child2)

                if room1 and room2:
                    self._connect_two_rooms(room1, room2, tiles)

    def _find_room_in_subtree(self, node: tcod.bsp.BSP) -> Room | None:
        """BSPサブツリーから部屋を探す。"""
        # 直接部屋を持っている場合
        room = getattr(node, "room", None)
        if room:
            return room

        # 子ノードから探す
        for child_node in node.pre_order():
            child_room = getattr(child_node, "room", None)
            if child_room:
                return child_room

        return None

    def _connect_two_rooms(self, room1: Room, room2: Room, tiles: np.ndarray) -> None:
        """2つの部屋をL字型通路で接続。"""
        # 各部屋の中心座標を取得
        x1, y1 = room1.center()
        x2, y2 = room2.center()

        # L字型通路を作成（水平→垂直）
        self._carve_horizontal_tunnel(tiles, x1, x2, y1)
        self._carve_vertical_tunnel(tiles, x2, y1, y2)

        # 接続点にドアを配置
        self._place_doors_for_rooms(room1, room2, tiles, x1, y1, x2, y2)

    def _carve_horizontal_tunnel(
        self, tiles: np.ndarray, x1: int, x2: int, y: int
    ) -> None:
        """水平通路を掘る。"""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                tiles[y, x] = Floor()

    def _carve_vertical_tunnel(
        self, tiles: np.ndarray, x: int, y1: int, y2: int
    ) -> None:
        """垂直通路を掘る。"""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                tiles[y, x] = Floor()

    def _place_doors_for_rooms(
        self,
        room1: Room,
        room2: Room,
        tiles: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ) -> None:
        """部屋と通路の接続点にドアを配置。"""
        for room in [room1, room2]:
            self._place_single_door_for_room(room, tiles, x1, y1, x2, y2)

    def _place_single_door_for_room(
        self, room: Room, tiles: np.ndarray, x1: int, y1: int, x2: int, y2: int
    ) -> None:
        """単一の部屋にドアを配置。"""
        # 水平通路との接続チェック
        if self._try_place_horizontal_door(room, tiles, x1, x2, y1):
            return

        # 垂直通路との接続チェック
        self._try_place_vertical_door(room, tiles, x2, y1, y2)

    def _try_place_horizontal_door(
        self, room: Room, tiles: np.ndarray, x1: int, x2: int, y: int
    ) -> bool:
        """水平通路にドアを配置を試行。"""
        if room.y <= y <= room.y + room.height - 1:
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if self._is_room_boundary(room, x, y):
                    tiles[y, x] = Door()
                    room.add_door(x, y)
                    return True
        return False

    def _try_place_vertical_door(
        self, room: Room, tiles: np.ndarray, x: int, y1: int, y2: int
    ) -> bool:
        """垂直通路にドアを配置を試行。"""
        if room.x <= x <= room.x + room.width - 1:
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if self._is_room_boundary(room, x, y):
                    tiles[y, x] = Door()
                    room.add_door(x, y)
                    return True
        return False

    def _is_room_boundary(self, room: Room, x: int, y: int) -> bool:
        """指定座標が部屋の境界かどうかを判定。"""
        return (
            (x == room.x or x == room.x + room.width - 1)
            and room.y <= y <= room.y + room.height - 1
        ) or (
            (y == room.y or y == room.y + room.height - 1)
            and room.x <= x <= room.x + room.width - 1
        )

    def reset(self) -> None:
        """ビルダーの状態をリセット。"""
        self.rooms = []

    def get_statistics(self) -> dict:
        """
        生成統計を取得。

        Returns
        -------
        dict
            生成されたダンジョンの統計情報を含む辞書

        """
        total_doors = sum(len(room.doors) for room in self.rooms)
        avg_room_size = (
            sum(room.width * room.height for room in self.rooms) / len(self.rooms)
            if self.rooms
            else 0
        )

        return {
            "builder_type": "TCOD BSP",
            "room_count": len(self.rooms),
            "min_room_size": self.min_room_size,
            "total_doors": total_doors,
            "average_room_size": f"{avg_room_size:.1f}",
            "bsp_depth": DEFAULT_BSP_DEPTH,
        }
