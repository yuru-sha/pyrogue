"""
ダンジョン生成定数のテストモジュール。

このモジュールは、ダンジョン生成関連の定数クラスの
値が適切に定義されていることを検証します。
"""

import pytest

from pyrogue.map.dungeon.constants import (
    BSPConstants,
    DoorConstants,
    CorridorConstants,
    MazeConstants,
    RoomConstants,
    StairsConstants,
    ValidationConstants,
)


class TestBSPConstants:
    """BSP定数のテストクラス。"""

    def test_bsp_constants_exist(self):
        """BSP定数が存在することを確認。"""
        assert hasattr(BSPConstants, 'DEPTH')
        assert hasattr(BSPConstants, 'MIN_SIZE')
        assert hasattr(BSPConstants, 'FULL_ROOMS')
        assert hasattr(BSPConstants, 'MIN_ROOM_SIZE')
        assert hasattr(BSPConstants, 'MAX_ROOM_SIZE_RATIO')

    def test_bsp_constants_values(self):
        """BSP定数の値が妥当であることを確認。"""
        assert BSPConstants.DEPTH == 10
        assert BSPConstants.MIN_SIZE == 8
        assert BSPConstants.FULL_ROOMS is False
        assert BSPConstants.MIN_ROOM_SIZE == 4
        assert BSPConstants.MAX_ROOM_SIZE_RATIO == 0.8

    def test_bsp_constants_types(self):
        """BSP定数の型が正しいことを確認。"""
        assert isinstance(BSPConstants.DEPTH, int)
        assert isinstance(BSPConstants.MIN_SIZE, int)
        assert isinstance(BSPConstants.FULL_ROOMS, bool)
        assert isinstance(BSPConstants.MIN_ROOM_SIZE, int)
        assert isinstance(BSPConstants.MAX_ROOM_SIZE_RATIO, float)


class TestDoorConstants:
    """ドア定数のテストクラス。"""

    def test_door_constants_exist(self):
        """ドア定数が存在することを確認。"""
        assert hasattr(DoorConstants, 'SECRET_DOOR_CHANCE')
        assert hasattr(DoorConstants, 'OPEN_DOOR_CHANCE')
        assert hasattr(DoorConstants, 'CLOSED_DOOR_CHANCE')
        assert hasattr(DoorConstants, 'MIN_DOOR_DISTANCE')
        assert hasattr(DoorConstants, 'MAX_DOORS_PER_ROOM')
        assert hasattr(DoorConstants, 'HIDDEN_DOOR_SEARCH_RANGE')

    def test_door_constants_values(self):
        """ドア定数の値が妥当であることを確認。"""
        assert DoorConstants.SECRET_DOOR_CHANCE == 0.10
        assert DoorConstants.OPEN_DOOR_CHANCE == 0.30
        assert DoorConstants.CLOSED_DOOR_CHANCE == 0.60
        assert DoorConstants.MIN_DOOR_DISTANCE == 2
        assert DoorConstants.MAX_DOORS_PER_ROOM == 4
        assert DoorConstants.HIDDEN_DOOR_SEARCH_RANGE == 2

    def test_door_probabilities_sum_to_one(self):
        """ドア確率の合計が1.0になることを確認。"""
        total = (
            DoorConstants.SECRET_DOOR_CHANCE +
            DoorConstants.OPEN_DOOR_CHANCE +
            DoorConstants.CLOSED_DOOR_CHANCE
        )
        assert abs(total - 1.0) < 0.001  # 浮動小数点の誤差を考慮

    def test_door_constants_types(self):
        """ドア定数の型が正しいことを確認。"""
        assert isinstance(DoorConstants.SECRET_DOOR_CHANCE, float)
        assert isinstance(DoorConstants.OPEN_DOOR_CHANCE, float)
        assert isinstance(DoorConstants.CLOSED_DOOR_CHANCE, float)
        assert isinstance(DoorConstants.MIN_DOOR_DISTANCE, int)
        assert isinstance(DoorConstants.MAX_DOORS_PER_ROOM, int)
        assert isinstance(DoorConstants.HIDDEN_DOOR_SEARCH_RANGE, int)


