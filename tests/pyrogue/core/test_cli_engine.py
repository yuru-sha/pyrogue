from pyrogue.core.cli_engine import CLIEngine
from pyrogue.core.rogue_game import MAX_FLOOR, GameState, Terrain


def test_cli_defaults_to_canonical_game_state(capsys) -> None:
    cli = CLIEngine()

    assert isinstance(cli.game_state, GameState)
    assert cli.process_command("help") is True
    assert "hjkl yubn move" in capsys.readouterr().out


def test_cli_count_call_and_options_use_canonical_turn_semantics(capsys) -> None:
    from pyrogue.core.rogue_game import ItemKind, ItemState

    cli = CLIEngine(seed=108)
    cli.game_state.floor.monsters.clear()
    assert cli.process_command("3.") is True
    assert cli.game_state.player.turns_played == 3

    item = ItemState(1085, ItemKind.POTION, "healing potion", appearance="red potion", identified=False)
    cli.game_state.player.inventory.append(item)
    assert cli.process_command("c 1085 emergency") is True
    assert item.display_name == "red potion called emergency"
    turns_before_options = cli.game_state.player.turns_played
    assert cli.process_command("o") is True
    assert cli.game_state.player.turns_played == turns_before_options
    assert "Options are available." in capsys.readouterr().out


def test_cli_preserves_uppercase_run_after_numeric_prefix() -> None:
    cli = CLIEngine(seed=108)
    game = cli.game_state
    game.floor.monsters.clear()
    x, y = game.player.position
    for row in range(y - 1, y + 2):
        for column in range(x - 1, x + 4):
            game.floor.set_tile((column, row), Terrain.WALL)
    for column in range(x, x + 3):
        game.floor.set_tile((column, y), Terrain.FLOOR)

    assert cli.process_command("2L")

    assert game.player.position == (x + 2, y)
    assert game.player.turns_played == 2


def test_cli_victory_summary_reports_deepest_floor(capsys) -> None:
    game = GameState(1234)

    for _ in range(1, MAX_FLOOR):
        game.floor.monsters.clear()
        game.player.position = game.floor.down_stairs
        assert game.descend().success

    game.floor.monsters.clear()
    amulet = next(item for item in game.floor.items if item.name == "amulet of yendor")
    game.player.position = amulet.position
    assert game.pickup().success

    for _ in range(1, MAX_FLOOR):
        game.floor.monsters.clear()
        game.player.position = game.floor.up_stairs
        assert game.ascend().success

    game.player.position = game.floor.up_stairs
    cli = CLIEngine(seed=1234)
    cli.game_state = game

    cli.process_command("ascend")

    assert "Deepest floor: B26F" in capsys.readouterr().out
