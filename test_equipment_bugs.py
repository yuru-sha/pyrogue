#!/usr/bin/env python3
"""
装備関連バグのテスト
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pyrogue.entities.actors.player import Player
from pyrogue.entities.items.item import Weapon


def test_equipment_bugs():
    """装備関連バグのテスト"""
    print("=== 装備関連バグのテスト ===")

    # プレイヤーを作成
    player = Player(40, 23)

    # 武器を2つ作成
    sword1 = Weapon(0, 0, "Short Sword", 5)
    sword2 = Weapon(0, 0, "Long Sword", 7)

    # インベントリに追加
    player.inventory.add_item(sword1)
    player.inventory.add_item(sword2)

    print("初期状態:")
    print(f"  インベントリ: {[item.name for item in player.inventory.items]}")
    print(f"  装備: {player.inventory.equipped}")

    # 最初の武器を装備
    print("\n=== Short Sword を装備 ===")
    old_item = player.inventory.equip(sword1)
    print(f"  old_item: {old_item.name if old_item else None}")
    print(f"  装備後インベントリ: {[item.name for item in player.inventory.items]}")
    print(f"  装備後装備: {player.inventory.equipped}")
    print(f"  sword1 is_equipped: {player.inventory.is_equipped(sword1)}")

    # インベントリから削除（装備後の処理をシミュレート）
    player.inventory.remove_item(sword1)
    print(f"  削除後インベントリ: {[item.name for item in player.inventory.items]}")

    # 2番目の武器を装備
    print("\n=== Long Sword を装備 ===")
    old_item = player.inventory.equip(sword2)
    print(f"  old_item: {old_item.name if old_item else None}")
    print(f"  装備後インベントリ: {[item.name for item in player.inventory.items]}")
    print(f"  装備後装備: {player.inventory.equipped}")
    print(f"  sword2 is_equipped: {player.inventory.is_equipped(sword2)}")

    # 古い装備をインベントリに戻す
    if old_item:
        player.inventory.add_item(old_item)
        print(f"  古い装備を戻した後: {[item.name for item in player.inventory.items]}")

    # インベントリから削除（装備後の処理をシミュレート）
    player.inventory.remove_item(sword2)
    print(f"  削除後インベントリ: {[item.name for item in player.inventory.items]}")

    # 再度最初の武器を装備（アイテム増殖をテスト）
    print("\n=== 再度 Short Sword を装備 ===")
    old_item = player.inventory.equip(sword1)
    print(f"  old_item: {old_item.name if old_item else None}")
    print(f"  装備後インベントリ: {[item.name for item in player.inventory.items]}")
    print(f"  装備後装備: {player.inventory.equipped}")

    # 古い装備をインベントリに戻す
    if old_item:
        player.inventory.add_item(old_item)
        print(f"  古い装備を戻した後: {[item.name for item in player.inventory.items]}")

    # 最終状態
    print("\n=== 最終状態 ===")
    print(f"  インベントリ: {[item.name for item in player.inventory.items]}")
    print(f"  装備: {player.inventory.equipped}")


if __name__ == "__main__":
    test_equipment_bugs()
