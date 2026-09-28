import json

import pytest

from pyrogue.core.rogue_game import GAME_VERSION, GameState, ItemKind, ItemState, MonsterState, SaveCompatibilityError
from pyrogue.core.save_manager import SaveError, SaveManager

_LEGACY_SAVE_PAYLOADS = [
    pytest.param({"spec_version": GAME_VERSION, "player_stats": {}, "current_floor": 1}, id="player-stats"),
    pytest.param(
        {"spec_version": GAME_VERSION, "player": {}, "inventory": {}, "current_floor": 1, "floor_data": {}},
        id="player-floor-data",
    ),
]


def test_save_load_preserves_canonical_state(tmp_path) -> None:
    game = GameState(1234)
    game.player.gold = 42
    game.player.blind_turns = 4
    game.player.faint_turns = 3
    game.player.monster_confusion_ready = True
    game.player.identified_item_names.append("healing potion")
    game.player.max_strength = 21
    game.player.inventory[0].called_name = "last resort"
    game._floors_without_food = 3
    game._wander_turns = 41
    game._wander_checks = 2
    monster = game.floor.monsters[0]
    monster.hp -= 1
    monster.running = True
    monster.held = True
    monster.invisible = True
    monster.hasted = True
    monster.slowed = True
    monster.slow_turn = False
    monster.confused_turns = 5
    monster.cancelled = True
    monster.mean_override = True
    monster.level_bonus = 2
    monster.revealed = True
    monster.carried_items.append(ItemState(9998, ItemKind.POTION, "healing potion"))
    monster.target_item_id = game.floor.items[0].id
    monster.carry_search_room_index = 0
    game.floor.monsters.append(MonsterState(9999, "xeroc", 1, 1, 5, disguise="stairs"))
    manager = SaveManager(tmp_path)
    expected = game.to_dict()

    assert manager.save_game_state(expected)
    assert manager.save_file.suffix == ".json"
    loaded = manager.load_game_state()

    assert loaded == expected
    restored = GameState.from_dict(loaded)
    assert restored.to_dict() == expected
    assert restored.floor.monsters[0].carry_search_room_index == 0
    assert restored.player.blind_turns == 4
    assert restored.player.faint_turns == 3
    assert restored.player.monster_confusion_ready
    assert restored.player.max_strength == 21
    assert restored.floor.monsters[0].mean_override
    assert restored._floors_without_food == 3
    assert restored.player.inventory[0].called_name == "last resort"


def test_load_defaults_new_monster_fields_for_older_saves() -> None:
    old_state = GameState(1234).to_dict()
    old_monster = old_state["floors"]["1"]["monsters"][0]
    old_monster.pop("level_bonus")
    old_monster.pop("revealed")
    old_monster.pop("disguise")
    old_monster.pop("carried_items")
    old_monster.pop("target_item_id")
    old_monster.pop("carry_search_room_index")
    old_monster.pop("mean_override")
    old_state["player"].pop("max_strength")
    for field in ("held", "invisible", "hasted", "slowed", "slow_turn", "confused_turns", "cancelled"):
        old_monster.pop(field)

    monster = GameState.from_dict(old_state).floor.monsters[0]

    assert monster.level_bonus == 0
    assert not monster.revealed
    assert monster.disguise is None
    assert monster.carried_items == []
    assert monster.target_item_id is None
    assert monster.carry_search_room_index is None
    assert not monster.held
    assert not monster.invisible
    assert not monster.hasted
    assert not monster.slowed
    assert monster.confused_turns == 0
    assert not monster.cancelled
    assert not monster.mean_override
    assert monster.slow_turn


def test_save_load_preserves_wandering_and_slow_turn_continuity() -> None:
    data = GameState(4321).to_dict()
    data["wander_turns"] = 2
    data["wander_checks"] = 3
    monster = data["floors"]["1"]["monsters"][0]
    monster["slowed"] = True
    monster["slow_turn"] = True
    uninterrupted = GameState.from_dict(data)
    restored = GameState.from_dict(json.loads(json.dumps(uninterrupted.to_dict())))

    for _ in range(4):
        uninterrupted.execute("wait")
        restored.execute("wait")

    assert restored.to_dict() == uninterrupted.to_dict()


@pytest.mark.parametrize("missing_field", ["wander_turns", "wander_checks"])
def test_save_manager_rejects_missing_wandering_state(tmp_path, missing_field: str) -> None:
    manager = SaveManager(tmp_path)
    payload = GameState(4321).to_dict()
    del payload[missing_field]

    assert not manager.save_game_state(payload)
    assert manager.last_error is not None
    assert missing_field in str(manager.last_error)
    with pytest.raises(SaveCompatibilityError):
        GameState.from_dict(payload)


