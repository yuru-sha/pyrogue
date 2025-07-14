"""
特別部屋ビルダー - 特別部屋生成専用コンポーネント。

このモジュールは、ダンジョンの特別部屋に特化したビルダーです。
宝物庫、実験室などの特別部屋の生成、装飾、アイテム配置を担当します。
"""

from __future__ import annotations

import random

from pyrogue.constants import ProbabilityConstants
from pyrogue.map.dungeon.room_builder import Room
from pyrogue.utils import game_logger


class SpecialRoomBuilder:
    """
    特別部屋生成専用のビルダークラス。

    宝物庫、実験室などの特別部屋の生成、装飾、
    特別アイテムの配置を担当します。

    Attributes
    ----------
        floor: 現在の階層
        special_rooms_created: 作成された特別部屋のリスト

    """

    def __init__(self, floor: int) -> None:
        """
        特別部屋ビルダーを初期化。

        Args:
        ----
            floor: 階層番号

        """
        self.floor = floor
        self.special_rooms_created: list[Room] = []

    def process_special_rooms(self, rooms: list[Room]) -> None:
        """
        特別部屋を処理。

        Args:
        ----
            rooms: 部屋のリスト

        """
        self.special_rooms_created: list[Room] = []

        for room in rooms:
            if self._should_create_special_room(room):
                room_type = self._select_special_room_type()
                room.is_special = True
                room.room_type = room_type
                self._decorate_special_room(room)
                self.special_rooms_created.append(room)

        game_logger.info(f"Created {len(self.special_rooms_created)} special rooms on floor {self.floor}")

    def _should_create_special_room(self, room: Room) -> bool:
        """
        特別部屋を作成するかどうかを判定。

        Args:
        ----
            room: 対象の部屋

        Returns:
        -------
            特別部屋を作成する場合True

        """
        # 階層が深いほど特別部屋の確率が高くなる
        base_chance = ProbabilityConstants.SPECIAL_ROOM_CHANCE
        floor_modifier = min(0.1, self.floor * 0.02)  # 階層ごとに2%ずつ増加、最大10%

        adjusted_chance = base_chance + floor_modifier

        return random.random() < adjusted_chance

    def _select_special_room_type(self) -> str:
        """
        特別部屋の種類を選択。

        Returns
        -------
            特別部屋の種類

        """
        # 階層に応じて異なる特別部屋を生成
        room_types = {
            "treasure_room": 0.4,  # 宝物庫
            "library": 0.2,  # 図書館（巻物が多い）
            "armory": 0.2,  # 武器庫（武器・防具が多い）
            "laboratory": 0.1,  # 実験室（ポーションが多い）
            "shrine": 0.1,  # 聖堂（特別な効果）
        }

        # 深い階層では宝物庫の確率を上げる
        if self.floor >= 15:
            room_types["treasure_room"] = 0.6
            room_types["vault"] = 0.1  # 金庫室（最深層のみ）

        # 最深層（26階）では特別な部屋
        if self.floor >= 26:
            room_types["amulet_chamber"] = 0.3  # アミュレット部屋

        # 確率に基づいて選択
        rand_val = random.random()
        cumulative = 0.0

        for room_type, probability in room_types.items():
            cumulative += probability
            if rand_val <= cumulative:
                return room_type

        return "treasure_room"  # デフォルト

    def _decorate_special_room(self, room: Room) -> None:
        """
        特別部屋を装飾。

        Args:
        ----
            room: 装飾する部屋

        """
        room_type = room.room_type

        game_logger.debug(f"Decorating {room_type} (room {room.id}) on floor {self.floor}")

        if room_type == "treasure_room":
            self._decorate_treasure_room(room)
        elif room_type == "library":
            self._decorate_library(room)
        elif room_type == "armory":
            self._decorate_armory(room)
        elif room_type == "laboratory":
            self._decorate_laboratory(room)
        elif room_type == "shrine":
            self._decorate_shrine(room)
        elif room_type == "vault":
            self._decorate_vault(room)
        elif room_type == "amulet_chamber":
            self._decorate_amulet_chamber(room)

    def _decorate_treasure_room(self, room: Room) -> None:
        """
        宝物庫を装飾。

        Args:
        ----
            room: 装飾する部屋

        """
        # アイテム配置はItemSpawnerで行われるため、
        # ここでは部屋の特性のみ設定
        room.treasure_multiplier = 2.0  # アイテム生成量を2倍に
        room.gold_multiplier = 3.0  # 金貨生成量を3倍に

    def _decorate_library(self, room: Room) -> None:
        """
        図書館を装飾。

        Args:
        ----
            room: 装飾する部屋

        """
        room.scroll_chance = 0.8  # 巻物の出現確率を80%に
        room.book_chance = 0.3  # 本の出現確率を30%に

    def _decorate_armory(self, room: Room) -> None:
        """
        武器庫を装飾。

        Args:
        ----
            room: 装飾する部屋

        """
        room.weapon_chance = 0.7  # 武器の出現確率を70%に
        room.armor_chance = 0.7  # 防具の出現確率を70%に
        room.enhancement_bonus = 1  # 装備の強化ボーナス

    def _decorate_laboratory(self, room: Room) -> None:
        """
        実験室を装飾。

        Args:
        ----
            room: 装飾する部屋

        """
        room.potion_chance = 0.8  # ポーションの出現確率を80%に
        room.rare_potion_chance = 0.3  # 希少ポーションの出現確率を30%に

    def _decorate_shrine(self, room: Room) -> None:
        """
        聖堂を装飾。

        Args:
        ----
            room: 装飾する部屋

        """
        room.blessing_chance = 0.5  # 祝福効果の確率を50%に
        room.holy_item_chance = 0.2  # 聖なるアイテムの確率を20%に

    def _decorate_vault(self, room: Room) -> None:
        """
        金庫室を装飾。

        Args:
        ----
            room: 装飾する部屋

        """
        room.treasure_multiplier = 5.0  # アイテム生成量を5倍に
        room.gold_multiplier = 10.0  # 金貨生成量を10倍に
        room.rare_item_chance = 0.8  # 希少アイテムの確率を80%に

    def _decorate_amulet_chamber(self, room: Room) -> None:
        """
        アミュレット部屋を装飾（最深層専用）。

        Args:
        ----
            room: 装飾する部屋

        """
        room.has_amulet = True  # イェンダーのアミュレット配置
        room.guardian_chance = 1.0  # ガーディアンモンスター確定

    def get_special_room_description(self, room: Room) -> str:
        """
        特別部屋の説明を取得。

        Args:
        ----
            room: 対象の部屋

        Returns:
        -------
            部屋の説明文

        """
        if not room.is_special:
            return "A normal room."

        descriptions = {
            "treasure_room": "This room glitters with treasure and gold!",
            "library": "Ancient tomes and scrolls line the walls of this library.",
            "armory": "Weapons and armor are stored here in neat rows.",
            "laboratory": "Strange potions and apparatus fill this laboratory.",
            "shrine": "A holy aura emanates from this sacred shrine.",
            "vault": "This heavily fortified vault contains incredible wealth!",
            "amulet_chamber": "The legendary Amulet of Yendor rests here!",
        }

        return descriptions.get(room.room_type, "A mysterious special room.")

    def count_special_rooms_by_type(self) -> dict:
        """
        種類別の特別部屋数をカウント。

        Returns
        -------
            部屋種類とその数の辞書

        """
        room_counts: dict[str, int] = {}
        for room in self.special_rooms_created:
            room_type = room.room_type
            room_counts[room_type] = room_counts.get(room_type, 0) + 1
        return room_counts

    def reset(self) -> None:
        """ビルダーの状態をリセット。"""
        self.special_rooms_created: list[Room] = []

    def get_statistics(self) -> dict:
        """特別部屋生成の統計情報を取得。"""
        room_counts = self.count_special_rooms_by_type()

        return {
            "floor": self.floor,
            "special_rooms_count": len(self.special_rooms_created),
            "room_types": room_counts,
        }
