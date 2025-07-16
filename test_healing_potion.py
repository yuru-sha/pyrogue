#!/usr/bin/env python3
"""
ヒーリングポーションのスタック数減少テスト
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pyrogue.core.managers.game_context import GameContext
from pyrogue.entities.actors.player import Player
from pyrogue.entities.items.effects import HealingEffect
from pyrogue.entities.items.item import Potion


def test_healing_potion_stack_reduction():
    """ヒーリングポーションのスタック数減少テスト"""
    print("=== ヒーリングポーションのスタック数減少テスト ===")

    # プレイヤーを作成
    player = Player(40, 23)

    # ヒーリングポーションを作成（スタック数3）
    healing_potion = Potion(0, 0, "Healing Potion", HealingEffect(10))
    healing_potion.stack_count = 3

    # インベントリに追加
    player.inventory.add_item(healing_potion)

    print("初期状態:")
    print(f"  プレイヤーHP: {player.hp}/{player.max_hp}")
    print(f"  ポーション数: {healing_potion.stack_count}")

    # GameContextを作成
    message_log = []
    context = GameContext(
        player=player,
        inventory=player.inventory,
        dungeon_manager=None,  # テスト用のダミー
        message_log=message_log,
    )

    # 1回目の使用（HPが満タンの場合）
    print("\n1回目の使用 (HP満タン):")
    success = player.use_item(healing_potion, context)
    print(f"  使用成功: {success}")
    print(f"  プレイヤーHP: {player.hp}/{player.max_hp}")
    print(f"  ポーション数: {healing_potion.stack_count}")
    print(f"  メッセージ: {message_log}")

    # HPを減らす
    player.hp = 15
    print("\nHPを15に減らしました")
    print(f"  プレイヤーHP: {player.hp}/{player.max_hp}")

    # 2回目の使用（HPが減っている場合）
    print("\n2回目の使用 (HP減少中):")
    success = player.use_item(healing_potion, context)
    print(f"  使用成功: {success}")
    print(f"  プレイヤーHP: {player.hp}/{player.max_hp}")
    print(f"  ポーション数: {healing_potion.stack_count}")
    print(f"  メッセージ: {message_log}")

    # 3回目の使用（最後の1個）
    print("\n3回目の使用 (最後の1個):")
    print(f"  使用前のインベントリ: {player.inventory.items}")
    print(f"  使用前のスタック数: {healing_potion.stack_count}")
    success = player.use_item(healing_potion, context)
    print(f"  使用成功: {success}")
    print(f"  プレイヤーHP: {player.hp}/{player.max_hp}")
    print(f"  ポーション数: {healing_potion.stack_count}")
    print(f"  インベントリに残っているか: {healing_potion in player.inventory.items}")
    print(f"  使用後のインベントリ: {player.inventory.items}")
    print(f"  最終メッセージ: {message_log}")


def test_other_stackable_items():
    """他のスタック可能アイテムのテスト"""
    print("\n=== 他のスタック可能アイテムのテスト ===")

    # プレイヤーを作成
    player = Player(40, 23)

    # 食料を作成
    from pyrogue.entities.items.effects import FOOD_BREAD
    from pyrogue.entities.items.item import Food

    bread = Food(0, 0, "Bread", FOOD_BREAD)
    bread.stack_count = 2

    # インベントリに追加
    player.inventory.add_item(bread)

    print("初期状態:")
    print(f"  プレイヤー満腹度: {player.hunger}")
    print(f"  パン数: {bread.stack_count}")

    # GameContextを作成
    message_log = []
    context = GameContext(
        player=player,
        inventory=player.inventory,
        dungeon_manager=None,  # テスト用のダミー
        message_log=message_log,
    )

    # 1回目の使用
    print("\n1回目の使用:")
    success = player.use_item(bread, context)
    print(f"  使用成功: {success}")
    print(f"  プレイヤー満腹度: {player.hunger}")
    print(f"  パン数: {bread.stack_count}")
    print(f"  インベントリに残っているか: {bread in player.inventory.items}")

    # 2回目の使用（最後の1個）
    print("\n2回目の使用 (最後の1個):")
    success = player.use_item(bread, context)
    print(f"  使用成功: {success}")
    print(f"  プレイヤー満腹度: {player.hunger}")
    print(f"  パン数: {bread.stack_count}")
    print(f"  インベントリに残っているか: {bread in player.inventory.items}")
    print(f"  使用後のインベントリ: {player.inventory.items}")


if __name__ == "__main__":
    test_healing_potion_stack_reduction()
    test_other_stackable_items()
