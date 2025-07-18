"""
包括的難易度調整システム。

このモジュールは、階層難易度管理、強化アイテム生成、
強化トラップ生成を統合し、全体的なゲームバランスを管理します。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from pyrogue.core.managers.floor_difficulty_manager import FloorDifficultyManager
from pyrogue.entities.items.enhanced_item_spawner import EnhancedItemSpawner
from pyrogue.entities.traps.enhanced_trap_spawner import EnhancedTrapSpawner
from pyrogue.utils import game_logger

if TYPE_CHECKING:
    import numpy as np

    from pyrogue.map.dungeon import Room


class ComprehensiveDifficultySystem:
    """
    包括的難易度調整システム。

    階層の難易度を分析し、モンスター、アイテム、トラップの
    出現バランスを総合的に調整します。
    """

    def __init__(self, floor: int) -> None:
        """
        包括的難易度システムを初期化。

        Args:
        ----
            floor: 階層番号

        """
        self.floor = floor
        self.difficulty_manager = FloorDifficultyManager(floor)

        # 各種生成システムを初期化
        self.item_spawner = EnhancedItemSpawner(floor)
        self.trap_spawner = EnhancedTrapSpawner(floor)

        # 総合統計情報
        self.comprehensive_statistics: dict[str, Any] = {
            "floor": floor,
            "difficulty_analysis": {},
            "balance_adjustments": {},
            "spawn_results": {},
            "recommendations": [],
        }

        game_logger.info(f"ComprehensiveDifficultySystem initialized for floor {floor}")

    def analyze_floor_difficulty(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> dict[str, Any]:
        """
        階層の難易度を包括的に分析。

        Args:
        ----
            dungeon_tiles: ダンジョンのタイル配列
            rooms: ダンジョンの部屋リスト

        Returns:
        -------
            包括的な難易度分析結果

        """
        analysis = {
            "layout_analysis": self._analyze_layout_difficulty(dungeon_tiles, rooms),
            "monster_analysis": self._analyze_monster_difficulty(),
            "item_analysis": self._analyze_item_difficulty(),
            "trap_analysis": self._analyze_trap_difficulty(),
            "overall_rating": self._calculate_overall_difficulty(),
        }

        self.comprehensive_statistics["difficulty_analysis"] = analysis
        return analysis

    def apply_comprehensive_spawning(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """
        包括的な生成システムを適用。

        Args:
        ----
            dungeon_tiles: ダンジョンのタイル配列
            rooms: ダンジョンの部屋リスト

        """
        # 事前分析
        difficulty_analysis = self.analyze_floor_difficulty(dungeon_tiles, rooms)

        # バランス調整の適用
        balance_adjustments = self._calculate_balance_adjustments(difficulty_analysis)
        self.comprehensive_statistics["balance_adjustments"] = balance_adjustments

        # 調整されたアイテム生成
        self._apply_adjusted_item_spawning(dungeon_tiles, rooms, balance_adjustments)

        # 調整されたトラップ生成
        self._apply_adjusted_trap_spawning(dungeon_tiles, rooms, balance_adjustments)

        # 結果の統計
        self._collect_spawn_results()

        # 推奨事項の生成
        self._generate_recommendations()

        game_logger.info(f"Comprehensive spawning completed for floor {self.floor}")

    def _analyze_layout_difficulty(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> dict[str, Any]:
        """レイアウトの難易度分析。"""
        height, width = dungeon_tiles.shape

        # 部屋の統計
        room_count = len(rooms)
        total_room_area = sum(room.width * room.height for room in rooms)
        avg_room_size = total_room_area / room_count if room_count > 0 else 0

        # 廊下の統計
        floor_tiles = sum(1 for y in range(height) for x in range(width) if dungeon_tiles[y, x].walkable)
        corridor_tiles = max(0, floor_tiles - total_room_area)
        corridor_ratio = corridor_tiles / floor_tiles if floor_tiles > 0 else 0

        # 複雑性の評価
        complexity_score = self._calculate_layout_complexity(rooms, corridor_ratio)

        return {
            "room_count": room_count,
            "avg_room_size": avg_room_size,
            "corridor_ratio": corridor_ratio,
            "complexity_score": complexity_score,
            "layout_type": self._classify_layout_type(room_count, corridor_ratio),
        }

    def _analyze_monster_difficulty(self) -> dict[str, Any]:
        """モンスターの難易度分析。"""
        monster_adjustments = self.difficulty_manager.get_monster_spawn_adjustments()

        # 予想される敵の強さ
        expected_monsters = monster_adjustments["base_count"]
        elite_chance = monster_adjustments["elite_spawn_chance"]
        pack_chance = monster_adjustments["pack_spawn_chance"]

        # 戦闘難易度の計算
        combat_difficulty = self._calculate_combat_difficulty(expected_monsters, elite_chance, pack_chance)

        return {
            "expected_monsters": expected_monsters,
            "elite_chance": elite_chance,
            "pack_chance": pack_chance,
            "combat_difficulty": combat_difficulty,
            "threat_level": self._classify_threat_level(combat_difficulty),
        }

    def _analyze_item_difficulty(self) -> dict[str, Any]:
        """アイテムの難易度分析。"""
        item_adjustments = self.difficulty_manager.get_item_spawn_adjustments()

        # 生存支援度の計算
        food_support = item_adjustments["food_weight_modifier"]
        rare_chance = item_adjustments["rare_item_chance"]
        cursed_chance = item_adjustments["cursed_item_chance"]

        # 支援度の評価
        support_level = self._calculate_support_level(food_support, rare_chance, cursed_chance)

        return {
            "expected_items": item_adjustments["base_count"],
            "food_support": food_support,
            "rare_chance": rare_chance,
            "cursed_chance": cursed_chance,
            "support_level": support_level,
        }

    def _analyze_trap_difficulty(self) -> dict[str, Any]:
        """トラップの難易度分析。"""
        trap_adjustments = self.difficulty_manager.get_trap_spawn_adjustments()

        # 危険度の計算
        expected_traps = trap_adjustments["base_count"]
        hidden_chance = trap_adjustments["hidden_trap_chance"]
        magical_chance = trap_adjustments["magical_trap_chance"]

        # 危険度の評価
        danger_level = self._calculate_danger_level(expected_traps, hidden_chance, magical_chance)

        return {
            "expected_traps": expected_traps,
            "hidden_chance": hidden_chance,
            "magical_chance": magical_chance,
            "danger_level": danger_level,
        }

    def _calculate_overall_difficulty(self) -> dict[str, Any]:
        """全体的な難易度の計算。"""
        # 各要素の難易度スコア
        layout_score = self._get_layout_difficulty_score()
        monster_score = self._get_monster_difficulty_score()
        item_score = self._get_item_difficulty_score()
        trap_score = self._get_trap_difficulty_score()

        # 重み付き平均
        overall_score = layout_score * 0.2 + monster_score * 0.4 + item_score * 0.2 + trap_score * 0.2

        return {
            "layout_score": layout_score,
            "monster_score": monster_score,
            "item_score": item_score,
            "trap_score": trap_score,
            "overall_score": overall_score,
            "difficulty_rating": self._classify_difficulty_rating(overall_score),
        }

    def _calculate_balance_adjustments(self, difficulty_analysis: dict[str, Any]) -> dict[str, Any]:
        """バランス調整の計算。"""
        overall_rating = difficulty_analysis["overall_rating"]
        overall_score = overall_rating["overall_score"]

        # バランス調整の決定
        adjustments = {
            "item_support_modifier": 1.0,
            "trap_danger_modifier": 1.0,
            "special_event_chance": 0.0,
            "emergency_supplies": False,
            "bonus_rewards": False,
        }

        # 難易度が高すぎる場合の調整
        if overall_score > 0.8:
            adjustments["item_support_modifier"] = 1.5  # アイテム支援を増加
            adjustments["trap_danger_modifier"] = 0.8  # トラップ危険度を減少
            adjustments["emergency_supplies"] = True  # 緊急補給を追加

        # 難易度が低すぎる場合の調整
        elif overall_score < 0.3:
            adjustments["item_support_modifier"] = 0.8  # アイテム支援を減少
            adjustments["trap_danger_modifier"] = 1.3  # トラップ危険度を増加
            adjustments["bonus_rewards"] = True  # ボーナス報酬を追加

        # 特殊イベントの調整
        if 0.4 <= overall_score <= 0.7:
            adjustments["special_event_chance"] = 0.1  # 特殊イベントの機会を増加

        return adjustments

    def _apply_adjusted_item_spawning(
        self, dungeon_tiles: np.ndarray, rooms: list[Room], adjustments: dict[str, Any]
    ) -> None:
        """調整されたアイテム生成を適用。"""
        # 基本的なアイテム生成
        self.item_spawner.spawn_items(dungeon_tiles, rooms)

        # 緊急補給の追加
        if adjustments["emergency_supplies"]:
            self._add_emergency_supplies(dungeon_tiles, rooms)

        # ボーナス報酬の追加
        if adjustments["bonus_rewards"]:
            self._add_bonus_rewards(dungeon_tiles, rooms)

    def _apply_adjusted_trap_spawning(
        self, dungeon_tiles: np.ndarray, rooms: list[Room], adjustments: dict[str, Any]
    ) -> None:
        """調整されたトラップ生成を適用。"""
        # 基本的なトラップ生成
        self.trap_spawner.spawn_traps(dungeon_tiles, rooms)

        # 危険度調整の適用
        danger_modifier = adjustments["trap_danger_modifier"]
        if danger_modifier != 1.0:
            self._adjust_trap_danger(danger_modifier)

    def _add_emergency_supplies(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """緊急補給の追加。"""
        # 追加の食料とポーション
        emergency_items = ["food", "healing_potion", "identify_scroll"]

        for item_type in emergency_items:
            position = self._find_safe_position(dungeon_tiles, rooms)
            if position:
                x, y = position
                item = self._create_emergency_item(item_type, x, y)
                if item:
                    self.item_spawner.add_item(item)

    def _add_bonus_rewards(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """ボーナス報酬の追加。"""
        # 高品質なアイテムの追加
        bonus_items = ["rare_weapon", "rare_armor", "gold_bonus"]

        for item_type in bonus_items:
            if random.random() < 0.3:  # 30%の確率
                position = self._find_hidden_position(dungeon_tiles, rooms)
                if position:
                    x, y = position
                    item = self._create_bonus_item(item_type, x, y)
                    if item:
                        self.item_spawner.add_item(item)

    def _adjust_trap_danger(self, modifier: float) -> None:
        """トラップ危険度の調整。"""
        trap_manager = self.trap_spawner.get_trap_manager()

        if modifier < 1.0:
            # 危険度を減少
            for trap in trap_manager.traps:
                if hasattr(trap, "damage"):
                    trap.damage = int(trap.damage * modifier)
                if hasattr(trap, "duration"):
                    trap.duration = max(1, int(trap.duration * modifier))

        elif modifier > 1.0:
            # 危険度を増加
            for trap in trap_manager.traps:
                if hasattr(trap, "damage"):
                    trap.damage = int(trap.damage * modifier)
                if hasattr(trap, "duration"):
                    trap.duration = int(trap.duration * modifier)

    def _collect_spawn_results(self) -> None:
        """生成結果の統計収集。"""
        item_stats = self.item_spawner.get_spawn_statistics()
        trap_stats = self.trap_spawner.get_spawn_statistics()

        self.comprehensive_statistics["spawn_results"] = {
            "items": item_stats,
            "traps": trap_stats,
            "total_entities": item_stats["spawn_statistics"]["total_spawned"]
            + trap_stats["spawn_statistics"]["total_spawned"],
        }

    def _generate_recommendations(self) -> None:
        """推奨事項の生成。"""
        recommendations = []

        difficulty_analysis = self.comprehensive_statistics["difficulty_analysis"]
        overall_score = difficulty_analysis["overall_rating"]["overall_score"]

        # 難易度に基づく推奨
        if overall_score > 0.8:
            recommendations.extend(
                [
                    "この階層は非常に困難です。慎重に進んでください。",
                    "回復アイテムを温存し、戦略的に使用してください。",
                    "トラップの探索を怠らないでください。",
                ]
            )
        elif overall_score > 0.6:
            recommendations.extend(
                [
                    "この階層は挑戦的です。準備を整えてください。",
                    "アイテムの識別を積極的に行ってください。",
                ]
            )
        elif overall_score < 0.3:
            recommendations.extend(
                [
                    "この階層は比較的安全です。探索を楽しんでください。",
                    "より深い階層への準備を整えてください。",
                ]
            )

        # 特定の要素に基づく推奨
        monster_threat = difficulty_analysis["monster_analysis"]["threat_level"]
        if monster_threat == "very_high":
            recommendations.append("強力な敵が多数います。戦闘を避けるか、十分な準備をしてください。")

        item_support = difficulty_analysis["item_analysis"]["support_level"]
        if item_support == "low":
            recommendations.append("アイテム支援が少ないです。リソース管理を厳重に行ってください。")

        trap_danger = difficulty_analysis["trap_analysis"]["danger_level"]
        if trap_danger == "high":
            recommendations.append("多くの危険なトラップがあります。探索を慎重に行ってください。")

        self.comprehensive_statistics["recommendations"] = recommendations

    def get_comprehensive_report(self) -> dict[str, Any]:
        """包括的なレポートを取得。"""
        return {
            "system_info": {
                "floor": self.floor,
                "difficulty_tier": self.difficulty_manager.difficulty_tier,
                "difficulty_modifier": self.difficulty_manager.difficulty_modifier,
            },
            "statistics": self.comprehensive_statistics,
            "difficulty_report": self.difficulty_manager.get_comprehensive_difficulty_report(),
        }

    def get_item_spawner(self) -> EnhancedItemSpawner:
        """アイテム生成器を取得。"""
        return self.item_spawner

    def get_trap_spawner(self) -> EnhancedTrapSpawner:
        """トラップ生成器を取得。"""
        return self.trap_spawner

    # ヘルパーメソッド
    def _calculate_layout_complexity(self, rooms: list[Room], corridor_ratio: float) -> float:
        """レイアウトの複雑性を計算。"""
        base_score = len(rooms) * 0.1
        corridor_score = corridor_ratio * 0.5
        return min(base_score + corridor_score, 1.0)

    def _classify_layout_type(self, room_count: int, corridor_ratio: float) -> str:
        """レイアウトタイプを分類。"""
        if room_count <= 3:
            return "simple"
        if room_count <= 8:
            return "moderate"
        return "complex"

    def _calculate_combat_difficulty(self, monster_count: int, elite_chance: float, pack_chance: float) -> float:
        """戦闘難易度を計算。"""
        base_score = monster_count * 0.05
        elite_score = elite_chance * 0.3
        pack_score = pack_chance * 0.2
        return min(base_score + elite_score + pack_score, 1.0)

    def _classify_threat_level(self, combat_difficulty: float) -> str:
        """脅威レベルを分類。"""
        if combat_difficulty < 0.3:
            return "low"
        if combat_difficulty < 0.6:
            return "moderate"
        if combat_difficulty < 0.8:
            return "high"
        return "very_high"

    def _calculate_support_level(self, food_support: float, rare_chance: float, cursed_chance: float) -> str:
        """支援レベルを計算。"""
        support_score = food_support * 0.4 + rare_chance * 0.3 - cursed_chance * 0.3

        if support_score < 0.5:
            return "low"
        if support_score < 1.0:
            return "moderate"
        return "high"

    def _calculate_danger_level(self, trap_count: int, hidden_chance: float, magical_chance: float) -> str:
        """危険レベルを計算。"""
        danger_score = trap_count * 0.1 + hidden_chance * 0.3 + magical_chance * 0.2

        if danger_score < 0.3:
            return "low"
        if danger_score < 0.6:
            return "moderate"
        return "high"

    def _get_layout_difficulty_score(self) -> float:
        """レイアウト難易度スコアを取得。"""
        return self.difficulty_manager.difficulty_tier * 0.2

    def _get_monster_difficulty_score(self) -> float:
        """モンスター難易度スコアを取得。"""
        return self.difficulty_manager.difficulty_tier * 0.2

    def _get_item_difficulty_score(self) -> float:
        """アイテム難易度スコアを取得。"""
        return self.difficulty_manager.difficulty_tier * 0.15

    def _get_trap_difficulty_score(self) -> float:
        """トラップ難易度スコアを取得。"""
        return self.difficulty_manager.difficulty_tier * 0.15

    def _classify_difficulty_rating(self, overall_score: float) -> str:
        """難易度レーティングを分類。"""
        if overall_score < 0.2:
            return "very_easy"
        if overall_score < 0.4:
            return "easy"
        if overall_score < 0.6:
            return "moderate"
        if overall_score < 0.8:
            return "hard"
        return "very_hard"

    def _find_safe_position(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> tuple[int, int] | None:
        """安全な位置を検索。"""
        if rooms:
            # 大きな部屋の中央付近
            large_room = max(rooms, key=lambda r: r.width * r.height)
            center_x = large_room.x + large_room.width // 2
            center_y = large_room.y + large_room.height // 2
            return (center_x, center_y)
        return None

    def _find_hidden_position(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> tuple[int, int] | None:
        """隠れた位置を検索。"""
        if rooms:
            # 部屋の角
            room = random.choice(rooms)
            corner_x = room.x + 1
            corner_y = room.y + 1
            return (corner_x, corner_y)
        return None

    def _create_emergency_item(self, item_type: str, x: int, y: int) -> Any | None:
        """緊急アイテムを作成。"""
        # 実装は省略（実際のアイテムクラスを使用）
        return None

    def _create_bonus_item(self, item_type: str, x: int, y: int) -> Any | None:
        """ボーナスアイテムを作成。"""
        # 実装は省略（実際のアイテムクラスを使用）
        return None
