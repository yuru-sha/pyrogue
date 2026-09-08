import json

import pytest

from pyrogue.core.rogue_game import (
    GAME_VERSION,
    MAX_FLOOR,
    GameState,
    GameStatus,
    SaveCompatibilityError,
)
from pyrogue.core.save_manager import SaveManager


def test_seed_reproduces_initial_state() -> None:
    assert GameState(1234).to_dict() == GameState(1234).to_dict()


def test_every_floor_has_reachable_stairs() -> None:
    generator = GameState(1234).generator

    for floor_number in range(1, MAX_FLOOR + 1):
        floor = generator.generate(floor_number)
        assert floor.up_stairs is not None
        if floor_number < MAX_FLOOR:
            assert floor.down_stairs is not None
            assert generator._path_exists(floor, floor.up_stairs, floor.down_stairs)


def test_vi_commands_do_not_collide_with_search() -> None:
    game = GameState(1234)
    position = game.player.position

    result = game.execute("s")

    assert result.success
    assert result.turn_consumed
    assert game.player.position == position


def test_command_aliases_share_dispatch() -> None:
    rest = GameState(1234)
    wait = GameState(1234)

    assert rest.execute("rest") == wait.execute("wait")
    assert rest.to_dict() == wait.to_dict()
    assert rest.player.equipped_item_ids == {rest.player.equipped_weapon, rest.player.equipped_armor}


def test_json_round_trip_preserves_future_state() -> None:
    game = GameState(1234)
    game.execute(".")

    restored = GameState.from_dict(json.loads(json.dumps(game.to_dict())))

    assert restored.to_dict() == game.to_dict()
    assert restored.execute(".") == game.execute(".")


def test_amulet_requires_returning_to_surface() -> None:
    game = GameState(1234)

    for _ in range(1, MAX_FLOOR):
        game.floor.monsters.clear()
        game.player.position = game.floor.down_stairs
        assert game.descend().success

    game.floor.monsters.clear()
    amulet = next(item for item in game.floor.items if item.name == "amulet of yendor")
    game.player.position = amulet.position
    assert game.pickup().success
    assert game.status == GameStatus.PLAYING

    for _ in range(1, MAX_FLOOR):
        game.floor.monsters.clear()
        game.player.position = game.floor.up_stairs
        assert game.ascend().success

    game.player.position = game.floor.up_stairs
    result = game.ascend()

    assert result.success
    assert game.status == GameStatus.VICTORY


def test_victory_summary_preserves_deepest_floor_after_return() -> None:
    game = GameState(1234)

    for _ in range(1, MAX_FLOOR):
        game.floor.monsters.clear()
        game.player.position = game.floor.down_stairs
        assert game.descend().success

    assert game.player.deepest_floor == MAX_FLOOR
    game.floor.monsters.clear()
    amulet = next(item for item in game.floor.items if item.name == "amulet of yendor")
    game.player.position = amulet.position
    assert game.pickup().success

    for _ in range(1, MAX_FLOOR):
        game.floor.monsters.clear()
        game.player.position = game.floor.up_stairs
        assert game.ascend().success

    game.player.position = game.floor.up_stairs
    result = game.ascend()

    assert result.data == {"deepest_floor": MAX_FLOOR, "score": game.score}
    saved = game.to_dict()
    assert saved["current_floor"] == 1
    assert saved["player"]["deepest_floor"] == MAX_FLOOR


def test_old_save_version_is_rejected() -> None:
    game = GameState(1234).to_dict()
    game["spec_version"] = "0.2.0"

    with pytest.raises(SaveCompatibilityError):
        GameState.from_dict(game)

    assert GAME_VERSION == "0.3.0"


def test_save_manager_persists_canonical_json(tmp_path) -> None:
    game = GameState(1234)
    manager = SaveManager(tmp_path)

    assert manager.save_game_state(game.to_dict())
    assert manager.save_file.suffix == ".json"
    restored = GameState.from_dict(manager.load_game_state())

    assert restored.to_dict() == game.to_dict()


def test_death_is_terminal_and_reports_score() -> None:
    game = GameState(1234)
    game._die("test")

    assert game.is_dead
    assert game.death_summary == {"score": game.score, "deepest_floor": 1, "cause": "test"}
    assert not game.execute(".").success
