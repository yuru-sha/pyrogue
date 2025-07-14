"""Victory screen module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
import tcod.console
import tcod.event

from pyrogue.core.game_states import GameStates

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine


class VictoryScreen:
    """Victory screen class."""

    def __init__(self, console: tcod.console.Console, engine: Engine) -> None:
        self.console = console
        self.engine = engine
        self.menu_selection = 0
        self.menu_options = ["Return to Menu", "Quit"]

        # プレイヤーの統計情報（勝利時に設定される）
        self.player_stats = {}
        self.final_floor = 26
        self.final_score = 0

    def update_console(self, console: tcod.console.Console) -> None:
        """コンソールの更新"""
        self.console = console

    def set_victory_data(self, player_stats: dict, final_floor: int, final_score: int) -> None:
        """勝利時のデータを設定"""
        self.player_stats = player_stats.copy()
        self.final_floor = final_floor
        self.final_score = final_score

    def calculate_score(self) -> int:
        """最終スコアを計算"""
        if self.final_score > 0:
            return self.final_score

        # スコア計算式
        level_bonus = self.player_stats.get("level", 1) * 100
        gold_bonus = self.player_stats.get("gold", 0) * 2
        floor_bonus = self.final_floor * 50
        hp_bonus = self.player_stats.get("hp", 0) * 10

        self.final_score = level_bonus + gold_bonus + floor_bonus + hp_bonus
        return self.final_score

    def render(self) -> None:
        """Render the victory screen."""
        self.console.clear()

        # 勝利タイトル
        title = "VICTORY!"
        subtitle = "You have retrieved the Amulet of Yendor!"
        title_y = self.console.height // 6

        self.console.print(
            (self.console.width - len(title)) // 2,
            title_y,
            title,
            fg=(255, 215, 0),  # 金色
        )

        self.console.print(
            (self.console.width - len(subtitle)) // 2,
            title_y + 2,
            subtitle,
            fg=(200, 200, 200),
        )

        # 統計情報
        stats_y = title_y + 5
        final_score = self.calculate_score()
        stats_info = [
            f"Final Level: {self.player_stats.get('level', 1)}",
            f"Final Floor: B{self.final_floor}F",
            f"Final HP: {self.player_stats.get('hp', 0)}/{self.player_stats.get('max_hp', 0)}",
            f"Experience: {self.player_stats.get('exp', 0)}",
            f"Gold Collected: {self.player_stats.get('gold', 0)}",
            "",
            f"FINAL SCORE: {final_score}",
        ]

        for i, stat in enumerate(stats_info):
            if stat == "":
                continue

            color = (255, 215, 0) if "FINAL SCORE" in stat else (150, 150, 150)
            self.console.print(
                (self.console.width - len(stat)) // 2,
                stats_y + i,
                stat,
                fg=color,
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
