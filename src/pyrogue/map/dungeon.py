"""Dungeon generation module."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Set
import random
import numpy as np

from pyrogue.utils import game_logger
from .tile import Tile, Floor, Wall, Door, SecretDoor, Stairs, Water, Lava

@dataclass
class Room:
    """部屋を表すクラス"""
    x: int
    y: int
    width: int
    height: int
    is_special: bool = False
    room_type: Optional[str] = None
    connected_rooms: Set[int] = field(default_factory=set)
    doors: List[Tuple[int, int]] = field(default_factory=list)
    id: int = field(default_factory=lambda: next(Room._id_counter))

    # IDカウンター
    _id_counter = iter(range(1000000))

    @property
    def center(self) -> Tuple[int, int]:
        """部屋の中心座標を返す"""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def inner(self) -> List[Tuple[int, int]]:
        """部屋の内部の座標リストを返す（壁と扉を除く）"""
        return [
            (x, y)
            for x in range(self.x + 1, self.x + self.width - 1)
            for y in range(self.y + 1, self.y + self.height - 1)
        ]

    def get_wall_center(self, direction: str) -> Tuple[int, int]:
        """指定した方向の壁の中心座標を返す"""
        if direction == "north":
            return (self.x + self.width // 2, self.y)
        elif direction == "south":
            return (self.x + self.width // 2, self.y + self.height - 1)
        elif direction == "west":
            return (self.x, self.y + self.height // 2)
        elif direction == "east":
            return (self.x + self.width - 1, self.y + self.height // 2)
        raise ValueError(f"Invalid direction: {direction}")

class DungeonGenerator:
    """ダンジョン生成クラス"""
    SPECIAL_ROOM_TYPES = ["treasure", "armory", "food", "monster", "laboratory", "library"]

    def __init__(
        self,
        width: int,
        height: int,
        floor: int = 1,
        min_room_size: Tuple[int, int] = (6, 6),
        max_room_size: Tuple[int, int] = (10, 10),
    ) -> None:
        self.width = width
        self.height = height
        self.floor = floor
        self.min_room_size = min_room_size
        self.max_room_size = max_room_size
        self.rooms: List[Room] = []
        self.tiles = np.full((height, width), fill_value=Wall(), dtype=object)
        self.start_pos: Optional[Tuple[int, int]] = None
        self.end_pos: Optional[Tuple[int, int]] = None

    def _create_room(self, room: Room) -> None:
        """部屋を生成する"""
        # 部屋の外周を壁に
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if (y == room.y or y == room.y + room.height - 1 or
                    x == room.x or x == room.x + room.width - 1):
                    self.tiles[y, x] = Wall()
                else:
                    self.tiles[y, x] = Floor()

        # 特別な部屋の場合、部屋タイプに応じたアイテムを配置
        if room.is_special and room.room_type:
            self._decorate_special_room(room)

    def _decorate_special_room(self, room: Room) -> None:
        """特別な部屋を装飾する"""
        inner_tiles = room.inner
        if not inner_tiles:
            return

        if room.room_type == "treasure":
            # 宝物庫：金貨とアイテムを配置
            gold_count = random.randint(100, 250)
            positions = random.sample(inner_tiles, min(len(inner_tiles), gold_count))
            for x, y in positions:
                self.tiles[y, x] = Floor(has_gold=True)

        elif room.room_type == "laboratory":
            # 実験室：ランダムな薬を配置
            potion_count = random.randint(5, 10)
            positions = random.sample(inner_tiles, min(len(inner_tiles), potion_count))
            for x, y in positions:
                self.tiles[y, x] = Floor(has_potion=True)

        elif room.room_type == "library":
            # 図書室：巻物を配置
            scroll_count = random.randint(5, 10)
            positions = random.sample(inner_tiles, min(len(inner_tiles), scroll_count))
            for x, y in positions:
                self.tiles[y, x] = Floor(has_scroll=True)

        # 他の特別な部屋タイプも同様に実装

    def _create_special_rooms(self) -> None:
        """特別な部屋を生成"""
        # 5階ごとに1つの特別な部屋を生成（10%の確率）
        if self.floor % 5 == 0 and random.random() < 0.1:
            room_type = random.choice(self.SPECIAL_ROOM_TYPES)
            width = random.randint(self.min_room_size[0], min(self.max_room_size[0], 5))
            height = random.randint(self.min_room_size[1], min(self.max_room_size[1], 5))
            
            # 部屋の配置位置を探す
            for _ in range(50):  # 最大50回試行
                x = random.randint(1, self.width - width - 1)
                y = random.randint(1, self.height - height - 1)
                
                # 既存の部屋と重なっていないか確認
                overlaps = False
                for room in self.rooms:
                    if (x < room.x + room.width + 2 and x + width + 2 > room.x and
                        y < room.y + room.height + 2 and y + height + 2 > room.y):
                        overlaps = True
                        break
                
                if not overlaps:
                    room = Room(x=x, y=y, width=width, height=height, is_special=True, room_type=room_type)
                    self._create_room(room)
                    self.rooms.append(room)
                    break

    def _connect_rooms(self) -> None:
        """部屋同士を接続"""
        # 最小全域木を使用して部屋を接続
        edges: List[Tuple[float, int, int]] = []  # (distance, room1_id, room2_id)
        room_dict = {room.id: room for room in self.rooms}
        
        for i, room1 in enumerate(self.rooms):
            for room2 in self.rooms[i + 1:]:
                distance = ((room1.center[0] - room2.center[0]) ** 2 + 
                          (room1.center[1] - room2.center[1]) ** 2) ** 0.5
                edges.append((distance, room1.id, room2.id))

        # 距離でソート
        edges.sort()

        # Union-Find用の親配列
        parent = {room.id: room.id for room in self.rooms}

        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x: int, y: int) -> None:
            parent[find(x)] = find(y)

        # 最小全域木を構築（30%の確率で追加の接続を作成）
        for distance, room1_id, room2_id in edges:
            room1 = room_dict[room1_id]
            room2 = room_dict[room2_id]
            if find(room1.id) != find(room2.id) or random.random() < 0.3:
                self._create_corridor(room1, room2)
                union(room1.id, room2.id)
                room1.connected_rooms.add(room2.id)
                room2.connected_rooms.add(room1.id)

    def _create_corridor(self, room1: Room, room2: Room) -> None:
        """2つの部屋を接続する通路を生成"""
        x1, y1 = room1.center
        x2, y2 = room2.center

        # 部屋の相対位置に基づいて扉の位置を決定
        if abs(x1 - x2) > abs(y1 - y2):
            # 水平方向の接続
            if x1 < x2:
                door1_pos = room1.get_wall_center("east")
                door2_pos = room2.get_wall_center("west")
            else:
                door1_pos = room1.get_wall_center("west")
                door2_pos = room2.get_wall_center("east")
        else:
            # 垂直方向の接続
            if y1 < y2:
                door1_pos = room1.get_wall_center("south")
                door2_pos = room2.get_wall_center("north")
            else:
                door1_pos = room1.get_wall_center("north")
                door2_pos = room2.get_wall_center("south")

        # 扉を配置
        is_special_room = room1.is_special or room2.is_special
        for door_x, door_y in [door1_pos, door2_pos]:
            door = Door() if is_special_room else (SecretDoor() if random.random() < 0.5 else Door())
            self.tiles[door_y, door_x] = door
            if door_x == door1_pos[0] and door_y == door1_pos[1]:
                room1.doors.append((door_x, door_y))
            else:
                room2.doors.append((door_x, door_y))

        # L字型の通路を生成
        if abs(x1 - x2) > abs(y1 - y2):
            # 水平方向が長い場合、水平→垂直の順で通路を生成
            self._create_h_tunnel(door1_pos[0], door2_pos[0], door1_pos[1])
            self._create_v_tunnel(door1_pos[1], door2_pos[1], door2_pos[0])
        else:
            # 垂直方向が長い場合、垂直→水平の順で通路を生成
            self._create_v_tunnel(door1_pos[1], door2_pos[1], door1_pos[0])
            self._create_h_tunnel(door1_pos[0], door2_pos[0], door2_pos[1])

    def _create_h_tunnel(self, x1: int, x2: int, y: int) -> None:
        """水平方向の通路を生成"""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if not isinstance(self.tiles[y, x], Door):
                self.tiles[y, x] = Floor()

    def _create_v_tunnel(self, y1: int, y2: int, x: int) -> None:
        """垂直方向の通路を生成"""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if not isinstance(self.tiles[y, x], Door):
                self.tiles[y, x] = Floor()

    def _place_stairs(self) -> None:
        """階段を配置"""
        # 上り階段用の部屋を選択（特別な部屋は除外）
        normal_rooms = [room for room in self.rooms if not room.is_special]
        if not normal_rooms:
            return

        up_room = random.choice(normal_rooms)
        up_x, up_y = random.choice(up_room.inner)
        self.tiles[up_y, up_x] = Stairs(down=False)
        self.start_pos = (up_x, up_y)

        # 下り階段用の部屋を選択
        # - 上り階段とは別の部屋
        # - 特別な部屋は除外
        # - 上り階段の部屋から十分離れた部屋を選択
        available_rooms = []
        for room in normal_rooms:
            if room == up_room:
                continue
            
            # 部屋の中心点間の距離を計算
            dx = room.center[0] - up_room.center[0]
            dy = room.center[1] - up_room.center[1]
            distance = (dx * dx + dy * dy) ** 0.5
            
            # 最低でも部屋3つ分は離す
            min_separation = max(self.max_room_size) * 3
            if distance >= min_separation:
                available_rooms.append(room)

        if not available_rooms:
            # 十分離れた部屋がない場合は、上り階段以外の部屋から選択
            available_rooms = [room for room in normal_rooms if room != up_room]
            if not available_rooms:
                return

        # 利用可能な部屋の中から、最も遠い部屋を優先的に選択
        down_room = random.choice(available_rooms[-3:])  # 最も遠い3部屋からランダムに選択
        down_x, down_y = random.choice(down_room.inner)
        self.tiles[down_y, down_x] = Stairs(down=True)
        self.end_pos = (down_x, down_y)

    def generate(self) -> Tuple[np.ndarray, Tuple[int, int], Tuple[int, int]]:
        """ダンジョンを生成"""
        # 特別な部屋を生成
        self._create_special_rooms()

        # 通常の部屋を生成（ランダムな位置に配置）
        for _ in range(random.randint(8, 12)):  # 8-12個の部屋
            for _ in range(50):  # 最大50回試行
                width = random.randint(self.min_room_size[0], self.max_room_size[0])
                height = random.randint(self.min_room_size[1], self.max_room_size[1])
                x = random.randint(1, self.width - width - 1)
                y = random.randint(1, self.height - height - 1)

                # 既存の部屋と重なっていないか確認（通路用の余白も確保）
                overlaps = False
                for room in self.rooms:
                    if (x < room.x + room.width + 2 and x + width + 2 > room.x and
                        y < room.y + room.height + 2 and y + height + 2 > room.y):
                        overlaps = True
                        break

                if not overlaps:
                    room = Room(x=x, y=y, width=width, height=height)
                    self._create_room(room)
                    self.rooms.append(room)
                    break

        # 部屋を接続
        self._connect_rooms()

        # 階段を配置
        self._place_stairs()

        return self.tiles, self.start_pos, self.end_pos 