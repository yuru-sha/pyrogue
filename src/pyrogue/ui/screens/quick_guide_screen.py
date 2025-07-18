"""
クイックガイドスクリーンモジュール。

新しいゲーム開始時に表示される簡潔なガイダンス画面です。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
import tcod.console
import tcod.event

from pyrogue.core.game_states import GameStates

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine


class QuickGuideScreen:
    """
    クイックガイドスクリーンクラス。

    新しいゲーム開始時に表示される簡潔なガイダンスを提供します。
    初心者プレイヤーが最低限知っておくべき情報を表示します。
    """

    def __init__(self, console: tcod.console.Console, engine: Engine) -> None:
        """
        クイックガイドスクリーンを初期化。

        Args:
        ----
            console: TCODコンソールオブジェクト
            engine: メインゲームエンジンのインスタンス

        """
        self.console = console
        self.engine = engine

    def update_console(self, console: tcod.console.Console) -> None:
        """
        コンソールの更新。

        Args:
        ----
            console: 新しいTCODコンソールオブジェクト

        """
        self.console = console

    def render(self) -> None:
        """クイックガイドを描画。"""
        self.console.clear()

        # タイトル表示
        title = "Welcome to PyRogue!"
        self.console.print(
            (self.console.width - len(title)) // 2,
            3,
            title,
            fg=(255, 215, 0),  # 金色
        )

        # ミッション説明
        mission_lines = [
            "Your Mission:",
            "• Descend 26 levels into the dungeon",
            "• Find the Amulet of Yendor on B26F",
            "• Return to the surface and escape!",
        ]

        start_y = 6
        for i, line in enumerate(mission_lines):
            color = (255, 255, 100) if i == 0 else (200, 200, 200)
            self.console.print(
                (self.console.width - len(line)) // 2,
                start_y + i,
                line,
                fg=color,
            )

        # 重要なコマンド
        commands_title = "Essential Commands:"
        self.console.print(
            (self.console.width - len(commands_title)) // 2,
            start_y + 6,
            commands_title,
            fg=(255, 255, 100),
        )

        commands = [
            "hjkl / Arrow Keys  - Move around",
            ", (comma)          - Pick up items",
            "i                  - Open inventory",
            "?                  - Show help",
            "o / c              - Open / Close doors",
            "s                  - Search for secrets",
            "Ctrl+S / Ctrl+L    - Save / Load game",
        ]

        for i, command in enumerate(commands):
            self.console.print(
                (self.console.width - len(command)) // 2,
                start_y + 8 + i,
                command,
                fg=(150, 200, 150),
            )

        # 重要な注意事項
        warnings_title = "Important Notes:"
        self.console.print(
            (self.console.width - len(warnings_title)) // 2,
            start_y + 17,
            warnings_title,
            fg=(255, 100, 100),
        )

        warnings = [
            "• PERMADEATH: When you die, the game is over!",
            "• Manage hunger: Eat food to stay strong",
            "• Identify items: Use Scroll of Identify",
            "• Press ? anytime for detailed help",
        ]

        for i, warning in enumerate(warnings):
            self.console.print(
                (self.console.width - len(warning)) // 2,
                start_y + 19 + i,
                warning,
                fg=(255, 150, 150),
            )

        # 操作説明
        help_text = "Press any key to start your adventure!"
        self.console.print(
            (self.console.width - len(help_text)) // 2,
            self.console.height - 3,
            help_text,
            fg=(100, 255, 100),
        )

    def handle_input(self, key: tcod.event.KeyDown) -> GameStates | None:
        """
        ユーザー入力の処理。

        任意のキーでゲームを開始します。

        Args:
        ----
            key: キーボード入力イベント

        Returns:
        -------
            ゲーム状態

        """
        # 任意のキーでゲーム開始
        return GameStates.PLAYERS_TURN