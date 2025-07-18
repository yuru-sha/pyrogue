"""
強化アイテム生成システム。

既存のアイテム生成システムを拡張し、
階層難易度管理システムと統合してより戦略的な
アイテム配置を実現します。
"""

from __future__ import annotations

import random
from typing import Any

import numpy as np

from pyrogue.core.managers.floor_difficulty_manager import FloorDifficultyManager
from pyrogue.map.dungeon import Room
from pyrogue.utils import game_logger

from .amulet import AmuletOfYendor
from .effects import (
    ENCHANT_ARMOR,
    ENCHANT_WEAPON,
    IDENTIFY,
    LIGHT,
    MAGIC_MAPPING,
    REMOVE_CURSE,
    TELEPORT,
    Effect,
    HealingEffect,
)
from .item import Armor, Food, Gold, Item, Potion, Ring, Scroll, Wand, Weapon
from .item_types import (
    ARMORS,
    FOODS,
    POTIONS,
    RINGS,
    SCROLLS,
    WANDS,
    WEAPONS,
    get_available_items,
    get_gold_amount,
)


class EnhancedItemSpawner:
    """
    強化アイテム生成クラス。

    階層難易度管理システムと統合し、
    動的なアイテム配置とバランス調整を行います。
    """

    def __init__(self, floor: int) -> None:
        """
        強化アイテム生成器を初期化。

        Args:
        ----
            floor: 対象となる階層

        """
        self.floor = floor
        self.items: list[Item] = []
        self.occupied_positions: set[tuple[int, int]] = set()

        # 階層難易度管理システムを初期化
        self.difficulty_manager = FloorDifficultyManager(floor)
        self.item_adjustments = self.difficulty_manager.get_item_spawn_adjustments()

        # 統計情報
        self.spawn_statistics: dict[str, Any] = {
            "total_spawned": 0,
            "by_type": {},
            "rare_items": 0,
            "cursed_items": 0,
            "blessed_items": 0,
            "enchanted_items": 0,
        }

        game_logger.debug(f"EnhancedItemSpawner initialized for floor {floor}")

    def spawn_items(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """
        強化されたアイテム配置システム。

        Args:
        ----
            dungeon_tiles: ダンジョンのタイル配列
            rooms: ダンジョンの部屋リスト

        """
        self.items.clear()
        self.occupied_positions.clear()
        self._reset_statistics()

        # 調整されたアイテム数を取得
        base_count = self.item_adjustments["base_count"]
        count_modifier = self.item_adjustments["count_modifier"]
        total_items = int(base_count * count_modifier)

        # 特別なアイテムの配置
        self._spawn_special_items(dungeon_tiles, rooms)

        # 通常アイテムの配置
        self._spawn_regular_items(dungeon_tiles, rooms, total_items)

        # 戦略的アイテムの配置
        self._spawn_strategic_items(dungeon_tiles, rooms)

        # 統計情報の更新
        self._update_statistics()

        game_logger.info(f"Enhanced item spawning completed: {len(self.items)} items on floor {self.floor}")

    def _spawn_special_items(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """特別なアイテムの配置。"""
        # イェンダーのアミュレット（26階層）
        if self.floor == 26:
            position = self._find_strategic_position(dungeon_tiles, rooms, "center")
            if position:
                x, y = position
                amulet = AmuletOfYendor(x=x, y=y)
                self.items.append(amulet)
                self.occupied_positions.add((x, y))
                game_logger.info(f"Amulet of Yendor placed at ({x}, {y})")

    def _spawn_regular_items(self, dungeon_tiles: np.ndarray, rooms: list[Room], total_items: int) -> None:
        """通常アイテムの配置。"""
        for _ in range(total_items):
            # 配置位置の決定
            position = self._find_optimal_position(dungeon_tiles, rooms)
            if not position:
                continue

            x, y = position

            # アイテムタイプの決定
            item_type = self._determine_item_type()

            # アイテムの生成
            item = self._create_enhanced_item(item_type)
            if item:
                item.x = x
                item.y = y
                self.items.append(item)
                self.occupied_positions.add((x, y))

                # 統計情報の更新
                self._update_item_statistics(item, item_type)

    def _spawn_strategic_items(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """戦略的アイテムの配置。"""
        # 食料不足対策
        if self.floor >= 10:
            self._spawn_emergency_food(dungeon_tiles, rooms)

        # 識別支援
        if self.floor >= 5:
            self._spawn_identification_items(dungeon_tiles, rooms)

        # 戦闘支援
        if self.floor >= 15:
            self._spawn_combat_items(dungeon_tiles, rooms)

    def _determine_item_type(self) -> str:
        """アイテムタイプの決定。"""
        # 基本重み
        base_weights = {
            "weapon": 15,
            "armor": 15,
            "ring": 10,
            "scroll": 25,
            "potion": 25,
            "food": 20,
            "wand": 10,
            "gold": 35,
        }

        # 階層別調整
        adjusted_weights = self._adjust_item_weights(base_weights)

        # 重み付き抽選
        item_types = list(adjusted_weights.keys())
        weights = list(adjusted_weights.values())

        return random.choices(item_types, weights=weights, k=1)[0]

    def _adjust_item_weights(self, base_weights: dict[str, int]) -> dict[str, int]:
        """アイテム重みの調整。"""
        adjusted = base_weights.copy()

        # 食料重み修正
        food_modifier = self.item_adjustments["food_weight_modifier"]
        adjusted["food"] = int(adjusted["food"] * food_modifier)

        # 金貨重み修正
        gold_modifier = self.item_adjustments["gold_amount_modifier"]
        adjusted["gold"] = int(adjusted["gold"] * gold_modifier)

        # 階層別特殊調整
        if self.floor <= 5:
            # 初期階層: 装備重視
            adjusted["weapon"] *= 2
            adjusted["armor"] *= 2
            adjusted["ring"] = max(adjusted["ring"] // 2, 1)
        elif self.floor <= 10:
            # 中盤: バランス
            pass
        elif self.floor <= 20:
            # 終盤: 消耗品重視
            adjusted["potion"] = int(adjusted["potion"] * 1.5)
            adjusted["scroll"] = int(adjusted["scroll"] * 1.5)
        else:
            # 最深部: 全て重要
            for key in adjusted:
                adjusted[key] = int(adjusted[key] * 1.2)

        return adjusted

    def _create_enhanced_item(self, item_type: str) -> Item | None:
        """強化されたアイテム作成。"""
        if item_type == "weapon":
            return self._create_enhanced_weapon()
        if item_type == "armor":
            return self._create_enhanced_armor()
        if item_type == "ring":
            return self._create_enhanced_ring()
        if item_type == "scroll":
            return self._create_enhanced_scroll()
        if item_type == "potion":
            return self._create_enhanced_potion()
        if item_type == "food":
            return self._create_enhanced_food()
        if item_type == "wand":
            return self._create_enhanced_wand()
        # gold
        return self._create_enhanced_gold()

    def _create_enhanced_weapon(self) -> Weapon | None:
        """強化された武器作成。"""
        available = get_available_items(self.floor, WEAPONS)
        if not available:
            return None

        # レア武器の判定
        is_rare = random.random() < self.item_adjustments["rare_item_chance"]

        if is_rare:
            # 高品質な武器を選択
            weapon_type = max(available, key=lambda w: w.base_damage)
        else:
            # 通常の重み付き抽選
            weapon_type = random.choices(available, weights=[w.spawn_weight for w in available], k=1)[0]

        # ボーナス値の計算
        bonus = self._calculate_enhanced_bonus(weapon_type.bonus_range, is_rare)

        # 武器の作成
        weapon = Weapon(0, 0, weapon_type.name, bonus)

        # 特殊状態の適用
        self._apply_special_states(weapon)

        return weapon

    def _create_enhanced_armor(self) -> Armor | None:
        """強化された防具作成。"""
        available = get_available_items(self.floor, ARMORS)
        if not available:
            return None

        # レア防具の判定
        is_rare = random.random() < self.item_adjustments["rare_item_chance"]

        if is_rare:
            # 高品質な防具を選択
            armor_type = max(available, key=lambda a: a.base_defense)
        else:
            # 通常の重み付き抽選
            armor_type = random.choices(available, weights=[a.spawn_weight for a in available], k=1)[0]

        # ボーナス値の計算
        bonus = self._calculate_enhanced_bonus(armor_type.bonus_range, is_rare)

        # 防具の作成
        armor = Armor(0, 0, armor_type.name, bonus)

        # 特殊状態の適用
        self._apply_special_states(armor)

        return armor

    def _create_enhanced_ring(self) -> Ring | None:
        """強化された指輪作成。"""
        available = get_available_items(self.floor, RINGS)
        if not available:
            return None

        # レア指輪の判定
        is_rare = random.random() < self.item_adjustments["rare_item_chance"]

        if is_rare:
            # 高品質な指輪を選択
            ring_type = max(available, key=lambda r: r.power_range[1])
        else:
            # 通常の重み付き抽選
            ring_type = random.choices(available, weights=[r.spawn_weight for r in available], k=1)[0]

        # パワー値の計算
        power = self._calculate_enhanced_power(ring_type.power_range, is_rare)

        # 指輪の作成
        ring = Ring(0, 0, ring_type.name, ring_type.effect, power)

        # 特殊状態の適用
        self._apply_special_states(ring)

        return ring

    def _create_enhanced_scroll(self) -> Scroll | None:
        """強化された巻物作成。"""
        available = get_available_items(self.floor, SCROLLS)
        if not available:
            return None

        # 戦略的巻物選択
        scroll_type = self._select_strategic_scroll(available)

        # 巻物の作成
        effect = self._get_scroll_effect(scroll_type.effect)
        scroll = Scroll(0, 0, scroll_type.name, effect)

        # 特殊状態の適用
        self._apply_special_states(scroll)

        return scroll

    def _create_enhanced_potion(self) -> Potion | None:
        """強化されたポーション作成。"""
        available = get_available_items(self.floor, POTIONS)
        if not available:
            return None

        # 戦略的ポーション選択
        potion_type = self._select_strategic_potion(available)

        # ポーションの作成
        effect = self._get_potion_effect(potion_type.effect, potion_type.power_range)
        potion = Potion(0, 0, potion_type.name, effect)

        # 特殊状態の適用
        self._apply_special_states(potion)

        return potion

    def _create_enhanced_food(self) -> Food | None:
        """強化された食料作成。"""
        available = get_available_items(self.floor, FOODS)
        if not available:
            return None

        # 食料重要度に基づく選択
        if self.floor >= 15:
            # 深い階層では高栄養食料を優先
            food_type = max(available, key=lambda f: f.nutrition)
        else:
            # 通常の重み付き抽選
            food_type = random.choices(available, weights=[f.spawn_weight for f in available], k=1)[0]

        # 食料の作成
        effect = self._get_food_effect(food_type.nutrition)
        food = Food(0, 0, food_type.name, effect)

        return food

    def _create_enhanced_wand(self) -> Wand | None:
        """強化されたワンド作成。"""
        available = get_available_items(self.floor, WANDS)
        if not available:
            return None

        # レアワンドの判定
        is_rare = random.random() < self.item_adjustments["rare_item_chance"]

        if is_rare:
            # 高品質なワンドを選択
            wand_type = max(available, key=lambda w: w.charges_range[1])
        else:
            # 通常の重み付き抽選
            wand_type = random.choices(available, weights=[w.spawn_weight for w in available], k=1)[0]

        # チャージ数の計算
        charges = self._calculate_enhanced_charges(wand_type.charges_range, is_rare)

        # ワンドの作成
        effect = self._get_wand_effect(wand_type.effect)
        wand = Wand(0, 0, wand_type.name, effect, charges)

        # 特殊状態の適用
        self._apply_special_states(wand)

        return wand

    def _create_enhanced_gold(self) -> Gold:
        """強化された金貨作成。"""
        base_amount = get_gold_amount(self.floor)
        gold_modifier = self.item_adjustments["gold_amount_modifier"]

        # 調整された金額
        adjusted_amount = int(base_amount * gold_modifier)

        # ランダムな変動
        variance = random.randint(-20, 20)  # ±20%の変動
        final_amount = max(1, adjusted_amount + (adjusted_amount * variance // 100))

        return Gold(0, 0, final_amount)

    def _calculate_enhanced_bonus(self, bonus_range: tuple[int, int], is_rare: bool) -> int:
        """強化されたボーナス値計算。"""
        min_bonus, max_bonus = bonus_range

        if is_rare:
            # レアアイテムは高いボーナス
            bonus = random.randint(max_bonus, max_bonus + 2)
        else:
            # 通常のボーナス
            bonus = random.randint(min_bonus, max_bonus)

        # エンチャントボーナスの適用
        enchant_bonus = self.item_adjustments["enchantment_bonus"]
        if random.random() < enchant_bonus:
            bonus += random.randint(1, 3)

        return bonus

    def _calculate_enhanced_power(self, power_range: tuple[int, int], is_rare: bool) -> int:
        """強化されたパワー値計算。"""
        min_power, max_power = power_range

        if is_rare:
            # レアアイテムは高いパワー
            power = random.randint(max_power, max_power + 2)
        else:
            # 通常のパワー
            power = random.randint(min_power, max_power)

        return power

    def _calculate_enhanced_charges(self, charges_range: tuple[int, int], is_rare: bool) -> int:
        """強化されたチャージ数計算。"""
        min_charges, max_charges = charges_range

        if is_rare:
            # レアワンドは多いチャージ
            charges = random.randint(max_charges, max_charges + 3)
        else:
            # 通常のチャージ
            charges = random.randint(min_charges, max_charges)

        return charges

    def _apply_special_states(self, item: Item) -> None:
        """特殊状態の適用。"""
        # 呪い状態の適用
        if random.random() < self.item_adjustments["cursed_item_chance"]:
            item.cursed = True
            self.spawn_statistics["cursed_items"] += 1

        # 祝福状態の適用
        elif random.random() < self.item_adjustments["blessed_item_chance"]:
            item.blessed = True
            self.spawn_statistics["blessed_items"] += 1

    def _select_strategic_scroll(self, available: list[Any]) -> Any:
        """戦略的巻物選択。"""
        # 階層に応じた戦略的選択
        if self.floor >= 15:
            # 深い階層では識別と魔法地図を優先
            priority_effects = ["identify", "magic_mapping", "remove_curse"]
            for scroll_type in available:
                if scroll_type.effect in priority_effects:
                    return scroll_type

        # 通常の重み付き抽選
        return random.choices(available, weights=[s.spawn_weight for s in available], k=1)[0]

    def _select_strategic_potion(self, available: list[Any]) -> Any:
        """戦略的ポーション選択。"""
        # 階層に応じた戦略的選択
        if self.floor >= 10:
            # 中盤以降では回復ポーションを優先
            priority_effects = ["healing", "extra_healing"]
            for potion_type in available:
                if potion_type.effect in priority_effects:
                    return potion_type

        # 通常の重み付き抽選
        return random.choices(available, weights=[p.spawn_weight for p in available], k=1)[0]

    def _find_optimal_position(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> tuple[int, int] | None:
        """最適な配置位置を検索。"""
        # 戦略的位置の候補
        strategic_positions = [
            self._find_strategic_position(dungeon_tiles, rooms, "corner"),
            self._find_strategic_position(dungeon_tiles, rooms, "edge"),
            self._find_strategic_position(dungeon_tiles, rooms, "center"),
        ]

        # 有効な位置から選択
        valid_positions = [pos for pos in strategic_positions if pos is not None]

        if valid_positions:
            return random.choice(valid_positions)

        # フォールバック: 通常の位置検索
        return self._find_valid_position_anywhere(dungeon_tiles)

    def _find_strategic_position(
        self, dungeon_tiles: np.ndarray, rooms: list[Room], strategy: str
    ) -> tuple[int, int] | None:
        """戦略的位置の検索。"""
        if not rooms:
            return self._find_valid_position_anywhere(dungeon_tiles)

        if strategy == "corner":
            # 部屋の角に配置
            room = random.choice(rooms)
            corners = [
                (room.x + 1, room.y + 1),
                (room.x + room.width - 2, room.y + 1),
                (room.x + 1, room.y + room.height - 2),
                (room.x + room.width - 2, room.y + room.height - 2),
            ]

            for x, y in corners:
                if self._is_valid_position(dungeon_tiles, x, y):
                    return (x, y)

        elif strategy == "edge":
            # 部屋の端に配置
            room = random.choice(rooms)
            edges = []

            # 上下の端
            for x in range(room.x + 1, room.x + room.width - 1):
                edges.extend([(x, room.y + 1), (x, room.y + room.height - 2)])

            # 左右の端
            for y in range(room.y + 1, room.y + room.height - 1):
                edges.extend([(room.x + 1, y), (room.x + room.width - 2, y)])

            random.shuffle(edges)
            for x, y in edges:
                if self._is_valid_position(dungeon_tiles, x, y):
                    return (x, y)

        elif strategy == "center":
            # 部屋の中央に配置
            room = random.choice(rooms)
            center_x = room.x + room.width // 2
            center_y = room.y + room.height // 2

            if self._is_valid_position(dungeon_tiles, center_x, center_y):
                return (center_x, center_y)

        return None

    def _find_valid_position_anywhere(self, dungeon_tiles: np.ndarray) -> tuple[int, int] | None:
        """ダンジョン全体での有効位置検索。"""
        height, width = dungeon_tiles.shape

        for _ in range(50):
            x = random.randint(1, width - 2)
            y = random.randint(1, height - 2)

            if self._is_valid_position(dungeon_tiles, x, y):
                return (x, y)

        return None

    def _is_valid_position(self, dungeon_tiles: np.ndarray, x: int, y: int) -> bool:
        """位置の有効性チェック。"""
        if not (0 <= x < dungeon_tiles.shape[1] and 0 <= y < dungeon_tiles.shape[0]):
            return False

        return dungeon_tiles[y, x].walkable and (x, y) not in self.occupied_positions

    def _spawn_emergency_food(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """緊急食料の配置。"""
        # 深い階層では追加の食料を配置
        if self.floor >= 15:
            emergency_food_count = 2
        else:
            emergency_food_count = 1

        for _ in range(emergency_food_count):
            position = self._find_strategic_position(dungeon_tiles, rooms, "corner")
            if position:
                x, y = position
                food = self._create_enhanced_food()
                if food:
                    food.x = x
                    food.y = y
                    self.items.append(food)
                    self.occupied_positions.add((x, y))

    def _spawn_identification_items(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """識別アイテムの配置。"""
        # 識別巻物の追加配置
        if random.random() < 0.3:  # 30%の確率
            position = self._find_strategic_position(dungeon_tiles, rooms, "edge")
            if position:
                x, y = position
                scroll = Scroll(0, 0, "Scroll of Identify", IDENTIFY)
                scroll.x = x
                scroll.y = y
                self.items.append(scroll)
                self.occupied_positions.add((x, y))

    def _spawn_combat_items(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """戦闘アイテムの配置。"""
        # 回復ポーションの追加配置
        if random.random() < 0.4:  # 40%の確率
            position = self._find_strategic_position(dungeon_tiles, rooms, "center")
            if position:
                x, y = position
                potion = Potion(0, 0, "Potion of Healing", HealingEffect(25))
                potion.x = x
                potion.y = y
                self.items.append(potion)
                self.occupied_positions.add((x, y))

    def _reset_statistics(self) -> None:
        """統計情報のリセット。"""
        self.spawn_statistics = {
            "total_spawned": 0,
            "by_type": {},
            "rare_items": 0,
            "cursed_items": 0,
            "blessed_items": 0,
            "enchanted_items": 0,
        }

    def _update_item_statistics(self, item: Item, item_type: str) -> None:
        """アイテム統計の更新。"""
        self.spawn_statistics["total_spawned"] += 1

        if item_type not in self.spawn_statistics["by_type"]:
            self.spawn_statistics["by_type"][item_type] = 0
        self.spawn_statistics["by_type"][item_type] += 1

        # レアアイテムの判定（簡易版）
        if (hasattr(item, "bonus") and item.bonus > 2) or (hasattr(item, "power") and item.power > 3):
            self.spawn_statistics["rare_items"] += 1

    def _update_statistics(self) -> None:
        """統計情報の最終更新。"""
        game_logger.debug(f"Item spawn statistics for floor {self.floor}: {self.spawn_statistics}")

    # 既存のメソッドをそのまま使用
    def _get_scroll_effect(self, effect_name: str) -> Effect:
        """Map effect name to Effect object for scrolls."""
        effect_map = {
            "identify": IDENTIFY,
            "light": LIGHT,
            "remove_curse": REMOVE_CURSE,
            "enchant_weapon": ENCHANT_WEAPON,
            "enchant_armor": ENCHANT_ARMOR,
            "teleport": TELEPORT,
            "magic_mapping": MAGIC_MAPPING,
        }
        return effect_map.get(effect_name, IDENTIFY)

    def _get_potion_effect(self, effect_name: str, power_range: tuple[int, int]) -> Effect:
        """Map effect name to Effect object for potions."""
        power = random.randint(*power_range)

        if effect_name == "healing" or effect_name == "extra_healing":
            return HealingEffect(power)
        if effect_name == "poison":
            from .effects import PoisonPotionEffect

            return PoisonPotionEffect(duration=power, damage=2)
        if effect_name == "paralysis":
            from .effects import ParalysisPotionEffect

            return ParalysisPotionEffect(duration=power)
        if effect_name == "confusion":
            from .effects import ConfusionPotionEffect

            return ConfusionPotionEffect(duration=power)
        if effect_name in ["strength", "restore_strength", "haste_self", "see_invisible"]:
            return HealingEffect(power)

        return HealingEffect(power)

    def _get_food_effect(self, nutrition: int) -> Effect:
        """Map nutrition value to Effect object for food."""
        from .effects import NutritionEffect

        hunger_value = nutrition // 36
        return NutritionEffect(hunger_value)

    def _get_wand_effect(self, effect_name: str) -> Effect:
        """Map effect name to Effect object for wands."""
        from .effects import (
            LIGHT_WAND,
            LIGHTNING_WAND,
            MAGIC_MISSILE_WAND,
            NOTHING_WAND,
        )

        effect_map = {
            "magic_missile": MAGIC_MISSILE_WAND,
            "lightning": LIGHTNING_WAND,
            "light": LIGHT_WAND,
            "nothing": NOTHING_WAND,
            "fire": NOTHING_WAND,
            "cold": NOTHING_WAND,
            "polymorph": NOTHING_WAND,
            "teleport_monster": NOTHING_WAND,
            "slow_monster": NOTHING_WAND,
            "haste_monster": NOTHING_WAND,
            "sleep": NOTHING_WAND,
            "drain_life": NOTHING_WAND,
        }
        return effect_map.get(effect_name, NOTHING_WAND)

    def get_spawn_statistics(self) -> dict[str, Any]:
        """生成統計情報を取得。"""
        return {
            "floor": self.floor,
            "difficulty_tier": self.difficulty_manager.difficulty_tier,
            "spawn_statistics": self.spawn_statistics,
            "adjustments_applied": self.item_adjustments,
        }

    # 既存の互換性メソッド
    def get_item_at(self, x: int, y: int) -> Item | None:
        """指定された位置にあるアイテムを取得。"""
        for item in self.items:
            if item.x == x and item.y == y:
                return item
        return None

    def remove_item(self, item: Item) -> None:
        """アイテムを削除。"""
        if item in self.items:
            self.items.remove(item)
            pos = (item.x, item.y)
            if pos in self.occupied_positions:
                self.occupied_positions.remove(pos)

    def add_item(self, item: Item) -> bool:
        """アイテムを追加。"""
        pos = (item.x, item.y)
        self.items.append(item)
        self.occupied_positions.add(pos)
        return True
