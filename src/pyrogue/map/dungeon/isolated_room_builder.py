"""
孤立部屋群生成システム。

隠し通路でのみアクセス可能な独立した部屋群を生成する。
メインダンジョンから完全に分離されており、秘密の通路を発見することでのみアクセス可能。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import numpy as np

from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Floor, Wall, SecretDoor
from pyrogue.utils import game_logger

if TYPE_CHECKING:
    pass


class IsolatedRoomGroup:
    """
    孤立部屋群を表すクラス。

    メインダンジョンから分離された部屋群で、
    隠し通路でのみアクセス可能。
    """

    def __init__(self, rooms: list[Room], access_points: list[tuple[int, int]]) -> None:
        """
        孤立部屋群を初期化。

        Args:
            rooms: 部屋群
            access_points: アクセスポイント（隠し通路の位置）
        """
        self.rooms = rooms
        self.access_points = access_points
        self.is_discovered = False
        self.group_id = random.randint(1000, 9999)

        game_logger.debug(f"IsolatedRoomGroup created: {len(rooms)} rooms, {len(access_points)} access points")


class IsolatedRoomBuilder:
    """
    孤立部屋群生成ビルダー。

    メインダンジョンから分離された部屋群を生成し、
    隠し通路でのみアクセス可能にする。
    """

    def __init__(self, width: int, height: int, isolation_level: float = 0.8) -> None:
        """
        孤立部屋ビルダーを初期化。

        Args:
            width: ダンジョンの幅
            height: ダンジョンの高さ
            isolation_level: 孤立度（0.0-1.0）。高いほど発見が困難
        """
        self.width = width
        self.height = height
        self.isolation_level = isolation_level
        self.isolated_groups: list[IsolatedRoomGroup] = []
        self.used_areas: set[tuple[int, int]] = set()

        game_logger.info(f"IsolatedRoomBuilder initialized: {width}x{height}, isolation_level={isolation_level}")

    def generate_isolated_rooms(
        self,
        tiles: np.ndarray,
        existing_rooms: list[Room],
        max_groups: int = 3
    ) -> list[IsolatedRoomGroup]:
        """
        孤立部屋群を生成。

        Args:
            tiles: タイル配列
            existing_rooms: 既存の部屋群
            max_groups: 最大グループ数

        Returns:
            生成された孤立部屋群のリスト
        """
        # 状態をリセットしてから開始
        self.reset()

        # 既存の部屋エリアをマーク
        self._mark_existing_areas(existing_rooms)

        # 孤立部屋群を生成
        for group_id in range(max_groups):
            isolated_group = self._generate_single_group(tiles, group_id)
            if isolated_group:
                self.isolated_groups.append(isolated_group)

        # 隠し通路でメインダンジョンに接続
        self._connect_with_secret_passages(tiles, existing_rooms)

        game_logger.info(f"Generated {len(self.isolated_groups)} isolated room groups")
        return self.isolated_groups

    def _mark_existing_areas(self, existing_rooms: list[Room]) -> None:
        """既存の部屋エリアをマーク。"""
        for room in existing_rooms:
            for x in range(room.x - 2, room.x + room.width + 2):
                for y in range(room.y - 2, room.y + room.height + 2):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.used_areas.add((x, y))

    def _generate_single_group(self, tiles: np.ndarray, group_id: int) -> IsolatedRoomGroup | None:
        """
        単一の孤立部屋群を生成。

        Args:
            tiles: タイル配列
            group_id: グループID

        Returns:
            生成された孤立部屋群、または None
        """
        # 孤立エリアの位置を決定
        isolation_area = self._find_isolation_area()
        if not isolation_area:
            return None

        area_x, area_y, area_width, area_height = isolation_area

        # 孤立エリア内に小さな部屋群を生成
        rooms = self._generate_rooms_in_area(area_x, area_y, area_width, area_height)
        if not rooms:
            return None

        # 部屋をタイルに配置
        self._place_rooms_in_tiles(rooms, tiles)

        # 部屋間を通路で接続
        self._connect_rooms_in_group(rooms, tiles)

        # アクセスポイントを決定
        access_points = self._determine_access_points(rooms)

        return IsolatedRoomGroup(rooms, access_points)

    def _find_isolation_area(self) -> tuple[int, int, int, int] | None:
        """
        孤立エリアを見つける。

        Returns:
            (x, y, width, height) または None
        """
        # 孤立エリアのサイズを決定
        area_width = random.randint(15, 25)
        area_height = random.randint(10, 15)

        # 利用可能な位置を検索
        max_attempts = 50
        for _ in range(max_attempts):
            x = random.randint(5, self.width - area_width - 5)
            y = random.randint(5, self.height - area_height - 5)

            # エリアが既存の部屋と重複しないかチェック
            if self._is_area_available(x, y, area_width, area_height):
                # 使用済みエリアとしてマーク
                for ax in range(x, x + area_width):
                    for ay in range(y, y + area_height):
                        self.used_areas.add((ax, ay))
                return (x, y, area_width, area_height)

        return None

    def _is_area_available(self, x: int, y: int, width: int, height: int) -> bool:
        """エリアが利用可能かチェック。"""
        buffer = 5  # 既存エリアからの最小距離

        for ax in range(x - buffer, x + width + buffer):
            for ay in range(y - buffer, y + height + buffer):
                if (ax, ay) in self.used_areas:
                    return False
        return True

    def _generate_rooms_in_area(self, area_x: int, area_y: int, area_width: int, area_height: int) -> list[Room]:
        """孤立エリア内に部屋を生成。"""
        rooms = []
        room_count = random.randint(2, 4)

        for i in range(room_count):
            # 部屋サイズを決定
            room_width = random.randint(5, 8)
            room_height = random.randint(4, 6)

            # 部屋位置を決定
            max_attempts = 20
            for _ in range(max_attempts):
                x = random.randint(area_x + 1, area_x + area_width - room_width - 1)
                y = random.randint(area_y + 1, area_y + area_height - room_height - 1)

                # 他の部屋と重複しないかチェック
                new_room = Room(x, y, room_width, room_height)
                if not self._room_overlaps_with_existing(new_room, rooms):
                    new_room.id = f"isolated_{len(rooms)}"
                    new_room.is_isolated = True
                    rooms.append(new_room)
                    break

        return rooms

    def _room_overlaps_with_existing(self, new_room: Room, existing_rooms: list[Room]) -> bool:
        """新しい部屋が既存の部屋と重複するかチェック。"""
        for room in existing_rooms:
            if (new_room.x < room.x + room.width + 2 and
                new_room.x + new_room.width + 2 > room.x and
                new_room.y < room.y + room.height + 2 and
                new_room.y + new_room.height + 2 > room.y):
                return True
        return False

    def _place_rooms_in_tiles(self, rooms: list[Room], tiles: np.ndarray) -> None:
        """部屋をタイルに配置。"""
        for room in rooms:
            # 部屋の内部を床に設定
            for y in range(room.y + 1, room.y + room.height - 1):
                for x in range(room.x + 1, room.x + room.width - 1):
                    if 0 <= y < self.height and 0 <= x < self.width:
                        tiles[y, x] = Floor()

            # 部屋の境界は壁のまま（既に初期化済み）

    def _connect_rooms_in_group(self, rooms: list[Room], tiles: np.ndarray) -> None:
        """グループ内の部屋を通路で接続。"""
        if len(rooms) < 2:
            return

        # 最小スパニングツリーで部屋を接続
        connected_rooms = {rooms[0]}
        unconnected_rooms = set(rooms[1:])

        while unconnected_rooms:
            # 最も近い部屋ペアを見つける
            min_distance = float('inf')
            closest_pair = None

            for connected_room in connected_rooms:
                for unconnected_room in unconnected_rooms:
                    distance = self._calculate_room_distance(connected_room, unconnected_room)
                    if distance < min_distance:
                        min_distance = distance
                        closest_pair = (connected_room, unconnected_room)

            if closest_pair:
                room1, room2 = closest_pair
                self._create_corridor_between_rooms(room1, room2, tiles)

                # 接続情報を更新
                room1.connected_rooms.add(room2.id)
                room2.connected_rooms.add(room1.id)

                connected_rooms.add(room2)
                unconnected_rooms.remove(room2)

    def _calculate_room_distance(self, room1: Room, room2: Room) -> float:
        """部屋間の距離を計算。"""
        center1 = room1.center()
        center2 = room2.center()
        return ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5

    def _create_corridor_between_rooms(self, room1: Room, room2: Room, tiles: np.ndarray) -> None:
        """部屋間に通路を作成。"""
        start = room1.center()
        end = room2.center()

        # L字型の通路を作成
        current_x, current_y = start
        target_x, target_y = end

        # 水平方向に移動
        while current_x != target_x:
            if current_x < target_x:
                current_x += 1
            else:
                current_x -= 1

            if 0 <= current_y < self.height and 0 <= current_x < self.width:
                tiles[current_y, current_x] = Floor()

        # 垂直方向に移動
        while current_y != target_y:
            if current_y < target_y:
                current_y += 1
            else:
                current_y -= 1

            if 0 <= current_y < self.height and 0 <= current_x < self.width:
                tiles[current_y, current_x] = Floor()

    def _determine_access_points(self, rooms: list[Room]) -> list[tuple[int, int]]:
        """アクセスポイントを決定。"""
        access_points = []

        # 各部屋に1つずつアクセスポイントを設定
        for room in rooms:
            # 部屋の境界からランダムに選択
            walls = []

            # 上下の壁
            for x in range(room.x + 1, room.x + room.width - 1):
                walls.append((x, room.y))  # 上壁
                walls.append((x, room.y + room.height - 1))  # 下壁

            # 左右の壁
            for y in range(room.y + 1, room.y + room.height - 1):
                walls.append((room.x, y))  # 左壁
                walls.append((room.x + room.width - 1, y))  # 右壁

            if walls:
                access_point = random.choice(walls)
                access_points.append(access_point)

        return access_points

    def _connect_with_secret_passages(self, tiles: np.ndarray, existing_rooms: list[Room]) -> None:
        """隠し通路でメインダンジョンに接続。"""
        for group in self.isolated_groups:
            # 孤立度に基づいて隠し通路の数を決定
            secret_passages = max(1, int(len(group.access_points) * (1.0 - self.isolation_level)))

            for i in range(min(secret_passages, len(group.access_points))):
                access_point = group.access_points[i]

                # 最も近いメインダンジョンの部屋を見つける
                nearest_room = self._find_nearest_main_room(access_point, existing_rooms)
                if nearest_room:
                    # 隠し通路を作成
                    self._create_secret_passage(access_point, nearest_room, tiles)

    def _find_nearest_main_room(self, access_point: tuple[int, int], existing_rooms: list[Room]) -> Room | None:
        """最も近いメインダンジョンの部屋を見つける。"""
        if not existing_rooms:
            return None

        min_distance = float('inf')
        nearest_room = None

        for room in existing_rooms:
            center = room.center()
            distance = ((access_point[0] - center[0]) ** 2 + (access_point[1] - center[1]) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_room = room

        return nearest_room

    def _create_secret_passage(self, start: tuple[int, int], target_room: Room, tiles: np.ndarray) -> None:
        """隠し通路を作成。"""
        # 目標部屋の境界上のランダムな点を選択
        target_walls = []

        # 上下の壁
        for x in range(target_room.x + 1, target_room.x + target_room.width - 1):
            target_walls.append((x, target_room.y))
            target_walls.append((x, target_room.y + target_room.height - 1))

        # 左右の壁
        for y in range(target_room.y + 1, target_room.y + target_room.height - 1):
            target_walls.append((target_room.x, y))
            target_walls.append((target_room.x + target_room.width - 1, y))

        if not target_walls:
            return

        target = random.choice(target_walls)

        # 隠し通路を作成（直線的ではなく、曲がりくねった通路）
        current_x, current_y = start
        target_x, target_y = target

        # 隠し通路のパスを計算
        path = self._calculate_secret_path(current_x, current_y, target_x, target_y)

        # 隠し通路を配置
        for x, y in path:
            if 0 <= x < self.width and 0 <= y < self.height:
                if isinstance(tiles[y, x], Wall):
                    tiles[y, x] = SecretDoor()

        game_logger.debug(f"Created secret passage from {start} to {target}")

    def _calculate_secret_path(self, start_x: int, start_y: int, end_x: int, end_y: int) -> list[tuple[int, int]]:
        """隠し通路のパスを計算。"""
        path = []
        current_x, current_y = start_x, start_y

        # 曲がりくねった通路を作成
        while current_x != end_x or current_y != end_y:
            path.append((current_x, current_y))

            # ランダムに方向を選択（目標方向に偏重）
            dx = 0 if current_x == end_x else (1 if current_x < end_x else -1)
            dy = 0 if current_y == end_y else (1 if current_y < end_y else -1)

            # 50%の確率で最適方向、50%の確率でランダム方向
            if random.random() < 0.5:
                # 最適方向
                if dx != 0 and dy != 0:
                    if random.random() < 0.5:
                        current_x += dx
                    else:
                        current_y += dy
                elif dx != 0:
                    current_x += dx
                elif dy != 0:
                    current_y += dy
            else:
                # ランダム方向（ただし目標から離れない）
                possible_moves = []
                if dx != 0:
                    possible_moves.append((dx, 0))
                if dy != 0:
                    possible_moves.append((0, dy))

                if possible_moves:
                    move_dx, move_dy = random.choice(possible_moves)
                    current_x += move_dx
                    current_y += move_dy

        path.append((current_x, current_y))
        return path

    def get_isolated_groups(self) -> list[IsolatedRoomGroup]:
        """生成された孤立部屋群を取得。"""
        return self.isolated_groups

    def reset(self) -> None:
        """ビルダーの状態をリセット。"""
        self.isolated_groups = []
        self.used_areas.clear()

    def get_statistics(self) -> dict:
        """生成統計を取得。"""
        total_rooms = sum(len(group.rooms) for group in self.isolated_groups)
        total_access_points = sum(len(group.access_points) for group in self.isolated_groups)

        return {
            "builder_type": "IsolatedRooms",
            "isolation_level": self.isolation_level,
            "group_count": len(self.isolated_groups),
            "total_rooms": total_rooms,
            "total_access_points": total_access_points,
        }
