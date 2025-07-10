"""
トラップシステムモジュール。

このモジュールは、ダンジョン内に配置されるトラップの
基底クラスと具体的なトラップ実装を定義します。

Example:
    >>> pit_trap = PitTrap(x=10, y=5)
    >>> pit_trap.activate(player)
    >>> poison_trap = PoisonNeedleTrap(x=15, y=8)
    >>> poison_trap.reveal()

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogue.entities.items.effects import EffectContext

from pyrogue.entities.actors.status_effects import PoisonEffect


class Trap(ABC):
    """
    トラップの基底クラス。

    ダンジョン内に配置される隠れたトラップの基本的な
    機能と状態管理を定義します。

    Attributes:
        x: トラップのX座標
        y: トラップのY座標
        is_hidden: 隠蔽状態（Trueで隠れている）
        is_disarmed: 解除状態（Trueで無効化済み）
        char: 発見されたときの表示文字
        color: 表示色（RGB）
        name: トラップの名前

    """

    def __init__(
        self,
        x: int,
        y: int,
        is_hidden: bool = True,
        is_disarmed: bool = False
    ) -> None:
        """
        トラップを初期化。

        Args:
            x: トラップのX座標
            y: トラップのY座標
            is_hidden: 初期の隠蔽状態（デフォルト: True）
            is_disarmed: 初期の解除状態（デフォルト: False）

        """
        self.x = x
        self.y = y
        self.is_hidden = is_hidden
        self.is_disarmed = is_disarmed
        self.char: str = "^"
        self.color: tuple[int, int, int] = (255, 0, 0)
        self.name: str = "Trap"

    def reveal(self, context: "EffectContext" | None = None) -> None:
        """
        トラップを発見済み状態にする。

        Args:
            context: メッセージ表示用のコンテキスト

        """
        if self.is_hidden:
            self.is_hidden = False
            if context and context.game_screen:
                context.game_screen.message_log.append(f"You discovered a {self.name}!")

    def disarm(self, context: "EffectContext" | None = None) -> bool:
        """
        トラップを無効化する。

        Args:
            context: メッセージ表示用のコンテキスト

        Returns:
            解除に成功した場合はTrue、失敗した場合はFalse

        """
        if self.is_disarmed:
            if context and context.game_screen:
                context.game_screen.message_log.append("This trap is already disarmed.")
            return False

        if self.is_hidden:
            if context and context.game_screen:
                context.game_screen.message_log.append("You can't disarm a trap you can't see!")
            return False

        # 簡単な成功判定（将来的にはスキルベースに）
        import random
        success = random.random() < 0.7  # 70%の成功率

        if success:
            self.is_disarmed = True
            if context and context.game_screen:
                context.game_screen.message_log.append(f"You successfully disarmed the {self.name}!")
            return True
        else:
            if context and context.game_screen:
                context.game_screen.message_log.append(f"You failed to disarm the {self.name}!")
            # 失敗時にトラップが発動する可能性
            if random.random() < 0.3:  # 30%の確率で発動
                if context and context.game_screen:
                    context.game_screen.message_log.append("Your clumsy attempt triggers the trap!")
                self.activate(context)
            return False

    def is_active(self) -> bool:
        """
        トラップが有効（発動可能）かどうかを判定。

        Returns:
            有効な場合はTrue、無効な場合はFalse

        """
        return not self.is_disarmed

    def is_visible(self) -> bool:
        """
        トラップが見える状態かどうかを判定。

        Returns:
            見える場合はTrue、隠れている場合はFalse

        """
        return not self.is_hidden

    @abstractmethod
    def activate(self, context: "EffectContext") -> None:
        """
        トラップを発動させる。

        Args:
            context: 効果適用のためのコンテキスト

        """
        pass


class PitTrap(Trap):
    """
    落とし穴トラップ。

    踏むとダメージを受ける基本的なトラップです。
    発動時に固定ダメージを与えます。

    """

    def __init__(self, x: int, y: int, damage: int = 10) -> None:
        """
        落とし穴トラップを初期化。

        Args:
            x: トラップのX座標
            y: トラップのY座標
            damage: 与えるダメージ量

        """
        super().__init__(x, y)
        self.name = "Pit Trap"
        self.damage = damage
        self.char = "^"
        self.color = (139, 69, 19)  # 茶色

    def activate(self, context: "EffectContext") -> None:
        """
        落とし穴の効果を発動。

        Args:
            context: 効果適用のためのコンテキスト

        """
        player = context.player

        # ダメージを与える（防御力を考慮）
        actual_damage = max(1, self.damage - player.get_defense())
        player.hp = max(0, player.hp - actual_damage)

        # メッセージを表示
        context.game_screen.message_log.append(
            f"You fall into a pit! You take {actual_damage} damage!"
        )

        # トラップを発見状態にする
        self.reveal()


class PoisonNeedleTrap(Trap):
    """
    毒針トラップ。

    踏むと毒状態異常になるトラップです。
    既存の毒エフェクトシステムと連携します。

    """

    def __init__(self, x: int, y: int, poison_duration: int = 8) -> None:
        """
        毒針トラップを初期化。

        Args:
            x: トラップのX座標
            y: トラップのY座標
            poison_duration: 毒の継続ターン数

        """
        super().__init__(x, y)
        self.name = "Poison Needle Trap"
        self.poison_duration = poison_duration
        self.char = "^"
        self.color = (0, 255, 0)  # 緑色

    def activate(self, context: "EffectContext") -> None:
        """
        毒針の効果を発動。

        Args:
            context: 効果適用のためのコンテキスト

        """
        player = context.player

        # 毒状態異常を適用
        poison_effect = PoisonEffect(duration=self.poison_duration, damage=2)
        player.status_effects.add_effect(poison_effect)

        # メッセージを表示
        context.game_screen.message_log.append(
            "You step on a poison needle! You feel sick..."
        )

        # トラップを発見状態にする
        self.reveal()


class TeleportTrap(Trap):
    """
    テレポートトラップ。

    踏むとランダムな場所にテレポートされるトラップです。
    既存のテレポートエフェクトシステムと連携します。

    """

    def __init__(self, x: int, y: int) -> None:
        """
        テレポートトラップを初期化。

        Args:
            x: トラップのX座標
            y: トラップのY座標

        """
        super().__init__(x, y)
        self.name = "Teleport Trap"
        self.char = "^"
        self.color = (255, 0, 255)  # マゼンタ色

    def activate(self, context: "EffectContext") -> None:
        """
        テレポートの効果を発動。

        Args:
            context: 効果適用のためのコンテキスト

        """
        # 既存のテレポートエフェクトを使用
        from pyrogue.entities.items.effects import TeleportEffect

        teleport_effect = TeleportEffect()
        success = teleport_effect.apply(context)

        if success:
            # メッセージを表示
            context.game_screen.message_log.append(
                "You step on a strange rune and are whisked away!"
            )

        # トラップを発見状態にする
        self.reveal()


class TrapManager:
    """
    トラップの管理クラス。

    ダンジョン内のすべてのトラップの管理、
    検出、発動処理を統合的に行います。

    """

    def __init__(self) -> None:
        """トラップマネージャーを初期化。"""
        self.traps: list[Trap] = []

    def add_trap(self, trap: Trap) -> None:
        """
        トラップを追加。

        Args:
            trap: 追加するトラップ

        """
        self.traps.append(trap)

    def remove_trap(self, trap: Trap) -> bool:
        """
        トラップを削除。

        Args:
            trap: 削除するトラップ

        Returns:
            削除に成功した場合はTrue、トラップが存在しない場合はFalse

        """
        if trap in self.traps:
            self.traps.remove(trap)
            return True
        return False

    def get_trap_at(self, x: int, y: int) -> Trap | None:
        """
        指定された位置にあるトラップを取得。

        Args:
            x: X座標
            y: Y座標

        Returns:
            トラップが存在する場合はTrapオブジェクト、
            存在しない場合はNone

        """
        for trap in self.traps:
            if trap.x == x and trap.y == y and trap.is_active():
                return trap
        return None

    def get_visible_traps(self) -> list[Trap]:
        """
        発見済みで有効なトラップのリストを取得。

        Returns:
            発見済みで有効なトラップのリスト

        """
        return [trap for trap in self.traps if trap.is_visible() and trap.is_active()]

    def trigger_trap_at(self, x: int, y: int, context: "EffectContext") -> bool:
        """
        指定された位置のトラップを発動。

        Args:
            x: X座標
            y: Y座標
            context: 効果適用のためのコンテキスト

        Returns:
            トラップが発動した場合はTrue、なかった場合はFalse

        """
        trap = self.get_trap_at(x, y)
        if trap and trap.is_hidden:
            trap.activate(context)
            return True
        return False

    def clear_all_traps(self) -> None:
        """すべてのトラップを削除。"""
        self.traps.clear()

    def get_trap_count(self) -> int:
        """
        有効なトラップの総数を取得。

        Returns:
            有効なトラップの数

        """
        return len([trap for trap in self.traps if trap.is_active()])
