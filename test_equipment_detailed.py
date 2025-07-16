#!/usr/bin/env python3
"""
詳細な装備システムテスト
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pyrogue.entities.actors.player import Player
from pyrogue.entities.items.item import Armor, Weapon


def test_equipment_detailed():
    """詳細な装備システムテスト"""
    print("=== 詳細な装備システムテスト ===")

    # プレイヤーを作成
    player = Player(40, 23)

    # 武器を3つ作成
    sword1 = Weapon(0, 0, "Short Sword", 5)
    sword2 = Weapon(0, 0, "Long Sword", 7)
    sword3 = Weapon(0, 0, "Broad Sword", 9)

    # 防具を2つ作成
    armor1 = Armor(0, 0, "Leather Armor", 2)
    armor2 = Armor(0, 0, "Chain Mail", 4)

    # インベントリに追加
    player.inventory.add_item(sword1)
    player.inventory.add_item(sword2)
    player.inventory.add_item(sword3)
    player.inventory.add_item(armor1)
    player.inventory.add_item(armor2)

    print("初期状態:")
    print(f"  インベントリ: {[item.name for item in player.inventory.items]}")
    print(f"  装備: weapon={player.inventory.equipped['weapon']}, armor={player.inventory.equipped['armor']}")

    # 装備の繰り返し切り替えテスト
    print("\n=== 装備の繰り返し切り替えテスト ===")

    for i in range(3):
        print(f"\n--- Round {i+1} ---")

        # sword1を装備
        old_weapon = player.inventory.equip(sword1)
        print(f"sword1装備: old={old_weapon.name if old_weapon else None}")
        player.inventory.remove_item(sword1)
        if old_weapon:
            player.inventory.add_item(old_weapon)
        print(f"  インベントリ: {[item.name for item in player.inventory.items]}")

        # sword2を装備
        old_weapon = player.inventory.equip(sword2)
        print(f"sword2装備: old={old_weapon.name if old_weapon else None}")
        player.inventory.remove_item(sword2)
        if old_weapon:
            player.inventory.add_item(old_weapon)
        print(f"  インベントリ: {[item.name for item in player.inventory.items]}")

        # armor1を装備
        old_armor = player.inventory.equip(armor1)
        print(f"armor1装備: old={old_armor.name if old_armor else None}")
        player.inventory.remove_item(armor1)
        if old_armor:
            player.inventory.add_item(old_armor)
        print(f"  インベントリ: {[item.name for item in player.inventory.items]}")

        # armor2を装備
        old_armor = player.inventory.equip(armor2)
        print(f"armor2装備: old={old_armor.name if old_armor else None}")
        player.inventory.remove_item(armor2)
        if old_armor:
            player.inventory.add_item(old_armor)
        print(f"  インベントリ: {[item.name for item in player.inventory.items]}")

    print("\n=== 最終状態 ===")
    print(f"  インベントリ: {[item.name for item in player.inventory.items]}")
    print(f"  装備: weapon={player.inventory.equipped['weapon']}, armor={player.inventory.equipped['armor']}")

    # アイテム数カウント
    inventory_count = {}
    for item in player.inventory.items:
        inventory_count[item.name] = inventory_count.get(item.name, 0) + 1

    print("\n=== アイテム数カウント ===")
    for name, count in inventory_count.items():
        print(f"  {name}: {count}")

    # 装備済みアイテムの確認
    equipped_weapon = player.inventory.equipped["weapon"]
    equipped_armor = player.inventory.equipped["armor"]

    print("\n=== 装備済みアイテムの確認 ===")
    print(f"  装備済み武器: {equipped_weapon.name if equipped_weapon else None}")
    print(f"  装備済み防具: {equipped_armor.name if equipped_armor else None}")

    # 装備済みアイテムがインベントリに存在するかチェック
    if equipped_weapon:
        weapon_in_inventory = any(item.name == equipped_weapon.name for item in player.inventory.items)
        print(f"  装備済み武器がインベントリに存在: {weapon_in_inventory}")

    if equipped_armor:
        armor_in_inventory = any(item.name == equipped_armor.name for item in player.inventory.items)
        print(f"  装備済み防具がインベントリに存在: {armor_in_inventory}")


if __name__ == "__main__":
    test_equipment_detailed()