class TestCorridorConstants:
    """通路定数のテストクラス。"""

    def test_corridor_constants_exist(self):
        """通路定数が存在することを確認。"""
        assert hasattr(CorridorConstants, 'ADDITIONAL_CONNECTION_CHANCE')
        assert hasattr(CorridorConstants, 'MIN_ROOMS_FOR_ADDITIONAL')
        assert hasattr(CorridorConstants, 'CORRIDOR_WIDTH')
        assert hasattr(CorridorConstants, 'MIN_CORRIDOR_LENGTH')
        assert hasattr(CorridorConstants, 'CONNECTION_POINT_OFFSET')

    def test_corridor_constants_values(self):
        """通路定数の値が妥当であることを確認。"""
        assert CorridorConstants.ADDITIONAL_CONNECTION_CHANCE == 0.20
        assert CorridorConstants.MIN_ROOMS_FOR_ADDITIONAL == 3
        assert CorridorConstants.CORRIDOR_WIDTH == 1
        assert CorridorConstants.MIN_CORRIDOR_LENGTH == 2
        assert CorridorConstants.CONNECTION_POINT_OFFSET == 2

    def test_corridor_constants_types(self):
        """通路定数の型が正しいことを確認。"""
        assert isinstance(CorridorConstants.ADDITIONAL_CONNECTION_CHANCE, float)
        assert isinstance(CorridorConstants.MIN_ROOMS_FOR_ADDITIONAL, int)
        assert isinstance(CorridorConstants.CORRIDOR_WIDTH, int)
        assert isinstance(CorridorConstants.MIN_CORRIDOR_LENGTH, int)
        assert isinstance(CorridorConstants.CONNECTION_POINT_OFFSET, int)


class TestMazeConstants:
    """迷路定数のテストクラス。"""

    def test_maze_constants_exist(self):
        """迷路定数が存在することを確認。"""
        assert hasattr(MazeConstants, 'MIN_FLOOR_DENSITY')
        assert hasattr(MazeConstants, 'MAX_FLOOR_DENSITY')
        assert hasattr(MazeConstants, 'TARGET_FLOOR_DENSITY')
        assert hasattr(MazeConstants, 'CELLULAR_AUTOMATA_ITERATIONS')
        assert hasattr(MazeConstants, 'BIRTH_LIMIT')
        assert hasattr(MazeConstants, 'DEATH_LIMIT')
        assert hasattr(MazeConstants, 'MAZE_FLOORS')

    def test_maze_constants_values(self):
        """迷路定数の値が妥当であることを確認。"""
        assert MazeConstants.MIN_FLOOR_DENSITY == 0.10
        assert MazeConstants.MAX_FLOOR_DENSITY == 0.40
        assert MazeConstants.TARGET_FLOOR_DENSITY == 0.25
        assert MazeConstants.CELLULAR_AUTOMATA_ITERATIONS == 5
        assert MazeConstants.BIRTH_LIMIT == 4
        assert MazeConstants.DEATH_LIMIT == 3
        assert MazeConstants.MAZE_FLOORS == [7, 13, 19]

    def test_maze_density_relationships(self):
        """迷路密度の関係が妥当であることを確認。"""
        assert MazeConstants.MIN_FLOOR_DENSITY < MazeConstants.MAX_FLOOR_DENSITY
        assert MazeConstants.MIN_FLOOR_DENSITY <= MazeConstants.TARGET_FLOOR_DENSITY <= MazeConstants.MAX_FLOOR_DENSITY

    def test_maze_constants_types(self):
        """迷路定数の型が正しいことを確認。"""
        assert isinstance(MazeConstants.MIN_FLOOR_DENSITY, float)
        assert isinstance(MazeConstants.MAX_FLOOR_DENSITY, float)
        assert isinstance(MazeConstants.TARGET_FLOOR_DENSITY, float)
        assert isinstance(MazeConstants.CELLULAR_AUTOMATA_ITERATIONS, int)
        assert isinstance(MazeConstants.BIRTH_LIMIT, int)
        assert isinstance(MazeConstants.DEATH_LIMIT, int)
        assert isinstance(MazeConstants.MAZE_FLOORS, list)


