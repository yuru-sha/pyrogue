import json

import pytest

from pyrogue.core.rogue_game import GAME_VERSION, GameState, SaveCompatibilityError
from pyrogue.core.save_manager import SaveError, SaveManager


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


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"player": {}},
        {"spec_version": None},
        {"spec_version": 0.3},
        {"spec_version": "0.2.0"},
        {"version": GAME_VERSION},
    ],
)
def test_save_rejects_invalid_spec_version_without_touching_existing_save(tmp_path, payload):
    """不正な仕様バージョンのセーブは既存ファイルを変更しない。"""
    manager = SaveManager(tmp_path)
    valid_payload = {"spec_version": GAME_VERSION, "player_stats": {"hp": 10}, "current_floor": 1}
    assert manager.save_game_state(valid_payload)
    before = manager.save_file.read_bytes()

    assert not manager.save_game_state(payload)
    assert manager.save_file.read_bytes() == before
    assert manager.last_error is not None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"player": {}},
        {"spec_version": None},
        {"spec_version": 0.3},
        {"spec_version": "0.2.0"},
        {"version": GAME_VERSION},
    ],
)
def test_load_rejects_invalid_spec_version_without_touching_save_file(tmp_path, payload):
    """不正な仕様バージョンのロードはセーブファイルを変更しない。"""
    manager = SaveManager(tmp_path)
    manager.save_file.write_text(json.dumps(payload), encoding="utf-8")
    before = manager.save_file.read_bytes()

    assert manager.load_game_state() is None
    assert manager.save_file.read_bytes() == before
    assert manager.last_error is not None


def test_save_writes_exact_spec_version(tmp_path):
    """正常なセーブには現在の仕様バージョンをそのまま書き込む。"""
    manager = SaveManager(tmp_path)

    assert manager.save_game_state({"spec_version": GAME_VERSION, "player_stats": {"hp": 10}, "current_floor": 1})
    saved = json.loads(manager.save_file.read_text(encoding="utf-8"))

    assert saved["spec_version"] == GAME_VERSION


@pytest.mark.parametrize(
    "payload",
    [
        {"spec_version": GAME_VERSION},
        {"spec_version": GAME_VERSION, "player": {}},
    ],
)
def test_save_and_load_reject_current_version_without_required_shape(tmp_path, payload):
    """現行バージョンでもcanonical/legacyの必須項目がなければ拒否する。"""
    manager = SaveManager(tmp_path)
    manager.save_file.write_text(json.dumps(payload), encoding="utf-8")

    assert not manager.save_game_state(payload)
    assert manager.last_error is not None

    assert manager.load_game_state() is None
    assert isinstance(manager.last_error, SaveError)


def test_load_invalid_save_does_not_delete_files_when_metadata_marks_dead(tmp_path):
    """不正なセーブは死亡メタデータがあってもファイルを削除しない。"""
    manager = SaveManager(tmp_path)
    manager.save_file.write_text(json.dumps({"spec_version": "0.2.0"}), encoding="utf-8")
    manager.metadata_file.write_text(json.dumps({"is_alive": False}), encoding="utf-8")
    before_save = manager.save_file.read_bytes()
    before_metadata = manager.metadata_file.read_bytes()

    assert manager.load_game_state() is None
    assert manager.save_file.read_bytes() == before_save
    assert manager.metadata_file.read_bytes() == before_metadata


def test_checksum_failure_sets_error_for_invalid_save(tmp_path):
    """チェックサム不一致の不正セーブはファイルなしと区別できる。"""
    manager = SaveManager(tmp_path)
    manager.save_file.write_text(json.dumps({"spec_version": "0.2.0"}), encoding="utf-8")
    manager.checksum_file.write_text("invalid checksum", encoding="utf-8")
    before = manager.save_file.read_bytes()

    assert manager.load_game_state() is None
    assert manager.last_error is not None
    assert manager.save_file.read_bytes() == before
