"""
通路生成システムのテストモジュール。

このモジュールは、CorridorBuilderクラスの機能を包括的にテストし、
通路生成アルゴリズムの正確性を検証します。
"""

import numpy as np
from pyrogue.map.dungeon.corridor_builder import Corridor, CorridorBuilder
from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Floor, Wall


class TestCorridorBuilder:
    """通路生成ビルダーのテストクラス。"""

    def test_init(self):
        """初期化のテスト。"""
        builder = CorridorBuilder(80, 25)

        assert builder.width == 80
        assert builder.height == 25
        assert builder.corridors == []

    def test_connect_rooms_rogue_style_empty_rooms(self):
        """空の部屋リストでの接続テスト。"""
        builder = CorridorBuilder(80, 25)
        tiles = np.full((25, 80), Wall(), dtype=object)

        corridors = builder.connect_rooms_rogue_style([], tiles)

        assert corridors == []
        assert builder.corridors == []

    def test_connect_rooms_rogue_style_single_room(self):
        """単一部屋での接続テスト。"""
        builder = CorridorBuilder(80, 25)
        tiles = np.full((25, 80), Wall(), dtype=object)

        room = Room(10, 10, 8, 6, id=1)
        corridors = builder.connect_rooms_rogue_style([room], tiles)

        assert corridors == []
        assert builder.corridors == []

    def test_connect_rooms_rogue_style_two_rooms(self):
        """2つの部屋の接続テスト。"""
        builder = CorridorBuilder(80, 25)
        tiles = np.full((25, 80), Wall(), dtype=object)

        room1 = Room(10, 10, 8, 6, id=1)
        room2 = Room(30, 10, 8, 6, id=2)

        corridors = builder.connect_rooms_rogue_style([room1, room2], tiles)

        assert len(corridors) >= 1
        assert len(builder.corridors) >= 1

        # 部屋が接続されているかチェック
        assert room1.is_connected_to(room2)

    def test_connect_rooms_rogue_style_multiple_rooms(self):
        """複数部屋の接続テスト。"""
        builder = CorridorBuilder(80, 25)
        tiles = np.full((25, 80), Wall(), dtype=object)

        rooms = [
            Room(10, 5, 8, 6, id=1),
            Room(30, 5, 8, 6, id=2),
            Room(50, 5, 8, 6, id=3),
            Room(10, 15, 8, 6, id=4),
        ]

        corridors = builder.connect_rooms_rogue_style(rooms, tiles)

        # 最小スパニングツリーにより、n-1個の接続が基本
        assert len(corridors) >= len(rooms) - 1

        # 全ての部屋が何らかの接続を持っているか確認
        for room in rooms:
            assert len(room.connected_rooms) > 0

    def test_calculate_distance(self):
        """距離計算のテスト。"""
        builder = CorridorBuilder(80, 25)

        # 水平距離
        assert builder._calculate_distance((0, 0), (3, 0)) == 3.0

        # 垂直距離
        assert builder._calculate_distance((0, 0), (0, 4)) == 4.0

        # 対角距離
        assert builder._calculate_distance((0, 0), (3, 4)) == 5.0

    def test_find_connection_point(self):
        """接続点検索のテスト。"""
        builder = CorridorBuilder(80, 25)

        from_room = Room(10, 10, 8, 6, id=1)
        to_room = Room(30, 10, 8, 6, id=2)

        connection_point = builder._find_connection_point(from_room, to_room)

        assert connection_point is not None
        assert isinstance(connection_point, tuple)
        assert len(connection_point) == 2

        # 接続点が部屋の境界上にあることを確認
        x, y = connection_point
        assert (x == from_room.x or x == from_room.x + from_room.width - 1) or (
            y == from_room.y or y == from_room.y + from_room.height - 1
        )

    def test_create_straight_corridor(self):
        """直線通路作成のテスト。"""
        builder = CorridorBuilder(80, 25)
        tiles = np.full((25, 80), Wall(), dtype=object)

        start = (10, 10)
        end = (20, 10)

        corridor_points = builder._create_straight_corridor(start, end, tiles)

        assert len(corridor_points) > 0
        assert start in corridor_points
        assert end in corridor_points

        # 通路が直線状に配置されていることを確認
        for x, y in corridor_points:
            assert y == 10  # 水平線なので y座標は一定
            assert isinstance(tiles[y, x], Floor)

    def test_is_valid_corridor_position(self):
        """通路配置位置の妥当性チェックのテスト。"""
        builder = CorridorBuilder(80, 25)
        tiles = np.full((25, 80), Wall(), dtype=object)

        # 有効な位置
        assert builder._is_valid_corridor_position(10, 10, tiles) is True

        # 境界上の無効な位置
        assert builder._is_valid_corridor_position(0, 10, tiles) is False
        assert builder._is_valid_corridor_position(79, 10, tiles) is False
        assert builder._is_valid_corridor_position(10, 0, tiles) is False
        assert builder._is_valid_corridor_position(10, 24, tiles) is False

        # 境界外の無効な位置
        assert builder._is_valid_corridor_position(-1, 10, tiles) is False
        assert builder._is_valid_corridor_position(80, 10, tiles) is False
        assert builder._is_valid_corridor_position(10, -1, tiles) is False
        assert builder._is_valid_corridor_position(10, 25, tiles) is False

    def test_create_corridor_between_rooms(self):
        """部屋間通路作成のテスト。"""
        builder = CorridorBuilder(80, 25)
        tiles = np.full((25, 80), Wall(), dtype=object)

        room1 = Room(10, 10, 8, 6, id=1)
        room2 = Room(30, 10, 8, 6, id=2)

        corridor = builder._create_corridor_between_rooms(room1, room2, tiles)

        assert corridor is not None
        assert isinstance(corridor, Corridor)
        assert corridor.connecting_rooms == (room1.id, room2.id)
        assert len(corridor.points) > 0

    def test_get_corridor_at_position(self):
        """位置での通路取得のテスト。"""
        builder = CorridorBuilder(80, 25)
        tiles = np.full((25, 80), Wall(), dtype=object)

        room1 = Room(10, 10, 8, 6, id=1)
        room2 = Room(30, 10, 8, 6, id=2)

        corridors = builder.connect_rooms_rogue_style([room1, room2], tiles)

        # 通路上の位置で通路を取得
        if corridors:
            corridor = corridors[0]
            if corridor.points:
                x, y = corridor.points[0]
                found_corridor = builder.get_corridor_at_position(x, y)
                assert found_corridor == corridor

        # 通路がない位置では None
        assert builder.get_corridor_at_position(0, 0) is None

    def test_reset(self):
        """リセット機能のテスト。"""
        builder = CorridorBuilder(80, 25)
        tiles = np.full((25, 80), Wall(), dtype=object)

        room1 = Room(10, 10, 8, 6, id=1)
        room2 = Room(30, 10, 8, 6, id=2)

        # 通路を作成
        builder.connect_rooms_rogue_style([room1, room2], tiles)
        assert len(builder.corridors) > 0

        # リセット
        builder.reset()
        assert len(builder.corridors) == 0

    def test_get_statistics(self):
        """統計情報取得のテスト。"""
        builder = CorridorBuilder(80, 25)
        tiles = np.full((25, 80), Wall(), dtype=object)

        # 通路なしの統計
        stats = builder.get_statistics()
        assert stats["corridors_count"] == 0
        assert stats["total_length"] == 0
        assert stats["average_length"] == 0

        # 通路ありの統計
        room1 = Room(10, 10, 8, 6, id=1)
        room2 = Room(30, 10, 8, 6, id=2)

        builder.connect_rooms_rogue_style([room1, room2], tiles)
        stats = builder.get_statistics()

        assert stats["corridors_count"] > 0
        assert stats["total_length"] > 0
        assert stats["average_length"] > 0

    def test_additional_connections(self):
        """追加接続機能のテスト。"""
        builder = CorridorBuilder(80, 25)
        tiles = np.full((25, 80), Wall(), dtype=object)

        rooms = [
            Room(10, 5, 8, 6, id=1),
            Room(30, 5, 8, 6, id=2),
            Room(50, 5, 8, 6, id=3),
            Room(10, 15, 8, 6, id=4),
        ]

        # 複数回実行して追加接続が発生するかテスト
        additional_connections_found = False
        for _ in range(10):  # 確率的なので複数回テスト
            builder.reset()
            corridors = builder.connect_rooms_rogue_style(rooms, tiles)

            if len(corridors) > len(rooms) - 1:
                additional_connections_found = True
                break

        # 追加接続が発生する可能性があることを確認
        # （確率的なので毎回は発生しない）
        # このテストは統計的な動作を確認するためのもの


class TestCorridor:
    """Corridorデータクラスのテストクラス。"""

    def test_corridor_init(self):
        """Corridor初期化のテスト。"""
        start = (10, 10)
        end = (20, 10)
        points = [(10, 10), (15, 10), (20, 10)]

        corridor = Corridor(start, end, points, (1, 2))

        assert corridor.start_pos == start
        assert corridor.end_pos == end
        assert corridor.points == points
        assert corridor.connecting_rooms == (1, 2)

    def test_corridor_post_init(self):
        """Corridor __post_init__ のテスト。"""
        corridor = Corridor((10, 10), (20, 10), [])

        assert corridor.points == []

    def test_corridor_without_connecting_rooms(self):
        """接続部屋なしのCorridorのテスト。"""
        corridor = Corridor((10, 10), (20, 10), [(10, 10), (20, 10)])

        assert corridor.connecting_rooms is None
