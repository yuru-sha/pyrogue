#!/usr/bin/env python3
"""
装備アイテムのドロップテスト
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pyrogue.entities.actors.player import Player
from pyrogue.entities.items.item import Weapon, Armor

def test_equipment_drop():
    """装備アイテムのドロップテスト"""
    print("=== 装備アイテムのドロップテスト ===")
    
    # プレイヤーを作成
    player = Player(40, 23)
    
    # 武器を作成
    sword = Weapon(0, 0, "Long Sword", 7)
    armor = Armor(0, 0, "Chain Mail", 4)
    
    # インベントリに追加
    player.inventory.add_item(sword)
    player.inventory.add_item(armor)
    
    print(f"初期状態:")
    print(f"  インベントリ: {[item.name for item in player.inventory.items]}")
    print(f"  装備: weapon={player.inventory.equipped['weapon']}, armor={player.inventory.equipped['armor']}")
    
    # 武器を装備
    player.inventory.equip(sword)
    player.inventory.remove_item(sword)
    print(f"\n武器装備後:")
    print(f"  インベントリ: {[item.name for item in player.inventory.items]}")
    print(f"  装備: weapon={player.inventory.equipped['weapon']}, armor={player.inventory.equipped['armor']}")
    
    # 防具を装備
    player.inventory.equip(armor)
    player.inventory.remove_item(armor)
    print(f"\n防具装備後:")
    print(f"  インベントリ: {[item.name for item in player.inventory.items]}")
    print(f"  装備: weapon={player.inventory.equipped['weapon']}, armor={player.inventory.equipped['armor']}")
    
    # 装備中の武器をドロップ
    print(f"\n=== 装備中の武器をドロップ ===")
    equipped_weapon = player.inventory.equipped["weapon"]
    if equipped_weapon:
        success, dropped_count, message = player.inventory.drop_item(equipped_weapon)
        print(f"  ドロップ成功: {success}")
        print(f"  ドロップ数: {dropped_count}")
        print(f"  メッセージ: {message}")
        print(f"  ドロップ後インベントリ: {[item.name for item in player.inventory.items]}")
        print(f"  ドロップ後装備: weapon={player.inventory.equipped['weapon']}, armor={player.inventory.equipped['armor']}")
    
    # 装備中の防具をドロップ
    print(f"\n=== 装備中の防具をドロップ ===")
    equipped_armor = player.inventory.equipped["armor"]
    if equipped_armor:
        success, dropped_count, message = player.inventory.drop_item(equipped_armor)
        print(f"  ドロップ成功: {success}")
        print(f"  ドロップ数: {dropped_count}")
        print(f"  メッセージ: {message}")
        print(f"  ドロップ後インベントリ: {[item.name for item in player.inventory.items]}")
        print(f"  ドロップ後装備: weapon={player.inventory.equipped['weapon']}, armor={player.inventory.equipped['armor']}")

if __name__ == "__main__":
    test_equipment_drop()