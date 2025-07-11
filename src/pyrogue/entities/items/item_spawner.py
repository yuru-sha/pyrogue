"""
アイテム生成モジュール。

このモジュールは、ダンジョン内のアイテムの配置と生成を管理します。
階層に応じたアイテムの種類、数量、品質を調整し、
ゲームバランスと探索の楽しさを両立させます。

Example:
-------
    >>> spawner = ItemSpawner(floor=1)
    >>> spawner.spawn_items(dungeon_tiles, rooms)
    >>> item = spawner.get_item_at(10, 5)

"""

from __future__ import annotations

import random

import numpy as np
from pyrogue.map.dungeon import Room

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
from .item import Armor, Food, Gold, Item, Potion, Ring, Scroll, Weapon
from .item_types import (
    ARMORS,
    FOODS,
    POTIONS,
    RINGS,
    SCROLLS,
    WEAPONS,
    get_available_items,
    get_gold_amount,
    get_item_spawn_count,
)


class ItemSpawner:
    """
    アイテムの生成と管理を行うクラス。

    ダンジョンの各階層に適切なアイテムを配置し、
    アイテムの重複配置を防ぎ、階層に応じた品質調整を行います。
    イェンダーのアミュレットなどの特別なアイテムも管理します。

    Attributes
    ----------
        floor: 現在の階層
        items: 配置されたアイテムのリスト
        occupied_positions: アイテムが配置されている座標のセット

    """

    def __init__(self, floor: int) -> None:
        """
        アイテムスポナーを初期化。

        Args:
        ----
            floor: 対象となる階層

        """
        self.floor = floor
        self.items: list[Item] = []
        self.occupied_positions: set[tuple[int, int]] = set()

    def spawn_items(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """
        ダンジョン内にアイテムを配置。

        階層に応じたアイテム数とタイプを決定し、部屋内の適切な位置に配置します。
        26階層では特別にイェンダーのアミュレットを配置します。

        Args:
        ----
            dungeon_tiles: ダンジョンのタイル配列
            rooms: ダンジョンの部屋リスト

        """
        self.items.clear()
        self.occupied_positions.clear()  # 位置情報もクリア

        # Get total number of items to spawn on this floor
        total_items = get_item_spawn_count(self.floor)

        # Spawn Amulet of Yendor on floor 26
        if self.floor == 26:
            if not rooms:
                x, y = self._find_valid_position_anywhere(dungeon_tiles)
            else:
                room = random.choice(rooms)
                x, y = self._find_valid_position(dungeon_tiles, room)

            if x is not None and y is not None:
                amulet = AmuletOfYendor(x=x, y=y)
                self.items.append(amulet)
                self.occupied_positions.add((x, y))  # 位置を追加

        # Spawn regular items
        for _ in range(total_items):
            # 迷路階層など部屋がない場合は床タイルから直接選択
            if not rooms:
                x, y = self._find_valid_position_anywhere(dungeon_tiles)
            else:
                room = random.choice(rooms)
                x, y = self._find_valid_position(dungeon_tiles, room)

            if x is None or y is None:
                continue

            # Determine item type
            item_type = random.choices(
                ["weapon", "armor", "ring", "scroll", "potion", "food", "gold"],
                weights=[15, 15, 10, 25, 25, 10, 35],
                k=1,
            )[0]

            item = None
            if item_type == "weapon":
                item = self._create_weapon()
            elif item_type == "armor":
                item = self._create_armor()
            elif item_type == "ring":
                item = self._create_ring()
            elif item_type == "scroll":
                item = self._create_scroll()
            elif item_type == "potion":
                item = self._create_potion()
            elif item_type == "food":
                item = self._create_food()
            else:  # gold
                item = self._create_gold()

            if item:
                item.x = x
                item.y = y
                self.items.append(item)
                self.occupied_positions.add((x, y))  # 位置を追加

    def _find_valid_position(
        self, dungeon_tiles: np.ndarray, room: Room
    ) -> tuple[int | None, int | None]:
        """
        指定された部屋内でアイテムの有効な配置位置を検索。

        壁を避け、他のアイテムと重複しない位置を最大10回試行して見つけます。

        Args:
        ----
            dungeon_tiles: ダンジョンのタイル配列
            room: 対象の部屋

        Returns:
        -------
            有効な位置の(x, y)座標。見つからない場合は(None, None)

        """
        # Get room dimensions
        x1, y1 = room.x, room.y
        width = room.width
        height = room.height

        # Try 10 times to find a valid position
        for _ in range(10):
            x = x1 + random.randint(1, width - 2)  # Avoid walls
            y = y1 + random.randint(1, height - 2)  # Avoid walls

            # Check if position is valid
            if dungeon_tiles[y, x].walkable and not self._is_position_occupied(x, y):
                return x, y

        return None, None

    def _find_valid_position_anywhere(
        self, dungeon_tiles: np.ndarray
    ) -> tuple[int | None, int | None]:
        """
        ダンジョン全体でアイテムの有効な配置位置を検索。

        迷路階層など部屋がない場合に使用します。

        Args:
        ----
            dungeon_tiles: ダンジョンのタイル配列

        Returns:
        -------
            有効な位置の(x, y)座標。見つからない場合は(None, None)
        """
        height, width = dungeon_tiles.shape

        # 最大50回試行して有効な位置を探す
        for _ in range(50):
            x = random.randint(1, width - 2)
            y = random.randint(1, height - 2)

            # 歩行可能で占有されていない位置をチェック
            if dungeon_tiles[y, x].walkable and not self._is_position_occupied(x, y):
                return x, y

        return None, None

    def _is_position_occupied(self, x: int, y: int) -> bool:
        """
        指定された位置がアイテムによって占有されているかチェック。

        Args:
        ----
            x: X座標
            y: Y座標

        Returns:
        -------
            占有されている場合True

        """
        return any(item.x == x and item.y == y for item in self.items)

    def _create_weapon(self) -> Weapon | None:
        """
        ランダムな武器を生成。

        現在の階層で利用可能な武器タイプから重み付き抽選で選択し、
        ボーナス値もランダムに決定します。

        Returns
        -------
            生成された武器。利用可能な武器がない場合はNone

        """
        available = get_available_items(self.floor, WEAPONS)
        if not available:
            return None

        weapon_type = random.choices(
            available, weights=[w.spawn_weight for w in available], k=1
        )[0]
        bonus = random.randint(*weapon_type.bonus_range)
        return Weapon(0, 0, weapon_type.name, bonus)

    def _create_armor(self) -> Armor | None:
        """
        ランダムな防具を生成。

        現在の階層で利用可能な防具タイプから重み付き抽選で選択し、
        ボーナス値もランダムに決定します。

        Returns
        -------
            生成された防具。利用可能な防具がない場合はNone

        """
        available = get_available_items(self.floor, ARMORS)
        if not available:
            return None

        armor_type = random.choices(
            available, weights=[a.spawn_weight for a in available], k=1
        )[0]
        bonus = random.randint(*armor_type.bonus_range)
        return Armor(0, 0, armor_type.name, bonus)

    def _create_ring(self) -> Ring | None:
        """
        ランダムな指輪を生成。

        現在の階層で利用可能な指輪タイプから重み付き抽選で選択し、
        効果の強度もランダムに決定します。

        Returns
        -------
            生成された指輪。利用可能な指輪がない場合はNone

        """
        available = get_available_items(self.floor, RINGS)
        if not available:
            return None

        ring_type = random.choices(
            available, weights=[r.spawn_weight for r in available], k=1
        )[0]
        power = random.randint(*ring_type.power_range)
        return Ring(0, 0, ring_type.name, ring_type.effect, power)

    def _create_scroll(self) -> Scroll | None:
        """
        ランダムな巻物を生成。

        現在の階層で利用可能な巻物タイプから重み付き抽選で選択します。

        Returns
        -------
            生成された巻物。利用可能な巻物がない場合はNone

        """
        available = get_available_items(self.floor, SCROLLS)
        if not available:
            return None

        scroll_type = random.choices(
            available, weights=[s.spawn_weight for s in available], k=1
        )[0]
        effect = self._get_scroll_effect(scroll_type.effect)
        return Scroll(0, 0, scroll_type.name, effect)

    def _create_potion(self) -> Potion | None:
        """
        ランダムなポーションを生成。

        現在の階層で利用可能なポーションタイプから重み付き抽選で選択し、
        効果の強度もランダムに決定します。

        Returns
        -------
            生成されたポーション。利用可能なポーションがない場合はNone

        """
        available = get_available_items(self.floor, POTIONS)
        if not available:
            return None

        potion_type = random.choices(
            available, weights=[p.spawn_weight for p in available], k=1
        )[0]
        effect = self._get_potion_effect(potion_type.effect, potion_type.power_range)
        return Potion(0, 0, potion_type.name, effect)

    def _create_food(self) -> Food | None:
        """
        ランダムな食料を生成。

        現在の階層で利用可能な食料タイプから重み付き抽選で選択します。

        Returns
        -------
            生成された食料。利用可能な食料がない場合はNone

        """
        available = get_available_items(self.floor, FOODS)
        if not available:
            return None

        food_type = random.choices(
            available, weights=[f.spawn_weight for f in available], k=1
        )[0]
        effect = self._get_food_effect(food_type.nutrition)
        return Food(0, 0, food_type.name, effect)

    def _create_gold(self) -> Gold:
        """
        金貨の山を生成。

        現在の階層に応じた金額を決定します。

        Returns
        -------
            生成された金貨

        """
        amount = get_gold_amount(self.floor)
        return Gold(0, 0, amount)

    def get_item_at(self, x: int, y: int) -> Item | None:
        """
        指定された位置にあるアイテムを取得。

        Args:
        ----
            x: X座標
            y: Y座標

        Returns:
        -------
            該当位置のアイテム。存在しない場合はNone

        """
        for item in self.items:
            if item.x == x and item.y == y:
                return item
        return None

    def remove_item(self, item: Item) -> None:
        """
        アイテムを削除。

        アイテムリストと占有位置セットの両方から削除します。

        Args:
        ----
            item: 削除するアイテム

        """
        if item in self.items:
            self.items.remove(item)
            pos = (item.x, item.y)
            if pos in self.occupied_positions:  # 位置が存在する場合のみ削除
                self.occupied_positions.remove(pos)

    def add_item(self, item: Item) -> bool:
        """
        アイテムを追加。

        Args:
        ----
            item: 追加するアイテム

        Returns:
        -------
            bool: 追加に成功した場合はTrue

        """
        pos = (item.x, item.y)

        # 同じ位置に複数のアイテムを許可（ローグライクゲームでは一般的）
        self.items.append(item)
        self.occupied_positions.add(pos)
        return True

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

    def _get_potion_effect(
        self, effect_name: str, power_range: tuple[int, int]
    ) -> Effect:
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
        if effect_name in [
            "strength",
            "restore_strength",
            "haste_self",
            "see_invisible",
        ]:
            # These need special handling or are placeholders
            return HealingEffect(power)  # Temporary fallback

        return HealingEffect(power)

    def _get_food_effect(self, nutrition: int) -> Effect:
        """Map nutrition value to Effect object for food."""
        from .effects import NutritionEffect

        # Convert nutrition to hunger restoration value
        hunger_value = nutrition // 36  # 900 -> 25, 600 -> 16
        return NutritionEffect(hunger_value)
