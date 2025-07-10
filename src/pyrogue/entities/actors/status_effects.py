"""
ステータス異常システムモジュール。

このモジュールは、プレイヤーやモンスターに適用される
継続的な状態異常（毒、麻痺、混乱など）を定義します。

Example:
    >>> poison = PoisonEffect(duration=5, damage=2)
    >>> poison.apply_per_turn(context)
    >>> confusion = ConfusionEffect(duration=3)
    >>> confusion.apply_per_turn(context)

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogue.entities.items.effects import EffectContext


@dataclass
class StatusEffect(ABC):
    """
    状態異常の基底クラス。

    継続的な効果を持つ状態異常（毒、麻痺、混乱など）の
    基本的な機能を定義します。

    Attributes:
        name: 状態異常の名前
        description: 状態異常の説明
        duration: 残り継続ターン数
        original_duration: 元の継続ターン数

    """

    name: str
    description: str
    duration: int
    original_duration: int

    def __init__(self, name: str, description: str, duration: int) -> None:
        """
        状態異常を初期化。

        Args:
            name: 状態異常の名前
            description: 状態異常の説明
            duration: 継続ターン数

        """
        self.name = name
        self.description = description
        self.duration = duration
        self.original_duration = duration

    @abstractmethod
    def apply_per_turn(self, context: EffectContext) -> bool:
        """
        ターンごとに状態異常の効果を適用。

        Args:
            context: 効果適用のためのコンテキスト

        Returns:
            状態異常が継続する場合はTrue、終了した場合はFalse

        """

    def update_duration(self) -> bool:
        """
        状態異常の継続ターン数を更新。

        Returns:
            状態異常が継続する場合はTrue、終了した場合はFalse

        """
        self.duration -= 1
        return self.duration > 0

    def is_active(self) -> bool:
        """状態異常が有効かどうかを判定。"""
        return self.duration > 0

    def get_display_name(self) -> str:
        """表示用の名前を取得。"""
        return f"{self.name}({self.duration})"


class PoisonEffect(StatusEffect):
    """
    毒状態効果。

    毎ターン固定ダメージを与える状態異常です。
    防御力を無視してダメージを与えます。

    """

    def __init__(self, duration: int = 5, damage: int = 2) -> None:
        """
        毒状態効果を初期化。

        Args:
            duration: 継続ターン数
            damage: 毎ターンのダメージ量

        """
        super().__init__(
            name="Poison",
            description=f"毒状態：毎ターン{damage}ダメージ",
            duration=duration
        )
        self.damage = damage

    def apply_per_turn(self, context: EffectContext) -> bool:
        """
        毒の効果を適用。

        Args:
            context: 効果適用のためのコンテキスト

        Returns:
            毒状態が継続する場合はTrue、終了した場合はFalse

        """
        # 防御力を無視した直接ダメージ
        context.player.hp = max(0, context.player.hp - self.damage)

        # メッセージを表示
        context.game_screen.message_log.append(
            f"毒によって{self.damage}ダメージを受けた！"
        )

        # 継続ターン数を更新
        return self.update_duration()


class ParalysisEffect(StatusEffect):
    """
    麻痺状態効果。

    行動を阻害する状態異常です。
    移動や攻撃を制限します。

    """

    def __init__(self, duration: int = 3) -> None:
        """
        麻痺状態効果を初期化。

        Args:
            duration: 継続ターン数

        """
        super().__init__(
            name="Paralysis",
            description="麻痺状態：行動不能",
            duration=duration
        )

    def apply_per_turn(self, context: EffectContext) -> bool:
        """
        麻痺の効果を適用。

        Args:
            context: 効果適用のためのコンテキスト

        Returns:
            麻痺状態が継続する場合はTrue、終了した場合はFalse

        """
        # 麻痺状態のメッセージを表示
        context.game_screen.message_log.append("麻痺して動けない！")

        # 継続ターン数を更新
        return self.update_duration()


class ConfusionEffect(StatusEffect):
    """
    混乱状態効果。

    行動をランダム化する状態異常です。
    意図した方向とは異なる方向に移動する可能性があります。

    """

    def __init__(self, duration: int = 4) -> None:
        """
        混乱状態効果を初期化。

        Args:
            duration: 継続ターン数

        """
        super().__init__(
            name="Confusion",
            description="混乱状態：行動がランダム化",
            duration=duration
        )

    def apply_per_turn(self, context: EffectContext) -> bool:
        """
        混乱の効果を適用。

        Args:
            context: 効果適用のためのコンテキスト

        Returns:
            混乱状態が継続する場合はTrue、終了した場合はFalse

        """
        # 混乱状態のメッセージを表示
        context.game_screen.message_log.append("混乱して正常な判断ができない！")

        # 継続ターン数を更新
        return self.update_duration()


class HallucinationEffect(StatusEffect):
    """
    幻覚状態効果。

    視覚混乱によってモンスターやアイテムの表示を
    ランダムな文字に変換する状態異常です。

    """

    def __init__(self, duration: int = 8) -> None:
        """
        幻覚状態効果を初期化。

        Args:
            duration: 継続ターン数

        """
        super().__init__(
            name="Hallucination",
            description="幻覚状態：視覚混乱",
            duration=duration
        )

    def apply_per_turn(self, context: EffectContext) -> bool:
        """
        幻覚の効果を適用。

        Args:
            context: 効果適用のためのコンテキスト

        Returns:
            幻覚状態が継続する場合はTrue、終了した場合はFalse

        """
        # 幻覚状態のメッセージを表示
        import random
        messages = [
            "Everything looks strange and distorted!",
            "Your vision blurs and shifts!",
            "Reality seems to waver before your eyes!",
            "The world around you seems unreal!"
        ]

        if hasattr(context, 'add_message'):
            context.add_message(random.choice(messages))
        elif hasattr(context, 'game_screen') and hasattr(context.game_screen, 'message_log'):
            context.game_screen.message_log.append(random.choice(messages))

        # 継続ターン数を更新
        return self.update_duration()


class StatusEffectManager:
    """
    状態異常の管理クラス。

    アクター（プレイヤー、モンスター）に適用されている
    状態異常の管理と更新を行います。

    """

    def __init__(self) -> None:
        """状態異常管理を初期化。"""
        self.effects: dict[str, StatusEffect] = {}

    def add_effect(self, effect: StatusEffect) -> None:
        """
        状態異常を追加。

        同じ名前の状態異常が既に存在する場合は、
        より長い継続時間を優先します。

        Args:
            effect: 追加する状態異常

        """
        if effect.name in self.effects:
            # 既存の効果より長い場合のみ更新
            if effect.duration > self.effects[effect.name].duration:
                self.effects[effect.name] = effect
        else:
            self.effects[effect.name] = effect

    def remove_effect(self, name: str) -> bool:
        """
        状態異常を削除。

        Args:
            name: 削除する状態異常の名前

        Returns:
            削除に成功した場合はTrue、指定された名前の状態異常が
            存在しない場合はFalse

        """
        if name in self.effects:
            del self.effects[name]
            return True
        return False

    def has_effect(self, name: str) -> bool:
        """
        指定された状態異常があるかどうかを判定。

        Args:
            name: 判定する状態異常の名前

        Returns:
            状態異常が存在する場合はTrue、そうでなければFalse

        """
        return name in self.effects and self.effects[name].is_active()

    def get_active_effects(self) -> list[StatusEffect]:
        """
        有効な状態異常のリストを取得。

        Returns:
            有効な状態異常のリスト

        """
        return [effect for effect in self.effects.values() if effect.is_active()]

    def update_effects(self, context: EffectContext) -> None:
        """
        すべての状態異常を更新。

        各状態異常の効果を適用し、継続ターン数を更新します。
        効果が切れた状態異常は自動的に削除されます。

        Args:
            context: 効果適用のためのコンテキスト

        """
        # 効果が切れた状態異常を記録
        expired_effects = []

        for name, effect in self.effects.items():
            if effect.is_active():
                # 状態異常の効果を適用
                if not effect.apply_per_turn(context):
                    expired_effects.append(name)
            else:
                expired_effects.append(name)

        # 効果が切れた状態異常を削除
        for name in expired_effects:
            self.remove_effect(name)

    def clear_all_effects(self) -> None:
        """すべての状態異常を削除。"""
        self.effects.clear()

    def get_effect_summary(self) -> str:
        """
        状態異常の要約を取得。

        Returns:
            状態異常の要約文字列

        """
        active_effects = self.get_active_effects()
        if not active_effects:
            return ""

        return ", ".join(effect.get_display_name() for effect in active_effects)
