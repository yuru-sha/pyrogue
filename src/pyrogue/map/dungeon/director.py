"""
ダンジョンディレクター - Builder Patternのディレクター。

このモジュールは、ダンジョン生成の全体的なプロセスを管理し、
各ビルダーコンポーネントを適切な順序で実行します。
"""

from __future__ import annotations

import numpy as np

from pyrogue.map.dungeon.corridor_builder import CorridorBuilder
from pyrogue.map.dungeon.dark_room_builder import DarkRoomBuilder
from pyrogue.map.dungeon.door_manager import DoorManager
from pyrogue.map.dungeon.enhanced_bsp_builder import EnhancedBSPBuilder
from pyrogue.map.dungeon.isolated_room_builder import IsolatedRoomBuilder
from pyrogue.map.dungeon.maze_builder import MazeBuilder
from pyrogue.map.dungeon.profiler import DungeonProfiler
from pyrogue.map.dungeon.room_builder import RoomBuilder
from pyrogue.map.dungeon.section_based_builder import BSPDungeonBuilder
from pyrogue.map.dungeon.special_room_builder import SpecialRoomBuilder
from pyrogue.map.dungeon.stairs_manager import StairsManager
from pyrogue.map.dungeon.validation_manager import ValidationManager
from pyrogue.map.tile import Floor, Wall
from pyrogue.utils import game_logger


# 型の前方宣言
class Room:
    """部屋クラス（前方宣言）。"""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.inner: list[tuple[int, int]] = []


class Corridor:
    """通路クラス（前方宣言）。"""

    def __init__(self):
        self.points: list[tuple[int, int]] = []


