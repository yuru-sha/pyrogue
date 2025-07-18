"""
通路ビルダー - 通路生成専用コンポーネント。

このモジュールは、部屋間を接続する通路の生成に特化したビルダーです。
オリジナルRogue式の接続アルゴリズム、直線通路、安全な線描画を担当します。
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np

from pyrogue.map.dungeon.constants import CorridorConstants
from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Floor
from pyrogue.utils import game_logger


@dataclass
class Corridor:
    """
    通路を表すデータクラス。
    """

    start_pos: tuple[int, int]
    end_pos: tuple[int, int]
    points: list[tuple[int, int]]
    connecting_rooms: tuple[int, int] | None = None  # 接続する部屋のID

    def __post_init__(self):
        if not self.points:
            self.points = []


class CorridorBuilder:
    """
    通路生成専用のビルダークラス。

    部屋間を接続する通路の生成、オリジナルRogue式の接続アルゴリズム、
    直線通路の作成、安全な線描画を担当します。

    Attributes
    ----------
        width: ダンジョンの幅
        height: ダンジョンの高さ
        corridors: 生成された通路のリスト

    """

    def __init__(self, width: int, height: int) -> None:
        """
        通路ビルダーを初期化。

        Args:
        ----
            width: ダンジョンの幅
            height: ダンジョンの高さ

        """
        self.width = width
        self.height = height
        self.corridors: list[Corridor] = []

    def connect_rooms_rogue_style(self, rooms: list[Room], tiles: np.ndarray) -> list[Corridor]:
        """
        オリジナルRogue式の部屋接続アルゴリズム。

        Args:
        ----
            rooms: 接続する部屋のリスト
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            生成された通路のリスト

        """
        self.corridors = []

        if len(rooms) < 2:
            return self.corridors

        # 最小スパニングツリー方式で全ての部屋を接続
        connected_rooms = set()

        # 最初の部屋から開始
        if rooms:
            connected_rooms.add(rooms[0].id)

        # 全ての部屋が接続されるまで継続
        while len(connected_rooms) < len(rooms):
            # 接続済み部屋から最も近い未接続部屋を見つける
            best_distance = float("inf")
            best_pair = None

            for connected_room in rooms:
                if connected_room.id not in connected_rooms:
                    continue

                for unconnected_room in rooms:
                    if unconnected_room.id in connected_rooms:
                        continue

                    distance = self._calculate_distance(connected_room.center(), unconnected_room.center())
                    if distance < best_distance:
                        best_distance = distance
                        best_pair = (connected_room, unconnected_room)

            # 最適なペアを接続
            if best_pair:
                room1, room2 = best_pair
                corridor = self._create_corridor_between_rooms(room1, room2, tiles)
                if corridor:
                    self.corridors.append(corridor)
                    room1.add_connection(room2)
                    connected_rooms.add(room2.id)

        # 追加の接続を作成（ランダムに）
        self._create_additional_connections(rooms, tiles)

        game_logger.info(f"Created {len(self.corridors)} corridors connecting {len(rooms)} rooms")
        return self.corridors

    def _calculate_distance(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> float:
        """
        2点間の距離を計算。

        Args:
        ----
            pos1: 点1の座標
            pos2: 点2の座標

        Returns:
        -------
            ユークリッド距離

        """
        return ((pos2[0] - pos1[0]) ** 2 + (pos2[1] - pos1[1]) ** 2) ** 0.5

    def _create_corridor_between_rooms(self, room1: Room, room2: Room, tiles: np.ndarray) -> Corridor | None:
        """
        2つの部屋を接続する通路を作成。

        Args:
        ----
            room1: 部屋1
            room2: 部屋2
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            作成された通路、または None

        """
        # 接続点を決定
        start_point = self._find_connection_point(room1, room2)
        end_point = self._find_connection_point(room2, room1)

        if not start_point or not end_point:
            return None

        # 直線通路を作成
        corridor_points = self._create_straight_corridor(start_point, end_point, tiles)

        if corridor_points:
            corridor = Corridor(
                start_pos=start_point,
                end_pos=end_point,
                points=corridor_points,
                connecting_rooms=(room1.id, room2.id),
            )
            return corridor

        return None

    def _find_connection_point(self, from_room: Room, to_room: Room) -> tuple[int, int] | None:
        """
        部屋の壁上で最適な接続点を見つける。

        Args:
        ----
            from_room: 接続元の部屋
            to_room: 接続先の部屋

        Returns:
        -------
            接続点の座標、または None

        """
        to_center = to_room.center()

        # 部屋の4つの壁から最も近い点を選択
        walls = [
            # 北壁
            (from_room.x + from_room.width // 2, from_room.y),
            # 南壁
            (from_room.x + from_room.width // 2, from_room.y + from_room.height - 1),
            # 西壁
            (from_room.x, from_room.y + from_room.height // 2),
            # 東壁
            (from_room.x + from_room.width - 1, from_room.y + from_room.height // 2),
        ]

        closest_point = None
        min_distance = float("inf")

        for wall_point in walls:
            distance = self._calculate_distance(wall_point, to_center)
            if distance < min_distance:
                min_distance = distance
                closest_point = wall_point

        return closest_point

    def _create_straight_corridor(
        self, start: tuple[int, int], end: tuple[int, int], tiles: np.ndarray
    ) -> list[tuple[int, int]]:
        """
        直線通路を作成（Bresenhamアルゴリズムで直線接続）。

        Args:
        ----
            start: 開始点
            end: 終了点
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            通路の座標点のリスト

        """
        corridor_points = []

        # 直線で接続する（Bresenhamアルゴリズム的な直線）
        x1, y1 = start
        x2, y2 = end

        # 水平距離と垂直距離を計算
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        # 方向を決定
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1

        # 誤差項
        err = dx - dy

        # 現在位置
        x, y = x1, y1

        # 直線を描画
        while True:
            corridor_points.append((x, y))

            # 終点に到達したら終了
            if x == x2 and y == y2:
                break

            # 次の点を計算
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

        # 重複を除去
        corridor_points = list(dict.fromkeys(corridor_points))

        # タイルに通路を配置
        actual_corridor_points = []
        for x, y in corridor_points:
            if self._is_valid_corridor_position(x, y, tiles):
                # 通路座標を床タイルに変更
                tiles[y, x] = Floor()
                actual_corridor_points.append((x, y))

        return actual_corridor_points

    def _is_valid_corridor_position(self, x: int, y: int, tiles: np.ndarray) -> bool:
        """
        通路配置位置が有効かチェック。

        Args:
        ----
            x: X座標
            y: Y座標
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            有効な位置の場合True

        """
        # 境界チェック
        if x < 1 or y < 1 or x >= self.width - 1 or y >= self.height - 1:
            return False

        return True

    def _create_additional_connections(self, rooms: list[Room], tiles: np.ndarray) -> None:
        """
        追加の接続を作成（ランダムに）。

        Args:
        ----
            rooms: 部屋のリスト
            tiles: ダンジョンのタイル配列

        """
        # 定数で定義された確率で追加接続を作成
        if (
            random.random() < CorridorConstants.ADDITIONAL_CONNECTION_CHANCE
            and len(rooms) >= CorridorConstants.MIN_ROOMS_FOR_ADDITIONAL
        ):
            room1 = random.choice(rooms)
            room2 = random.choice([r for r in rooms if r.id != room1.id])

            if not room1.is_connected_to(room2):
                corridor = self._create_corridor_between_rooms(room1, room2, tiles)
                if corridor:
                    self.corridors.append(corridor)
                    room1.add_connection(room2)

    def get_corridor_at_position(self, x: int, y: int) -> Corridor | None:
        """
        指定位置の通路を取得。

        Args:
        ----
            x: X座標
            y: Y座標

        Returns:
        -------
            見つかった通路、または None

        """
        for corridor in self.corridors:
            if (x, y) in corridor.points:
                return corridor
        return None

    def reset(self) -> None:
        """ビルダーの状態をリセット。"""
        self.corridors = []

    def get_statistics(self) -> dict:
        """通路生成の統計情報を取得。"""
        total_length = sum(len(corridor.points) for corridor in self.corridors)

        return {
            "corridors_count": len(self.corridors),
            "total_length": total_length,
            "average_length": total_length / len(self.corridors) if self.corridors else 0,
        }
