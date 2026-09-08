from pyrogue.core.rogue_game import (
    EntityKind,
    GameState,
    ItemKind,
    ItemState,
    MonsterState,
    Terrain,
    TrapKind,
    TrapState,
)
from pyrogue.ui.display_renderer import cell_glyph, render_ascii


def test_ascii_renderer_uses_display_cells_and_keeps_entity_priority() -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    game.floor.items.clear()

    initial_cells = game.display_cells()
    player_position = game.player.position
    visible_positions = [
        position
        for position, cell in initial_cells.items()
        if cell.visible and cell.terrain is not None and position != player_position
    ]
    monster_position, item_position, trap_position = visible_positions[:3]
    game.floor.set_tile(trap_position, Terrain.FLOOR)
    game.floor.monsters.append(MonsterState(1, "venus_flytrap", *monster_position, 25))
    game.floor.items.extend(
        [
            ItemState(id=1, kind=ItemKind.GOLD, name="gold", position=monster_position),
            ItemState(id=2, kind=ItemKind.FOOD, name="food ration", position=item_position),
        ]
    )
    game.floor.traps.append(TrapState(1, TrapKind.TRAP_DOOR, *trap_position, discovered=True))

    cells = game.display_cells()
    rendered = render_ascii(cells, game.width, game.height).splitlines()

    assert cells[monster_position].entity == EntityKind.MONSTER
    assert cells[monster_position].entity_variant == "venus_flytrap"
    assert rendered[player_position[1]][player_position[0]] == "@"
    assert rendered[monster_position[1]][monster_position[0]] == "F"
    assert rendered[item_position[1]][item_position[0]] == ":"
    assert rendered[trap_position[1]][trap_position[0]] == "."
    assert cell_glyph(cells[trap_position]) == "^"
    assert not hasattr(GameState, "render_ascii")
    assert not hasattr(ItemState, "char")
    assert not hasattr(MonsterState, "char")
    assert not hasattr(TrapState, "char")
