from pyrogue.core.save_manager import SaveManager
from pyrogue.ui.screens.game_screen import GameScreen


def test_game_screen_save_load(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAVE_DIRECTORY", str(tmp_path))
    game_screen = GameScreen(None, seed=1234)
    game = game_screen.rogue_game
    game.player.hp = 7
    game.player.gold = 42
    expected = game.to_dict()

    assert game_screen.save_game()
    assert SaveManager(tmp_path).save_file.exists()

    game.player.hp = 1
    game.player.gold = 999
    assert game_screen.load_game()

    assert game_screen.rogue_game.to_dict() == expected
