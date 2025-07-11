"""
暗い部屋システムの統合テスト。

このテストは、暗い部屋システムが他のダンジョン生成システムと
正しく統合されていることを確認します。
"""

import pytest
import numpy as np

from pyrogue.map.dungeon.director import DungeonDirector
from pyrogue.map.dungeon.dark_room_builder import DarkRoom, DarkRoomBuilder
from pyrogue.map.tile import Floor, Wall
from pyrogue.entities.items.light_items import Torch, Lantern, LightRing


class TestDarkRoomIntegration:
    """暗い部屋システムの統合テストクラス。"""

    def test_director_with_dark_rooms(self):
        """ダンジョンディレクターとの統合テスト。"""
        # 暗い部屋が生成される階層をテスト
        director = DungeonDirector(80, 45, floor=6)  # 6階は暗い部屋生成対象

        # ダンジョンを生成
        tiles, start_pos, end_pos = director.build_dungeon()

        # 基本的なダンジョン構造をチェック
        assert tiles.shape == (45, 80)
        assert start_pos is not None
        assert end_pos is not None

        # 床タイルが存在することを確認
        floor_count = 0
        light_source_count = 0

        for y in range(45):
            for x in range(80):
                if isinstance(tiles[y, x], Floor):
                    floor_count += 1
                    # 光源タイルをチェック
                    if hasattr(tiles[y, x], 'has_light_source') and tiles[y, x].has_light_source:
                        light_source_count += 1

        assert floor_count > 0, "床タイルが存在しません"
        # 光源は確率的に生成されるため、存在チェックは行わない

    def test_dark_room_generation_probability(self):
        """暗い部屋生成確率のテスト。"""
        # 暗い部屋が生成される階層
        dark_room_floors = [6, 10, 14, 17, 20, 23, 24]

        for floor in dark_room_floors:
            director = DungeonDirector(80, 45, floor=floor)
            should_generate = director._should_generate_dark_rooms()
            assert should_generate, f"階層{floor}で暗い部屋が生成されるべきです"

        # 暗い部屋が生成されない階層
        non_dark_room_floors = [1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13, 15, 16, 18, 19, 21, 22, 25, 26]

        for floor in non_dark_room_floors:
            director = DungeonDirector(80, 45, floor=floor)
            should_generate = director._should_generate_dark_rooms()
            assert not should_generate, f"階層{floor}で暗い部屋が生成されるべきではありません"

    def test_dark_room_with_bsp_system(self):
        """BSPシステムとの統合テスト。"""
        director = DungeonDirector(80, 45, floor=6)  # 6階は暗い部屋生成対象（迷路ではない）

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

        # 暗い部屋ビルダーの統計を確認
        dark_stats = director.dark_room_builder.get_statistics()
        assert dark_stats["builder_type"] == "DarkRooms"

    def test_light_source_placement_in_dark_rooms(self):
        """暗い部屋での光源配置テスト。"""
        director = DungeonDirector(80, 45, floor=14)

        # ダンジョンを生成
        tiles, start_pos, end_pos = director.build_dungeon()

        # 光源が配置されているかチェック
        light_sources = director.dark_room_builder.light_sources

        for light_x, light_y in light_sources:
            # 光源位置が有効範囲内かチェック
            assert 0 <= light_x < 80
            assert 0 <= light_y < 45

            # 光源タイルが床または階段であることを確認
            light_tile = tiles[light_y, light_x]
            from pyrogue.map.tile import StairsUp, StairsDown
            assert isinstance(light_tile, (Floor, StairsUp, StairsDown))
            # 床タイルの場合のみ光源属性をチェック
            if isinstance(light_tile, Floor):
                assert hasattr(light_tile, 'has_light_source')
                assert light_tile.has_light_source

    def test_darkness_level_calculation(self):
        """暗さレベル計算のテスト。"""
        director = DungeonDirector(80, 45, floor=17)

        # ダンジョンを生成
        tiles, start_pos, end_pos = director.build_dungeon()

        # 暗い部屋の暗さレベルをチェック
        dark_rooms = director.dark_room_builder.dark_rooms

        for dark_room in dark_rooms:
            assert isinstance(dark_room, DarkRoom)
            assert dark_room.is_dark
            assert 0.0 < dark_room.darkness_level <= 1.0
            assert dark_room.base_visibility_range >= 1

    def test_visibility_range_with_light_sources(self):
        """光源による視界範囲のテスト。"""
        director = DungeonDirector(80, 45, floor=20)
        dark_room_builder = director.dark_room_builder

        # 暗い部屋を手動で作成
        dark_room = DarkRoom(20, 20, 10, 8, darkness_level=0.9)
        rooms = [dark_room]

        # 光源なしの場合
        visibility_no_light = dark_room_builder.get_visibility_range_at(
            25, 24, rooms, player_has_light=False
        )

        # 光源ありの場合
        visibility_with_light = dark_room_builder.get_visibility_range_at(
            25, 24, rooms, player_has_light=True, light_radius=5
        )

        # 光源ありの方が視界が広い
        assert visibility_with_light > visibility_no_light

    def test_light_influence_calculation(self):
        """光の影響度計算のテスト。"""
        director = DungeonDirector(80, 45, floor=23)
        dark_room_builder = director.dark_room_builder

        # 光源を設定
        light_sources = [(15, 15), (25, 25)]

        # 光源の近くでは影響度が高い
        influence_near = dark_room_builder.get_light_influence_at(16, 15, light_sources)
        assert influence_near > 0.5

        # 光源から離れた場所では影響度が低い
        influence_far = dark_room_builder.get_light_influence_at(35, 35, light_sources)
        assert influence_far == 0.0

    def test_dungeon_generation_with_different_floors(self):
        """異なる階層でのダンジョン生成テスト。"""
        # 暗い部屋が生成される階層のテスト
        test_floors = [6, 10, 14, 17, 20, 23, 24]

        for floor in test_floors:
            director = DungeonDirector(80, 45, floor=floor)

            try:
                tiles, start_pos, end_pos = director.build_dungeon()

                # 基本的な検証
                assert tiles.shape == (45, 80)
                assert start_pos is not None

                # 最深階以外では下り階段が存在
                if floor < 26:
                    assert end_pos is not None

                # 暗い部屋ビルダーが初期化されていることを確認
                assert director.dark_room_builder is not None

            except Exception as e:
                pytest.fail(f"階層{floor}でダンジョン生成に失敗: {e}")

    def test_dark_room_builder_reset(self):
        """暗い部屋ビルダーのリセット機能テスト。"""
        director = DungeonDirector(80, 45, floor=14)

        # 初回生成
        tiles1, _, _ = director.build_dungeon()

        # 暗い部屋の状態を保存
        dark_rooms_before = len(director.dark_room_builder.dark_rooms)
        light_sources_before = len(director.dark_room_builder.light_sources)

        # リセット
        director.reset()

        # リセット直後の状態を確認
        assert director.dark_room_builder.dark_rooms == []
        assert director.dark_room_builder.light_sources == []

        # 再生成
        tiles2, _, _ = director.build_dungeon()

        # 基本的な検証（両方とも正常に生成される）
        assert tiles1.shape == (45, 80)
        assert tiles2.shape == (45, 80)

    def test_director_statistics_with_dark_rooms(self):
        """暗い部屋を含むダンジョンの統計テスト。"""
        director = DungeonDirector(80, 45, floor=17)

        # ダンジョンを生成
        tiles, start_pos, end_pos = director.build_dungeon()

        # 暗い部屋の統計情報を取得
        dark_stats = director.dark_room_builder.get_statistics()

        # 基本的な統計情報の存在を確認
        assert "builder_type" in dark_stats
        assert "darkness_intensity" in dark_stats
        assert "dark_rooms_count" in dark_stats
        assert "light_sources_count" in dark_stats
        assert "average_darkness_level" in dark_stats

        # 値の妥当性をチェック
        assert dark_stats["builder_type"] == "DarkRooms"
        assert 0.0 <= dark_stats["darkness_intensity"] <= 1.0
        assert dark_stats["dark_rooms_count"] >= 0
        assert dark_stats["light_sources_count"] >= 0
        assert 0.0 <= dark_stats["average_darkness_level"] <= 1.0

    def test_darkness_intensity_effects(self):
        """暗さ強度による効果のテスト。"""
        # 高い暗さ強度
        high_darkness_builder = DarkRoomBuilder(darkness_intensity=0.9)

        # 低い暗さ強度
        low_darkness_builder = DarkRoomBuilder(darkness_intensity=0.2)

        # 統計情報で暗さ強度が正しく設定されているかチェック
        high_stats = high_darkness_builder.get_statistics()
        low_stats = low_darkness_builder.get_statistics()

        assert high_stats["darkness_intensity"] == 0.9
        assert low_stats["darkness_intensity"] == 0.2

        # 暗さ強度が部屋の変換に影響することを確認
        assert high_darkness_builder.darkness_intensity > low_darkness_builder.darkness_intensity

    def test_special_room_exclusion_from_darkness(self):
        """特別な部屋が暗くならないことの確認テスト。"""
        from pyrogue.map.dungeon.room_builder import Room

        builder = DarkRoomBuilder(darkness_intensity=1.0)

        # 特別な部屋（アミュレット部屋）を作成
        amulet_room = Room(10, 10, 8, 6)
        amulet_room.is_special = True
        amulet_room.room_type = "amulet_chamber"

        # 通常の部屋を作成
        normal_room = Room(25, 15, 6, 5)

        rooms = [amulet_room, normal_room]

        # 100%の確率で暗くしようとする
        dark_rooms = builder.apply_darkness_to_rooms(rooms, darkness_probability=1.0)

        # アミュレット部屋は除外され、通常の部屋のみが暗くなる
        assert len(dark_rooms) == 1
        dark_room_ids = [room.id for room in dark_rooms]
        assert normal_room.id in dark_room_ids


