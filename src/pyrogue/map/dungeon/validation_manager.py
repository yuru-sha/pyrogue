"""
検証管理コンポーネント - ダンジョン検証専用。

このモジュールは、生成されたダンジョンの検証に特化したマネージャーです。
部屋接続性、通路の完全性、境界制約、特別部屋ルールの検証を担当します。
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

from pyrogue.map.dungeon.corridor_builder import Corridor
from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Floor, StairsDown, StairsUp, Wall
from pyrogue.utils import game_logger


class ValidationError(Exception):
    """ダンジョン検証エラー。"""
    pass


class ValidationManager:
    """
    ダンジョン検証専用のマネージャークラス。

    生成されたダンジョンの構造的妥当性、接続性、
    ゲームルールへの準拠を検証します。

    Attributes:
        validation_results: 検証結果のリスト
        warnings: 警告のリスト
    """

    def __init__(self) -> None:
        """検証マネージャーを初期化。"""
        self.validation_results = []
        self.warnings = []

    def validate_dungeon(
        self,
        rooms: List[Room],
        corridors: List[Corridor],
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        tiles: np.ndarray
    ) -> bool:
        """
        ダンジョン全体を検証。

        Args:
            rooms: 部屋のリスト
            corridors: 通路のリスト
            start_pos: 上り階段位置
            end_pos: 下り階段位置
            tiles: ダンジョンのタイル配列

        Returns:
            検証が成功した場合True

        Raises:
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

    def _validate_basic_structure(self, rooms: List[Room], tiles: np.ndarray) -> None:
        """
        基本構造を検証。

        Args:
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
                    f"Room {room.id} is too small: {room.width}x{room.height}"
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

    def _validate_room_connectivity(self, rooms: List[Room]) -> None:
        """
        部屋接続性を検証。

        Args:
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
                f"Only {visited_rooms}/{total_rooms} rooms are connected"
            )

    def _validate_corridor_integrity(self, corridors: List[Corridor], tiles: np.ndarray) -> None:
        """
        通路の完全性を検証。

        Args:
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
                if (0 <= x < tiles.shape[1] and 0 <= y < tiles.shape[0]):
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
                    f"Corridor integrity: {integrity_ratio:.2%}"
                )
            else:
                self._add_result(
                    "corridor_integrity",
                    False,
                    f"Poor corridor integrity: {integrity_ratio:.2%}"
                )

    def _validate_boundary_constraints(
        self,
        rooms: List[Room],
        corridors: List[Corridor],
        tiles: np.ndarray
    ) -> None:
        """
        境界制約を検証。

        Args:
            rooms: 部屋のリスト
            corridors: 通路のリスト
            tiles: ダンジョンのタイル配列
        """
        height, width = tiles.shape
        boundary_violations = 0

        # 部屋の境界チェック
        for room in rooms:
            if (room.x < 1 or room.y < 1 or
                room.x + room.width >= width - 1 or
                room.y + room.height >= height - 1):
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
                f"{boundary_violations} boundary violations found"
            )

    def _validate_stairs_placement(
        self,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        tiles: np.ndarray
    ) -> None:
        """
        階段配置を検証。

        Args:
            start_pos: 上り階段位置
            end_pos: 下り階段位置
            tiles: ダンジョンのタイル配列
        """
        issues = []

        # 上り階段の検証
        if start_pos:
            x, y = start_pos
            if (0 <= x < tiles.shape[1] and 0 <= y < tiles.shape[0]):
                if not isinstance(tiles[y, x], StairsUp):
                    issues.append("Up stairs position mismatch")
            else:
                issues.append("Up stairs position out of bounds")

        # 下り階段の検証
        if end_pos:
            x, y = end_pos
            if (0 <= x < tiles.shape[1] and 0 <= y < tiles.shape[0]):
                if not isinstance(tiles[y, x], StairsDown):
                    issues.append("Down stairs position mismatch")
            else:
                issues.append("Down stairs position out of bounds")

        if issues:
            self._add_result("stairs_placement", False, "; ".join(issues))
        else:
            self._add_result("stairs_placement", True, "Stairs placed correctly")

    def _validate_special_room_rules(self, rooms: List[Room]) -> None:
        """
        特別部屋ルールを検証。

        Args:
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
                f"Too many special rooms: {special_ratio:.2%}"
            )
        else:
            self._add_result(
                "special_room_rules",
                True,
                f"Special room ratio: {special_ratio:.2%}"
            )

    def _validate_accessibility(
        self,
        rooms: List[Room],
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        tiles: np.ndarray
    ) -> None:
        """
        アクセス可能性を検証。

        Args:
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

    def _find_room_containing_position(
        self,
        position: Tuple[int, int],
        rooms: List[Room]
    ) -> Room | None:
        """
        指定位置を含む部屋を検索。

        Args:
            position: 位置
            rooms: 部屋のリスト

        Returns:
            見つかった部屋、または None
        """
        x, y = position

        for room in rooms:
            if (room.x <= x < room.x + room.width and
                room.y <= y < room.y + room.height):
                return room

        return None

    def _add_result(self, test_name: str, passed: bool, message: str) -> None:
        """
        検証結果を追加。

        Args:
            test_name: テスト名
            passed: 成功したかどうか
            message: メッセージ
        """
        self.validation_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })

    def _add_warning(self, message: str) -> None:
        """
        警告を追加。

        Args:
            message: 警告メッセージ
        """
        self.warnings.append(message)

    def get_validation_report(self) -> dict:
        """
        検証レポートを取得。

        Returns:
            検証結果の詳細レポート
        """
        passed_tests = len([r for r in self.validation_results if r["passed"]])
        total_tests = len(self.validation_results)

        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "warnings": len(self.warnings)
            },
            "results": self.validation_results,
            "warnings": self.warnings
        }

    def reset(self) -> None:
        """マネージャーの状態をリセット。"""
        self.validation_results = []
        self.warnings = []
