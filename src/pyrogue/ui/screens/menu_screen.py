"""Menu screen module."""
from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
import tcod.console
import tcod.event

from pyrogue.core.game_states import GameStates

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine

class MenuScreen:
    """Menu screen class."""

    def __init__(self, console: tcod.console.Console, engine: Engine):
        self.console = console
        self.engine = engine
        self.menu_selection = 0
        self.menu_options = ["New Game", "Quit"]

    def update_console(self, console: tcod.console.Console) -> None:
        """コンソールの更新"""
        self.console = console

    def render(self) -> None:
        """Render the menu screen."""
        self.console.clear()

        # タイトルを表示
        title = "PyRogue"
        title_y = self.console.height // 4
        self.console.print(
            x=(self.console.width - len(title)) // 2,
            y=title_y,
            string=title
        )

        # メニューオプションを表示
        menu_start_y = title_y + 4
        for i, option in enumerate(self.menu_options):
            text = f"> {option}" if i == self.menu_selection else f"  {option}"
            self.console.print(
                x=(self.console.width - len(text)) // 2,
                y=menu_start_y + i * 2,
                string=text
            )

    def handle_input(self, key: tcod.event.KeyDown) -> GameStates | None:
        """入力処理"""
        if key.sym == tcod.event.KeySym.UP:
            self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
        elif key.sym == tcod.event.KeySym.DOWN:
            self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
        elif key.sym == tcod.event.KeySym.RETURN:
            if self.menu_options[self.menu_selection] == "New Game":
                self.engine.new_game()
                return GameStates.PLAYERS_TURN
            if self.menu_options[self.menu_selection] == "Continue":
                return GameStates.PLAYERS_TURN
            if self.menu_options[self.menu_selection] == "Quit":
                return GameStates.EXIT

        return None
