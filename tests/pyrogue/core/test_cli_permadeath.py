from unittest.mock import patch

from pyrogue.core.cli_engine import CLIEngine
from pyrogue.core.engine import Engine
from pyrogue.core.game_states import GameStates
from pyrogue.core.rogue_game import STARVETIME, GameState, GameStatus
from pyrogue.core.save_manager import SaveManager


def test_cli_death_shows_summary_and_deletes_save(tmp_path, capsys) -> None:
    engine = CLIEngine(seed=1234, spec_mode=True)
    game = engine.spec_game
    game.player.gold = 7
    game.player.monsters_killed = 2
    game.player.deepest_floor = 4
    game.player.food_units = -STARVETIME
    save_manager = SaveManager(tmp_path)
    assert save_manager.save_game_state(game.to_dict())

    with patch("pyrogue.core.cli_engine.SaveManager", return_value=save_manager):
        engine.process_command(".")

    output = capsys.readouterr().out
    assert "GAME OVER!" in output
    assert "Score: 27" in output
    assert "Deepest Floor: 4" in output
    assert "Cause of Death: starvation" in output
    assert SaveManager(tmp_path).load_game_state() is None


def test_permadeath_only_deletes_dead_canonical_state(tmp_path) -> None:
    victory_manager = SaveManager(tmp_path / "victory")
    victory_game = GameState(1234)
    victory_game.status = GameStatus.VICTORY
    assert victory_manager.save_game_state(victory_game.to_dict())

    assert victory_manager.finalize_death(victory_game) is None

    assert victory_manager.load_game_state() is not None

    dead_manager = SaveManager(tmp_path / "dead")
    dead_game = GameState(1234)
    dead_game._die("test")
    assert dead_manager.save_game_state(dead_game.to_dict())

    assert dead_manager.finalize_death(dead_game) == dead_game.death_summary

    assert dead_manager.load_game_state() is None


def test_gui_game_over_uses_shared_death_finalizer(tmp_path) -> None:
    save_manager = SaveManager(tmp_path)
    with patch("pyrogue.core.engine.SaveManager", return_value=save_manager):
        engine = Engine(seed=1234)

    game = engine.game_screen.rogue_game
    game._die("test")
    assert save_manager.save_game_state(game.to_dict())

    engine.game_over()

    assert engine.game_over_screen.player_stats["score"] == game.score
    assert engine.game_over_screen.final_floor == game.player.deepest_floor
    assert engine.game_over_screen.cause_of_death == "test"
    assert SaveManager(tmp_path).load_game_state() is None


def test_victory_screen_and_save_are_unchanged(tmp_path) -> None:
    save_manager = SaveManager(tmp_path)
    with patch("pyrogue.core.engine.SaveManager", return_value=save_manager):
        engine = Engine(seed=1234)

    game = engine.game_screen.rogue_game
    game.status = GameStatus.VICTORY
    game.player.has_amulet = True
    assert save_manager.save_game_state(game.to_dict())

    engine.victory({"level": 1, "gold": 0, "hp": 12, "max_hp": 12, "exp": 0}, game.current_floor)

    assert engine.state == GameStates.VICTORY
    assert save_manager.load_game_state() is not None
