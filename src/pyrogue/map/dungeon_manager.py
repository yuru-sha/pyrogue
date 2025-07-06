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
    >>> dungeon_manager = DungeonManager()
    >>> floor_data = dungeon_manager.get_floor(1)
    >>> dungeon_manager.set_current_floor(2)

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Tuple

import numpy as np

if TYPE_CHECKING:
    from pyrogue.entities.actors.monster_spawner import MonsterSpawner
    from pyrogue.entities.items.item_spawner import ItemSpawner

from pyrogue.entities.actors.monster_spawner import MonsterSpawner
from pyrogue.entities.items.item_spawner import ItemSpawner
from pyrogue.map.dungeon import DungeonGenerator


class FloorData:
    """
    単一フロアのデータを表すクラス。

    各階層の状態（タイル、エンティティ、探索状況）を保持します。

    Attributes:
        tiles: ダンジョンタイルの2次元配列
        up_pos: 上り階段の位置 (x, y)
        down_pos: 下り階段の位置 (x, y)
        monster_spawner: モンスター管理インスタンス
        item_spawner: アイテム管理インスタンス
        explored: 探索済み領域のブール配列
        floor_number: 階層番号
    """

    def __init__(
        self,
        floor_number: int,
        tiles: np.ndarray,
        up_pos: Tuple[int, int],
        down_pos: Tuple[int, int],
        monster_spawner: MonsterSpawner,
        item_spawner: ItemSpawner,
        explored: np.ndarray,
    ) -> None:
        """
        フロアデータを初期化。

        Args:
            floor_number: 階層番号
            tiles: ダンジョンタイルの2次元配列
            up_pos: 上り階段の位置
            down_pos: 下り階段の位置
            monster_spawner: モンスター管理インスタンス
            item_spawner: アイテム管理インスタンス
            explored: 探索済み領域のブール配列
        """
        self.floor_number = floor_number
        self.tiles = tiles
        self.up_pos = up_pos
        self.down_pos = down_pos
        self.monster_spawner = monster_spawner
        self.item_spawner = item_spawner
        self.explored = explored


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

    Attributes:
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
            dungeon_width: ダンジョンの幅
            dungeon_height: ダンジョンの高さ
        """
        self.current_floor = 1
        self.previous_floor = 1
        self.floors: Dict[int, FloorData] = {}
        self.dungeon_width = dungeon_width
        self.dungeon_height = dungeon_height

    def get_floor(self, floor_number: int) -> FloorData:
        """
        指定された階層のデータを取得。

        階層が存在しない場合は新しく生成します。

        Args:
            floor_number: 取得する階層番号

        Returns:
            指定された階層のFloorDataインスタンス
        """
        if floor_number not in self.floors:
            self._generate_floor(floor_number)

        return self.floors[floor_number]

    def set_current_floor(self, floor_number: int) -> FloorData:
        """
        現在の階層を設定し、そのデータを返す。

        Args:
            floor_number: 設定する階層番号

        Returns:
            設定された階層のFloorDataインスタンス
        """
        self.previous_floor = self.current_floor
        self.current_floor = floor_number
        return self.get_floor(floor_number)

    def get_current_floor_data(self) -> FloorData:
        """
        現在の階層データを取得。

        Returns:
            現在の階層のFloorDataインスタンス
        """
        return self.get_floor(self.current_floor)

    def descend_stairs(self) -> FloorData:
        """
        階段を下りて次の階層に移動。

        Returns:
            移動先階層のFloorDataインスタンス
        """
        return self.set_current_floor(self.current_floor + 1)

    def ascend_stairs(self) -> Optional[FloorData]:
        """
        階段を上って前の階層に移動。

        Returns:
            移動先階層のFloorDataインスタンス。1階より上には移動できない場合はNone
        """
        if self.current_floor > 1:
            return self.set_current_floor(self.current_floor - 1)
        return None

    def get_player_spawn_position(self, floor_data: FloorData) -> Tuple[int, int]:
        """
        プレイヤーのスポーン位置を決定。

        前の階層との関係に基づいて適切な位置を返します。

        Args:
            floor_data: 移動先の階層データ

        Returns:
            プレイヤーのスポーン位置 (x, y)
        """
        if self.current_floor < self.previous_floor:
            # 上の階に戻る場合は下り階段の位置
            return floor_data.down_pos
        else:
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
            floor_number: 更新する階層番号
            explored: 新しい探索済み領域のブール配列
        """
        if floor_number in self.floors:
            self.floors[floor_number].explored = explored.copy()

    def _generate_floor(self, floor_number: int) -> None:
        """
        新しい階層を生成。

        Args:
            floor_number: 生成する階層番号
        """
        # ダンジョンを生成
        dungeon = DungeonGenerator(
            width=self.dungeon_width,
            height=self.dungeon_height,
            floor=floor_number,
        )
        tiles, up_pos, down_pos = dungeon.generate()

        # モンスターとアイテムを生成
        monster_spawner = MonsterSpawner(floor_number)
        monster_spawner.spawn_monsters(tiles, dungeon.rooms)

        item_spawner = ItemSpawner(floor_number)
        item_spawner.spawn_items(tiles, dungeon.rooms)

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
            explored=explored,
        )

        self.floors[floor_number] = floor_data

    def get_serializable_data(self) -> Dict:
        """
        セーブ/ロード用のシリアライズ可能なデータを取得。

        Returns:
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
                    "explored": data.explored.tolist()
                    if data.explored is not None
                    else None,
                }
                for floor_num, data in self.floors.items()
            },
        }

    def load_from_serialized_data(self, data: Dict) -> None:
        """
        シリアライズされたデータから状態を復元。

        Args:
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
