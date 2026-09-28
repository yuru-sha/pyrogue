import json
from unittest.mock import Mock

from pyrogue.core.game_states import GameStates
from pyrogue.core.rogue_game import GAME_VERSION
from pyrogue.core.save_manager import SaveManager
from pyrogue.ui.screens.menu_screen import MenuScreen


def test_invalid_save_does_not_start_new_game(tmp_path):
    """メニューから不正なセーブをロードしても新規ゲームへ遷移しない。"""
    menu = MenuScreen.__new__(MenuScreen)
    menu.save_manager = SaveManager(tmp_path)
    menu.engine = Mock()
    menu.save_manager.save_file.write_text(json.dumps({"spec_version": "0.3.0"}), encoding="utf-8")

    assert menu._load_game() == GameStates.MENU
    menu.engine.new_game.assert_not_called()


def test_legacy_save_reports_in_menu_and_is_preserved(tmp_path):
    menu = MenuScreen.__new__(MenuScreen)
    menu.save_manager = SaveManager(tmp_path)
    menu.engine = Mock()
    menu.console = Mock(width=80, height=40)
    menu.menu_selection = 0
    menu.save_manager.save_file.write_text(
        json.dumps({"spec_version": GAME_VERSION, "player_stats": {}, "current_floor": 1}), encoding="utf-8"
    )
    before = menu.save_manager.save_file.read_bytes()

    assert menu._load_game() == GameStates.MENU
    menu.render()

    assert any(
        call.args[2] == "Failed to load save data: Unsupported legacy save format"
        for call in menu.console.print.call_args_list
    )
    assert menu.save_manager.save_file.read_bytes() == before
    menu.engine.new_game.assert_not_called()


def test_menu_restores_the_payload_it_already_consumed(tmp_path) -> None:
    from pyrogue.core.rogue_game import GameState
    from pyrogue.ui.screens.game_screen import GameScreen

    manager = SaveManager(tmp_path)
    saved_game = GameState(seed=1234)
    saved_game.player.gold = 42
    expected = saved_game.to_dict()
    assert manager.save_game_state(expected)

    menu = MenuScreen.__new__(MenuScreen)
    menu.save_manager = manager
    menu.engine = Mock()
    menu.engine.game_screen = GameScreen(None, seed=9999)

    assert menu._load_game() == GameStates.PLAYERS_TURN

    assert menu.engine.game_screen.rogue_game.to_dict() == expected


def test_menu_offers_load_when_only_backup_is_available(tmp_path) -> None:
    from pyrogue.core.rogue_game import GameState

    manager = SaveManager(tmp_path)
    assert manager.save_game_state(GameState(1234).to_dict())
    assert manager.save_game_state(GameState(5678).to_dict())
    manager.save_file.unlink()

    menu = MenuScreen.__new__(MenuScreen)
    menu.save_manager = manager

    assert "Load Game" in menu._get_menu_options()
