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

    call = engine.victory_screen.set_victory_data.call_args
    assert call.args[1:] == (26, 1000)
