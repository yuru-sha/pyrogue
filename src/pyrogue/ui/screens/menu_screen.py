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

        # ASCII アートタイトル
        title_art = [
            "██████╗ ██╗   ██╗██████╗  ██████╗  ██████╗ ██╗   ██╗███████╗",
            "██╔══██╗╚██╗ ██╔╝██╔══██╗██╔═══██╗██╔════╝ ██║   ██║██╔════╝",
            "██████╔╝ ╚████╔╝ ██████╔╝██║   ██║██║  ███╗██║   ██║█████╗  ",
            "██╔═══╝   ╚██╔╝  ██╔══██╗██║   ██║██║   ██║██║   ██║██╔══╝  ",
            "██║        ██║   ██║  ██║╚██████╔╝╚██████╔╝╚██████╔╝███████╗",
            "╚═╝        ╚═╝   ╚═╝  ╚═╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝",
        ]

        # タイトルアートが画面に収まるかチェック
        if self.console.width >= 60 and self.console.height >= 20:
            # 大きなタイトルを表示
            title_y = self.console.height // 6
            for i, line in enumerate(title_art):
                self.console.print(
                    (self.console.width - len(line)) // 2,
                    title_y + i,
                    line,
                    fg=(255, 215, 0),  # 金色
                )
        else:
            # 小さなタイトルを表示
            title = "PyRogue"
            title_y = self.console.height // 4
            self.console.print(
                (self.console.width - len(title)) // 2,
                title_y,
                title,
                fg=(255, 215, 0),  # 金色
            )

        # サブタイトル
        subtitle = "A Python Roguelike Adventure"
        subtitle_y = title_y + (len(title_art) if self.console.width >= 60 else 2)
        self.console.print(
            (self.console.width - len(subtitle)) // 2,
            subtitle_y,
            subtitle,
            fg=(150, 150, 150),
        )

        # メニューオプションを表示
        menu_start_y = subtitle_y + 3
        for i, option in enumerate(self.menu_options):
            text = f"> {option}" if i == self.menu_selection else f"  {option}"
            color = (255, 255, 255) if i == self.menu_selection else (150, 150, 150)
            self.console.print(
                (self.console.width - len(text)) // 2,
                menu_start_y + i * 2,
                text,
                fg=color,
            )

        # 操作説明
        help_text = "Use UP/DOWN arrows to navigate, ENTER to select, ESC to quit"
        self.console.print(
            (self.console.width - len(help_text)) // 2,
            self.console.height - 3,
            help_text,
            fg=(100, 100, 100),
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
