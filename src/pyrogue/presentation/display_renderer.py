"""Render renderer-neutral display cells as text."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrogue.core.rogue_game import DisplayCell, EntityKind, Position, Terrain

if TYPE_CHECKING:
    from collections.abc import Mapping


TERRAIN_GLYPHS = {
    Terrain.WALL: "#",
    Terrain.FLOOR: ".",
    Terrain.DOOR_CLOSED: "+",
    Terrain.DOOR_OPEN: "/",
    Terrain.STAIRS_UP: "<",
    Terrain.STAIRS_DOWN: ">",
}
ITEM_GLYPHS = {
    "weapon": ")",
    "armor": "]",
    "food": ":",
    "potion": "!",
    "scroll": "?",
    "wand": "/",
    "ring": "=",
    "gold": "*",
    "amulet": ",",
}
MONSTER_GLYPHS = {
    "aquator": "A",
    "bat": "B",
    "centaur": "C",
    "dragon": "D",
    "emu": "E",
    "venus_flytrap": "F",
    "griffin": "G",
    "hobgoblin": "H",
    "ice_monster": "I",
    "jabberwock": "J",
    "kestrel": "K",
    "leprechaun": "L",
    "medusa": "M",
    "nymph": "N",
    "orc": "O",
    "phantom": "P",
    "quagga": "Q",
    "rattlesnake": "R",
    "snake": "S",
    "troll": "T",
    "ur_vile": "U",
    "vampire": "V",
    "wraith": "W",
    "xeroc": "X",
    "yeti": "Y",
    "zombie": "Z",
}


def cell_glyph(cell: DisplayCell, show_traps: bool = True) -> str:
    """Convert one display cell to its ASCII glyph."""
    if cell.entity == EntityKind.PLAYER:
        return "@"
    if cell.entity == EntityKind.MONSTER:
        return MONSTER_GLYPHS.get(cell.entity_variant or "", "?")
    if cell.entity == EntityKind.ITEM:
        return ITEM_GLYPHS.get(cell.entity_variant or "", "*")
    if cell.entity == EntityKind.TRAP and show_traps:
        return "^"
    if cell.terrain is None:
        return " "
    return TERRAIN_GLYPHS[cell.terrain]


def render_ascii(cells: Mapping[Position, DisplayCell], width: int, height: int, show_traps: bool = False) -> str:
    """Render display cells as plain text."""
    return "\n".join("".join(cell_glyph(cells[(x, y)], show_traps) for x in range(width)) for y in range(height))
