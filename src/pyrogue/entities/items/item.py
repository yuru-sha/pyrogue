"""Item module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pyrogue.entities.items.effects import Effect, EffectContext


@dataclass
class Item:
    """アイテムの基本クラス"""

    x: int
    y: int
    name: str
    char: str
    color: tuple[int, int, int]
    stackable: bool = False  # 重ね合わせ可能か
    identified: bool = True  # 識別済みか（このゲームでは常にTrue）
    stack_count: int = 1  # スタック数
    cursed: bool = False  # 呪いフラグ

    def pick_up(self) -> str:
        """アイテムを拾った時のメッセージを返す"""
        if self.stackable and self.stack_count > 1:
            return f"You pick up {self.stack_count} {self.name}."
        return f"You pick up the {self.name}."

    def drop(self) -> str:
        """アイテムを落とした時のメッセージを返す"""
        if self.stackable and self.stack_count > 1:
            return f"You drop {self.stack_count} {self.name}."
        return f"You drop the {self.name}."


class Weapon(Item):
    """武器クラス"""

    def __init__(self, x: int, y: int, name: str, attack_bonus: int):
        super().__init__(
            x=x,
            y=y,
            name=name,
            char=")",
            color=(192, 192, 192),  # 銀色
            stackable=False,
            identified=True,
        )
        self.attack = attack_bonus
        self.enchantment = 0  # 強化レベル

    def pick_up(self) -> str:
        """武器を拾った時のメッセージ"""
        return f"You pick up the {self.name} (ATK +{self.attack})."


class Armor(Item):
    """防具クラス"""

    def __init__(self, x: int, y: int, name: str, defense_bonus: int):
        super().__init__(
            x=x,
            y=y,
            name=name,
            char="[",
            color=(192, 192, 192),  # 銀色
            stackable=False,
            identified=True,
        )
        self.defense = defense_bonus
        self.enchantment = 0  # 強化レベル

    def pick_up(self) -> str:
        """防具を拾った時のメッセージ"""
        return f"You pick up the {self.name} (DEF +{self.defense})."


class Ring(Item):
    """指輪クラス"""

    def __init__(self, x: int, y: int, name: str, effect: str, bonus: int):
        super().__init__(
            x=x,
            y=y,
            name=name,
            char="=",
            color=(255, 215, 0),  # 金色
            stackable=False,
            identified=True,
        )
        self.effect = effect
        self.bonus = bonus


class Scroll(Item):
    """巻物クラス"""

    def __init__(self, x: int, y: int, name: str, effect: "Effect"):
        super().__init__(
            x=x,
            y=y,
            name=name,
            char="?",
            color=(255, 255, 255),  # 白色
            stackable=True,
            identified=True,
        )
        self.effect = effect

    def use(self) -> str:
        """巻物を使用した時のメッセージを返す"""
        return f"You read {self.name}."

    def apply_effect(self, context: "EffectContext") -> bool:
        """巻物の効果を適用する"""
        return self.effect.apply(context)


class Potion(Item):
    """薬クラス"""

    def __init__(self, x: int, y: int, name: str, effect: "Effect"):
        super().__init__(
            x=x,
            y=y,
            name=name,
            char="!",
            color=(255, 0, 255),  # マゼンタ
            stackable=True,
            identified=True,
        )
        self.effect = effect

    def use(self) -> str:
        """薬を使用した時のメッセージを返す"""
        return f"You drink {self.name}."

    def apply_effect(self, context: "EffectContext") -> bool:
        """薬の効果を適用する"""
        return self.effect.apply(context)


class Food(Item):
    """食料クラス"""

    def __init__(self, x: int, y: int, name: str, effect: "Effect"):
        super().__init__(
            x=x,
            y=y,
            name=name,
            char="%",
            color=(139, 69, 19),  # 茶色
            stackable=True,
            identified=True,
        )
        self.effect = effect

    def use(self) -> str:
        """食料を使用した時のメッセージを返す"""
        return f"You eat {self.name}."

    def apply_effect(self, context: "EffectContext") -> bool:
        """食料の効果を適用する"""
        return self.effect.apply(context)


class Gold(Item):
    """金貨クラス"""

    def __init__(self, x: int, y: int, amount: int):
        super().__init__(
            x=x,
            y=y,
            name=f"{amount} gold pieces",
            char="$",
            color=(255, 215, 0),  # 金色
            stackable=True,
            identified=True,
        )
        self.amount = amount

    def pick_up(self) -> str:
        return f"You pick up {self.amount} gold pieces."
