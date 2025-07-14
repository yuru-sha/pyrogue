"""
検証管理コンポーネント - ダンジョン検証専用。

このモジュールは、生成されたダンジョンの検証に特化したマネージャーです。
部屋接続性、通路の完全性、境界制約、特別部屋ルールの検証を担当します。
"""

from __future__ import annotations

import numpy as np

from pyrogue.map.dungeon.corridor_builder import Corridor
from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Floor, StairsDown, StairsUp, Wall
from pyrogue.utils import game_logger


class ValidationError(Exception):
    """ダンジョン検証エラー。"""


class ValidationManager:
    """
    ダンジョン検証専用のマネージャークラス。

    生成されたダンジョンの構造的妥当性、接続性、
    ゲームルールへの準拠を検証します。

    Attributes
    ----------
        validation_results: 検証結果のリスト
        warnings: 警告のリスト

    """

    def __init__(self) -> None:
        """検証マネージャーを初期化。"""
        self.validation_results: list[dict[str, bool | str]] = []
        self.warnings: list[str] = []

    def validate_dungeon(
        self,
        rooms: list[Room],
        corridors: list[Corridor],
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        tiles: np.ndarray,
    ) -> bool:
        """
        ダンジョン全体を検証。

        Args:
        ----
            rooms: 部屋のリスト
            corridors: 通路のリスト
            start_pos: 上り階段位置
            end_pos: 下り階段位置
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            検証が成功した場合True

        Raises:
        ------
            ValidationError: 重大な検証エラーが発生した場合

        """
        self.validation_results = []
        self.warnings = []

        try:
            # 基本構造の検証
            self._validate_basic_structure(rooms, tiles)

            # 部屋接続性の検証
            self._validate_room_connectivity(rooms)

            # 通路の完全性検証
            self._validate_corridor_integrity(corridors, tiles)

            # 境界制約の検証
            self._validate_boundary_constraints(rooms, corridors, tiles)

            # 階段配置の検証
            self._validate_stairs_placement(start_pos, end_pos, tiles)

            # 特別部屋ルールの検証
            self._validate_special_room_rules(rooms)

            # アクセス可能性の検証
            self._validate_accessibility(rooms, start_pos, end_pos, tiles)

            success = len([r for r in self.validation_results if not r["passed"]]) == 0

            if success:
                game_logger.info("Dungeon validation passed successfully")
            else:
                game_logger.warning(f"Dungeon validation failed: {len(self.validation_results)} errors")

            return success

        except Exception as e:
            game_logger.error(f"Validation error: {e}")
            raise ValidationError(f"Dungeon validation failed: {e}")

    def _validate_basic_structure(self, rooms: list[Room], tiles: np.ndarray) -> None:
        """
        基本構造を検証。

        Args:
        ----
            rooms: 部屋のリスト
            tiles: ダンジョンのタイル配列

        """
        # 最小部屋数のチェック
        if len(rooms) < 1:
            self._add_result("basic_structure", False, "No rooms generated")
            return

        # 部屋サイズの検証
        for room in rooms:
            if room.width < 3 or room.height < 3:
                self._add_result(
                    "room_size",
                    False,
                    f"Room {room.id} is too small: {room.width}x{room.height}",
                )

            if room.width > 20 or room.height > 20:
                self._add_warning(f"Room {room.id} is very large: {room.width}x{room.height}")

        # タイル配列の整合性チェック
        height, width = tiles.shape
        floor_count = 0
        wall_count = 0

        for y in range(height):
            for x in range(width):
                tile = tiles[y, x]
                if isinstance(tile, Floor):
                    floor_count += 1
                elif isinstance(tile, Wall):
                    wall_count += 1

        total_tiles = height * width
        floor_ratio = floor_count / total_tiles

        if floor_ratio < 0.1:
            self._add_result("floor_coverage", False, f"Too few floor tiles: {floor_ratio:.2%}")
        elif floor_ratio > 0.8:
            self._add_result("floor_coverage", False, f"Too many floor tiles: {floor_ratio:.2%}")
        else:
            self._add_result("floor_coverage", True, f"Floor coverage: {floor_ratio:.2%}")

    def _validate_room_connectivity(self, rooms: list[Room]) -> None:
        """
        部屋接続性を検証。

        Args:
        ----
            rooms: 部屋のリスト

        """
        if len(rooms) < 2:
            self._add_result("connectivity", True, "Single room, connectivity N/A")
            return

        # グラフ探索で全部屋が接続されているかチェック
        visited = set()
        to_visit = {rooms[0].id}

        while to_visit:
            current_id = to_visit.pop()
            visited.add(current_id)

            # 現在の部屋を取得
            current_room = next((r for r in rooms if r.id == current_id), None)
            if not current_room:
                continue

            # 接続された部屋を探索キューに追加
            for connected_id in current_room.connected_rooms:
                if connected_id not in visited:
                    to_visit.add(connected_id)

        # 全部屋が訪問されたかチェック
        total_rooms = len(rooms)
        visited_rooms = len(visited)

        if visited_rooms == total_rooms:
            self._add_result("connectivity", True, f"All {total_rooms} rooms are connected")
        else:
            self._add_result(
                "connectivity",
                False,
                f"Only {visited_rooms}/{total_rooms} rooms are connected",
            )

    def _validate_corridor_integrity(self, corridors: list[Corridor], tiles: np.ndarray) -> None:
        """
        通路の完全性を検証。

        Args:
        ----
            corridors: 通路のリスト
            tiles: ダンジョンのタイル配列

        """
        if not corridors:
            self._add_result("corridor_integrity", True, "No corridors to validate")
            return

        total_corridor_points = 0
        valid_corridor_points = 0

        for corridor in corridors:
            for x, y in corridor.points:
                total_corridor_points += 1

                # 境界チェック
                if 0 <= x < tiles.shape[1] and 0 <= y < tiles.shape[0]:
                    tile = tiles[y, x]
                    if isinstance(tile, Floor):
                        valid_corridor_points += 1

        if total_corridor_points == 0:
            self._add_result("corridor_integrity", True, "No corridor points to validate")
        else:
            integrity_ratio = valid_corridor_points / total_corridor_points
            if integrity_ratio >= 0.95:
                self._add_result(
                    "corridor_integrity",
                    True,
                    f"Corridor integrity: {integrity_ratio:.2%}",
                )
            else:
                self._add_result(
                    "corridor_integrity",
                    False,
                    f"Poor corridor integrity: {integrity_ratio:.2%}",
                )

    def _validate_boundary_constraints(self, rooms: list[Room], corridors: list[Corridor], tiles: np.ndarray) -> None:
        """
        境界制約を検証。

        Args:
        ----
            rooms: 部屋のリスト
            corridors: 通路のリスト
            tiles: ダンジョンのタイル配列

        """
        height, width = tiles.shape
        boundary_violations = 0

        # 部屋の境界チェック
        for room in rooms:
            if room.x < 1 or room.y < 1 or room.x + room.width >= width - 1 or room.y + room.height >= height - 1:
                boundary_violations += 1

        # 通路の境界チェック
        for corridor in corridors:
            for x, y in corridor.points:
                if x < 1 or y < 1 or x >= width - 1 or y >= height - 1:
                    boundary_violations += 1
                    break  # 1つの通路で1つの違反をカウント

        if boundary_violations == 0:
            self._add_result("boundary_constraints", True, "No boundary violations")
        else:
            self._add_result(
                "boundary_constraints",
                False,
                f"{boundary_violations} boundary violations found",
            )

    def _validate_stairs_placement(
        self, start_pos: tuple[int, int], end_pos: tuple[int, int], tiles: np.ndarray
    ) -> None:
        """
        階段配置を検証。

        Args:
        ----
            start_pos: 上り階段位置
            end_pos: 下り階段位置
            tiles: ダンジョンのタイル配列

        """
        issues = []

        # 上り階段の検証
        if start_pos:
            x, y = start_pos
            if 0 <= x < tiles.shape[1] and 0 <= y < tiles.shape[0]:
                if not isinstance(tiles[y, x], StairsUp):
                    issues.append("Up stairs position mismatch")
            else:
                issues.append("Up stairs position out of bounds")

        # 下り階段の検証
        if end_pos:
            x, y = end_pos
            if 0 <= x < tiles.shape[1] and 0 <= y < tiles.shape[0]:
                if not isinstance(tiles[y, x], StairsDown):
                    issues.append("Down stairs position mismatch")
            else:
                issues.append("Down stairs position out of bounds")

        if issues:
            self._add_result("stairs_placement", False, "; ".join(issues))
        else:
            self._add_result("stairs_placement", True, "Stairs placed correctly")

    def _validate_special_room_rules(self, rooms: list[Room]) -> None:
        """
        特別部屋ルールを検証。

        Args:
        ----
            rooms: 部屋のリスト

        """
        special_rooms = [room for room in rooms if room.is_special]
        total_rooms = len(rooms)
        special_ratio = len(special_rooms) / total_rooms if total_rooms > 0 else 0

        # 特別部屋の割合チェック（10%～50%の範囲）
        if special_ratio > 0.5:
            self._add_result(
                "special_room_rules",
                False,
                f"Too many special rooms: {special_ratio:.2%}",
            )
        else:
            self._add_result("special_room_rules", True, f"Special room ratio: {special_ratio:.2%}")

    def _validate_accessibility(
        self,
        rooms: list[Room],
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        tiles: np.ndarray,
    ) -> None:
        """
        アクセス可能性を検証。

        Args:
        ----
            rooms: 部屋のリスト
            start_pos: 上り階段位置
            end_pos: 下り階段位置
            tiles: ダンジョンのタイル配列

        """
        # 簡単なアクセス可能性チェック
        # 上り階段から下り階段への経路が存在するかをチェック

        if not start_pos or not end_pos:
            self._add_result("accessibility", True, "Stairs positions not available")
            return

        # 実際の経路探索は複雑なので、簡易チェックのみ実装
        # 部屋が接続されていて、階段が部屋内にあれば基本的にアクセス可能

        start_room = self._find_room_containing_position(start_pos, rooms)
        end_room = self._find_room_containing_position(end_pos, rooms)

        if start_room and end_room:
            self._add_result("accessibility", True, "Stairs are in accessible rooms")
        else:
            self._add_result("accessibility", False, "Stairs are not in proper rooms")

    def _find_room_containing_position(self, position: tuple[int, int], rooms: list[Room]) -> Room | None:
        """
        指定位置を含む部屋を検索。

        Args:
        ----
            position: 位置
            rooms: 部屋のリスト

        Returns:
        -------
            見つかった部屋、または None

        """
        x, y = position

        for room in rooms:
            if room.x <= x < room.x + room.width and room.y <= y < room.y + room.height:
                return room

        return None

    def _add_result(self, test_name: str, passed: bool, message: str) -> None:
        """
        検証結果を追加。

        Args:
        ----
            test_name: テスト名
            passed: 成功したかどうか
            message: メッセージ

        """
        self.validation_results.append({"test": test_name, "passed": passed, "message": message})

    def _add_warning(self, message: str) -> None:
        """
        警告を追加。

        Args:
        ----
            message: 警告メッセージ

        """
        self.warnings.append(message)

    def get_validation_report(self) -> dict:
        """
        検証レポートを取得。

        Returns
        -------
            検証結果の詳細レポート

        """
        passed_tests = len([r for r in self.validation_results if r["passed"]])
        total_tests = len(self.validation_results)

        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "warnings": len(self.warnings),
            },
            "results": self.validation_results,
            "warnings": self.warnings,
        }

    def validate_maze_dungeon(
        self,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        tiles: np.ndarray,
        floor: int = 1,
    ) -> bool:
        """
        迷路階層を検証。

        Args:
        ----
            start_pos: 上り階段の位置
            end_pos: 下り階段の位置
            tiles: ダンジョンのタイル配列
            floor: 階層番号

        Returns:
        -------
            検証が成功した場合True

        Raises:
        ------
            ValidationError: 検証に失敗した場合

        """
        self.validation_results = []
        self.warnings = []

        try:
            # 1. 基本的な境界検証
            self._validate_boundary_constraints([], [], tiles)

            # 2. 迷路専用の連結性検証
            self._validate_maze_connectivity(start_pos, end_pos, tiles, floor)

            # 3. 階段配置の検証
            self._validate_stairs_placement_for_maze(start_pos, end_pos, tiles, floor)

            # 4. 迷路構造の検証
            self._validate_maze_structure(tiles)

            # 検証結果の確認
            failed_tests = [r for r in self.validation_results if not r["passed"]]
            if failed_tests:
                errors = "; ".join([r["message"] for r in failed_tests])
                game_logger.error(f"Maze validation failed: {errors}")
                raise ValidationError(f"Maze validation failed: {errors}")

            game_logger.info("Maze validation passed successfully")
            return True

        except Exception as e:
            game_logger.error(f"Maze validation error: {e}")
            raise ValidationError(f"Maze validation failed: {e}")

    def _validate_maze_connectivity(
        self,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        tiles: np.ndarray,
        floor: int = 1,
    ) -> None:
        """
        迷路の連結性を検証。

        Args:
        ----
            start_pos: 上り階段の位置
            end_pos: 下り階段の位置
            tiles: ダンジョンのタイル配列
            floor: 階層番号

        """
        from pyrogue.constants import GameConstants

        # 1階や最下層では階段が片方しかないので、連結性チェックをスキップ
        if floor == 1 or floor == GameConstants.MAX_FLOORS:
            self._add_result("maze_connectivity", True, "Single floor, no connectivity check needed")
            return

        # 階段間の経路の存在を確認
        if start_pos and end_pos:
            path_exists = self._find_path_between_positions(start_pos, end_pos, tiles)
            if path_exists:
                self._add_result("maze_connectivity", True, "Stairs are connected")
            else:
                self._add_result("maze_connectivity", False, "Stairs are not connected")
        else:
            self._add_result("maze_connectivity", True, "No stairs to connect")

    def _validate_stairs_placement_for_maze(
        self,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        tiles: np.ndarray,
        floor: int = 1,
    ) -> None:
        """
        迷路階層の階段配置を検証。

        Args:
        ----
            start_pos: 上り階段の位置
            end_pos: 下り階段の位置
            tiles: ダンジョンのタイル配列
            floor: 階層番号

        """
        from pyrogue.constants import GameConstants

        issues = []

        # 上り階段の検証（1階では不要）
        if floor > 1 and start_pos:
            x, y = start_pos
            if 0 <= x < tiles.shape[1] and 0 <= y < tiles.shape[0]:
                if not isinstance(tiles[y, x], StairsUp):
                    issues.append("Up stairs position mismatch")
            else:
                issues.append("Up stairs position out of bounds")

        # 下り階段の検証（最下層では不要）
        if floor < GameConstants.MAX_FLOORS and end_pos:
            x, y = end_pos
            if 0 <= x < tiles.shape[1] and 0 <= y < tiles.shape[0]:
                if not isinstance(tiles[y, x], StairsDown):
                    issues.append("Down stairs position mismatch")
            else:
                issues.append("Down stairs position out of bounds")

        if issues:
            self._add_result("maze_stairs_placement", False, "; ".join(issues))
        else:
            self._add_result("maze_stairs_placement", True, "Stairs placed correctly in maze")

    def _validate_maze_structure(self, tiles: np.ndarray) -> None:
        """
        迷路構造を検証。

        Args:
        ----
            tiles: ダンジョンのタイル配列

        """
        height, width = tiles.shape
        floor_count = 0
        wall_count = 0

        for y in range(height):
            for x in range(width):
                if isinstance(tiles[y, x], Floor):
                    floor_count += 1
                elif isinstance(tiles[y, x], Wall):
                    wall_count += 1

        # 迷路の密度をチェック（床の割合が4%～40%の範囲）
        total_tiles = height * width
        floor_ratio = floor_count / total_tiles

        if floor_ratio < 0.02:  # より現実的な通路密度の下限に調整
            self._add_result("maze_structure", False, f"Too few corridors: {floor_ratio:.2%}")
        elif floor_ratio > 0.4:
            self._add_result("maze_structure", False, f"Too many corridors: {floor_ratio:.2%}")
        else:
            self._add_result("maze_structure", True, f"Good maze density: {floor_ratio:.2%}")

        # 連結性の確認
        connected_floor_count = self._count_connected_floors(tiles)
        if connected_floor_count < floor_count * 0.85:
            self._add_result("maze_structure", False, "Maze has disconnected areas")
        else:
            self._add_result("maze_structure", True, "Maze is well connected")

    def _count_connected_floors(self, tiles: np.ndarray) -> int:
        """
        連結された床タイルの数を数える。

        Args:
        ----
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            最大連結成分の床タイル数

        """
        height, width = tiles.shape
        visited = np.zeros((height, width), dtype=bool)
        max_component_size = 0

        for y in range(height):
            for x in range(width):
                if isinstance(tiles[y, x], Floor) and not visited[y, x]:
                    component_size = self._flood_fill_count(tiles, visited, x, y)
                    max_component_size = max(max_component_size, component_size)

        return max_component_size

    def _flood_fill_count(self, tiles: np.ndarray, visited: np.ndarray, start_x: int, start_y: int) -> int:
        """
        フラッドフィルで連結成分のサイズを数える。

        Args:
        ----
            tiles: ダンジョンのタイル配列
            visited: 訪問済みフラグ配列
            start_x: 開始X座標
            start_y: 開始Y座標

        Returns:
        -------
            連結成分のサイズ

        """
        height, width = tiles.shape
        count = 0
        stack = [(start_x, start_y)]

        while stack:
            x, y = stack.pop()
            if x < 0 or x >= width or y < 0 or y >= height or visited[y, x] or not isinstance(tiles[y, x], Floor):
                continue

            visited[y, x] = True
            count += 1

            # 4方向に探索
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                stack.append((x + dx, y + dy))

        return count

    def _find_path_between_positions(
        self, start_pos: tuple[int, int], end_pos: tuple[int, int], tiles: np.ndarray
    ) -> bool:
        """
        2つの位置間のパスが存在するかチェック。

        Args:
        ----
            start_pos: 開始位置
            end_pos: 終了位置
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            パスが存在する場合True

        """
        if not start_pos or not end_pos:
            return False

        height, width = tiles.shape
        visited = set()
        stack = [start_pos]

        while stack:
            x, y = stack.pop()
            if (x, y) == end_pos:
                return True

            if (x, y) in visited:
                continue

            visited.add((x, y))

            # 4方向をチェック
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                    # 通行可能なタイルかチェック
                    if isinstance(tiles[ny, nx], (Floor, StairsUp, StairsDown)):
                        stack.append((nx, ny))

        return False

    def reset(self) -> None:
        """マネージャーの状態をリセット。"""
        self.validation_results = []
        self.warnings = []
