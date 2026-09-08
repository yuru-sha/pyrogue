import json
from unittest.mock import Mock

from pyrogue.core.game_states import GameStates
from pyrogue.core.save_manager import SaveManager
from pyrogue.ui.screens.menu_screen import MenuScreen


def test_invalid_save_does_not_start_new_game(tmp_path):
    """メニューから不正なセーブをロードしても新規ゲームへ遷移しない。"""
    menu = MenuScreen.__new__(MenuScreen)
    menu.save_manager = SaveManager(tmp_path)
    menu.engine = Mock()
    menu.save_manager.save_file.write_text(json.dumps({"spec_version": "0.2.0"}), encoding="utf-8")

    assert menu._load_game() == GameStates.MENU
    menu.engine.new_game.assert_not_called()
