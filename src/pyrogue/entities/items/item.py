"""Item module."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Optional

@dataclass
class Item:
    """アイテムの基本クラス"""
    x: int
    y: int
    name: str
    char: str
    color: Tuple[int, int, int]
    stackable: bool = False  # 重ね合わせ可能か
    identified: bool = True  # 識別済みか（このゲームでは常にTrue）
    stack_count: int = 1  # スタック数

    def pick_up(self) -> str:
        """アイテムを拾った時のメッセージを返す"""
        return f"You pick up {self.name}."

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
            identified=True
        )
        self.attack_bonus = attack_bonus

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
            identified=True
        )
        self.defense_bonus = defense_bonus

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
            identified=True
        )
        self.effect = effect
        self.bonus = bonus

class Scroll(Item):
    """巻物クラス"""
    def __init__(self, x: int, y: int, name: str, effect: str):
        super().__init__(
            x=x,
            y=y,
            name=name,
            char="?",
            color=(255, 255, 255),  # 白色
            stackable=True,
            identified=True
        )
        self.effect = effect

    def use(self) -> str:
        """巻物を使用した時のメッセージを返す"""
        return f"You read {self.name}."

class Potion(Item):
    """薬クラス"""
    def __init__(self, x: int, y: int, name: str, effect: str, power: int):
        super().__init__(
            x=x,
            y=y,
            name=name,
            char="!",
            color=(255, 0, 255),  # マゼンタ
            stackable=True,
            identified=True
        )
        self.effect = effect
        self.power = power

    def use(self) -> str:
        """薬を使用した時のメッセージを返す"""
        return f"You drink {self.name}."

class Food(Item):
    """食料クラス"""
    def __init__(self, x: int, y: int, name: str, nutrition: int):
        super().__init__(
            x=x,
            y=y,
            name=name,
            char="%",
            color=(139, 69, 19),  # 茶色
            stackable=True,
            identified=True
        )
        self.nutrition = nutrition

    def use(self) -> str:
        """食料を使用した時のメッセージを返す"""
        return f"You eat {self.name}."

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
            identified=True
        )
        self.amount = amount

    def pick_up(self) -> str:
        return f"You pick up {self.amount} gold pieces." 