"""Inventory management module."""
from __future__ import annotations

from typing import List, Optional, Dict
from pyrogue.entities.items.item import Item, Weapon, Armor, Ring

class Inventory:
    """インベントリ管理クラス"""
    
    def __init__(self, capacity: int = 26):  # a-zの26文字分
        self.capacity = capacity
        self.items: List[Item] = []
        
        # 装備スロット
        self.equipped: Dict[str, Optional[Item]] = {
            "weapon": None,
            "armor": None,
            "ring_left": None,
            "ring_right": None
        }
    
    def add_item(self, item: Item) -> bool:
        """アイテムを追加
        
        Args:
            item: 追加するアイテム
            
        Returns:
            bool: 追加に成功したかどうか
        """
        if len(self.items) >= self.capacity:
            return False
        
        # スタック可能なアイテムの場合、既存のスタックに追加を試みる
        if item.stackable:
            for existing_item in self.items:
                if (existing_item.name == item.name and
                    existing_item.stackable and
                    isinstance(existing_item, type(item))):
                    existing_item.stack_count += item.stack_count
                    return True
        
        self.items.append(item)
        return True
    
    def remove_item(self, item: Item) -> None:
        """アイテムを削除
        
        Args:
            item: 削除するアイテム
        """
        if item in self.items:
            self.items.remove(item)
    
    def get_item(self, index: int) -> Optional[Item]:
        """指定されたインデックスのアイテムを取得
        
        Args:
            index: アイテムのインデックス
            
        Returns:
            Optional[Item]: アイテム（存在しない場合はNone）
        """
        if 0 <= index < len(self.items):
            return self.items[index]
        return None
    
    def equip(self, item: Item) -> Optional[Item]:
        """アイテムを装備
        
        Args:
            item: 装備するアイテム
            
        Returns:
            Optional[Item]: 外したアイテム（ある場合）
        """
        if isinstance(item, Weapon):
            old_item = self.equipped["weapon"]
            self.equipped["weapon"] = item
            return old_item
        
        elif isinstance(item, Armor):
            old_item = self.equipped["armor"]
            self.equipped["armor"] = item
            return old_item
        
        elif isinstance(item, Ring):
            # 左手の指輪が空いていれば左手に、そうでなければ右手に装備
            if self.equipped["ring_left"] is None:
                old_item = self.equipped["ring_left"]
                self.equipped["ring_left"] = item
                return old_item
            else:
                old_item = self.equipped["ring_right"]
                self.equipped["ring_right"] = item
                return old_item
        
        return None
    
    def unequip(self, slot: str) -> Optional[Item]:
        """装備を外す
        
        Args:
            slot: 装備スロット名
            
        Returns:
            Optional[Item]: 外したアイテム（ある場合）
        """
        if slot in self.equipped:
            item = self.equipped[slot]
            self.equipped[slot] = None
            return item
        return None
    
    def get_attack_bonus(self) -> int:
        """装備による攻撃力ボーナスを計算
        
        Returns:
            int: 攻撃力ボーナス
        """
        bonus = 0
        
        # 武器のボーナス
        if isinstance(self.equipped["weapon"], Weapon):
            bonus += self.equipped["weapon"].attack
        
        # 指輪のボーナス
        for ring_slot in ["ring_left", "ring_right"]:
            ring = self.equipped[ring_slot]
            if isinstance(ring, Ring) and ring.effect == "attack":
                bonus += ring.bonus
        
        return bonus
    
    def get_defense_bonus(self) -> int:
        """装備による防御力ボーナスを計算
        
        Returns:
            int: 防御力ボーナス
        """
        bonus = 0
        
        # 防具のボーナス
        if isinstance(self.equipped["armor"], Armor):
            bonus += self.equipped["armor"].defense
        
        # 指輪のボーナス
        for ring_slot in ["ring_left", "ring_right"]:
            ring = self.equipped[ring_slot]
            if isinstance(ring, Ring) and ring.effect == "defense":
                bonus += ring.bonus
        
        return bonus
    
    def get_equipped_item_name(self, slot: str) -> str:
        """装備スロットのアイテム名を取得
        
        Args:
            slot: 装備スロット名
            
        Returns:
            str: アイテム名（装備なしの場合は "None"）
        """
        item = self.equipped.get(slot)
        return item.name if item else "None" 