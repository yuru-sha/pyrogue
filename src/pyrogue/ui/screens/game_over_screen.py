"""Game over screen module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
import tcod.console
import tcod.event

from pyrogue.core.game_states import GameStates

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine


class GameOverScreen:
    """Game over screen class."""

    def __init__(self, console: tcod.console.Console, engine: Engine):
        self.console = console
        self.engine = engine
        self.menu_selection = 0
        self.menu_options = ["Return to Menu", "Quit"]

        # プレイヤーの統計情報（ゲームオーバー時に設定される）
        self.player_stats = {}
        self.final_floor = 1
        self.cause_of_death = "Unknown"

    def update_console(self, console: tcod.console.Console) -> None:
        """コンソールの更新"""
        self.console = console

    def set_game_over_data(
        self, player_stats: dict, final_floor: int, cause_of_death: str = "Unknown"
    ) -> None:
        """ゲームオーバー時のデータを設定"""
        self.player_stats = player_stats.copy()
        self.final_floor = final_floor
        self.cause_of_death = cause_of_death

    def render(self) -> None:
        """Render the game over screen."""
        self.console.clear()

        # ゲームオーバータイトル
        title = "GAME OVER"
        title_y = self.console.height // 6
        self.console.print(
            (self.console.width - len(title)) // 2,
            title_y,
            title,
            fg=(255, 0, 0),  # 赤色
        )

        # 死因
        death_msg = f"You died: {self.cause_of_death}"
        self.console.print(
            (self.console.width - len(death_msg)) // 2,
            title_y + 2,
            death_msg,
            fg=(200, 200, 200),
        )

        # 統計情報
        stats_y = title_y + 5
        stats_info = [
            f"Final Level: {self.player_stats.get('level', 1)}",
            f"Final Floor: {self.final_floor}",
            f"Experience: {self.player_stats.get('exp', 0)}",
            f"Gold Collected: {self.player_stats.get('gold', 0)}",
        ]

        for i, stat in enumerate(stats_info):
            self.console.print(
                (self.console.width - len(stat)) // 2,
                stats_y + i,
                stat,
                fg=(150, 150, 150),
            )

        # メニューオプション
        menu_start_y = stats_y + len(stats_info) + 3
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
        help_text = "Use UP/DOWN arrows to navigate, ENTER to select"
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
            if self.menu_options[self.menu_selection] == "Return to Menu":
                return GameStates.MENU
            if self.menu_options[self.menu_selection] == "Quit":
                return GameStates.EXIT

        return None
