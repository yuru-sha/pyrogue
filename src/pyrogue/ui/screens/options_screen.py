"""Rogue command options presentation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.event

from pyrogue.core.game_states import GameStates

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine


class OptionsScreen:
    """Present display options without advancing game time."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def render(self) -> None:
        """Draw the current display options."""
        console = self.engine.console
        console.clear()
        title = "Options"
        console.print((console.width - len(title)) // 2, 4, title, fg=(255, 215, 0))
        options = [
            f"FOV masking: {'on' if self.engine.game_screen.fov_manager.fov_enabled else 'off'} (Tab)",
            "Return to game (Esc)",
        ]
        for index, option in enumerate(options):
            console.print(8, 8 + index * 2, option, fg=(220, 220, 220))

    def handle_input(self, event: tcod.event.KeyDown) -> GameStates | None:
        """Apply a display option or return to the active game."""
        if event.sym == tcod.event.KeySym.ESCAPE:
            return GameStates.PLAYERS_TURN
        if event.sym == tcod.event.KeySym.TAB:
            self.engine.game_screen.toggle_fov()
        return None
