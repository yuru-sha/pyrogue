import json

import pytest

from pyrogue.core.rogue_game import GameState, SaveCompatibilityError
from pyrogue.core.save_manager import SaveManager


def test_save_load_preserves_canonical_state(tmp_path) -> None:
    game = GameState(1234)
    game.player.gold = 42
    manager = SaveManager(tmp_path)
    expected = game.to_dict()

    assert manager.save_game_state(expected)
    assert manager.save_file.suffix == ".json"
    loaded = manager.load_game_state()

    assert loaded == expected
    assert GameState.from_dict(loaded).to_dict() == expected


def test_save_manager_rejects_unsupported_spec_version(tmp_path) -> None:
    manager = SaveManager(tmp_path)
    assert manager.save_game_state(GameState(1234).to_dict())
    manager.checksum_file.unlink()
    payload = json.loads(manager.save_file.read_text(encoding="utf-8"))
    payload["spec_version"] = "0.2.0"
    manager.save_file.write_text(json.dumps(payload), encoding="utf-8")

    assert manager.load_game_state() is None
    assert manager.last_error is not None
    assert "Unsupported save version" in str(manager.last_error)
    with pytest.raises(SaveCompatibilityError):
        GameState.from_dict(payload)
