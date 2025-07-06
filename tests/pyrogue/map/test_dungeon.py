"""Test cases for dungeon generation."""

from pyrogue.map.dungeon import DungeonGenerator, Room
from pyrogue.map.tile import Door, Floor, SecretDoor, Wall


def test_room_size():
    """部屋のサイズが制限内かテスト"""
    generator = DungeonGenerator(80, 50)
    generator.generate()

    for room in generator.rooms:
        assert 6 <= room.width <= 10, f"Room width {room.width} is out of bounds"
        assert 6 <= room.height <= 10, f"Room height {room.height} is out of bounds"


def test_room_spacing():
    """部屋間の間隔が3マス以上あるかテスト"""
    generator = DungeonGenerator(80, 50)
    generator.generate()

    for room1 in generator.rooms:
        for room2 in generator.rooms:
            if room1 != room2:
                # 部屋間の距離を計算
                x_distance = min(
                    abs(room1.x + room1.width - room2.x),
                    abs(room2.x + room2.width - room1.x),
                )
                y_distance = min(
                    abs(room1.y + room1.height - room2.y),
                    abs(room2.y + room2.height - room1.y),
                )
                if x_distance > 0 and y_distance > 0:  # 部屋が重なっていない場合
                    assert x_distance >= 3 or y_distance >= 3, "Rooms are too close"


def test_door_placement():
    """扉の配置ルールをテスト"""
    generator = DungeonGenerator(80, 50)
    generator.generate()

    for room in generator.rooms:
        # 扉の数は4個以下
        assert len(room.doors) <= 4, f"Room has too many doors: {len(room.doors)}"

        # 各壁の扉の数をカウント
        wall_doors = {"north": 0, "south": 0, "east": 0, "west": 0}

        for door_x, door_y in room.doors:
            # 扉が壁の中央にあるか確認
            if door_y == room.y:  # 北壁
                assert door_x == room.x + room.width // 2, (
                    "Door not in center of north wall"
                )
                wall_doors["north"] += 1
            elif door_y == room.y + room.height - 1:  # 南壁
                assert door_x == room.x + room.width // 2, (
                    "Door not in center of south wall"
                )
                wall_doors["south"] += 1
            elif door_x == room.x:  # 西壁
                assert door_y == room.y + room.height // 2, (
                    "Door not in center of west wall"
                )
                wall_doors["west"] += 1
            elif door_x == room.x + room.width - 1:  # 東壁
                assert door_y == room.y + room.height // 2, (
                    "Door not in center of east wall"
                )
                wall_doors["east"] += 1

        # 各壁の扉は0個か1個
        for wall, count in wall_doors.items():
            assert count <= 1, f"Wall {wall} has multiple doors"


def test_corridor_rules():
    """通路の生成ルールをテスト"""
    generator = DungeonGenerator(80, 50)
    generator.generate()

    # 通路の座標をチェック
    for x, y in generator.corridors:
        # 通路が部屋と交差していないことを確認
        for room in generator.rooms:
            if (
                room.x < x < room.x + room.width - 1
                and room.y < y < room.y + room.height - 1
            ):
                assert False, "Corridor intersects with room"

        # 通路が直線またはL字型であることを確認
        # TODO: 通路の形状チェックを実装


def test_stairs_placement():
    """階段の配置ルールをテスト"""
    generator = DungeonGenerator(80, 50)
    tiles, start_pos, end_pos = generator.generate()

    # 上り階段と下り階段が別の部屋にあることを確認
    start_room = None
    end_room = None

    for room in generator.rooms:
        if (
            start_pos[0] > room.x
            and start_pos[0] < room.x + room.width - 1
            and start_pos[1] > room.y
            and start_pos[1] < room.y + room.height - 1
        ):
            start_room = room

        if (
            end_pos[0] > room.x
            and end_pos[0] < room.x + room.width - 1
            and end_pos[1] > room.y
            and end_pos[1] < room.y + room.height - 1
        ):
            end_room = room

    assert start_room is not None, "Up stairs not in any room"
    assert end_room is not None, "Down stairs not in any room"
    assert start_room != end_room, "Stairs are in the same room"


def test_special_room_doors():
    """特別な部屋の扉生成ルールをテスト"""
    generator = DungeonGenerator(80, 50, floor=5)  # 特別な部屋が生成される階
    generator.generate()

    # 特別な部屋を探す
    special_rooms = [room for room in generator.rooms if room.is_special]
    if special_rooms:
        for room in special_rooms:
            for door_x, door_y in room.doors:
                # 特別な部屋への扉は必ず通常の扉
                assert isinstance(generator.tiles[door_y, door_x], Door), (
                    "Special room door is not a normal door"
                )


