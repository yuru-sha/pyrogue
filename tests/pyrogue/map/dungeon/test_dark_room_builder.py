"""
暗い部屋ビルダーのテスト。

このテストは、暗い部屋生成システムが正常に動作することを確認します。
"""

import pytest
import numpy as np

from pyrogue.map.dungeon.dark_room_builder import DarkRoomBuilder, DarkRoom
from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Floor, Wall


class TestDarkRoomBuilder:
    """暗い部屋ビルダーのテストクラス。"""

    def test_initialization(self):
        """初期化テスト。"""
        builder = DarkRoomBuilder(darkness_intensity=0.7)

        assert builder.darkness_intensity == 0.7
        assert builder.dark_rooms == []
        assert builder.light_sources == []

    def test_dark_room_creation(self):
        """暗い部屋の作成テスト。"""
        dark_room = DarkRoom(10, 10, 8, 6, darkness_level=0.8)

        assert dark_room.x == 10
        assert dark_room.y == 10
        assert dark_room.width == 8
        assert dark_room.height == 6
        assert dark_room.is_dark
        assert dark_room.darkness_level == 0.8
        assert dark_room.requires_light
        assert dark_room.room_type == "dark"
        assert dark_room.base_visibility_range > 0

    def test_convert_to_dark_room(self):
        """通常の部屋を暗い部屋に変換するテスト。"""
        builder = DarkRoomBuilder(darkness_intensity=0.6)

        # 通常の部屋を作成
        normal_room = Room(5, 5, 10, 8)
        normal_room.id = "test_room"
        normal_room.room_type = "normal"
        normal_room.connected_rooms.add("room1")
        normal_room.doors.append((7, 5))

        # 暗い部屋に変換
        dark_room = builder._convert_to_dark_room(normal_room)

        assert isinstance(dark_room, DarkRoom)
        assert dark_room.x == normal_room.x
        assert dark_room.y == normal_room.y
        assert dark_room.width == normal_room.width
        assert dark_room.height == normal_room.height
        assert dark_room.id == normal_room.id
        assert dark_room.is_dark
        assert dark_room.darkness_level > 0.4  # 最低でも0.4以上
        assert dark_room.darkness_level <= 1.0
        assert "room1" in dark_room.connected_rooms
        assert (7, 5) in dark_room.doors

    def test_apply_darkness_to_rooms(self):
        """部屋群に暗さを適用するテスト。"""
        builder = DarkRoomBuilder(darkness_intensity=0.8)

        # 複数の部屋を作成
        rooms = [
            Room(5, 5, 8, 6),
            Room(20, 10, 10, 8),
            Room(35, 15, 6, 5),
        ]

        # 各部屋にIDを設定
        for i, room in enumerate(rooms):
            room.id = f"room_{i}"

        # 暗い部屋に変換（100%の確率で変換）
        dark_rooms = builder.apply_darkness_to_rooms(rooms, darkness_probability=1.0)

        # 結果を検証
        assert len(dark_rooms) == 3
        for dark_room in dark_rooms:
            assert isinstance(dark_room, DarkRoom)
            assert dark_room.is_dark
            assert dark_room.darkness_level > 0.0

    def test_special_rooms_not_darkened(self):
        """特別な部屋が暗くならないテスト。"""
        builder = DarkRoomBuilder(darkness_intensity=0.8)

        # 特別な部屋を作成
        special_room = Room(10, 10, 8, 6)
        special_room.id = "special_room"
        special_room.is_special = True
        special_room.room_type = "amulet_chamber"

        # 通常の部屋を作成
        normal_room = Room(25, 15, 6, 5)
        normal_room.id = "normal_room"

        rooms = [special_room, normal_room]

        # 100%の確率で暗くしようとする
        dark_rooms = builder.apply_darkness_to_rooms(rooms, darkness_probability=1.0)

        # 特別な部屋は除外され、通常の部屋のみが暗くなる
        assert len(dark_rooms) == 1
        assert dark_rooms[0].id == "normal_room"

    def test_light_source_placement(self):
        """光源配置のテスト。"""
        builder = DarkRoomBuilder()

        # 暗い部屋を作成
        dark_room = DarkRoom(10, 10, 8, 6)
        dark_rooms = [dark_room]

        # タイル配列を初期化
        tiles = np.full((45, 80), Wall(), dtype=object)

        # 暗い部屋の内部を床に設定
        for y in range(dark_room.y + 1, dark_room.y + dark_room.height - 1):
            for x in range(dark_room.x + 1, dark_room.x + dark_room.width - 1):
                tiles[y, x] = Floor()

        # 光源を配置（100%の確率）
        builder.place_light_sources(dark_rooms, tiles, light_source_probability=1.0)

        # 光源が配置されたかチェック
        assert len(builder.light_sources) == 1

        # 光源が部屋内に配置されているかチェック
        light_x, light_y = builder.light_sources[0]
        assert dark_room.x < light_x < dark_room.x + dark_room.width
        assert dark_room.y < light_y < dark_room.y + dark_room.height

        # 光源タイルが設定されているかチェック
        light_tile = tiles[light_y, light_x]
        assert hasattr(light_tile, 'has_light_source')
        assert light_tile.has_light_source
        assert hasattr(light_tile, 'light_radius')
        assert light_tile.light_radius > 0

    def test_darkness_level_detection(self):
        """暗さレベル検出のテスト。"""
        builder = DarkRoomBuilder()

        # 暗い部屋を作成
        dark_room = DarkRoom(10, 10, 8, 6, darkness_level=0.7)
        rooms = [dark_room]

        # 暗い部屋内の位置をテスト
        darkness_level = builder.get_darkness_level_at(12, 12, rooms)
        assert darkness_level == 0.7

        # 暗い部屋外の位置をテスト
        darkness_level = builder.get_darkness_level_at(5, 5, rooms)
        assert darkness_level == 0.0

    def test_dark_room_detection(self):
        """暗い部屋検出のテスト。"""
        builder = DarkRoomBuilder()

        # 暗い部屋を作成
        dark_room = DarkRoom(10, 10, 8, 6)
        rooms = [dark_room]

        # 暗い部屋内の位置をテスト
        is_dark = builder.is_position_in_dark_room(12, 12, rooms)
        assert is_dark

        # 暗い部屋外の位置をテスト
        is_dark = builder.is_position_in_dark_room(5, 5, rooms)
        assert not is_dark

    def test_visibility_range_calculation(self):
        """視界範囲計算のテスト。"""
        builder = DarkRoomBuilder()

        # 暗い部屋を作成
        dark_room = DarkRoom(10, 10, 8, 6, darkness_level=0.8)
        rooms = [dark_room]

        # 光源なしの場合
        visibility_range = builder.get_visibility_range_at(12, 12, rooms, False)
        assert visibility_range < 8  # 通常より狭い

        # 光源ありの場合
        visibility_range = builder.get_visibility_range_at(12, 12, rooms, True, 6)
        assert visibility_range == 6  # 光源の範囲

        # 暗い部屋外の場合
        visibility_range = builder.get_visibility_range_at(5, 5, rooms, False)
        assert visibility_range == 8  # 通常の範囲

    def test_light_source_finding(self):
        """光源発見のテスト。"""
        builder = DarkRoomBuilder()

        # 光源を設定
        builder.light_sources = [(10, 10), (20, 20), (30, 30)]

        # 最も近い光源を検索
        nearest = builder.find_nearest_light_source(12, 12, max_distance=10)
        assert nearest == (10, 10)

        # 距離制限内の場合
        nearest = builder.find_nearest_light_source(32, 32, max_distance=5)
        assert nearest == (30, 30)

        # 範囲外の場合
        nearest = builder.find_nearest_light_source(50, 50, max_distance=5)
        assert nearest is None

    def test_light_influence_calculation(self):
        """光の影響度計算のテスト。"""
        builder = DarkRoomBuilder()

        # 光源を設定
        light_sources = [(10, 10)]

        # 光源の真上（影響度最大）
        influence = builder.get_light_influence_at(10, 10, light_sources)
        assert influence == 1.0

        # 光源から1セル離れた位置
        influence = builder.get_light_influence_at(11, 10, light_sources)
        assert 0.5 < influence < 1.0

        # 光源から3セル離れた位置（境界）
        influence = builder.get_light_influence_at(13, 10, light_sources)
        assert influence == 0.0

    def test_statistics_generation(self):
        """統計情報生成のテスト。"""
        builder = DarkRoomBuilder(darkness_intensity=0.7)

        # 暗い部屋を手動で設定
        dark_room1 = DarkRoom(5, 5, 8, 6, darkness_level=0.6)
        dark_room2 = DarkRoom(20, 10, 10, 8, darkness_level=0.8)
        builder.dark_rooms = [dark_room1, dark_room2]

        # 光源を設定
        builder.light_sources = [(10, 10), (25, 15)]

        stats = builder.get_statistics()

        assert stats["builder_type"] == "DarkRooms"
        assert stats["darkness_intensity"] == 0.7
        assert stats["dark_rooms_count"] == 2
        assert stats["light_sources_count"] == 2
        assert stats["average_darkness_level"] == 0.7  # (0.6 + 0.8) / 2

    def test_reset_functionality(self):
        """リセット機能のテスト。"""
        builder = DarkRoomBuilder()

        # 状態を設定
        dark_room = DarkRoom(10, 10, 8, 6)
        builder.dark_rooms = [dark_room]
        builder.light_sources = [(15, 15)]

        # リセットを実行
        builder.reset()

        # 状態がリセットされているかチェック
        assert builder.dark_rooms == []
        assert builder.light_sources == []


