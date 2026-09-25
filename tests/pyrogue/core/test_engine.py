from types import SimpleNamespace
from unittest.mock import Mock

import tcod.event

from pyrogue.core.engine import Engine
from pyrogue.core.game_states import GameStates


def test_engine_passes_deepest_floor_to_victory_screen(monkeypatch) -> None:
    engine = Engine(seed=1234)
    engine.state = GameStates.PLAYERS_TURN
    engine.context = Mock()
    engine.game_screen.render = Mock()
    engine.victory_screen.render = Mock()
    engine.victory_screen.set_victory_data = Mock()
    engine.game_screen.rogue_game = SimpleNamespace(
        player=SimpleNamespace(
            level=1,
            exp=0,
            gold=0,
            hp=12,
            max_hp=12,
            monsters_killed=0,
            turns_played=0,
        ),
        current_floor=1,
        score=1000,
        victory_summary={"deepest_floor": 26, "score": 1000},
    )
    engine._handle_input = Mock(return_value=(True, GameStates.VICTORY))
    events = iter([[SimpleNamespace(type="KEYDOWN")], [SimpleNamespace(type="QUIT")]])
    monkeypatch.setattr(tcod.event, "wait", lambda: next(events))

    engine.run()
    engine.game_screen.render.assert_called_once_with(engine.console)

    call = engine.victory_screen.set_victory_data.call_args
    assert call.args[1:] == (26, 1000)
    engine.victory_screen.render.assert_called()


def test_engine_presents_each_key_event_before_processing_the_next(monkeypatch) -> None:
    engine = Engine(seed=1234)
    engine.context = Mock()
    events = iter(
        [
            [
                SimpleNamespace(type="KEYDOWN", key="first"),
                SimpleNamespace(type="KEYDOWN", key="second"),
                SimpleNamespace(type="QUIT"),
            ]
        ]
    )
    monkeypatch.setattr(tcod.event, "wait", lambda: next(events))

    sequence: list[str] = []
    engine._render_current_screen = Mock(side_effect=lambda: sequence.append("render"))
    engine.context.present.side_effect = lambda console: sequence.append("present")

    def handle_input(event):
        sequence.append(event.key)
        return True, None

    engine._handle_input = Mock(side_effect=handle_input)

    engine.run()

    assert sequence.index("present") < sequence.index("first")
    assert sequence.index("first") < sequence.index("second")
    assert sequence.index("render", sequence.index("first")) < sequence.index("second")
    assert sequence.index("present", sequence.index("first")) < sequence.index("second")
