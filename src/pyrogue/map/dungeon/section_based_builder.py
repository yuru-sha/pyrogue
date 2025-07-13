"""
RogueBasinチュートリアルに基づくTCOD BSPダンジョン生成システム。

参考: https://www.roguebasin.com/index.php/Complete_Roguelike_Tutorial,_using_Python+libtcod,_extras#BSP_Dungeon_Generator
"""

from __future__ import annotations

import random

import numpy as np
import tcod.bsp

from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Floor, Wall
from pyrogue.utils import game_logger

# RogueBasinチュートリアルに基づく定数
BSP_DEPTH = 10
BSP_MIN_SIZE = 6
FULL_ROOMS = False


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
        
        # 1. BSPツリーを作成・分割
        bsp = tcod.bsp.BSP(x=0, y=0, width=self.width, height=self.height)
        bsp.split_recursive(
            depth=BSP_DEPTH,
            min_width=BSP_MIN_SIZE + 1,
            min_height=BSP_MIN_SIZE + 1,
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
        # 部屋のサイズをランダムに決定（範囲チェック付き）
        max_width = max(BSP_MIN_SIZE, node.width - 2)
        max_height = max(BSP_MIN_SIZE, node.height - 2)
        
        room_width = random.randint(BSP_MIN_SIZE, max_width)
        room_height = random.randint(BSP_MIN_SIZE, max_height)
        
        # 部屋の位置をランダムに決定（ノード内で、範囲チェック付き）
        max_x_offset = max(0, node.width - room_width - 1)
        max_y_offset = max(0, node.height - room_height - 1)
        
        room_x = node.x + random.randint(0, max_x_offset) if max_x_offset > 0 else node.x
        room_y = node.y + random.randint(0, max_y_offset) if max_y_offset > 0 else node.y
        
        # 境界チェック
        room_x = max(1, min(room_x, self.width - room_width - 1))
        room_y = max(1, min(room_y, self.height - room_height - 1))
        
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
        """2つのノード間を接続。"""
        # 各ノードから代表的な部屋を取得
        room1 = self._get_room_from_node(node1)
        room2 = self._get_room_from_node(node2)
        
        if room1 and room2:
            # 部屋の中心点を取得
            center1_x, center1_y = room1.center()
            center2_x, center2_y = room2.center()
            
            # RogueBasinスタイルの接続（L字型通路）
            if random.random() < 0.5:
                # 水平→垂直
                self._hline(tiles, center1_x, center2_x, center1_y)
                self._vline(tiles, center2_x, center1_y, center2_y)
            else:
                # 垂直→水平
                self._vline(tiles, center1_x, center1_y, center2_y)
                self._hline(tiles, center1_x, center2_x, center2_y)

    def _get_room_from_node(self, node: tcod.bsp.BSP) -> Room | None:
        """ノードから部屋を取得（再帰的に検索）。"""
        # 直接部屋を持っている場合
        room = getattr(node, 'room', None)
        if room:
            return room
        
        # 子ノードから探す
        if node.children:
            for child in node.children:
                room = self._get_room_from_node(child)
                if room:
                    return room
        
        return None

    def _hline(self, tiles: np.ndarray, x1: int, x2: int, y: int) -> None:
        """水平線を掘る。"""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                tiles[y, x] = Floor()

    def _vline(self, tiles: np.ndarray, x: int, y1: int, y2: int) -> None:
        """垂直線を掘る。"""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                tiles[y, x] = Floor()

    def reset(self) -> None:
        """ビルダーの状態をリセット。"""
        self.rooms = []
        self.room_id_counter = 0

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
            "builder_type": "RogueBasin BSP",
            "room_count": len(self.rooms),
            "bsp_depth": BSP_DEPTH,
            "bsp_min_size": BSP_MIN_SIZE,
            "average_room_size": f"{avg_room_size:.1f}",
        }