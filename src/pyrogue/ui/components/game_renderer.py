"""Render the canonical renderer-neutral game state in TCOD."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod

from pyrogue.presentation.display_renderer import cell_glyph

if TYPE_CHECKING:
    from pyrogue.ui.screens.game_screen import GameScreen


class GameRenderer:
    """Draw the active game's visible cells, status, and messages."""

    def __init__(self, game_screen: GameScreen) -> None:
        self.game_screen = game_screen

    def render(self, console: tcod.Console) -> None:
        """Draw visible map cells and the canonical status/message rows."""
        console.clear()
        game = self.game_screen.rogue_game
        for cell in self.game_screen.display_cells().values():
            if cell.terrain is None:
                continue
            x, y = cell.position
            if 0 <= x < console.width and 0 <= y + 1 < console.height - 1:
                color = (255, 255, 255) if cell.visible else (80, 80, 80)
                console.print(x, y + 1, cell_glyph(cell), fg=color)

        if console.width:
            message = game.messages[-1] if game.messages else ""
            status = f"B{game.current_floor}F  {game.status_text()}"
            console.print(0, 0, str(message)[: console.width], fg=(255, 255, 255))
            console.print(0, console.height - 1, status[: console.width], fg=(255, 255, 255))
