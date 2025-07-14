"""
RogueBasinチュートリアルに基づくTCOD BSPダンジョン生成システム。

参考: https://www.roguebasin.com/index.php/Complete_Roguelike_Tutorial,_using_Python+libtcod,_extras#BSP_Dungeon_Generator
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import tcod.bsp

from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Door, Floor, SecretDoor
from pyrogue.utils import game_logger

if TYPE_CHECKING:
    import numpy as np

# RogueBasinチュートリアルに基づく定数
BSP_DEPTH = 10
BSP_MIN_SIZE = 5  # 参考リンクに合わせて5に変更
FULL_ROOMS = False  # False: ランダムサイズ部屋, True: ノード全体を部屋に


class BSPDungeonBuilder:
    """
    RogueBasinチュートリアルに基づくBSPダンジョン生成ビルダー。
    
    シンプルなtraverse_node()アプローチを使用して、
    確実に接続されたダンジョンを生成する。
    """

    def __init__(self, width: int, height: int, min_section_size: int = 6) -> None:
        """
        BSPダンジョンビルダーを初期化。

        Args:
        ----
            width: ダンジョンの幅
            height: ダンジョンの高さ
            min_section_size: 最小セクションサイズ（使用されない、互換性のため）

        """
        self.width = width
        self.height = height
        self.rooms: list[Room] = []
        self.room_id_counter = 0
        self.door_positions: set[tuple[int, int]] = set()  # ドア配置済み位置を記録

        # カスタマイズ可能なパラメータ
        self._depth = BSP_DEPTH
        self._min_size = BSP_MIN_SIZE
        self._full_rooms = FULL_ROOMS

        game_logger.info(
            f"RogueBasin BSP DungeonBuilder initialized: {width}x{height}"
        )

    def build_dungeon(self, tiles: np.ndarray) -> list[Room]:
        """
        RogueBasinスタイルのBSPダンジョンを生成。

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
            min_width=self._min_size + 1,
            min_height=self._min_size + 1,
            max_horizontal_ratio=1.5,
            max_vertical_ratio=1.5,
        )

        # 2. traverse_node()でダンジョンを構築
        self._traverse_node(bsp, tiles)

        game_logger.info(f"RogueBasin BSP dungeon built: {len(self.rooms)} rooms")
        return self.rooms

    def _traverse_node(self, node: tcod.bsp.BSP, tiles: np.ndarray) -> None:
        """
        RogueBasinスタイルのノード巡回処理。
        
        葉ノードでは部屋を作成し、非葉ノードでは子を接続する。
        """
        if not node.children:
            # 葉ノード: 部屋を作成
            self._create_room(node, tiles)
        else:
            # 非葉ノード: 子ノードを再帰処理してから接続
            child1, child2 = node.children

            # 子ノードを再帰的に処理
            self._traverse_node(child1, tiles)
            self._traverse_node(child2, tiles)

            # 子ノード間を接続
            self._connect_nodes(child1, child2, tiles)

    def _create_room(self, node: tcod.bsp.BSP, tiles: np.ndarray) -> None:
        """葉ノードに部屋を作成。"""
        if self._full_rooms:
            # ノード全体を部屋にする
            room_x = node.x + 1
            room_y = node.y + 1
            room_width = node.width - 2
            room_height = node.height - 2
        else:
            # 部屋のサイズをランダムに決定（範囲チェック付き）
            max_width = max(self._min_size, node.width - 2)
            max_height = max(self._min_size, node.height - 2)

            room_width = random.randint(self._min_size, max_width)
            room_height = random.randint(self._min_size, max_height)

            # 部屋の位置をランダムに決定（ノード内で、範囲チェック付き）
            max_x_offset = max(0, node.width - room_width - 1)
            max_y_offset = max(0, node.height - room_height - 1)

            room_x = node.x + random.randint(0, max_x_offset) if max_x_offset > 0 else node.x
            room_y = node.y + random.randint(0, max_y_offset) if max_y_offset > 0 else node.y

        # 境界チェック
        room_x = max(1, min(room_x, self.width - room_width - 1))
        room_y = max(1, min(room_y, self.height - room_height - 1))
        room_width = min(room_width, self.width - room_x - 1)
        room_height = min(room_height, self.height - room_y - 1)

        # 最小サイズチェック
        if room_width < self._min_size or room_height < self._min_size:
            return

        # 部屋を作成
        room = Room(
            id=self.room_id_counter,
            x=room_x,
            y=room_y,
            width=room_width,
            height=room_height
        )
        self.rooms.append(room)
        self.room_id_counter += 1

        # タイルに部屋を配置
        self._dig_room(room, tiles)

        # ノードに部屋情報を保存
        node.room = room  # type: ignore[attr-defined]

    def _dig_room(self, room: Room, tiles: np.ndarray) -> None:
        """部屋をタイル配列に掘る。"""
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= x < self.width and 0 <= y < self.height:
                    tiles[y, x] = Floor()

    def _connect_nodes(self, node1: tcod.bsp.BSP, node2: tcod.bsp.BSP, tiles: np.ndarray) -> None:
        """2つのノード間を接続（参考リンク準拠の多様なパターン）。"""
        # 各ノードから代表的な部屋を取得
        room1 = self._get_room_from_node(node1)
        room2 = self._get_room_from_node(node2)

        game_logger.debug(f"Connecting nodes: room1={room1.id if room1 else None}, room2={room2.id if room2 else None}")

        if room1 and room2:
            # 部屋の中心から中心へ接続
            center1, center2 = self._get_room_centers(room1, room2)
            game_logger.debug(f"Connecting centers: {center1} -> {center2}")

            # L字型通路で中心同士を接続
            if random.random() < 0.5:
                # 水平→垂直
                self._hline_with_connection_door(tiles, center1[0], center2[0], center1[1])
                self._vline_with_connection_door(tiles, center2[0], center1[1], center2[1])
            else:
                # 垂直→水平
                self._vline_with_connection_door(tiles, center1[0], center1[1], center2[1])
                self._hline_with_connection_door(tiles, center1[0], center2[0], center2[1])
        else:
            game_logger.warning("No rooms found in nodes for connection")

    def _get_room_from_node(self, node: tcod.bsp.BSP) -> Room | None:
        """ノードから部屋を取得（再帰的に検索）。"""
        # 直接部屋を持っている場合
        room = getattr(node, "room", None)
        if room:
            return room

        # 子ノードから探す
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


    def _is_wall_adjacent_to_room(self, x: int, y: int) -> bool:
        """指定された壁が部屋に隣接しているかどうかを判定。"""
        # 隣接する4方向をチェック
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for dx, dy in directions:
            adj_x, adj_y = x + dx, y + dy

            # 境界チェック
            if not (0 <= adj_x < self.width and 0 <= adj_y < self.height):
                continue

            # 隣接位置が部屋の床（境界含む）かチェック
            if self._is_room_floor(adj_x, adj_y):
                return True

        return False

    def _place_corridor_tile(self, tiles: np.ndarray, x: int, y: int, allow_door: bool = True) -> None:
        """通路タイルを配置（壁を貫通する際にドア設置）。"""
        from pyrogue.map.tile import Wall

        if 0 <= x < self.width and 0 <= y < self.height:
            current_tile = tiles[y, x]
            is_wall = isinstance(current_tile, Wall)
            position = (x, y)

            # 壁を貫通する際の処理
            if is_wall and allow_door and position not in self.door_positions:
                # 部屋の境界（外周）を突き抜ける箇所のみでドア配置 & 隣接ドアがないかチェック
                if self._is_room_boundary_wall(x, y) and not self._has_adjacent_door(x, y):
                    # 壁をランダムな状態のドアで置き換え
                    door = self._create_random_door()
                    tiles[y, x] = door
                    self.door_positions.add(position)
                    game_logger.debug(f"Door placed at ({x},{y}) - room boundary penetration, type: {type(door).__name__}")
                else:
                    # 通常の壁を通路で置き換え
                    tiles[y, x] = Floor()
            else:
                # 壁以外（床など）を通路で置き換え
                tiles[y, x] = Floor()

    def _create_random_door(self) -> Door | SecretDoor:
        """ランダムな状態のドアを作成（60%閉鎖、30%開放、10%隠し扉）。"""
        rand = random.random()
        if rand < 0.10:  # 10% 隠し扉
            return SecretDoor()
        if rand < 0.40:  # 30% オープンドア (0.10-0.40)
            return Door(state="open")
        # 60% クローズドドア (0.40-1.00)
        return Door(state="closed")

    def _place_boundary_door_tile(self, tiles: np.ndarray, x: int, y: int, allow_door: bool = True) -> None:
        """境界位置でのドア配置（より積極的にドアを設置）。"""
        from pyrogue.map.tile import Wall

        if 0 <= x < self.width and 0 <= y < self.height:
            current_tile = tiles[y, x]
            is_wall = isinstance(current_tile, Wall)
            position = (x, y)

            # 壁を貫通する際の処理
            if is_wall and allow_door and position not in self.door_positions:
                # 部屋の境界（外周）を突き抜ける箇所のみでドア配置 & 隣接ドアがないかチェック
                if self._is_room_boundary_wall(x, y) and not self._has_adjacent_door(x, y):
                    # 壁をランダムな状態のドアで置き換え
                    door = self._create_random_door()
                    tiles[y, x] = door
                    self.door_positions.add(position)
                    game_logger.debug(f"Boundary door placed at ({x},{y}) - room boundary penetration, type: {type(door).__name__}")
                else:
                    # 通常の壁を通路で置き換え
                    tiles[y, x] = Floor()
            else:
                # 壁以外（床など）を通路で置き換え
                tiles[y, x] = Floor()

    def _is_wall_near_room(self, x: int, y: int) -> bool:
        """指定された壁が部屋の近く（2タイル以内）にあるかどうかを判定。"""
        # 隣接する8方向（対角線含む）を広範囲でチェック
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx == 0 and dy == 0:
                    continue

                adj_x, adj_y = x + dx, y + dy

                # 境界チェック
                if not (0 <= adj_x < self.width and 0 <= adj_y < self.height):
                    continue

                # 近傍に部屋の床があるかチェック
                if self._is_room_floor(adj_x, adj_y):
                    return True

        return False

    def _is_room_boundary_wall(self, x: int, y: int) -> bool:
        """指定された壁が部屋の境界（外周）かどうかを判定。"""
        for room in self.rooms:
            # 部屋の境界座標
            left, right = room.x, room.x + room.width - 1
            top, bottom = room.y, room.y + room.height - 1
            
            # 部屋の外周の壁かチェック
            # 上下の境界壁
            if (y == top - 1 or y == bottom + 1) and (left <= x <= right):
                return True
            # 左右の境界壁  
            if (x == left - 1 or x == right + 1) and (top <= y <= bottom):
                return True
                
        return False

    def _has_adjacent_door(self, x: int, y: int) -> bool:
        """指定された位置の隣接8方向にドアがあるかどうかをチェック。"""
        from pyrogue.map.tile import Door, SecretDoor
        
        # 隣接8方向をチェック
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                    
                adj_x, adj_y = x + dx, y + dy
                
                # 境界チェック
                if not (0 <= adj_x < self.width and 0 <= adj_y < self.height):
                    continue
                    
                # 既にドアが配置済みの位置かチェック
                if (adj_x, adj_y) in self.door_positions:
                    return True
        
        return False

    def _is_inside_room(self, x: int, y: int) -> bool:
        """指定された座標が部屋の内部にあるかどうかを判定。"""
        for room in self.rooms:
            # 部屋の内部（境界を除く）かどうかをチェック
            if (room.x < x < room.x + room.width - 1 and
                room.y < y < room.y + room.height - 1):
                return True
        return False

    def _is_room_floor(self, x: int, y: int) -> bool:
        """指定された座標が部屋の床（境界含む）かどうかを判定。"""
        for room in self.rooms:
            # 部屋の範囲内（境界含む）かどうかをチェック
            if (room.x <= x <= room.x + room.width - 1 and
                room.y <= y <= room.y + room.height - 1):
                return True
        return False

    def _hline_with_connection_door(self, tiles: np.ndarray, x1: int, x2: int, y: int) -> None:
        """水平線を掘る（境界含む複数ドア配置可能）。"""
        x_start, x_end = min(x1, x2), max(x1, x2)
        for i, x in enumerate(range(x_start, x_end + 1)):
            # 最初と最後の位置では特に積極的にドア配置
            is_boundary = (i == 0) or (x == x_end)
            allow_door = True

            # 境界位置では部屋隣接チェックを緩和
            if is_boundary:
                self._place_boundary_door_tile(tiles, x, y, allow_door)
            else:
                self._place_corridor_tile(tiles, x, y, allow_door)

    def _vline_with_connection_door(self, tiles: np.ndarray, x: int, y1: int, y2: int) -> None:
        """垂直線を掘る（境界含む複数ドア配置可能）。"""
        y_start, y_end = min(y1, y2), max(y1, y2)
        for i, y in enumerate(range(y_start, y_end + 1)):
            # 最初と最後の位置では特に積極的にドア配置
            is_boundary = (i == 0) or (y == y_end)
            allow_door = True

            # 境界位置では部屋隣接チェックを緩和
            if is_boundary:
                self._place_boundary_door_tile(tiles, x, y, allow_door)
            else:
                self._place_corridor_tile(tiles, x, y, allow_door)

    def _hline(self, tiles: np.ndarray, x1: int, x2: int, y: int) -> None:
        """水平線を掘る（境界含む複数ドア配置可能）。"""
        x_start, x_end = min(x1, x2), max(x1, x2)
        for i, x in enumerate(range(x_start, x_end + 1)):
            # 最初と最後の位置では特に積極的にドア配置
            is_boundary = (i == 0) or (x == x_end)
            allow_door = True

            # 境界位置では部屋隣接チェックを緩和
            if is_boundary:
                self._place_boundary_door_tile(tiles, x, y, allow_door)
            else:
                self._place_corridor_tile(tiles, x, y, allow_door)

    def _hline_left(self, tiles: np.ndarray, x1: int, x2: int, y: int) -> None:
        """水平線を掘る（境界含む複数ドア配置可能）。"""
        x_start, x_end = min(x1, x2), max(x1, x2)
        x_values = list(range(x_end, x_start - 1, -1))
        for i, x in enumerate(x_values):
            # 最初と最後の位置では特に積極的にドア配置
            is_boundary = (i == 0) or (i == len(x_values) - 1)
            allow_door = True

            # 境界位置では部屋隣接チェックを緩和
            if is_boundary:
                self._place_boundary_door_tile(tiles, x, y, allow_door)
            else:
                self._place_corridor_tile(tiles, x, y, allow_door)

    def _vline(self, tiles: np.ndarray, x: int, y1: int, y2: int) -> None:
        """垂直線を掘る（境界含む複数ドア配置可能）。"""
        y_start, y_end = min(y1, y2), max(y1, y2)
        for i, y in enumerate(range(y_start, y_end + 1)):
            # 最初と最後の位置では特に積極的にドア配置
            is_boundary = (i == 0) or (y == y_end)
            allow_door = True

            # 境界位置では部屋隣接チェックを緩和
            if is_boundary:
                self._place_boundary_door_tile(tiles, x, y, allow_door)
            else:
                self._place_corridor_tile(tiles, x, y, allow_door)

    def _vline_up(self, tiles: np.ndarray, x: int, y1: int, y2: int) -> None:
        """垂直線を掘る（境界含む複数ドア配置可能）。"""
        y_start, y_end = min(y1, y2), max(y1, y2)
        y_values = list(range(y_end, y_start - 1, -1))
        for i, y in enumerate(y_values):
            # 最初と最後の位置では特に積極的にドア配置
            is_boundary = (i == 0) or (i == len(y_values) - 1)
            allow_door = True

            # 境界位置では部屋隣接チェックを緩和
            if is_boundary:
                self._place_boundary_door_tile(tiles, x, y, allow_door)
            else:
                self._place_corridor_tile(tiles, x, y, allow_door)

    def reset(self) -> None:
        """ビルダーの状態をリセット。"""
        self.rooms = []
        self.room_id_counter = 0
        self.door_positions = set()

    def make_bsp(self, tiles: np.ndarray, depth: int | None = None,
                 min_size: int | None = None, full_rooms: bool | None = None) -> list[Room]:
        """
        参考リンク準拠のmake_bsp関数インターフェース。

        Args:
        ----
            tiles: タイル配列
            depth: BSP分割の深度（Noneの場合はデフォルト値使用）
            min_size: 最小部屋サイズ（Noneの場合はデフォルト値使用）
            full_rooms: 全体部屋フラグ（Noneの場合はデフォルト値使用）

        Returns:
        -------
            生成された部屋のリスト

        """
        # 現在のパラメータを保存
        original_depth = self._depth
        original_min_size = self._min_size
        original_full_rooms = self._full_rooms

        # カスタムパラメータを適用
        if depth is not None:
            self._depth = depth
        if min_size is not None:
            self._min_size = min_size
        if full_rooms is not None:
            self._full_rooms = full_rooms

        try:
            # 通常の生成プロセスを実行
            rooms = self.build_dungeon(tiles)
            game_logger.info(f"make_bsp completed: {len(rooms)} rooms generated")
            return rooms
        finally:
            # パラメータを復元
            self._depth = original_depth
            self._min_size = original_min_size
            self._full_rooms = original_full_rooms

    def get_statistics(self) -> dict:
        """
        生成統計を取得。

        Returns
        -------
        dict
            生成されたダンジョンの統計情報を含む辞書

        """
        avg_room_size = (
            sum(room.width * room.height for room in self.rooms) / len(self.rooms)
            if self.rooms
            else 0
        )

        return {
            "builder_type": "RogueBasin BSP (Enhanced)",
            "room_count": len(self.rooms),
            "bsp_depth": self._depth,
            "bsp_min_size": self._min_size,
            "full_rooms_mode": self._full_rooms,
            "average_room_size": f"{avg_room_size:.1f}",
            "corridor_patterns": "4種類（標準・左向き・上向き・組み合わせ）",
        }

