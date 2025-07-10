#!/usr/bin/env python3
"""
BSPダンジョン生成の部屋アスペクト比テスト
"""

import numpy as np
import pytest
from pyrogue.map.dungeon.section_based_builder import BSPDungeonBuilder
from pyrogue.map.tile import Wall


def test_room_aspect_ratios():
    """部屋のアスペクト比をテストする"""
    width, height = 80, 45
    builder = BSPDungeonBuilder(width, height)

    # 複数回テストして統計を取る
    total_rooms = 0
    thin_rooms = 0
    aspect_ratios = []

    for test_run in range(10):
        # 初期タイル（全て壁）
        tiles = np.full((height, width), Wall(), dtype=object)

        # ダンジョン生成
        builder.reset()
        rooms = builder.build_dungeon(tiles)

        for room in rooms:
            total_rooms += 1
            aspect_ratio = max(room.width, room.height) / min(room.width, room.height)
            aspect_ratios.append(aspect_ratio)

            if aspect_ratio > 2.0:
                thin_rooms += 1
                print(f"細い部屋: {room.width}x{room.height} (比率: {aspect_ratio:.2f})")

    print(f"\n=== 部屋アスペクト比統計 ===")
    print(f"総部屋数: {total_rooms}")
    print(f"細い部屋数 (2:1以上): {thin_rooms}")
    print(f"細い部屋の割合: {thin_rooms/total_rooms*100:.1f}%")
    print(f"平均アスペクト比: {np.mean(aspect_ratios):.2f}")
    print(f"最大アスペクト比: {max(aspect_ratios):.2f}")
    print(f"最小アスペクト比: {min(aspect_ratios):.2f}")

    # 理想的な結果
    if thin_rooms / total_rooms < 0.1:  # 10%未満
        print("✅ 改善成功: 細い部屋の割合が10%未満")
    else:
        print("❌ 改善不十分: 細い部屋の割合が10%以上")


if __name__ == "__main__":
    test_room_aspect_ratios()
