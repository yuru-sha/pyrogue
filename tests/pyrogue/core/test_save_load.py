#!/usr/bin/env python3
"""
セーブ/ロード機能のテスト
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pyrogue.core.save_manager import SaveManager


def test_save_load():
    """セーブ/ロード機能をテスト"""
    print("=== セーブ/ロード機能テスト ===")

    # SaveManagerをテスト
    save_manager = SaveManager()

    # テスト用のゲームデータ
    test_data = {
        "player_x": 10,
        "player_y": 5,
        "current_floor": 2,
        "player_stats": {
            "level": 3,
            "hp": 15,
            "hp_max": 20,
            "attack": 8,
            "defense": 5,
            "gold": 150,
        },
        "inventory_items": [],
        "floor_data": {},
    }

    # セーブテスト
    print("1. セーブ機能をテスト...")
    success = save_manager.save_game_state(test_data)
    print(f"   セーブ結果: {'成功' if success else '失敗'}")

    # セーブファイルの存在チェック
    has_save = save_manager.has_save_file()
    print(f"   セーブファイル存在: {'はい' if has_save else 'いいえ'}")

    # ロードテスト
    print("2. ロード機能をテスト...")
    loaded_data = save_manager.load_game_state()
    if loaded_data:
        print("   ロード成功")
        print(
            f"   プレイヤー位置: ({loaded_data['player_x']}, {loaded_data['player_y']})"
        )
        print(f"   現在階層: {loaded_data['current_floor']}")
        print(
            f"   プレイヤーHP: {loaded_data['player_stats']['hp']}/{loaded_data['player_stats']['hp_max']}"
        )
    else:
        print("   ロード失敗")

    # パーマデステスト
    print("3. パーマデス機能をテスト...")
    # プレイヤーを死亡状態にする
    test_data["player_stats"]["hp"] = 0
    save_manager.trigger_permadeath_on_death(test_data)

    # セーブファイルが削除されているかチェック
    has_save_after_death = save_manager.has_save_file()
    print(
        f"   死亡後のセーブファイル存在: {'はい' if has_save_after_death else 'いいえ'}"
    )

    # 死亡後のロード試行
    loaded_after_death = save_manager.load_game_state()
    print(f"   死亡後のロード結果: {'成功' if loaded_after_death else '失敗（正常）'}")

    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_save_load()
