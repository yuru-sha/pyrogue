"""
環境変数設定モジュール。

.envファイルの読み込みと環境変数の管理を行います。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


class EnvConfig:
    """
    環境変数設定を管理するクラス。

    .envファイルから環境変数を読み込み、ゲームの設定を管理します。
    """

    def __init__(self, env_file: str | Path | None = None) -> None:
        """
        環境設定を初期化。

        Args:
        ----
            env_file: .envファイルのパス（指定されない場合はプロジェクトルートの.envを使用）
        """
        self._loaded = False
        self.load_env(env_file)

    def load_env(self, env_file: str | Path | None = None) -> None:
        """
        .envファイルを読み込み。

        Args:
        ----
            env_file: .envファイルのパス
        """
        if env_file is None:
            # プロジェクトルートの.envファイルを探す
            current_dir = Path(__file__).parent
            while current_dir.parent != current_dir:
                env_path = current_dir / ".env"
                if env_path.exists():
                    env_file = env_path
                    break
                current_dir = current_dir.parent

        if env_file and Path(env_file).exists():
            load_dotenv(env_file)
            self._loaded = True

    def get(self, key: str, default: Any = None) -> Any:
        """
        環境変数の値を取得。

        Args:
        ----
            key: 環境変数のキー
            default: デフォルト値

        Returns:
        -------
            環境変数の値またはデフォルト値
        """
        return os.getenv(key, default)

    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        環境変数をbool値として取得。

        Args:
        ----
            key: 環境変数のキー
            default: デフォルト値

        Returns:
        -------
            bool値
        """
        value = self.get(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def get_int(self, key: str, default: int = 0) -> int:
        """
        環境変数をint値として取得。

        Args:
        ----
            key: 環境変数のキー
            default: デフォルト値

        Returns:
        -------
            int値
        """
        try:
            return int(self.get(key, str(default)))
        except ValueError:
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        環境変数をfloat値として取得。

        Args:
        ----
            key: 環境変数のキー
            default: デフォルト値

        Returns:
        -------
            float値
        """
        try:
            return float(self.get(key, str(default)))
        except ValueError:
            return default

    @property
    def is_loaded(self) -> bool:
        """
        .envファイルが読み込まれたかどうか。

        Returns
        -------
            読み込まれた場合True
        """
        return self._loaded


# グローバルインスタンス
env_config = EnvConfig()


# ゲーム設定に関連する環境変数のアクセサー関数
def get_debug_mode() -> bool:
    """デバッグモードの設定を取得。"""
    return env_config.get_bool("DEBUG", False)


def get_log_level() -> str:
    """ログレベルの設定を取得。"""
    return env_config.get("LOG_LEVEL", "INFO")


def get_save_directory() -> str:
    """セーブディレクトリの設定を取得。"""
    return env_config.get("SAVE_DIRECTORY", "saves")


def get_window_width() -> int:
    """ウィンドウ幅の設定を取得。"""
    return env_config.get_int("WINDOW_WIDTH", 80)


def get_window_height() -> int:
    """ウィンドウ高さの設定を取得。"""
    return env_config.get_int("WINDOW_HEIGHT", 50)


def get_fps_limit() -> int:
    """FPS制限の設定を取得。"""
    return env_config.get_int("FPS_LIMIT", 60)


def get_auto_save_enabled() -> bool:
    """オートセーブ機能の設定を取得。"""
    return env_config.get_bool("AUTO_SAVE_ENABLED", True)


def get_sound_enabled() -> bool:
    """音声機能の設定を取得。"""
    return env_config.get_bool("SOUND_ENABLED", False)
