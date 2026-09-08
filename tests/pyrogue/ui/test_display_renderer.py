from pyrogue.core.rogue_game import EntityKind, GameState, ItemKind, ItemState, MonsterState
from pyrogue.ui.display_renderer import render_ascii


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
    monster_position, item_position = visible_positions[:2]
    game.floor.monsters.append(MonsterState(1, "bat", *monster_position, 5))
    game.floor.items.extend(
        [
            ItemState(id=1, kind=ItemKind.GOLD, name="gold", position=monster_position),
            ItemState(id=2, kind=ItemKind.FOOD, name="food ration", position=item_position),
        ]
    )

    cells = game.display_cells()
    rendered = render_ascii(game).splitlines()

    assert cells[monster_position].entity == EntityKind.MONSTER
    assert rendered[player_position[1]][player_position[0]] == "@"
    assert rendered[monster_position[1]][monster_position[0]] == "B"
    assert rendered[item_position[1]][item_position[0]] == ":"
