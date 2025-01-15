"""Game engine module.

This module implements the core game engine, handling the main game loop,
state management, and event processing.
"""
from __future__ import annotations

import tcod
import tcod.console
import tcod.event
import tcod.tileset

from pyrogue.utils import game_logger
from pyrogue.ui.screens.menu_screen import MenuScreen
from pyrogue.ui.screens.game_screen import GameScreen

class GameState:
    """Represents the current state of the game."""
    MENU = "menu"
    GAME = "game"
    INVENTORY = "inventory"
    HELP = "help"
    GAME_OVER = "game_over"

class Engine:
    """Main game engine class."""

    def __init__(self):
        self.screen_width = 80
        self.screen_height = 50
        self.title = "PyRogue"
        self.console = tcod.console.Console(self.screen_width, self.screen_height)
        self.state = GameState.MENU
        self.running = False
        
        # 画面の初期化
        self.menu_screen = MenuScreen(self.console)
        self.game_screen = GameScreen(self.console)
        
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
        self.context = tcod.context.new(
            columns=self.screen_width,
            rows=self.screen_height,
            title=self.title,
            vsync=True,
        )
        game_logger.debug("Game engine initialized")

    def run(self) -> None:
        """Run the main game loop."""
        self.running = True
        game_logger.debug("Starting game loop")

        try:
            while self.running:
                self.console.clear()
                
                # 現在の状態に応じて描画
                if self.state == GameState.MENU:
                    self.menu_screen.render()
                elif self.state == GameState.GAME:
                    self.game_screen.render()
                
                self.context.present(self.console)
                
                for event in tcod.event.wait():
                    if event.type == "QUIT":
                        game_logger.debug("Quit event received")
                        self.running = False
                        break
                    
                    if event.type == "KEYDOWN":
                        if not self.handle_keydown(event):
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

    def handle_keydown(self, event: tcod.event.KeyDown) -> bool:
        """Handle keyboard input.
        
        Returns:
            bool: False if the game should quit, True otherwise.
        """
        # ESCキーの処理
        if event.sym == tcod.event.KeySym.ESCAPE:
            if self.state == GameState.GAME:
                self.state = GameState.MENU
                return True
            elif self.state == GameState.MENU:
                return False

        # 状態に応じたキー処理
        if self.state == GameState.MENU:
            if self.menu_screen.handle_keydown(event):
                if self.menu_screen.menu_selection == 0:  # New Game selected
                    self.state = GameState.GAME
                return True
            return False
        elif self.state == GameState.GAME:
            self.game_screen.handle_keydown(event)
            return True
        return True

    def cleanup(self) -> None:
        """Cleanup resources before exiting."""
        game_logger.debug("Cleaning up resources") 