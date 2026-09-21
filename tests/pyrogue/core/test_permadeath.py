"""
Permadeath機能のテストモジュール。

このモジュールは、SaveManagerのPermadeath機能を検証し、
プレイヤー死亡時のセーブデータ自動削除、セーブファイル暗号化、
整合性チェックなどの機能が正しく動作することを確認します。
"""

import json
import pickle
import tempfile
from unittest.mock import patch

from pyrogue.core.rogue_game import GAME_VERSION, GameState, ItemKind, ItemState
from pyrogue.core.save_manager import SaveManager


def _game_at_floor(seed: int, floor_number: int) -> GameState:
    game = GameState(seed)
    if floor_number != game.current_floor:
        floor = game._ensure_floor(floor_number)
        assert floor.up_stairs is not None
        game.current_floor = floor_number
        game.player.position = floor.up_stairs
        floor.player_position = floor.up_stairs
    return game


class TestPermadeathSystem:
    """Permadeath機能のテスト。"""

    def test_creates_missing_save_directory_parents(self, tmp_path):
        """存在しない親ディレクトリを含むセーブ先を作成する。"""
        save_dir = tmp_path / "missing" / "saves"

        save_manager = SaveManager(save_dir)

        assert save_manager.save_dir == save_dir
        assert save_dir.is_dir()

    def test_normal_save_and_load(self):
        """正常なセーブ・ロード機能のテスト。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            save_manager = SaveManager(temp_dir)

            game = _game_at_floor(1234, 3)
            game.player.inventory = [
                ItemState(id=9001, kind=ItemKind.WEAPON, name="sword"),
                ItemState(id=9002, kind=ItemKind.POTION, name="potion"),
            ]
            game_data = game.to_dict()
            game_data["player"].update({"hp": 50, "max_hp": 100, "level": 5, "exp": 1000})

            # セーブ
            success = save_manager.save_game_state(game_data)
            assert success is True

            # ロード
            loaded_data = save_manager.load_game_state()
            assert loaded_data is not None
            assert loaded_data["player"]["hp"] == 50
            assert loaded_data["current_floor"] == 3
            assert [item["name"] for item in loaded_data["player"]["inventory"]] == ["sword", "potion"]

    def test_permadeath_triggered_on_death(self):
        """プレイヤー死亡時のPermadeath発動テスト。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            save_manager = SaveManager(temp_dir)

            # セーブファイルを作成
            game_data = _game_at_floor(1234, 3).to_dict()
            save_manager.save_game_state(game_data)

            # セーブファイルが存在することを確認
            assert save_manager.has_save_file() is True

            # プレイヤー死亡データでPermadeath発動
            death_data = GameState(1234).to_dict()
            death_data["status"] = "dead"
            save_manager.trigger_permadeath_on_death(death_data)

            # セーブファイルが削除されることを確認
            assert save_manager.has_save_file() is False
            assert not save_manager.save_file.exists()
            assert not save_manager.backup_file.exists()
            assert not save_manager.metadata_file.exists()

    def test_dead_player_cannot_be_loaded(self):
        """死亡したプレイヤーのセーブデータがロードできないテスト。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            save_manager = SaveManager(temp_dir)

            # 死亡したプレイヤーのデータを作成
            game_data = _game_at_floor(1234, 3).to_dict()
            game_data["status"] = "dead"
            game_data["player"]["hp"] = 0

            # 直接メタデータを作成（死亡状態を記録）
            metadata = {
                "save_time": 1234567890,
                "save_version": GAME_VERSION,
                "player_level": 5,
                "current_floor": 3,
                "player_hp": 0,
                "player_max_hp": 100,
                "is_alive": False,  # 死亡状態
            }

            # ファイルを直接作成
            with open(save_manager.save_file, "w", encoding="utf-8") as f:
                json.dump(game_data, f)

            with open(save_manager.metadata_file, "w") as f:
                json.dump(metadata, f)

            # ロードを試行
            loaded_data = save_manager.load_game_state()

            # ロードが失敗することを確認
            assert loaded_data is None

            # Permadeathが発動してファイルが削除されることを確認
            assert not save_manager.save_file.exists()

    def test_checksum_verification(self):
        """チェックサム検証機能のテスト。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            save_manager = SaveManager(temp_dir)

            # セーブデータを作成
            game_data = GameState(1234).to_dict()
            game_data["player"]["hp"] = 50

            # セーブ
            success = save_manager.save_game_state(game_data)
            assert success is True

            # チェックサムファイルが作成されることを確認
            assert save_manager.checksum_file.exists()

            # 正常なロード
            loaded_data = save_manager.load_game_state()
            assert loaded_data is not None

            # セーブファイルを改竄（内容を変更）
            with open(save_manager.save_file, "wb") as f:
                tampered_data = game_data.copy()
                tampered_data["player"]["hp"] = 999  # 改竄
                pickle.dump(tampered_data, f)

            # 改竄されたファイルのロードは失敗することを確認
            loaded_data = save_manager.load_game_state()
            assert loaded_data is None

    def test_permadeath_prevents_save(self):
        """Permadeath発動後はセーブできないテスト。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            save_manager = SaveManager(temp_dir)

            # Permadeathを発動
            death_data = GameState(1234).to_dict()
            death_data["status"] = "dead"
            save_manager.trigger_permadeath_on_death(death_data)

            # Permadeath発動後はセーブできないことを確認
            new_data = GameState(5678).to_dict()
            new_data["player"]["hp"] = 100
            new_data["player"]["max_hp"] = 100
            new_data["player"]["level"] = 6

            success = save_manager.save_game_state(new_data)
            assert success is False
            assert not save_manager.save_file.exists()

    def test_save_info_retrieval(self):
        """セーブ情報取得機能のテスト。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            save_manager = SaveManager(temp_dir)

            # セーブデータを作成
            game_data = _game_at_floor(1234, 10).to_dict()
            game_data["player"].update({"hp": 75, "max_hp": 100, "level": 8})

            # セーブ
            save_manager.save_game_state(game_data)

            # セーブ情報を取得
            save_info = save_manager.get_save_info()
            assert save_info is not None
            assert save_info["player_level"] == 8
            assert save_info["current_floor"] == 10
            assert save_info["player_hp"] == 75
            assert save_info["player_max_hp"] == 100
            assert save_info["is_alive"] is True

    def test_manual_save_deletion(self):
        """手動セーブデータ削除機能のテスト。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            save_manager = SaveManager(temp_dir)

            # セーブデータを作成
            game_data = GameState(1234).to_dict()
            save_manager.save_game_state(game_data)

            # セーブファイルが存在することを確認
            assert save_manager.has_save_file() is True

            # 手動削除
            success = save_manager.delete_save_data()
            assert success is True

            # セーブファイルが削除されることを確認
            assert save_manager.has_save_file() is False
            assert not save_manager.save_file.exists()

    def test_backup_file_recovery(self):
        """バックアップファイルからの復旧機能のテスト。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            save_manager = SaveManager(temp_dir)

            # 最初のセーブ
            game_data1 = _game_at_floor(1234, 3).to_dict()
            game_data1["player"]["level"] = 5
            save_manager.save_game_state(game_data1)

            # 2回目のセーブ（バックアップが作成される）
            game_data2 = _game_at_floor(5678, 4).to_dict()
            game_data2["player"]["level"] = 6
            game_data2["player"]["hp"] = 75
            save_manager.save_game_state(game_data2)

            # メインセーブファイルを破損
            with open(save_manager.save_file, "wb") as f:
                f.write(b"corrupted data")

            # バックアップから復旧できることを確認
            loaded_data = save_manager.load_game_state()
            assert loaded_data is not None
            assert loaded_data["player"]["level"] == 5  # バックアップの内容
            assert loaded_data["current_floor"] == 3

    @patch("pyrogue.core.save_manager.game_logger")
    def test_error_handling(self, mock_logger):
        """エラーハンドリングのテスト。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            save_manager = SaveManager(temp_dir)

            # 存在しないファイルのロード
            loaded_data = save_manager.load_game_state()
            assert loaded_data is None
            mock_logger.info.assert_called_with("No save file found")

            # 存在しないファイルのセーブ情報取得
            save_info = save_manager.get_save_info()
            assert save_info is None
