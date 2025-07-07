"""
異なるゲーム状態に対応する入力処理システム。
"""

from abc import ABC, abstractmethod
from typing import Any

import tcod.event

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
        pass

    def handle_input(
        self, event: tcod.event.KeyDown, current_state: GameStates, context: Any
    ) -> tuple[bool, GameStates | None]:
        """
        Handle input based on current state.

        Args:
            event: The key event
            current_state: Current game state
            context: Context object (screen instance)

        Returns:
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
