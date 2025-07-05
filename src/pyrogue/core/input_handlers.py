"""
Input handling system for different game states.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

import tcod.event

from pyrogue.core.game_states import GameStates


class InputHandler(ABC):
    """Base class for input handlers."""
    
    @abstractmethod
    def handle_input(self, event: tcod.event.KeyDown, context: Any) -> Optional[GameStates]:
        """Handle input for a specific state."""
        pass
    
    def handle_escape(self, current_state: GameStates) -> Optional[GameStates]:
        """Handle escape key press - default behavior."""
        if current_state in (GameStates.PLAYERS_TURN, GameStates.GAME_OVER, GameStates.VICTORY):
            return GameStates.MENU
        if current_state == GameStates.MENU:
            return GameStates.EXIT
        return None


class StateManager:
    """Manages input handling for different game states."""
    
    def __init__(self):
        self.input_handler = InputHandler()
    
    def handle_input(self, event: tcod.event.KeyDown, current_state: GameStates, context: Any) -> tuple[bool, Optional[GameStates]]:
        """
        Handle input based on current state.
        
        Args:
            event: The key event
            current_state: Current game state
            context: Context object (screen instance)
            
        Returns:
            Tuple of (continue_game, new_state)
        """
        # Handle escape key globally
        if event.sym == tcod.event.KeySym.ESCAPE:
            new_state = self.input_handler.handle_escape(current_state)
            if new_state == GameStates.EXIT:
                return False, None
            return True, new_state
        
        # Delegate to appropriate handler
        if current_state == GameStates.MENU:
            new_state = context.handle_input(event)
            if new_state == GameStates.EXIT:
                return False, None
            return True, new_state
        
        elif current_state == GameStates.PLAYERS_TURN:
            context.handle_key(event)
            return True, None
        
        elif current_state == GameStates.GAME_OVER:
            new_state = context.handle_input(event)
            if new_state == GameStates.EXIT:
                return False, None
            return True, new_state
        
        elif current_state == GameStates.VICTORY:
            new_state = context.handle_input(event)
            if new_state == GameStates.EXIT:
                return False, None
            return True, new_state
        
        return True, None