class TestLightItemsIntegration:
    """光源アイテムとの統合テストクラス。"""

    def test_light_items_basic_functionality(self):
        """光源アイテムの基本機能テスト。"""
        # 各種光源アイテムを作成
        torch = Torch(duration=100)
        lantern = Lantern(duration=200)
        ring = LightRing(light_radius=4)

        # 点灯/装備
        torch.use_light()
        lantern.use_light()
        ring.use_light()

        # 光源としての機能をテスト
        assert torch.get_light_radius() > 0
        assert lantern.get_light_radius() > 0
        assert ring.get_light_radius() > 0

        # 燃料消費テスト（指輪は永続）
        torch.consume_fuel(50)
        lantern.consume_fuel(50)

        assert torch.remaining_duration == 50
        assert lantern.remaining_duration == 150
        assert not ring.is_depleted()  # 指輪は永続

    def test_visibility_calculation_with_light_items(self):
        """光源アイテムによる視界計算テスト。"""
        from pyrogue.map.dungeon.dark_room_builder import DarkRoomBuilder

        builder = DarkRoomBuilder()

        # 暗い部屋を作成
        dark_room = DarkRoom(10, 10, 8, 6, darkness_level=0.8)
        rooms = [dark_room]

        # 異なる光源での視界範囲をテスト
        torch_visibility = builder.get_visibility_range_at(
            12, 12, rooms, True, 4  # たいまつの光量
        )

        lantern_visibility = builder.get_visibility_range_at(
            12, 12, rooms, True, 6  # ランタンの光量
        )

        ring_visibility = builder.get_visibility_range_at(
            12, 12, rooms, True, 3  # 指輪の光量
        )

        # ランタンが最も明るく、たいまつがその次、指輪が最も暗い
        assert lantern_visibility >= torch_visibility >= ring_visibility
