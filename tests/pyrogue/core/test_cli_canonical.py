from pyrogue.core.cli_engine import CLIEngine
from pyrogue.core.rogue_game import ItemKind, ItemState, TrapKind, TrapState
from pyrogue.core.save_manager import SaveManager


def _walkable_step(game) -> tuple[str, tuple[int, int]]:
    directions = {
        "east": (1, 0),
        "west": (-1, 0),
        "south": (0, 1),
        "north": (0, -1),
    }
    for name, (dx, dy) in directions.items():
        position = (game.player.x + dx, game.player.y + dy)
        if game.floor.is_walkable(position):
            return name, position
    raise AssertionError


def test_cli_death_prints_summary_and_removes_save(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("SAVE_DIRECTORY", str(tmp_path))
    cli = CLIEngine(seed=1234, spec_mode=True)
    save_manager = SaveManager(tmp_path)

    assert cli.process_command("save") is True
    assert save_manager.save_file.exists()

    game = cli.spec_game
    game.floor.monsters.clear()
    game.player.hp = 1
    direction, position = _walkable_step(game)
    game.floor.traps = [TrapState(999, TrapKind.BEAR, *position)]

    assert cli.process_command(f"move {direction}") is True

    output = capsys.readouterr().out
    assert game.is_dead
    assert "Score:" in output
    assert "Deepest floor:" in output
    assert "Cause:" in output
    assert not save_manager.save_file.exists()
    assert not save_manager.metadata_file.exists()


def test_cli_victory_prints_deepest_floor(capsys) -> None:
    cli = CLIEngine(seed=1234, spec_mode=True)
    game = cli.spec_game
    game.player.has_amulet = True
    game.player.deepest_floor = 26
    game.player.position = game.floor.up_stairs

    assert cli.process_command("stairs up") is True

    output = capsys.readouterr().out
    assert game.is_victory
    assert "VICTORY" in output
    assert "Score:" in output
    assert "Deepest floor: B26F" in output


def test_cli_save_load_restores_canonical_state(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("SAVE_DIRECTORY", str(tmp_path))
    cli = CLIEngine(seed=1234, spec_mode=True)
    game = cli.spec_game
    game.player.hp = 7
    game.player.gold = 42

    assert cli.process_command("save") is True
    capsys.readouterr()
    expected = cli.spec_game.to_dict()

    game.player.hp = 1
    game.player.gold = 999
    assert cli.process_command("load") is True

    assert cli.spec_game.to_dict() == expected


def test_cli_slash_identifies_one_unknown_item(capsys, monkeypatch) -> None:
    cli = CLIEngine(seed=1234, spec_mode=True)
    item = ItemState(
        1000,
        ItemKind.POTION,
        "healing potion",
        appearance="red",
        identified=False,
        effect="healing",
    )
    cli.spec_game.player.inventory.append(item)
    results = []
    execute = cli.spec_game.execute

    def record_execute(command, args=()):
        result = execute(command, args)
        results.append(result)
        return result

    monkeypatch.setattr(cli.spec_game, "execute", record_execute)

    assert cli.process_command("/") is True

    result = results[-1]
    assert result.success
    assert result.message == "You identify the healing potion."
    assert not result.turn_consumed
    assert item.identified
    assert "You identify the healing potion." in capsys.readouterr().out
