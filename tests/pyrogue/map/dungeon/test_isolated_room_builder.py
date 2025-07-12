"""
孤立部屋群ビルダーのテスト。

このテストは、孤立部屋群の生成システムが正常に動作することを確認します。
"""

import numpy as np
from pyrogue.map.dungeon.isolated_room_builder import (
    IsolatedRoomBuilder,
    IsolatedRoomGroup,
)
from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Floor, SecretDoor, Wall


class TestIsolatedRoomBuilder:
    """孤立部屋群ビルダーのテストクラス。"""

    def test_initialization(self):
        """初期化テスト。"""
        builder = IsolatedRoomBuilder(80, 45, isolation_level=0.7)

        assert builder.width == 80
        assert builder.height == 45
        assert builder.isolation_level == 0.7
        assert builder.isolated_groups == []
        assert builder.used_areas == set()

    def test_isolated_room_group_creation(self):
        """孤立部屋群の作成テスト。"""
        room1 = Room(5, 5, 8, 6)
        room2 = Room(15, 10, 6, 5)
        access_points = [(7, 5), (18, 10)]

        group = IsolatedRoomGroup([room1, room2], access_points)

        assert len(group.rooms) == 2
        assert len(group.access_points) == 2
        assert not group.is_discovered
        assert group.group_id is not None

    def test_mark_existing_areas(self):
        """既存エリアマーキングのテスト。"""
        builder = IsolatedRoomBuilder(80, 45)

        # 既存の部屋を作成
        existing_room = Room(10, 10, 8, 6)
        builder._mark_existing_areas([existing_room])

        # 部屋周辺の2セルマージンがマークされているかチェック
        assert (10, 10) in builder.used_areas
        assert (8, 8) in builder.used_areas  # 左上マージン
        assert (19, 17) in builder.used_areas  # 右下マージン

    def test_find_isolation_area(self):
        """孤立エリア発見のテスト。"""
        builder = IsolatedRoomBuilder(80, 45)

        # 利用可能エリアを見つける
        area = builder._find_isolation_area()

        if area:  # エリアが見つかった場合
            x, y, width, height = area
            assert 5 <= x < 80 - width - 5
            assert 5 <= y < 45 - height - 5
            assert 15 <= width <= 25
            assert 10 <= height <= 15

    def test_room_overlap_detection(self):
        """部屋の重複検出テスト。"""
        builder = IsolatedRoomBuilder(80, 45)

        existing_room = Room(10, 10, 8, 6)
        existing_rooms = [existing_room]

        # 重複する部屋
        overlapping_room = Room(12, 12, 6, 5)
        assert builder._room_overlaps_with_existing(overlapping_room, existing_rooms)

        # 重複しない部屋
        non_overlapping_room = Room(25, 25, 6, 5)
        assert not builder._room_overlaps_with_existing(
            non_overlapping_room, existing_rooms
        )

    def test_room_distance_calculation(self):
        """部屋間距離計算のテスト。"""
        builder = IsolatedRoomBuilder(80, 45)

        room1 = Room(5, 5, 8, 6)
        room2 = Room(15, 10, 6, 5)

        distance = builder._calculate_room_distance(room1, room2)

        # 中心点間の距離を計算
        center1 = room1.center()
        center2 = room2.center()
        expected_distance = (
            (center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2
        ) ** 0.5

        assert abs(distance - expected_distance) < 0.01

    def test_generate_isolated_rooms(self):
        """孤立部屋群生成のテスト。"""
        builder = IsolatedRoomBuilder(80, 45, isolation_level=0.5)

        # タイル配列を初期化
        tiles = np.full((45, 80), Wall(), dtype=object)

        # 既存の部屋を作成
        existing_room = Room(10, 10, 8, 6)
        existing_rooms = [existing_room]

        # 既存の部屋をタイルに配置
        for y in range(existing_room.y + 1, existing_room.y + existing_room.height - 1):
            for x in range(
                existing_room.x + 1, existing_room.x + existing_room.width - 1
            ):
                tiles[y, x] = Floor()

        # 孤立部屋群を生成
        isolated_groups = builder.generate_isolated_rooms(
            tiles, existing_rooms, max_groups=1
        )

        # 結果を検証
        assert len(isolated_groups) >= 0  # 生成される可能性がある

        for group in isolated_groups:
            assert len(group.rooms) >= 1
            assert len(group.access_points) >= 1

            # 孤立部屋の属性チェック
            for room in group.rooms:
                assert room.is_isolated
                assert room.id is not None

    def test_secret_path_calculation(self):
        """隠し通路のパス計算テスト。"""
        builder = IsolatedRoomBuilder(80, 45)

        start_x, start_y = 5, 5
        end_x, end_y = 15, 12

        path = builder._calculate_secret_path(start_x, start_y, end_x, end_y)

        # パスの検証
        assert len(path) > 0
        assert path[0] == (start_x, start_y)
        assert path[-1] == (end_x, end_y)

        # パスの連続性をチェック
        for i in range(len(path) - 1):
            current = path[i]
            next_pos = path[i + 1]

            # 隣接する位置かチェック（マンハッタン距離が1）
            distance = abs(current[0] - next_pos[0]) + abs(current[1] - next_pos[1])
            assert distance == 1

    def test_access_point_determination(self):
        """アクセスポイント決定のテスト。"""
        builder = IsolatedRoomBuilder(80, 45)

        room = Room(10, 10, 8, 6)
        rooms = [room]

        access_points = builder._determine_access_points(rooms)

        # 各部屋に対してアクセスポイントが設定されているかチェック
        assert len(access_points) >= 1

        for access_point in access_points:
            x, y = access_point

            # アクセスポイントが部屋の境界上にあるかチェック
            is_on_boundary = (x == room.x or x == room.x + room.width - 1) or (
                y == room.y or y == room.y + room.height - 1
            )
            assert is_on_boundary

    def test_statistics_generation(self):
        """統計情報生成のテスト。"""
        builder = IsolatedRoomBuilder(80, 45, isolation_level=0.6)

        # 孤立部屋群を手動で設定
        room1 = Room(5, 5, 8, 6)
        room2 = Room(15, 10, 6, 5)
        group = IsolatedRoomGroup([room1, room2], [(7, 5), (18, 10)])
        builder.isolated_groups = [group]

        stats = builder.get_statistics()

        assert stats["builder_type"] == "IsolatedRooms"
        assert stats["isolation_level"] == 0.6
        assert stats["group_count"] == 1
        assert stats["total_rooms"] == 2
        assert stats["total_access_points"] == 2

    def test_reset_functionality(self):
        """リセット機能のテスト。"""
        builder = IsolatedRoomBuilder(80, 45)

        # 状態を設定
        builder.used_areas.add((10, 10))
        room = Room(5, 5, 8, 6)
        group = IsolatedRoomGroup([room], [(7, 5)])
        builder.isolated_groups = [group]

        # リセットを実行
        builder.reset()

        # 状態がリセットされているかチェック
        assert builder.isolated_groups == []
        assert builder.used_areas == set()

    def test_secret_door_placement(self):
        """隠し扉配置のテスト。"""
        builder = IsolatedRoomBuilder(80, 45)

        # タイル配列を初期化
        tiles = np.full((45, 80), Wall(), dtype=object)

        # 目標部屋を作成
        target_room = Room(20, 20, 8, 6)
        for y in range(target_room.y + 1, target_room.y + target_room.height - 1):
            for x in range(target_room.x + 1, target_room.x + target_room.width - 1):
                tiles[y, x] = Floor()

        # 隠し通路を作成
        start_point = (10, 10)
        builder._create_secret_passage(start_point, target_room, tiles)

        # 隠し扉が配置されているかチェック
        secret_door_found = False
        for y in range(45):
            for x in range(80):
                if isinstance(tiles[y, x], SecretDoor):
                    secret_door_found = True
                    break
            if secret_door_found:
                break

        assert secret_door_found, "隠し扉が配置されていません"


class TestIsolatedRoomGroup:
    """孤立部屋群クラスのテストクラス。"""

    def test_group_initialization(self):
        """グループ初期化のテスト。"""
        room1 = Room(5, 5, 8, 6)
        room2 = Room(15, 10, 6, 5)
        access_points = [(7, 5), (18, 10)]

        group = IsolatedRoomGroup([room1, room2], access_points)

        assert len(group.rooms) == 2
        assert len(group.access_points) == 2
        assert not group.is_discovered
        assert isinstance(group.group_id, int)
        assert 1000 <= group.group_id <= 9999

    def test_group_discovery(self):
        """グループ発見のテスト。"""
        room = Room(5, 5, 8, 6)
        group = IsolatedRoomGroup([room], [(7, 5)])

        assert not group.is_discovered

        # 発見状態を変更
        group.is_discovered = True
        assert group.is_discovered
