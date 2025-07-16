#!/usr/bin/env python3
"""
指輪のボーナス表示テスト
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pyrogue.entities.actors.player import Player
from pyrogue.entities.items.item import Armor, Ring, Weapon


def test_ring_display():
    """指輪のボーナス表示テスト"""
    print("=== 指輪のボーナス表示テスト ===")

    # プレイヤーを作成
    player = Player(40, 23)

    # 各種装備を作成
    sword = Weapon(0, 0, "Iron Sword", 5)
    armor = Armor(0, 0, "Leather Armor", 3)
    attack_ring = Ring(0, 0, "Ring of Strength", "strength", 2)
    defense_ring = Ring(0, 0, "Ring of Protection", "protection", 1)

    print("初期状態:")
    print(f"  攻撃力: {player.get_attack()}")
    print(f"  防御力: {player.get_defense()}")
    print(f"  ステータス: {player.get_status_text()}")

    # 武器を装備
    print("\n武器を装備:")
    print(f"  拾得メッセージ: {sword.pick_up()}")
    player.inventory.add_item(sword)
    old_item = player.equip_item(sword)
    print(f"  攻撃力: {player.get_attack()}")
    print(f"  武器表示: {player.inventory.get_equipped_item_name('weapon')}")

    # 防具を装備
    print("\n防具を装備:")
    print(f"  拾得メッセージ: {armor.pick_up()}")
    player.inventory.add_item(armor)
    old_item = player.equip_item(armor)
    print(f"  防御力: {player.get_defense()}")
    print(f"  防具表示: {player.inventory.get_equipped_item_name('armor')}")

    # 攻撃力向上の指輪を装備
    print("\n攻撃力向上の指輪を装備:")
    print(f"  拾得メッセージ: {attack_ring.pick_up()}")
    player.inventory.add_item(attack_ring)
    old_item = player.equip_item(attack_ring)
    print(f"  攻撃力: {player.get_attack()}")
    print(f"  左手指輪表示: {player.inventory.get_equipped_item_name('ring_left')}")

    # 防御力向上の指輪を装備
    print("\n防御力向上の指輪を装備:")
    print(f"  拾得メッセージ: {defense_ring.pick_up()}")
    player.inventory.add_item(defense_ring)
    old_item = player.equip_item(defense_ring)
    print(f"  防御力: {player.get_defense()}")
    print(f"  右手指輪表示: {player.inventory.get_equipped_item_name('ring_right')}")

    print("\n最終ステータス:")
    print(f"  攻撃力: {player.get_attack()}")
    print(f"  防御力: {player.get_defense()}")
    print("  ステータス表示:")
    print(f"    {player.get_status_text()}")


if __name__ == "__main__":
    test_ring_display()
