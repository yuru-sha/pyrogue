#!/usr/bin/env python3
"""NPCシステムの統合テスト"""

from pyrogue.map.dungeon.director import DungeonDirector
from pyrogue.entities.actors.npc_spawner import NPCSpawner

def test_npc_integration():
    """NPCシステムの統合テスト"""
    print("NPCシステムの統合テスト開始...")

    # ダンジョンを生成
    director = DungeonDirector(80, 50, floor=1)
    tiles, up_pos, down_pos = director.build_dungeon()

    print(f"ダンジョン生成完了: {len(director.rooms)}個の部屋")

    # NPCを配置
    npc_spawner = NPCSpawner(floor=1)
    npc_spawner.spawn_npcs(tiles, director.rooms)

    print(f"NPC配置完了: {len(npc_spawner.npcs)}個のNPC")

    # NPCの詳細を表示
    for i, npc in enumerate(npc_spawner.npcs):
        print(f"  NPC {i+1}: {npc.name} (種類: {npc.npc_type}, 位置: ({npc.x}, {npc.y}))")

    # 特別な部屋のNPCを確認
    special_npcs = [npc for npc in npc_spawner.npcs if npc.npc_type.value in ['MERCHANT', 'PRIEST', 'MAGE']]
    print(f"特別な部屋のNPC: {len(special_npcs)}個")

    print("統合テスト完了！")

if __name__ == "__main__":
    test_npc_integration()
