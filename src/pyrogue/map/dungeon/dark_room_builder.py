"""
暗い部屋生成システム。

照明なしでは視界が効かない特殊な部屋を生成する。
プレイヤーは光源アイテム（たいまつ、光る指輪など）を使用する必要がある。
"""

from __future__ import annotations

import random

import numpy as np

from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Floor
from pyrogue.utils import game_logger


class DarkRoom(Room):
    """
    暗い部屋を表すクラス。

    通常の部屋と異なり、照明なしでは視界が効かない。
    """

    def __init__(self, x: int, y: int, width: int, height: int, darkness_level: float = 1.0) -> None:
        """
        暗い部屋を初期化。

        Args:
        ----
            x: X座標
            y: Y座標
            width: 幅
            height: 高さ
            darkness_level: 暗さレベル（0.0-1.0）。1.0は完全な暗闇

        """
        super().__init__(x, y, width, height)
        self.is_dark = True
        self.darkness_level = darkness_level
        self.requires_light = True
        self.room_type = "dark"

        # 暗い部屋の視界範囲（光源なしの場合）
        self.base_visibility_range = max(1, int(3 * (1.0 - darkness_level)))

        game_logger.debug(f"DarkRoom created at ({x}, {y}): {width}x{height}, darkness={darkness_level}")


