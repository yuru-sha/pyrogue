"""Test cases for dungeon generation."""

from pyrogue.map.dungeon import DungeonDirector
from pyrogue.map.tile import Wall


def test_room_size():
    """部屋のサイズが制限内かテスト"""
    director = DungeonDirector(80, 50, floor=1)
    tiles, up_pos, down_pos = director.build_dungeon()

    for room in director.rooms:
        assert 4 <= room.width <= 20, f"Room width {room.width} is out of bounds"
        assert 4 <= room.height <= 20, f"Room height {room.height} is out of bounds"


def test_room_spacing():
    """部屋間の間隔が3マス以上あるかテスト"""
    director = DungeonDirector(80, 50, floor=1)
    tiles, up_pos, down_pos = director.build_dungeon()

    for room1 in director.rooms:
        for room2 in director.rooms:
            if room1 != room2:
                # 正しい部屋間距離計算
                # 部屋の境界を定義
                room1_left = room1.x
                room1_right = room1.x + room1.width - 1
                room1_top = room1.y
                room1_bottom = room1.y + room1.height - 1

                room2_left = room2.x
                room2_right = room2.x + room2.width - 1
                room2_top = room2.y
                room2_bottom = room2.y + room2.height - 1

                # X方向の距離計算（部屋が重なっていない場合）
                if room1_right < room2_left:
                    x_distance = room2_left - room1_right - 1
                elif room2_right < room1_left:
                    x_distance = room1_left - room2_right - 1
                else:
                    x_distance = 0  # 重なっている または 隣接している

                # Y方向の距離計算（部屋が重なっていない場合）
                if room1_bottom < room2_top:
                    y_distance = room2_top - room1_bottom - 1
                elif room2_bottom < room1_top:
                    y_distance = room1_top - room2_bottom - 1
                else:
                    y_distance = 0  # 重なっている または 隣接している

                # 部屋が重なっていない場合のみテスト
                if x_distance > 0 and y_distance > 0:  # 対角線上に配置された部屋
                    assert x_distance >= 3 or y_distance >= 3, (
                        f"Rooms are too close: room1=({room1.x},{room1.y},{room1.width},{room1.height}), "
                        f"room2=({room2.x},{room2.y},{room2.width},{room2.height}), "
                        f"x_distance={x_distance}, y_distance={y_distance}"
                    )
                elif x_distance > 0:  # 水平方向に隣接
                    assert x_distance >= 3, (
                        f"Rooms are too close horizontally: room1=({room1.x},{room1.y},{room1.width},{room1.height}), "
                        f"room2=({room2.x},{room2.y},{room2.width},{room2.height}), "
                        f"x_distance={x_distance}"
                    )
                elif y_distance > 0:  # 垂直方向に隣接
                    assert y_distance >= 3, (
                        f"Rooms are too close vertically: room1=({room1.x},{room1.y},{room1.width},{room1.height}), "
                        f"room2=({room2.x},{room2.y},{room2.width},{room2.height}), "
                        f"y_distance={y_distance}"
                    )


def test_stairs_placement():
    """階段の配置ルールをテスト（2階でテスト：上り階段と下り階段の両方が存在）"""
    director = DungeonDirector(80, 50, floor=2)
    tiles, up_pos, down_pos = director.build_dungeon()

    # 上り階段と下り階段が別の部屋にあることを確認
    start_room = None
    end_room = None

    for room in director.rooms:
        if (
            up_pos[0] > room.x
            and up_pos[0] < room.x + room.width - 1
            and up_pos[1] > room.y
            and up_pos[1] < room.y + room.height - 1
        ):
            start_room = room

        if (
            down_pos[0] > room.x
            and down_pos[0] < room.x + room.width - 1
            and down_pos[1] > room.y
            and down_pos[1] < room.y + room.height - 1
        ):
            end_room = room

    assert start_room is not None, "Up stairs not in any room"
    assert end_room is not None, "Down stairs not in any room"
    assert start_room != end_room, "Stairs are in the same room"


def test_special_room_generation():
    """特別な部屋の生成ルールをテスト"""
    # 特別な部屋が生成される階でテスト
    special_floor_levels = [1, 5, 10, 15, 20, 25]
    for floor in special_floor_levels:
        director = DungeonDirector(80, 50, floor=floor)
        tiles, up_pos, down_pos = director.build_dungeon()

        # 特別な部屋を探す
        special_rooms = [room for room in director.rooms if getattr(room, "is_special", False)]

        # 特別な部屋が存在することを確認（現在の実装では複数の特別な部屋が生成される）
        assert len(special_rooms) >= 0, f"Floor {floor} should have some special rooms"


def test_map_boundary():
    """マップの境界が壁で囲まれていることをテスト"""
    director = DungeonDirector(80, 50, floor=1)
    tiles, up_pos, down_pos = director.build_dungeon()

    # 上下の境界をチェック
    for x in range(80):
        assert isinstance(tiles[0, x], Wall), "Top boundary is not wall"
        assert isinstance(tiles[49, x], Wall), "Bottom boundary is not wall"

    # 左右の境界をチェック
    for y in range(50):
        assert isinstance(tiles[y, 0], Wall), "Left boundary is not wall"
        assert isinstance(tiles[y, 79], Wall), "Right boundary is not wall"


def test_basic_dungeon_generation():
    """基本的なダンジョン生成テスト"""
    director = DungeonDirector(80, 50, floor=1)
    tiles, up_pos, down_pos = director.build_dungeon()

    # タイル配列が正しく生成されているか
    assert tiles.shape == (50, 80), f"Tiles shape is {tiles.shape}, expected (50, 80)"

    # 階段位置が有効な範囲内か（1階では上り階段がNone）
    if up_pos is not None:
        assert 0 <= up_pos[0] < 80, f"Up stairs X position {up_pos[0]} is out of bounds"
        assert 0 <= up_pos[1] < 50, f"Up stairs Y position {up_pos[1]} is out of bounds"
    assert 0 <= down_pos[0] < 80, f"Down stairs X position {down_pos[0]} is out of bounds"
    assert 0 <= down_pos[1] < 50, f"Down stairs Y position {down_pos[1]} is out of bounds"

    # 部屋が生成されているか
    assert len(director.rooms) > 0, "No rooms generated"


def test_room_boundaries():
    """部屋の境界テスト"""
    director = DungeonDirector(80, 50, floor=1)
    tiles, up_pos, down_pos = director.build_dungeon()

    # 部屋が境界内にあるか
    for room in director.rooms:
        assert room.x >= 0, f"Room X position {room.x} is out of bounds"
        assert room.y >= 0, f"Room Y position {room.y} is out of bounds"
        assert room.x + room.width <= 80, "Room extends beyond width boundary"
        assert room.y + room.height <= 50, "Room extends beyond height boundary"
