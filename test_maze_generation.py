#!/usr/bin/env python3
"""
迷路生成テスト
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pyrogue.map.dungeon_manager import DungeonManager
from pyrogue.entities.actors.player import Player

def test_maze_generation():
    """迷路生成のテスト"""
    print("=== 迷路生成テスト ===")
    
    # プレイヤーを作成
    player = Player(40, 23)
    
    # ダンジョンマネージャーを作成
    dungeon_manager = DungeonManager()
    
    # 複数の階層を生成してテスト
    for floor in range(1, 6):
        try:
            print(f"\n階層 {floor} を生成中...")
            floor_data = dungeon_manager.get_floor(floor)
            height, width = floor_data.tiles.shape
            print(f"  成功: 階層 {floor} ({width}x{height})")
            
            # 階層タイプを確認
            floor_type = "迷路" if floor >= 5 else "通常"
            print(f"  タイプ: {floor_type}")
            
        except Exception as e:
            print(f"  エラー: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_maze_generation()