def test_save_manager_rejects_unsupported_spec_version(tmp_path) -> None:
    manager = SaveManager(tmp_path)
    assert manager.save_game_state(GameState(1234).to_dict())
    manager.checksum_file.unlink()
    payload = json.loads(manager.save_file.read_text(encoding="utf-8"))
    payload["spec_version"] = "0.3.4"
    manager.save_file.write_text(json.dumps(payload), encoding="utf-8")

    assert manager.load_game_state() is None
    assert manager.last_error is not None
    assert "Unsupported save version" in str(manager.last_error)
    with pytest.raises(SaveCompatibilityError):
        GameState.from_dict(payload)


@pytest.mark.parametrize(
    "payload",
    _LEGACY_SAVE_PAYLOADS,
)
def test_load_rejects_legacy_save_shapes_without_deleting_them(tmp_path, payload):
    manager = SaveManager(tmp_path)
    manager.save_file.write_text(json.dumps(payload), encoding="utf-8")
    before = manager.save_file.read_bytes()

    assert manager.load_game_state() is None
    assert isinstance(manager.last_error, SaveError)
    assert "legacy" in str(manager.last_error).lower()
    assert manager.save_file.read_bytes() == before
    assert not manager.is_permadeath_triggered


@pytest.mark.parametrize(
    "payload",
    _LEGACY_SAVE_PAYLOADS,
)
def test_save_rejects_legacy_shapes_without_touching_existing_save(tmp_path, payload):
    manager = SaveManager(tmp_path)
    assert manager.save_game_state(GameState(1234).to_dict())
    before = manager.save_file.read_bytes()

    assert not manager.save_game_state(payload)
    assert isinstance(manager.last_error, SaveError)
    assert "legacy" in str(manager.last_error).lower()
    assert manager.save_file.read_bytes() == before


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"player": {}},
        {"spec_version": None},
        {"spec_version": 0.3},
        {"spec_version": "0.3.0"},
        {"version": GAME_VERSION},
    ],
)
def test_save_rejects_invalid_spec_version_without_touching_existing_save(tmp_path, payload):
    """不正な仕様バージョンのセーブは既存ファイルを変更しない。"""
    manager = SaveManager(tmp_path)
    valid_payload = GameState(1234).to_dict()
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
        {"spec_version": "0.3.0"},
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

    assert manager.save_game_state(GameState(1234).to_dict())
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
    """現行バージョンでもcanonicalの必須項目がなければ拒否する。"""
    manager = SaveManager(tmp_path)
    manager.save_file.write_text(json.dumps(payload), encoding="utf-8")

    assert not manager.save_game_state(payload)
    assert manager.last_error is not None

    assert manager.load_game_state() is None
    assert isinstance(manager.last_error, SaveError)


def test_load_invalid_save_does_not_delete_files_when_metadata_marks_dead(tmp_path):
    """不正なセーブは死亡メタデータがあってもファイルを削除しない。"""
    manager = SaveManager(tmp_path)
    manager.save_file.write_text(json.dumps({"spec_version": "0.3.0"}), encoding="utf-8")
    manager.metadata_file.write_text(json.dumps({"is_alive": False}), encoding="utf-8")
    before_save = manager.save_file.read_bytes()
    before_metadata = manager.metadata_file.read_bytes()

    assert manager.load_game_state() is None
    assert manager.save_file.read_bytes() == before_save
    assert manager.metadata_file.read_bytes() == before_metadata


def test_checksum_failure_sets_error_for_invalid_save(tmp_path):
    """チェックサム不一致の不正セーブはファイルなしと区別できる。"""
    manager = SaveManager(tmp_path)
    manager.save_file.write_text(json.dumps({"spec_version": "0.3.0"}), encoding="utf-8")
    manager.checksum_file.write_text("invalid checksum", encoding="utf-8")
    before = manager.save_file.read_bytes()

    assert manager.load_game_state() is None
    assert manager.last_error is not None
    assert manager.save_file.read_bytes() == before


def test_checksum_failure_rejects_dead_backup_payload_and_cleans_up(tmp_path):
    """チェックサム失敗時も死亡バックアップをロードしない。"""
    manager = SaveManager(tmp_path)
    dead_payload = GameState(1234).to_dict()
    dead_payload["status"] = "dead"
    assert manager.save_game_state(dead_payload)
    manager.metadata_file.write_text(json.dumps({"is_alive": True}), encoding="utf-8")
    manager.backup_file.write_bytes(manager.save_file.read_bytes())
    manager.save_file.write_text("corrupted", encoding="utf-8")

    assert manager.load_game_state() is None
    assert manager.is_permadeath_triggered
    assert not manager.save_file.exists()
    assert not manager.backup_file.exists()
    assert not manager.metadata_file.exists()


