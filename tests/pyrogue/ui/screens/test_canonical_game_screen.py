import tcod.event

from pyrogue.core.cli_engine import CLIEngine
from pyrogue.core.rogue_game import GameState, ItemKind, ItemState, MonsterState
from pyrogue.ui.screens.game_screen import GameScreen


def _key(character: str) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(0, ord(character), 0)


def _walkable_direction(game: GameState) -> tuple[str, tuple[int, int]]:
    directions = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}
    for name, (dx, dy) in directions.items():
        position = (game.player.x + dx, game.player.y + dy)
        if game.floor.is_walkable(position):
            return name, position
    raise AssertionError


def test_headless_gui_key_execution_matches_cli() -> None:
    cli = CLIEngine(seed=1234, spec_mode=True)
    game_screen = GameScreen(None, seed=1234)

    assert game_screen.handle_key(_key(".")) is None
    assert cli.process_command(".") is True

    assert game_screen.rogue_game.to_dict() == cli.spec_game.to_dict()


def test_headless_gui_and_cli_select_the_same_item_and_target_direction() -> None:
    cli = CLIEngine(seed=1234, spec_mode=True)
    gui = GameScreen(None, seed=1234)

    for game in (cli.spec_game, gui.rogue_game):
        game.floor.monsters.clear()
        direction, position = _walkable_direction(game)
        wand = ItemState(1000, ItemKind.WAND, "test wand", effect="magic_missile", charges=2)
        game.floor.monsters.append(MonsterState(2000, "bat", *position, 20))
        game.player.inventory.append(wand)

    direction, _ = _walkable_direction(gui.rogue_game)
    gui_result = gui.rogue_game.execute("zap", [1000, direction])
    cli_result = cli.spec_game.execute("zap", [1000, direction])

    assert gui_result == cli_result
    assert gui.rogue_game.to_dict() == cli.spec_game.to_dict()


def test_headless_gui_target_selection_moves_and_confirms() -> None:
    game_screen = GameScreen(None, seed=1234)
    start = game_screen.player.position
    handler = game_screen.input_handler
    handler.start_targeting(*start)

    handler.handle_key(_key("l"))
    selected = handler.get_targeting_info()
    assert selected == (True, start[0] + 1, start[1])

    handler.handle_key(tcod.event.KeyDown(0, tcod.event.KeySym.RETURN, 0))
    assert handler.get_targeting_info() == (False, start[0] + 1, start[1])
