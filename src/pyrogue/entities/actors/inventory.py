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

    def remove_item(self, item: Item) -> None:
        """
        アイテムを削除

        Args:
        ----
            item: 削除するアイテム

        """
        if item in self.items:
            self.items.remove(item)

            # 装備中のアイテムの場合は装備スロットもクリア
            for slot, equipped_item in self.equipped.items():
                if equipped_item is item:
                    self.equipped[slot] = None

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
                old_item = self.equipped["ring_left"]
                self.equipped["ring_left"] = item
                return old_item
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
            if isinstance(ring, Ring) and ring.effect == "attack":
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
            if isinstance(ring, Ring) and ring.effect == "defense":
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
        return item.name if item else "None"

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