def test_checksum_failure_does_not_resurrect_backup_after_dead_metadata(tmp_path):
    """死亡メタデータがあれば、古い生存バックアップも復旧しない。"""
    manager = SaveManager(tmp_path)
    first_payload = GameState(1234).to_dict()
    second_payload = GameState(5678).to_dict()
    assert manager.save_game_state(first_payload)
    assert manager.save_game_state(second_payload)
    manager.metadata_file.write_text(json.dumps({"is_alive": False}), encoding="utf-8")
    manager.save_file.write_text("corrupted", encoding="utf-8")

    assert manager.load_game_state() is None
    assert manager.is_permadeath_triggered
    assert not manager.save_file.exists()
    assert not manager.backup_file.exists()
    assert not manager.metadata_file.exists()


def test_successful_restore_consumes_save_and_all_recovery_artifacts(tmp_path) -> None:
    manager = SaveManager(tmp_path)
    first = GameState(1234).to_dict()
    second = GameState(5678).to_dict()
    assert manager.save_game_state(first)
    assert manager.save_game_state(second)
    assert manager.backup_file.exists()

    restored = manager.load_game_state()

    assert restored == second
    assert manager.load_game_state() is None
    assert not manager.save_file.exists()
    assert not manager.backup_file.exists()
    assert not manager.metadata_file.exists()
    assert not manager.checksum_file.exists()
    third = GameState(9012).to_dict()
    assert manager.save_game_state(third)
    assert manager.load_game_state() == third


def test_incompatible_main_save_restores_valid_backup(tmp_path) -> None:
    manager = SaveManager(tmp_path)
    payload = GameState(1234).to_dict()
    assert manager.save_game_state(payload)
    before = manager.save_file.read_bytes()
    manager.backup_file.write_bytes(before)

    incompatible_payload = dict(payload)
    incompatible_payload["player"] = None
    manager.save_file.write_text(json.dumps(incompatible_payload), encoding="utf-8")
    manager._save_checksum()

    assert manager.load_game_state() == payload
    assert not manager.save_file.exists()
    assert not manager.backup_file.exists()
    assert not manager.metadata_file.exists()
    assert not manager.checksum_file.exists()


def test_failed_consumption_marker_write_preserves_save_artifacts(tmp_path, monkeypatch) -> None:
    from pathlib import Path

    manager = SaveManager(tmp_path)
    payload = GameState(1234).to_dict()
    assert manager.save_game_state(payload)
    manager.backup_file.write_bytes(manager.save_file.read_bytes())
    save_bytes = manager.save_file.read_bytes()
    backup_bytes = manager.backup_file.read_bytes()
    write_text = Path.write_text

    def fail_after_partial_write(path, *args, **kwargs):
        result = write_text(path, *args, **kwargs)
        if path == manager.consumed_temp_file:
            raise OSError
        return result

    with monkeypatch.context() as patch:
        patch.setattr(Path, "write_text", fail_after_partial_write)
        assert manager.load_game_state() is None

    assert manager.save_file.read_bytes() == save_bytes
    assert manager.backup_file.read_bytes() == backup_bytes
    assert not manager.consumed_file.exists()
    assert manager.load_game_state() == payload


def test_checksum_write_failure_keeps_previous_save_loadable(tmp_path, monkeypatch) -> None:
    from pathlib import Path

    manager = SaveManager(tmp_path)
    assert manager.save_game_state(GameState(1234).to_dict())
    expected = GameState(5678).to_dict()
    assert manager.save_game_state(expected)
    previous_backup_bytes = manager.backup_file.read_bytes()
    saved_bytes = manager.save_file.read_bytes()
    saved_checksum = manager.checksum_file.read_bytes()
    saved_metadata = manager.metadata_file.read_bytes()
    write_text = Path.write_text
    checksum_temp_file = manager.checksum_file.with_suffix(".tmp")

    def fail_checksum_write(path, *args, **kwargs):
        result = write_text(path, *args, **kwargs)
        if path == checksum_temp_file:
            raise OSError
        return result

    failed_save = GameState(9999).to_dict()
    failed_save["status"] = "dead"
    with monkeypatch.context() as patch:
        patch.setattr(Path, "write_text", fail_checksum_write)
        assert not manager.save_game_state(failed_save)

    assert manager.save_file.read_bytes() == saved_bytes
    assert manager.backup_file.read_bytes() == previous_backup_bytes
    assert manager.checksum_file.read_bytes() == saved_checksum
    assert manager.metadata_file.read_bytes() == saved_metadata
    assert manager.load_game_state() == expected


