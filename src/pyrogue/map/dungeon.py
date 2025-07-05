"""
ダンジョン生成モジュール。

このモジュールは、オリジナルRogue式のダンジョン生成アルゴリズムを提供します。
3x3グリッドに部屋を配置し、通路で接続することで、伝統的なローグライクゲームの
ダンジョン構造を再現します。

Example:
    >>> generator = DungeonGenerator(width=80, height=50, floor=1)
    >>> tiles, start_pos, end_pos = generator.generate()

"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np

from .tile import (
    Door,
    Floor,
    SecretDoor,
    StairsDown,
    StairsUp,
    Wall,
)

# Import after class definitions to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dungeon_builder import CorridorBuilder, RoomConnector, StairsManager


@dataclass
class Room:
    """
    ダンジョンの部屋を表すクラス。

    部屋は矩形の形状を持ち、特別な部屋タイプを持つ場合があります。
    各部屋は他の部屋との接続関係を管理し、ドアの配置情報も保持します。

    Attributes:
        x: 部屋の左上隅のX座標
        y: 部屋の左上隅のY座標
        width: 部屋の幅
        height: 部屋の高さ
        is_special: 特別な部屋かどうか
        room_type: 部屋のタイプ（treasure, armory等）
        connected_rooms: 接続されている部屋のIDセット
        doors: ドアの座標リスト
        id: 部屋の一意識別子

    """

    x: int
    y: int
    width: int
    height: int
    is_special: bool = False
    room_type: str | None = None
    connected_rooms: set[int] = field(default_factory=set)
    doors: list[tuple[int, int]] = field(default_factory=list)
    id: int = field(default_factory=lambda: next(Room._id_counter))

    # 部屋の一意識別子を生成するためのカウンター
    _id_counter = iter(range(1000000))

    def __hash__(self) -> int:
        """
        Roomオブジェクトをハッシュ可能にする。

        Returns:
            部屋のIDに基づくハッシュ値

        """
        return hash(self.id)

    @property
    def _id(self) -> int:
        """
        テスト互換性のため_id属性を提供。

        Returns:
            部屋のID

        """
        return self.id

    @property
    def center(self) -> tuple[int, int]:
        """
        部屋の中心座標を返す。

        Returns:
            (x, y)形式の部屋の中心座標

        """
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def inner(self) -> list[tuple[int, int]]:
        """
        部屋の内部の座標リストを返す（壁と扉を除く）。

        Returns:
            部屋の内部の座標リスト

        """
        return [
            (x, y)
            for x in range(self.x + 1, self.x + self.width - 1)
            for y in range(self.y + 1, self.y + self.height - 1)
        ]

    def get_wall_center(self, direction: str) -> tuple[int, int]:
        """
        指定した方向の壁の中心座標を返す。

        Args:
            direction: 方向（"north", "south", "west", "east"）

        Returns:
            指定方向の壁の中心座標

        Raises:
            ValueError: 無効な方向が指定された場合

        """
        if direction == "north":
            return (self.x + self.width // 2, self.y)
        if direction == "south":
            return (self.x + self.width // 2, self.y + self.height - 1)
        if direction == "west":
            return (self.x, self.y + self.height // 2)
        if direction == "east":
            return (self.x + self.width - 1, self.y + self.height // 2)
        raise ValueError(f"Invalid direction: {direction}")

    def get_special_room_message(self) -> str:
        """
        特別な部屋のメッセージを返す。

        Returns:
            部屋のタイプに応じたメッセージ文字列

        """
        if not self.is_special or not self.room_type:
            return ""

        messages = {
            "treasure": "この部屋には宝物が眠っている...",
            "armory": "武器と防具が並んでいる。",
            "food": "食べ物の匂いが漂っている。",
            "monster": "何か危険な気配がする...",
            "laboratory": "薬品の匂いがする実験室だ。",
            "library": "古い書物が並んでいる図書室だ。",
        }

        return messages.get(self.room_type, "特別な部屋のようだ。")

    def is_connected_to(self, other_room: Room) -> bool:
        """
        他の部屋に接続されているかどうかを確認。

        Args:
            other_room: 接続を確認する対象の部屋

        Returns:
            接続されている場合True、そうでなければFalse

        """
        return other_room.id in self.connected_rooms


class DungeonGenerator:
    """
    ダンジョン生成クラス（オリジナルRogue式）。

    3x3グリッドに部屋を配置し、通路で接続することで、
    伝統的なローグライクゲームのダンジョン構造を再現します。

    特徴:
        - 3x3グリッドでの部屋配置
        - gone room（通路のみ）の概念
        - 特別な部屋タイプ（宝物庫、実験室等）
        - 秘密のドアの配置
        - 階段の自動配置

    Attributes:
        width: ダンジョンの幅
        height: ダンジョンの高さ
        floor: 現在の階層
        rooms: 生成された部屋のリスト
        tiles: タイルマップ
        start_pos: 開始位置（上り階段）
        end_pos: 終了位置（下り階段）

    """

    SPECIAL_ROOM_TYPES = [
        "treasure",
        "armory",
        "food",
        "monster",
        "laboratory",
        "library",
    ]

    def __init__(
        self,
        width: int,
        height: int,
        floor: int = 1,
        grid_size: tuple[int, int] = (3, 3),
    ) -> None:
        """
        ダンジョン生成器を初期化。

        Args:
            width: ダンジョンの幅
            height: ダンジョンの高さ
            floor: 現在の階層数
            grid_size: グリッドのサイズ（幅, 高さ）

        """
        self.width = width
        self.height = height
        self.floor = floor
        self.grid_width, self.grid_height = grid_size
        self.cell_width = width // self.grid_width
        self.cell_height = height // self.grid_height
        self.rooms: list[Room] = []
        self.tiles = np.full((height, width), fill_value=Wall(), dtype=object)
        self.start_pos: tuple[int, int] | None = None
        self.end_pos: tuple[int, int] | None = None
        # 3x3グリッドでの部屋配置情報を管理
        self.room_grid: list[list[Room | None]] = [
            [None for _ in range(self.grid_width)] for _ in range(self.grid_height)
        ]
        # 部屋の接続状態を追跡するためのグリッド座標セット
        self.connected_rooms: set[tuple[int, int]] = set()
        # "gone room"（通路のみのグリッドセル）の位置を記録
        self.gone_rooms: set[tuple[int, int]] = set()
        # 通路の位置を追跡するセット（テスト互換性のために維持）
        self.corridors: set[tuple[int, int]] = set()
        
        # Initialize builder components (lazy initialization)
        self._room_connector = None
        self._corridor_builder = None
        self._stairs_manager = None
    
    @property
    def room_connector(self):
        """Lazy initialization of room connector."""
        if self._room_connector is None:
            from .dungeon_builder import RoomConnector
            self._room_connector = RoomConnector(self)
        return self._room_connector
    
    @property
    def corridor_builder(self):
        """Lazy initialization of corridor builder."""
        if self._corridor_builder is None:
            from .dungeon_builder import CorridorBuilder
            self._corridor_builder = CorridorBuilder(self)
        return self._corridor_builder
    
    @property
    def stairs_manager(self):
        """Lazy initialization of stairs manager."""
        if self._stairs_manager is None:
            from .dungeon_builder import StairsManager
            self._stairs_manager = StairsManager(self)
        return self._stairs_manager

    def _create_room(self, room: Room) -> None:
        """
        部屋を生成する。

        部屋の外周を壁で囲み、内部を床にします。
        特別な部屋の場合、タイプに応じたアイテムを配置します。

        Args:
            room: 生成する部屋オブジェクト

        """
        # 部屋の外周を壁に、内部を床に設定
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if (
                    y == room.y
                    or y == room.y + room.height - 1
                    or x == room.x
                    or x == room.x + room.width - 1
                ):
                    self.tiles[y, x] = Wall()
                else:
                    self.tiles[y, x] = Floor()

        # 特別な部屋の場合、部屋タイプに応じたアイテムを配置する
        if room.is_special and room.room_type:
            self._decorate_special_room(room)

    def _decorate_special_room(self, room: Room) -> None:
        """
        特別な部屋を装飾する。

        部屋のタイプに応じて適切なアイテムを配置します。

        Args:
            room: 装飾する特別な部屋

        """
        inner_tiles = room.inner
        if not inner_tiles:
            return

        if room.room_type == "treasure":
            # 宝物庫：金貨をランダムに配置
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

        # 他の特別な部屋タイプも同様に実装する予定

    def _create_rooms_in_grid(self) -> None:
        """3x3グリッドに部屋を生成（オリジナルRogue式）"""
        for grid_y in range(self.grid_height):
            for grid_x in range(self.grid_width):
                # 特別な部屋の判定（テストで指定された階層に1つ生成）
                special_floors = [1, 5, 10, 15, 20, 25]
                is_special = (
                    self.floor in special_floors and grid_x == 1 and grid_y == 1
                )

                # 特別な部屋でない場合、25%の確率で"gone room"（通路のみ）にする
                if not is_special and random.random() < 0.25:
                    self.gone_rooms.add((grid_x, grid_y))
                    continue

                # グリッドセル内での部屋のサイズと位置を決定
                # より多様なサイズの部屋を作成（安全な範囲内で）
                base_width = max(6, min(10, self.cell_width - 4))
                base_height = max(6, min(10, self.cell_height - 4))

                if is_special:
                    # 特別な部屋は大きめ
                    room_width = random.randint(
                        max(6, base_width - 1), min(10, base_width)
                    )
                    room_height = random.randint(
                        max(6, base_height - 1), min(10, base_height)
                    )
                else:
                    # 通常の部屋はサイズにバリエーション
                    size_variation = random.choice(["small", "medium", "large"])
                    if size_variation == "small":
                        room_width = random.randint(6, min(8, base_width - 1))
                        room_height = random.randint(6, min(8, base_height - 1))
                    elif size_variation == "large":
                        room_width = random.randint(
                            max(7, base_width - 2), min(10, base_width)
                        )
                        room_height = random.randint(
                            max(7, base_height - 2), min(10, base_height)
                        )
                    else:  # medium
                        room_width = random.randint(6, min(9, base_width - 1))
                        room_height = random.randint(6, min(9, base_height - 1))

                # グリッドセル内でのランダムな位置
                cell_x = grid_x * self.cell_width
                cell_y = grid_y * self.cell_height

                # セル内での余白を考慮した位置
                margin_x = max(1, (self.cell_width - room_width) // 2)
                margin_y = max(1, (self.cell_height - room_height) // 2)

                room_x = cell_x + margin_x
                room_y = cell_y + margin_y

                # 境界チェック
                if room_x + room_width >= self.width:
                    room_x = self.width - room_width - 1
                if room_y + room_height >= self.height:
                    room_y = self.height - room_height - 1

                room_type = (
                    random.choice(self.SPECIAL_ROOM_TYPES) if is_special else None
                )

                room = Room(
                    x=room_x,
                    y=room_y,
                    width=room_width,
                    height=room_height,
                    is_special=is_special,
                    room_type=room_type,
                )

                self._create_room(room)
                self.rooms.append(room)
                self.room_grid[grid_y][grid_x] = room

    def _connect_rooms_rogue_style(self) -> None:
        """部屋間を通路で接続（オリジナルRogue式）"""
        if not self.rooms:
            return

        # ランダムな部屋から開始
        start_room_idx = random.randint(0, len(self.rooms) - 1)
        start_room = self.rooms[start_room_idx]
        start_grid_pos = self._get_room_grid_position(start_room)

        if start_grid_pos:
            self.connected_rooms.add(start_grid_pos)

            # 上り階段を最初の部屋に配置
            if self.floor > 1:
                center_x, center_y = start_room.center
                self.tiles[center_y, center_x] = StairsUp()
                self.start_pos = (center_x, center_y)
            else:
                self.start_pos = start_room.center

        # 未接続の部屋がある限り接続を続ける
        while len(self.connected_rooms) < len(self.rooms):
            # 接続済みの部屋から隣接する未接続の部屋を探す
            connected_room_found = False

            for connected_pos in list(self.connected_rooms):
                neighbors = self._get_adjacent_grid_positions(connected_pos)

                for neighbor_pos in neighbors:
                    if neighbor_pos not in self.connected_rooms:
                        # 隣接する未接続の部屋またはgone roomを見つけた
                        if neighbor_pos in self.gone_rooms:
                            # gone roomの場合は通路として接続
                            self._create_gone_room_corridor(connected_pos, neighbor_pos)
                        else:
                            # 通常の部屋の場合
                            neighbor_room = self.room_grid[neighbor_pos[1]][
                                neighbor_pos[0]
                            ]
                            if neighbor_room:
                                self._create_corridor_between_grid_cells(
                                    connected_pos, neighbor_pos
                                )
                                # 部屋の接続関係を記録
                                connected_room = self.room_grid[connected_pos[1]][
                                    connected_pos[0]
                                ]
                                if connected_room:
                                    connected_room.connected_rooms.add(neighbor_room.id)
                                    neighbor_room.connected_rooms.add(connected_room.id)

                        self.connected_rooms.add(neighbor_pos)
                        connected_room_found = True
                        break

                if connected_room_found:
                    break

            # 接続できる隣接部屋がない場合、ランダムに選択
            if not connected_room_found:
                unconnected_rooms = []
                for y in range(self.grid_height):
                    for x in range(self.grid_width):
                        if (x, y) not in self.connected_rooms:
                            if (x, y) not in self.gone_rooms and self.room_grid[y][x]:
                                unconnected_rooms.append((x, y))

                if unconnected_rooms:
                    # 最も近い未接続の部屋を選択
                    target_pos = random.choice(unconnected_rooms)
                    # 最も近い接続済み部屋を見つけて接続
                    closest_connected = min(
                        self.connected_rooms,
                        key=lambda pos: abs(pos[0] - target_pos[0])
                        + abs(pos[1] - target_pos[1]),
                    )
                    self._create_corridor_between_grid_cells(
                        closest_connected, target_pos
                    )
                    # 部屋の接続関係を記録
                    target_room = self.room_grid[target_pos[1]][target_pos[0]]
                    connected_room = self.room_grid[closest_connected[1]][
                        closest_connected[0]
                    ]
                    if target_room and connected_room:
                        target_room.connected_rooms.add(connected_room.id)
                        connected_room.connected_rooms.add(target_room.id)
                    self.connected_rooms.add(target_pos)
                else:
                    break

        # 下り階段を最後に接続された部屋に配置
        if self.connected_rooms:
            last_connected = list(self.connected_rooms)[-1]
            if last_connected not in self.gone_rooms:
                last_room = self.room_grid[last_connected[1]][last_connected[0]]
                if last_room:
                    center_x, center_y = last_room.center
                    self.tiles[center_y, center_x] = StairsDown()
                    self.end_pos = (center_x, center_y)

    def _get_room_grid_position(self, room: Room) -> tuple[int, int] | None:
        """部屋のグリッド位置を取得"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.room_grid[y][x] == room:
                    return (x, y)
        return None

    def _get_adjacent_grid_positions(
        self, grid_pos: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """隣接するグリッド位置のリストを取得"""
        x, y = grid_pos
        adjacent = []

        # 上下左右の隣接セルをチェック
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                adjacent.append((nx, ny))

        return adjacent

    def _create_corridor_between_grid_cells(
        self, pos1: tuple[int, int], pos2: tuple[int, int]
    ) -> None:
        """グリッドセル間の通路を作成（オリジナルRogue式）"""
        self.corridor_builder.create_corridor_between_grid_cells(pos1, pos2)

    def _create_gone_room_corridor(
        self, connected_pos: tuple[int, int], gone_pos: tuple[int, int]
    ) -> None:
        """Gone room（通路のみ）への接続を作成"""
        # gone roomの中心に通路を作成
        gone_x, gone_y = gone_pos
        center_x = gone_x * self.cell_width + self.cell_width // 2
        center_y = gone_y * self.cell_height + self.cell_height // 2

        # オリジナルRogue式：L字型の通路を作成
        connected_x, connected_y = connected_pos
        connected_center_x = connected_x * self.cell_width + self.cell_width // 2
        connected_center_y = connected_y * self.cell_height + self.cell_height // 2

        # gone roomの中心に通路を作成
        if 0 <= center_x < self.width and 0 <= center_y < self.height:
            self.tiles[center_y, center_x] = Floor()

        # 接続済み部屋からgone roomへの通路を作成
        self._create_corridor_between_grid_cells(connected_pos, gone_pos)

    def _create_line(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """二点間に線を引く（オリジナルRogue式、ドア配置付き）"""
        # 壁を通路に変換し、部屋の壁を貫通する場所にドアを配置
        if x1 == x2:  # 縦線
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= x1 < self.width and 0 <= y < self.height:
                    current_tile = self.tiles[y, x1]
                    if isinstance(current_tile, Wall):
                        # 部屋の壁を貫通している場合はドア、通路はFloor
                        if self._is_room_wall(x1, y):
                            room = self._find_room_at_wall(x1, y)
                            if room and room.is_special:
                                # 特別な部屋は必ず通常のドア
                                door = Door()
                            else:
                                # 通常の部屋は15%の確率で秘密のドア
                                door = (
                                    SecretDoor() if random.random() < 0.15 else Door()
                                )
                            self.tiles[y, x1] = door
                            # どの部屋の壁かを特定してドアリストに追加
                            if room:
                                room.doors.append((x1, y))
                        else:
                            self.tiles[y, x1] = Floor()
                            self.corridors.add((x1, y))
        else:  # 横線
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= x < self.width and 0 <= y1 < self.height:
                    current_tile = self.tiles[y1, x]
                    if isinstance(current_tile, Wall):
                        # 部屋の壁を貫通している場合はドア、通路はFloor
                        if self._is_room_wall(x, y1):
                            room = self._find_room_at_wall(x, y1)
                            if room and room.is_special:
                                # 特別な部屋は必ず通常のドア
                                door = Door()
                            else:
                                # 通常の部屋は15%の確率で秘密のドア
                                door = (
                                    SecretDoor() if random.random() < 0.15 else Door()
                                )
                            self.tiles[y1, x] = door
                            # どの部屋の壁かを特定してドアリストに追加
                            if room:
                                room.doors.append((x, y1))
                        else:
                            self.tiles[y1, x] = Floor()
                            self.corridors.add((x, y1))

    def _is_room_wall(self, x: int, y: int) -> bool:
        """指定位置が部屋の壁かどうかを判定"""
        for room in self.rooms:
            # 部屋の境界上かどうかをチェック
            is_on_boundary = (
                (x == room.x or x == room.x + room.width - 1)
                and room.y <= y <= room.y + room.height - 1
            ) or (
                (y == room.y or y == room.y + room.height - 1)
                and room.x <= x <= room.x + room.width - 1
            )
            if is_on_boundary:
                return True
        return False

    def _find_room_at_wall(self, x: int, y: int) -> Room | None:
        """指定位置の壁がどの部屋のものかを特定"""
        for room in self.rooms:
            # 部屋の境界上かどうかをチェック
            is_on_boundary = (
                (x == room.x or x == room.x + room.width - 1)
                and room.y <= y <= room.y + room.height - 1
            ) or (
                (y == room.y or y == room.y + room.height - 1)
                and room.x <= x <= room.x + room.width - 1
            )
            if is_on_boundary:
                return room
        return None

    def _place_doors(self) -> None:
        """ドアを配置（通路生成時に自動配置されるため不要）"""
        # ドアは通路生成時に自動的に配置される

    def _find_corridor_connections(self, room: Room) -> list[tuple[int, int]]:
        """部屋と通路の接続点を見つける"""
        connections = []

        # 部屋の境界をチェック
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                # 部屋の境界（壁）かどうかをチェック
                is_wall_position = (
                    (
                        x == room.x
                        or x == room.x + room.width - 1
                        or y == room.y
                        or y == room.y + room.height - 1
                    )
                    and not (x == room.x and y == room.y)  # 角は除外
                    and not (x == room.x and y == room.y + room.height - 1)
                    and not (x == room.x + room.width - 1 and y == room.y)
                    and not (
                        x == room.x + room.width - 1 and y == room.y + room.height - 1
                    )
                )

                if is_wall_position and isinstance(self.tiles[y, x], Wall):
                    # この壁の位置が通路と直接接続しているかチェック
                    if self._is_corridor_connection_point(room, x, y):
                        connections.append((x, y))

        return connections

    def _is_corridor_connection_point(self, room: Room, x: int, y: int) -> bool:
        """指定位置が通路との接続点かどうかを判定"""
        # 隣接する4方向をチェック
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                # 部屋の外側で通路がある場合
                is_outside_room = (
                    nx < room.x
                    or nx >= room.x + room.width
                    or ny < room.y
                    or ny >= room.y + room.height
                )

                if is_outside_room and isinstance(self.tiles[ny, nx], Floor):
                    # さらにその隣が通路の続きか、もう一つの部屋への入口かチェック
                    if self._leads_to_corridor_or_room(nx, ny, room):
                        return True

        return False

    def _leads_to_corridor_or_room(self, x: int, y: int, origin_room: Room) -> bool:
        """指定位置から通路または他の部屋につながっているかチェック"""
        # 隣接する位置をチェック
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if isinstance(self.tiles[ny, nx], Floor):
                    # 他の部屋の内部かチェック
                    for room in self.rooms:
                        if room != origin_room:
                            if (
                                room.x < nx < room.x + room.width - 1
                                and room.y < ny < room.y + room.height - 1
                            ):
                                return True

                    # 通路システムの一部かチェック
                    if (nx, ny) in self.corridors:
                        return True

        return False

    def _is_door_position(self, room: Room, x: int, y: int) -> bool:
        """指定された位置がドアの配置位置かどうかを判定（後方互換性）"""
        return self._is_corridor_connection_point(room, x, y)

    def _can_create_corridor(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> bool:
        """通路を作成できるかどうかを判定"""
        x1, y1 = start
        x2, y2 = end

        # 境界チェック
        if x1 < 2 or x1 >= self.width - 2 or y1 < 2 or y1 >= self.height - 2:
            return False
        if x2 < 2 or x2 >= self.width - 2 or y2 < 2 or y2 >= self.height - 2:
            return False

        return True

    def _create_corridor(self, room1: Room, room2: Room) -> None:
        """2つの部屋を接続する通路を生成（シンプルで確実な方法）"""
        # 既に接続されている部屋ペアかチェック
        pair_key = (min(room1.id, room2.id), max(room1.id, room2.id))
        if pair_key in self.connected_pairs:
            return

        # 部屋の中心から最も近い壁の点を見つける
        start_point = self._find_connection_point(room1, room2)
        end_point = self._find_connection_point(room2, room1)

        if start_point and end_point:
            # シンプルなL字型通路を生成
            self._create_simple_corridor(start_point, end_point, room1, room2)
            self.connected_pairs.add(pair_key)

    def _find_connection_point(
        self, from_room: Room, to_room: Room
    ) -> tuple[int, int] | None:
        """部屋から別の部屋への最適な接続点を見つける"""
        from_center = from_room.center
        to_center = to_room.center

        # 方向を決定
        dx = to_center[0] - from_center[0]
        dy = to_center[1] - from_center[1]

        # 境界チェック付きで接続点を決定
        if abs(dx) > abs(dy):
            # 水平方向が主
            if dx > 0:  # 右方向
                # Y座標を部屋の範囲内に制限
                y = max(
                    from_room.y + 1,
                    min(from_room.y + from_room.height - 2, from_center[1]),
                )
                return (from_room.x + from_room.width - 1, y)
            # 左方向
            y = max(
                from_room.y + 1, min(from_room.y + from_room.height - 2, from_center[1])
            )
            return (from_room.x, y)
        # 垂直方向が主
        if dy > 0:  # 下方向
            # X座標を部屋の範囲内に制限
            x = max(
                from_room.x + 1, min(from_room.x + from_room.width - 2, from_center[0])
            )
            return (x, from_room.y + from_room.height - 1)
        # 上方向
        x = max(from_room.x + 1, min(from_room.x + from_room.width - 2, from_center[0]))
        return (x, from_room.y)

    def _create_simple_corridor(
        self, start: tuple[int, int], end: tuple[int, int], room1: Room, room2: Room
    ) -> None:
        """シンプルなL字型通路を生成"""
        x1, y1 = start
        x2, y2 = end

        # L字型通路を生成（重複チェック付き）
        if random.random() < 0.5:
            # 水平→垂直
            self._create_safe_line(x1, y1, x2, y1)  # 水平線
            self._create_safe_line(x2, y1, x2, y2)  # 垂直線
            # 中間点にドアを配置
            if random.random() < 0.1:  # 10%の確率で中間にドアを配置
                self._place_door_safe((x2, y1), room1)
        else:
            # 垂直→水平
            self._create_safe_line(x1, y1, x1, y2)  # 垂直線
            self._create_safe_line(x1, y2, x2, y2)  # 水平線
            # 中間点にドアを配置
            if random.random() < 0.1:  # 10%の確率で中間にドアを配置
                self._place_door_safe((x1, y2), room1)

        # 部屋の壁にドアを配置
        self._place_door_safe(start, room1)
        self._place_door_safe(end, room2)

    def _create_safe_line(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """安全な1マス幅の線を生成（改良版：部屋外の既存通路で停止）"""
        if x1 == x2:  # 垂直線
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= x1 < self.width and 0 <= y < self.height:
                    current_tile = self.tiles[y, x1]

                    # 既存の通路（部屋外の床）に当たったら停止
                    if (x1, y) in self.corridors:
                        break

                    # 壁の場合は床に変更
                    if isinstance(current_tile, Wall):
                        self.tiles[y, x1] = Floor()
                        self.corridors.add((x1, y))
                    # ドアがある場合はそのまま保持し、通路として記録
                    elif isinstance(current_tile, (Door, SecretDoor)) or isinstance(
                        current_tile, Floor
                    ):
                        self.corridors.add((x1, y))
        else:  # 水平線
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= x < self.width and 0 <= y1 < self.height:
                    current_tile = self.tiles[y1, x]

                    # 既存の通路（部屋外の床）に当たったら停止
                    if (x, y1) in self.corridors:
                        break

                    # 壁の場合は床に変更
                    if isinstance(current_tile, Wall):
                        self.tiles[y1, x] = Floor()
                        self.corridors.add((x, y1))
                    # ドアがある場合はそのまま保持し、通路として記録
                    elif isinstance(current_tile, (Door, SecretDoor)) or isinstance(
                        current_tile, Floor
                    ):
                        self.corridors.add((x, y1))

    def _place_door_safe(self, position: tuple[int, int], room: Room) -> None:
        """安全にドアを配置"""
        x, y = position
        if (
            0 <= x < self.width
            and 0 <= y < self.height
            and self._is_on_room_wall(room, x, y)
            and not isinstance(self.tiles[y, x], Door)
            and not isinstance(self.tiles[y, x], SecretDoor)
        ):
            door = (
                Door()
                if room.is_special
                else (SecretDoor() if random.random() < 0.2 else Door())
            )
            self.tiles[y, x] = door
            room.doors.append((x, y))

    def _is_on_room_wall(self, room: Room, x: int, y: int) -> bool:
        """指定された座標が部屋の壁の上にあるかどうかをチェック"""
        return (
            (x == room.x or x == room.x + room.width - 1)
            and room.y <= y <= room.y + room.height - 1
        ) or (
            (y == room.y or y == room.y + room.height - 1)
            and room.x <= x <= room.x + room.width - 1
        )

    def _create_h_tunnel(self, x1: int, x2: int, y: int) -> None:
        """水平方向の通路を生成（廃止予定 - 新しいロジックでは使用しない）"""
        # この関数は後方互換性のために残しているが、新しいロジックでは使用しない

    def _create_v_tunnel(self, y1: int, y2: int, x: int) -> None:
        """垂直方向の通路を生成（廃止予定 - 新しいロジックでは使用しない）"""
        # この関数は後方互換性のために残しているが、新しいロジックでは使用しない

    def _place_stairs(self) -> None:
        """階段を配置"""
        if not self.rooms:
            return

        # 上り階段を配置（1階の場合は配置しない - GameScreenで制御）
        up_room = random.choice(self.rooms)
        up_x = random.randint(up_room.x + 1, up_room.x + up_room.width - 2)
        up_y = random.randint(up_room.y + 1, up_room.y + up_room.height - 2)

        if self.floor > 1:
            self.tiles[up_y, up_x] = StairsUp()

        self.start_pos = (up_x, up_y)

        # 下り階段を配置（上り階段とは別の部屋に）
        down_rooms = [room for room in self.rooms if room != up_room]
        if down_rooms:
            down_room = random.choice(down_rooms)
        else:
            down_room = up_room  # 部屋が1つしかない場合は同じ部屋に配置

        down_x = random.randint(down_room.x + 1, down_room.x + down_room.width - 2)
        down_y = random.randint(down_room.y + 1, down_room.y + down_room.height - 2)
        self.tiles[down_y, down_x] = StairsDown()
        self.end_pos = (down_x, down_y)

    def generate(self) -> tuple[np.ndarray, tuple[int, int], tuple[int, int]]:
        """ダンジョンを生成（オリジナルRogue式）"""
        # 3x3グリッドに部屋を生成
        self._create_rooms_in_grid()

        # 部屋を接続（オリジナルRogue式）
        self.room_connector.connect_rooms_rogue_style()
        
        # 階段を配置
        self.stairs_manager.place_stairs()

        # ドアを配置
        self._place_doors()

        # start_posとend_posがNoneの場合のデフォルト値を設定
        if self.start_pos is None:
            self.start_pos = (1, 1)
        if self.end_pos is None:
            self.end_pos = (self.width - 2, self.height - 2)

        return self.tiles, self.start_pos, self.end_pos
