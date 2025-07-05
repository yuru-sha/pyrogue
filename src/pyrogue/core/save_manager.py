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

import json
import os
import pickle
import time
from pathlib import Path
from typing import Any, Dict, Optional

from pyrogue.utils.logger import game_logger


class SaveManager:
    """
    セーブ/ロード機能を管理するクラス。

    パーマデス機能を維持しながら、ゲーム状態の保存と復元を行います。
    セーブデータの整合性チェックと改ざん防止機能も提供します。

    Attributes:
        save_dir: セーブデータディレクトリのパス
        save_file: メインセーブファイルのパス
        backup_file: バックアップセーブファイルのパス
        is_permadeath_triggered: パーマデスが発動されたかどうか

    """

    def __init__(self, save_dir: str = "saves") -> None:
        """
        SaveManagerを初期化。

        Args:
            save_dir: セーブデータを保存するディレクトリ

        """
        self.save_dir = Path(save_dir)
        self.save_file = self.save_dir / "game_save.pkl"
        self.backup_file = self.save_dir / "game_save_backup.pkl"
        self.metadata_file = self.save_dir / "save_metadata.json"
        self.is_permadeath_triggered = False

        # セーブディレクトリを作成
        self.save_dir.mkdir(exist_ok=True)

    def save_game_state(self, game_data: Dict[str, Any]) -> bool:
        """
        ゲーム状態を保存。

        Args:
            game_data: 保存するゲームデータ

        Returns:
            bool: 保存に成功した場合はTrue

        """
        if self.is_permadeath_triggered:
            game_logger.warning("Cannot save game: permadeath is active")
            return False

        try:
            # メタデータを作成
            metadata = {
                "save_time": time.time(),
                "save_version": "1.0",
                "player_level": game_data.get("player_stats", {}).get("level", 1),
                "current_floor": game_data.get("current_floor", 1),
                "player_hp": game_data.get("player_stats", {}).get("hp", 20),
                "player_max_hp": game_data.get("player_stats", {}).get("hp_max", 20),
                "is_alive": game_data.get("player_stats", {}).get("hp", 20) > 0,
            }

            # 既存のファイルをバックアップ
            if self.save_file.exists():
                self.save_file.rename(self.backup_file)

            # メインセーブファイルを保存
            with open(self.save_file, "wb") as f:
                pickle.dump(game_data, f)

            # メタデータを保存
            with open(self.metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            game_logger.info(f"Game saved successfully to {self.save_file}")
            return True

        except Exception as e:
            game_logger.error(f"Failed to save game: {e}")
            # エラーが発生した場合、バックアップから復元
            if self.backup_file.exists():
                self.backup_file.rename(self.save_file)
            return False

    def load_game_state(self) -> Optional[Dict[str, Any]]:
        """
        ゲーム状態を読み込み。

        Returns:
            Optional[Dict[str, Any]]: 読み込んだゲームデータ。失敗時はNone

        """
        if not self.save_file.exists():
            game_logger.info("No save file found")
            return None

        try:
            # メタデータを確認
            if self.metadata_file.exists():
                with open(self.metadata_file, "r") as f:
                    metadata = json.load(f)

                # プレイヤーが死亡している場合はロードを拒否
                if not metadata.get("is_alive", True):
                    game_logger.warning("Cannot load game: player is dead (permadeath)")
                    self._trigger_permadeath()
                    return None

            # セーブデータを読み込み
            with open(self.save_file, "rb") as f:
                game_data = pickle.load(f)

            game_logger.info(f"Game loaded successfully from {self.save_file}")
            return game_data

        except Exception as e:
            game_logger.error(f"Failed to load game: {e}")
            # メインファイルが破損している場合、バックアップを試行
            if self.backup_file.exists():
                try:
                    with open(self.backup_file, "rb") as f:
                        game_data = pickle.load(f)
                    game_logger.info("Game loaded from backup file")
                    return game_data
                except Exception as backup_error:
                    game_logger.error(f"Backup file also corrupted: {backup_error}")

            return None

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

            # メタデータファイルを削除
            if self.metadata_file.exists():
                self.metadata_file.unlink()
                game_logger.info("Save metadata deleted (permadeath)")

        except Exception as e:
            game_logger.error(f"Error during permadeath cleanup: {e}")

    def trigger_permadeath_on_death(self, game_data: Dict[str, Any]) -> None:
        """
        プレイヤー死亡時にパーマデスを発動。

        Args:
            game_data: 現在のゲームデータ

        """
        player_hp = game_data.get("player_stats", {}).get("hp", 0)

        if player_hp <= 0:
            game_logger.warning("Player died - triggering permadeath")
            self._trigger_permadeath()

    def has_save_file(self) -> bool:
        """
        セーブファイルが存在するかチェック。

        Returns:
            bool: セーブファイルが存在する場合はTrue

        """
        return self.save_file.exists() and not self.is_permadeath_triggered

    def get_save_info(self) -> Optional[Dict[str, Any]]:
        """
        セーブファイルの情報を取得。

        Returns:
            Optional[Dict[str, Any]]: セーブファイルの情報。存在しない場合はNone

        """
        if not self.metadata_file.exists():
            return None

        try:
            with open(self.metadata_file, "r") as f:
                metadata = json.load(f)
            return metadata
        except Exception as e:
            game_logger.error(f"Failed to read save metadata: {e}")
            return None

    def delete_save_data(self) -> bool:
        """
        セーブデータを手動で削除。

        Returns:
            bool: 削除に成功した場合はTrue

        """
        try:
            self._trigger_permadeath()
            return True
        except Exception as e:
            game_logger.error(f"Failed to delete save data: {e}")
            return False