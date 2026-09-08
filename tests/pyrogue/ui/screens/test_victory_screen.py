from unittest.mock import Mock

from pyrogue.ui.screens.victory_screen import VictoryScreen


def test_victory_screen_labels_deepest_floor() -> None:
    console = Mock(width=80, height=45)
    screen = VictoryScreen(console, None)
    screen.set_victory_data({"level": 1, "hp": 12, "max_hp": 12}, 26, 1000)

    screen.render()

    printed_strings = [call.args[2] for call in console.print.call_args_list]
    assert "Deepest Floor: B26F" in printed_strings
