"""
階層難易度管理システム。

このモジュールは、ダンジョンの各階層の難易度を動的に調整し、
モンスター出現率、アイテム出現率、トラップ配置を最適化します。
"""

from __future__ import annotations

from typing import Any

from pyrogue.utils import game_logger


class FloorDifficultyManager:
    """
    階層難易度管理クラス。

    各階層の難易度を分析し、モンスター・アイテム・トラップの
    出現率を動的に調整します。
    """

    def __init__(self, floor: int) -> None:
        """
        階層難易度管理を初期化。

        Args:
        ----
            floor: 階層番号

        """
        self.floor = floor
        self.difficulty_tier = self._calculate_difficulty_tier(floor)
        self.difficulty_modifier = self._calculate_difficulty_modifier(floor)

        # 階層別の基本パラメータ
        self.base_monster_count = self._calculate_base_monster_count(floor)
        self.base_item_count = self._calculate_base_item_count(floor)
        self.base_trap_count = self._calculate_base_trap_count(floor)

        game_logger.debug(f"FloorDifficultyManager initialized for floor {floor} (tier {self.difficulty_tier})")

    def _calculate_difficulty_tier(self, floor: int) -> int:
        """
        階層の難易度ティアを計算。

        Args:
        ----
            floor: 階層番号

        Returns:
        -------
            難易度ティア（1-5）

        """
        if floor <= 5:
            return 1  # 初心者ティア
        if floor <= 10:
            return 2  # 初級ティア
        if floor <= 15:
            return 3  # 中級ティア
        if floor <= 20:
            return 4  # 上級ティア
        return 5  # 最高難易度ティア

    def _calculate_difficulty_modifier(self, floor: int) -> float:
        """
        階層の難易度修正値を計算。

        Args:
        ----
            floor: 階層番号

        Returns:
        -------
            難易度修正値（0.5-2.0）

        """
        # 非線形な難易度曲線を使用
        base_modifier = 0.5 + (floor - 1) * 0.06  # 基本的な線形増加

        # 特定の階層での難易度スパイク
        spike_floors = [7, 13, 19, 26]  # 迷路階層と最終階層
        if floor in spike_floors:
            base_modifier *= 1.3

        # 階層別の特殊修正
        if floor >= 21:  # 最深部
            base_modifier *= 1.5
        elif floor >= 16:  # 終盤
            base_modifier *= 1.2

        return min(base_modifier, 2.0)  # 最大値を制限

    def _calculate_base_monster_count(self, floor: int) -> int:
        """
        基本モンスター数を計算。

        Args:
        ----
            floor: 階層番号

        Returns:
        -------
            基本モンスター数

        """
        base_count = 3 + (floor - 1) // 2  # 2階層ごとに1体増加
        tier_bonus = self.difficulty_tier * 2  # ティアごとに2体増加

        # 最大値制限
        total_count = min(base_count + tier_bonus, 15)

        return max(total_count, 3)  # 最小値保証

    def _calculate_base_item_count(self, floor: int) -> int:
        """
        基本アイテム数を計算。

        Args:
        ----
            floor: 階層番号

        Returns:
        -------
            基本アイテム数

        """
        base_count = 2 + (floor - 1) // 3  # 3階層ごとに1個増加
        tier_bonus = self.difficulty_tier  # ティアごとに1個増加

        # 食料不足を防ぐため、深い階層ではアイテム数を増加
        if floor >= 15:
            base_count += 2
        elif floor >= 10:
            base_count += 1

        return max(base_count + tier_bonus, 3)  # 最小値保証

    def _calculate_base_trap_count(self, floor: int) -> int:
        """
        基本トラップ数を計算。

        Args:
        ----
            floor: 階層番号

        Returns:
        -------
            基本トラップ数

        """
        if floor <= 2:
            return 0  # 最初の2階層はトラップなし

        base_count = (floor - 2) // 2  # 3階層目から2階層ごとに1個増加
        tier_bonus = max(0, self.difficulty_tier - 1)  # ティア2以上で増加

        return min(base_count + tier_bonus, 8)  # 最大値制限

    def get_monster_spawn_adjustments(self) -> dict[str, Any]:
        """
        モンスター出現調整パラメータを取得。

        Returns
        -------
            モンスター出現調整パラメータ

        """
        return {
            "base_count": self.base_monster_count,
            "count_modifier": self.difficulty_modifier,
            "elite_spawn_chance": self._get_elite_spawn_chance(),
            "pack_spawn_chance": self._get_pack_spawn_chance(),
            "boss_spawn_chance": self._get_boss_spawn_chance(),
            "level_variance": self._get_monster_level_variance(),
            "equipment_quality": self._get_monster_equipment_quality(),
        }

    def _get_elite_spawn_chance(self) -> float:
        """エリートモンスターの出現確率を取得。"""
        base_chance = 0.05  # 5%
        tier_bonus = self.difficulty_tier * 0.03  # ティアごとに3%増加
        floor_bonus = (self.floor - 1) * 0.01  # 階層ごとに1%増加

        return min(base_chance + tier_bonus + floor_bonus, 0.3)  # 最大30%

    def _get_pack_spawn_chance(self) -> float:
        """群れモンスターの出現確率を取得。"""
        if self.floor <= 3:
            return 0.0  # 初期階層では群れなし

        base_chance = 0.1  # 10%
        tier_bonus = self.difficulty_tier * 0.05  # ティアごとに5%増加

        return min(base_chance + tier_bonus, 0.4)  # 最大40%

    def _get_boss_spawn_chance(self) -> float:
        """ボスモンスターの出現確率を取得。"""
        if self.floor <= 5:
            return 0.0  # 初期階層ではボスなし

        # 特定の階層でボス出現率を高める
        boss_floors = [10, 15, 20, 25, 26]
        if self.floor in boss_floors:
            return 0.8  # 80%

        base_chance = 0.02  # 2%
        tier_bonus = self.difficulty_tier * 0.02  # ティアごとに2%増加

        return min(base_chance + tier_bonus, 0.2)  # 最大20%

    def _get_monster_level_variance(self) -> int:
        """モンスターレベルの変動範囲を取得。"""
        return min(self.difficulty_tier, 3)  # 最大±3

    def _get_monster_equipment_quality(self) -> float:
        """モンスターの装備品質修正値を取得。"""
        base_quality = 1.0
        tier_bonus = self.difficulty_tier * 0.1  # ティアごとに10%向上

        return min(base_quality + tier_bonus, 1.5)  # 最大150%

    def get_item_spawn_adjustments(self) -> dict[str, Any]:
        """
        アイテム出現調整パラメータを取得。

        Returns
        -------
            アイテム出現調整パラメータ

        """
        return {
            "base_count": self.base_item_count,
            "count_modifier": self.difficulty_modifier,
            "rare_item_chance": self._get_rare_item_chance(),
            "cursed_item_chance": self._get_cursed_item_chance(),
            "blessed_item_chance": self._get_blessed_item_chance(),
            "enchantment_bonus": self._get_enchantment_bonus(),
            "food_weight_modifier": self._get_food_weight_modifier(),
            "gold_amount_modifier": self._get_gold_amount_modifier(),
        }

    def _get_rare_item_chance(self) -> float:
        """レアアイテムの出現確率を取得。"""
        base_chance = 0.05  # 5%
        tier_bonus = self.difficulty_tier * 0.03  # ティアごとに3%増加
        floor_bonus = (self.floor - 1) * 0.005  # 階層ごとに0.5%増加

        return min(base_chance + tier_bonus + floor_bonus, 0.25)  # 最大25%

    def _get_cursed_item_chance(self) -> float:
        """呪われたアイテムの出現確率を取得。"""
        if self.floor <= 2:
            return 0.0  # 初期階層では呪いなし

        base_chance = 0.1  # 10%
        tier_bonus = self.difficulty_tier * 0.05  # ティアごとに5%増加

        return min(base_chance + tier_bonus, 0.4)  # 最大40%

    def _get_blessed_item_chance(self) -> float:
        """祝福されたアイテムの出現確率を取得。"""
        base_chance = 0.02  # 2%
        tier_bonus = self.difficulty_tier * 0.01  # ティアごとに1%増加

        return min(base_chance + tier_bonus, 0.1)  # 最大10%

    def _get_enchantment_bonus(self) -> float:
        """エンチャントボーナス修正値を取得。"""
        base_bonus = 0.0
        tier_bonus = self.difficulty_tier * 0.2  # ティアごとに20%向上

        return min(base_bonus + tier_bonus, 1.0)  # 最大100%

    def _get_food_weight_modifier(self) -> float:
        """食料の出現重み修正値を取得。"""
        if self.floor <= 5:
            return 1.0  # 初期階層では通常

        # 深い階層ほど食料の重要性が増す
        base_modifier = 1.0
        depth_bonus = (self.floor - 5) * 0.1  # 6階層目から階層ごとに10%増加

        return min(base_modifier + depth_bonus, 2.5)  # 最大250%

    def _get_gold_amount_modifier(self) -> float:
        """金貨の量修正値を取得。"""
        base_modifier = 1.0
        tier_bonus = self.difficulty_tier * 0.3  # ティアごとに30%増加

        return min(base_modifier + tier_bonus, 2.0)  # 最大200%

    def get_trap_spawn_adjustments(self) -> dict[str, Any]:
        """
        トラップ出現調整パラメータを取得。

        Returns
        -------
            トラップ出現調整パラメータ

        """
        return {
            "base_count": self.base_trap_count,
            "count_modifier": self.difficulty_modifier,
            "hidden_trap_chance": self._get_hidden_trap_chance(),
            "magical_trap_chance": self._get_magical_trap_chance(),
            "trap_damage_modifier": self._get_trap_damage_modifier(),
            "trap_detection_difficulty": self._get_trap_detection_difficulty(),
        }

    def _get_hidden_trap_chance(self) -> float:
        """隠しトラップの出現確率を取得。"""
        if self.floor <= 3:
            return 0.3  # 初期階層では少なめ

        base_chance = 0.5  # 50%
        tier_bonus = self.difficulty_tier * 0.1  # ティアごとに10%増加

        return min(base_chance + tier_bonus, 0.9)  # 最大90%

    def _get_magical_trap_chance(self) -> float:
        """魔法トラップの出現確率を取得。"""
        if self.floor <= 5:
            return 0.0  # 初期階層では魔法トラップなし

        base_chance = 0.2  # 20%
        tier_bonus = self.difficulty_tier * 0.1  # ティアごとに10%増加

        return min(base_chance + tier_bonus, 0.6)  # 最大60%

    def _get_trap_damage_modifier(self) -> float:
        """トラップダメージ修正値を取得。"""
        base_modifier = 1.0
        tier_bonus = self.difficulty_tier * 0.2  # ティアごとに20%増加

        return min(base_modifier + tier_bonus, 2.0)  # 最大200%

    def _get_trap_detection_difficulty(self) -> int:
        """トラップ探知難易度を取得。"""
        base_difficulty = 10  # 基本難易度
        tier_bonus = self.difficulty_tier * 2  # ティアごとに+2

        return min(base_difficulty + tier_bonus, 20)  # 最大20

    def get_environmental_adjustments(self) -> dict[str, Any]:
        """
        環境調整パラメータを取得。

        Returns
        -------
            環境調整パラメータ

        """
        return {
            "darkness_chance": self._get_darkness_chance(),
            "confusion_chance": self._get_confusion_chance(),
            "teleporter_chance": self._get_teleporter_chance(),
            "illusion_chance": self._get_illusion_chance(),
            "poison_gas_chance": self._get_poison_gas_chance(),
        }

    def _get_darkness_chance(self) -> float:
        """暗闇エリアの出現確率を取得。"""
        if self.floor <= 3:
            return 0.0  # 初期階層では暗闇なし

        base_chance = 0.1  # 10%
        tier_bonus = self.difficulty_tier * 0.05  # ティアごとに5%増加

        return min(base_chance + tier_bonus, 0.3)  # 最大30%

    def _get_confusion_chance(self) -> float:
        """混乱エリアの出現確率を取得。"""
        if self.floor <= 5:
            return 0.0  # 初期階層では混乱なし

        base_chance = 0.05  # 5%
        tier_bonus = self.difficulty_tier * 0.02  # ティアごとに2%増加

        return min(base_chance + tier_bonus, 0.15)  # 最大15%

    def _get_teleporter_chance(self) -> float:
        """テレポーターの出現確率を取得。"""
        if self.floor <= 7:
            return 0.0  # 初期階層ではテレポーターなし

        base_chance = 0.03  # 3%
        tier_bonus = self.difficulty_tier * 0.02  # ティアごとに2%増加

        return min(base_chance + tier_bonus, 0.12)  # 最大12%

    def _get_illusion_chance(self) -> float:
        """幻覚エリアの出現確率を取得。"""
        if self.floor <= 10:
            return 0.0  # 中盤以降から出現

        base_chance = 0.02  # 2%
        tier_bonus = self.difficulty_tier * 0.01  # ティアごとに1%増加

        return min(base_chance + tier_bonus, 0.08)  # 最大8%

    def _get_poison_gas_chance(self) -> float:
        """毒ガスエリアの出現確率を取得。"""
        if self.floor <= 8:
            return 0.0  # 中盤以降から出現

        base_chance = 0.03  # 3%
        tier_bonus = self.difficulty_tier * 0.02  # ティアごとに2%増加

        return min(base_chance + tier_bonus, 0.12)  # 最大12%

    def get_special_events_adjustments(self) -> dict[str, Any]:
        """
        特殊イベント調整パラメータを取得。

        Returns
        -------
            特殊イベント調整パラメータ

        """
        return {
            "treasure_room_chance": self._get_treasure_room_chance(),
            "monster_house_chance": self._get_monster_house_chance(),
            "puzzle_room_chance": self._get_puzzle_room_chance(),
            "shrine_chance": self._get_shrine_chance(),
            "vault_chance": self._get_vault_chance(),
        }

    def _get_treasure_room_chance(self) -> float:
        """宝物庫の出現確率を取得。"""
        if self.floor <= 5:
            return 0.01  # 初期階層では稀

        base_chance = 0.05  # 5%
        tier_bonus = self.difficulty_tier * 0.02  # ティアごとに2%増加

        return min(base_chance + tier_bonus, 0.15)  # 最大15%

    def _get_monster_house_chance(self) -> float:
        """モンスターハウスの出現確率を取得。"""
        if self.floor <= 3:
            return 0.0  # 初期階層ではモンスターハウスなし

        base_chance = 0.03  # 3%
        tier_bonus = self.difficulty_tier * 0.02  # ティアごとに2%増加

        return min(base_chance + tier_bonus, 0.12)  # 最大12%

    def _get_puzzle_room_chance(self) -> float:
        """パズル部屋の出現確率を取得。"""
        if self.floor <= 7:
            return 0.0  # 中盤以降から出現

        base_chance = 0.02  # 2%
        tier_bonus = self.difficulty_tier * 0.01  # ティアごとに1%増加

        return min(base_chance + tier_bonus, 0.08)  # 最大8%

    def _get_shrine_chance(self) -> float:
        """祠の出現確率を取得。"""
        if self.floor <= 10:
            return 0.0  # 中盤以降から出現

        base_chance = 0.03  # 3%
        tier_bonus = self.difficulty_tier * 0.01  # ティアごとに1%増加

        return min(base_chance + tier_bonus, 0.08)  # 最大8%

    def _get_vault_chance(self) -> float:
        """金庫室の出現確率を取得。"""
        if self.floor <= 12:
            return 0.0  # 終盤以降から出現

        base_chance = 0.02  # 2%
        tier_bonus = self.difficulty_tier * 0.01  # ティアごとに1%増加

        return min(base_chance + tier_bonus, 0.06)  # 最大6%

    def get_comprehensive_difficulty_report(self) -> dict[str, Any]:
        """
        包括的な難易度レポートを取得。

        Returns
        -------
            包括的な難易度レポート

        """
        return {
            "floor": self.floor,
            "difficulty_tier": self.difficulty_tier,
            "difficulty_modifier": self.difficulty_modifier,
            "tier_description": self._get_tier_description(),
            "monster_adjustments": self.get_monster_spawn_adjustments(),
            "item_adjustments": self.get_item_spawn_adjustments(),
            "trap_adjustments": self.get_trap_spawn_adjustments(),
            "environmental_adjustments": self.get_environmental_adjustments(),
            "special_events_adjustments": self.get_special_events_adjustments(),
            "survival_tips": self._get_survival_tips(),
            "challenge_rating": self._get_challenge_rating(),
        }

    def _get_tier_description(self) -> str:
        """難易度ティアの説明を取得。"""
        descriptions = {
            1: "初心者向け - 基本的な敵と安全な環境",
            2: "初級者向け - 少し挑戦的な敵と基本的なトラップ",
            3: "中級者向け - 多様な敵と複雑なトラップ",
            4: "上級者向け - 強力な敵と危険な環境",
            5: "エキスパート向け - 最強の敵と極限の挑戦",
        }

        return descriptions.get(self.difficulty_tier, "不明な難易度")

    def _get_survival_tips(self) -> list[str]:
        """階層別の生存のコツを取得。"""
        tips = []

        if self.difficulty_tier == 1:
            tips.extend(
                [
                    "基本的な戦闘とアイテム管理を覚える",
                    "食料を大切に管理する",
                    "隠しドアやトラップを探索する",
                ]
            )
        elif self.difficulty_tier == 2:
            tips.extend(
                [
                    "装備のアップグレードを怠らない",
                    "ポーションと巻物を効果的に使う",
                    "敵の行動パターンを学習する",
                ]
            )
        elif self.difficulty_tier == 3:
            tips.extend(
                [
                    "複数の敵との戦闘に備える",
                    "トラップの探知と解除を身につける",
                    "アイテムの識別を積極的に行う",
                ]
            )
        elif self.difficulty_tier == 4:
            tips.extend(
                [
                    "強力な敵に対する戦略を立てる",
                    "環境を利用した戦術を使う",
                    "リソース管理を慎重に行う",
                ]
            )
        else:  # ティア5
            tips.extend(
                [
                    "最強の装備と戦略が必要",
                    "全てのリソースを最大限活用",
                    "死を覚悟した最終決戦",
                ]
            )

        return tips

    def _get_challenge_rating(self) -> str:
        """挑戦度レーティングを取得。"""
        rating = self.difficulty_modifier

        if rating <= 0.7:
            return "やさしい"
        if rating <= 1.0:
            return "普通"
        if rating <= 1.3:
            return "やや難しい"
        if rating <= 1.6:
            return "難しい"
        if rating <= 1.9:
            return "とても難しい"
        return "極限"
