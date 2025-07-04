"""Item spawner module."""

from __future__ import annotations

import random

import numpy as np

from pyrogue.map.dungeon import Room

from .item import Armor, Food, Gold, Item, Potion, Ring, Scroll, Weapon
from .item_types import (
    AMULET,
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
    """アイテムの生成と管理を行うクラス"""

    def __init__(self, floor: int):
        """Initialize item spawner."""
        self.floor = floor
        self.items: list[Item] = []
        self.occupied_positions: set[tuple[int, int]] = set()

    def spawn_items(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """Spawn items in the dungeon."""
        self.items.clear()
        self.occupied_positions.clear()  # 位置情報もクリア

        # Get total number of items to spawn on this floor
        total_items = get_item_spawn_count(self.floor)

        # Spawn Amulet of Yendor on floor 26
        if self.floor == 26:
            room = random.choice(rooms)
            x, y = self._find_valid_position(dungeon_tiles, room)
            if x is not None and y is not None:
                amulet = Item(
                    x, y, AMULET.char, AMULET.name, (255, 215, 0)
                )  # Gold color
                self.items.append(amulet)
                self.occupied_positions.add((x, y))  # 位置を追加

        # Spawn regular items
        for _ in range(total_items):
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
        """Find a valid position for an item in the given room."""
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

    def _is_position_occupied(self, x: int, y: int) -> bool:
        """Check if a position is occupied by an item."""
        return any(item.x == x and item.y == y for item in self.items)

    def _create_weapon(self) -> Weapon | None:
        """Create a random weapon."""
        available = get_available_items(self.floor, WEAPONS)
        if not available:
            return None

        weapon_type = random.choices(
            available, weights=[w.spawn_weight for w in available], k=1
        )[0]
        bonus = random.randint(*weapon_type.bonus_range)
        return Weapon(0, 0, weapon_type.name, bonus)

    def _create_armor(self) -> Armor | None:
        """Create a random armor."""
        available = get_available_items(self.floor, ARMORS)
        if not available:
            return None

        armor_type = random.choices(
            available, weights=[a.spawn_weight for a in available], k=1
        )[0]
        bonus = random.randint(*armor_type.bonus_range)
        return Armor(0, 0, armor_type.name, bonus)

    def _create_ring(self) -> Ring | None:
        """Create a random ring."""
        available = get_available_items(self.floor, RINGS)
        if not available:
            return None

        ring_type = random.choices(
            available, weights=[r.spawn_weight for r in available], k=1
        )[0]
        power = random.randint(*ring_type.power_range)
        return Ring(0, 0, ring_type.name, ring_type.effect, power)

    def _create_scroll(self) -> Scroll | None:
        """Create a random scroll."""
        available = get_available_items(self.floor, SCROLLS)
        if not available:
            return None

        scroll_type = random.choices(
            available, weights=[s.spawn_weight for s in available], k=1
        )[0]
        return Scroll(0, 0, scroll_type.name, scroll_type.effect)

    def _create_potion(self) -> Potion | None:
        """Create a random potion."""
        available = get_available_items(self.floor, POTIONS)
        if not available:
            return None

        potion_type = random.choices(
            available, weights=[p.spawn_weight for p in available], k=1
        )[0]
        power = random.randint(*potion_type.power_range)
        return Potion(0, 0, potion_type.name, potion_type.effect, power)

    def _create_food(self) -> Food | None:
        """Create a random food item."""
        available = get_available_items(self.floor, FOODS)
        if not available:
            return None

        food_type = random.choices(
            available, weights=[f.spawn_weight for f in available], k=1
        )[0]
        return Food(0, 0, food_type.name, food_type.nutrition)

    def _create_gold(self) -> Gold:
        """Create a gold pile."""
        amount = get_gold_amount(self.floor)
        return Gold(0, 0, amount)

    def get_item_at(self, x: int, y: int) -> Item | None:
        """指定された位置にあるアイテムを取得"""
        for item in self.items:
            if item.x == x and item.y == y:
                return item
        return None

    def remove_item(self, item: Item) -> None:
        """アイテムを削除"""
        if item in self.items:
            self.items.remove(item)
            pos = (item.x, item.y)
            if pos in self.occupied_positions:  # 位置が存在する場合のみ削除
                self.occupied_positions.remove(pos)
