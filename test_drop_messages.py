#!/usr/bin/env python3
"""
アイテムドロップメッセージのテスト
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pyrogue.entities.items.item import Weapon, Armor, Scroll, Food, Gold

def test_drop_messages():
    """ドロップメッセージをテスト"""
    print("=== アイテムドロップメッセージテスト ===")
    
    # 武器テスト
    weapon = Weapon(0, 0, "Iron Sword", 8)
    print(f"武器: {weapon.drop()}")
    
    # 防具テスト  
    armor = Armor(0, 0, "Leather Armor", 3)
    print(f"防具: {armor.drop()}")
    
    # スタック可能アイテムテスト
    scroll = Scroll(0, 0, "Scroll of Healing", "healing")
    scroll.stack_count = 5
    print(f"スクロール(5個): {scroll.drop()}")
    
    # 食料テスト
    food = Food(0, 0, "Bread", 100)
    food.stack_count = 2
    print(f"食料(2個): {food.drop()}")
    
    # 金貨テスト
    gold = Gold(0, 0, 150)
    print(f"金貨: {gold.drop()}")
    
    print("\n=== メッセージテスト完了 ===")

if __name__ == "__main__":
    test_drop_messages()