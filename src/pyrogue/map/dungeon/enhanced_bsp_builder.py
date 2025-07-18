"""
拡張BSPダンジョン生成システム。

既存のBSPビルダーを拡張し、新しい部屋配置最適化、
高度廊下生成、デッドエンド管理システムを統合します。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import numpy as np
import tcod.bsp

from pyrogue.map.dungeon.advanced_corridor_generator import AdvancedCorridorGenerator
from pyrogue.map.dungeon.constants import BSPConstants, DoorConstants
from pyrogue.map.dungeon.deadend_manager import DeadEndManager
from pyrogue.map.dungeon.line_drawer import LineDrawer
from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.dungeon.room_placement_optimizer import RoomPlacementOptimizer
from pyrogue.map.tile import Door, Floor, SecretDoor
from pyrogue.utils import game_logger

if TYPE_CHECKING:
    import numpy as np


class EnhancedBSPBuilder:
    """
    拡張BSPダンジョン生成ビルダー。

    既存のBSPアルゴリズムを拡張し、
    高度な部屋配置、廊下生成、デッドエンド管理を統合します。
    """

    def __init__(self, width: int, height: int, floor: int = 1, min_section_size: int = 6) -> None:
        """
        拡張BSPダンジョンビルダーを初期化。

        Args:
        ----
            width: ダンジョンの幅
            height: ダンジョンの高さ
            floor: 階層番号（拡張機能に影響）
            min_section_size: 最小セクションサイズ（使用されない、互換性のため）

        """
        self.width = width
        self.height = height
        self.floor = floor
        self.rooms: list[Room] = []
        self.room_id_counter = 0
        self.door_positions: set[tuple[int, int]] = set()

        # BSP設定
        self._depth = BSPConstants.DEPTH
        self._min_size = BSPConstants.MIN_SIZE
        self._full_rooms = BSPConstants.FULL_ROOMS

        # 拡張システムを初期化
        self.room_optimizer = RoomPlacementOptimizer(width, height, floor)
        self.corridor_generator = AdvancedCorridorGenerator(width, height, floor)
        self.deadend_manager = DeadEndManager(width, height, floor)

        # 線描画器を初期化
        self.line_drawer = LineDrawer(self._place_corridor_tile)

        # 拡張機能の有効/無効フラグ
        self.enable_room_optimization = True
        self.enable_advanced_corridors = True
        self.enable_deadend_placement = True

        game_logger.info(f"EnhancedBSPBuilder initialized for floor {floor}: {width}x{height}")

    def build_dungeon(self, tiles: np.ndarray) -> list[Room]:
        """
        拡張BSPダンジョンを生成。

        Args:
        ----
            tiles: タイル配列

        Returns:
        -------
            生成された部屋のリスト

        """
        self.rooms = []
        self.room_id_counter = 0
        self.door_positions = set()

        # 1. BSPツリーを作成・分割
        bsp = tcod.bsp.BSP(x=0, y=0, width=self.width, height=self.height)
        bsp.split_recursive(
            depth=self._depth,
            min_width=self._min_size + 4,
            min_height=self._min_size + 4,
            max_horizontal_ratio=1.5,
            max_vertical_ratio=1.5,
        )

        # 2. 拡張されたノード巡回処理
        self._traverse_node_enhanced(bsp, tiles)

        # 3. デッドエンド配置（有効な場合）
        if self.enable_deadend_placement:
            self._place_deadends(tiles)

        game_logger.info(f"Enhanced BSP dungeon built: {len(self.rooms)} rooms")
        return self.rooms

    def _traverse_node_enhanced(self, node: tcod.bsp.BSP, tiles: np.ndarray) -> None:
        """
        拡張されたノード巡回処理。

        従来のtraverse_nodeに拡張機能を統合します。
        """
        if not node.children:
            # 葉ノード: 最適化された部屋を作成
            self._create_room_enhanced(node, tiles)
        else:
            # 非葉ノード: 子ノードを再帰処理してから接続
            child1, child2 = node.children

            # 子ノードを再帰的に処理
            self._traverse_node_enhanced(child1, tiles)
            self._traverse_node_enhanced(child2, tiles)

            # 高度な廊下で子ノード間を接続
            self._connect_nodes_enhanced(child1, child2, tiles)

    def _create_room_enhanced(self, node: tcod.bsp.BSP, tiles: np.ndarray) -> None:
        """
        拡張された部屋作成処理。

        部屋配置最適化を使用して、より戦略的な部屋を作成します。
        """
        room_margin = 2

        if self.enable_room_optimization:
            # 最適化された部屋配置を使用
            room = self.room_optimizer.optimize_room_placement(node, room_margin)
        else:
            # 従来の部屋配置を使用
            room = self._create_room_traditional(node, room_margin)

        if room:
            # 部屋IDを更新
            room.id = self.room_id_counter
            self.room_id_counter += 1

            self.rooms.append(room)

            # タイルに部屋を配置
            self._dig_room(room, tiles)

            # ノードに部屋情報を保存
            node.room = room  # type: ignore[attr-defined]

            game_logger.debug(
                f"Enhanced room created: {room.id} at ({room.x},{room.y}) size {room.width}x{room.height}"
            )

    def _create_room_traditional(self, node: tcod.bsp.BSP, room_margin: int) -> Room | None:
        """
        従来の部屋作成処理（フォールバック用）。
        """
        available_width = node.width - 2 * room_margin
        available_height = node.height - 2 * room_margin

        if available_width < self._min_size or available_height < self._min_size:
            return None

        if self._full_rooms:
            room_x = node.x + room_margin
            room_y = node.y + room_margin
            room_width = available_width
            room_height = available_height
        else:
            max_width = max(self._min_size, available_width)
            max_height = max(self._min_size, available_height)

            room_width = random.randint(self._min_size, max_width)
            room_height = random.randint(self._min_size, max_height)

            max_x_offset = max(0, available_width - room_width)
            max_y_offset = max(0, available_height - room_height)

            room_x = node.x + room_margin + (random.randint(0, max_x_offset) if max_x_offset > 0 else 0)
            room_y = node.y + room_margin + (random.randint(0, max_y_offset) if max_y_offset > 0 else 0)

        # 境界チェック
        room_x = max(1, min(room_x, self.width - room_width - 1))
        room_y = max(1, min(room_y, self.height - room_height - 1))
        room_width = min(room_width, self.width - room_x - 1)
        room_height = min(room_height, self.height - room_y - 1)

        if room_width < self._min_size or room_height < self._min_size:
            return None

        return Room(
            id=self.room_id_counter,
            x=room_x,
            y=room_y,
            width=room_width,
            height=room_height,
        )

    def _dig_room(self, room: Room, tiles: np.ndarray) -> None:
        """部屋をタイル配列に掘る。"""
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= x < self.width and 0 <= y < self.height:
                    tiles[y, x] = Floor()

    def _connect_nodes_enhanced(self, node1: tcod.bsp.BSP, node2: tcod.bsp.BSP, tiles: np.ndarray) -> None:
        """
        拡張されたノード接続処理。

        高度な廊下生成を使用して、より興味深い通路を作成します。
        """
        # 各ノードから代表的な部屋を取得
        room1 = self._get_room_from_node(node1)
        room2 = self._get_room_from_node(node2)

        if room1 and room2:
            if self.enable_advanced_corridors:
                # 高度廊下生成を使用
                self.corridor_generator.generate_advanced_corridor(
                    room1, room2, tiles, self._place_corridor_tile, self._place_boundary_door_tile
                )
            else:
                # 従来のL字型廊下を使用
                self._connect_nodes_traditional(room1, room2, tiles)
        else:
            game_logger.warning("No rooms found in nodes for connection")

    def _connect_nodes_traditional(self, room1: Room, room2: Room, tiles: np.ndarray) -> None:
        """従来のL字型廊下接続（フォールバック用）。"""
        center1, center2 = self._get_room_centers(room1, room2)

        # L字型通路で中心同士を接続
        horizontal_first = random.random() < 0.5
        self.line_drawer.draw_connection_line(
            tiles,
            center1[0],
            center1[1],
            center2[0],
            center2[1],
            horizontal_first=horizontal_first,
            boundary_door_placer=self._place_boundary_door_tile,
        )

    def _place_deadends(self, tiles: np.ndarray) -> None:
        """デッドエンドを配置。"""
        if self.rooms:
            # numpy配列をリストに変換（デッドエンドマネージャーとの互換性）
            tiles_list = tiles.tolist()

            # デッドエンドを配置
            deadend_points = self.deadend_manager.place_strategic_deadends(
                self.rooms, tiles_list, self._place_corridor_tile
            )

            # 変更をnumpy配列に反映
            for i, row in enumerate(tiles_list):
                for j, tile in enumerate(row):
                    tiles[i, j] = tile

            game_logger.info(f"Placed {len(deadend_points)} deadend points")

    def _get_room_from_node(self, node: tcod.bsp.BSP) -> Room | None:
        """ノードから部屋を取得（再帰的に検索）。"""
        room = getattr(node, "room", None)
        if room:
            return room

        if node.children:
            for child in node.children:
                room = self._get_room_from_node(child)
                if room:
                    return room

        return None

    def _get_room_centers(self, room1: Room, room2: Room) -> tuple[tuple[int, int], tuple[int, int]]:
        """2つの部屋の中心座標を取得。"""
        center1_x, center1_y = room1.center()
        center2_x, center2_y = room2.center()
        return ((center1_x, center1_y), (center2_x, center2_y))

    def _place_corridor_tile(self, tiles: np.ndarray, x: int, y: int, allow_door: bool = True) -> None:
        """通路タイルを配置（壁を貫通する際にドア設置）。"""
        from pyrogue.map.tile import Wall

        if 0 <= x < self.width and 0 <= y < self.height:
            current_tile = tiles[y, x]
            is_wall = isinstance(current_tile, Wall)
            position = (x, y)

            if is_wall and allow_door and position not in self.door_positions:
                if self._is_room_boundary_wall(x, y) and not self._has_adjacent_door(x, y):
                    door = self._create_random_door()
                    tiles[y, x] = door
                    self.door_positions.add(position)
                    game_logger.debug(f"Door placed at ({x},{y}), type: {type(door).__name__}")
                else:
                    tiles[y, x] = Floor()
            else:
                tiles[y, x] = Floor()

    def _place_boundary_door_tile(self, tiles: np.ndarray, x: int, y: int, allow_door: bool = True) -> None:
        """境界位置でのドア配置（より積極的にドアを設置）。"""
        from pyrogue.map.tile import Wall

        if 0 <= x < self.width and 0 <= y < self.height:
            current_tile = tiles[y, x]
            is_wall = isinstance(current_tile, Wall)
            position = (x, y)

            if is_wall and allow_door and position not in self.door_positions:
                if self._is_room_boundary_wall(x, y) and not self._has_adjacent_door(x, y):
                    door = self._create_random_door()
                    tiles[y, x] = door
                    self.door_positions.add(position)
                    game_logger.debug(f"Boundary door placed at ({x},{y}), type: {type(door).__name__}")
                else:
                    tiles[y, x] = Floor()
            else:
                tiles[y, x] = Floor()

    def _create_random_door(self) -> Door | SecretDoor:
        """ランダムな状態のドアを作成。"""
        rand = random.random()
        if rand < DoorConstants.SECRET_DOOR_CHANCE:
            return SecretDoor()
        if rand < DoorConstants.SECRET_DOOR_CHANCE + DoorConstants.OPEN_DOOR_CHANCE:
            return Door(state="open")
        return Door(state="closed")

    def _is_room_boundary_wall(self, x: int, y: int) -> bool:
        """指定された壁が部屋の境界（外周）かどうかを判定。"""
        for room in self.rooms:
            left, right = room.x, room.x + room.width - 1
            top, bottom = room.y, room.y + room.height - 1

            if (y == top - 1 or y == bottom + 1) and (left <= x <= right):
                return True
            if (x == left - 1 or x == right + 1) and (top <= y <= bottom):
                return True

        return False

    def _has_adjacent_door(self, x: int, y: int) -> bool:
        """指定された位置の隣接8方向にドアがあるかどうかをチェック。"""
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue

                adj_x, adj_y = x + dx, y + dy

                if not (0 <= adj_x < self.width and 0 <= adj_y < self.height):
                    continue

                if (adj_x, adj_y) in self.door_positions:
                    return True

        return False

    def set_enhancement_flags(
        self, room_optimization: bool = True, advanced_corridors: bool = True, deadend_placement: bool = True
    ) -> None:
        """
        拡張機能の有効/無効を設定。

        Args:
        ----
            room_optimization: 部屋配置最適化の有効/無効
            advanced_corridors: 高度廊下生成の有効/無効
            deadend_placement: デッドエンド配置の有効/無効

        """
        self.enable_room_optimization = room_optimization
        self.enable_advanced_corridors = advanced_corridors
        self.enable_deadend_placement = deadend_placement

        game_logger.info(
            f"Enhancement flags set: room_opt={room_optimization}, "
            f"advanced_corr={advanced_corridors}, deadends={deadend_placement}"
        )

    def get_statistics(self) -> dict:
        """
        拡張生成統計を取得。

        Returns
        -------
            生成されたダンジョンの統計情報を含む辞書

        """
        avg_room_size = sum(room.width * room.height for room in self.rooms) / len(self.rooms) if self.rooms else 0

        base_stats = {
            "builder_type": "Enhanced BSP Builder",
            "room_count": len(self.rooms),
            "floor": self.floor,
            "bsp_depth": self._depth,
            "bsp_min_size": self._min_size,
            "average_room_size": f"{avg_room_size:.1f}",
            "enhancements": {
                "room_optimization": self.enable_room_optimization,
                "advanced_corridors": self.enable_advanced_corridors,
                "deadend_placement": self.enable_deadend_placement,
            },
        }

        # 各拡張システムの統計を追加
        if hasattr(self, "room_optimizer"):
            base_stats["room_placement"] = self.room_optimizer.get_placement_statistics()

        if hasattr(self, "corridor_generator"):
            base_stats["corridor_generation"] = self.corridor_generator.get_generation_statistics()

        if hasattr(self, "deadend_manager"):
            base_stats["deadend_placement"] = self.deadend_manager.get_deadend_statistics()

        return base_stats

    def reset(self) -> None:
        """ビルダーの状態をリセット。"""
        self.rooms = []
        self.room_id_counter = 0
        self.door_positions = set()

        # 拡張システムのリセット
        if hasattr(self, "room_optimizer"):
            self.room_optimizer.room_id_counter = 0

        if hasattr(self, "corridor_generator"):
            self.corridor_generator.corridors_created = 0

        if hasattr(self, "deadend_manager"):
            self.deadend_manager.deadends_created = 0
            self.deadend_manager.deadend_locations = []
            self.deadend_manager.deadend_types = []
