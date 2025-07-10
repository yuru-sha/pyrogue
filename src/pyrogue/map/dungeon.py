"""
ダンジョン生成モジュール - Builder Patternファサード。

このモジュールは、Builder Patternで実装されたダンジョン生成システムへの
ファサードを提供し、既存コードとの後方互換性を保ちます。

Example:
    >>> generator = DungeonGenerator(width=80, height=50, floor=1)
    >>> tiles, start_pos, end_pos = generator.generate()

"""

from __future__ import annotations

import numpy as np

from pyrogue.map.dungeon.director import DungeonDirector
from pyrogue.map.dungeon.room_builder import Room
from pyrogue.utils import game_logger


class DungeonGenerator:
    """
    ダンジョン生成クラス - Builder Patternのファサード。

    既存のAPIを維持しながら、新しいBuilder Patternベースの
    ダンジョン生成システムを使用します。

    Attributes:
        width: ダンジョンの幅
        height: ダンジョンの高さ
        floor: 階層番号
        director: Builder Patternのディレクター
        rooms: 生成された部屋のリスト
        tiles: 生成されたタイル配列

    """

    def __init__(self, width: int, height: int, floor: int = 1) -> None:
        """
        ダンジョンジェネレーターを初期化。

        Args:
            width: ダンジョンの幅
            height: ダンジョンの高さ
            floor: 階層番号

        """
        self.width = width
        self.height = height
        self.floor = floor

        # Builder Patternのディレクターを作成
        self.director = DungeonDirector(width, height, floor)

        # 生成結果の保存用
        self.rooms = []
        self.tiles = None
        self.start_pos = None
        self.end_pos = None

        game_logger.debug(f"DungeonGenerator initialized for floor {floor} ({width}x{height})")

    def generate(self) -> tuple[np.ndarray, tuple[int, int], tuple[int, int]]:
        """
        ダンジョンを生成。

        Returns:
            (tiles, start_pos, end_pos) のタプル

        """
        try:
            # Builder Patternでダンジョンを構築
            self.tiles, self.start_pos, self.end_pos = self.director.build_dungeon()

            # 部屋情報を取得
            self.rooms = self.director.rooms

            game_logger.info(f"Dungeon generation completed for floor {self.floor}")

            return self.tiles, self.start_pos, self.end_pos

        except Exception as e:
            game_logger.error(f"Dungeon generation failed: {e}")
            raise

    def get_generation_statistics(self) -> dict:
        """
        ダンジョン生成の統計情報を取得。

        Returns:
            生成統計の辞書

        """
        return self.director.get_generation_statistics()

    def get_validation_report(self) -> dict:
        """
        ダンジョン検証レポートを取得。

        Returns:
            検証レポートの辞書

        """
        return self.director.validation_manager.get_validation_report()

    def reset(self) -> None:
        """
        ジェネレーターの状態をリセット。
        """
        self.director.reset()
        self.rooms = []
        self.tiles = None
        self.start_pos = None
        self.end_pos = None

    # 後方互換性のためのプロパティ
    @property
    def corridors(self) -> list:
        """通路のリスト（後方互換性のため）。"""
        return getattr(self.director.corridor_builder, "corridors", [])

    # 後方互換性のためのメソッド
    def _get_room_grid_position(self, room: Room) -> tuple[int, int]:
        """部屋のグリッド位置を取得（後方互換性のため）。"""
        return self.director.room_builder.get_room_grid_position(room)

    def _find_room_at_grid(self, grid_x: int, grid_y: int) -> Room | None:
        """グリッド位置の部屋を検索（後方互換性のため）。"""
        return self.director.room_builder.find_room_at_grid(self.rooms, grid_x, grid_y)

    def _can_create_corridor(self, start: tuple, end: tuple) -> bool:
        """通路作成可能性をチェック（後方互換性のため）。"""
        # 簡単な距離チェック
        distance = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
        return distance > 0 and distance < max(self.width, self.height)

    def get_debug_info(self) -> dict:
        """
        デバッグ情報を取得。

        Returns:
            デバッグ情報の辞書

        """
        info = {
            "dungeon_info": {
                "width": self.width,
                "height": self.height,
                "floor": self.floor,
                "rooms_count": len(self.rooms),
            },
            "generation_stats": self.get_generation_statistics(),
        }

        # 各ビルダーコンポーネントの統計情報
        if hasattr(self.director.room_builder, "get_statistics"):
            info["room_builder_stats"] = self.director.room_builder.get_statistics()

        if hasattr(self.director.corridor_builder, "get_statistics"):
            info["corridor_builder_stats"] = self.director.corridor_builder.get_statistics()

        if hasattr(self.director.door_manager, "get_statistics"):
            info["door_manager_stats"] = self.director.door_manager.get_statistics()

        if hasattr(self.director.special_room_builder, "get_statistics"):
            info["special_room_builder_stats"] = self.director.special_room_builder.get_statistics()

        if hasattr(self.director.stairs_manager, "get_statistics"):
            info["stairs_manager_stats"] = self.director.stairs_manager.get_statistics()

        return info


# 後方互換性のためのクラスエイリアス
# 新しいRoomクラスを既存コードで使用できるようにする

# モジュールレベルでのエクスポート
__all__ = [
    "DungeonGenerator",
    "Room",
]
