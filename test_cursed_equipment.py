#!/usr/bin/env python3
"""
祝福・呪い装備の動作調査
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pyrogue.entities.actors.player import Player
from pyrogue.entities.items.item import Ring, Weapon, Armor
from pyrogue.core.managers.game_context import GameContext

def test_cursed_equipment():
    """祝福・呪い装備の動作テスト"""
    print("=== 祝福・呪い装備の動作テスト ===")
    
    # プレイヤーを作成
    player = Player(40, 23)
    
    # GameContextを作成
    message_log = []
    context = GameContext(
        player=player,
        inventory=player.inventory,
        dungeon_manager=None,
        message_log=message_log
    )
    
    # 通常の装備を作成
    normal_sword = Weapon(0, 0, "Normal Sword", 5)
    normal_armor = Armor(0, 0, "Normal Armor", 3)
    normal_ring = Ring(0, 0, "Normal Ring", "strength", 2)
    
    # 呪われた装備を作成
    cursed_sword = Weapon(0, 0, "Cursed Sword", 8)
    cursed_sword.cursed = True
    cursed_armor = Armor(0, 0, "Cursed Armor", 5)
    cursed_armor.cursed = True
    cursed_ring = Ring(0, 0, "Cursed Ring", "protection", 3)
    cursed_ring.cursed = True
    
    # アイテムをインベントリに追加
    for item in [normal_sword, normal_armor, normal_ring, cursed_sword, cursed_armor, cursed_ring]:
        player.inventory.add_item(item)
    
    print(f"初期状態:")
    print(f"  インベントリ: {[f'{item.name}(cursed={item.cursed})' for item in player.inventory.items]}")
    print(f"  装備: {[(slot, item.name if item else None) for slot, item in player.inventory.equipped.items()]}")
    
    # 通常装備を装備
    print(f"\n=== 通常装備のテスト ===")
    print(f"通常の剣を装備:")
    old_weapon = player.equip_item(normal_sword)
    print(f"  装備成功: {player.inventory.is_equipped(normal_sword)}")
    print(f"  装備後: {player.inventory.get_equipped_item_name('weapon')}")
    print(f"  インベントリ: {[item.name for item in player.inventory.items]}")
    
    # 装備を外す
    print(f"\n武器を外す:")
    unequipped = player.unequip_item("weapon")
    print(f"  外した武器: {unequipped.name if unequipped else None}")
    print(f"  現在の装備: {player.inventory.get_equipped_item_name('weapon')}")
    print(f"  インベントリ: {[item.name for item in player.inventory.items]}")
    
    # 装備をドロップ
    print(f"\n通常装備をドロップ:")
    can_drop, reason = player.inventory.can_drop_item(normal_sword)
    print(f"  ドロップ可能: {can_drop}, 理由: {reason}")
    if can_drop:
        player.inventory.remove_item(normal_sword)
        print(f"  ドロップ後インベントリ: {[item.name for item in player.inventory.items]}")
    
    # 呪われた装備を装備
    print(f"\n=== 呪われた装備のテスト ===")
    print(f"呪われた剣を装備:")
    old_weapon = player.equip_item(cursed_sword)
    print(f"  装備成功: {player.inventory.is_equipped(cursed_sword)}")
    print(f"  装備後: {player.inventory.get_equipped_item_name('weapon')}")
    print(f"  インベントリ: {[item.name for item in player.inventory.items]}")
    
    # 呪われた装備を外そうとする
    print(f"\n呪われた武器を外そうとする:")
    unequipped = player.unequip_item("weapon")
    print(f"  外した武器: {unequipped.name if unequipped else None}")
    print(f"  現在の装備: {player.inventory.get_equipped_item_name('weapon')}")
    print(f"  メッセージ: {message_log}")
    
    # 呪われた装備をドロップしようとする
    print(f"\n呪われた装備をドロップしようとする:")
    can_drop, reason = player.inventory.can_drop_item(cursed_sword)
    print(f"  ドロップ可能: {can_drop}, 理由: {reason}")
    
    # 呪われた指輪も試す
    print(f"\n呪われた指輪を装備:")
    old_ring = player.equip_item(cursed_ring)
    print(f"  装備成功: {player.inventory.is_equipped(cursed_ring)}")
    print(f"  装備後: {player.inventory.get_equipped_item_name('ring_left')}")
    
    print(f"\n呪われた指輪を外そうとする:")
    unequipped_ring = player.unequip_item("ring_left")
    print(f"  外した指輪: {unequipped_ring.name if unequipped_ring else None}")
    print(f"  現在の装備: {player.inventory.get_equipped_item_name('ring_left')}")
    
    # 呪われた装備をドロップしようとする
    print(f"\n呪われた指輪をドロップしようとする:")
    can_drop, reason = player.inventory.can_drop_item(cursed_ring)
    print(f"  ドロップ可能: {can_drop}, 理由: {reason}")
    
    print(f"\n最終状態:")
    print(f"  インベントリ: {[f'{item.name}(cursed={item.cursed})' for item in player.inventory.items]}")
    print(f"  装備: {[(slot, f'{item.name}(cursed={item.cursed})' if item else None) for slot, item in player.inventory.equipped.items()]}")
    print(f"  メッセージログ: {message_log}")

if __name__ == "__main__":
    test_cursed_equipment()