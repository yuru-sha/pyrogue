"""
ゲームコンテキストクラス。

このモジュールは、各マネージャーが必要とする共有データへの
アクセスを提供するコンテキストクラスを定義します。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyrogue.entities.actors.inventory import Inventory
    from pyrogue.entities.actors.player import Player
    from pyrogue.map.dungeon_manager import DungeonManager


class GameContext:
    """
    ゲーム状態の共有コンテキストクラス。

    各マネージャーが必要とする共有データへのアクセスを提供し、
    依存関係を明確にします。

    Attributes
    ----------
        player: プレイヤーオブジェクト
        inventory: インベントリオブジェクト
        dungeon_manager: ダンジョン管理オブジェクト
        message_log: メッセージログリスト
        engine: ゲームエンジン（CLIモードではNone）
        game_screen: ゲームスクリーン（UIコンテキスト用）

    """

    def __init__(
        self,
        player: Player,
        inventory: Inventory,
        dungeon_manager: DungeonManager,
        message_log: list[str],
        engine: Any = None,
        game_screen: Any = None,
    ) -> None:
        """
        ゲームコンテキストを初期化。

        Args:
        ----
            player: プレイヤーオブジェクト
            inventory: インベントリオブジェクト
            dungeon_manager: ダンジョン管理オブジェクト
            message_log: メッセージログリスト
            engine: ゲームエンジン（オプション）
            game_screen: ゲームスクリーン（オプション）

        """
        self.player = player
        self.inventory = inventory
        self.dungeon_manager = dungeon_manager
        self.message_log = message_log
        self.engine = engine
        self.game_screen = game_screen

        # マネージャーへの参照（他のマネージャーから設定される）
        self.monster_ai_manager: Any = None
        self.game_logic: Any = None
        self.combat_manager: Any = None
        self.turn_manager: Any = None
        self.movement_manager: Any = None
        self.item_manager: Any = None
        self.floor_manager: Any = None

    def add_message(self, message: str) -> None:
        """
        メッセージログにメッセージを追加。

        Args:
        ----
            message: 追加するメッセージ

        """
        try:
            # 安全な文字列変換
            safe_message = str(message)[:200]  # 過度に長いメッセージを切り詰め
            self.message_log.append(safe_message)

            # 原子的なサイズ制限処理（インプレース更新）
            if len(self.message_log) > 200:
                # 200件を超えた場合、150件まで削減（段階的な削減）
                self.message_log[:] = self.message_log[-150:]
        except Exception as e:
            # メッセージ追加エラーを記録（重要：無限ループを避けるためprintを使用）
            print(f"Warning: Failed to add message '{message}': {e}")

    def get_current_floor_data(self):
        """現在のフロアデータを取得。"""
        return self.dungeon_manager.get_current_floor_data(self.player)

    def get_current_floor_number(self) -> int:
        """現在のフロア番号を取得。"""
        return self.dungeon_manager.current_floor

    def update_console(self) -> None:
        """コンソールの更新（エンジンが存在する場合）。"""
        if self.engine and hasattr(self.engine, "update_console"):
            self.engine.update_console()

    def is_cli_mode(self) -> bool:
        """CLIモードかどうかを判定。"""
        return self.engine is None

    def has_game_screen(self) -> bool:
        """ゲームスクリーンが設定されているかを判定。"""
        return self.game_screen is not None
