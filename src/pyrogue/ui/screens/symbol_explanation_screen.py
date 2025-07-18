"""
シンボル説明スクリーンモジュール。

このモジュールはゲーム中に呼び出されるシンボル説明スクリーンを表示し、
プレイヤーがゲーム内で使用される記号の意味を確認できます。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
import tcod.console
import tcod.event

from pyrogue.core.game_states import GameStates

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine


class SymbolExplanationScreen:
    """
    シンボル説明スクリーンクラス。

    ゲーム内で使用される記号の意味を表示します。
    """

    def __init__(self, console: tcod.console.Console, engine: Engine) -> None:
        """
        シンボル説明スクリーンを初期化。

        Args:
        ----
            console: TCODコンソールオブジェクト
            engine: メインゲームエンジンのインスタンス

        """
        self.console = console
        self.engine = engine
        self.scroll_y = 0
        self.symbol_content = self._get_symbol_content()
        self.max_scroll = max(0, len(self.symbol_content) - (self.console.height - 6))

    def update_console(self, console: tcod.console.Console) -> None:
        """
        コンソールの更新。

        Args:
        ----
            console: 新しいTCODコンソールオブジェクト

        """
        self.console = console
        self.max_scroll = max(0, len(self.symbol_content) - (self.console.height - 6))

    def render(self) -> None:
        """シンボル説明スクリーンを描画。"""
        self.console.clear()

        # タイトル表示
        title = "=== Symbol Explanation ==="
        self.console.print(
            (self.console.width - len(title)) // 2,
            1,
            title,
            fg=(255, 215, 0),  # 金色
        )

        # シンボル説明の表示（スクロール対応）
        content_start_y = 3
        visible_lines = self.console.height - 6

        for i in range(visible_lines):
            line_index = self.scroll_y + i
            if line_index < len(self.symbol_content):
                line = self.symbol_content[line_index]
                # セクションタイトル（=== で始まる行）は色を変える
                if line.startswith("==="):
                    color = (255, 255, 100)  # 黄色
                elif line.startswith("  "):
                    color = (200, 200, 200)  # 薄いグレー
                else:
                    color = (255, 255, 255)  # 白色

                self.console.print(
                    2,
                    content_start_y + i,
                    line,
                    fg=color,
                )

        # スクロール状態の表示
        if self.max_scroll > 0:
            scroll_info = f"({self.scroll_y + 1}/{len(self.symbol_content) - visible_lines + 1})"
            self.console.print(
                self.console.width - len(scroll_info) - 2,
                1,
                scroll_info,
                fg=(100, 100, 100),
            )

        # 操作説明
        help_text = "UP/DOWN: Scroll  ESC: Back to Game"
        self.console.print(
            (self.console.width - len(help_text)) // 2,
            self.console.height - 2,
            help_text,
            fg=(100, 100, 100),
        )

    def handle_input(self, key: tcod.event.KeyDown) -> GameStates | None:
        """
        ユーザー入力の処理。

        Args:
        ----
            key: キーボード入力イベント

        Returns:
        -------
            ゲーム状態、またはNone

        """
        # 上矢印キーで上にスクロール
        if key.sym == tcod.event.KeySym.UP:
            self.scroll_y = max(0, self.scroll_y - 1)
        # 下矢印キーで下にスクロール
        elif key.sym == tcod.event.KeySym.DOWN:
            self.scroll_y = min(self.max_scroll, self.scroll_y + 1)
        # Page Upで大きくスクロール
        elif key.sym == tcod.event.KeySym.PAGEUP:
            self.scroll_y = max(0, self.scroll_y - 10)
        # Page Downで大きくスクロール
        elif key.sym == tcod.event.KeySym.PAGEDOWN:
            self.scroll_y = min(self.max_scroll, self.scroll_y + 10)
        # ESCキーでゲームに戻る
        elif key.sym == tcod.event.KeySym.ESCAPE:
            return GameStates.PLAYERS_TURN
        # /キーでもゲームに戻る（JIS配列対応）
        elif key.sym == tcod.event.KeySym.SLASH or key.unicode == "/":
            return GameStates.PLAYERS_TURN

        return None

    def _get_symbol_content(self) -> list[str]:
        """
        シンボル説明コンテンツを取得。

        Returns
        -------
            シンボル説明コンテンツの行リスト

        """
        return [
            "=== Basic Symbols ===",
            "  @  - Player (you)",
            "  #  - Wall",
            "  .  - Floor",
            "",
            "=== Doors ===",
            "  +  - Closed door",
            "  /  - Open door",
            "",
            "=== Items ===",
            "  %  - Food",
            "  !  - Potion",
            "  ?  - Scroll",
            "  )  - Weapon",
            "  [  - Armor",
            "  =  - Ring",
            "  /  - Wand",
            "  $  - Gold",
            "",
            "=== Stairs ===",
            "  <  - Stairs up",
            "  >  - Stairs down",
            "",
            "=== Dangers ===",
            "  ^  - Trap",
            "",
            "=== Monsters ===",
            "  A-Z - Various monsters",
            "",
            "=== Monster Types (Examples) ===",
            "  A  - Aquator",
            "  B  - Bat",
            "  C  - Centaur",
            "  D  - Dragon",
            "  E  - Emu",
            "  F  - Venus Flytrap",
            "  G  - Griffin",
            "  H  - Hobgoblin",
            "  I  - Ice Monster",
            "  J  - Jabberwock",
            "  K  - Kestrel",
            "  L  - Leprechaun",
            "  M  - Mimic",
            "  N  - Nymph",
            "  O  - Orc",
            "  P  - Phantom",
            "  Q  - Quagga",
            "  R  - Rattlesnake",
            "  S  - Snake",
            "  T  - Troll",
            "  U  - Ur-vile",
            "  V  - Vampire",
            "  W  - Wraith",
            "  X  - Xeroc",
            "  Y  - Yeti",
            "  Z  - Zombie",
            "",
            "=== Tips ===",
            "  • Different monsters have different abilities",
            "  • Some steal items, some drain experience",
            "  • Higher level monsters appear deeper",
            "  • Use 'l' to look at specific tiles",
            "",
            "Press ESC or / to return to the game.",
        ]
