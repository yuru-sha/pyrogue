#!/usr/bin/env python3
"""
インベントリ表示のバグ調査
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pyrogue.entities.actors.player import Player
from pyrogue.entities.items.item import Armor, Ring, Weapon


def test_inventory_display_bug():
    """インベントリ表示バグの調査"""
    print("=== インベントリ表示バグ調査 ===")

    # プレイヤーを作成
    player = Player(40, 23)

    # テスト用アイテムを作成
    sword = Weapon(0, 0, "Two-Handed Sword", 10)
    armor = Armor(0, 0, "Chain Mail", 4)
    attack_ring = Ring(0, 0, "granite ring", "attack", 3)  # スクリーンショットと同じ名前
    defense_ring = Ring(0, 0, "Ring of See Invisible", "defense", 2)  # スクリーンショットと同じ名前

    # アイテムをインベントリに追加
    player.inventory.add_item(sword)
    player.inventory.add_item(armor)
    player.inventory.add_item(attack_ring)
    player.inventory.add_item(defense_ring)

    print("初期状態:")
    print(f"  インベントリ内容: {[item.name for item in player.inventory.items]}")
    print(f"  装備状態: {[(slot, item.name if item else None) for slot, item in player.inventory.equipped.items()]}")

    # 装備する
    print("\n装備処理:")
    player.equip_item(sword)
    print(f"  武器装備後: {player.inventory.equipped['weapon'].name if player.inventory.equipped['weapon'] else None}")

    player.equip_item(armor)
    print(f"  防具装備後: {player.inventory.equipped['armor'].name if player.inventory.equipped['armor'] else None}")

    player.equip_item(attack_ring)
    print(
        f"  攻撃指輪装備後: 左手={player.inventory.equipped['ring_left'].name if player.inventory.equipped['ring_left'] else None}"
    )

    player.equip_item(defense_ring)
    print(
        f"  防御指輪装備後: 右手={player.inventory.equipped['ring_right'].name if player.inventory.equipped['ring_right'] else None}"
    )

    # 装備状態を詳細チェック
    print("\n詳細チェック:")
    print(f"  装備状態: {[(slot, item.name if item else None) for slot, item in player.inventory.equipped.items()]}")
    print(f"  インベントリ内容: {[item.name for item in player.inventory.items]}")

    # get_equipped_item_name の結果を確認
    print("\nget_equipped_item_name の結果:")
    print(f"  武器: {player.inventory.get_equipped_item_name('weapon')}")
    print(f"  防具: {player.inventory.get_equipped_item_name('armor')}")
    print(f"  左手指輪: {player.inventory.get_equipped_item_name('ring_left')}")
    print(f"  右手指輪: {player.inventory.get_equipped_item_name('ring_right')}")

    # ボーナス計算を確認
    print("\nボーナス計算:")
    print(f"  攻撃ボーナス: {player.inventory.get_attack_bonus()}")
    print(f"  防御ボーナス: {player.inventory.get_defense_bonus()}")
    print(f"  プレイヤー総攻撃力: {player.get_attack()}")
    print(f"  プレイヤー総防御力: {player.get_defense()}")

    # 各指輪の効果を個別確認
    print("\n指輪効果の個別確認:")
    left_ring = player.inventory.equipped["ring_left"]
    right_ring = player.inventory.equipped["ring_right"]

    if left_ring:
        print(f"  左手指輪: {left_ring.name}, effect={left_ring.effect}, bonus={left_ring.bonus}")
    if right_ring:
        print(f"  右手指輪: {right_ring.name}, effect={right_ring.effect}, bonus={right_ring.bonus}")

    # is_equipped チェック
    print("\nis_equipped チェック:")
    for item in player.inventory.items:
        is_eq = player.inventory.is_equipped(item)
        slot = player.inventory.get_equipped_slot(item) if is_eq else None
        print(f"  {item.name}: equipped={is_eq}, slot={slot}")


if __name__ == "__main__":
    test_inventory_display_bug()
