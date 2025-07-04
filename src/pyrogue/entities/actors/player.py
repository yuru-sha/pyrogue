"""Player module."""

from dataclasses import dataclass

from pyrogue.entities.actors.inventory import Inventory
from pyrogue.entities.items.item import (
    Armor,
    Food,
    Gold,
    Item,
    Potion,
    Ring,
    Scroll,
    Weapon,
)


@dataclass
class Player:
    """プレイヤーを表すクラス"""

    x: int = 0
    y: int = 0
    hp: int = 20
    max_hp: int = 20
    attack: int = 5
    defense: int = 3
    level: int = 1
    exp: int = 0
    hunger: int = 100  # 満腹度（100が最大）
    gold: int = 0

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.inventory = Inventory()
        self.gold = 0

    def move(self, dx: int, dy: int) -> None:
        """指定した方向に移動"""
        self.x += dx
        self.y += dy

    def take_damage(self, amount: int) -> None:
        """ダメージを受ける"""
        self.hp = max(0, self.hp - max(0, amount - self.defense))

    def heal(self, amount: int) -> None:
        """HPを回復"""
        self.hp = min(self.max_hp, self.hp + amount)

    def gain_exp(self, amount: int) -> bool:
        """
        経験値を獲得

        Returns:
            bool: レベルアップした場合はTrue

        """
        self.exp += amount
        if self.exp >= self.level * 100:  # 簡単な経験値テーブル
            self.level_up()
            return True
        return False

    def level_up(self) -> None:
        """レベルアップ時の処理"""
        self.level += 1
        self.max_hp += 5
        self.hp = self.max_hp
        self.attack += 2
        self.defense += 1
        self.exp = 0  # 経験値リセット

    def consume_food(self, amount: int = 1) -> None:
        """食料を消費（満腹度が減少）"""
        self.hunger = max(0, self.hunger - amount)

    def eat_food(self, amount: int = 25) -> None:
        """食料を食べる（満腹度が回復）"""
        self.hunger = min(100, self.hunger + amount)

    def get_attack(self) -> int:
        """
        攻撃力を計算

        Returns:
            int: 攻撃力

        """
        base_attack = 5  # 基本攻撃力
        bonus = self.inventory.get_attack_bonus()
        return base_attack + bonus

    def get_defense(self) -> int:
        """
        防御力を計算

        Returns:
            int: 防御力

        """
        base_defense = 2  # 基本防御力
        bonus = self.inventory.get_defense_bonus()
        return base_defense + bonus

    def equip_item(self, item: Item) -> Item | None:
        """
        アイテムを装備

        Args:
            item: 装備するアイテム

        Returns:
            Optional[Item]: 外したアイテム（ある場合）

        """
        if isinstance(item, (Weapon, Armor, Ring)):
            old_item = self.inventory.equip(item)
            self.inventory.remove_item(item)
            if old_item:
                self.inventory.add_item(old_item)
            return old_item
        return None

    def unequip_item(self, slot: str) -> Item | None:
        """
        装備を外す

        Args:
            slot: 装備スロット名

        Returns:
            Optional[Item]: 外したアイテム（ある場合）

        """
        item = self.inventory.unequip(slot)
        if item:
            self.inventory.add_item(item)
        return item

    def use_item(self, item: Item) -> bool:
        """
        アイテムを使用

        Args:
            item: 使用するアイテム

        Returns:
            bool: 使用に成功したかどうか

        """
        if isinstance(item, Scroll):
            # 巻物の効果を適用
            success = item.apply_effect(self)
            if success:
                self.inventory.remove_item(item)
            return success

        if isinstance(item, Potion):
            # 薬の効果を適用
            success = item.apply_effect(self)
            if success:
                self.inventory.remove_item(item)
            return success

        if isinstance(item, Food):
            # 食料を消費
            self.hunger = min(100, self.hunger + item.nutrition)
            self.inventory.remove_item(item)
            return True

        if isinstance(item, Gold):
            # 金貨を獲得
            self.gold += item.amount
            self.inventory.remove_item(item)
            return True

        return False

    def get_status_text(self) -> str:
        """
        ステータス表示用のテキストを取得

        Returns:
            str: ステータステキスト

        """
        weapon = self.inventory.get_equipped_item_name("weapon")
        armor = self.inventory.get_equipped_item_name("armor")
        ring_l = self.inventory.get_equipped_item_name("ring_left")
        ring_r = self.inventory.get_equipped_item_name("ring_right")

        return (
            f"Lv:{self.level} HP:{self.hp}/{self.max_hp} "
            f"Atk:{self.get_attack()} Def:{self.get_defense()} "
            f"Hunger:{self.hunger}% Exp:{self.exp} Gold:{self.gold}\n"
            f"Weap:{weapon} Armor:{armor} Ring(L):{ring_l} Ring(R):{ring_r}"
        )
