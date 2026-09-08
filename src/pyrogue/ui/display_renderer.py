"""Render renderer-neutral display cells as text."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrogue.core.rogue_game import DisplayCell, EntityKind, Terrain

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyrogue.core.rogue_game import GameState, Position


TERRAIN_GLYPHS = {
    Terrain.WALL: "#",
    Terrain.FLOOR: ".",
    Terrain.DOOR_CLOSED: "+",
    Terrain.DOOR_OPEN: "/",
    Terrain.STAIRS_UP: "<",
    Terrain.STAIRS_DOWN: ">",
}


def cell_glyph(
    cell: DisplayCell,
    monster_glyphs: Mapping[Position, str],
    item_glyphs: Mapping[Position, str],
) -> str:
    """Convert one display cell to its ASCII glyph."""
    if cell.entity == EntityKind.PLAYER:
        return "@"
    if cell.entity == EntityKind.MONSTER:
        return monster_glyphs.get(cell.position, "?")
    if cell.entity == EntityKind.ITEM:
        return item_glyphs.get(cell.position, "*")
    if cell.entity == EntityKind.TRAP:
        return "^"
    if cell.terrain is None:
        return " "
    return TERRAIN_GLYPHS[cell.terrain]


def render_ascii(game: GameState) -> str:
    """Render the explored game state as plain text."""
    cells = game.display_cells()
    monster_glyphs = {(monster.x, monster.y): monster.char for monster in game.floor.monsters if monster.hp > 0}
    item_glyphs = {item.position: item.char for item in game.floor.items if item.position is not None}
    return "\n".join(
        "".join(cell_glyph(cells[(x, y)], monster_glyphs, item_glyphs) for x in range(game.width))
        for y in range(game.height)
    )
