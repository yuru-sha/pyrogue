#!/usr/bin/env python3
"""
改善されたアイテムピックアップメッセージのテスト
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pyrogue.entities.items.item import Weapon, Armor, Scroll, Food, Gold

def test_pickup_messages():
    """改善されたピックアップメッセージをテスト"""
    print("=== アイテムピックアップメッセージテスト ===")

    # 武器テスト
    weapon = Weapon(0, 0, "Iron Sword", 8)
    print(f"武器: {weapon.pick_up()}")

    # 防具テスト
    armor = Armor(0, 0, "Leather Armor", 3)
    print(f"防具: {armor.pick_up()}")

    # スタック可能アイテムテスト
    scroll = Scroll(0, 0, "Scroll of Healing", "healing")
    scroll.stack_count = 3
    print(f"スクロール(3個): {scroll.pick_up()}")

    # 食料テスト
    food = Food(0, 0, "Bread", 100)
    print(f"食料: {food.pick_up()}")

    # 金貨テスト
    gold = Gold(0, 0, 50)
    print(f"金貨: {gold.pick_up()}")

    print("\n=== メッセージテスト完了 ===")

if __name__ == "__main__":
    test_pickup_messages()
