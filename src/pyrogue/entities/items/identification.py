"""
アイテム識別システムモジュール。

オリジナルRogue風の未識別アイテム表示と識別機能を提供します。
"""

from __future__ import annotations

import random


class ItemIdentification:
    """アイテム識別状態管理クラス"""

    def __init__(self) -> None:
        """識別状態を初期化"""
        # 識別済みアイテムを追跡
        self.identified_potions: set[str] = set()
        self.identified_scrolls: set[str] = set()
        self.identified_rings: set[str] = set()

        # 未識別名マッピング（プレイ毎にランダム化）
        self.potion_appearances: dict[str, str] = {}
        self.scroll_appearances: dict[str, str] = {}
        self.ring_appearances: dict[str, str] = {}

        # 未識別名のプール
        self.potion_colors = [
            "red",
            "blue",
            "green",
            "yellow",
            "purple",
            "orange",
            "pink",
            "brown",
            "black",
            "white",
            "gray",
            "cyan",
            "magenta",
            "silver",
            "gold",
            "clear",
        ]

        self.scroll_words = [
            "ZELGO MER",
            "JUYED AWK YACC",
            "NR 9",
            "XIXAXA XOXAXA",
            "PRIRUTSENIE",
            "ELBIB YLOH",
            "VERR YED HORRE",
            "VENZAR BORGAVVE",
            "THARR",
            "YUM YUM",
            "KERNOD WEL",
            "ELAM EBOW",
            "DUAM XNAHT",
            "ANDOVA BEGARIN",
            "KIRJE",
            "VE FORBRYDERNE",
            "CHATRANG",
            "VELOX NEB",
            "FOOBIE BLETCH",
            "TEMOV",
        ]

        self.ring_materials = [
            "wooden",
            "granite",
            "opal",
            "clay",
            "coral",
            "black onyx",
            "moonstone",
            "tiger eye",
            "pearl",
            "glass",
            "agate",
            "sapphire",
            "ruby",
            "diamond",
            "jacinth",
            "obsidian",
            "jade",
            "amber",
            "jet",
            "bronze",
        ]

        self._initialize_appearances()

    def _initialize_appearances(self) -> None:
        """未識別名をランダムに割り当て"""
        # ポーション名のシャッフル
        potion_names = [
            "Healing Potion",
            "Mana Potion",
            "Poison Potion",
            "Strength Potion",
        ]
        available_colors = self.potion_colors.copy()
        random.shuffle(available_colors)

        for i, potion_name in enumerate(potion_names):
            if i < len(available_colors):
                self.potion_appearances[potion_name] = available_colors[i]

        # 巻物名のシャッフル
        scroll_names = [
            "Scroll of Identify",
            "Scroll of Teleportation",
            "Scroll of Magic Mapping",
            "Scroll of Light",
            "Scroll of Remove Curse",
            "Scroll of Enchant Weapon",
            "Scroll of Enchant Armor",
        ]
        available_words = self.scroll_words.copy()
        random.shuffle(available_words)

        for i, scroll_name in enumerate(scroll_names):
            if i < len(available_words):
                self.scroll_appearances[scroll_name] = available_words[i]

        # 指輪名のシャッフル
        ring_names = [
            "Ring of Strength",
            "Ring of Protection",
            "Ring of Dexterity",
            "Ring of Regeneration",
        ]
        available_materials = self.ring_materials.copy()
        random.shuffle(available_materials)

        for i, ring_name in enumerate(ring_names):
            if i < len(available_materials):
                self.ring_appearances[ring_name] = available_materials[i]

    def get_display_name(self, item_name: str, item_type: str) -> str:
        """アイテムの表示名を取得（識別状態に応じて）"""
        if item_type == "POTION":
            if item_name in self.identified_potions:
                return item_name
            if item_name in self.potion_appearances:
                color = self.potion_appearances[item_name]
                return f"{color} potion"

        elif item_type == "SCROLL":
            if item_name in self.identified_scrolls:
                return item_name
            if item_name in self.scroll_appearances:
                words = self.scroll_appearances[item_name]
                return f'scroll labeled "{words}"'

        elif item_type == "RING":
            if item_name in self.identified_rings:
                return item_name
            if item_name in self.ring_appearances:
                material = self.ring_appearances[item_name]
                return f"{material} ring"

        # 未対応のアイテムタイプや武器・防具は常に識別済み
        return item_name

    def identify_item(self, item_name: str, item_type: str) -> bool:
        """アイテムを識別"""
        if item_type == "POTION" and item_name not in self.identified_potions:
            self.identified_potions.add(item_name)
            return True
        if item_type == "SCROLL" and item_name not in self.identified_scrolls:
            self.identified_scrolls.add(item_name)
            return True
        if item_type == "RING" and item_name not in self.identified_rings:
            self.identified_rings.add(item_name)
            return True

        return False  # 既に識別済み

    def is_identified(self, item_name: str, item_type: str) -> bool:
        """アイテムが識別済みかどうかを判定"""
        if item_type == "POTION":
            return item_name in self.identified_potions
        if item_type == "SCROLL":
            return item_name in self.identified_scrolls
        if item_type == "RING":
            return item_name in self.identified_rings

        # 武器・防具・食料・金貨は常に識別済み
        return True

    def identify_all_of_type(self, item_name: str, item_type: str) -> int:
        """同じタイプのアイテムをすべて識別（識別の巻物用）"""
        count = 0
        if self.identify_item(item_name, item_type):
            count = 1

        # 同じタイプのアイテムがインベントリにあれば、それらも識別される
        # この処理は呼び出し元で行う
        return count

    def get_identification_message(self, item_name: str, item_type: str) -> str:
        """識別時のメッセージを取得"""
        display_name = self.get_display_name(item_name, item_type)

        if item_type == "POTION" or item_type == "SCROLL" or item_type == "RING":
            return f"This {display_name} is a {item_name}!"

        return f"You have identified the {item_name}."