class DarkRoomBuilder:
    """
    暗い部屋生成ビルダー。

    照明なしでは視界が効かない特殊な部屋を生成する。
    通常の部屋を暗い部屋に変換する機能も提供。
    """

    def __init__(self, darkness_intensity: float = 0.8) -> None:
        """
        暗い部屋ビルダーを初期化。

        Args:
        ----
            darkness_intensity: 暗さの強度（0.0-1.0）。高いほど暗い

        """
        self.darkness_intensity = darkness_intensity
        self.dark_rooms: list[DarkRoom] = []
        self.light_sources: list[tuple[int, int]] = []  # 光源の位置

        game_logger.info(f"DarkRoomBuilder initialized: darkness_intensity={darkness_intensity}")

    def apply_darkness_to_rooms(self, rooms: list[Room], darkness_probability: float = 0.3) -> list[DarkRoom]:
        """
        既存の部屋を暗い部屋に変換。

        Args:
        ----
            rooms: 変換対象の部屋リスト
            darkness_probability: 暗い部屋になる確率

        Returns:
        -------
            生成された暗い部屋のリスト

        """
        self.dark_rooms = []

        for room in rooms:
            # 特別な部屋や重要な部屋は暗くしない
            if room.is_special and room.room_type in ["amulet_chamber", "treasure"]:
                continue

            # 確率に基づいて暗い部屋に変換
            if random.random() < darkness_probability:
                dark_room = self._convert_to_dark_room(room)
                self.dark_rooms.append(dark_room)

        game_logger.info(f"Converted {len(self.dark_rooms)} rooms to dark rooms")
        return self.dark_rooms

    def _convert_to_dark_room(self, room: Room) -> DarkRoom:
        """
        通常の部屋を暗い部屋に変換。

        Args:
        ----
            room: 変換対象の部屋

        Returns:
        -------
            変換された暗い部屋

        """
        # 暗さレベルを決定（強度に基づいて変動）
        darkness_level = max(0.5, self.darkness_intensity + random.uniform(-0.2, 0.2))
        darkness_level = min(1.0, darkness_level)

        # 暗い部屋を作成
        dark_room = DarkRoom(room.x, room.y, room.width, room.height, darkness_level)

        # 元の部屋の属性を継承
        dark_room.id = room.id
        dark_room.connected_rooms = room.connected_rooms.copy()
        dark_room.doors = room.doors.copy()
        dark_room.is_special = room.is_special

        # 暗い部屋特有の属性を設定
        if room.room_type and room.room_type != "dark":
            dark_room.room_type = f"dark_{room.room_type}"

        return dark_room

    def place_light_sources(
        self,
        dark_rooms: list[DarkRoom],
        tiles: np.ndarray,
        light_source_probability: float = 0.4,
    ) -> None:
        """
        暗い部屋に光源を配置。

        Args:
        ----
            dark_rooms: 暗い部屋のリスト
            tiles: ダンジョンのタイル配列
            light_source_probability: 光源配置確率

        """
        self.light_sources = []

        for dark_room in dark_rooms:
            # 光源を配置するかどうかを決定
            if random.random() < light_source_probability:
                light_pos = self._find_light_source_position(dark_room, tiles)
                if light_pos:
                    self._place_light_source(light_pos, tiles)
                    self.light_sources.append(light_pos)

        game_logger.info(f"Placed {len(self.light_sources)} light sources")

    def _find_light_source_position(self, dark_room: DarkRoom, tiles: np.ndarray) -> tuple[int, int] | None:
        """
        光源の配置位置を見つける。

        Args:
        ----
            dark_room: 暗い部屋
            tiles: ダンジョンのタイル配列

        Returns:
        -------
            光源の位置、または None

        """
        # 部屋の内部から候補位置を選択
        candidates = []

        for y in range(dark_room.y + 1, dark_room.y + dark_room.height - 1):
            for x in range(dark_room.x + 1, dark_room.x + dark_room.width - 1):
                if 0 <= y < tiles.shape[0] and 0 <= x < tiles.shape[1] and isinstance(tiles[y, x], Floor):
                    # 階段タイルでないことを確認
                    from pyrogue.map.tile import StairsDown, StairsUp

                    if not isinstance(tiles[y, x], (StairsUp, StairsDown)):
                        candidates.append((x, y))

        if not candidates:
            return None

        # 部屋の中央付近を優先
        center_x, center_y = dark_room.center()
        candidates.sort(key=lambda pos: abs(pos[0] - center_x) + abs(pos[1] - center_y))

        # 上位候補からランダムに選択
        top_candidates = candidates[: min(3, len(candidates))]
        return random.choice(top_candidates)

    def _place_light_source(self, position: tuple[int, int], tiles: np.ndarray) -> None:
        """
        光源を配置。

        Args:
        ----
            position: 光源の位置
            tiles: ダンジョンのタイル配列

        """
        x, y = position

        # 既存の床タイルに光源属性を追加
        if isinstance(tiles[y, x], Floor):
            tiles[y, x].has_light_source = True
            tiles[y, x].light_radius = 3  # 光源の照射範囲
            game_logger.debug(f"Placed light source at ({x}, {y})")

    def get_darkness_level_at(self, x: int, y: int, rooms: list[Room]) -> float:
        """
        指定位置の暗さレベルを取得。

        Args:
        ----
            x: X座標
            y: Y座標
            rooms: 部屋のリスト

        Returns:
        -------
            暗さレベル（0.0-1.0）。0.0は明るい、1.0は完全な暗闇

        """
        for room in rooms:
            if isinstance(room, DarkRoom):
                if room.x <= x < room.x + room.width and room.y <= y < room.y + room.height:
                    return room.darkness_level

        return 0.0  # 通常の部屋は明るい

    def is_position_in_dark_room(self, x: int, y: int, rooms: list[Room]) -> bool:
        """
        指定位置が暗い部屋内かどうかを判定。

        Args:
        ----
            x: X座標
            y: Y座標
            rooms: 部屋のリスト

        Returns:
        -------
            暗い部屋内の場合True

        """
        for room in rooms:
            if isinstance(room, DarkRoom):
                if room.x <= x < room.x + room.width and room.y <= y < room.y + room.height:
                    return True

        return False

    def get_visibility_range_at(
        self,
        x: int,
        y: int,
        rooms: list[Room],
        player_has_light: bool = False,
        light_radius: int = 5,
    ) -> int:
        """
        指定位置での視界範囲を取得。

        Args:
        ----
            x: X座標
            y: Y座標
            rooms: 部屋のリスト
            player_has_light: プレイヤーが光源を持っているか
            light_radius: 光源の照射範囲

        Returns:
        -------
            視界範囲（セル数）

        """
        # 暗い部屋内かチェック
        for room in rooms:
            if isinstance(room, DarkRoom):
                if room.x <= x < room.x + room.width and room.y <= y < room.y + room.height:
                    if player_has_light:
                        # 光源を持っている場合は通常の視界範囲
                        return light_radius
                    # 光源なしの場合は制限された視界範囲
                    return room.base_visibility_range

        # 通常の部屋では標準的な視界範囲
        return 8  # デフォルトのFOV範囲

    def find_nearest_light_source(self, x: int, y: int, max_distance: int = 10) -> tuple[int, int] | None:
        """
        最も近い光源を見つける。

        Args:
        ----
            x: X座標
            y: Y座標
            max_distance: 最大探索距離

        Returns:
        -------
            最も近い光源の位置、または None

        """
        if not self.light_sources:
            return None

        min_distance = float("inf")
        nearest_light = None

        for light_x, light_y in self.light_sources:
            distance = abs(x - light_x) + abs(y - light_y)  # マンハッタン距離
            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                nearest_light = (light_x, light_y)

        return nearest_light

    def get_light_influence_at(self, x: int, y: int, light_sources: list[tuple[int, int]] | None = None) -> float:
        """
        指定位置での光の影響度を取得。

        Args:
        ----
            x: X座標
            y: Y座標
            light_sources: 光源のリスト（Noneの場合は内部リストを使用）

        Returns:
        -------
            光の影響度（0.0-1.0）。1.0は完全に照明されている

        """
        if light_sources is None:
            light_sources = self.light_sources

        max_influence = 0.0

        for light_x, light_y in light_sources:
            distance = ((x - light_x) ** 2 + (y - light_y) ** 2) ** 0.5

            # 光の影響は距離に反比例（最大3セル）
            if distance <= 3:
                influence = max(0.0, 1.0 - distance / 3.0)
                max_influence = max(max_influence, influence)

        return min(1.0, max_influence)

    def reset(self) -> None:
        """ビルダーの状態をリセット。"""
        self.dark_rooms = []
        self.light_sources = []

    def get_statistics(self) -> dict:
        """生成統計を取得。"""
        return {
            "builder_type": "DarkRooms",
            "darkness_intensity": self.darkness_intensity,
            "dark_rooms_count": len(self.dark_rooms),
            "light_sources_count": len(self.light_sources),
            "average_darkness_level": sum(room.darkness_level for room in self.dark_rooms) / len(self.dark_rooms)
            if self.dark_rooms
            else 0.0,
        }
