"""Wand selection screen module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
import tcod.event
from tcod.console import Console

from pyrogue.entities.items.wand import Wand
from pyrogue.ui.screens.screen import Screen

if TYPE_CHECKING:
    from pyrogue.ui.screens.game_screen import GameScreen


class WandSelectionScreen(Screen):
    """ワンド選択画面"""

    def __init__(self, game_screen: GameScreen) -> None:
        super().__init__(game_screen.engine)
        self.game_screen = game_screen
        self.selected_index = 0
        self.wands: list[Wand] = []
        self.selected_wand: Wand | None = None

    def setup(self) -> None:
        """画面セットアップ - ワンド一覧を取得"""
        self.wands = self._get_available_wands()
        self.selected_index = 0

    def _get_available_wands(self) -> list[Wand]:
        """
        プレイヤーが持っているワンドのリストを取得。

        Returns
        -------
            ワンドのリスト

        """
        player = self.game_screen.player
        return [item for item in player.inventory.items if hasattr(item, "item_type") and item.item_type == "WAND"]

    def render(self, console: Console) -> None:
        """
        画面を描画

        Args:
        ----
            console: 描画対象のコンソール

        """
        # 背景を塗りつぶし
        console.clear()

        # タイトルを描画
        console.print(1, 1, "Select a wand to zap:", (255, 255, 0))

        if not self.wands:
            console.print(1, 3, "You have no wands to zap.", (255, 255, 255))
            return

        # ワンド一覧を描画
        for i, wand in enumerate(self.wands):
            # インデックスを文字に変換（0=a, 1=b, ...）
            index_char = chr(ord("a") + i)

            # 選択中のワンドはハイライト
            fg = (255, 255, 255) if i != self.selected_index else (255, 255, 0)
            bg = (0, 0, 0) if i != self.selected_index else (64, 64, 64)

            # ワンドの表示名を取得
            player = self.game_screen.game_logic.player
            display_name = wand.get_display_name(player.identification)

            # チャージ情報を取得
            charges_info = wand.get_charges_info() if hasattr(wand, "get_charges_info") else ""

            wand_text = f"{index_char}) {display_name} {charges_info}"
            console.print(2, 3 + i, wand_text, fg, bg)

        # 操作説明を描画
        console.print(1, 3 + len(self.wands) + 2, "↑/↓: Select  Enter: Confirm  ESC: Cancel", (200, 200, 200))

    def handle_event(self, event: tcod.event.Event) -> bool:
        """
        イベントを処理

        Args:
        ----
            event: TCODイベント

        Returns:
        -------
            bool: イベントが処理された場合True

        """
        if isinstance(event, tcod.event.KeyDown):
            if not self.wands:
                # ワンドがない場合はESCで終了
                if event.sym == tcod.event.KeySym.ESCAPE:
                    self.game_screen.engine.state = self.game_screen.engine.last_state
                    return True
                return False

            # ↑/↓キーでワンド選択
            if event.sym == tcod.event.KeySym.UP:
                self.selected_index = (self.selected_index - 1) % len(self.wands)
                return True
            elif event.sym == tcod.event.KeySym.DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.wands)
                return True

            # Enterキーで確定
            elif event.sym == tcod.event.KeySym.RETURN:
                if 0 <= self.selected_index < len(self.wands):
                    self.selected_wand = self.wands[self.selected_index]
                    # 方向選択モードに移行
                    self.game_screen.input_handler.wand_direction_mode = True
                    self.game_screen.input_handler.selected_wand = self.selected_wand
                    self.game_screen.game_logic.add_message(f"Zap {self.selected_wand.name} in which direction?")
                    self.game_screen.engine.state = self.game_screen.engine.last_state
                return True

            # ESCキーでキャンセル
            elif event.sym == tcod.event.KeySym.ESCAPE:
                self.game_screen.game_logic.add_message("Cancelled.")
                self.game_screen.engine.state = self.game_screen.engine.last_state
                return True

        return False
