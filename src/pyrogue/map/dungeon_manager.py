"""
ダンジョン管理モジュール。

このモジュールは、マルチフロアダンジョンの状態管理を担当します。
階層の生成、保存、読み込み、および現在の階層状態の管理を統合的に処理します。

主要機能:
    - 階層データの生成と保存
    - モンスターとアイテムのスポーン管理
    - 探索済み領域の追跡
    - 階段の位置管理
    - フロア間移動のサポート

Example:
-------
    >>> dungeon_manager = DungeonManager()
    >>> floor_data = dungeon_manager.get_floor(1)
    >>> dungeon_manager.set_current_floor(2)

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from pyrogue.entities.actors.monster_spawner import MonsterSpawner
    from pyrogue.entities.items.item_spawner import ItemSpawner

from pyrogue.entities.actors.monster_spawner import MonsterSpawner
from pyrogue.entities.items.item_spawner import ItemSpawner
from pyrogue.entities.traps.trap import TrapManager

# 新しいBuilder Patternベースのダンジョン生成システムを使用
from pyrogue.map.dungeon.director import DungeonDirector


class FloorData:
    """
    単一フロアのデータを表すクラス。

    各階層の状態（タイル、エンティティ、探索状況）を保持します。

    Attributes
    ----------
        tiles: ダンジョンタイルの2次元配列
        up_pos: 上り階段の位置 (x, y)
        down_pos: 下り階段の位置 (x, y)
        monster_spawner: モンスター管理インスタンス
        item_spawner: アイテム管理インスタンス
        trap_manager: トラップ管理インスタンス
        explored: 探索済み領域のブール配列
        floor_number: 階層番号

    """

    def __init__(
        self,
        floor_number: int,
        tiles: np.ndarray,
        up_pos: tuple[int, int],
        down_pos: tuple[int, int],
        monster_spawner: MonsterSpawner,
        item_spawner: ItemSpawner,
        trap_manager: TrapManager,
        explored: np.ndarray,
    ) -> None:
        """
        フロアデータを初期化。

        Args:
        ----
            floor_number: 階層番号
            tiles: ダンジョンタイルの2次元配列
            up_pos: 上り階段の位置
            down_pos: 下り階段の位置
            monster_spawner: モンスター管理インスタンス
            item_spawner: アイテム管理インスタンス
            trap_manager: トラップ管理インスタンス
            explored: 探索済み領域のブール配列

        """
        self.floor_number = floor_number
        self.tiles = tiles
        self.up_pos = up_pos
        self.down_pos = down_pos
        self.monster_spawner = monster_spawner
        self.item_spawner = item_spawner
        self.trap_manager = trap_manager
        self.explored = explored

        # 開始位置を設定
        if floor_number == 1:
            # 1階では階段から離れた安全な位置を動的に探す
            self.start_pos = self._find_safe_start_position_for_floor1(tiles, up_pos, down_pos)
        # 2階以降では上り階段の位置を使用
        elif up_pos is not None:
            self.start_pos = up_pos
        elif down_pos is not None:
            self.start_pos = down_pos
        else:
            # フォールバック：適切な位置
            self.start_pos = (1, 1)  # 最小限の安全な位置

    def is_valid_position(self, x: int, y: int) -> bool:
        """
        指定された位置が有効な範囲内かチェック。

        Args:
        ----
            x: X座標
            y: Y座標

        Returns:
        -------
            有効な座標の場合True

        """
        return 0 <= x < self.tiles.shape[1] and 0 <= y < self.tiles.shape[0]

    def get_tile(self, x: int, y: int):
        """
        指定位置のタイルを取得。

        Args:
        ----
            x: X座標
            y: Y座標

        Returns:
        -------
            タイルインスタンス、無効な座標の場合None

        """
        if self.is_valid_position(x, y):
            return self.tiles[y, x]
        return None

    def set_tile_walkable(self, x: int, y: int, walkable: bool) -> None:
        """
        指定位置のタイルの通行可能性を設定。

        Args:
        ----
            x: X座標
            y: Y座標
            walkable: 通行可能かどうか

        """
        if self.is_valid_position(x, y):
            tile = self.tiles[y, x]
            if hasattr(tile, "walkable"):
                tile.walkable = walkable

    def set_tile(self, x: int, y: int, tile_type: str) -> None:
        """
        指定位置のタイルを設定。

        Args:
        ----
            x: X座標
            y: Y座標
            tile_type: タイルタイプ

        """
        if self.is_valid_position(x, y):
            # タイルタイプに応じたタイルインスタンスを作成
            from pyrogue.map.tile import Door, Floor, Wall

            if tile_type == "Door":
                self.tiles[y, x] = Door()
            elif tile_type == "Floor":
                self.tiles[y, x] = Floor()
            elif tile_type == "Wall":
                self.tiles[y, x] = Wall()

    def get_stairs_up_position(self) -> tuple[int, int] | None:
        """上り階段の位置を取得。"""
        return self.up_pos

    def get_stairs_down_position(self) -> tuple[int, int] | None:
        """下り階段の位置を取得。"""
        return self.down_pos

    @property
    def monsters(self):
        """現在のフロアのモンスターリストを取得。"""
        return self.monster_spawner.monsters

    @property
    def items(self):
        """現在のフロアのアイテムリストを取得。"""
        return self.item_spawner.items

    @property
    def traps(self):
        """現在のフロアのトラップリストを取得。"""
        return self.trap_manager.traps

    def _find_safe_start_position_for_floor1(
        self,
        tiles: np.ndarray,
        up_pos: tuple[int, int] | None,
        down_pos: tuple[int, int] | None,
    ) -> tuple[int, int]:
        """
        1階でプレイヤーの安全な開始位置を見つける。

        階段から離れた床タイルの位置を動的に探し、
        階段と重複しない安全な開始位置を返します。

        Args:
        ----
            tiles: ダンジョンタイルの2次元配列
            up_pos: 上り階段の位置
            down_pos: 下り階段の位置

        Returns:
        -------
            安全な開始位置のタプル (x, y)

        """
        from pyrogue.map.tile import Floor

        height, width = tiles.shape

        # 階段位置をリストにまとめる
        stairs_positions = []
        if up_pos is not None:
            stairs_positions.append(up_pos)
        if down_pos is not None:
            stairs_positions.append(down_pos)

        # 床タイルで階段から離れた位置を探す
        best_candidates = []

        # まず中央付近から検索
        center_x, center_y = width // 2, height // 2

        # 中央から外側に向かって螺旋状に検索
        for radius in range(1, min(width, height) // 2):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    x, y = center_x + dx, center_y + dy

                    # 境界チェック
                    if not (1 <= x < width - 1 and 1 <= y < height - 1):
                        continue

                    # 床タイルかチェック
                    if not isinstance(tiles[y, x], Floor):
                        continue

                    # 階段位置でないかチェック
                    if (x, y) in stairs_positions:
                        continue

                    # 階段から十分離れているかチェック
                    min_distance_to_stairs = float("inf")
                    for stairs_x, stairs_y in stairs_positions:
                        distance = abs(x - stairs_x) + abs(y - stairs_y)  # マンハッタン距離
                        min_distance_to_stairs = min(min_distance_to_stairs, distance)

                    # 階段から少なくとも2マス以上離れている位置を優先
                    if min_distance_to_stairs >= 2:
                        best_candidates.append((x, y))

                    # 十分な候補が見つかったら早期終了
                    if len(best_candidates) >= 10:
                        break
                if len(best_candidates) >= 10:
                    break
            if len(best_candidates) >= 10:
                break

        # 最適な候補が見つかった場合
        if best_candidates:
            # 中央に最も近い位置を選択
            best_position = min(
                best_candidates,
                key=lambda pos: abs(pos[0] - center_x) + abs(pos[1] - center_y),
            )
            return best_position

        # フォールバック: 階段から離れた位置で床タイルを探す
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if isinstance(tiles[y, x], Floor) and (x, y) not in stairs_positions:
                    return (x, y)

        # 最終フォールバック: 安全な固定位置
        fallback_x = max(2, min(width - 3, width // 4))
        fallback_y = max(2, min(height - 3, height // 4))
        return (fallback_x, fallback_y)


class DungeonManager:
    """
    ダンジョン管理クラス。

    マルチフロアダンジョンの状態を管理し、階層の生成、保存、
    読み込みを統合的に処理します。

    特徴:
        - 遅延生成によるメモリ効率化
        - 階層データの自動キャッシュ
        - プレイヤーの移動履歴追跡
        - 階層状態の永続化サポート

    Attributes
    ----------
        current_floor: 現在の階層番号
        previous_floor: 前回いた階層番号
        floors: 生成済み階層データのキャッシュ
        dungeon_width: ダンジョンの幅
        dungeon_height: ダンジョンの高さ

    """

    def __init__(self, dungeon_width: int = 80, dungeon_height: int = 45) -> None:
        """
        ダンジョンマネージャーを初期化。

        Args:
        ----
            dungeon_width: ダンジョンの幅
            dungeon_height: ダンジョンの高さ

        """
        self.current_floor = 1
        self.previous_floor = 1
        self.floors: dict[int, FloorData] = {}
        self.dungeon_width = dungeon_width
        self.dungeon_height = dungeon_height

    def get_floor(self, floor_number: int) -> FloorData:
        """
        指定された階層のデータを取得。

        階層が存在しない場合は新しく生成します。

        Args:
        ----
            floor_number: 取得する階層番号

        Returns:
        -------
            指定された階層のFloorDataインスタンス

        """
        if floor_number not in self.floors:
            self._generate_floor(floor_number)

        return self.floors[floor_number]

    def set_current_floor(self, floor_number: int) -> FloorData:
        """
        現在の階層を設定し、そのデータを返す。

        Args:
        ----
            floor_number: 設定する階層番号

        Returns:
        -------
            設定された階層のFloorDataインスタンス

        """
        self.previous_floor = self.current_floor
        self.current_floor = floor_number
        return self.get_floor(floor_number)

    def get_current_floor_data(self) -> FloorData:
        """
        現在の階層データを取得。

        Returns
        -------
            現在の階層のFloorDataインスタンス

        """
        return self.get_floor(self.current_floor)

    def descend_stairs(self) -> FloorData:
        """
        階段を下りて次の階層に移動。

        Returns
        -------
            移動先階層のFloorDataインスタンス

        """
        return self.set_current_floor(self.current_floor + 1)

    def ascend_stairs(self) -> FloorData | None:
        """
        階段を上って前の階層に移動。

        Returns
        -------
            移動先階層のFloorDataインスタンス。1階より上には移動できない場合はNone

        """
        if self.current_floor > 1:
            return self.set_current_floor(self.current_floor - 1)
        return None

    def get_player_spawn_position(self, floor_data: FloorData) -> tuple[int, int]:
        """
        プレイヤーのスポーン位置を決定。

        前の階層との関係に基づいて適切な位置を返します。

        Args:
        ----
            floor_data: 移動先の階層データ

        Returns:
        -------
            プレイヤーのスポーン位置 (x, y)

        """
        if self.current_floor < self.previous_floor:
            # 上の階に戻る場合は下り階段の位置
            return floor_data.down_pos
        # 下の階に降りる場合は上り階段の位置
        return floor_data.up_pos

    def clear_all_floors(self) -> None:
        """
        全ての階層データをクリア。

        新しいゲーム開始時などに使用します。
        """
        self.floors.clear()
        self.current_floor = 1
        self.previous_floor = 1

    def save_floor_state(self, floor_number: int, explored: np.ndarray) -> None:
        """
        指定階層の探索状態を更新。

        Args:
        ----
            floor_number: 更新する階層番号
            explored: 新しい探索済み領域のブール配列

        """
        if floor_number in self.floors:
            self.floors[floor_number].explored = explored.copy()

    def _generate_floor(self, floor_number: int) -> None:
        """
        新しい階層を生成。

        Args:
        ----
            floor_number: 生成する階層番号

        """
        # ダンジョンを生成
        dungeon_director = DungeonDirector(
            width=self.dungeon_width,
            height=self.dungeon_height,
            floor=floor_number,
        )
        tiles, up_pos, down_pos = dungeon_director.build_dungeon()

        # モンスターとアイテムを生成
        monster_spawner = MonsterSpawner(floor_number)
        monster_spawner.spawn_monsters(tiles, dungeon_director.rooms)


        item_spawner = ItemSpawner(floor_number)
        item_spawner.spawn_items(tiles, dungeon_director.rooms)

        # トラップを生成
        trap_manager = TrapManager()
        self._spawn_traps(trap_manager, tiles, dungeon_director.rooms, floor_number)

        # 探索済み領域を初期化
        explored = np.full((self.dungeon_height, self.dungeon_width), False, dtype=bool)

        # フロアデータを作成してキャッシュ
        floor_data = FloorData(
            floor_number=floor_number,
            tiles=tiles,
            up_pos=up_pos,
            down_pos=down_pos,
            monster_spawner=monster_spawner,
            item_spawner=item_spawner,
            trap_manager=trap_manager,
            explored=explored,
        )

        self.floors[floor_number] = floor_data

    def _spawn_traps(
        self,
        trap_manager: TrapManager,
        tiles: np.ndarray,
        rooms: list,
        floor_number: int,
    ) -> None:
        """
        トラップを生成して配置。

        Args:
        ----
            trap_manager: トラップ管理インスタンス
            tiles: ダンジョンタイルの2次元配列
            rooms: 部屋のリスト
            floor_number: 現在の階層番号

        """
        import random

        from pyrogue.entities.traps.trap import PitTrap, PoisonNeedleTrap, TeleportTrap
        from pyrogue.map.tile import Floor

        # トラップの種類と重み（階層に応じて調整）
        trap_types = [
            (PitTrap, 40),  # 落とし穴（一般的）
            (PoisonNeedleTrap, 30),  # 毒針（中程度）
            (TeleportTrap, 20),  # テレポート（稀）
        ]

        # 迷路階層の場合（部屋がない場合）の対応
        if not rooms:
            self._spawn_traps_in_maze(trap_manager, tiles, trap_types, floor_number)
            return

        # 階層が深いほどトラップの数を増加
        max_traps_per_room = min(3, 1 + floor_number // 5)

        for room in rooms:
            # 特別な部屋にはトラップを配置しない
            if room.is_special:
                continue

            # 部屋ごとのトラップ数を決定
            num_traps = random.randint(0, max_traps_per_room)

            for _ in range(num_traps):
                # 部屋の内部からランダムな床タイルを選択
                attempts = 0
                max_attempts = 20

                while attempts < max_attempts:
                    x = random.randint(room.x + 1, room.x + room.width - 2)
                    y = random.randint(room.y + 1, room.y + room.height - 2)

                    # 床タイルであることを確認
                    if isinstance(tiles[y, x], Floor):
                        # 同じ位置に既にトラップがないことを確認
                        if trap_manager.get_trap_at(x, y) is None:
                            # 重み付き抽選でトラップタイプを選択
                            trap_class = random.choices(
                                [trap_type for trap_type, _ in trap_types],
                                weights=[weight for _, weight in trap_types],
                                k=1,
                            )[0]

                            # トラップを作成して追加
                            new_trap = trap_class(x, y)
                            trap_manager.add_trap(new_trap)
                            break

                    attempts += 1

    def _spawn_traps_in_maze(
        self,
        trap_manager: TrapManager,
        tiles: np.ndarray,
        trap_types: list,
        floor_number: int,
    ) -> None:
        """
        迷路階層でトラップを配置。

        Args:
        ----
            trap_manager: トラップ管理インスタンス
            tiles: ダンジョンタイルの2次元配列
            trap_types: トラップの種類と重みのリスト
            floor_number: 現在の階層番号

        """
        from pyrogue.map.tile import Floor

        # 迷路の床タイル（通路）を全て取得
        floor_positions = []
        height, width = tiles.shape
        
        for y in range(height):
            for x in range(width):
                if isinstance(tiles[y, x], Floor):
                    floor_positions.append((x, y))
        
        # 迷路での基本トラップ数を決定（通路数に応じて調整）
        base_trap_count = max(2, len(floor_positions) // 50)  # 50床タイルごとに1つのトラップ
        level_bonus = floor_number // 5  # 階層ボーナス
        total_traps = min(base_trap_count + level_bonus, len(floor_positions) // 10)  # 最大密度制限
        
        # ランダムに配置位置を選択
        random.shuffle(floor_positions)
        
        # トラップを配置
        for i in range(min(total_traps, len(floor_positions))):
            x, y = floor_positions[i]
            
            # 同じ位置に既にトラップがないことを確認
            if trap_manager.get_trap_at(x, y) is None:
                # 重み付き抽選でトラップタイプを選択
                trap_class = random.choices(
                    [trap_type for trap_type, _ in trap_types],
                    weights=[weight for _, weight in trap_types],
                    k=1,
                )[0]
                
                # トラップを作成して追加
                new_trap = trap_class(x, y)
                trap_manager.add_trap(new_trap)

    def get_serializable_data(self) -> dict:
        """
        セーブ/ロード用のシリアライズ可能なデータを取得。

        Returns
        -------
            シリアライズ可能な階層データの辞書

        """
        return {
            "current_floor": self.current_floor,
            "previous_floor": self.previous_floor,
            "dungeon_width": self.dungeon_width,
            "dungeon_height": self.dungeon_height,
            "floors": {
                floor_num: {
                    "floor_number": data.floor_number,
                    "up_pos": data.up_pos,
                    "down_pos": data.down_pos,
                    "explored": data.explored.tolist() if data.explored is not None else None,
                }
                for floor_num, data in self.floors.items()
            },
        }

    def load_from_serialized_data(self, data: dict) -> None:
        """
        シリアライズされたデータから状態を復元。

        Args:
        ----
            data: シリアライズされたデータ

        """
        self.current_floor = data.get("current_floor", 1)
        self.previous_floor = data.get("previous_floor", 1)
        self.dungeon_width = data.get("dungeon_width", 80)
        self.dungeon_height = data.get("dungeon_height", 45)

        # 階層データは必要時に再生成されるため、
        # 探索済み情報のみを復元
        self.floors.clear()
        floors_data = data.get("floors", {})

        for floor_num_str, floor_info in floors_data.items():
            floor_num = int(floor_num_str)

            # 最小限のデータで階層を再生成
            self._generate_floor(floor_num)

            # 探索済み情報を復元
            if floor_info.get("explored"):
                explored_array = np.array(floor_info["explored"], dtype=bool)
                self.floors[floor_num].explored = explored_array
