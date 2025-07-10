"""
ダンジョンディレクター - Builder Patternのディレクター。

このモジュールは、ダンジョン生成の全体的なプロセスを管理し、
各ビルダーコンポーネントを適切な順序で実行します。
"""

from __future__ import annotations

import numpy as np

from pyrogue.map.dungeon.corridor_builder import CorridorBuilder
from pyrogue.map.dungeon.door_manager import DoorManager
from pyrogue.map.dungeon.room_builder import RoomBuilder
from pyrogue.map.dungeon.section_based_builder import BSPDungeonBuilder
from pyrogue.map.dungeon.special_room_builder import SpecialRoomBuilder
from pyrogue.map.dungeon.stairs_manager import StairsManager
from pyrogue.map.dungeon.validation_manager import ValidationManager
from pyrogue.map.tile import Floor, Wall
from pyrogue.utils import game_logger


class DungeonDirector:
    """
    ダンジョン生成のディレクタークラス。

    Builder Patternのディレクターとして、各ビルダーコンポーネントを
    適切な順序で実行し、統合されたダンジョンを構築します。

    Attributes:
        width: ダンジョンの幅
        height: ダンジョンの高さ
        floor: 現在の階層
        tiles: ダンジョンのタイル配列
        rooms: 生成された部屋のリスト
        corridors: 生成された通路のリスト

    """

    def __init__(self, width: int, height: int, floor: int) -> None:
        """
        ダンジョンディレクターを初期化。

        Args:
            width: ダンジョンの幅
            height: ダンジョンの高さ
            floor: 階層番号

        """
        self.width = width
        self.height = height
        self.floor = floor

        # タイル配列を初期化（全て壁で開始）
        self.tiles = np.full((height, width), Wall(), dtype=object)
        self.rooms = []
        self.corridors = []

        # Builder components
        self.room_builder = RoomBuilder(width, height, floor)
        self.bsp_builder = BSPDungeonBuilder(width, height, min_section_size=8)
        self.corridor_builder = CorridorBuilder(width, height)
        self.door_manager = DoorManager()
        self.special_room_builder = SpecialRoomBuilder(floor)
        self.stairs_manager = StairsManager()
        self.validation_manager = ValidationManager()

        # フラグ: セクションベースシステムを使用するか
        # 新しいダンジョン生成システムを使用したい場合は True に設定
        self.use_section_based = True

        game_logger.debug(f"DungeonDirector initialized for floor {floor} ({width}x{height})")

    def build_dungeon(self) -> tuple[np.ndarray, tuple[int, int], tuple[int, int]]:
        """
        ダンジョンを構築。

        Returns:
            (tiles, start_pos, end_pos) のタプル

        """
        game_logger.info(f"Starting dungeon generation for floor {self.floor}")

        try:
            if self.use_section_based:
                # BSPベースシステムを使用
                # 1. BSPで部屋と通路を生成
                self.rooms = self.bsp_builder.build_dungeon(self.tiles)
                game_logger.debug(f"Generated {len(self.rooms)} rooms using BSP system")

                # 2. 特別部屋の処理
                self.special_room_builder.process_special_rooms(self.rooms)

                # 3. ドアの配置
                self.door_manager.place_doors(self.rooms, [], self.tiles)

                # 4. 階段の配置
                start_pos, end_pos = self.stairs_manager.place_stairs(
                    self.rooms, self.floor, self.tiles
                )

                # 5. 最終検証
                self.validation_manager.validate_dungeon(
                    self.rooms, [], start_pos, end_pos, self.tiles
                )
            else:
                # 従来のシステムを使用
                # 1. 基本部屋構造の生成
                self.rooms = self.room_builder.create_room_grid()
                game_logger.debug(f"Generated {len(self.rooms)} rooms")

                # 2. 特別部屋の処理
                self.special_room_builder.process_special_rooms(self.rooms)

                # 3. 部屋をタイル配列に配置
                self._place_rooms_on_tiles()

                # 4. 通路の生成
                self.corridors = self.corridor_builder.connect_rooms_rogue_style(
                    self.rooms, self.tiles
                )
                game_logger.debug(f"Generated {len(self.corridors)} corridor segments")

                # 5. ドアの配置
                self.door_manager.place_doors(self.rooms, self.corridors, self.tiles)

                # 6. 階段の配置
                start_pos, end_pos = self.stairs_manager.place_stairs(
                    self.rooms, self.floor, self.tiles
                )

                # 7. 最終検証
                self.validation_manager.validate_dungeon(
                    self.rooms, self.corridors, start_pos, end_pos, self.tiles
                )

            game_logger.info(f"Dungeon generation completed for floor {self.floor}")
            return self.tiles, start_pos, end_pos

        except Exception as e:
            game_logger.error(f"Dungeon generation failed for floor {self.floor}: {e}")
            raise

    def _place_rooms_on_tiles(self) -> None:
        """
        生成された部屋をタイル配列に配置。
        """
        for room in self.rooms:
            # 部屋の内部を床に設定
            for y in range(room.y + 1, room.y + room.height - 1):
                for x in range(room.x + 1, room.x + room.width - 1):
                    if 0 <= y < self.height and 0 <= x < self.width:
                        self.tiles[y, x] = Floor()

            # 部屋の境界は壁のまま（既に初期化済み）

    def _reinforce_room_boundaries(self) -> None:
        """
        部屋の境界を再強化し、通路以外の境界が確実に壁になるようにする。
        """
        from pyrogue.map.tile import Floor, Wall

        for room in self.rooms:
            # 部屋の境界座標を取得
            for x in range(room.x, room.x + room.width):
                for y in range(room.y, room.y + room.height):
                    # 境界（外周）かつ内部でない位置
                    if ((x == room.x or x == room.x + room.width - 1 or
                         y == room.y or y == room.y + room.height - 1) and
                        (x, y) not in room.inner):

                        # 現在のタイルが床の場合のみ壁に変更
                        # （ドアや階段は保護）
                        if isinstance(self.tiles[y, x], Floor):
                            # この床が通路かチェック
                            is_corridor = False
                            for corridor in self.corridors:
                                if (x, y) in corridor.points:
                                    is_corridor = True
                                    break

                            # 通路でない床は壁に戻す
                            if not is_corridor:
                                self.tiles[y, x] = Wall()

        game_logger.debug("Reinforced room boundaries")

    def get_generation_statistics(self) -> dict:
        """
        ダンジョン生成の統計情報を取得。

        Returns:
            生成統計の辞書

        """
        total_floor_tiles = sum(
            1 for y in range(self.height) for x in range(self.width)
            if isinstance(self.tiles[y, x], Floor)
        )

        total_wall_tiles = sum(
            1 for y in range(self.height) for x in range(self.width)
            if isinstance(self.tiles[y, x], Wall)
        )

        return {
            "floor": self.floor,
            "dimensions": f"{self.width}x{self.height}",
            "rooms_count": len(self.rooms),
            "corridors_count": len(self.corridors),
            "floor_tiles": total_floor_tiles,
            "wall_tiles": total_wall_tiles,
            "floor_coverage": f"{(total_floor_tiles / (self.width * self.height)) * 100:.1f}%"
        }

    def set_custom_builders(
        self,
        room_builder: RoomBuilder = None,
        corridor_builder: CorridorBuilder = None,
        door_manager: DoorManager = None,
        special_room_builder: SpecialRoomBuilder = None,
        stairs_manager: StairsManager = None,
        validation_manager: ValidationManager = None,
    ) -> None:
        """
        カスタムビルダーコンポーネントを設定。

        Args:
            各ビルダーコンポーネント（Noneの場合はデフォルトを使用）

        """
        if room_builder:
            self.room_builder = room_builder
        if corridor_builder:
            self.corridor_builder = corridor_builder
        if door_manager:
            self.door_manager = door_manager
        if special_room_builder:
            self.special_room_builder = special_room_builder
        if stairs_manager:
            self.stairs_manager = stairs_manager
        if validation_manager:
            self.validation_manager = validation_manager

    def reset(self) -> None:
        """
        ディレクターの状態をリセット。
        """
        self.tiles = np.full((self.height, self.width), Wall(), dtype=object)
        self.rooms = []
        self.corridors = []

        # 各ビルダーコンポーネントもリセット
        for builder in [
            self.room_builder,
            self.corridor_builder,
            self.door_manager,
            self.special_room_builder,
            self.stairs_manager,
            self.validation_manager,
        ]:
            if hasattr(builder, "reset"):
                builder.reset()
