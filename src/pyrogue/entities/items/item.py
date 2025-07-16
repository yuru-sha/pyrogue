"""Item module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogue.entities.items.effects import Effect, EffectContext
    from pyrogue.entities.items.identification import ItemIdentification


@dataclass
class Item:
    """アイテムの基本クラス"""

    x: int
    y: int
    name: str
    char: str
    color: tuple[int, int, int]
    stackable: bool = False  # 重ね合わせ可能か
    identified: bool = True  # 識別済みか
    item_type: str = "ITEM"  # アイテムタイプ（識別システム用）
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

    def get_display_name(self, identification: ItemIdentification) -> str:
        """識別状態に応じた表示名を取得"""
        return identification.get_display_name(self.name, self.item_type)


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
            item_type="WEAPON",
        )
        self.attack = attack_bonus
        self.enchantment = 0  # 強化レベル

    def pick_up(self) -> str:
        """武器を拾った時のメッセージ"""
        sign = "+" if self.attack >= 0 else ""
        return f"You pick up the {self.name} (ATK {sign}{self.attack})."


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
            item_type="ARMOR",
        )
        self.defense = defense_bonus
        self.enchantment = 0  # 強化レベル

    def pick_up(self) -> str:
        """防具を拾った時のメッセージ"""
        sign = "+" if self.defense >= 0 else ""
        return f"You pick up the {self.name} (DEF {sign}{self.defense})."


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
            identified=False,  # 指輪は未識別
            item_type="RING",
        )
        self.effect = effect
        self.bonus = bonus

    def pick_up(self) -> str:
        """指輪を拾った時のメッセージ"""
        sign = "+" if self.bonus >= 0 else ""
        # 効果名をより読みやすく表示
        effect_display = {
            "protection": "DEF",
            "strength": "ATK",
            "sustain": "SUSTAIN",
            "search": "SEARCH",
            "see_invisible": "SEE INV",
            "regeneration": "REGEN",
        }.get(self.effect, self.effect.upper())
        return f"You pick up the {self.name} ({effect_display} {sign}{self.bonus})."


class Scroll(Item):
    """巻物クラス"""

    def __init__(self, x: int, y: int, name: str, effect: Effect):
        super().__init__(
            x=x,
            y=y,
            name=name,
            char="?",
            color=(255, 255, 255),  # 白色
            stackable=True,
            identified=False,  # 巻物は未識別
            item_type="SCROLL",
        )
        self.effect = effect

    def use(self) -> str:
        """巻物を使用した時のメッセージを返す"""
        return f"You read {self.name}."

    def apply_effect(self, context: EffectContext) -> bool:
        """巻物の効果を適用する"""
        return self.effect.apply(context)


class Potion(Item):
    """薬クラス"""

    def __init__(self, x: int, y: int, name: str, effect: Effect):
        super().__init__(
            x=x,
            y=y,
            name=name,
            char="!",
            color=(255, 0, 255),  # マゼンタ
            stackable=True,
            identified=False,  # ポーションは未識別
            item_type="POTION",
        )
        self.effect = effect

    def use(self) -> str:
        """薬を使用した時のメッセージを返す"""
        return f"You drink {self.name}."

    def apply_effect(self, context: EffectContext) -> bool:
        """薬の効果を適用する"""
        return self.effect.apply(context)


class Food(Item):
    """食料クラス"""

    def __init__(self, x: int, y: int, name: str, effect: Effect):
        super().__init__(
            x=x,
            y=y,
            name=name,
            char="%",
            color=(139, 69, 19),  # 茶色
            stackable=True,
            identified=True,
            item_type="FOOD",
        )
        self.effect = effect

    def use(self) -> str:
        """食料を使用した時のメッセージを返す"""
        return f"You eat {self.name}."

    def apply_effect(self, context: EffectContext) -> bool:
        """食料の効果を適用する"""
        return self.effect.apply(context)


class Wand(Item):
    """ワンドクラス"""

    def __init__(self, x: int, y: int, name: str, effect: Effect, charges: int):
        super().__init__(
            x=x,
            y=y,
            name=name,
            char="/",
            color=(139, 69, 19),  # 茶色
            stackable=False,
            identified=False,  # ワンドは未識別
            item_type="WAND",
        )
        self.effect = effect
        self.charges = charges
        self.max_charges = charges  # 最大チャージ数を記録

    def use(self) -> str:
        """ワンドを使用した時のメッセージを返す"""
        return f"You zap {self.name}."

    def apply_effect(self, context: EffectContext, direction: tuple[int, int]) -> bool:
        """ワンドの効果を適用する"""
        if self.charges <= 0:
            return False

        # チャージを消費
        self.charges -= 1

        # 効果を適用（方向情報を渡す）
        return self.effect.apply(context, direction=direction)

    def has_charges(self) -> bool:
        """チャージが残っているかチェック"""
        return self.charges > 0

    def get_charges_info(self) -> str:
        """チャージ情報を取得"""
        if self.identified:
            return f"({self.charges}/{self.max_charges} charges)"
        else:
            return ""


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
            item_type="GOLD",
        )
        self.amount = amount
        self.item_type = "GOLD"  # ゴールドタイプを明示的に設定

    def pick_up(self) -> str:
        return f"You pick up {self.amount} gold pieces."
