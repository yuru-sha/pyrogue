"""
異なるゲーム状態に対応する入力処理システム。
"""

from abc import ABC, abstractmethod
from typing import Any

import tcod.event

from pyrogue.core.command_handler import CommonCommandHandler, GUICommandContext
from pyrogue.core.game_states import GameStates


class InputHandler(ABC):
    """入力ハンドラーの基底クラス。"""

    @abstractmethod
    def handle_input(
        self, event: tcod.event.KeyDown, context: Any
    ) -> GameStates | None:
        """特定の状態における入力を処理。"""

    def handle_escape(self, current_state: GameStates) -> GameStates | None:
        """Handle escape key press - default behavior."""
        if current_state in (
            GameStates.PLAYERS_TURN,
            GameStates.GAME_OVER,
            GameStates.VICTORY,
        ):
            return GameStates.MENU
        if current_state == GameStates.MENU:
            return GameStates.EXIT
        return None


class StateManager:
    """異なるゲーム状態に対する入力処理を管理。"""

    def __init__(self):
        # We don't need to instantiate InputHandler since we handle each state directly
        self.command_handler = None

    def set_command_handler(self, game_screen) -> None:
        """GameScreenからのコマンドハンドラー設定。"""
        if game_screen:
            context = GUICommandContext(game_screen)
            self.command_handler = CommonCommandHandler(context)

    def handle_input(
        self, event: tcod.event.KeyDown, current_state: GameStates, context: Any
    ) -> tuple[bool, GameStates | None]:
        """
        Handle input based on current state.

        Args:
        ----
            event: The key event
            current_state: Current game state
            context: Context object (screen instance)

        Returns:
        -------
            Tuple of (continue_game, new_state)

        """
        # Delegate to appropriate handler first
        if current_state == GameStates.MENU:
            new_state = context.handle_input(event)
            if new_state == GameStates.EXIT:
                return False, None
            return True, new_state

        if current_state == GameStates.PLAYERS_TURN:
            context.handle_key(event)
            return True, None

        if current_state == GameStates.SHOW_INVENTORY:
            context.handle_input(event)
            return True, None

        if current_state == GameStates.SHOW_MAGIC:
            context.handle_key(event)
            return True, None

        if current_state == GameStates.TARGETING:
            context.handle_targeting(event)
            return True, None

        if current_state == GameStates.DIALOGUE:
            new_screen = context.handle_key(event)
            if new_screen:
                return True, GameStates.PLAYERS_TURN
            return True, None

        if current_state == GameStates.GAME_OVER or current_state == GameStates.VICTORY:
            new_state = context.handle_input(event)
            if new_state == GameStates.EXIT:
                return False, None
            return True, new_state

        # Handle escape key as fallback for states without explicit handling
        if event.sym == tcod.event.KeySym.ESCAPE:
            new_state = self._handle_escape(current_state)
            if new_state == GameStates.EXIT:
                return False, None
            return True, new_state

        return True, None

    def _handle_escape(self, current_state: GameStates) -> GameStates | None:
        """Handle escape key press - default behavior."""
        if current_state in (
            GameStates.PLAYERS_TURN,
            GameStates.GAME_OVER,
            GameStates.VICTORY,
        ):
            return GameStates.MENU
        if current_state == GameStates.MENU:
            return GameStates.EXIT
        if current_state in (
            GameStates.SHOW_INVENTORY,
            GameStates.SHOW_MAGIC,
            GameStates.TARGETING,
        ):
            return GameStates.PLAYERS_TURN
        return None

    def try_handle_with_command_handler(self, event: tcod.event.KeyDown) -> bool:
        """
        共通コマンドハンドラーでの処理を試行。

        Args:
        ----
            event: キーイベント

        Returns:
        -------
            bool: コマンドハンドラーで処理された場合True
        """
        if not self.command_handler:
            return False

        # キーイベントをコマンドに変換
        command = self._key_to_command(event)
        if not command:
            return False

        # コマンドハンドラーで処理
        result = self.command_handler.handle_command(command)
        return result.success

    def _key_to_command(self, event: tcod.event.KeyDown) -> str | None:
        """キーイベントをコマンド文字列に変換。"""
        key = event.sym

        # 移動キー - 文字コードで比較
        if key in (ord("h"), tcod.event.KeySym.LEFT):
            return "west"
        elif key in (ord("j"), tcod.event.KeySym.DOWN):
            return "south"
        elif key in (ord("k"), tcod.event.KeySym.UP):
            return "north"
        elif key in (ord("l"), tcod.event.KeySym.RIGHT):
            return "east"
        elif key == ord("y"):
            return "move northwest"
        elif key == ord("u"):
            return "move northeast"
        elif key == ord("b"):
            return "move southwest"
        elif key == ord("n"):
            return "move southeast"

        # アクションキー
        elif key == ord("g"):
            return "get"
        elif key == ord("o"):
            return "open"
        elif key == ord("c"):
            return "close"
        elif key == ord("s"):
            return "search"
        elif key == ord("d"):
            return "disarm"

        return None
