"""Item spawner module."""
from __future__ import annotations

import random
from typing import List, Optional, Dict, Set, Tuple
import numpy as np

from .item import Item, Weapon, Armor, Ring, Scroll, Potion, Food, Gold
from .item_types import (
    WEAPONS, ARMORS, RINGS, SCROLLS, POTIONS, FOODS,
    GOLD_BY_FLOOR, SPECIAL_ROOM_ITEMS
)
from pyrogue.map.tile import Floor

class ItemSpawner:
    """アイテムの生成と管理を行うクラス"""
    
    def __init__(self, dungeon_level: int):
        self.dungeon_level = dungeon_level
        self.items: List[Item] = []
        self.occupied_positions: Set[Tuple[int, int]] = set()
    
    def spawn_items(self, dungeon_tiles: np.ndarray, rooms: List[any]) -> None:
        """アイテムを生成
        
        Args:
            dungeon_tiles: ダンジョンのタイル配列
            rooms: 部屋のリスト
        """
        # 通常の部屋にアイテムを配置
        self._spawn_normal_room_items(dungeon_tiles, rooms)
        
        # 特別な部屋にアイテムを配置
        self._spawn_special_room_items(dungeon_tiles, rooms)
    
    def _spawn_normal_room_items(self, dungeon_tiles: np.ndarray, rooms: List[any]) -> None:
        """通常の部屋にアイテムを配置"""
        # 階層に応じたアイテム数を決定（基本2-4個、階層が上がるごとに若干増加）
        base_count = random.randint(2, 4)
        level_bonus = min(3, self.dungeon_level // 4)  # 最大で3個まで追加
        item_count = base_count + level_bonus
        
        # 通常の部屋にアイテムを配置
        normal_rooms = [room for room in rooms if not room.is_special]
        if not normal_rooms:
            return
        
        for _ in range(item_count):
            room = random.choice(normal_rooms)
            
            # 部屋の内部の座標から、まだアイテムがない場所を選択
            available_positions = [
                (x, y) for x, y in room.inner
                if isinstance(dungeon_tiles[y, x], Floor) and
                (x, y) not in self.occupied_positions
            ]
            
            if not available_positions:
                continue
            
            pos = random.choice(available_positions)
            item = self._create_random_item(pos[0], pos[1])
            if item:
                self.items.append(item)
                self.occupied_positions.add(pos)
    
    def _spawn_special_room_items(self, dungeon_tiles: np.ndarray, rooms: List[any]) -> None:
        """特別な部屋にアイテムを配置"""
        for room in rooms:
            if not room.is_special or not room.room_type:
                continue
            
            # 部屋タイプに応じたアイテム生成ルールを取得
            rules = SPECIAL_ROOM_ITEMS.get(room.room_type)
            if not rules:
                continue
            
            # 利用可能な位置を取得
            available_positions = [
                (x, y) for x, y in room.inner
                if isinstance(dungeon_tiles[y, x], Floor) and
                (x, y) not in self.occupied_positions
            ]
            
            if not available_positions:
                continue
            
            # ルールに従ってアイテムを生成
            if room.room_type == "treasure":
                # 金貨を生成
                gold_min, gold_max = rules["gold"]
                for _ in range(random.randint(3, 5)):
                    if not available_positions:
                        break
                    pos = random.choice(available_positions)
                    available_positions.remove(pos)
                    amount = random.randint(gold_min, gold_max)
                    gold = Gold(pos[0], pos[1], amount)
                    self.items.append(gold)
                    self.occupied_positions.add(pos)
                
                # その他のアイテム
                for _ in range(rules["items"]):
                    if not available_positions:
                        break
                    pos = random.choice(available_positions)
                    available_positions.remove(pos)
                    item = self._create_valuable_item(pos[0], pos[1])
                    if item:
                        self.items.append(item)
                        self.occupied_positions.add(pos)
            
            elif room.room_type == "armory":
                # 武器を生成
                for _ in range(rules["weapons"]):
                    if not available_positions:
                        break
                    pos = random.choice(available_positions)
                    available_positions.remove(pos)
                    weapon = self._create_weapon(pos[0], pos[1])
                    if weapon:
                        self.items.append(weapon)
                        self.occupied_positions.add(pos)
                
                # 防具を生成
                for _ in range(rules["armors"]):
                    if not available_positions:
                        break
                    pos = random.choice(available_positions)
                    available_positions.remove(pos)
                    armor = self._create_armor(pos[0], pos[1])
                    if armor:
                        self.items.append(armor)
                        self.occupied_positions.add(pos)
            
            elif room.room_type == "library":
                # 巻物を生成
                for _ in range(rules["scrolls"]):
                    if not available_positions:
                        break
                    pos = random.choice(available_positions)
                    available_positions.remove(pos)
                    scroll = self._create_scroll(pos[0], pos[1])
                    if scroll:
                        self.items.append(scroll)
                        self.occupied_positions.add(pos)
            
            elif room.room_type == "laboratory":
                # 薬を生成
                for _ in range(rules["potions"]):
                    if not available_positions:
                        break
                    pos = random.choice(available_positions)
                    available_positions.remove(pos)
                    potion = self._create_potion(pos[0], pos[1])
                    if potion:
                        self.items.append(potion)
                        self.occupied_positions.add(pos)
    
    def _create_random_item(self, x: int, y: int) -> Optional[Item]:
        """ランダムなアイテムを生成"""
        # アイテムの種類をランダムに選択
        item_type = random.choices(
            ["weapon", "armor", "ring", "scroll", "potion", "food", "gold"],
            weights=[15, 15, 10, 20, 20, 10, 10]
        )[0]
        
        if item_type == "weapon":
            return self._create_weapon(x, y)
        elif item_type == "armor":
            return self._create_armor(x, y)
        elif item_type == "ring":
            return self._create_ring(x, y)
        elif item_type == "scroll":
            return self._create_scroll(x, y)
        elif item_type == "potion":
            return self._create_potion(x, y)
        elif item_type == "food":
            return self._create_food(x, y)
        elif item_type == "gold":
            return self._create_gold(x, y)
        
        return None
    
    def _create_valuable_item(self, x: int, y: int) -> Optional[Item]:
        """価値の高いアイテムを生成（宝物庫用）"""
        # 武器、防具、指輪のみを生成
        item_type = random.choice(["weapon", "armor", "ring"])
        
        if item_type == "weapon":
            return self._create_weapon(x, y, quality_bonus=2)
        elif item_type == "armor":
            return self._create_armor(x, y, quality_bonus=2)
        else:
            return self._create_ring(x, y)
    
    def _create_weapon(self, x: int, y: int, quality_bonus: int = 0) -> Optional[Weapon]:
        """武器を生成"""
        available_weapons = [
            w for w in WEAPONS
            if w[2] <= self.dungeon_level + quality_bonus
        ]
        if not available_weapons:
            return None
        
        # レア度に基づいて選択
        total_rarity = sum(w[3] for w in available_weapons)
        r = random.randint(1, total_rarity)
        cumulative = 0
        
        for name, attack, level, rarity in available_weapons:
            cumulative += rarity
            if r <= cumulative:
                return Weapon(x, y, name, attack)
        
        return None
    
    def _create_armor(self, x: int, y: int, quality_bonus: int = 0) -> Optional[Armor]:
        """防具を生成"""
        available_armors = [
            a for a in ARMORS
            if a[2] <= self.dungeon_level + quality_bonus
        ]
        if not available_armors:
            return None
        
        # レア度に基づいて選択
        total_rarity = sum(a[3] for a in available_armors)
        r = random.randint(1, total_rarity)
        cumulative = 0
        
        for name, defense, level, rarity in available_armors:
            cumulative += rarity
            if r <= cumulative:
                return Armor(x, y, name, defense)
        
        return None
    
    def _create_ring(self, x: int, y: int) -> Optional[Ring]:
        """指輪を生成"""
        available_rings = [
            r for r in RINGS
            if r[3] <= self.dungeon_level
        ]
        if not available_rings:
            return None
        
        # レア度に基づいて選択
        total_rarity = sum(r[4] for r in available_rings)
        r = random.randint(1, total_rarity)
        cumulative = 0
        
        for name, effect, bonus, level, rarity in available_rings:
            cumulative += rarity
            if r <= cumulative:
                return Ring(x, y, name, effect, bonus)
        
        return None
    
    def _create_scroll(self, x: int, y: int) -> Optional[Scroll]:
        """巻物を生成"""
        available_scrolls = [
            s for s in SCROLLS
            if s[2] <= self.dungeon_level
        ]
        if not available_scrolls:
            return None
        
        # レア度に基づいて選択
        total_rarity = sum(s[3] for s in available_scrolls)
        r = random.randint(1, total_rarity)
        cumulative = 0
        
        for name, effect, level, rarity in available_scrolls:
            cumulative += rarity
            if r <= cumulative:
                return Scroll(x, y, name, effect)
        
        return None
    
    def _create_potion(self, x: int, y: int) -> Optional[Potion]:
        """薬を生成"""
        available_potions = [
            p for p in POTIONS
            if p[3] <= self.dungeon_level
        ]
        if not available_potions:
            return None
        
        # レア度に基づいて選択
        total_rarity = sum(p[4] for p in available_potions)
        r = random.randint(1, total_rarity)
        cumulative = 0
        
        for name, effect, power, level, rarity in available_potions:
            cumulative += rarity
            if r <= cumulative:
                return Potion(x, y, name, effect, power)
        
        return None
    
    def _create_food(self, x: int, y: int) -> Optional[Food]:
        """食料を生成"""
        available_foods = [
            f for f in FOODS
            if f[2] <= self.dungeon_level
        ]
        if not available_foods:
            return None
        
        # レア度に基づいて選択
        total_rarity = sum(f[3] for f in available_foods)
        r = random.randint(1, total_rarity)
        cumulative = 0
        
        for name, nutrition, level, rarity in available_foods:
            cumulative += rarity
            if r <= cumulative:
                return Food(x, y, name, nutrition)
        
        return None
    
    def _create_gold(self, x: int, y: int) -> Gold:
        """金貨を生成"""
        # 階層に応じた金貨量を決定
        level = min(self.dungeon_level, 10)  # 10階以降は10階と同じ
        min_gold, max_gold = GOLD_BY_FLOOR[level]
        amount = random.randint(min_gold, max_gold)
        return Gold(x, y, amount)
    
    def get_item_at(self, x: int, y: int) -> Optional[Item]:
        """指定された位置にあるアイテムを取得"""
        for item in self.items:
            if item.x == x and item.y == y:
                return item
        return None
    
    def remove_item(self, item: Item) -> None:
        """アイテムを削除"""
        if item in self.items:
            self.items.remove(item)
            self.occupied_positions.remove((item.x, item.y)) 