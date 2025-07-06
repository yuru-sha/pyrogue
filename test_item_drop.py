#!/usr/bin/env python3
"""
アイテムドロップ機能のテストスクリプト
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pyrogue.entities.items.item_spawner import ItemSpawner
from pyrogue.entities.actors.inventory import Inventory
from pyrogue.entities.items.item import Weapon, Armor, Scroll, Food


def test_item_drop():
    """アイテムドロップ機能をテスト"""
    print("=== アイテムドロップ機能テスト ===")

    # テスト環境の準備
    inventory = Inventory()
    item_spawner = ItemSpawner(1)

    # テスト用アイテムをインベントリに追加
    weapon = Weapon(0, 0, "Test Sword", 5)
    armor = Armor(0, 0, "Test Armor", 3)
    scroll = Scroll(0, 0, "Test Scroll", "healing")

    inventory.add_item(weapon)
    inventory.add_item(armor)
    inventory.add_item(scroll)

    print(f"初期インベントリサイズ: {len(inventory.items)}")
    print(f"初期地面アイテム数: {len(item_spawner.items)}")

    # ドロップテスト1: 成功ケース
    print("\n1. 通常ドロップテスト...")
    weapon.x = 10
    weapon.y = 10

    if item_spawner.add_item(weapon):
        inventory.remove_item(weapon)
        print(f"武器ドロップ成功: {weapon.name}")
        print(f"ドロップ後インベントリサイズ: {len(inventory.items)}")
        print(f"ドロップ後地面アイテム数: {len(item_spawner.items)}")
    else:
        print("武器ドロップ失敗")

    # ドロップテスト2: 同じ位置に再ドロップ（失敗ケース）
    print("\n2. 重複位置ドロップテスト...")
    armor.x = 10
    armor.y = 10

    if item_spawner.add_item(armor):
        inventory.remove_item(armor)
        print("防具ドロップ成功（期待しない結果）")
    else:
        print("防具ドロップ失敗（期待する結果）")

    # ドロップテスト3: 異なる位置へのドロップ
    print("\n3. 異なる位置ドロップテスト...")
    armor.x = 11
    armor.y = 10

    if item_spawner.add_item(armor):
        inventory.remove_item(armor)
        print(f"防具ドロップ成功: {armor.name}")
        print(f"最終インベントリサイズ: {len(inventory.items)}")
        print(f"最終地面アイテム数: {len(item_spawner.items)}")
    else:
        print("防具ドロップ失敗")

    # アイテム位置確認
    print("\n4. アイテム位置確認...")
    for item in item_spawner.items:
        print(f"  {item.name}: ({item.x}, {item.y})")

    # 占有位置確認
    print(f"占有位置: {item_spawner.occupied_positions}")

    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_item_drop()