def test_corridor_shape():
    """通路が直線またはL字型であることをテスト"""
    generator = DungeonGenerator(80, 50)
    generator.generate()

    # 通路の座標をグループ化（連続する通路をまとめる）
    corridor_groups = []
    current_group = set()

    for x, y in generator.corridors:
        # 現在のグループに隣接しているか確認
        is_adjacent = False
        for cx, cy in current_group:
            if abs(x - cx) + abs(y - cy) == 1:  # マンハッタン距離が1なら隣接
                is_adjacent = True
                break

        if is_adjacent:
            current_group.add((x, y))
        else:
            if current_group:
                corridor_groups.append(current_group)
            current_group = {(x, y)}

    if current_group:
        corridor_groups.append(current_group)

    # 各通路グループが直線またはL字型かチェック
    for corridor in corridor_groups:
        # 通路の端点を見つける
        x_coords = [x for x, _ in corridor]
        y_coords = [y for _, y in corridor]

        # 直線の場合：x座標またはy座標が一定
        is_straight = len(set(x_coords)) == 1 or len(set(y_coords)) == 1

        # L字型の場合：x座標とy座標がそれぞれ2つの値のみ
        is_l_shaped = len(set(x_coords)) == 2 and len(set(y_coords)) == 2

        assert is_straight or is_l_shaped, "Corridor is neither straight nor L-shaped"


def test_door_types():
    """扉の種類の生成確率をテスト"""
    # 複数回のテストで統計を取る
    normal_doors = 0
    secret_doors = 0
    dead_end_normal = 0
    dead_end_secret = 0
    special_room_doors = 0

    # 100回テストを実行
    for _ in range(100):
        generator = DungeonGenerator(80, 50, floor=5)  # 特別な部屋が生成される階
        generator.generate()

        for room in generator.rooms:
            for door_x, door_y in room.doors:
                door = generator.tiles[door_y, door_x]

                if room.is_special:
                    special_room_doors += 1
                    assert isinstance(door, Door), "Special room door must be normal"
                else:
                    # 行き止まりの扉かどうかを判定
                    is_dead_end = False
                    connected_corridors = 0
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        if (door_x + dx, door_y + dy) in generator.corridors:
                            connected_corridors += 1
                    is_dead_end = connected_corridors == 1

                    if is_dead_end:
                        if isinstance(door, Door):
                            dead_end_normal += 1
                        else:
                            dead_end_secret += 1
                    elif isinstance(door, Door):
                        normal_doors += 1
                    else:
                        secret_doors += 1

    # 通常の扉の確率をチェック（許容誤差10%）
    total_normal_doors = normal_doors + secret_doors
    if total_normal_doors > 0:  # 分母が0でないことを確認
        normal_ratio = normal_doors / total_normal_doors
        assert 0.4 <= normal_ratio <= 0.6, "Normal door ratio out of expected range"

    # 行き止まりの扉の確率をチェック（許容誤差10%）
    total_dead_end_doors = dead_end_normal + dead_end_secret
    if total_dead_end_doors > 0:  # 分母が0でないことを確認
        dead_end_normal_ratio = dead_end_normal / total_dead_end_doors
        assert 0.15 <= dead_end_normal_ratio <= 0.35, (
            "Dead end normal door ratio out of expected range"
        )

    # 特別な部屋の扉は全て通常の扉
    assert special_room_doors > 0, "No special room doors generated"


def test_special_room_corridor_intersection():
    """特別な部屋への通路が他の通路と交差しないことをテスト"""
    generator = DungeonGenerator(80, 50, floor=5)
    generator.generate()

    special_rooms = [room for room in generator.rooms if room.is_special]
    if special_rooms:
        for room in special_rooms:
            # 特別な部屋の扉から通路を追跡
            for door_x, door_y in room.doors:
                # 扉から接続される通路の座標を収集
                special_corridor = set()
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    next_x, next_y = door_x + dx, door_y + dy
                    if (next_x, next_y) in generator.corridors:
                        special_corridor.add((next_x, next_y))
                        # 通路を追跡
                        while (next_x, next_y) in generator.corridors:
                            special_corridor.add((next_x, next_y))
                            # 次の通路タイルを探す
                            found_next = False
                            for ndx, ndy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                                new_x, new_y = next_x + ndx, next_y + ndy
                                if (new_x, new_y) in generator.corridors and (
                                    new_x,
                                    new_y,
                                ) not in special_corridor:
                                    next_x, next_y = new_x, new_y
                                    found_next = True
                                    break
                            if not found_next:
                                break

                # 他の通路との交差をチェック
                other_corridors = generator.corridors - special_corridor
                for x, y in special_corridor:
                    # 上下左右の通路をチェック
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        if (x + dx, y + dy) in other_corridors:
                            assert False, (
                                "Special room corridor intersects with other corridor"
                            )


