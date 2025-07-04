"""
Game engine module.

This module implements the core game engine, handling the main game loop,
state management, and event processing.
"""

from __future__ import annotations

import tcod
import tcod.console
import tcod.event
import tcod.tileset

from pyrogue.core.game_states import GameStates
from pyrogue.ui.screens.game_screen import GameScreen
from pyrogue.ui.screens.menu_screen import MenuScreen
from pyrogue.ui.screens.game_over_screen import GameOverScreen
from pyrogue.utils import game_logger


class Engine:
    """Main game engine class."""

    def __init__(self):
        self.screen_width = 80
        self.screen_height = 50
        self.map_width = 80
        self.map_height = (
            43  # 画面上部にステータス表示、下部にメッセージログ用の余白を確保
        )
        self.title = "PyRogue"
        self.console = tcod.console.Console(self.screen_width, self.screen_height)
        self.state = GameStates.MENU
        self.running = False
        self.message_log = []  # メッセージログを追加

        # 画面の初期化
        self.menu_screen = MenuScreen(self.console, self)
        self.game_screen = GameScreen(self)
        self.game_over_screen = GameOverScreen(self.console, self)

        game_logger.debug(
            "Initializing game engine",
            extra={
                "screen_width": self.screen_width,
                "screen_height": self.screen_height,
                "title": self.title,
            },
        )

    def initialize(self) -> None:
        """Initialize the game engine and TCOD console."""
        # フォントの設定
        tileset = tcod.tileset.load_tilesheet(
            "data/assets/fonts/dejavu10x10_gs_tc.png",  # デフォルトフォント
            32,
            8,  # 列数と行数
            tcod.tileset.CHARMAP_TCOD,  # 文字マップ
        )

        # フォントサイズの設定
        self.font_width = 10
        self.font_height = 10

        # Create the context with resizable window
        self.context = tcod.context.new(
            columns=self.screen_width,
            rows=self.screen_height,
            tileset=tileset,
            title=self.title,
            vsync=True,
            sdl_window_flags=tcod.context.SDL_WINDOW_RESIZABLE,
        )
        game_logger.debug("Game engine initialized")

    def handle_resize(self, event: tcod.event.WindowEvent) -> None:
        """ウィンドウリサイズ時の処理"""
        # 新しいウィンドウサイズを取得
        pixel_width = event.width
        pixel_height = event.height

        # ピクセルサイズから文字数を計算
        self.screen_width = max(80, pixel_width // self.font_width)  # 最小幅は80文字
        self.screen_height = max(
            50, pixel_height // self.font_height
        )  # 最小高さは50文字

        # コンソールを再作成
        self.console = tcod.console.Console(self.screen_width, self.screen_height)

        # 各画面のコンソールを更新
        self.menu_screen.update_console(self.console)
        self.game_screen.update_console(self.console)
        self.game_over_screen.update_console(self.console)

        game_logger.debug(
            "Window resized",
            extra={
                "new_width": self.screen_width,
                "new_height": self.screen_height,
            },
        )

    def run(self) -> None:
        """Run the main game loop."""
        self.running = True
        game_logger.debug("Starting game loop")

        try:
            while self.running:
                self.console.clear()

                # 現在の状態に応じて描画
                if self.state == GameStates.MENU:
                    self.menu_screen.render()
                elif self.state == GameStates.PLAYERS_TURN:
                    self.game_screen.render()
                elif self.state == GameStates.GAME_OVER:
                    self.game_over_screen.render()

                self.context.present(self.console)

                for event in tcod.event.wait():
                    if event.type == "QUIT":
                        game_logger.debug("Quit event received")
                        self.running = False
                        break
                    if event.type == "WINDOWRESIZED":
                        self.handle_resize(event)
                    elif event.type == "KEYDOWN":
                        if not self.handle_input(event):
                            self.running = False
                            break

        except Exception as e:
            game_logger.error(
                "Fatal error in game loop",
                extra={"error": str(e)},
            )
            raise
        finally:
            self.cleanup()

    def handle_input(self, event: tcod.event.KeyDown) -> bool:
        """
        キー入力の処理

        Returns:
            bool: ゲームを続行する場合はTrue、終了する場合はFalse

        """
        # ESCキーの処理
        if event.sym == tcod.event.KeySym.ESCAPE:
            if self.state == GameStates.PLAYERS_TURN:
                self.state = GameStates.MENU
                return True
            if self.state == GameStates.MENU:
                return False
            if self.state == GameStates.GAME_OVER:
                self.state = GameStates.MENU
                return True

        # 状態に応じたキー処理
        if self.state == GameStates.MENU:
            new_state = self.menu_screen.handle_input(event)
            if new_state:
                if new_state == GameStates.EXIT:
                    return False
                self.state = new_state
            return True
        if self.state == GameStates.PLAYERS_TURN:
            self.game_screen.handle_key(event)
            return True
        if self.state == GameStates.GAME_OVER:
            new_state = self.game_over_screen.handle_input(event)
            if new_state:
                if new_state == GameStates.EXIT:
                    return False
                self.state = new_state
            return True
        return True

    def cleanup(self) -> None:
        """Cleanup resources before exiting."""
        game_logger.debug("Cleaning up resources")

    def new_game(self) -> None:
        """新しいゲームを開始"""
        self.game_screen.setup_new_game()
        self.state = GameStates.PLAYERS_TURN

    def game_over(
        self, player_stats: dict, final_floor: int, cause_of_death: str = "Unknown"
    ) -> None:
        """ゲームオーバー処理"""
        self.game_over_screen.set_game_over_data(
            player_stats, final_floor, cause_of_death
        )
        self.state = GameStates.GAME_OVER
