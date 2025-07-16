#!/usr/bin/env python3
"""
杖の方向選択デバッグ
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pyrogue.entities.actors.player import Player
from pyrogue.entities.items.effects import MagicMissileWandEffect, NothingWandEffect
from pyrogue.entities.items.item import Wand


def debug_wand_direction():
    """杖の方向選択デバッグ"""
    print("=== 杖の方向選択デバッグ ===")

    # プレイヤーを作成
    player = Player(40, 23)

    # Magic Missile杖を作成
    magic_missile_wand = Wand(0, 0, "Wand of Magic Missiles", MagicMissileWandEffect(), 5)
    nothing_wand = Wand(0, 0, "Wand of Nothing", NothingWandEffect(), 5)

    print("Magic Missile Wand:")
    print(f"  name: {magic_missile_wand.name}")
    print(f"  effect: {magic_missile_wand.effect}")
    print(f"  effect type: {type(magic_missile_wand.effect)}")
    print(f"  charges: {magic_missile_wand.charges}")

    print("\nNothing Wand:")
    print(f"  name: {nothing_wand.name}")
    print(f"  effect: {nothing_wand.effect}")
    print(f"  effect type: {type(nothing_wand.effect)}")
    print(f"  charges: {nothing_wand.charges}")

    # apply_effectメソッドのテスト
    print("\n=== apply_effect テスト ===")

    # Magic Missile Wandのテスト
    print("Magic Missile Wand apply_effect:")
    try:
        # 簡単なcontextを作成
        class SimpleContext:
            def __init__(self, player):
                self.player = player
                self.messages = []

            def add_message(self, msg):
                self.messages.append(msg)
                print(f"  MESSAGE: {msg}")

        context = SimpleContext(player)

        # 方向を指定してテスト
        direction = (0, 1)  # 下方向
        result = magic_missile_wand.apply_effect(context, direction)
        print(f"  result: {result}")
        print(f"  messages: {context.messages}")

    except Exception as e:
        print(f"  Error: {e}")
        import traceback

        traceback.print_exc()

    # Nothing Wandのテスト
    print("\nNothing Wand apply_effect:")
    try:
        context = SimpleContext(player)
        direction = (0, 1)  # 下方向
        result = nothing_wand.apply_effect(context, direction)
        print(f"  result: {result}")
        print(f"  messages: {context.messages}")

    except Exception as e:
        print(f"  Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_wand_direction()
