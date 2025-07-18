"""
ダンジョン生成パフォーマンスプロファイラー。

このモジュールは、ダンジョン生成プロセスの各段階での
パフォーマンスを計測し、分析するためのツールを提供します。
"""

from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from pyrogue.utils import game_logger


class DungeonProfiler:
    """
    ダンジョン生成パフォーマンスプロファイラー。

    各段階での処理時間を計測し、詳細なレポートを提供します。

    Attributes
    ----------
        timings: 各段階の処理時間記録
        memory_usage: メモリ使用量記録
        stats: 統計情報

    """

    def __init__(self) -> None:
        """プロファイラーを初期化。"""
        self.timings: dict[str, float] = {}
        self.memory_usage: dict[str, int] = {}
        self.stats: dict[str, Any] = {}
        self.start_time: float = 0.0
        self.total_time: float = 0.0

    def start_profiling(self) -> None:
        """プロファイリングを開始。"""
        self.start_time = time.perf_counter()
        self.timings.clear()
        self.memory_usage.clear()
        self.stats.clear()

    def stop_profiling(self) -> None:
        """プロファイリングを停止。"""
        self.total_time = time.perf_counter() - self.start_time

    @contextmanager
    def section(self, name: str) -> Generator[None, None, None]:
        """
        プロファイリング区間のコンテキストマネージャー。

        Args:
        ----
            name: 区間名

        Yields:
        ------
            None

        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            self.timings[name] = end_time - start_time
            game_logger.debug(f"Profiling [{name}]: {self.timings[name]:.4f}s")

    def record_stat(self, name: str, value: Any) -> None:
        """
        統計情報を記録。

        Args:
        ----
            name: 統計名
            value: 値

        """
        self.stats[name] = value

    def get_report(self) -> dict[str, Any]:
        """
        パフォーマンスレポートを生成。

        Returns
        -------
            レポート辞書

        """
        return {
            "total_time": self.total_time,
            "timings": self.timings.copy(),
            "memory_usage": self.memory_usage.copy(),
            "stats": self.stats.copy(),
            "analysis": self._analyze_performance(),
        }

    def _analyze_performance(self) -> dict[str, Any]:
        """
        パフォーマンス分析を実行。

        Returns
        -------
            分析結果

        """
        if not self.timings:
            return {"warning": "No timing data available"}

        # 最も時間のかかった段階を特定
        slowest_section = max(self.timings.items(), key=lambda x: x[1])

        # 各段階の比率を計算
        section_percentages = {}
        for name, timing in self.timings.items():
            percentage = (timing / self.total_time) * 100
            section_percentages[name] = percentage

        # ボトルネック検出
        bottlenecks = []
        for name, percentage in section_percentages.items():
            if percentage > 30:  # 30%以上の時間を占める段階
                bottlenecks.append({"section": name, "percentage": percentage, "time": self.timings[name]})

        return {
            "slowest_section": {
                "name": slowest_section[0],
                "time": slowest_section[1],
                "percentage": section_percentages[slowest_section[0]],
            },
            "section_percentages": section_percentages,
            "bottlenecks": bottlenecks,
            "performance_level": self._classify_performance(),
        }

    def _classify_performance(self) -> str:
        """
        パフォーマンスレベルを分類。

        Returns
        -------
            パフォーマンスレベル

        """
        if self.total_time < 0.1:
            return "excellent"
        if self.total_time < 0.5:
            return "good"
        if self.total_time < 1.0:
            return "acceptable"
        if self.total_time < 2.0:
            return "slow"
        return "very_slow"

    def log_report(self) -> None:
        """レポートをログに出力。"""
        report = self.get_report()

        game_logger.info(f"Dungeon generation completed in {report['total_time']:.4f}s")
        game_logger.info(f"Performance level: {report['analysis']['performance_level']}")

        # 各段階の時間を詳細ログ
        for section, timing in report["timings"].items():
            percentage = report["analysis"]["section_percentages"][section]
            game_logger.debug(f"  {section}: {timing:.4f}s ({percentage:.1f}%)")

        # ボトルネック警告
        if report["analysis"]["bottlenecks"]:
            game_logger.warning("Performance bottlenecks detected:")
            for bottleneck in report["analysis"]["bottlenecks"]:
                game_logger.warning(
                    f"  {bottleneck['section']}: {bottleneck['time']:.4f}s ({bottleneck['percentage']:.1f}%)"
                )
