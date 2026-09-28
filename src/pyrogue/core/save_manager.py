"""
セーブ/ロード機能管理モジュール。

このモジュールは、ゲーム状態の保存と復元を担当します。
パーマデス機能を維持しながら、プレイヤーの進行状況を
安全に保存・復元できるようにします。

Features:
    - ゲーム状態の完全なシリアライゼーション
    - パーマデス制御（死亡時セーブデータ削除）
    - セーブファイルの整合性チェック
    - セーブデータの暗号化（改ざん防止）

"""

from __future__ import annotations

import contextlib
import hashlib
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pyrogue.core.rogue_game import GAME_VERSION
from pyrogue.utils.logger import game_logger

if TYPE_CHECKING:
    from pyrogue.core.rogue_game import GameState


class SaveError(Exception):
    """セーブ・ロード処理で発生するエラー。"""


class SaveManager:
    """
    セーブ/ロード機能を管理するクラス。

    パーマデス機能を維持しながら、ゲーム状態の保存と復元を行います。
    セーブデータの整合性チェックと改ざん防止機能も提供します。

    Attributes
    ----------
        save_dir: セーブデータディレクトリのパス
        save_file: メインセーブファイルのパス
        backup_file: バックアップセーブファイルのパス
        is_permadeath_triggered: パーマデスが発動されたかどうか

    """

    def __init__(self, save_dir: str | None = None) -> None:
        """
        SaveManagerを初期化。

        Args:
        ----
            save_dir: セーブデータを保存するディレクトリ（Noneの場合は環境変数から取得）

        """
        if save_dir is None:
            from pyrogue.config.env import get_save_directory

            save_dir = get_save_directory()
        self.save_dir = Path(save_dir)
        self.save_file = self.save_dir / "game_save.json"
        self.backup_file = self.save_dir / "game_save_backup.json"
        self.backup_rollback_file = self.save_dir / "game_save_backup.rollback"
        self.metadata_file = self.save_dir / "save_metadata.json"
        self.checksum_file = self.save_dir / "save_checksum.txt"
        self.consumed_file = self.save_dir / "game_save_consumed"
        self.consumed_temp_file = self.save_dir / "game_save_consumed.tmp"
        self.is_permadeath_triggered = False
        self.last_error: SaveError | None = None

        # セーブディレクトリを作成
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def save_game_state(self, game_data: dict[str, Any]) -> bool:
        """
        ゲーム状態を保存。

        Args:
        ----
            game_data: 保存するゲームデータ

        Returns:
        -------
            bool: 保存に成功した場合はTrue

        """
        if self.is_permadeath_triggered:
            game_logger.warning("Cannot save game: permadeath is active")
            return False

        self.last_error = None
        if self.consumed_file.exists():
            try:
                self._clear_save_artifacts()
                self.consumed_file.unlink()
            except OSError as error:
                self.last_error = SaveError(f"Failed to clear consumed save artifacts: {error}")
                return False
        if not self._check_save_version(game_data):
            game_logger.warning("Cannot save game: invalid save payload")
            return False

        try:
            previous_metadata = self.metadata_file.read_bytes() if self.metadata_file.exists() else None
        except OSError as error:
            self.last_error = SaveError(f"Failed to read existing save metadata: {error}")
            return False
        if self.backup_rollback_file.exists():
            try:
                if self.backup_file.exists():
                    self.backup_rollback_file.unlink()
                else:
                    self.backup_rollback_file.replace(self.backup_file)
            except OSError as error:
                self.last_error = SaveError(f"Failed to recover previous backup: {error}")
                return False

        had_current_save = self.save_file.exists()
        moved_current_save = False
        moved_previous_backup = False
        try:
            player_data = game_data.get("player_stats", game_data.get("player", {}))
            player_hp = player_data.get("hp", 20)
            metadata = {
                "save_time": time.time(),
                "save_version": GAME_VERSION,
                "spec_version": GAME_VERSION,
                "player_level": player_data.get("level", 1),
                "current_floor": game_data.get("current_floor", 1),
                "player_hp": player_hp,
                "player_max_hp": player_data.get("hp_max", player_data.get("max_hp", 20)),
                "is_alive": game_data.get("status") != "dead" and player_hp > 0,
            }

            if self.backup_file.exists():
                self.backup_file.replace(self.backup_rollback_file)
                moved_previous_backup = True
            if self.save_file.exists():
                self.save_file.replace(self.backup_file)
                moved_current_save = True

            with open(self.save_file, "w", encoding="utf-8") as f:
                json.dump(game_data, f, ensure_ascii=False, indent=2)
            self._atomic_write(self.metadata_file, json.dumps(metadata, indent=2))
            self._save_checksum()
        except Exception as error:
            self.last_error = error if isinstance(error, SaveError) else SaveError(str(error))
            game_logger.error(f"Failed to save game: {error}")
            rollback_main_succeeded = True
            try:
                if moved_current_save and self.backup_file.exists():
                    self.backup_file.replace(self.save_file)
                elif not had_current_save:
                    self.save_file.unlink(missing_ok=True)
            except OSError as rollback_error:
                game_logger.error(f"Failed to restore previous save: {rollback_error}")
                rollback_main_succeeded = False
            if moved_previous_backup and rollback_main_succeeded and self.backup_rollback_file.exists():
                try:
                    self.backup_rollback_file.replace(self.backup_file)
                except OSError as rollback_error:
                    game_logger.error(f"Failed to restore previous backup: {rollback_error}")
            try:
                if previous_metadata is None:
                    self.metadata_file.unlink(missing_ok=True)
                else:
                    self._atomic_write(self.metadata_file, previous_metadata)
            except (OSError, SaveError) as rollback_error:
                game_logger.error(f"Failed to restore previous save metadata: {rollback_error}")
            return False
        if moved_previous_backup:
            with contextlib.suppress(OSError):
                self.backup_rollback_file.unlink(missing_ok=True)
        game_logger.info(f"Game saved successfully to {self.save_file}")
        return True

    def load_game_state(self) -> dict[str, Any] | None:
        """
        ゲーム状態を読み込み。

        Returns
        -------
            Optional[Dict[str, Any]]: 読み込んだゲームデータ。失敗時はNone

        """
        self.last_error = None
        if self.consumed_file.exists():
            try:
                self._clear_save_artifacts()
            except OSError as error:
                self.last_error = SaveError(f"Failed to clear consumed save artifacts: {error}")
            return None
        if not self.save_file.exists():
            return self._load_backup()

        try:
            if not self._verify_checksum():
                game_logger.warning("Save file integrity check failed - potential tampering detected")
                self.last_error = SaveError("Save file integrity check failed")
                try:
                    with open(self.save_file, encoding="utf-8") as f:
                        self._check_save_version(json.load(f))
                except Exception as main_error:
                    self.last_error = main_error if isinstance(main_error, SaveError) else SaveError(str(main_error))
                return self._load_backup()

            with open(self.save_file, encoding="utf-8") as f:
                game_data = json.load(f)
            restored = self._restore_and_consume(game_data)
            return restored if restored is not None else self._load_backup()
        except Exception as error:
            self.last_error = error if isinstance(error, SaveError) else SaveError(str(error))
            game_logger.error(f"Failed to load game: {error}")
            return self._load_backup()

    def _load_backup(self) -> dict[str, Any] | None:
        """Restore from backup when the main save is unreadable or unusable."""
        for backup_file in (self.backup_file, self.backup_rollback_file):
            if not backup_file.exists():
                continue
            try:
                with open(backup_file, encoding="utf-8") as f:
                    game_data = json.load(f)
                restored = self._restore_and_consume(game_data)
                if restored is not None:
                    return restored
            except Exception as error:
                game_logger.error(f"Backup file also corrupted: {error}")
        return None

    def _restore_and_consume(self, game_data: dict[str, Any]) -> dict[str, Any] | None:
        """Validate a canonical restore before marking and deleting its save artifacts."""
        if not self._check_save_version(game_data) or not self._check_permadeath(game_data):
            return None
        try:
            from pyrogue.core.rogue_game import GameState

            GameState.from_dict(game_data)
        except (KeyError, TypeError, ValueError) as error:
            self.last_error = SaveError(f"Save data is not restorable: {error}")
            return None

        try:
            self._atomic_write(self.consumed_file, "consumed")
        except SaveError as error:
            self.last_error = SaveError(f"Failed to mark restored save as consumed: {error}")
            return None
        try:
            self._clear_save_artifacts()
        except OSError as error:
            game_logger.warning(f"Restored save artifacts could not all be removed: {error}")
        return game_data

    def _atomic_write(self, path: Path, content: str | bytes) -> None:
        """Replace a file only after its complete contents have been written."""
        temporary_file = path.with_suffix(".tmp")
        try:
            if isinstance(content, bytes):
                temporary_file.write_bytes(content)
            else:
                temporary_file.write_text(content, encoding="utf-8")
            temporary_file.replace(path)
        except OSError as error:
            with contextlib.suppress(OSError):
                temporary_file.unlink(missing_ok=True)
            raise SaveError(f"Failed to atomically write {path.name}: {error}") from error

    def _clear_save_artifacts(self) -> None:
        """Remove every file that could restore or describe a consumed session."""
        for path in (
            self.save_file,
            self.backup_file,
            self.backup_rollback_file,
            self.metadata_file,
            self.checksum_file,
        ):
            path.unlink(missing_ok=True)

    def _check_permadeath(self, game_data: dict[str, Any]) -> bool:
        """Reject and delete saves whose payload or metadata records a dead player."""
        player_data = game_data.get("player_stats", game_data.get("player", {}))
        if game_data.get("status") == "dead" or ("player_stats" in game_data and player_data.get("hp", 20) <= 0):
            game_logger.warning("Cannot load game: player is dead (permadeath)")
            self._trigger_permadeath()
            return False

        if not self.metadata_file.exists():
            return True

        with open(self.metadata_file) as f:
            metadata = json.load(f)

        if metadata.get("is_alive", True):
            return True

        game_logger.warning("Cannot load game: player is dead (permadeath)")
        self._trigger_permadeath()
        return False

    def _check_save_version(self, game_data: Any) -> bool:
        """Validate the JSON save envelope and its exact specification version."""
        if not isinstance(game_data, dict):
            self.last_error = SaveError("Save data must be a JSON object")
            return False
        if "spec_version" not in game_data:
            self.last_error = SaveError("Save is missing the PyRogue specification version")
            return False
        save_version = game_data["spec_version"]
        if not isinstance(save_version, str):
            self.last_error = SaveError("Save specification version must be a string")
            return False
        if save_version != GAME_VERSION:
            self.last_error = SaveError(f"Unsupported save version: {save_version}")
            return False

        if {"player_stats", "current_floor"} <= game_data.keys() or {
            "player",
            "inventory",
            "current_floor",
            "floor_data",
        } <= game_data.keys():
            self.last_error = SaveError("Unsupported legacy save format")
            return False

        required_keys = ("seed", "player", "floors", "rng_state", "wander_turns", "wander_checks")
        object_fields = ("player", "floors")

        missing_keys = [key for key in required_keys if key not in game_data]
        if missing_keys:
            self.last_error = SaveError(f"Save data is missing required fields: {', '.join(missing_keys)}")
            return False
        for field in object_fields:
            if not isinstance(game_data[field], dict):
                self.last_error = SaveError(f"Save field must be a JSON object: {field}")
                return False
        return True

    def _trigger_permadeath(self) -> None:
        """
        パーマデスを発動（セーブデータを削除）。

        プレイヤーが死亡した場合に呼び出され、
        セーブデータとメタデータを削除します。

        """
        self.is_permadeath_triggered = True

        try:
            # セーブファイルを削除
            if self.save_file.exists():
                self.save_file.unlink()
                game_logger.info("Main save file deleted (permadeath)")

            # バックアップファイルを削除
            if self.backup_file.exists():
                self.backup_file.unlink()
                game_logger.info("Backup save file deleted (permadeath)")

            if self.backup_rollback_file.exists():
                self.backup_rollback_file.unlink()

            # メタデータファイルを削除
            if self.metadata_file.exists():
                self.metadata_file.unlink()
                game_logger.info("Save metadata deleted (permadeath)")

            # チェックサムファイルを削除
            if self.checksum_file.exists():
                self.checksum_file.unlink()
                game_logger.info("Save checksum deleted (permadeath)")

        except Exception as e:
            game_logger.error(f"Error during permadeath cleanup: {e}")

    def finalize_death(self, game: GameState) -> dict[str, Any] | None:
        """Apply shared permadeath cleanup and return the canonical death summary."""
        if not game.is_dead:
            return None
        self._trigger_permadeath()
        return game.death_summary

    def trigger_permadeath_on_death(self, game_data: dict[str, Any]) -> None:
        """
        旧シリアライズ済みゲームデータに対してパーマデスを発動。

        正規のGameStateを扱う呼び出し元は、共有後処理の ``finalize_death``
        を使用します。

        Args:
        ----
            game_data: 現在のゲームデータ

        """
        if "player" in game_data and "status" in game_data:
            if game_data.get("status") == "dead":
                self._trigger_permadeath()
            return
        player_data = game_data.get("player_stats", game_data.get("player", {}))
        player_hp = player_data.get("hp", 0)
        if player_hp <= 0:
            game_logger.warning("Player died - triggering permadeath")
            self._trigger_permadeath()

    def has_save_file(self) -> bool:
        """
        セーブファイルが存在するかチェック。

        Returns
        -------
            bool: セーブファイルが存在する場合はTrue

        """
        if self.is_permadeath_triggered or self.consumed_file.exists():
            return False
        return any(path.exists() for path in (self.save_file, self.backup_file, self.backup_rollback_file))

    def get_save_info(self) -> dict[str, Any] | None:
        """
        セーブファイルの情報を取得。

        Returns
        -------
            Optional[Dict[str, Any]]: セーブファイルの情報。存在しない場合はNone

        """
        if not self.metadata_file.exists():
            return None

        try:
            with open(self.metadata_file) as f:
                metadata = json.load(f)
            return metadata
        except Exception as e:
            game_logger.error(f"Failed to read save metadata: {e}")
            return None

    def delete_save_data(self) -> bool:
        """
        セーブデータを手動で削除。

        Returns
        -------
            bool: 削除に成功した場合はTrue

        """
        try:
            self._trigger_permadeath()
            return True
        except Exception as e:
            game_logger.error(f"Failed to delete save data: {e}")
            return False

    def _calculate_checksum(self, file_path: Path) -> str:
        """
        ファイルのSHA256チェックサムを計算。

        Args:
        ----
            file_path: チェックサムを計算するファイルのパス

        Returns:
        -------
            SHA256チェックサムの16進数表現

        """
        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            game_logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""

    def _save_checksum(self) -> None:
        """Write a checksum atomically or fail the containing save operation."""
        if not self.save_file.exists():
            raise SaveError("Cannot checksum missing save file")

        checksum = self._calculate_checksum(self.save_file)
        if not checksum:
            raise SaveError("Failed to calculate save checksum")
        self._atomic_write(self.checksum_file, checksum)

    def _verify_checksum(self) -> bool:
        """
        セーブファイルの整合性をチェックサムで検証。

        Returns
        -------
            bool: チェックサムが一致する場合はTrue

        """
        if not self.save_file.exists() or not self.checksum_file.exists():
            return True  # ファイルが存在しない場合は検証をスキップ

        try:
            # 保存されたチェックサムを読み込み
            with open(self.checksum_file) as f:
                stored_checksum = f.read().strip()

            # 現在のファイルのチェックサムを計算
            current_checksum = self._calculate_checksum(self.save_file)

            # チェックサムを比較
            is_valid = stored_checksum == current_checksum
            if not is_valid:
                game_logger.warning(f"Checksum mismatch: stored={stored_checksum}, current={current_checksum}")

            return is_valid

        except Exception as e:
            game_logger.error(f"Failed to verify checksum: {e}")
            return False
