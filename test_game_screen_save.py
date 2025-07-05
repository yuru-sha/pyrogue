#!/usr/bin/env python3
"""
GameScreenのセーブ/ロード機能のテスト
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pyrogue.core.engine import Engine
from pyrogue.ui.screens.game_screen import GameScreen

def test_game_screen_save_load():
    """GameScreenのセーブ/ロード機能をテスト"""
    print("=== GameScreenセーブ/ロード機能テスト ===")
    
    try:
        # Engineを作成（最小限の設定）
        engine = Engine()
        
        # GameScreenを作成
        game_screen = GameScreen(engine)
        
        # テスト用データを設定
        original_x = game_screen.player_x = 15
        original_y = game_screen.player_y = 10
        original_floor = game_screen.current_floor = 3
        original_hp = game_screen.player_stats["hp"] = 18
        original_gold = game_screen.player_stats["gold"] = 200
        
        print(f"セーブ前の状態:")
        print(f"  位置: ({original_x}, {original_y})")
        print(f"  階層: {original_floor}")
        print(f"  HP: {original_hp}")
        print(f"  Gold: {original_gold}")
        
        # セーブ
        print("\n1. セーブを実行...")
        save_success = game_screen.save_game()
        print(f"   セーブ結果: {'成功' if save_success else '失敗'}")
        
        # ゲーム状態を変更
        game_screen.player_x = 99
        game_screen.player_y = 99
        game_screen.current_floor = 99
        game_screen.player_stats["hp"] = 1
        game_screen.player_stats["gold"] = 999
        
        print(f"\n変更後の状態:")
        print(f"  位置: ({game_screen.player_x}, {game_screen.player_y})")
        print(f"  階層: {game_screen.current_floor}")
        print(f"  HP: {game_screen.player_stats['hp']}")
        print(f"  Gold: {game_screen.player_stats['gold']}")
        
        # ロード
        print("\n2. ロードを実行...")
        load_success = game_screen.load_game()
        print(f"   ロード結果: {'成功' if load_success else '失敗'}")
        
        if load_success:
            print(f"\nロード後の状態:")
            print(f"  位置: ({game_screen.player_x}, {game_screen.player_y})")
            print(f"  階層: {game_screen.current_floor}")
            print(f"  HP: {game_screen.player_stats['hp']}")
            print(f"  Gold: {game_screen.player_stats['gold']}")
            
            # 復元確認
            restored_correctly = (
                game_screen.player_x == original_x and
                game_screen.player_y == original_y and
                game_screen.current_floor == original_floor and
                game_screen.player_stats["hp"] == original_hp and
                game_screen.player_stats["gold"] == original_gold
            )
            print(f"\n復元確認: {'正常' if restored_correctly else '異常'}")
        
        # 死亡テスト
        print("\n3. 死亡時のパーマデス処理をテスト...")
        game_screen.player_stats["hp"] = 0
        game_screen.check_player_death()
        
        # 死亡後のロード試行
        load_after_death = game_screen.load_game()
        print(f"   死亡後のロード結果: {'成功' if load_after_death else '失敗（正常）'}")
        
        print("\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_game_screen_save_load()