class TestRoomConstants:
    """部屋定数のテストクラス。"""

    def test_room_constants_exist(self):
        """部屋定数が存在することを確認。"""
        assert hasattr(RoomConstants, 'MIN_ROOM_WIDTH')
        assert hasattr(RoomConstants, 'MIN_ROOM_HEIGHT')
        assert hasattr(RoomConstants, 'MAX_ROOM_WIDTH')
        assert hasattr(RoomConstants, 'MAX_ROOM_HEIGHT')
        assert hasattr(RoomConstants, 'MIN_ROOM_DISTANCE')
        assert hasattr(RoomConstants, 'ROOM_PADDING')
        assert hasattr(RoomConstants, 'SPECIAL_ROOM_CHANCE')

    def test_room_constants_values(self):
        """部屋定数の値が妥当であることを確認。"""
        assert RoomConstants.MIN_ROOM_WIDTH == 4
        assert RoomConstants.MIN_ROOM_HEIGHT == 4
        assert RoomConstants.MAX_ROOM_WIDTH == 20
        assert RoomConstants.MAX_ROOM_HEIGHT == 15
        assert RoomConstants.MIN_ROOM_DISTANCE == 3
        assert RoomConstants.ROOM_PADDING == 1
        assert RoomConstants.SPECIAL_ROOM_CHANCE == 0.15

    def test_room_size_relationships(self):
        """部屋サイズの関係が妥当であることを確認。"""
        assert RoomConstants.MIN_ROOM_WIDTH < RoomConstants.MAX_ROOM_WIDTH
        assert RoomConstants.MIN_ROOM_HEIGHT < RoomConstants.MAX_ROOM_HEIGHT

    def test_room_constants_types(self):
        """部屋定数の型が正しいことを確認。"""
        assert isinstance(RoomConstants.MIN_ROOM_WIDTH, int)
        assert isinstance(RoomConstants.MIN_ROOM_HEIGHT, int)
        assert isinstance(RoomConstants.MAX_ROOM_WIDTH, int)
        assert isinstance(RoomConstants.MAX_ROOM_HEIGHT, int)
        assert isinstance(RoomConstants.MIN_ROOM_DISTANCE, int)
        assert isinstance(RoomConstants.ROOM_PADDING, int)
        assert isinstance(RoomConstants.SPECIAL_ROOM_CHANCE, float)


class TestStairsConstants:
    """階段定数のテストクラス。"""

    def test_stairs_constants_exist(self):
        """階段定数が存在することを確認。"""
        assert hasattr(StairsConstants, 'MIN_STAIRS_DISTANCE')
        assert hasattr(StairsConstants, 'STAIRS_ROOM_PREFERENCE')
        assert hasattr(StairsConstants, 'STAIRS_SAFE_RADIUS')

    def test_stairs_constants_values(self):
        """階段定数の値が妥当であることを確認。"""
        assert StairsConstants.MIN_STAIRS_DISTANCE == 10
        assert StairsConstants.STAIRS_ROOM_PREFERENCE == 0.8
        assert StairsConstants.STAIRS_SAFE_RADIUS == 2

    def test_stairs_constants_types(self):
        """階段定数の型が正しいことを確認。"""
        assert isinstance(StairsConstants.MIN_STAIRS_DISTANCE, int)
        assert isinstance(StairsConstants.STAIRS_ROOM_PREFERENCE, float)
        assert isinstance(StairsConstants.STAIRS_SAFE_RADIUS, int)


class TestValidationConstants:
    """検証定数のテストクラス。"""

    def test_validation_constants_exist(self):
        """検証定数が存在することを確認。"""
        assert hasattr(ValidationConstants, 'MIN_REACHABLE_TILES')
        assert hasattr(ValidationConstants, 'MAX_ISOLATED_AREAS')
        assert hasattr(ValidationConstants, 'MIN_ROOMS_PER_FLOOR')
        assert hasattr(ValidationConstants, 'MAX_ROOMS_PER_FLOOR')
        assert hasattr(ValidationConstants, 'MIN_CORRIDOR_COUNT')
        assert hasattr(ValidationConstants, 'MAX_CORRIDOR_COMPLEXITY')

    def test_validation_constants_values(self):
        """検証定数の値が妥当であることを確認。"""
        assert ValidationConstants.MIN_REACHABLE_TILES == 0.30
        assert ValidationConstants.MAX_ISOLATED_AREAS == 3
        assert ValidationConstants.MIN_ROOMS_PER_FLOOR == 4
        assert ValidationConstants.MAX_ROOMS_PER_FLOOR == 12
        assert ValidationConstants.MIN_CORRIDOR_COUNT == 3
        assert ValidationConstants.MAX_CORRIDOR_COMPLEXITY == 0.5

    def test_validation_room_relationships(self):
        """検証部屋数の関係が妥当であることを確認。"""
        assert ValidationConstants.MIN_ROOMS_PER_FLOOR < ValidationConstants.MAX_ROOMS_PER_FLOOR

    def test_validation_constants_types(self):
        """検証定数の型が正しいことを確認。"""
        assert isinstance(ValidationConstants.MIN_REACHABLE_TILES, float)
        assert isinstance(ValidationConstants.MAX_ISOLATED_AREAS, int)
        assert isinstance(ValidationConstants.MIN_ROOMS_PER_FLOOR, int)
        assert isinstance(ValidationConstants.MAX_ROOMS_PER_FLOOR, int)
        assert isinstance(ValidationConstants.MIN_CORRIDOR_COUNT, int)
        assert isinstance(ValidationConstants.MAX_CORRIDOR_COMPLEXITY, float)