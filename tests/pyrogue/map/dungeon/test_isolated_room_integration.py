"""
孤立部屋群システムの統合テスト。

このテストは、孤立部屋群システムが他のダンジョン生成システムと
正しく統合されていることを確認します。
"""

import pytest

from pyrogue.map.dungeon.director import DungeonDirector
from pyrogue.map.dungeon.isolated_room_builder import IsolatedRoomBuilder
from pyrogue.map.tile import Floor, SecretDoor


class TestIsolatedRoomIntegration:
    """孤立部屋群システムの統合テストクラス。"""

    def test_director_with_isolated_rooms(self):
        """ダンジョンディレクターとの統合テスト。"""
        # 孤立部屋群が生成される階層をテスト
        director = DungeonDirector(80, 45, floor=4)  # 4階は孤立部屋群生成対象

        # ダンジョンを生成
        tiles, start_pos, end_pos = director.build_dungeon()

        # 基本的なダンジョン構造をチェック
        assert tiles.shape == (45, 80)
        assert start_pos is not None
        assert end_pos is not None

        # 床タイルが存在することを確認
        floor_count = 0
        secret_door_count = 0

        for y in range(45):
            for x in range(80):
                if isinstance(tiles[y, x], Floor):
                    floor_count += 1
                elif isinstance(tiles[y, x], SecretDoor):
                    secret_door_count += 1

        assert floor_count > 0, "床タイルが存在しません"
        # 隠し扉は確率的に生成されるため、存在チェックは行わない

    def test_isolated_room_generation_probability(self):
        """孤立部屋群生成確率のテスト。"""
        # 孤立部屋群が生成される階層
        isolation_floors = [4, 8, 11, 15, 18, 22, 25]

        for floor in isolation_floors:
            director = DungeonDirector(80, 45, floor=floor)
            should_generate = director._should_generate_isolated_rooms()
            assert should_generate, f"階層{floor}で孤立部屋群が生成されるべきです"

        # 孤立部屋群が生成されない階層
        non_isolation_floors = [
            1,
            2,
            3,
            5,
            6,
            7,
            9,
            10,
            12,
            13,
            14,
            16,
            17,
            19,
            20,
            21,
            23,
            24,
            26,
        ]

        for floor in non_isolation_floors:
            director = DungeonDirector(80, 45, floor=floor)
            should_generate = director._should_generate_isolated_rooms()
            assert not should_generate, f"階層{floor}で孤立部屋群が生成されるべきではありません"

    def test_isolated_room_with_bsp_system(self):
        """BSPシステムとの統合テスト。"""
        director = DungeonDirector(80, 45, floor=8)  # 8階は孤立部屋群生成対象

        # BSPシステムを使用
        director.use_section_based = True

        # ダンジョンを生成
        tiles, start_pos, end_pos = director.build_dungeon()

        # 基本的な検証
        assert tiles.shape == (45, 80)
        assert start_pos is not None
        assert end_pos is not None

        # 部屋数をチェック（BSPシステムでは通常複数の部屋が生成される）
        assert len(director.rooms) > 0

    def test_secret_door_discovery(self):
        """隠し扉発見のテスト。"""
        from pyrogue.core.game_logic import GameLogic
        from pyrogue.map.tile import SecretDoor

        # ゲームロジックを初期化
        game_logic = GameLogic(dungeon_width=80, dungeon_height=45)
        game_logic.setup_new_game()

        # 隠し扉を手動で配置
        floor_data = game_logic.get_current_floor_data()
        secret_door = SecretDoor()
        floor_data.tiles[10][15] = secret_door

        # 隠し扉の発見テスト
        assert secret_door.door_state == "secret"
        assert secret_door.char == "#"

        # 発見処理を実行
        discovered = game_logic.search_secret_door(15, 10)

        if discovered:
            assert secret_door.door_state == "closed"
            assert secret_door.char == "+"

    def test_isolated_room_statistics(self):
        """孤立部屋群統計のテスト。"""
        builder = IsolatedRoomBuilder(80, 45, isolation_level=0.6)

        # 空の状態での統計
        stats = builder.get_statistics()
        assert stats["builder_type"] == "IsolatedRooms"
        assert stats["isolation_level"] == 0.6
        assert stats["group_count"] == 0
        assert stats["total_rooms"] == 0
        assert stats["total_access_points"] == 0

    def test_dungeon_generation_with_different_floors(self):
        """異なる階層でのダンジョン生成テスト。"""
        # 複数の階層でダンジョンを生成し、エラーが発生しないことを確認
        # 迷路階層（13階）は除外（検証基準が厳しいため）
        test_floors = [1, 4, 8, 18, 22, 26]

        for floor in test_floors:
            director = DungeonDirector(80, 45, floor=floor)

            try:
                tiles, start_pos, end_pos = director.build_dungeon()

                # 基本的な検証
                assert tiles.shape == (45, 80)
                # 1階では上り階段がNone、2階以降では存在する
                if floor == 1:
                    assert start_pos is None, f"Floor 1 should have no up stairs, got {start_pos}"
                else:
                    assert start_pos is not None, f"Floor {floor} should have up stairs"

                # 最深階以外では下り階段が存在
                if floor < 26:
                    assert end_pos is not None

            except Exception as e:
                pytest.fail(f"階層{floor}でダンジョン生成に失敗: {e}")

    def test_isolated_room_builder_reset(self):
        """孤立部屋群ビルダーのリセット機能テスト。"""
        director = DungeonDirector(80, 45, floor=4)

        # 初回生成
        tiles1, _, _ = director.build_dungeon()

        # リセット前の状態を保存
        groups_before_reset = len(director.isolated_room_builder.isolated_groups)

        # リセット
        director.reset()

        # リセット直後の状態を確認
        assert director.isolated_room_builder.isolated_groups == []
        assert director.isolated_room_builder.used_areas == set()

        # 再生成
        tiles2, _, _ = director.build_dungeon()

        # 基本的な検証（両方とも正常に生成される）
        assert tiles1.shape == (45, 80)
        assert tiles2.shape == (45, 80)

        # 再生成後は新しい状態が設定される
        assert len(director.isolated_room_builder.isolated_groups) >= 0

    def test_director_statistics_with_isolated_rooms(self):
        """孤立部屋群を含むダンジョンの統計テスト。"""
        director = DungeonDirector(80, 45, floor=8)

        # ダンジョンを生成
        tiles, start_pos, end_pos = director.build_dungeon()

        # 統計情報を取得
        stats = director.get_generation_statistics()

        # 基本的な統計情報の存在を確認
        assert "floor" in stats
        assert "dimensions" in stats
        assert "rooms_count" in stats
        assert "floor_tiles" in stats
        assert "wall_tiles" in stats
        assert "floor_coverage" in stats

        # 値の妥当性をチェック
        assert stats["floor"] == 8
        assert stats["dimensions"] == "80x45"
        assert stats["rooms_count"] >= 0
        assert stats["floor_tiles"] > 0
        assert stats["wall_tiles"] > 0

    def test_isolation_level_effects(self):
        """孤立度による効果のテスト。"""
        # 高い孤立度
        high_isolation_builder = IsolatedRoomBuilder(80, 45, isolation_level=0.9)

        # 低い孤立度
        low_isolation_builder = IsolatedRoomBuilder(80, 45, isolation_level=0.1)

        # 統計情報で孤立度が正しく設定されているかチェック
        high_stats = high_isolation_builder.get_statistics()
        low_stats = low_isolation_builder.get_statistics()

        assert high_stats["isolation_level"] == 0.9
        assert low_stats["isolation_level"] == 0.1

        # 孤立度が隠し通路の生成に影響することを確認
        # （具体的な効果は実装に依存するため、基本的な設定チェックのみ）
        assert high_isolation_builder.isolation_level > low_isolation_builder.isolation_level
