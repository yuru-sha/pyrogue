"""
経路探索管理コンポーネント。

このモジュールは、A*アルゴリズムを使用した経路探索機能を提供します。
モンスターやプレイヤーの移動経路計算を担当します。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod

from pyrogue.utils import game_logger

if TYPE_CHECKING:
    from pyrogue.core.managers.game_context import GameContext


class PathfindingManager:
    """
    経路探索システムの管理クラス。

    A*アルゴリズムを使用して、ゲーム内のエンティティの
    最適な移動経路を計算します。
    """

    def __init__(self) -> None:
        """経路探索マネージャーを初期化。"""
        # 経路探索キャッシュ
        self._pathfinding_cache: dict[tuple[int, int, int, int], list[tuple[int, int]]] = {}

    def find_path(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        context: GameContext,
        max_distance: int = 15,
    ) -> list[tuple[int, int]] | None:
        """
        A*アルゴリズムを使用して経路を探索。

        Args:
        ----
            start_x, start_y: 開始位置
            end_x, end_y: 終了位置
            context: ゲームコンテキスト
            max_distance: 最大探索距離

        Returns:
        -------
            経路のリスト（見つからない場合はNone）

        """
        # 距離が遠い場合は経路探索を使用しない（パフォーマンス最適化）
        distance = self._calculate_distance(start_x, start_y, end_x, end_y)
        if distance > max_distance:
            return None

        # キャッシュから経路を取得
        cache_key = (start_x, start_y, end_x, end_y)
        if cache_key in self._pathfinding_cache:
            return self._pathfinding_cache[cache_key]

        # 経路探索を実行
        path = self._find_path_internal(start_x, start_y, end_x, end_y, context)
        if path:
            # キャッシュに保存
            self._pathfinding_cache[cache_key] = path

        return path

    def _find_path_internal(
        self, start_x: int, start_y: int, end_x: int, end_y: int, context: GameContext
    ) -> list[tuple[int, int]] | None:
        """
        内部的な経路探索実行。

        Args:
        ----
            start_x, start_y: 開始位置
            end_x, end_y: 終了位置
            context: ゲームコンテキスト

        Returns:
        -------
            経路のリスト（見つからない場合はNone）

        """
        floor_data = context.get_current_floor_data()
        if not floor_data:
            return None

        # コストマップを作成
        cost_map = self._create_cost_map(context)
        if cost_map is None:
            return None

        # A*アルゴリズムを実行
        try:
            path = tcod.path.find_path(  # type: ignore
                cost_map,
                start=(start_x, start_y),
                end=(end_x, end_y),
                diagonal=True,
                algorithm=tcod.path.DIJKSTRA,  # type: ignore
            )
            return [(x, y) for x, y in path]
        except Exception as e:
            game_logger.debug(f"Pathfinding failed: {e}")
            return None

    def _create_cost_map(self, context: GameContext) -> tcod.path.Pathfinder | None:
        """
        経路探索用のコストマップを作成。

        Args:
        ----
            context: ゲームコンテキスト

        Returns:
        -------
            コストマップ（作成に失敗した場合はNone）

        """
        floor_data = context.get_current_floor_data()
        if not floor_data:
            return None

        try:
            # タイルの歩行可能性に基づいてコストを設定
            height, width = floor_data.tiles.shape
            cost_array = tcod.numpy.zeros((height, width), dtype=tcod.numpy.int8)  # type: ignore

            for y in range(height):
                for x in range(width):
                    tile = floor_data.tiles[y, x]
                    if getattr(tile, "walkable", False):
                        cost_array[y, x] = 1  # 歩行可能
                    else:
                        cost_array[y, x] = 0  # 歩行不可

            return tcod.path.Pathfinder(cost_array)
        except Exception as e:
            game_logger.debug(f"Cost map creation failed: {e}")
            return None

    def _calculate_distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """
        2点間の距離を計算。

        Args:
        ----
            x1, y1: 点1の座標
            x2, y2: 点2の座標

        Returns:
        -------
            ユークリッド距離

        """
        return float(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5)

    def clear_cache(self) -> None:
        """経路探索キャッシュをクリア。"""
        self._pathfinding_cache.clear()

    def get_cache_size(self) -> int:
        """キャッシュサイズを取得。"""
        return len(self._pathfinding_cache)
