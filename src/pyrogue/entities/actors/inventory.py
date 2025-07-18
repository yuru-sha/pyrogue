"""Inventory management module."""

from __future__ import annotations

from pyrogue.entities.items.item import Armor, Item, Ring, Weapon


class Inventory:
    """インベントリ管理クラス"""

    def __init__(self, capacity: int = 26) -> None:  # a-zの26文字分
        self.capacity = capacity
        self.items: list[Item] = []

        # 装備スロット
        self.equipped: dict[str, Item | None] = {
            "weapon": None,
            "armor": None,
            "ring_left": None,
            "ring_right": None,
        }

    def add_item(self, item: Item) -> bool:
        """
        アイテムを追加

        Args:
        ----
            item: 追加するアイテム

        Returns:
        -------
            bool: 追加に成功したかどうか

        """
        if len(self.items) >= self.capacity:
            return False

        # スタック可能なアイテムの場合、既存のスタックに追加を試みる
        if item.stackable:
            for existing_item in self.items:
                if (
                    existing_item.name == item.name
                    and existing_item.stackable
                    and isinstance(existing_item, type(item))
                ):
                    existing_item.stack_count += item.stack_count
                    return True

        self.items.append(item)
        return True

    def remove_item(self, item: Item, count: int = 1) -> int:
        """
        アイテムを削除

        Args:
        ----
            item: 削除するアイテム
            count: 削除する数量（スタック可能アイテムの場合）

        Returns:
        -------
            実際に削除された数量

        Raises:
        ------
            ValueError: countが0以下の場合

        """
        if count <= 0:
            msg = f"Invalid count: {count}. Count must be positive."
            raise ValueError(msg)

        if item not in self.items:
            return 0  # アイテムが存在しない場合は0を返す

        if item.stackable and item.stack_count > count:
            # スタック可能なアイテムで、削除数がスタック数より少ない場合
            item.stack_count -= count
            return count
        # スタック不可能、または削除数がスタック数以上の場合は完全削除
        actual_removed = item.stack_count if item.stackable else 1
        self.items.remove(item)

        return actual_removed

    def get_item(self, index: int) -> Item | None:
        """
        指定されたインデックスのアイテムを取得

        Args:
        ----
            index: アイテムのインデックス

        Returns:
        -------
            Optional[Item]: アイテム（存在しない場合はNone）

        """
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def equip(self, item: Item) -> Item | None:
        """
        アイテムを装備

        Args:
        ----
            item: 装備するアイテム

        Returns:
        -------
            Optional[Item]: 外したアイテム（ある場合）

        """
        if isinstance(item, Weapon):
            old_item = self.equipped["weapon"]
            self.equipped["weapon"] = item
            return old_item

        if isinstance(item, Armor):
            old_item = self.equipped["armor"]
            self.equipped["armor"] = item
            return old_item

        if isinstance(item, Ring):
            # 左手の指輪が空いていれば左手に、そうでなければ右手に装備
            if self.equipped["ring_left"] is None:
                self.equipped["ring_left"] = item
                return None  # 交換されたアイテムはない
            old_item = self.equipped["ring_right"]
            self.equipped["ring_right"] = item
            return old_item

        return None

    def unequip(self, slot: str) -> Item | None:
        """
        装備を外す

        Args:
        ----
            slot: 装備スロット名

        Returns:
        -------
            Optional[Item]: 外したアイテム（ある場合）

        """
        if slot in self.equipped:
            item = self.equipped[slot]
            # 呪われたアイテムは外せない
            if item and item.cursed:
                return None
            self.equipped[slot] = None
            return item
        return None

    def get_attack_bonus(self) -> int:
        """
        装備による攻撃力ボーナスを計算

        Returns
        -------
            int: 攻撃力ボーナス

        """
        bonus = 0

        # 武器のボーナス（基本攻撃力＋強化値）
        if isinstance(self.equipped["weapon"], Weapon):
            weapon = self.equipped["weapon"]
            bonus += weapon.attack + weapon.enchantment

        # 指輪のボーナス
        for ring_slot in ["ring_left", "ring_right"]:
            ring = self.equipped[ring_slot]
            if isinstance(ring, Ring) and ring.effect == "strength":
                bonus += ring.bonus

        return bonus

    def get_defense_bonus(self) -> int:
        """
        装備による防御力ボーナスを計算

        Returns
        -------
            int: 防御力ボーナス

        """
        bonus = 0

        # 防具のボーナス（基本防御力＋強化値）
        if isinstance(self.equipped["armor"], Armor):
            armor = self.equipped["armor"]
            bonus += armor.defense + armor.enchantment

        # 指輪のボーナス
        for ring_slot in ["ring_left", "ring_right"]:
            ring = self.equipped[ring_slot]
            if isinstance(ring, Ring) and ring.effect == "protection":
                bonus += ring.bonus

        return bonus

    def get_equipped_item_name(self, slot: str) -> str:
        """
        装備スロットのアイテム名を取得

        Args:
        ----
            slot: 装備スロット名

        Returns:
        -------
            str: アイテム名（装備なしの場合は "None"）

        """
        item = self.equipped.get(slot)
        if not item:
            return "None"

        # ボーナス情報を含む表示名を生成
        if isinstance(item, Weapon):
            sign = "+" if item.attack >= 0 else ""
            enchant_text = f" {sign}{item.enchantment}" if item.enchantment != 0 else ""
            return f"{item.name} (ATK {sign}{item.attack}{enchant_text})"
        if isinstance(item, Armor):
            sign = "+" if item.defense >= 0 else ""
            enchant_text = f" {sign}{item.enchantment}" if item.enchantment != 0 else ""
            return f"{item.name} (DEF {sign}{item.defense}{enchant_text})"
        if isinstance(item, Ring):
            sign = "+" if item.bonus >= 0 else ""
            # 効果名をより読みやすく表示
            effect_display = {
                "protection": "DEF",
                "strength": "ATK",
                "sustain": "SUSTAIN",
                "search": "SEARCH",
                "see_invisible": "SEE INV",
                "regeneration": "REGEN",
            }.get(item.effect, item.effect.upper())
            return f"{item.name} ({effect_display} {sign}{item.bonus})"
        return item.name

    def get_equipped_weapon(self) -> Weapon | None:
        """
        装備中の武器を取得

        Returns
        -------
            Optional[Weapon]: 装備中の武器（ない場合はNone）

        """
        weapon = self.equipped.get("weapon")
        return weapon if isinstance(weapon, Weapon) else None

    def get_equipped_armor(self) -> Armor | None:
        """
        装備中の防具を取得

        Returns
        -------
            Optional[Armor]: 装備中の防具（ない場合はNone）

        """
        armor = self.equipped.get("armor")
        return armor if isinstance(armor, Armor) else None

    def is_equipped(self, item: Item) -> bool:
        """
        指定されたアイテムが装備中かどうかを確認

        Args:
        ----
            item: 確認するアイテム

        Returns:
        -------
            bool: 装備中の場合True

        """
        return item in self.equipped.values()

    def get_equipped_slot(self, item: Item) -> str | None:
        """
        指定されたアイテムの装備スロットを取得

        Args:
        ----
            item: 確認するアイテム

        Returns:
        -------
            str | None: 装備スロット名（装備されていない場合はNone）

        """
        for slot, equipped_item in self.equipped.items():
            if equipped_item is item:
                return slot
        return None

    def can_drop_item(self, item: Item) -> tuple[bool, str | None]:
        """
        アイテムがドロップ可能かどうかを判定

        Args:
        ----
            item: 確認するアイテム

        Returns:
        -------
            tuple[bool, str | None]: (ドロップ可能か, エラーメッセージ)

        """
        # 呪われた装備中のアイテムはドロップ不可
        if self.is_equipped(item) and hasattr(item, "cursed") and item.cursed:
            return False, f"You cannot drop the cursed {item.name}! You must first remove the curse."
        return True, None

    def drop_item(self, item: Item, drop_count: int = 1) -> tuple[bool, int, str]:
        """
        アイテムをドロップ（装備解除含む）

        Args:
        ----
            item: ドロップするアイテム
            drop_count: ドロップする数量

        Returns:
        -------
            tuple[bool, int, str]: (成功したか, 実際にドロップした数量, メッセージ)

        """
        # ドロップ可能かチェック
        can_drop, error_msg = self.can_drop_item(item)
        if not can_drop:
            return False, 0, error_msg

        # 装備中の場合は先に装備解除
        was_equipped = self.is_equipped(item)
        if was_equipped:
            slot = self.get_equipped_slot(item)
            if slot:
                self.equipped[slot] = None

        # アイテムを削除
        if item.stackable:
            actual_count = min(drop_count, item.stack_count)
            removed_count = self.remove_item(item, actual_count)
            if removed_count > 1:
                message = f"You drop {removed_count} {item.name}."
            else:
                message = f"You drop the {item.name}."
        else:
            removed_count = self.remove_item(item, 1)
            message = f"You drop the {item.name}."

        # 装備解除メッセージを前に追加
        if was_equipped:
            message = f"You first unequip the {item.name}. {message}"

        return True, removed_count, message