def test_door_on_walls_only():
    """扉が壁にのみ配置されていることをテスト"""
    generator = DungeonGenerator(80, 50)
    generator.generate()

    for room in generator.rooms:
        # 部屋の内部の座標を取得
        interior_coords = set(
            (x, y)
            for x in range(room.x + 1, room.x + room.width - 1)
            for y in range(room.y + 1, room.y + room.height - 1)
        )

        # 扉の座標が部屋の内部に含まれていないことを確認
        for door_x, door_y in room.doors:
            assert (door_x, door_y) not in interior_coords, (
                "Door found inside room interior"
            )

            # 扉が壁上にあることを確認
            is_on_wall = (
                (
                    door_y == room.y or door_y == room.y + room.height - 1
                )  # 北壁または南壁
                or (
                    door_x == room.x or door_x == room.x + room.width - 1
                )  # 西壁または東壁
            )
            assert is_on_wall, "Door not placed on wall"


def test_dead_end_corridors():
    """行き止まりの通路生成をテスト"""
    generator = DungeonGenerator(80, 50)
    generator.generate()

    # 行き止まりの通路を探す
    dead_ends = []
    for x, y in generator.corridors:
        # 通路の接続数をカウント
        connections = 0
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            next_x, next_y = x + dx, y + dy
            if (next_x, next_y) in generator.corridors or isinstance(
                generator.tiles[next_y, next_x], (Door, SecretDoor)
            ):
                connections += 1

        # 接続が1つのみの通路は行き止まり
        if connections == 1:
            dead_ends.append((x, y))

    # 行き止まりの数をチェック（2-4個の範囲内）
    assert 2 <= len(dead_ends) <= 4, f"Unexpected number of dead ends: {len(dead_ends)}"

    # 各行き止まりが部屋と交差していないことを確認
    for dead_end_x, dead_end_y in dead_ends:
        for room in generator.rooms:
            assert not (
                room.x < dead_end_x < room.x + room.width - 1
                and room.y < dead_end_y < room.y + room.height - 1
            ), "Dead end corridor intersects with room"


def test_special_room_generation():
    """特別な部屋の生成ルールをテスト"""
    # 特別な部屋が生成される階でテスト
    special_floor_levels = [1, 5, 10, 15, 20, 25]
    for floor in special_floor_levels:
        generator = DungeonGenerator(80, 50, floor=floor)
        generator.generate()

        # 特別な部屋を探す
        special_rooms = [room for room in generator.rooms if room.is_special]

        # 特別な部屋が1つ存在することを確認
        assert len(special_rooms) == 1, (
            f"Floor {floor} should have exactly one special room"
        )

        special_room = special_rooms[0]

        # 部屋のタイプが正しいことを確認
        assert special_room.room_type in [
            "treasure",
            "armory",
            "food",
            "monster",
            "library",
            "laboratory",
        ], f"Invalid special room type: {special_room.room_type}"

        # 特別な部屋のメッセージが存在することを確認
        assert special_room.get_special_room_message(), (
            f"Special room message not found for type: {special_room.room_type}"
        )


def test_no_special_room_on_normal_floors():
    """通常の階では特別な部屋が生成されないことをテスト"""
    normal_floors = [2, 3, 4, 6, 7, 8, 9, 11, 12]
    for floor in normal_floors:
        generator = DungeonGenerator(80, 50, floor=floor)
        generator.generate()

        # 特別な部屋が存在しないことを確認
        special_rooms = [room for room in generator.rooms if room.is_special]
        assert len(special_rooms) == 0, f"Floor {floor} should not have special rooms"


def test_room_connectivity():
    """全ての部屋が接続されていることをテスト"""
    generator = DungeonGenerator(80, 50)
    generator.generate()

    # 部屋が存在することを確認
    assert len(generator.rooms) > 0, "No rooms generated"

    # 最初の部屋から到達可能な部屋を探索
    visited = set()
    to_visit = {generator.rooms[0]}

    while to_visit:
        room = to_visit.pop()
        visited.add(room)

        # 接続された部屋を探索
        for other_room in generator.rooms:
            if other_room not in visited and room.is_connected_to(other_room):
                to_visit.add(other_room)

    # 全ての部屋が接続されていることを確認
    assert len(visited) == len(generator.rooms), "Not all rooms are connected"