def test_unusable_main_save_falls_back_to_valid_backup_without_losing_it(tmp_path) -> None:
    manager = SaveManager(tmp_path)
    expected = GameState(1234).to_dict()
    assert manager.save_game_state(expected)
    assert manager.save_game_state(GameState(5678).to_dict())
    malformed = GameState(9999).to_dict()
    malformed["floors"]["1"]["tiles"] = []
    manager.save_file.write_text(json.dumps(malformed), encoding="utf-8")
    manager.checksum_file.unlink()

    restored = manager.load_game_state()

    assert restored == expected
    assert manager.consumed_file.exists()
    assert not manager.save_file.exists()
    assert not manager.backup_rollback_file.exists()
    assert not manager.backup_file.exists()
    assert manager.load_game_state() is None


def test_failed_backup_rename_preserves_current_save(tmp_path, monkeypatch) -> None:
    from pathlib import Path

    manager = SaveManager(tmp_path)
    expected = GameState(1234).to_dict()
    assert manager.save_game_state(expected)
    save_bytes = manager.save_file.read_bytes()
    checksum_bytes = manager.checksum_file.read_bytes()
    metadata_bytes = manager.metadata_file.read_bytes()
    replace = Path.replace

    def fail_current_save_rename(path, target):
        if path == manager.save_file:
            raise OSError
        return replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_current_save_rename)

    assert not manager.save_game_state(GameState(5678).to_dict())

    assert manager.save_file.read_bytes() == save_bytes
    assert manager.checksum_file.read_bytes() == checksum_bytes
    assert manager.metadata_file.read_bytes() == metadata_bytes


def test_metadata_write_failure_preserves_previous_save_and_metadata(tmp_path, monkeypatch) -> None:
    from pathlib import Path

    manager = SaveManager(tmp_path)
    expected = GameState(1234).to_dict()
    assert manager.save_game_state(expected)
    save_bytes = manager.save_file.read_bytes()
    checksum_bytes = manager.checksum_file.read_bytes()
    metadata_bytes = manager.metadata_file.read_bytes()
    write_text = Path.write_text
    metadata_temp_file = manager.metadata_file.with_suffix(".tmp")

    def fail_after_partial_write(path, *args, **kwargs):
        result = write_text(path, *args, **kwargs)
        if path == metadata_temp_file:
            raise OSError
        return result

    with monkeypatch.context() as patch:
        patch.setattr(Path, "write_text", fail_after_partial_write)
        assert not manager.save_game_state(GameState(5678).to_dict())

    assert manager.save_file.read_bytes() == save_bytes
    assert manager.checksum_file.read_bytes() == checksum_bytes
    assert manager.metadata_file.read_bytes() == metadata_bytes
    assert manager.load_game_state() == expected


def test_out_of_bounds_player_save_falls_back_to_valid_backup(tmp_path) -> None:
    manager = SaveManager(tmp_path)
    expected = GameState(1234).to_dict()
    assert manager.save_game_state(expected)
    assert manager.save_game_state(GameState(5678).to_dict())
    unusable = GameState(9999).to_dict()
    unusable["player"]["x"] = 10_000
    unusable["player"]["y"] = 10_000
    manager.save_file.write_text(json.dumps(unusable), encoding="utf-8")
    manager.checksum_file.unlink()

    assert manager.load_game_state() == expected


def test_wall_position_save_falls_back_to_valid_backup(tmp_path) -> None:
    manager = SaveManager(tmp_path)
    expected = GameState(1234).to_dict()
    assert manager.save_game_state(expected)
    assert manager.save_game_state(GameState(5678).to_dict())
    unusable = GameState(9999).to_dict()
    unusable["player"]["x"] = 0
    unusable["player"]["y"] = 0
    manager.save_file.write_text(json.dumps(unusable), encoding="utf-8")
    manager.checksum_file.unlink()

    assert manager.load_game_state() == expected


def test_restore_uses_backup_when_save_rollback_cannot_restore_main(tmp_path, monkeypatch) -> None:
    import builtins
    from pathlib import Path

    manager = SaveManager(tmp_path)
    assert manager.save_game_state(GameState(1234).to_dict())
    expected = GameState(5678).to_dict()
    assert manager.save_game_state(expected)
    expected_bytes = manager.save_file.read_bytes()
    real_open = builtins.open
    replace = Path.replace

    def fail_new_main_write(file, mode="r", *args, **kwargs):
        if Path(file) == manager.save_file and mode == "w":
            raise OSError
        return real_open(file, mode, *args, **kwargs)

    def fail_main_restore(path, target):
        if path == manager.backup_file and target == manager.save_file:
            raise OSError
        return replace(path, target)

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "open", fail_new_main_write)
        patch.setattr(Path, "replace", fail_main_restore)
        assert not manager.save_game_state(GameState(9999).to_dict())

    assert not manager.save_file.exists()
    assert manager.backup_file.read_bytes() == expected_bytes
    assert manager.has_save_file()
    assert manager.load_game_state() == expected
    assert not manager.has_save_file()
