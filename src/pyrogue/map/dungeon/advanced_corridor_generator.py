"""
高度廊下生成システム。

このモジュールは、BSPダンジョンでの廊下生成を改善し、
より自然で戦略的な通路レイアウトを実現します。
"""

from __future__ import annotations

import math
import random
from typing import Any

from pyrogue.map.dungeon.room_builder import Room
from pyrogue.utils import game_logger


class AdvancedCorridorGenerator:
    """
    高度廊下生成クラス。

    従来の単純なL字型接続から、より自然で戦略的な
    廊下パターンを生成します。
    """

    def __init__(self, width: int, height: int, floor: int = 1) -> None:
        """
        高度廊下生成器を初期化。

        Args:
        ----
            width: ダンジョンの幅
            height: ダンジョンの高さ
            floor: 階層番号（パターンに影響）

        """
        self.width = width
        self.height = height
        self.floor = floor
        self.corridors_created = 0

        # 階層に応じた廊下パターンの選択
        self.corridor_patterns = self._determine_corridor_patterns(floor)

        game_logger.debug(f"AdvancedCorridorGenerator initialized for floor {floor}")

    def generate_advanced_corridor(
        self,
        room1: Room,
        room2: Room,
        tiles: list[list[Any]],
        tile_placer: callable,
        boundary_door_placer: callable | None = None,
    ) -> list[tuple[int, int]]:
        """
        高度な廊下パターンを生成。

        Args:
        ----
            room1: 開始部屋
            room2: 終了部屋
            tiles: タイル配列
            tile_placer: タイル配置関数
            boundary_door_placer: 境界ドア配置関数

        Returns:
        -------
            廊下の座標リスト

        """
        # 部屋の位置関係を分析
        relationship = self._analyze_room_relationship(room1, room2)

        # 適切な廊下パターンを選択
        pattern = self._select_corridor_pattern(relationship)

        # パターンに応じた廊下を生成
        if pattern == "direct":
            return self._generate_direct_corridor(room1, room2, tiles, tile_placer, boundary_door_placer)
        if pattern == "curved":
            return self._generate_curved_corridor(room1, room2, tiles, tile_placer, boundary_door_placer)
        if pattern == "zigzag":
            return self._generate_zigzag_corridor(room1, room2, tiles, tile_placer, boundary_door_placer)
        if pattern == "branch":
            return self._generate_branch_corridor(room1, room2, tiles, tile_placer, boundary_door_placer)
        if pattern == "scenic":
            return self._generate_scenic_corridor(room1, room2, tiles, tile_placer, boundary_door_placer)
        # デフォルト：標準L字型
        return self._generate_standard_l_corridor(room1, room2, tiles, tile_placer, boundary_door_placer)

    def _determine_corridor_patterns(self, floor: int) -> list[str]:
        """
        階層に応じた廊下パターンを決定。

        Args:
        ----
            floor: 階層番号

        Returns:
        -------
            利用可能なパターンのリスト

        """
        if floor <= 5:
            return ["direct", "standard_l"]  # 浅い階層：シンプル
        if floor <= 10:
            return ["direct", "standard_l", "curved"]  # 中間階層：少し複雑
        if floor <= 15:
            return ["standard_l", "curved", "zigzag"]  # 深い階層：複雑
        if floor <= 20:
            return ["curved", "zigzag", "branch"]  # 深層：高度なパターン
        return ["zigzag", "branch", "scenic"]  # 最深部：最も複雑

    def _analyze_room_relationship(self, room1: Room, room2: Room) -> dict[str, Any]:
        """
        2つの部屋の位置関係を分析。

        Args:
        ----
            room1: 部屋1
            room2: 部屋2

        Returns:
        -------
            位置関係の分析結果

        """
        center1 = room1.center()
        center2 = room2.center()

        dx = center2[0] - center1[0]
        dy = center2[1] - center1[1]

        distance = math.sqrt(dx * dx + dy * dy)

        # 角度を計算（0-360度）
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360

        # 部屋の重複をチェック
        overlap_x = self._check_overlap(room1.x, room1.x + room1.width, room2.x, room2.x + room2.width)
        overlap_y = self._check_overlap(room1.y, room1.y + room1.height, room2.y, room2.y + room2.height)

        return {
            "distance": distance,
            "dx": dx,
            "dy": dy,
            "angle": angle,
            "overlap_x": overlap_x,
            "overlap_y": overlap_y,
            "is_aligned_horizontal": abs(dy) < 3,
            "is_aligned_vertical": abs(dx) < 3,
            "is_diagonal": 30 < angle < 60 or 120 < angle < 150 or 210 < angle < 240 or 300 < angle < 330,
        }

    def _check_overlap(self, start1: int, end1: int, start2: int, end2: int) -> bool:
        """座標軸での重複をチェック。"""
        return not (end1 <= start2 or end2 <= start1)

    def _select_corridor_pattern(self, relationship: dict[str, Any]) -> str:
        """
        部屋の位置関係に応じて廊下パターンを選択。

        Args:
        ----
            relationship: 位置関係の分析結果

        Returns:
        -------
            選択された廊下パターン

        """
        # 距離が近い場合は直接接続
        if relationship["distance"] < 8:
            return "direct"

        # 水平・垂直に整列している場合
        if relationship["is_aligned_horizontal"] or relationship["is_aligned_vertical"]:
            return random.choice(["direct", "curved"])

        # 対角線上にある場合
        if relationship["is_diagonal"]:
            return random.choice(["zigzag", "branch"])

        # 距離が遠い場合は景観廊下
        if relationship["distance"] > 15:
            return "scenic"

        # デフォルト：利用可能なパターンからランダム選択
        return random.choice(self.corridor_patterns)

    def _generate_direct_corridor(
        self,
        room1: Room,
        room2: Room,
        tiles: list[list[Any]],
        tile_placer: callable,
        boundary_door_placer: callable | None,
    ) -> list[tuple[int, int]]:
        """
        直接接続廊下を生成。

        最短経路で部屋を接続します。
        """
        center1 = room1.center()
        center2 = room2.center()

        points = []

        # Bresenhamライン アルゴリズムで直線を描画
        points.extend(self._bresenham_line(center1[0], center1[1], center2[0], center2[1]))

        # 廊下を実際に描画
        for x, y in points:
            if 0 <= x < self.width and 0 <= y < self.height:
                tile_placer(tiles, x, y, True)

        game_logger.debug(f"Generated direct corridor: {len(points)} points")
        self.corridors_created += 1

        return points

    def _generate_curved_corridor(
        self,
        room1: Room,
        room2: Room,
        tiles: list[list[Any]],
        tile_placer: callable,
        boundary_door_placer: callable | None,
    ) -> list[tuple[int, int]]:
        """
        曲線廊下を生成。

        滑らかな曲線で部屋を接続します。
        """
        center1 = room1.center()
        center2 = room2.center()

        # 制御点を計算（ベジェ曲線用）
        control_points = self._calculate_bezier_control_points(center1, center2)

        # ベジェ曲線で滑らかな廊下を生成
        points = self._generate_bezier_curve(control_points, steps=20)

        # 廊下を実際に描画
        for x, y in points:
            if 0 <= x < self.width and 0 <= y < self.height:
                tile_placer(tiles, x, y, True)

        game_logger.debug(f"Generated curved corridor: {len(points)} points")
        self.corridors_created += 1

        return points

    def _generate_zigzag_corridor(
        self,
        room1: Room,
        room2: Room,
        tiles: list[list[Any]],
        tile_placer: callable,
        boundary_door_placer: callable | None,
    ) -> list[tuple[int, int]]:
        """
        ジグザグ廊下を生成。

        複数の直角カーブで部屋を接続します。
        """
        center1 = room1.center()
        center2 = room2.center()

        # 中間ポイントを計算
        intermediate_points = self._calculate_zigzag_points(center1, center2)

        points = []

        # 各セグメントを直線で接続
        current_point = center1
        for next_point in intermediate_points + [center2]:
            segment_points = self._bresenham_line(current_point[0], current_point[1], next_point[0], next_point[1])
            points.extend(segment_points)
            current_point = next_point

        # 廊下を実際に描画
        for x, y in points:
            if 0 <= x < self.width and 0 <= y < self.height:
                tile_placer(tiles, x, y, True)

        game_logger.debug(f"Generated zigzag corridor: {len(points)} points")
        self.corridors_created += 1

        return points

    def _generate_branch_corridor(
        self,
        room1: Room,
        room2: Room,
        tiles: list[list[Any]],
        tile_placer: callable,
        boundary_door_placer: callable | None,
    ) -> list[tuple[int, int]]:
        """
        分岐廊下を生成。

        メイン廊下から分岐する小さな廊下を含みます。
        """
        # メイン廊下を生成
        main_points = self._generate_standard_l_corridor(room1, room2, tiles, tile_placer, boundary_door_placer)

        # 分岐廊下を追加
        if len(main_points) > 6:
            # メイン廊下の中間点から分岐
            branch_start = main_points[len(main_points) // 2]
            branch_points = self._generate_branch_segments(branch_start, tiles, tile_placer)
            main_points.extend(branch_points)

        game_logger.debug(f"Generated branch corridor: {len(main_points)} points")
        self.corridors_created += 1

        return main_points

    def _generate_scenic_corridor(
        self,
        room1: Room,
        room2: Room,
        tiles: list[list[Any]],
        tile_placer: callable,
        boundary_door_placer: callable | None,
    ) -> list[tuple[int, int]]:
        """
        景観廊下を生成。

        迂回路を通る長い廊下で、探索の楽しさを提供します。
        """
        center1 = room1.center()
        center2 = room2.center()

        # 迂回ポイントを計算
        scenic_points = self._calculate_scenic_waypoints(center1, center2)

        points = []

        # 各ウェイポイントを曲線で接続
        current_point = center1
        for next_point in scenic_points + [center2]:
            # 曲線セグメントを生成
            control_points = self._calculate_bezier_control_points(current_point, next_point)
            segment_points = self._generate_bezier_curve(control_points, steps=15)
            points.extend(segment_points)
            current_point = next_point

        # 廊下を実際に描画
        for x, y in points:
            if 0 <= x < self.width and 0 <= y < self.height:
                tile_placer(tiles, x, y, True)

        game_logger.debug(f"Generated scenic corridor: {len(points)} points")
        self.corridors_created += 1

        return points

    def _generate_standard_l_corridor(
        self,
        room1: Room,
        room2: Room,
        tiles: list[list[Any]],
        tile_placer: callable,
        boundary_door_placer: callable | None,
    ) -> list[tuple[int, int]]:
        """
        標準L字型廊下を生成（既存の動作を維持）。
        """
        center1 = room1.center()
        center2 = room2.center()

        points = []

        # ランダムにL字の方向を決定
        horizontal_first = random.random() < 0.5

        if horizontal_first:
            # 水平→垂直
            # 水平セグメント
            for x in range(min(center1[0], center2[0]), max(center1[0], center2[0]) + 1):
                points.append((x, center1[1]))
                tile_placer(tiles, x, center1[1], True)

            # 垂直セグメント
            for y in range(min(center1[1], center2[1]), max(center1[1], center2[1]) + 1):
                points.append((center2[0], y))
                tile_placer(tiles, center2[0], y, True)
        else:
            # 垂直→水平
            # 垂直セグメント
            for y in range(min(center1[1], center2[1]), max(center1[1], center2[1]) + 1):
                points.append((center1[0], y))
                tile_placer(tiles, center1[0], y, True)

            # 水平セグメント
            for x in range(min(center1[0], center2[0]), max(center1[0], center2[0]) + 1):
                points.append((x, center2[1]))
                tile_placer(tiles, x, center2[1], True)

        game_logger.debug(f"Generated standard L corridor: {len(points)} points")
        self.corridors_created += 1

        return points

    def _bresenham_line(self, x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
        """Bresenham直線アルゴリズムで線を描画。"""
        points = []

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)

        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1

        err = dx - dy

        while True:
            points.append((x0, y0))

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err

            if e2 > -dy:
                err -= dy
                x0 += sx

            if e2 < dx:
                err += dx
                y0 += sy

        return points

    def _calculate_bezier_control_points(self, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        """ベジェ曲線の制御点を計算。"""
        start_x, start_y = start
        end_x, end_y = end

        # 中間点を計算
        mid_x = (start_x + end_x) // 2
        mid_y = (start_y + end_y) // 2

        # 制御点を計算（曲線を作るためにオフセット）
        offset = min(abs(end_x - start_x), abs(end_y - start_y)) // 4

        control1_x = mid_x + random.randint(-offset, offset)
        control1_y = mid_y + random.randint(-offset, offset)

        return [start, (control1_x, control1_y), end]

    def _generate_bezier_curve(self, control_points: list[tuple[int, int]], steps: int = 20) -> list[tuple[int, int]]:
        """ベジェ曲線を生成。"""
        points = []

        for i in range(steps + 1):
            t = i / steps

            # 2次ベジェ曲線
            if len(control_points) == 3:
                x = int(
                    (1 - t) ** 2 * control_points[0][0]
                    + 2 * (1 - t) * t * control_points[1][0]
                    + t**2 * control_points[2][0]
                )
                y = int(
                    (1 - t) ** 2 * control_points[0][1]
                    + 2 * (1 - t) * t * control_points[1][1]
                    + t**2 * control_points[2][1]
                )

                points.append((x, y))

        return points

    def _calculate_zigzag_points(self, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        """ジグザグ廊下の中間点を計算。"""
        start_x, start_y = start
        end_x, end_y = end

        points = []

        # 2-3個の中間点を作成
        num_points = random.randint(2, 3)

        for i in range(1, num_points + 1):
            # 基本的な補間
            t = i / (num_points + 1)
            base_x = int(start_x + (end_x - start_x) * t)
            base_y = int(start_y + (end_y - start_y) * t)

            # ジグザグ効果のためのオフセット
            offset = random.randint(-3, 3)

            if i % 2 == 1:
                # 奇数番目の点は X軸にオフセット
                points.append((base_x + offset, base_y))
            else:
                # 偶数番目の点は Y軸にオフセット
                points.append((base_x, base_y + offset))

        return points

    def _generate_branch_segments(
        self, branch_start: tuple[int, int], tiles: list[list[Any]], tile_placer: callable
    ) -> list[tuple[int, int]]:
        """分岐セグメントを生成。"""
        points = []

        # 分岐の方向をランダムに決定
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        branch_direction = random.choice(directions)

        # 分岐の長さ
        branch_length = random.randint(3, 6)

        for i in range(1, branch_length + 1):
            x = branch_start[0] + branch_direction[0] * i
            y = branch_start[1] + branch_direction[1] * i

            if 0 <= x < self.width and 0 <= y < self.height:
                points.append((x, y))
                tile_placer(tiles, x, y, True)

        return points

    def _calculate_scenic_waypoints(self, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        """景観廊下のウェイポイントを計算。"""
        start_x, start_y = start
        end_x, end_y = end

        # 中間点を計算
        mid_x = (start_x + end_x) // 2
        (start_y + end_y) // 2

        # 迂回ポイントを作成
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)

        waypoint1 = (mid_x + offset_x, start_y + offset_y)
        waypoint2 = (mid_x - offset_x, end_y - offset_y)

        return [waypoint1, waypoint2]

    def get_generation_statistics(self) -> dict[str, Any]:
        """
        生成統計情報を取得。

        Returns
        -------
            生成統計の辞書

        """
        return {
            "corridors_created": self.corridors_created,
            "available_patterns": self.corridor_patterns,
            "floor": self.floor,
            "dungeon_size": f"{self.width}x{self.height}",
            "pattern_complexity": len(self.corridor_patterns),
        }