def test_room_id_uniqueness():
    """部屋のIDが一意であることをテスト"""
    generator = DungeonGenerator(80, 50)
    generator.generate()

    # 全ての部屋のIDを収集
    room_ids = [room._id for room in generator.rooms]

    # IDが重複していないことを確認
    assert len(room_ids) == len(set(room_ids)), "Duplicate room IDs found"


def test_map_boundary():
    """マップの境界が壁で囲まれていることをテスト"""
    generator = DungeonGenerator(80, 50)
    generator.generate()

    # 上下の境界をチェック
    for x in range(generator.width):
        assert isinstance(generator.tiles[0, x], Wall), "Top boundary is not wall"
        assert isinstance(generator.tiles[generator.height - 1, x], Wall), (
            "Bottom boundary is not wall"
        )

    # 左右の境界をチェック
    for y in range(generator.height):
        assert isinstance(generator.tiles[y, 0], Wall), "Left boundary is not wall"
        assert isinstance(generator.tiles[y, generator.width - 1], Wall), (
            "Right boundary is not wall"
        )


def test_stairs_in_room_interior():
    """階段が部屋の内部に配置されていることをテスト"""
    generator = DungeonGenerator(80, 50)
    tiles, start_pos, end_pos = generator.generate()

    def is_in_room_interior(pos: tuple[int, int], room: Room) -> bool:
        """座標が部屋の内部にあるかチェック"""
        return pos in room.inner

    # 上り階段のチェック
    up_stairs_in_interior = any(
        is_in_room_interior(start_pos, room) for room in generator.rooms
    )
    assert up_stairs_in_interior, "Up stairs not in room interior"

    # 下り階段のチェック
    down_stairs_in_interior = any(
        is_in_room_interior(end_pos, room) for room in generator.rooms
    )
    assert down_stairs_in_interior, "Down stairs not in room interior"


def test_corridor_boundary_distance():
    """通路がマップ境界から適切な距離を保っているかテスト"""
    dungeon = DungeonGenerator(80, 50)
    tiles, _, _ = dungeon.generate()

    # マップ境界から2マス以内には通路が生成されていないことを確認
    for y in range(50):
        for x in range(80):
            if isinstance(tiles[y, x], Floor) and (x, y) in dungeon.corridors:
                # 境界からの距離が2マス以上あることを確認
                assert x > 2 and x < 77, (
                    f"Corridor at ({x}, {y}) is too close to horizontal boundary"
                )
                assert y > 2 and y < 47, (
                    f"Corridor at ({x}, {y}) is too close to vertical boundary"
                )


def test_dead_end_boundary_distance():
    """行き止まり通路がマップ境界から適切な距離を保っているかテスト"""
    dungeon = DungeonGenerator(80, 50)
    tiles, _, _ = dungeon.generate()

    # 行き止まりを特定（3方向が壁に囲まれたFloorタイル）
    for y in range(1, 49):
        for x in range(1, 79):
            if isinstance(tiles[y, x], Floor) and (x, y) in dungeon.corridors:
                wall_count = 0
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    if isinstance(tiles[y + dy, x + dx], Wall):
                        wall_count += 1

                # 行き止まりの場合（3方向以上が壁）
                if wall_count >= 3:
                    # 境界からの距離が2マス以上あることを確認
                    assert x > 2 and x < 77, (
                        f"Dead end at ({x}, {y}) is too close to horizontal boundary"
                    )
                    assert y > 2 and y < 47, (
                        f"Dead end at ({x}, {y}) is too close to vertical boundary"
                    )


def test_corridor_creation_near_boundary():
    """境界付近での通路生成が適切に制限されているかテスト"""
    dungeon = DungeonGenerator(80, 50)

    # 境界付近の座標で通路生成を試みる
    boundary_positions = [
        ((2, 25), (10, 25)),  # 左境界付近
        ((70, 25), (78, 25)),  # 右境界付近
        ((40, 2), (40, 10)),  # 上境界付近
        ((40, 40), (40, 48)),  # 下境界付近
    ]

    for start, end in boundary_positions:
        # 境界付近での通路生成は失敗するはず
        assert not dungeon._can_create_corridor(start, end), (
            f"Corridor creation should fail near boundary: {start} to {end}"
        )