class TestDarkRoom:
    """暗い部屋クラスのテストクラス。"""

    def test_dark_room_initialization(self):
        """暗い部屋の初期化テスト。"""
        dark_room = DarkRoom(15, 20, 12, 10, darkness_level=0.9)

        assert dark_room.x == 15
        assert dark_room.y == 20
        assert dark_room.width == 12
        assert dark_room.height == 10
        assert dark_room.is_dark
        assert dark_room.darkness_level == 0.9
        assert dark_room.requires_light
        assert dark_room.room_type == "dark"
        assert dark_room.base_visibility_range >= 1

    def test_darkness_level_affects_visibility(self):
        """暗さレベルが視界に影響するテスト。"""
        # 暗さレベルが高い部屋
        very_dark_room = DarkRoom(5, 5, 8, 6, darkness_level=1.0)

        # 暗さレベルが低い部屋
        slightly_dark_room = DarkRoom(20, 10, 8, 6, darkness_level=0.3)

        # より暗い部屋の方が視界が狭い
        assert very_dark_room.base_visibility_range <= slightly_dark_room.base_visibility_range

    def test_dark_room_inheritance(self):
        """暗い部屋の継承テスト。"""
        dark_room = DarkRoom(10, 10, 8, 6)

        # Room クラスから継承したメソッドが使用可能
        center = dark_room.center()
        assert center == (14, 13)  # (10 + 8//2, 10 + 6//2)

        # 暗い部屋固有の属性も利用可能
        assert dark_room.is_dark
        assert dark_room.darkness_level > 0.0
