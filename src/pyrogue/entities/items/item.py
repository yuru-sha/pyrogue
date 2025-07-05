"""Item module."""

from __future__ import annotations

from dataclasses import dataclass


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

    def __init__(self, x: int, y: int, name: str, effect: str):
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

    def apply_effect(self, target: object) -> bool:
        """巻物の効果を適用する"""
        from pyrogue.entities.actors.player import Player
        
        if not isinstance(target, Player):
            return False
            
        if self.effect == "identify":
            # 現在は常に識別済みなので効果なし
            return True
        elif self.effect == "light":
            # 現在は視界システムがないので効果なし
            return True
        elif self.effect == "remove_curse":
            # 呪いシステムがないので効果なし
            return True
        elif self.effect == "enchant_weapon":
            # 武器を強化
            weapon = target.inventory.get_equipped_weapon()
            if weapon:
                weapon.attack += 1
                return True
            return False
        elif self.effect == "enchant_armor":
            # 防具を強化
            armor = target.inventory.get_equipped_armor()
            if armor:
                armor.defense += 1
                return True
            return False
        elif self.effect == "teleport":
            # テレポートはゲームエンジンで処理する必要がある
            return True
        elif self.effect == "magic_mapping":
            # マップ表示はゲームエンジンで処理する必要がある
            return True
        
        return False


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
            identified=True,
        )
        self.effect = effect
        self.power = power

    def use(self) -> str:
        """薬を使用した時のメッセージを返す"""
        return f"You drink {self.name}."

    def apply_effect(self, target: object) -> bool:
        """薬の効果を適用する"""
        from pyrogue.entities.actors.player import Player
        
        if not isinstance(target, Player):
            return False
            
        if self.effect == "healing":
            target.heal(self.power)
            return True
        elif self.effect == "extra_healing":
            target.heal(self.power)
            return True
        elif self.effect == "strength":
            # 一時的な攻撃力上昇は現在未実装なので、基本攻撃力を上げる
            target.attack += self.power
            return True
        elif self.effect == "restore_strength":
            # 攻撃力を初期値に戻す（レベルボーナス含む）
            target.attack = max(5 + (target.level - 1) * 2, target.attack)
            return True
        elif self.effect == "haste_self":
            # 現在はメッセージのみ（実装は後で）
            return True
        elif self.effect == "see_invisible":
            # 現在はメッセージのみ（実装は後で）
            return True
        elif self.effect == "poison":
            # 毒ポーション（ダメージを与える）
            target.take_damage(self.power)
            return True
        
        return False


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
            identified=True,
        )
        self.nutrition = nutrition

    def use(self) -> str:
        """食料を使用した時のメッセージを返す"""
        return f"You eat {self.name}."

    def apply_effect(self, target: object) -> bool:
        """食料の効果を適用する"""
        from pyrogue.entities.actors.player import Player
        
        if not isinstance(target, Player):
            return False
            
        # 満腹度を回復
        target.eat_food(self.nutrition // 36)  # 900 -> 25, 600 -> 16
        
        # 食料によってはHPも少し回復
        if self.nutrition >= 900:  # Food Ration
            target.heal(1)
        
        return True


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
