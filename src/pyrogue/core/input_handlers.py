"""Route key events to the active screen."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyrogue.core.game_states import GameStates

if TYPE_CHECKING:
    import tcod.event


class StateManager:
    """Dispatch one key event to the screen for the current state."""

    def handle_input(
        self, event: tcod.event.KeyDown, current_state: GameStates, context: Any
    ) -> tuple[bool, GameStates | None]:
        """Dispatch an event and report whether the engine should continue."""
        if current_state == GameStates.MENU:
            new_state = context.handle_input(event)
        elif current_state in {GameStates.PLAYERS_TURN, GameStates.SHOW_INVENTORY}:
            new_state = (
                context.handle_key(event) if current_state == GameStates.PLAYERS_TURN else context.handle_input(event)
            )
        elif current_state in {
            GameStates.HELP_MENU,
            GameStates.QUICK_GUIDE,
            GameStates.GAME_OVER,
            GameStates.VICTORY,
        }:
            new_state = context.handle_input(event)
        else:
            new_state = None
        if new_state == GameStates.EXIT:
            return False, None
        return True, new_state
