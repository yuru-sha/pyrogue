"""
ゲームエンジンモジュール。

このモジュールは、コアゲームエンジンを実装し、メインゲームループ、
状態管理、イベント処理を担当します。

主要機能:
    - ゲームの主要ループ制御
    - 画面状態（メニュー、ゲーム、ゲームオーバー）の管理
    - ユーザー入力の処理とルーティング
    - ウィンドウリサイズの対応
    - TCODライブラリとの統合

Example:
-------
    >>> engine = Engine()
    >>> engine.initialize()
    >>> engine.run()

"""

from __future__ import annotations

import tcod
import tcod.console
import tcod.event
import tcod.tileset

from pyrogue.config import CONFIG
from pyrogue.core.game_states import GameStates
from pyrogue.core.input_handlers import StateManager
from pyrogue.core.save_manager import SaveManager
from pyrogue.ui.screens.game_over_screen import GameOverScreen
from pyrogue.ui.screens.game_screen import GameScreen
from pyrogue.ui.screens.help_menu_screen import HelpMenuScreen
from pyrogue.ui.screens.inventory_screen import InventoryScreen
from pyrogue.ui.screens.menu_screen import MenuScreen
from pyrogue.ui.screens.quick_guide_screen import QuickGuideScreen
from pyrogue.ui.screens.symbol_explanation_screen import SymbolExplanationScreen
from pyrogue.ui.screens.victory_screen import VictoryScreen
from pyrogue.utils import game_logger


