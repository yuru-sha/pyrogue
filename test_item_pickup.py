#!/usr/bin/env python3
"""
アイテム拾い機能のテストスクリプト
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pyrogue.entities.items.item_spawner import ItemSpawner
from pyrogue.entities.actors.inventory import Inventory
from pyrogue.entities.items.item import Weapon, Gold


def test_item_pickup():
    """アイテム拾い機能をテスト"""
    print("=== アイテム拾い機能テスト ===")

    # テスト環境の準備
    inventory = Inventory()
    item_spawner = ItemSpawner(1)

    # テスト用アイテムをスポーン
    weapon = Weapon(10, 10, "Test Sword", 5)
    gold = Gold(11, 10, 50)

    print(f"初期インベントリサイズ: {len(inventory.items)}")

    # インベントリにアイテム追加テスト
    print("\n1. インベントリ追加テスト...")
    result = inventory.add_item(weapon)
    print(f"武器追加成功: {result}")
    print(f"追加後インベントリサイズ: {len(inventory.items)}")
    print(f"武器名: {inventory.items[0].name if inventory.items else 'なし'}")

    # アイテムスポナーの機能テスト
    print("\n2. アイテムスポナーテスト...")
    item_spawner.items = [weapon, gold]
    item_spawner.occupied_positions = {(10, 10), (11, 10)}

    found_weapon = item_spawner.get_item_at(10, 10)
    found_gold = item_spawner.get_item_at(11, 10)
    nothing = item_spawner.get_item_at(12, 12)

    print(f"位置(10,10)のアイテム: {found_weapon.name if found_weapon else 'なし'}")
    print(f"位置(11,10)のアイテム: {found_gold.name if found_gold else 'なし'}")
    print(f"位置(12,12)のアイテム: {nothing.name if nothing else 'なし'}")

    # アイテム削除テスト
    print("\n3. アイテム削除テスト...")
    print(f"削除前のアイテム数: {len(item_spawner.items)}")
    item_spawner.remove_item(weapon)
    print(f"削除後のアイテム数: {len(item_spawner.items)}")

    # インベントリ満杯テスト
    print("\n4. インベントリ満杯テスト...")
    # インベントリを満杯にする
    for i in range(25):  # 容量26なので25個追加（1個は既に追加済み）
        test_item = Weapon(0, 0, f"Filler {i}", 1)
        inventory.add_item(test_item)

    print(f"満杯時のインベントリサイズ: {len(inventory.items)}")

    # 満杯状態で追加できないことを確認
    weapon3 = Weapon(13, 10, "Full Test", 1)
    result = inventory.add_item(weapon3)
    print(f"満杯時の追加結果: {result}")
    print(f"最終インベントリサイズ: {len(inventory.items)}")

    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_item_pickup()
