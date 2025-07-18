"""
リファクタリングされたゲームスクリーンモジュール。

このモジュールは、元のGameScreenから責務を分離し、
各コンポーネントに処理を委譲する構造になっています。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod

from pyrogue.core.game_logic import GameLogic
from pyrogue.core.game_states import GameStates
from pyrogue.ui.components.fov_manager import FOVManager
from pyrogue.ui.components.game_renderer import GameRenderer
from pyrogue.ui.components.input_handler import InputHandler

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine
    from pyrogue.entities.actors.player import Player


class GameScreen:
    """
    リファクタリングされたメインゲームスクリーン。

    各責務を専用のコンポーネントに委譲し、
    自身はコンポーネント間の調整役に徹します。

    Attributes
    ----------
        engine: ゲームエンジンインスタンス
        game_logic: ゲームロジック管理インスタンス
        renderer: 描画処理コンポーネント
        input_handler: 入力処理コンポーネント
        fov_manager: FOV管理コンポーネント
        dungeon_width: ダンジョンの幅
        dungeon_height: ダンジョンの高さ

    """

    def __init__(self, engine: Engine | None) -> None:
        """
        ゲームスクリーンを初期化。

        Args:
        ----
            engine: メインゲームエンジンのインスタンス（CLIモードの場合はNone）

        """
        self.engine = engine

        # ダンジョンサイズの設定
        if engine:
            self.dungeon_width = getattr(engine, "map_width", 80)
            self.dungeon_height = getattr(engine, "map_height", 45)
        else:
            # CLIモードでは固定値を使用
            self.dungeon_width = 80
            self.dungeon_height = 45

        # ゲームロジックを初期化
        self.game_logic = GameLogic(engine, self.dungeon_width, self.dungeon_height)

        # 各コンポーネントを初期化
        self.renderer = GameRenderer(self)
        self.input_handler = InputHandler(self)
        self.fov_manager = FOVManager(self)

        # ゲームロジックに自身の参照を設定
        self.game_logic.set_game_screen_reference(self)

    def setup_new_game(self) -> None:
        """
        新しいゲームをセットアップ。
        """
        self.game_logic.reset_game()
        self.game_logic.setup_new_game()
        self.fov_manager.update_fov()

    def update_console(self) -> None:
        """
        コンソールの更新（エンジンから呼ばれる）。
        """
        if self.engine:
            self.engine.update_console()

    def render(self, console: tcod.Console) -> None:
        """
        画面の描画（レンダラーに委譲）。

        Args:
        ----
            console: TCODコンソール

        """
        # FOVを更新
        self.fov_manager.update_fov()

        # 描画処理を委譲
        self.renderer.render(console)

    def handle_key(self, event: tcod.event.KeyDown) -> GameStates | None:
        """
        キー入力の処理（入力ハンドラーに委譲）。

        Args:
        ----
            event: TCODキーイベント

        Returns:
        -------
            新しいゲーム状態、またはNone

        """
        return self.input_handler.handle_key(event)

    def handle_targeting(self, event: tcod.event.KeyDown) -> None:
        """
        ターゲット選択モードのキー入力処理（入力ハンドラーに委譲）。

        Args:
        ----
            event: TCODキーイベント

        """
        self.input_handler.handle_targeting(event)

    def save_game(self) -> bool:
        """
        ゲーム状態を保存（CommonCommandHandler経由の統合処理）。

        Returns
        -------
            保存に成功した場合True

        """
        from pyrogue.core.command_handler import CommonCommandHandler, GUICommandContext

        context = GUICommandContext(self)
        command_handler = CommonCommandHandler(context)
        result = command_handler.handle_command("save")

        return result.success

    def load_game(self) -> bool:
        """
        ゲーム状態を読み込み（CommonCommandHandler経由の統合処理）。

        Returns
        -------
            読み込みに成功した場合True

        """
        from pyrogue.core.command_handler import CommonCommandHandler, GUICommandContext

        context = GUICommandContext(self)
        command_handler = CommonCommandHandler(context)
        result = command_handler.handle_command("load")

        # ロード成功時にFOVを更新
        if result.success:
            self.fov_manager.update_fov()

        return result.success

    # GameLogic連携プロパティ
    @property
    def player(self) -> Player:
        """プレイヤーオブジェクトへのアクセス。"""
        return self.game_logic.player

    @property
    def dungeon(self):
        """ダンジョンオブジェクトへのアクセス。"""
        return self._create_dungeon_object()

    @property
    def game_screen(self):
        """ゲームスクリーン自身へのアクセス。"""
        return self

    def add_message(self, message: str, color: tuple[int, int, int] = (255, 255, 255)) -> None:
        """メッセージをゲームログに追加。"""
        self.game_logic.add_message(message)

    def _create_dungeon_object(self):
        """ダンジョンオブジェクトのプロキシを作成。"""

        class DungeonProxy:
            def __init__(self, game_screen):
                self.game_screen = game_screen

            @property
            def current_floor(self):
                return self.game_screen.game_logic.dungeon_manager.current_floor

            @property
            def tiles(self):
                current_floor = self.game_screen.game_logic.get_current_floor_data()
                return current_floor.tiles

            @property
            def width(self):
                return self.game_screen.dungeon_width

            @property
            def height(self):
                return self.game_screen.dungeon_height

            @property
            def explored(self):
                current_floor = self.game_screen.game_logic.get_current_floor_data()
                return current_floor.explored

            def get_blocking_entity_at(self, x, y):
                # モンスターがその位置にいるかチェック
                current_floor = self.game_screen.game_logic.get_current_floor_data()
                return current_floor.monster_spawner.get_monster_at(x, y)

        return DungeonProxy(self)

    # 状態チェック用メソッド（GameLogicから取得）
    def check_player_death(self) -> bool:
        """プレイヤーの死亡をチェック。"""
        return self.game_logic.check_player_death()

    def check_game_over(self) -> bool:
        """ゲームオーバー状態をチェック。"""
        return self.game_logic.check_game_over()

    def check_victory(self) -> bool:
        """勝利条件をチェック。"""
        return self.game_logic.check_victory()

    # CLIモード互換メソッド
    def try_move_player(self, dx: int, dy: int) -> bool:
        """プレイヤーの移動を試行。"""
        return self.game_logic.handle_player_move(dx, dy)

    def try_attack_adjacent_enemy(self) -> bool:
        """隣接する敵を攻撃。"""
        return self.game_logic.try_attack_adjacent_enemy()

    def try_use_item(self, item) -> bool:
        """アイテムを使用。"""
        return self.game_logic.try_use_item(item)

    def get_nearby_enemies(self) -> list:
        """周囲の敵を取得。"""
        return self.game_logic.get_nearby_enemies()

    def process_enemy_turns(self) -> None:
        """敵のターンを処理。"""
        self.game_logic.process_enemy_turns()

    # ユーティリティメソッド
    def start_targeting(self, start_x: int | None = None, start_y: int | None = None) -> None:
        """ターゲット選択モードを開始。"""
        self.input_handler.start_targeting(start_x, start_y)

    def get_targeting_info(self) -> tuple[bool, int, int]:
        """ターゲット選択の情報を取得。"""
        return self.input_handler.get_targeting_info()

    def toggle_fov(self) -> str:
        """FOV表示の切り替え。"""
        return self.fov_manager.toggle_fov()

    def has_save_file(self) -> bool:
        """セーブファイルが存在するかチェック。"""
        from pyrogue.core.save_manager import SaveManager

        save_manager = SaveManager()
        return save_manager.has_save_file()

    def delete_save_file(self) -> bool:
        """セーブファイルを削除。"""
        from pyrogue.core.save_manager import SaveManager

        save_manager = SaveManager()
        return save_manager.delete_save_data()
