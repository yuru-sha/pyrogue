#!/usr/bin/env python3
"""
corridor_builder のデバッグ
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from pyrogue.map.dungeon.corridor_builder import CorridorBuilder
from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Wall

def debug_corridor_builder():
    """corridor_builder のデバッグ"""
    print("=== corridor_builder デバッグ ===")
    
    builder = CorridorBuilder(80, 25)
    tiles = np.full((25, 80), Wall(), dtype=object)
    
    room1 = Room(1, 10, 10, 8, 6)
    room2 = Room(2, 30, 10, 8, 6)
    
    print(f"Room1: id={room1.id}, center={room1.center()}, bounds=({room1.x}, {room1.y}, {room1.width}, {room1.height})")
    print(f"Room2: id={room2.id}, center={room2.center()}, bounds=({room2.x}, {room2.y}, {room2.width}, {room2.height})")
    
    # 接続点を確認
    start_point = builder._find_connection_point(room1, room2)
    end_point = builder._find_connection_point(room2, room1)
    
    print(f"Start point: {start_point}")
    print(f"End point: {end_point}")
    
    # 直線通路の作成をテスト
    print(f"\n=== 直線通路の作成 ===")
    if start_point and end_point:
        try:
            corridor_points = builder._create_straight_corridor(start_point, end_point, tiles)
            print(f"Corridor points: {len(corridor_points)} points")
            if corridor_points:
                print(f"First few points: {corridor_points[:5]}")
                print(f"Last few points: {corridor_points[-5:]}")
        except Exception as e:
            print(f"Error in _create_straight_corridor: {e}")
            import traceback
            traceback.print_exc()
    
    # 実際の connect_rooms_rogue_style を試す
    print(f"\n=== connect_rooms_rogue_style テスト ===")
    try:
        # タイムアウト処理をシミュレート
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Function timed out")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)  # 5秒でタイムアウト
        
        corridors = builder.connect_rooms_rogue_style([room1, room2], tiles)
        signal.alarm(0)  # タイムアウトを解除
        
        print(f"Success! Corridors: {len(corridors)}")
        for i, corridor in enumerate(corridors):
            print(f"  Corridor {i}: {len(corridor.points)} points")
            
    except TimeoutError:
        print("Timeout! 無限ループの可能性あり")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_corridor_builder()