"""
NPCSpawner モジュール。

このモジュールは、ダンジョン生成時にNPCを配置するシステムを実装します。
特別な部屋や通常の部屋に適切なNPCを配置し、フロアごとのNPC管理を行います。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import numpy as np

from pyrogue.entities.actors.inventory import Inventory
from pyrogue.entities.actors.npc import NPC, NPCDisposition, NPCType
from pyrogue.entities.items.item import Armor, Weapon

if TYPE_CHECKING:
    from pyrogue.map.dungeon.room import Room


class NPCSpawner:
    """
    NPCの配置を管理するクラス。

    ダンジョン生成時に適切な場所にNPCを配置し、
    フロアごとのNPC管理を行います。

    Attributes:
        floor: 現在のフロア番号
        npcs: 生成されたNPCのリスト
        occupied_positions: 占有されている位置のセット

    """

    def __init__(self, floor: int) -> None:
        """
        NPCSpawnerの初期化。

        Args:
            floor: 現在のフロア番号

        """
        self.floor = floor
        self.npcs: list[NPC] = []
        self.occupied_positions: set[tuple[int, int]] = set()

    def spawn_npcs(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """
        ダンジョンにNPCを配置する。

        Args:
            dungeon_tiles: ダンジョンタイルの配列
            rooms: 部屋のリスト

        """
        # NPCシステムの有効性をチェック
        from pyrogue.constants import FeatureConstants
        if not FeatureConstants.ENABLE_NPC_SYSTEM:
            return

        # 特別な部屋にNPCを配置
        self._spawn_special_room_npcs(dungeon_tiles, rooms)

        # 通常の部屋にNPCを配置
        self._spawn_regular_room_npcs(dungeon_tiles, rooms)

    def _spawn_special_room_npcs(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """
        特別な部屋にNPCを配置する。

        Args:
            dungeon_tiles: ダンジョンタイルの配列
            rooms: 部屋のリスト

        """
        for room in rooms:
            if not room.is_special:
                continue

            # 特別な部屋の種類に応じてNPCを配置
            npc_type = self._get_npc_type_for_special_room(room.room_type)
            if npc_type:
                position = self._get_random_position_in_room(room, dungeon_tiles)
                if position:
                    npc = self._create_npc(npc_type, position, room.room_type)
                    if npc:
                        self.npcs.append(npc)
                        self.occupied_positions.add(position)

    def _spawn_regular_room_npcs(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """
        通常の部屋にNPCを配置する。

        Args:
            dungeon_tiles: ダンジョンタイルの配列
            rooms: 部屋のリスト

        """
        # フロアレベルに応じてNPC数を決定
        npc_count = self._calculate_npc_count()

        # 利用可能な通常の部屋を取得
        available_rooms = [room for room in rooms if not room.is_special]

        if not available_rooms:
            return

        # 指定数のNPCを配置
        for _ in range(npc_count):
            if not available_rooms:
                break

            room = random.choice(available_rooms)
            position = self._get_random_position_in_room(room, dungeon_tiles)

            if position:
                npc_type = self._get_random_npc_type()
                npc = self._create_npc(npc_type, position)
                if npc:
                    self.npcs.append(npc)
                    self.occupied_positions.add(position)

    def _get_npc_type_for_special_room(self, room_type: str) -> NPCType | None:
        """
        特別な部屋の種類に応じたNPCタイプを取得する。

        Args:
            room_type: 部屋の種類

        Returns:
            対応するNPCタイプ、またはNone

        """
        special_room_mapping = {
            "treasure_room": NPCType.MERCHANT,
            "shrine": NPCType.PRIEST,
            "laboratory": NPCType.MAGE,
            "library": NPCType.MAGE,
            "armory": NPCType.GUARD,
        }

        return special_room_mapping.get(room_type)

    def _get_random_npc_type(self) -> NPCType:
        """
        ランダムなNPCタイプを取得する。

        Returns:
            ランダムなNPCタイプ

        """
        # 一般的なNPCタイプの重み付き選択
        npc_types = [
            (NPCType.MERCHANT, 0.4),    # 商人は比較的多い
            (NPCType.VILLAGER, 0.3),    # 村人も多い
            (NPCType.GUARD, 0.2),       # 警備員は中程度
            (NPCType.PRIEST, 0.05),     # 僧侶は少ない
            (NPCType.MAGE, 0.05),       # 魔術師は少ない
        ]

        return random.choices(
            [npc_type for npc_type, _ in npc_types],
            weights=[weight for _, weight in npc_types]
        )[0]

    def _calculate_npc_count(self) -> int:
        """
        フロアレベルに応じたNPC数を計算する。

        Returns:
            配置するNPC数

        """
        # 上層フロアほどNPCが多い
        base_count = max(1, 3 - self.floor // 10)

        # ランダムな変動を加える
        variation = random.randint(-1, 1)

        return max(0, base_count + variation)

    def _get_random_position_in_room(self, room: Room, dungeon_tiles: np.ndarray) -> tuple[int, int] | None:
        """
        部屋内のランダムな位置を取得する。

        Args:
            room: 部屋オブジェクト
            dungeon_tiles: ダンジョンタイルの配列

        Returns:
            有効な位置のタプル、またはNone

        """
        # 部屋の境界を取得 (新しいRoom構造に対応)
        x1, y1 = room.x, room.y
        x2, y2 = room.x + room.width, room.y + room.height

        # 部屋の内部位置を試行
        max_attempts = 20
        for _ in range(max_attempts):
            x = random.randint(x1 + 1, x2 - 1)
            y = random.randint(y1 + 1, y2 - 1)

            # 位置が有効かチェック
            if self._is_valid_position(x, y, dungeon_tiles):
                return (x, y)

        return None

    def _is_valid_position(self, x: int, y: int, dungeon_tiles: np.ndarray) -> bool:
        """
        位置が有効かどうかをチェックする。

        Args:
            x: X座標
            y: Y座標
            dungeon_tiles: ダンジョンタイルの配列

        Returns:
            位置が有効な場合はTrue

        """
        # 境界チェック
        if not (0 <= x < dungeon_tiles.shape[1] and 0 <= y < dungeon_tiles.shape[0]):
            return False

        # 既に占有されている位置はNG
        if (x, y) in self.occupied_positions:
            return False

        # 床タイルかどうかをチェック
        # dungeon_tiles[y, x] が床タイルを表す値であることを確認
        # 実際の実装では、タイルの種類に応じて適切な値をチェック
        return dungeon_tiles[y, x] == 0  # 0 = 床タイル（実装により異なる）

    def _create_npc(self, npc_type: NPCType, position: tuple[int, int],
                   room_type: str | None = None) -> NPC | None:
        """
        NPCを作成する。

        Args:
            npc_type: NPCの種類
            position: 配置位置
            room_type: 部屋の種類（オプション）

        Returns:
            作成されたNPC、またはNone

        """
        x, y = position

        # NPCのタイプに応じた基本設定
        npc_configs = {
            NPCType.MERCHANT: {
                "name": self._generate_merchant_name(),
                "char": "@",
                "color": (255, 255, 0),  # 金色
                "disposition": NPCDisposition.FRIENDLY,
                "dialogue_id": "friendly_merchant",
                "create_inventory": True,
            },
            NPCType.PRIEST: {
                "name": self._generate_priest_name(),
                "char": "@",
                "color": (255, 255, 255),  # 白色
                "disposition": NPCDisposition.FRIENDLY,
                "dialogue_id": "friendly_priest",
                "create_inventory": False,
            },
            NPCType.MAGE: {
                "name": self._generate_mage_name(),
                "char": "@",
                "color": (128, 0, 128),  # 紫色
                "disposition": NPCDisposition.NEUTRAL,
                "dialogue_id": "neutral_mage",
                "create_inventory": False,
            },
            NPCType.GUARD: {
                "name": self._generate_guard_name(),
                "char": "@",
                "color": (169, 169, 169),  # 灰色
                "disposition": NPCDisposition.NEUTRAL,
                "dialogue_id": "neutral_guard",
                "create_inventory": False,
            },
            NPCType.VILLAGER: {
                "name": self._generate_villager_name(),
                "char": "@",
                "color": (139, 69, 19),  # 茶色
                "disposition": NPCDisposition.FRIENDLY,
                "dialogue_id": "friendly_villager",
                "create_inventory": False,
            },
        }

        if npc_type not in npc_configs:
            return None

        config = npc_configs[npc_type]

        # インベントリの作成
        inventory = None
        if config["create_inventory"]:
            inventory = self._create_merchant_inventory()

        # NPCの作成
        npc = NPC(
            char=config["char"],
            x=x,
            y=y,
            name=config["name"],
            level=1,
            hp=50,
            max_hp=50,
            attack=10,
            defense=5,
            color=config["color"],
            disposition=config["disposition"],
            npc_type=npc_type,
            dialogue_id=config["dialogue_id"],
            inventory=inventory,
        )

        return npc

    def _create_merchant_inventory(self) -> Inventory:
        """
        商人用のインベントリを作成する。

        Returns:
            商人用のインベントリ

        """
        inventory = Inventory()

        # 商人の商品をランダムに生成
        items = [
            # 武器
            Weapon(x=0, y=0, name="Iron Sword", attack_bonus=5),
            Weapon(x=0, y=0, name="Steel Dagger", attack_bonus=3),

            # 防具
            Armor(x=0, y=0, name="Leather Armor", defense_bonus=2),
            Armor(x=0, y=0, name="Chain Mail", defense_bonus=4),

            # ポーション（簡単なダミー効果を使用）
            # 一時的にコメントアウト - 実際の効果システムが実装されるまで
            # Potion(x=0, y=0, name="Healing Potion", effect=dummy_effect),
            # Potion(x=0, y=0, name="Mana Potion", effect=dummy_effect),

            # 巻物 - 一時的にコメントアウト（effectパラメータが必要）
            # Scroll(x=0, y=0, name="Scroll of Teleportation", effect=dummy_effect),
            # Scroll(x=0, y=0, name="Scroll of Identify", effect=dummy_effect),

            # 食料 - 一時的にコメントアウト（effectパラメータが必要）
            # Food(x=0, y=0, name="Bread", effect=dummy_effect),
            # Food(x=0, y=0, name="Cheese", effect=dummy_effect),
        ]

        # 商品をランダムに選択して追加
        num_items = random.randint(3, 6)
        selected_items = random.sample(items, min(num_items, len(items)))

        for item in selected_items:
            inventory.add_item(item)

        return inventory

    def _generate_merchant_name(self) -> str:
        """商人の名前を生成。"""
        names = ["Merchant Bob", "Trader Alice", "Shopkeeper Tom", "Vendor Mary"]
        return random.choice(names)

    def _generate_priest_name(self) -> str:
        """僧侶の名前を生成。"""
        names = ["Father John", "Sister Maria", "Brother Luke", "Priestess Anna"]
        return random.choice(names)

    def _generate_mage_name(self) -> str:
        """魔術師の名前を生成。"""
        names = ["Wizard Gandalf", "Sorceress Luna", "Mage Merlin", "Enchanter Zara"]
        return random.choice(names)

    def _generate_guard_name(self) -> str:
        """警備員の名前を生成。"""
        names = ["Guard Captain", "Sergeant Stone", "Watchman Joe", "Sentry Kate"]
        return random.choice(names)

    def _generate_villager_name(self) -> str:
        """村人の名前を生成。"""
        names = ["Villager Sam", "Citizen Jane", "Farmer Bill", "Resident Lisa"]
        return random.choice(names)

    def get_npcs(self) -> list[NPC]:
        """
        生成されたNPCのリストを取得する。

        Returns:
            NPCのリスト

        """
        return self.npcs.copy()

    def get_npc_at_position(self, x: int, y: int) -> NPC | None:
        """
        指定された位置にいるNPCを取得する。

        Args:
            x: X座標
            y: Y座標

        Returns:
            指定位置にいるNPC、またはNone

        """
        for npc in self.npcs:
            if npc.x == x and npc.y == y:
                return npc
        return None

    def clear_npcs(self) -> None:
        """NPCをクリアする。"""
        self.npcs.clear()
        self.occupied_positions.clear()
