from types import SimpleNamespace
from unittest.mock import Mock

from pyrogue.core.cli_engine import CLIEngine
from pyrogue.core.managers.floor_manager import FloorManager
from pyrogue.core.rogue_game import MAX_FLOOR, GameState
from pyrogue.entities.actors.player import Player
from pyrogue.map.tile import StairsDown


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
    cli.spec_game = game

    cli.process_command("ascend")

    assert "Deepest Floor: B26F" in capsys.readouterr().out


def test_legacy_cli_victory_summary_reports_deepest_floor(capsys) -> None:
    cli = CLIEngine()
    cli.game_logic = SimpleNamespace(
        ascend_stairs=lambda: True,
        check_victory=lambda: True,
        dungeon_manager=SimpleNamespace(current_floor=1),
        player=SimpleNamespace(deepest_floor=26),
    )

    assert cli.handle_stairs("up")

    assert "Deepest Floor: B26F" in capsys.readouterr().out


def test_floor_manager_updates_deepest_floor_on_descent() -> None:
    player = Player(0, 0)
    floor = Mock()
    floor.get_tile.return_value = StairsDown()
    floor.get_stairs_up_position.return_value = (2, 2)
    floor.start_pos = (2, 2)
    dungeon_manager = Mock(current_floor=1)
    dungeon_manager.get_current_floor_data.return_value = floor
    context = SimpleNamespace(
        player=player,
        dungeon_manager=dungeon_manager,
        add_message=Mock(),
    )

    assert FloorManager(context).handle_stairs_down()

    assert player.deepest_floor == 2
