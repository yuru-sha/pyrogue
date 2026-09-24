from pyrogue.core.cli_engine import CLIEngine
from pyrogue.core.rogue_game import MAX_FLOOR, GameState


def test_cli_defaults_to_canonical_game_state(capsys) -> None:
    cli = CLIEngine()

    assert isinstance(cli.game_state, GameState)
    assert cli.process_command("help") is True
    assert "hjkl yubn move" in capsys.readouterr().out


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
