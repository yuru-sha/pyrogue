"""
線描画ユーティリティ - 通路・線描画処理を統合。

このモジュールは、ダンジョン生成における線描画処理を統合し、
重複コードを除去するためのユーティリティクラスです。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


class LineDrawer:
    """
    線描画処理の統合クラス。

    水平線・垂直線の描画を統一的に処理し、
    重複コードを除去します。
    """

    def __init__(self, tile_placer: Callable[[np.ndarray, int, int, bool], None]) -> None:
        """
        線描画器を初期化。

        Args:
        ----
            tile_placer: タイル配置関数 (tiles, x, y, allow_door) -> None
        """
        self.tile_placer = tile_placer

    def draw_horizontal_line(
        self,
        tiles: np.ndarray,
        x1: int,
        x2: int,
        y: int,
        reverse: bool = False,
        boundary_door_placer: Callable[[np.ndarray, int, int, bool], None] | None = None,
    ) -> None:
        """
        水平線を描画。

        Args:
        ----
            tiles: ダンジョンのタイル配列
            x1: 開始X座標
            x2: 終了X座標
            y: Y座標
            reverse: 逆順描画フラグ
            boundary_door_placer: 境界位置用のタイル配置関数（オプション）
        """
        x_start, x_end = min(x1, x2), max(x1, x2)
        x_values = list(range(x_start, x_end + 1))

        if reverse:
            x_values.reverse()

        for i, x in enumerate(x_values):
            # 最初と最後の位置では特に積極的にドア配置
            is_boundary = (i == 0) or (i == len(x_values) - 1)
            allow_door = True

            # 境界位置では特別な処理を使用
            if is_boundary and boundary_door_placer:
                boundary_door_placer(tiles, x, y, allow_door)
            else:
                self.tile_placer(tiles, x, y, allow_door)

    def draw_vertical_line(
        self,
        tiles: np.ndarray,
        x: int,
        y1: int,
        y2: int,
        reverse: bool = False,
        boundary_door_placer: Callable[[np.ndarray, int, int, bool], None] | None = None,
    ) -> None:
        """
        垂直線を描画。

        Args:
        ----
            tiles: ダンジョンのタイル配列
            x: X座標
            y1: 開始Y座標
            y2: 終了Y座標
            reverse: 逆順描画フラグ
            boundary_door_placer: 境界位置用のタイル配置関数（オプション）
        """
        y_start, y_end = min(y1, y2), max(y1, y2)
        y_values = list(range(y_start, y_end + 1))

        if reverse:
            y_values.reverse()

        for i, y in enumerate(y_values):
            # 最初と最後の位置では特に積極的にドア配置
            is_boundary = (i == 0) or (i == len(y_values) - 1)
            allow_door = True

            # 境界位置では特別な処理を使用
            if is_boundary and boundary_door_placer:
                boundary_door_placer(tiles, x, y, allow_door)
            else:
                self.tile_placer(tiles, x, y, allow_door)

    def draw_connection_line(
        self,
        tiles: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        horizontal_first: bool = True,
        boundary_door_placer: Callable[[np.ndarray, int, int, bool], None] | None = None,
    ) -> None:
        """
        L字型の接続線を描画。

        Args:
        ----
            tiles: ダンジョンのタイル配列
            x1: 開始X座標
            y1: 開始Y座標
            x2: 終了X座標
            y2: 終了Y座標
            horizontal_first: 水平線から開始するかのフラグ
            boundary_door_placer: 境界位置用のタイル配置関数（オプション）
        """
        if horizontal_first:
            # 水平→垂直
            self.draw_horizontal_line(tiles, x1, x2, y1, boundary_door_placer=boundary_door_placer)
            self.draw_vertical_line(tiles, x2, y1, y2, boundary_door_placer=boundary_door_placer)
        else:
            # 垂直→水平
            self.draw_vertical_line(tiles, x1, y1, y2, boundary_door_placer=boundary_door_placer)
            self.draw_horizontal_line(tiles, x1, x2, y2, boundary_door_placer=boundary_door_placer)
