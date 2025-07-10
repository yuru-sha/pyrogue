"""
呪われたアイテム生成モジュール。

オリジナルRogue風の呪われたアイテムを生成します。
"""

from __future__ import annotations

import random
from typing import List

from pyrogue.entities.items.item import Armor, Ring, Weapon


class CursedItemGenerator:
    """呪われたアイテム生成器"""

    # 呪われた武器のテンプレート
    CURSED_WEAPONS = [
        ("Cursed Dagger", -1),
        ("Rusty Sword", -2),
        ("Broken Mace", -1),
        ("Dull Axe", -2),
        ("Bent Spear", -1),
    ]

    # 呪われた防具のテンプレート
    CURSED_ARMORS = [
        ("Cursed Leather", -1),
        ("Torn Robe", -1),
        ("Rusty Mail", -2),
        ("Cracked Shield", -1),
        ("Moth-eaten Cloak", -1),
    ]

    # 呪われた指輪のテンプレート
    CURSED_RINGS = [
        ("Ring of Weakness", "attack", -1),
        ("Ring of Vulnerability", "defense", -1),
        ("Ring of Misfortune", "attack", -2),
        ("Ring of Fragility", "defense", -2),
    ]

    @classmethod
    def generate_cursed_weapon(cls, x: int, y: int) -> Weapon:
        """
        呪われた武器を生成

        Args:
            x: 生成位置X
            y: 生成位置Y

        Returns:
            呪われた武器
        """
        name, attack_penalty = random.choice(cls.CURSED_WEAPONS)
        weapon = Weapon(x=x, y=y, name=name, attack_bonus=attack_penalty)
        weapon.cursed = True
        weapon.color = (128, 0, 128)  # 紫色で呪いを表現
        return weapon

    @classmethod
    def generate_cursed_armor(cls, x: int, y: int) -> Armor:
        """
        呪われた防具を生成

        Args:
            x: 生成位置X
            y: 生成位置Y

        Returns:
            呪われた防具
        """
        name, defense_penalty = random.choice(cls.CURSED_ARMORS)
        armor = Armor(x=x, y=y, name=name, defense_bonus=defense_penalty)
        armor.cursed = True
        armor.color = (128, 0, 128)  # 紫色で呪いを表現
        return armor

    @classmethod
    def generate_cursed_ring(cls, x: int, y: int) -> Ring:
        """
        呪われた指輪を生成

        Args:
            x: 生成位置X
            y: 生成位置Y

        Returns:
            呪われた指輪
        """
        name, effect, penalty = random.choice(cls.CURSED_RINGS)
        ring = Ring(x=x, y=y, name=name, effect=effect, bonus=penalty)
        ring.cursed = True
        ring.color = (128, 0, 128)  # 紫色で呪いを表現
        return ring

    @classmethod
    def curse_existing_item(cls, item) -> bool:
        """
        既存のアイテムを呪う

        Args:
            item: 呪うアイテム

        Returns:
            呪いの適用に成功したかどうか
        """
        if item.cursed:
            return False  # 既に呪われている

        if isinstance(item, Weapon):
            # 武器の攻撃力を-1～-3減少
            penalty = random.randint(1, 3)
            item.attack -= penalty
            item.name = f"Cursed {item.name}"
            item.cursed = True
            item.color = (128, 0, 128)
            return True

        elif isinstance(item, Armor):
            # 防具の防御力を-1～-2減少
            penalty = random.randint(1, 2)
            item.defense -= penalty
            item.name = f"Cursed {item.name}"
            item.cursed = True
            item.color = (128, 0, 128)
            return True

        elif isinstance(item, Ring):
            # 指輪のボーナスを-1～-2減少
            penalty = random.randint(1, 2)
            item.bonus -= penalty
            item.name = f"Cursed {item.name}"
            item.cursed = True
            item.color = (128, 0, 128)
            return True

        return False

    @classmethod
    def get_random_cursed_item(cls, x: int, y: int):
        """
        ランダムな呪われたアイテムを生成

        Args:
            x: 生成位置X
            y: 生成位置Y

        Returns:
            ランダムな呪われたアイテム
        """
        item_type = random.choice(["weapon", "armor", "ring"])

        if item_type == "weapon":
            return cls.generate_cursed_weapon(x, y)
        elif item_type == "armor":
            return cls.generate_cursed_armor(x, y)
        else:
            return cls.generate_cursed_ring(x, y)