class DungeonDirector:
    """
    ダンジョン生成のディレクタークラス。

    Builder Patternのディレクターとして、各ビルダーコンポーネントを
    適切な順序で実行し、統合されたダンジョンを構築します。

    Attributes
    ----------
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
        ----
            width: ダンジョンの幅
            height: ダンジョンの高さ
            floor: 階層番号

        """
        self.width = width
        self.height = height
        self.floor = floor

        # タイル配列を初期化（全て壁で開始）
        self.tiles = np.full((height, width), Wall(), dtype=object)
        self.rooms: list[Room] = []
        self.corridors: list[Corridor] = []

        # Builder components
        self.room_builder = RoomBuilder(width, height, floor)
        self.bsp_builder = BSPDungeonBuilder(width, height, min_section_size=5)
        self.enhanced_bsp_builder = EnhancedBSPBuilder(width, height, floor, min_section_size=5)

        # 迷路階層の場合はより低い複雑度でより広い迷路を生成
        maze_complexity = 0.5 if self._determine_dungeon_type(floor) == "maze" else 0.75
        self.maze_builder = MazeBuilder(width, height, complexity=maze_complexity)

        self.isolated_room_builder = IsolatedRoomBuilder(width, height, isolation_level=0.8)
        self.dark_room_builder = DarkRoomBuilder(darkness_intensity=0.8)
        self.corridor_builder = CorridorBuilder(width, height)
        self.door_manager = DoorManager()
        self.special_room_builder = SpecialRoomBuilder(floor)
        self.stairs_manager = StairsManager()
        self.validation_manager = ValidationManager()

        # フラグ: セクションベースシステムを使用するか
        # 新しいダンジョン生成システムを使用したい場合は True に設定
        self.use_section_based = True

        # フラグ: 拡張BSPシステムを使用するか
        # BSPアルゴリズムの改善版を使用したい場合は True に設定
        # 一時的に無効化（テスト互換性のため）
        self.use_enhanced_bsp = False

        # ダンジョンタイプの決定
        self.dungeon_type = self._determine_dungeon_type(floor)

        # パフォーマンスプロファイラー
        self.profiler = DungeonProfiler()

        game_logger.debug(f"DungeonDirector initialized for floor {floor} ({width}x{height})")

    def build_dungeon(self) -> tuple[np.ndarray, tuple[int, int], tuple[int, int]]:
        """
        ダンジョンを構築。

        Returns
        -------
            (tiles, start_pos, end_pos) のタプル

        """
        game_logger.info(f"Starting dungeon generation for floor {self.floor}")

        # パフォーマンス計測開始
        self.profiler.start_profiling()

        try:
            if self.use_section_based:
                if self.dungeon_type == "maze":
                    # 迷路階層を生成（リトライ機能付き）
                    start_pos, end_pos = self._build_maze_dungeon_with_profiling()
                elif self.dungeon_type != "maze":  # 通常ダンジョンまたはフォールバック処理
                    # BSPベースシステムを使用
                    start_pos, end_pos = self._build_normal_dungeon_with_profiling()
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
                self.corridors = self.corridor_builder.connect_rooms_rogue_style(self.rooms, self.tiles)
                game_logger.debug(f"Generated {len(self.corridors)} corridor segments")

                # 5. ドアの配置
                self.door_manager.place_doors(self.rooms, self.corridors, self.tiles)

                # 6. 階段の配置
                start_pos, end_pos = self.stairs_manager.place_stairs(self.rooms, self.floor, self.tiles)

                # 7. 最終検証
                self.validation_manager.validate_dungeon(self.rooms, self.corridors, start_pos, end_pos, self.tiles)

            # パフォーマンス計測終了とレポート
            self.profiler.stop_profiling()
            self.profiler.record_stat("rooms_count", len(self.rooms))
            self.profiler.record_stat("corridors_count", len(self.corridors))
            self.profiler.record_stat("floor_type", self.dungeon_type)
            self.profiler.log_report()

            game_logger.info(f"Dungeon generation completed for floor {self.floor}")
            return self.tiles, start_pos, end_pos

        except Exception as e:
            self.profiler.stop_profiling()
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
                    if (
                        x == room.x or x == room.x + room.width - 1 or y == room.y or y == room.y + room.height - 1
                    ) and (x, y) not in room.inner:
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

    def _build_maze_dungeon_with_profiling(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """
        迷路ダンジョンを生成（パフォーマンス計測付き）。

        Returns
        -------
            (start_pos, end_pos) のタプル

        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.profiler.section("maze_generation"):
                    self.rooms = self.maze_builder.build_dungeon(self.tiles)
                    game_logger.debug("Generated maze dungeon (no rooms)")

                with self.profiler.section("maze_stairs_placement"):
                    start_pos, end_pos = self.stairs_manager.place_stairs_for_maze(self.floor, self.tiles)

                with self.profiler.section("maze_validation"):
                    self.validation_manager.validate_maze_dungeon(start_pos, end_pos, self.tiles, self.floor)

                return start_pos, end_pos

            except Exception as e:
                game_logger.warning(f"Maze generation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    game_logger.error("Maze generation failed after all retries, using fallback")
                    # フォールバック: BSPベースシステムを使用
                    self.dungeon_type = "normal"
                    return self._build_normal_dungeon_with_profiling()
                # タイルを再初期化してリトライ
                self.tiles = np.full((self.height, self.width), Wall(), dtype=object)
                game_logger.debug(f"Retrying maze generation (attempt {attempt + 2})")

        # このポイントに到達することはないはずだが、安全のため
        raise RuntimeError("Maze generation failed after all retries")

    def _build_normal_dungeon_with_profiling(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """
        通常ダンジョンを生成（パフォーマンス計測付き）。

        Returns
        -------
            (start_pos, end_pos) のタプル

        """
        with self.profiler.section("bsp_room_generation"):
            if self.use_enhanced_bsp:
                self.rooms = self.enhanced_bsp_builder.build_dungeon(self.tiles)
                game_logger.debug(f"Generated {len(self.rooms)} rooms using Enhanced BSP system")
            else:
                self.rooms = self.bsp_builder.build_dungeon(self.tiles)
                game_logger.debug(f"Generated {len(self.rooms)} rooms using BSP system")

        with self.profiler.section("special_room_processing"):
            self.special_room_builder.process_special_rooms(self.rooms)

        if self._should_generate_isolated_rooms():
            with self.profiler.section("isolated_room_generation"):
                isolated_groups = self.isolated_room_builder.generate_isolated_rooms(
                    self.tiles, self.rooms, max_groups=2
                )
                game_logger.debug(f"Generated {len(isolated_groups)} isolated room groups")

        with self.profiler.section("door_placement"):
            # 拡張BSPでは既にドアが配置されているため、従来のドア配置はスキップ
            if not self.use_enhanced_bsp:
                self.door_manager.place_doors(self.rooms, [], self.tiles)

        if self._should_generate_dark_rooms():
            with self.profiler.section("dark_room_generation"):
                dark_rooms = self.dark_room_builder.apply_darkness_to_rooms(self.rooms, darkness_probability=0.4)
                # 暗い部屋に光源を配置
                self.dark_room_builder.place_light_sources(dark_rooms, self.tiles)
                game_logger.debug(f"Generated {len(dark_rooms)} dark rooms")

        with self.profiler.section("stairs_placement"):
            start_pos, end_pos = self.stairs_manager.place_stairs(self.rooms, self.floor, self.tiles)

        with self.profiler.section("dungeon_validation"):
            self.validation_manager.validate_dungeon(self.rooms, [], start_pos, end_pos, self.tiles)

        return start_pos, end_pos

    def get_generation_statistics(self) -> dict:
        """
        ダンジョン生成の統計情報を取得。

        Returns
        -------
            生成統計の辞書

        """
        total_floor_tiles = sum(
            1 for y in range(self.height) for x in range(self.width) if isinstance(self.tiles[y, x], Floor)
        )

        total_wall_tiles = sum(
            1 for y in range(self.height) for x in range(self.width) if isinstance(self.tiles[y, x], Wall)
        )

        stats = {
            "floor": self.floor,
            "dimensions": f"{self.width}x{self.height}",
            "rooms_count": len(self.rooms),
            "corridors_count": len(self.corridors),
            "floor_tiles": total_floor_tiles,
            "wall_tiles": total_wall_tiles,
            "floor_coverage": f"{(total_floor_tiles / (self.width * self.height)) * 100:.1f}%",
        }

        # パフォーマンス情報を統合
        if hasattr(self, "profiler") and self.profiler.total_time > 0:
            stats["performance"] = self.profiler.get_report()

        return stats

    def set_custom_builders(
        self,
        room_builder: RoomBuilder | None = None,
        corridor_builder: CorridorBuilder | None = None,
        door_manager: DoorManager | None = None,
        special_room_builder: SpecialRoomBuilder | None = None,
        stairs_manager: StairsManager | None = None,
        validation_manager: ValidationManager | None = None,
    ) -> None:
        """
        カスタムビルダーコンポーネントを設定。

        Args:
        ----
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
            self.bsp_builder,
            self.maze_builder,
            self.isolated_room_builder,
            self.dark_room_builder,
            self.corridor_builder,
            self.door_manager,
            self.special_room_builder,
            self.stairs_manager,
            self.validation_manager,
        ]:
            if hasattr(builder, "reset"):
                builder.reset()

    def _determine_dungeon_type(self, floor: int) -> str:
        """
        階層に基づいてダンジョンタイプを決定。

        Args:
        ----
            floor: 階層番号

        Returns:
        -------
            ダンジョンタイプ文字列

        """
        from pyrogue.config.env import is_test_mode

        # テスト環境では一貫した結果を保証するため、ランダム性を制御
        if is_test_mode():
            # テスト中は特定の階層のみ迷路にして、その他はBSPにする
            if floor in [7, 13, 19]:
                return "maze"
            return "bsp"

        # 特定の階層は必ず迷路にする（例：7階、13階、19階）
        if floor in [7, 13, 19]:
            return "maze"

        # 指定階層以外はすべてBSPダンジョンを生成
        return "bsp"

    def _should_generate_isolated_rooms(self) -> bool:
        """
        孤立部屋群を生成すべきかどうかを決定。

        Returns
        -------
            孤立部屋群を生成する場合True

        """
        # 特定の階層で孤立部屋群を生成
        # 浅い階層では低確率、深い階層では高確率
        if self.floor <= 3:
            return False  # 浅い階層では生成しない
        if self.floor <= 10:
            return self.floor in [4, 8]  # 4階、8階で確実に生成
        if self.floor <= 20:
            return self.floor in [11, 15, 18]  # 11階、15階、18階で確実に生成
        return self.floor in [22, 25]  # 22階、25階で確実に生成

    def _should_generate_dark_rooms(self) -> bool:
        """
        暗い部屋を生成すべきかどうかを決定。

        Returns
        -------
            暗い部屋を生成する場合True

        """
        # 特定の階層で暗い部屋を生成
        # 深い階層ほど暗い部屋が多くなる
        if self.floor <= 5:
            return False  # 浅い階層では生成しない
        if self.floor <= 12:
            return self.floor in [6, 10]  # 6階、10階で確実に生成
        if self.floor <= 20:
            return self.floor in [14, 17, 20]  # 14階、17階、20階で確実に生成
        return self.floor in [23, 24]  # 深層では23階、24階で確実に生成