class Engine:
    """
    メインゲームエンジンクラス。

    ゲーム全体のライフサイクルを管理し、各画面間の状態遷移、
    ユーザー入力の処理、レンダリングを統合的に制御します。

    特徴:
        - 状態ベースの画面管理
        - リサイズ可能なウィンドウサポート
        - イベント駆動型アーキテクチャ
        - 統合されたログ機能
        - エラー処理とリソース管理

    Attributes
    ----------
        screen_width: スクリーンの幅（文字数）
        screen_height: スクリーンの高さ（文字数）
        console: TCODコンソールオブジェクト
        state: 現在のゲーム状態
        running: ゲームループ実行フラグ
        menu_screen: メニュー画面インスタンス
        game_screen: ゲーム画面インスタンス
        game_over_screen: ゲームオーバー画面インスタンス

    """

    def __init__(self) -> None:
        """
        ゲームエンジンを初期化。

        画面サイズの設定、コンソールの作成、各画面インスタンスの初期化を行います。
        ゲーム状態はメニューから開始し、ログ機能を有効化します。
        """
        self.screen_width = CONFIG.display.SCREEN_WIDTH
        self.screen_height = CONFIG.display.SCREEN_HEIGHT
        self.map_width = CONFIG.display.MAP_WIDTH
        self.map_height = CONFIG.display.MAP_HEIGHT
        self.title = "PyRogue"
        self.console = tcod.console.Console(self.screen_width, self.screen_height)
        self.state = GameStates.MENU
        self.running = False
        self.message_log: list[str] = []  # メッセージログを追加
        self.state_manager = StateManager()

        # セーブマネージャーを初期化
        self.save_manager = SaveManager()

        # 各画面インスタンスの初期化
        self.menu_screen = MenuScreen(self.console, self)
        self.help_menu_screen = HelpMenuScreen(self.console, self)
        self.symbol_explanation_screen = SymbolExplanationScreen(self.console, self)
        self.quick_guide_screen = QuickGuideScreen(self.console, self)
        self.game_screen = GameScreen(self)
        self.inventory_screen = InventoryScreen(self.game_screen)
        self.game_over_screen = GameOverScreen(self.console, self)
        self.victory_screen = VictoryScreen(self.console, self)

        # 前の状態を記録する変数
        self.previous_state = None

        game_logger.debug(
            "Initializing game engine",
            extra={
                "screen_width": self.screen_width,
                "screen_height": self.screen_height,
                "title": self.title,
            },
        )

    def initialize(self) -> None:
        """
        ゲームエンジンとTCODコンソールを初期化。

        フォントの読み込み、ウィンドウコンテキストの作成、
        リサイズ可能なウィンドウの設定を行います。
        """
        # デフォルトフォントファイルの読み込みと設定
        tileset = tcod.tileset.load_tilesheet(
            "assets/fonts/dejavu10x10_gs_tc.png",  # デフォルトフォント
            32,
            8,  # 列数と行数
            tcod.tileset.CHARMAP_TCOD,  # 文字マップ
        )

        # フォントサイズをピクセル単位で設定
        self.font_width = CONFIG.display.FONT_WIDTH
        self.font_height = CONFIG.display.FONT_HEIGHT

        # リサイズ可能なウィンドウでコンテキストを作成
        self.context = tcod.context.new(
            columns=self.screen_width,
            rows=self.screen_height,
            tileset=tileset,
            title=self.title,
            vsync=True,
            sdl_window_flags=tcod.context.SDL_WINDOW_RESIZABLE,
        )
        game_logger.debug("Game engine initialized")

    def handle_resize(self, event: tcod.event.WindowEvent) -> None:
        """
        ウィンドウリサイズ時の処理。

        新しいウィンドウサイズに基づいて画面サイズを再計算し、
        コンソールと各画面を更新します。最小サイズ制限も適用します。

        Args:
        ----
            event: ウィンドウリサイズイベント

        """
        # ピクセル単位での新しいウィンドウサイズを取得
        pixel_width = getattr(event, "width", 800)
        pixel_height = getattr(event, "height", 600)

        # ピクセルサイズをフォントサイズで割って文字数を計算
        self.screen_width = max(CONFIG.display.MIN_SCREEN_WIDTH, pixel_width // self.font_width)  # 最小幅を保証
        self.screen_height = max(CONFIG.display.MIN_SCREEN_HEIGHT, pixel_height // self.font_height)  # 最小高さを保証

        # 新しいサイズでコンソールを再作成
        self.console = tcod.console.Console(self.screen_width, self.screen_height)

        # 各画面インスタンスのコンソール参照を更新
        self.menu_screen.update_console(self.console)
        self.help_menu_screen.update_console(self.console)
        self.symbol_explanation_screen.update_console(self.console)
        self.quick_guide_screen.update_console(self.console)
        self.game_screen.update_console(self.console)
        self.game_over_screen.update_console(self.console)
        self.victory_screen.update_console(self.console)

        game_logger.debug(
            "Window resized",
            extra={
                "new_width": self.screen_width,
                "new_height": self.screen_height,
            },
        )

    def run(self) -> None:
        """
        メインゲームループを実行。

        ゲームが終了するまでレンダリング、イベント処理、
        状態更新のサイクルを継続します。例外処理とリソース
        クリーンアップも含まれます。
        """
        self.running = True
        game_logger.debug("Starting game loop")

        try:
            while self.running:
                self.console.clear()

                # 現在のゲーム状態に応じた画面を描画
                if self.state == GameStates.MENU:
                    self.menu_screen.render()
                elif self.state == GameStates.HELP_MENU:
                    self.help_menu_screen.render()
                elif self.state == GameStates.SYMBOL_EXPLANATION:
                    self.symbol_explanation_screen.render()
                elif self.state == GameStates.QUICK_GUIDE:
                    self.quick_guide_screen.render()
                elif self.state == GameStates.PLAYERS_TURN:
                    self.game_screen.render(self.console)
                elif self.state == GameStates.SHOW_INVENTORY:
                    self.inventory_screen.render(self.console)
                elif self.state == GameStates.TARGETING:
                    self.game_screen.render(self.console)
                elif self.state == GameStates.GAME_OVER:
                    self.game_over_screen.render()
                elif self.state == GameStates.VICTORY:
                    self.victory_screen.render()

                self.context.present(self.console)

                for event in tcod.event.wait():
                    if event.type == "QUIT":
                        game_logger.debug("Quit event received")
                        self.running = False
                        break
                    if event.type == "WINDOWRESIZED":
                        self.handle_resize(event)
                    elif event.type == "KEYDOWN":
                        continue_game, new_state = self._handle_input(event)
                        if not continue_game:
                            self.running = False
                            break
                        if new_state:
                            # 状態遷移時に前の状態を記録
                            self.previous_state = self.state
                            self.state = new_state

        except Exception as e:
            game_logger.error(
                "Fatal error in game loop",
                extra={"error": str(e)},
            )
            raise
        finally:
            self.cleanup()

    def _handle_input(self, event: tcod.event.KeyDown) -> tuple[bool, GameStates | None]:
        """
        キー入力イベントを処理。

        StateManagerを使用してクリーンな状態管理を行います。

        Args:
        ----
            event: キーボード入力イベント

        Returns:
        -------
            Tuple of (continue_game, new_state)

        """
        # Get appropriate screen context for current state
        context = self._get_current_screen()

        # コンテキストがNoneの場合の安全な処理
        if context is None:
            # デフォルトの処理（通常は発生しないが安全のため）
            return True, None

        try:
            return self.state_manager.handle_input(event, self.state, context)
        except Exception as e:
            # 入力処理エラーを記録してゲームを継続
            print(f"Warning: Input handling error: {e}")
            return True, None

    def _get_current_screen(self):
        """Get the current screen instance based on state."""
        if self.state == GameStates.MENU:
            return self.menu_screen
        if self.state == GameStates.HELP_MENU:
            return self.help_menu_screen
        if self.state == GameStates.SYMBOL_EXPLANATION:
            return self.symbol_explanation_screen
        if self.state == GameStates.QUICK_GUIDE:
            return self.quick_guide_screen
        if self.state == GameStates.PLAYERS_TURN:
            return self.game_screen
        if self.state == GameStates.SHOW_INVENTORY:
            return self.inventory_screen
        if self.state == GameStates.SHOW_WAND_SELECTION:
            return getattr(self, "wand_selection_screen", None)
        if self.state == GameStates.TARGETING:
            return self.game_screen
        if self.state == GameStates.GAME_OVER:
            return self.game_over_screen
        if self.state == GameStates.VICTORY:
            return self.victory_screen
        return None

    def cleanup(self) -> None:
        """
        終了前のリソースクリーンアップ。

        ゲーム終了時に必要なリソースの解放処理を行います。
        """
        game_logger.debug("Cleaning up resources")

    def new_game(self) -> None:
        """
        新しいゲームを開始。

        ゲーム画面を初期化し、クイックガイドを表示してからプレイヤーターン状態に遷移します。
        """
        self.game_screen.setup_new_game()
        self.state = GameStates.QUICK_GUIDE

    def game_over(self, player_stats: dict, final_floor: int, cause_of_death: str = "Unknown") -> None:
        """
        ゲームオーバー処理。

        プレイヤーの最終ステータスと死因を記録し、
        ゲームオーバー画面に遷移します。
        Permadeath機能により、セーブデータを自動削除します。

        Args:
        ----
            player_stats: プレイヤーの最終ステータス
            final_floor: 到達した最終階層
            cause_of_death: 死因の説明文

        """
        # Permadeath機能：セーブデータを自動削除
        game_data = {
            "player_stats": player_stats,
            "current_floor": final_floor,
        }
        self.save_manager.trigger_permadeath_on_death(game_data)

        self.game_over_screen.set_game_over_data(player_stats, final_floor, cause_of_death)
        self.state = GameStates.GAME_OVER

    def victory(self, player_stats: dict, final_floor: int) -> None:
        """
        ゲーム勝利処理。

        プレイヤーの最終ステータスを記録し、
        勝利画面に遷移します。

        Args:
        ----
            player_stats: プレイヤーの最終ステータス
            final_floor: 到達した最終階層

        """
        final_score = self.calculate_final_score(player_stats, final_floor)
        self.victory_screen.set_victory_data(player_stats, final_floor, final_score)
        self.state = GameStates.VICTORY

    def calculate_final_score(self, player_stats: dict, final_floor: int) -> int:
        """
        最終スコアを計算。

        Args:
        ----
            player_stats: プレイヤーの最終ステータス
            final_floor: 到達した最終階層

        Returns:
        -------
            計算された最終スコア

        """
        level_bonus = player_stats.get("level", 1) * 100
        gold_bonus = player_stats.get("gold", 0) * 2
        floor_bonus = final_floor * 50
        hp_bonus = player_stats.get("hp", 0) * 10

        return level_bonus + gold_bonus + floor_bonus + hp_bonus
