"""
魔法システムモジュール。

このモジュールは、プレイヤーが使用できる魔法の定義と
魔法詠唱システムを提供します。

Example:
-------
    >>> magic_missile = MagicMissile()
    >>> success = magic_missile.cast(context, target_pos)
    >>> heal = Heal()
    >>> heal.cast(context)

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyrogue.entities.items.effects import EffectContext

from pyrogue.entities.actors.status_effects import PoisonEffect


class Spell(ABC):
    """
    魔法の基底クラス。

    すべての魔法が共通して持つ属性と機能を定義します。

    Attributes
    ----------
        name: 魔法の名前
        description: 魔法の説明
        mp_cost: MP消費量
        spell_level: 魔法のレベル（1-9）
        is_offensive: 攻撃魔法かどうか

    """

    def __init__(
        self,
        name: str,
        description: str,
        mp_cost: int,
        spell_level: int = 1,
        is_offensive: bool = False,
    ) -> None:
        """
        魔法を初期化。

        Args:
        ----
            name: 魔法の名前
            description: 魔法の説明
            mp_cost: MP消費量
            spell_level: 魔法のレベル
            is_offensive: 攻撃魔法かどうか

        """
        self.name = name
        self.description = description
        self.mp_cost = mp_cost
        self.spell_level = spell_level
        self.is_offensive = is_offensive

    def can_cast(self, context: EffectContext) -> bool:
        """
        魔法を詠唱できるかどうかを判定。

        Args:
        ----
            context: 効果適用のためのコンテキスト

        Returns:
        -------
            詠唱可能な場合はTrue、不可能な場合はFalse

        """
        return context.player.has_enough_mp(self.mp_cost)

    @abstractmethod
    def cast(self, context: EffectContext, **kwargs: Any) -> bool:
        """
        魔法を詠唱して効果を発動。

        Args:
        ----
            context: 効果適用のためのコンテキスト
            **kwargs: 魔法固有のパラメータ

        Returns:
        -------
            魔法の詠唱と効果適用に成功した場合はTrue、失敗した場合はFalse

        """

    def _consume_mp(self, context: EffectContext) -> bool:
        """
        MPを消費する。

        Args:
        ----
            context: 効果適用のためのコンテキスト

        Returns:
        -------
            MP消費に成功した場合はTrue、失敗した場合はFalse

        """
        return context.player.spend_mp(self.mp_cost)


class MagicMissile(Spell):
    """
    マジックミサイル。

    確実に命中する魔法の矢です。
    距離に関係なく対象にダメージを与えます。

    """

    def __init__(self, damage: int = 8) -> None:
        """
        マジックミサイルを初期化。

        Args:
        ----
            damage: 与えるダメージ量

        """
        super().__init__(
            name="Magic Missile",
            description=f"A magical projectile that deals {damage} damage",
            mp_cost=3,
            spell_level=1,
            is_offensive=True,
        )
        self.damage = damage

    def cast(
        self, context: EffectContext, target_pos: tuple[int, int] | None = None
    ) -> bool:
        """
        マジックミサイルを詠唱。

        Args:
        ----
            context: 効果適用のためのコンテキスト
            target_pos: ターゲット位置 (x, y)

        Returns:
        -------
            詠唱に成功した場合はTrue、失敗した場合はFalse

        """
        if not self.can_cast(context):
            context.add_message("You don't have enough MP!")
            return False

        if not target_pos:
            context.add_message("You need to specify a target!")
            return False

        # MPを消費
        if not self._consume_mp(context):
            return False

        # ターゲット位置のモンスターを確認
        current_floor = context.dungeon
        target_x, target_y = target_pos

        # 射程制限（視界内）
        player = context.player
        distance = ((player.x - target_x) ** 2 + (player.y - target_y) ** 2) ** 0.5
        if distance > player.light_radius:
            context.add_message("The target is too far away!")
            return False

        # モンスターを検索
        from pyrogue.core.game_logic import GameLogic

        if isinstance(context, GameLogic):
            current_floor_data = context.dungeon_manager.get_current_floor_data()
            monster = current_floor_data.monster_spawner.get_monster_at(
                target_x, target_y
            )

            if monster:
                # ダメージを与える（防御力無視）
                monster.hp = max(0, monster.hp - self.damage)
                context.add_message(
                    f"Your magic missile hits the {monster.name} for {self.damage} damage!"
                )

                # モンスターの死亡判定
                if monster.hp <= 0:
                    context.add_message(f"The {monster.name} dies!")
                    # 経験値獲得
                    context.player.gain_exp(monster.exp_value)
                    # モンスターを削除
                    current_floor_data.monster_spawner.monsters.remove(monster)

                return True
            context.add_message("Your magic missile hits nothing.")
            return True

        return False


class Heal(Spell):
    """
    ヒール。

    HPを回復する魔法です。
    自分にのみ使用可能です。

    """

    def __init__(self, heal_amount: int = 15) -> None:
        """
        ヒールを初期化。

        Args:
        ----
            heal_amount: 回復するHP量

        """
        super().__init__(
            name="Heal",
            description=f"Restores {heal_amount} HP",
            mp_cost=5,
            spell_level=1,
            is_offensive=False,
        )
        self.heal_amount = heal_amount

    def cast(self, context: EffectContext, **kwargs: Any) -> bool:
        """
        ヒールを詠唱。

        Args:
        ----
            context: 効果適用のためのコンテキスト
            **kwargs: 未使用

        Returns:
        -------
            詠唱に成功した場合はTrue、失敗した場合はFalse

        """
        if not self.can_cast(context):
            context.add_message("You don't have enough MP!")
            return False

        player = context.player

        if player.hp >= player.max_hp:
            context.add_message("You are already at full health!")
            return False

        # MPを消費
        if not self._consume_mp(context):
            return False

        # HPを回復
        old_hp = player.hp
        player.heal(self.heal_amount)
        actual_heal = player.hp - old_hp

        context.add_message(f"You feel better! (+{actual_heal} HP)")

        return True


class CurePoison(Spell):
    """
    毒回復。

    毒状態異常を解除する魔法です。

    """

    def __init__(self) -> None:
        """毒回復を初期化。"""
        super().__init__(
            name="Cure Poison",
            description="Removes poison status effect",
            mp_cost=4,
            spell_level=1,
            is_offensive=False,
        )

    def cast(self, context: EffectContext, **kwargs: Any) -> bool:
        """
        毒回復を詠唱。

        Args:
        ----
            context: 効果適用のためのコンテキスト
            **kwargs: 未使用

        Returns:
        -------
            詠唱に成功した場合はTrue、失敗した場合はFalse

        """
        if not self.can_cast(context):
            context.add_message("You don't have enough MP!")
            return False

        player = context.player

        if not player.is_poisoned():
            context.add_message("You are not poisoned!")
            return False

        # MPを消費
        if not self._consume_mp(context):
            return False

        # 毒状態を解除
        player.status_effects.remove_effect("Poison")
        context.add_message("You feel the poison leave your body!")

        return True


class PoisonBolt(Spell):
    """
    ポイズンボルト。

    対象に毒状態異常を与える攻撃魔法です。

    """

    def __init__(self, poison_duration: int = 6) -> None:
        """
        ポイズンボルトを初期化。

        Args:
        ----
            poison_duration: 毒の継続ターン数

        """
        super().__init__(
            name="Poison Bolt",
            description=f"Inflicts poison for {poison_duration} turns",
            mp_cost=6,
            spell_level=2,
            is_offensive=True,
        )
        self.poison_duration = poison_duration

    def cast(
        self, context: EffectContext, target_pos: tuple[int, int] | None = None
    ) -> bool:
        """
        ポイズンボルトを詠唱。

        Args:
        ----
            context: 効果適用のためのコンテキスト
            target_pos: ターゲット位置 (x, y)

        Returns:
        -------
            詠唱に成功した場合はTrue、失敗した場合はFalse

        """
        if not self.can_cast(context):
            context.add_message("You don't have enough MP!")
            return False

        if not target_pos:
            context.add_message("You need to specify a target!")
            return False

        # MPを消費
        if not self._consume_mp(context):
            return False

        # ターゲット位置のモンスターを確認
        target_x, target_y = target_pos
        player = context.player

        # 射程制限
        distance = ((player.x - target_x) ** 2 + (player.y - target_y) ** 2) ** 0.5
        if distance > player.light_radius:
            context.add_message("The target is too far away!")
            return False

        # モンスターを検索
        from pyrogue.core.game_logic import GameLogic

        if isinstance(context, GameLogic):
            current_floor_data = context.dungeon_manager.get_current_floor_data()
            monster = current_floor_data.monster_spawner.get_monster_at(
                target_x, target_y
            )

            if monster:
                # 毒状態異常を付与
                poison_effect = PoisonEffect(duration=self.poison_duration, damage=2)
                monster.status_effects.add_effect(poison_effect)

                context.add_message(
                    f"Your poison bolt hits the {monster.name}! It looks sick."
                )
                return True
            context.add_message("Your poison bolt hits nothing.")
            return True

        return False


class Spellbook:
    """
    魔法書クラス。

    プレイヤーが習得した魔法の管理と詠唱を行います。

    """

    def __init__(self) -> None:
        """魔法書を初期化。"""
        self.known_spells: list[Spell] = []
        self._initialize_basic_spells()

    def _initialize_basic_spells(self) -> None:
        """基本的な魔法を初期習得。"""
        # レベル1から使える基本魔法
        self.known_spells = [
            MagicMissile(),
            Heal(),
            CurePoison(),
        ]

    def add_spell(self, spell: Spell) -> None:
        """
        新しい魔法を習得。

        Args:
        ----
            spell: 習得する魔法

        """
        # 同じ名前の魔法は重複しない
        for known_spell in self.known_spells:
            if known_spell.name == spell.name:
                return

        self.known_spells.append(spell)

    def get_spell_by_name(self, name: str) -> Spell | None:
        """
        名前で魔法を検索。

        Args:
        ----
            name: 魔法の名前

        Returns:
        -------
            見つかった魔法、または None

        """
        for spell in self.known_spells:
            if spell.name.lower() == name.lower():
                return spell
        return None

    def get_castable_spells(self, context: EffectContext) -> list[Spell]:
        """
        詠唱可能な魔法のリストを取得。

        Args:
        ----
            context: 効果適用のためのコンテキスト

        Returns:
        -------
            詠唱可能な魔法のリスト

        """
        return [spell for spell in self.known_spells if spell.can_cast(context)]

    def cast_spell(self, spell_name: str, context: EffectContext, **kwargs) -> bool:
        """
        魔法を詠唱。

        Args:
        ----
            spell_name: 詠唱する魔法の名前
            context: 効果適用のためのコンテキスト
            **kwargs: 魔法固有のパラメータ

        Returns:
        -------
            詠唱に成功した場合はTrue、失敗した場合はFalse

        """
        spell = self.get_spell_by_name(spell_name)
        if not spell:
            context.add_message(
                f"You don't know the spell '{spell_name}'."
            )
            return False

        return spell.cast(context, **kwargs)

    def get_spell_list(self) -> list[str]:
        """
        習得済み魔法の名前リストを取得。

        Returns
        -------
            魔法名のリスト

        """
        return [spell.name for spell in self.known_spells]
