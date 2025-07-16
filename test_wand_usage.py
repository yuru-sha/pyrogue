#!/usr/bin/env python3
"""
杖の使用方法テスト
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pyrogue.entities.actors.player import Player
from pyrogue.entities.items.item import Wand
from pyrogue.entities.items.effects import MagicMissileWandEffect
from pyrogue.core.managers.game_context import GameContext

def test_wand_usage():
    """杖の使用方法テスト"""
    print("=== 杖の使用方法テスト ===")
    
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
    
    # 杖を作成
    magic_missile_wand = Wand(0, 0, "Wand of Magic Missiles", MagicMissileWandEffect(), 5)
    
    # インベントリに追加
    player.inventory.add_item(magic_missile_wand)
    
    print(f"初期状態:")
    print(f"  インベントリ: {[item.name for item in player.inventory.items]}")
    print(f"  杖のチャージ: {magic_missile_wand.charges}")
    print(f"  杖のhas_charges(): {magic_missile_wand.has_charges()}")
    
    # 杖の使用を試す
    print(f"\n=== 杖の使用テスト ===")
    
    # apply_effectの確認（ダンジョンが必要なのでスキップ）
    print(f"杖のapply_effect呼び出し:")
    print(f"  ダンジョンが必要なのでスキップ")
    
    # player.use_itemでの使用確認
    print(f"\nplayer.use_itemでの使用確認:")
    message_log.clear()
    try:
        success = player.use_item(magic_missile_wand, context)
        print(f"  成功: {success}")
        print(f"  メッセージ: {message_log}")
    except Exception as e:
        print(f"  エラー: {e}")
    
    # 杖が使用可能アイテムかチェック
    print(f"\n=== 杖の属性確認 ===")
    print(f"  type: {type(magic_missile_wand)}")
    print(f"  hasattr(charges): {hasattr(magic_missile_wand, 'charges')}")
    print(f"  charges: {magic_missile_wand.charges}")
    print(f"  has_charges(): {magic_missile_wand.has_charges()}")
    print(f"  apply_effect method: {hasattr(magic_missile_wand, 'apply_effect')}")
    
    # インベントリでの使用可能性をチェック
    print(f"\n=== インベントリでの使用可能性 ===")
    from pyrogue.entities.items.item import Scroll, Potion, Food
    print(f"  isinstance(Scroll): {isinstance(magic_missile_wand, Scroll)}")
    print(f"  isinstance(Potion): {isinstance(magic_missile_wand, Potion)}")
    print(f"  isinstance(Food): {isinstance(magic_missile_wand, Food)}")
    print(f"  isinstance(Wand): {isinstance(magic_missile_wand, Wand)}")
    
    # 複数回使用してチャージ消費を確認（ダンジョンが必要なのでスキップ）
    print(f"\n=== 複数回使用テスト ===")
    print(f"  ダンジョンが必要なのでスキップ")

if __name__ == "__main__":
    test_wand_usage()