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

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from pyrogue.entities.actors.monster_spawner import MonsterSpawner
    from pyrogue.entities.items.item_spawner import ItemSpawner

from pyrogue.entities.actors.monster_spawner import MonsterSpawner
from pyrogue.entities.actors.npc_spawner import NPCSpawner
from pyrogue.entities.items.item_spawner import ItemSpawner
from pyrogue.entities.traps.trap import TrapManager

# 新しいBuilder Patternベースのダンジョン生成システムを使用
from pyrogue.map.dungeon.director import DungeonDirector


class FloorData:
    """
    単一フロアのデータを表すクラス。

    各階層の状態（タイル、エンティティ、探索状況）を保持します。

    Attributes:
        tiles: ダンジョンタイルの2次元配列
        up_pos: 上り階段の位置 (x, y)
        down_pos: 下り階段の位置 (x, y)
        monster_spawner: モンスター管理インスタンス
        npc_spawner: NPC管理インスタンス
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
        npc_spawner: NPCSpawner,
        item_spawner: ItemSpawner,
        trap_manager: TrapManager,
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
            npc_spawner: NPC管理インスタンス
            item_spawner: アイテム管理インスタンス
            trap_manager: トラップ管理インスタンス
            explored: 探索済み領域のブール配列

        """
        self.floor_number = floor_number
        self.tiles = tiles
        self.up_pos = up_pos
        self.down_pos = down_pos
        self.monster_spawner = monster_spawner
        self.npc_spawner = npc_spawner
        self.item_spawner = item_spawner
        self.trap_manager = trap_manager
        self.explored = explored

        # 開始位置を設定（1階では下り階段の位置、その他では上り階段の位置）
        if up_pos is not None:
            self.start_pos = up_pos
        elif down_pos is not None:
            self.start_pos = down_pos
        else:
            # フォールバック：最初の部屋の中央
            self.start_pos = (0, 0)  # デフォルト値


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
        self.floors: dict[int, FloorData] = {}
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

    def ascend_stairs(self) -> FloorData | None:
        """
        階段を上って前の階層に移動。

        Returns:
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
            floor_data: 移動先の階層データ

        Returns:
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
        dungeon_director = DungeonDirector(
            width=self.dungeon_width,
            height=self.dungeon_height,
            floor=floor_number,
        )
        tiles, up_pos, down_pos = dungeon_director.build_dungeon()

        # モンスターとアイテムを生成
        monster_spawner = MonsterSpawner(floor_number)
        monster_spawner.spawn_monsters(tiles, dungeon_director.rooms)

        # NPCを生成
        npc_spawner = NPCSpawner(floor_number)
        npc_spawner.spawn_npcs(tiles, dungeon_director.rooms)

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
            npc_spawner=npc_spawner,
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
        floor_number: int
    ) -> None:
        """
        トラップを生成して配置。

        Args:
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
                                k=1
                            )[0]

                            # トラップを作成して追加
                            new_trap = trap_class(x, y)
                            trap_manager.add_trap(new_trap)
                            break

                    attempts += 1

    def get_serializable_data(self) -> dict:
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

    def load_from_serialized_data(self, data: dict) -> None:
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
