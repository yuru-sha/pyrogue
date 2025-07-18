"""
タイルバッファリングシステム。

このモジュールは、ダンジョン生成時のタイル操作を最適化するための
バッファリングシステムを提供します。
"""

from __future__ import annotations

from typing import Any

import numpy as np

from pyrogue.map.tile import Floor, Wall
from pyrogue.utils import game_logger


class TileBuffer:
    """
    タイル操作を最適化するためのバッファリングクラス。

    大量のタイル操作を一括で実行することでパフォーマンスを向上させます。

    Attributes
    ----------
        width: バッファの幅
        height: バッファの高さ
        operations: 未実行の操作リスト
        batch_size: バッチサイズ

    """

    def __init__(self, width: int, height: int, batch_size: int = 1000) -> None:
        """
        タイルバッファを初期化。

        Args:
        ----
            width: バッファの幅
            height: バッファの高さ
            batch_size: バッチサイズ

        """
        self.width = width
        self.height = height
        self.batch_size = batch_size
        self.operations: list[tuple[int, int, Any]] = []

    def queue_tile_change(self, x: int, y: int, tile: Any) -> None:
        """
        タイル変更をキューに追加。

        Args:
        ----
            x: X座標
            y: Y座標
            tile: 新しいタイルオブジェクト

        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.operations.append((x, y, tile))

            # バッチサイズに達したら自動実行
            if len(self.operations) >= self.batch_size:
                self._flush_partial()

    def queue_room_floor(self, room_x: int, room_y: int, room_width: int, room_height: int) -> None:
        """
        部屋の床タイルをバッチで追加。

        Args:
        ----
            room_x: 部屋のX座標
            room_y: 部屋のY座標
            room_width: 部屋の幅
            room_height: 部屋の高さ

        """
        floor_tile = Floor()
        for y in range(room_y + 1, room_y + room_height - 1):
            for x in range(room_x + 1, room_x + room_width - 1):
                self.queue_tile_change(x, y, floor_tile)

    def queue_corridor_tiles(self, points: list[tuple[int, int]]) -> None:
        """
        通路タイルをバッチで追加。

        Args:
        ----
            points: 通路の座標リスト

        """
        floor_tile = Floor()
        for x, y in points:
            self.queue_tile_change(x, y, floor_tile)

    def flush_to_tiles(self, tiles: np.ndarray) -> int:
        """
        キューに溜まった操作をタイル配列に適用。

        Args:
        ----
            tiles: タイル配列

        Returns:
        -------
            適用された操作数

        """
        operations_count = len(self.operations)

        if operations_count == 0:
            return 0

        # 座標による並び替えでキャッシュ効率を向上
        self.operations.sort(key=lambda op: (op[1], op[0]))  # y, x順

        # 一括適用
        for x, y, tile in self.operations:
            tiles[y, x] = tile

        self.operations.clear()

        game_logger.debug(f"Applied {operations_count} tile operations")
        return operations_count

    def _flush_partial(self) -> None:
        """
        部分的なフラッシュ（内部使用）。

        Note:
        ----
            この方法は現在の実装では使用されませんが、
            将来の拡張で使用される可能性があります。

        """
        # 現在の実装では何もしない
        # 将来、部分的なフラッシュが必要になった場合に実装

    def get_queue_size(self) -> int:
        """
        キューのサイズを取得。

        Returns
        -------
            キューに溜まった操作数

        """
        return len(self.operations)

    def clear_queue(self) -> None:
        """キューをクリア。"""
        self.operations.clear()

    def get_statistics(self) -> dict[str, Any]:
        """
        バッファの統計情報を取得。

        Returns
        -------
            統計情報の辞書

        """
        return {
            "buffer_size": f"{self.width}x{self.height}",
            "batch_size": self.batch_size,
            "queue_size": len(self.operations),
            "memory_usage_mb": len(self.operations) * 32 / 1024 / 1024,  # 概算
        }


class OptimizedTileManager:
    """
    最適化されたタイル管理クラス。

    TileBufferを使用してパフォーマンスを向上させます。

    """

    def __init__(self, width: int, height: int) -> None:
        """
        最適化されたタイル管理を初期化。

        Args:
        ----
            width: 幅
            height: 高さ

        """
        self.width = width
        self.height = height
        self.buffer = TileBuffer(width, height)

    def initialize_tiles(self) -> np.ndarray:
        """
        タイル配列を初期化。

        Returns
        -------
            初期化されたタイル配列

        """
        return np.full((self.height, self.width), Wall(), dtype=object)

    def batch_create_rooms(self, rooms: list[Any], tiles: np.ndarray) -> None:
        """
        部屋を一括作成。

        Args:
        ----
            rooms: 部屋のリスト
            tiles: タイル配列

        """
        # 全部屋の床タイルをバッファに追加
        for room in rooms:
            self.buffer.queue_room_floor(room.x, room.y, room.width, room.height)

        # 一括適用
        self.buffer.flush_to_tiles(tiles)

    def batch_create_corridors(self, corridors: list[Any], tiles: np.ndarray) -> None:
        """
        通路を一括作成。

        Args:
        ----
            corridors: 通路のリスト
            tiles: タイル配列

        """
        # 全通路の座標をバッファに追加
        for corridor in corridors:
            if hasattr(corridor, "points"):
                self.buffer.queue_corridor_tiles(corridor.points)

        # 一括適用
        self.buffer.flush_to_tiles(tiles)

    def get_buffer_statistics(self) -> dict[str, Any]:
        """
        バッファの統計情報を取得。

        Returns
        -------
            統計情報

        """
        return self.buffer.get_statistics()
