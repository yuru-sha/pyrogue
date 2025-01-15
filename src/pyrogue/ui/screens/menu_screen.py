"""Menu screen module."""
from __future__ import annotations

import tcod
import tcod.console
import tcod.event

from pyrogue.utils import game_logger

class MenuScreen:
    """Menu screen class."""

    def __init__(self, console: tcod.console.Console):
        self.console = console
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

    def handle_keydown(self, event: tcod.event.KeyDown) -> bool:
        """Handle keyboard input.
        
        Returns:
            bool: False if the game should quit, True otherwise.
        """
        if event.sym == tcod.event.KeySym.UP:
            self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
            game_logger.debug("Menu selection changed", extra={"selection": self.menu_options[self.menu_selection]})
        elif event.sym == tcod.event.KeySym.DOWN:
            self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
            game_logger.debug("Menu selection changed", extra={"selection": self.menu_options[self.menu_selection]})
        elif event.sym == tcod.event.KeySym.RETURN:
            if self.menu_selection == 0:  # New Game
                game_logger.debug("New game selected")
                return True
            elif self.menu_selection == 1:  # Quit
                game_logger.debug("Quit selected")
                return False
        return True 