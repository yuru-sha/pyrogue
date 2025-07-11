"""
魔法スクリーンモジュール。

このモジュールは、魔法詠唱のメニューを表示し、
プレイヤーが魔法を選択して詠唱するためのUIを提供します。

Example:
-------
    >>> engine = Engine()
    >>> magic_screen = MagicScreen(engine)
    >>> magic_screen.render(console)

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
import tcod.console
import tcod.event

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine

from pyrogue.core.game_states import GameStates
from pyrogue.ui.screens.screen import Screen


class MagicScreen(Screen):
    """
    魔法詠唱メニュー表示画面。

    プレイヤーが習得した魔法を一覧表示し、
    魔法を選択して詠唱する機能を提供します。

    """

    def __init__(self, engine: Engine) -> None:
        """
        魔法スクリーンを初期化。

        Args:
        ----
            engine: メインゲームエンジンのインスタンス

        """
        super().__init__(engine)
        self.selected_index = 0
        self.require_target = False
        self.selected_spell = None

    def render(self, console: tcod.console.Console) -> None:
        """
        魔法メニューを描画。

        Args:
        ----
            console: 描画先のコンソール

        """
        # 画面をクリア
        console.clear()

        # タイトル
        console.print(
            x=2, y=1, string="Spellbook - Select a spell to cast", fg=tcod.color.yellow
        )

        # MPの表示
        player = self.engine.game_screen.game_logic.player
        console.print(
            x=2,
            y=3,
            string=f"MP: {player.mp}/{player.max_mp}",
            fg=tcod.color.light_cyan,
        )

        # 魔法一覧
        spells = player.spellbook.known_spells
        if not spells:
            console.print(
                x=2, y=5, string="You don't know any spells yet.", fg=tcod.color.gray
            )
            console.print(x=2, y=7, string="Press ESC to return.", fg=tcod.color.gray)
            return

        # 魔法リスト表示
        for i, spell in enumerate(spells):
            y = 5 + i

            # 選択中の魔法をハイライト
            if i == self.selected_index:
                console.print(x=1, y=y, string=">", fg=tcod.color.yellow)

            # 魔法名とMP消費量
            spell_text = f"{chr(ord('a') + i)}) {spell.name} (MP:{spell.mp_cost})"

            # MP不足の場合は暗い色で表示
            if player.mp < spell.mp_cost:
                color = tcod.color.dark_gray
            else:
                color = tcod.color.white

            console.print(x=3, y=y, string=spell_text, fg=color)

            # 魔法の説明
            console.print(
                x=5, y=y + 1, string=f"   {spell.description}", fg=tcod.color.light_gray
            )

        # 操作説明
        console.print(
            x=2,
            y=len(spells) * 2 + 7,
            string="Use arrow keys to select, Enter to cast, ESC to cancel",
            fg=tcod.color.gray,
        )

    def handle_key(self, event: tcod.event.KeyDown) -> None:
        """
        魔法選択メニューのキー入力処理。

        Args:
        ----
            event: キー入力イベント

        """
        player = self.engine.game_screen.game_logic.player
        spells = player.spellbook.known_spells

        if not spells:
            # 魔法を覚えていない場合はESCのみ受け付け
            if event.sym == tcod.event.KeySym.ESCAPE:
                self.engine.state = GameStates.PLAYERS_TURN
            return

        # ESCキーでキャンセル
        if event.sym == tcod.event.KeySym.ESCAPE:
            self.engine.state = GameStates.PLAYERS_TURN
            return

        # 上下キーで選択
        if event.sym == tcod.event.KeySym.UP:
            self.selected_index = (self.selected_index - 1) % len(spells)
            return

        if event.sym == tcod.event.KeySym.DOWN:
            self.selected_index = (self.selected_index + 1) % len(spells)
            return

        # ENTERキーで魔法詠唱
        if event.sym == tcod.event.KeySym.RETURN:
            selected_spell = spells[self.selected_index]

            # MP不足チェック
            if player.mp < selected_spell.mp_cost:
                self.engine.game_screen.game_logic.add_message(
                    "You don't have enough MP!"
                )
                return

            # 攻撃魔法の場合はターゲット選択へ
            if selected_spell.is_offensive:
                self.selected_spell = selected_spell
                self.engine.state = GameStates.TARGETING
                return

            # 補助魔法の場合は即座に詠唱
            success = selected_spell.cast(self.engine.game_screen.game_logic)
            if success:
                self.engine.state = GameStates.PLAYERS_TURN
                # ターンを経過させる
                self.engine.game_screen.game_logic.process_turn()
            return

        # 文字キーで直接選択
        if event.sym >= tcod.event.KeySym.a and event.sym <= tcod.event.KeySym.z:
            index = event.sym - tcod.event.KeySym.a
            if 0 <= index < len(spells):
                self.selected_index = index
                # 選択後、即座に詠唱処理
                selected_spell = spells[self.selected_index]

                # MP不足チェック
                if player.mp < selected_spell.mp_cost:
                    self.engine.game_screen.game_logic.add_message(
                        "You don't have enough MP!"
                    )
                    return

                # 攻撃魔法の場合はターゲット選択へ
                if selected_spell.is_offensive:
                    self.selected_spell = selected_spell
                    self.engine.state = GameStates.TARGETING
                    return

                # 補助魔法の場合は即座に詠唱
                success = selected_spell.cast(self.engine.game_screen.game_logic)
                if success:
                    self.engine.state = GameStates.PLAYERS_TURN
                    # ターンを経過させる
                    self.engine.game_screen.game_logic.process_turn()
                return

    def get_selected_spell(self) -> Spell | None:
        """選択中の魔法を取得（ターゲット選択用）"""
        return self.selected_spell
