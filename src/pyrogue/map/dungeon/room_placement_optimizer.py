"""
部屋配置最適化システム。

このモジュールは、BSPアルゴリズムでの部屋配置を最適化し、
より良いダンジョンレイアウトを実現するためのシステムです。
"""

from __future__ import annotations

import math
import random
from typing import Any

import tcod.bsp

from pyrogue.map.dungeon.constants import RoomConstants
from pyrogue.map.dungeon.room_builder import Room
from pyrogue.utils import game_logger


class RoomPlacementOptimizer:
    """
    部屋配置最適化クラス。

    BSPノード内での部屋配置を最適化し、
    より戦略的で興味深いダンジョンレイアウトを生成します。
    """

    def __init__(self, width: int, height: int, floor: int = 1) -> None:
        """
        部屋配置最適化を初期化。

        Args:
        ----
            width: ダンジョンの幅
            height: ダンジョンの高さ
            floor: 階層番号（配置戦略に影響）

        """
        self.width = width
        self.height = height
        self.floor = floor
        self.room_id_counter = 0

        # 階層に応じた配置戦略
        self.placement_strategy = self._determine_placement_strategy(floor)

        game_logger.debug(f"RoomPlacementOptimizer initialized for floor {floor}")

    def optimize_room_placement(self, node: tcod.bsp.BSP, room_margin: int = 2) -> Room | None:
        """
        BSPノード内での最適な部屋配置を決定。

        Args:
        ----
            node: BSPノード
            room_margin: 部屋の境界マージン

        Returns:
        -------
            最適化された部屋、またはNone

        """
        # 利用可能スペースを計算
        available_width = node.width - 2 * room_margin
        available_height = node.height - 2 * room_margin

        # 最小サイズチェック
        if available_width < RoomConstants.MIN_ROOM_WIDTH or available_height < RoomConstants.MIN_ROOM_HEIGHT:
            return None

        # 配置戦略に応じて部屋を配置
        if self.placement_strategy == "corners":
            return self._place_room_in_corner(node, available_width, available_height, room_margin)
        if self.placement_strategy == "center_bias":
            return self._place_room_center_bias(node, available_width, available_height, room_margin)
        if self.placement_strategy == "edge_bias":
            return self._place_room_edge_bias(node, available_width, available_height, room_margin)
        if self.placement_strategy == "golden_ratio":
            return self._place_room_golden_ratio(node, available_width, available_height, room_margin)
        # デフォルト：ランダム配置
        return self._place_room_random(node, available_width, available_height, room_margin)

    def _determine_placement_strategy(self, floor: int) -> str:
        """
        階層に応じた配置戦略を決定。

        Args:
        ----
            floor: 階層番号

        Returns:
        -------
            配置戦略名

        """
        if floor <= 5:
            return "center_bias"  # 浅い階層：中央寄せで安定感
        if floor <= 10:
            return "random"  # 中間階層：ランダムでバリエーション
        if floor <= 15:
            return "edge_bias"  # 深い階層：端寄せで挑戦的
        if floor <= 20:
            return "golden_ratio"  # 深層：黄金比で美しい配置
        return "corners"  # 最深部：角配置で最高難易度

    def _place_room_in_corner(
        self, node: tcod.bsp.BSP, available_width: int, available_height: int, room_margin: int
    ) -> Room | None:
        """
        角寄せ配置戦略。

        部屋を4つの角のいずれかに配置し、
        通路の戦略性を高めます。
        """
        # 部屋サイズを決定（50-80%の範囲）
        room_width = self._calculate_room_size(available_width, 0.5, 0.8)
        room_height = self._calculate_room_size(available_height, 0.5, 0.8)

        # 角位置を選択
        corners = [
            (0, 0),  # 左上
            (available_width - room_width, 0),  # 右上
            (0, available_height - room_height),  # 左下
            (available_width - room_width, available_height - room_height),  # 右下
        ]

        corner_x, corner_y = random.choice(corners)

        room_x = node.x + room_margin + corner_x
        room_y = node.y + room_margin + corner_y

        return self._create_room(room_x, room_y, room_width, room_height)

    def _place_room_center_bias(
        self, node: tcod.bsp.BSP, available_width: int, available_height: int, room_margin: int
    ) -> Room | None:
        """
        中央寄せ配置戦略。

        部屋を中央付近に配置し、
        安定したダンジョンレイアウトを作成します。
        """
        # 部屋サイズを決定（60-90%の範囲）
        room_width = self._calculate_room_size(available_width, 0.6, 0.9)
        room_height = self._calculate_room_size(available_height, 0.6, 0.9)

        # 中央付近に配置（軽微なランダム性）
        center_x = (available_width - room_width) // 2
        center_y = (available_height - room_height) // 2

        # 中央から少しずらす
        max_offset = min(available_width - room_width, available_height - room_height) // 4
        offset_x = random.randint(-max_offset, max_offset) if max_offset > 0 else 0
        offset_y = random.randint(-max_offset, max_offset) if max_offset > 0 else 0

        room_x = node.x + room_margin + max(0, min(center_x + offset_x, available_width - room_width))
        room_y = node.y + room_margin + max(0, min(center_y + offset_y, available_height - room_height))

        return self._create_room(room_x, room_y, room_width, room_height)

    def _place_room_edge_bias(
        self, node: tcod.bsp.BSP, available_width: int, available_height: int, room_margin: int
    ) -> Room | None:
        """
        端寄せ配置戦略。

        部屋を端に寄せて配置し、
        通路の複雑性を高めます。
        """
        # 部屋サイズを決定（40-70%の範囲）
        room_width = self._calculate_room_size(available_width, 0.4, 0.7)
        room_height = self._calculate_room_size(available_height, 0.4, 0.7)

        # 端に寄せる方向を選択
        edge_type = random.choice(["left", "right", "top", "bottom"])

        if edge_type == "left":
            room_x = node.x + room_margin
            room_y = node.y + room_margin + random.randint(0, available_height - room_height)
        elif edge_type == "right":
            room_x = node.x + room_margin + available_width - room_width
            room_y = node.y + room_margin + random.randint(0, available_height - room_height)
        elif edge_type == "top":
            room_x = node.x + room_margin + random.randint(0, available_width - room_width)
            room_y = node.y + room_margin
        else:  # bottom
            room_x = node.x + room_margin + random.randint(0, available_width - room_width)
            room_y = node.y + room_margin + available_height - room_height

        return self._create_room(room_x, room_y, room_width, room_height)

    def _place_room_golden_ratio(
        self, node: tcod.bsp.BSP, available_width: int, available_height: int, room_margin: int
    ) -> Room | None:
        """
        黄金比配置戦略。

        黄金比（φ ≈ 1.618）を使用して、
        美しく調和のとれた部屋配置を作成します。
        """
        phi = (1 + math.sqrt(5)) / 2  # 黄金比

        # 部屋サイズを黄金比に基づいて決定
        if available_width > available_height:
            room_height = self._calculate_room_size(available_height, 0.5, 0.8)
            room_width = min(int(room_height * phi), available_width)
        else:
            room_width = self._calculate_room_size(available_width, 0.5, 0.8)
            room_height = min(int(room_width * phi), available_height)

        # 黄金比分割点に配置
        golden_x = int(available_width / phi)
        golden_y = int(available_height / phi)

        # 配置可能範囲内にクランプ
        room_x = node.x + room_margin + min(golden_x, available_width - room_width)
        room_y = node.y + room_margin + min(golden_y, available_height - room_height)

        return self._create_room(room_x, room_y, room_width, room_height)

    def _place_room_random(
        self, node: tcod.bsp.BSP, available_width: int, available_height: int, room_margin: int
    ) -> Room | None:
        """
        ランダム配置戦略（既存の動作）。

        従来のランダム配置を維持します。
        """
        # 部屋サイズをランダムに決定
        room_width = random.randint(RoomConstants.MIN_ROOM_WIDTH, min(available_width, RoomConstants.MAX_ROOM_WIDTH))
        room_height = random.randint(
            RoomConstants.MIN_ROOM_HEIGHT, min(available_height, RoomConstants.MAX_ROOM_HEIGHT)
        )

        # 部屋の位置をランダムに決定
        max_x_offset = max(0, available_width - room_width)
        max_y_offset = max(0, available_height - room_height)

        room_x = node.x + room_margin + (random.randint(0, max_x_offset) if max_x_offset > 0 else 0)
        room_y = node.y + room_margin + (random.randint(0, max_y_offset) if max_y_offset > 0 else 0)

        return self._create_room(room_x, room_y, room_width, room_height)

    def _calculate_room_size(self, available_size: int, min_ratio: float, max_ratio: float) -> int:
        """
        利用可能サイズに対する比率で部屋サイズを計算。

        Args:
        ----
            available_size: 利用可能サイズ
            min_ratio: 最小比率
            max_ratio: 最大比率

        Returns:
        -------
            計算された部屋サイズ

        """
        min_size = max(RoomConstants.MIN_ROOM_WIDTH, int(available_size * min_ratio))
        max_size = min(available_size, int(available_size * max_ratio))

        return random.randint(min_size, max_size)

    def _create_room(self, x: int, y: int, width: int, height: int) -> Room:
        """
        部屋オブジェクトを作成。

        Args:
        ----
            x: X座標
            y: Y座標
            width: 幅
            height: 高さ

        Returns:
        -------
            作成された部屋オブジェクト

        """
        # 境界チェック
        x = max(1, min(x, self.width - width - 1))
        y = max(1, min(y, self.height - height - 1))
        width = min(width, self.width - x - 1)
        height = min(height, self.height - y - 1)

        room = Room(
            id=self.room_id_counter,
            x=x,
            y=y,
            width=width,
            height=height,
        )

        self.room_id_counter += 1

        game_logger.debug(f"Room created: {room.id} at ({x},{y}) size {width}x{height} using {self.placement_strategy}")

        return room

    def get_placement_statistics(self) -> dict[str, Any]:
        """
        配置統計情報を取得。

        Returns
        -------
            配置統計の辞書

        """
        return {
            "strategy": self.placement_strategy,
            "floor": self.floor,
            "dungeon_size": f"{self.width}x{self.height}",
            "rooms_created": self.room_id_counter,
            "strategy_description": self._get_strategy_description(),
        }

    def _get_strategy_description(self) -> str:
        """配置戦略の説明を取得。"""
        descriptions = {
            "center_bias": "中央寄せ配置 - 安定したレイアウト",
            "random": "ランダム配置 - バリエーション豊富",
            "edge_bias": "端寄せ配置 - 挑戦的なレイアウト",
            "golden_ratio": "黄金比配置 - 美しい調和",
            "corners": "角配置 - 最高難易度",
        }

        return descriptions.get(self.placement_strategy, "不明な配置戦略")
