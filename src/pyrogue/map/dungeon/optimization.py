"""
ダンジョン生成最適化ヒューリスティックス。

このモジュールは、ダンジョン生成プロセスの各段階を最適化するための
ヒューリスティックスとベストプラクティスを提供します。
"""

from __future__ import annotations

import math
from typing import Any

from pyrogue.utils import game_logger


class DungeonOptimizer:
    """
    ダンジョン生成最適化クラス。

    生成パラメータを動的に調整し、パフォーマンスを最適化します。

    Attributes
    ----------
        width: ダンジョンの幅
        height: ダンジョンの高さ
        floor: 階層番号
        target_room_count: 目標部屋数

    """

    def __init__(self, width: int, height: int, floor: int) -> None:
        """
        最適化システムを初期化。

        Args:
        ----
            width: ダンジョンの幅
            height: ダンジョンの高さ
            floor: 階層番号

        """
        self.width = width
        self.height = height
        self.floor = floor
        self.target_room_count = self._calculate_optimal_room_count()

    def _calculate_optimal_room_count(self) -> int:
        """
        最適な部屋数を計算。

        Returns
        -------
            最適な部屋数

        """
        # ダンジョンサイズに基づく基本部屋数
        area = self.width * self.height
        base_rooms = int(math.sqrt(area / 100))  # 100平方ピクセルあたり1部屋

        # 階層による調整
        floor_modifier = 1.0 + (self.floor - 1) * 0.1  # 深い階層ほど複雑

        # 最小・最大値の制限
        optimal_rooms = max(3, min(15, int(base_rooms * floor_modifier)))

        game_logger.debug(f"Calculated optimal room count: {optimal_rooms} for floor {self.floor}")
        return optimal_rooms

    def get_room_generation_params(self) -> dict[str, Any]:
        """
        部屋生成パラメータを取得。

        Returns
        -------
            最適化されたパラメータ

        """
        return {
            "target_room_count": self.target_room_count,
            "min_room_size": max(3, self.width // 15),
            "max_room_size": min(12, self.width // 6),
            "room_spacing": 2,
            "max_attempts": self.target_room_count * 10,
        }

    def get_corridor_generation_params(self) -> dict[str, Any]:
        """
        通路生成パラメータを取得。

        Returns
        -------
            最適化されたパラメータ

        """
        return {
            "max_corridor_length": min(20, max(self.width, self.height) // 3),
            "corridor_width": 1,
            "prefer_straight_lines": True,
            "avoid_diagonal": True,
        }

    def get_special_room_probability(self) -> float:
        """
        特別部屋の生成確率を取得。

        Returns
        -------
            特別部屋の生成確率

        """
        # 階層が深いほど特別部屋の確率が高い
        base_probability = 0.2
        floor_bonus = (self.floor - 1) * 0.02
        return min(0.8, base_probability + floor_bonus)

    def should_use_bsp_algorithm(self) -> bool:
        """
        BSPアルゴリズムを使用すべきかどうか判定。

        Returns
        -------
            BSPアルゴリズムの使用推奨

        """
        # 大きなダンジョンではBSPが効率的
        return self.width * self.height > 2000

    def get_optimization_report(self) -> dict[str, Any]:
        """
        最適化設定のレポートを生成。

        Returns
        -------
            最適化レポート

        """
        return {
            "dungeon_size": f"{self.width}x{self.height}",
            "floor": self.floor,
            "target_room_count": self.target_room_count,
            "special_room_probability": self.get_special_room_probability(),
            "use_bsp_algorithm": self.should_use_bsp_algorithm(),
            "room_params": self.get_room_generation_params(),
            "corridor_params": self.get_corridor_generation_params(),
        }


class ValidationOptimizer:
    """
    検証処理最適化クラス。

    検証処理を効率化し、不要な処理をスキップします。

    """

    def __init__(self, width: int, height: int) -> None:
        """
        検証最適化を初期化。

        Args:
        ----
            width: ダンジョンの幅
            height: ダンジョンの高さ

        """
        self.width = width
        self.height = height

    def should_skip_connectivity_check(self, room_count: int) -> bool:
        """
        接続性チェックをスキップすべきかどうか判定。

        Args:
        ----
            room_count: 部屋数

        Returns:
        -------
            スキップ推奨かどうか

        """
        # 非常に小さなダンジョンでは接続性チェックをスキップ
        return room_count <= 2

    def get_validation_level(self, performance_budget: float) -> str:
        """
        パフォーマンス予算に基づいて検証レベルを決定。

        Args:
        ----
            performance_budget: パフォーマンス予算（秒）

        Returns:
        -------
            検証レベル（'minimal', 'standard', 'thorough'）

        """
        if performance_budget < 0.1:
            return "minimal"
        if performance_budget < 0.5:
            return "standard"
        return "thorough"

    def get_optimized_validation_params(self, validation_level: str) -> dict[str, Any]:
        """
        最適化された検証パラメータを取得。

        Args:
        ----
            validation_level: 検証レベル

        Returns:
        -------
            検証パラメータ

        """
        if validation_level == "minimal":
            return {
                "check_connectivity": False,
                "check_accessibility": True,
                "check_stairs": True,
                "check_room_overlap": False,
                "detailed_logging": False,
            }
        if validation_level == "standard":
            return {
                "check_connectivity": True,
                "check_accessibility": True,
                "check_stairs": True,
                "check_room_overlap": True,
                "detailed_logging": False,
            }
        # thorough
        return {
            "check_connectivity": True,
            "check_accessibility": True,
            "check_stairs": True,
            "check_room_overlap": True,
            "detailed_logging": True,
        }


class MemoryOptimizer:
    """
    メモリ使用量最適化クラス。

    メモリ使用量を最小限に抑えるための戦略を提供します。

    """

    @staticmethod
    def estimate_memory_usage(width: int, height: int, room_count: int) -> dict[str, float]:
        """
        メモリ使用量を推定。

        Args:
        ----
            width: ダンジョンの幅
            height: ダンジョンの高さ
            room_count: 部屋数

        Returns:
        -------
            メモリ使用量推定（MB）

        """
        # タイル配列のメモリ使用量（概算）
        tiles_memory = (width * height * 8) / 1024 / 1024  # 8 bytes per tile object

        # 部屋データのメモリ使用量
        rooms_memory = (room_count * 200) / 1024 / 1024  # 200 bytes per room

        # その他のデータ構造
        other_memory = 1.0  # 1MB for other data structures

        total_memory = tiles_memory + rooms_memory + other_memory

        return {
            "tiles_mb": tiles_memory,
            "rooms_mb": rooms_memory,
            "other_mb": other_memory,
            "total_mb": total_memory,
        }

    @staticmethod
    def get_memory_optimization_suggestions(memory_usage: dict[str, float]) -> list[str]:
        """
        メモリ最適化の提案を生成。

        Args:
        ----
            memory_usage: メモリ使用量推定

        Returns:
        -------
            最適化提案のリスト

        """
        suggestions = []

        if memory_usage["total_mb"] > 50:
            suggestions.append("Consider reducing dungeon size or room count")

        if memory_usage["tiles_mb"] > 30:
            suggestions.append("Use tile pooling or more efficient tile representation")

        if memory_usage["rooms_mb"] > 5:
            suggestions.append("Optimize room data structure")

        if not suggestions:
            suggestions.append("Memory usage is optimal")

        return suggestions

    @staticmethod
    def should_use_memory_optimization(total_memory_mb: float) -> bool:
        """
        メモリ最適化を使用すべきかどうか判定。

        Args:
        ----
            total_memory_mb: 総メモリ使用量（MB）

        Returns:
        -------
            メモリ最適化の使用推奨

        """
        return total_memory_mb > 20  # 20MB以上でメモリ最適化を推奨
