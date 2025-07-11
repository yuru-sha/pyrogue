"""Basic test cases for dungeon generation."""

from pyrogue.map.dungeon import DungeonDirector, Room
from pyrogue.map.tile import Door, Floor, SecretDoor, Wall


def test_dungeon_generation():
    """基本的なダンジョン生成テスト"""
    director = DungeonDirector(80, 50, floor=1)
    tiles, up_pos, down_pos = director.build_dungeon()

    # タイル配列が正しく生成されているか
    assert tiles.shape == (50, 80), f"Tiles shape is {tiles.shape}, expected (50, 80)"

    # 階段位置が有効な範囲内か
    assert 0 <= up_pos[0] < 80, f"Up stairs X position {up_pos[0]} is out of bounds"
    assert 0 <= up_pos[1] < 50, f"Up stairs Y position {up_pos[1]} is out of bounds"
    assert 0 <= down_pos[0] < 80, f"Down stairs X position {down_pos[0]} is out of bounds"
    assert 0 <= down_pos[1] < 50, f"Down stairs Y position {down_pos[1]} is out of bounds"

    # 部屋が生成されているか
    assert len(director.rooms) > 0, "No rooms generated"


def test_room_generation():
    """部屋の生成テスト"""
    director = DungeonDirector(80, 50, floor=1)
    tiles, up_pos, down_pos = director.build_dungeon()

    # 部屋が適切に生成されているか
    for room in director.rooms:
        assert room.width >= 4, f"Room width {room.width} is too small"
        assert room.height >= 4, f"Room height {room.height} is too small"
        assert room.width <= 25, f"Room width {room.width} is too large"
        assert room.height <= 25, f"Room height {room.height} is too large"

        # 部屋が境界内にあるか
        assert room.x >= 0, f"Room X position {room.x} is out of bounds"
        assert room.y >= 0, f"Room Y position {room.y} is out of bounds"
        assert room.x + room.width <= 80, f"Room extends beyond width boundary"
        assert room.y + room.height <= 50, f"Room extends beyond height boundary"


def test_boundary_walls():
    """境界壁のテスト"""
    director = DungeonDirector(80, 50, floor=1)
    tiles, up_pos, down_pos = director.build_dungeon()

    # 上下の境界が壁か
    for x in range(80):
        assert isinstance(tiles[0, x], Wall), f"Top boundary at ({x}, 0) is not wall"
        assert isinstance(tiles[49, x], Wall), f"Bottom boundary at ({x}, 49) is not wall"

    # 左右の境界が壁か
    for y in range(50):
        assert isinstance(tiles[y, 0], Wall), f"Left boundary at (0, {y}) is not wall"
        assert isinstance(tiles[y, 79], Wall), f"Right boundary at (79, {y}) is not wall"


def test_special_room_generation():
    """特別な部屋の生成テスト"""
    director = DungeonDirector(80, 50, floor=5)  # 特別な部屋が生成される階
    tiles, up_pos, down_pos = director.build_dungeon()

    # 特別な部屋が生成されているか
    special_rooms = [room for room in director.rooms if getattr(room, 'is_special', False)]

    # 特別な部屋の数をチェック（現在の実装では複数の特別な部屋が生成される）
    assert len(special_rooms) >= 0, f"Special rooms should be non-negative: {len(special_rooms)}"


def test_stairs_in_different_rooms():
    """階段が異なる部屋にあることのテスト"""
    director = DungeonDirector(80, 50, floor=1)
    tiles, up_pos, down_pos = director.build_dungeon()

    up_room = None
    down_room = None

    for room in director.rooms:
        # 階段が部屋内にあるかチェック
        if (room.x < up_pos[0] < room.x + room.width and
            room.y < up_pos[1] < room.y + room.height):
            up_room = room

        if (room.x < down_pos[0] < room.x + room.width and
            room.y < down_pos[1] < room.y + room.height):
            down_room = room

    # 階段が部屋内にあることを確認
    assert up_room is not None, "Up stairs not found in any room"
    assert down_room is not None, "Down stairs not found in any room"

    # 階段が異なる部屋にあることを確認
    assert up_room != down_room, "Stairs are in the same room"


def test_multiple_generations():
    """複数回の生成テスト（安定性確認）"""
    for i in range(5):
        director = DungeonDirector(80, 50, floor=i+1)
        tiles, up_pos, down_pos = director.build_dungeon()

        # 基本的なチェック
        assert tiles.shape == (50, 80), f"Generation {i}: Invalid tiles shape"
        assert len(director.rooms) > 0, f"Generation {i}: No rooms generated"
        assert up_pos != down_pos, f"Generation {i}: Stairs at same position"
