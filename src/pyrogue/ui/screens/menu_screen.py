"""
メニュースクリーンモジュール。

このモジュールはメインメニューの表示とユーザー入力を管理します。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
import tcod.console
import tcod.event

from pyrogue.core.game_states import GameStates
from pyrogue.core.save_manager import SaveManager

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine


class MenuScreen:
    """
    メインメニュースクリーンクラス。

    ゲームのメインメニューを表示し、ユーザーの入力を処理します。
    アスキーアートタイトルやメニューオプションの表示、
    ナビゲーション機能を提供します。
    """

    def __init__(self, console: tcod.console.Console, engine: Engine) -> None:
        """
        メニュースクリーンを初期化。

        Args:
        ----
            console: TCODコンソールオブジェクト
            engine: メインゲームエンジンのインスタンス

        """
        self.console = console
        self.engine = engine
        self.menu_selection = 0
        self.save_manager = SaveManager()
        self.menu_options = self._get_menu_options()

    def update_console(self, console: tcod.console.Console) -> None:
        """
        コンソールの更新。

        ウィンドウサイズ変更時にコンソール参照を更新します。

        Args:
        ----
            console: 新しいTCODコンソールオブジェクト

        """
        self.console = console
        # コンソール更新時にメニューオプションも更新
        self.menu_options = self._get_menu_options()

    def render(self) -> None:
        """
        メニュースクリーンを描画。

        アスキーアートタイトル、メニューオプション、
        操作説明を表示します。
        """
        self.console.clear()

        # メニューオプションを更新（セーブデータの状態が変わった場合を考慮）
        self.menu_options = self._get_menu_options()

        # 選択インデックスが範囲外の場合は調整
        if self.menu_selection >= len(self.menu_options):
            self.menu_selection = 0

        # ASCIIアートタイトルの表示
        title_art = [
            "██████╗ ██╗   ██╗██████╗  ██████╗  ██████╗ ██╗   ██╗███████╗",
            "██╔══██╗╚██╗ ██╔╝██╔══██╗██╔═══██╗██╔════╝ ██║   ██║██╔════╝",
            "██████╔╝ ╚████╔╝ ██████╔╝██║   ██║██║  ███╗██║   ██║█████╗  ",
            "██╔═══╝   ╚██╔╝  ██╔══██╗██║   ██║██║   ██║██║   ██║██╔══╝  ",
            "██║        ██║   ██║  ██║╚██████╔╝╚██████╔╝╚██████╔╝███████╗",
            "╚═╝        ╚═╝   ╚═╝  ╚═╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝",
        ]

        # タイトルアートが画面に収まるかチェック
        if self.console.width >= 60 and self.console.height >= 20:
            # 大きなタイトルを表示
            title_y = self.console.height // 6
            for i, line in enumerate(title_art):
                self.console.print(
                    (self.console.width - len(line)) // 2,
                    title_y + i,
                    line,
                    fg=(255, 215, 0),  # 金色
                )
        else:
            # 小さなタイトルを表示
            title = "PyRogue"
            title_y = self.console.height // 4
            self.console.print(
                (self.console.width - len(title)) // 2,
                title_y,
                title,
                fg=(255, 215, 0),  # 金色
            )

        # サブタイトルの表示
        subtitle = "A Python Roguelike Adventure"
        subtitle_y = title_y + (len(title_art) if self.console.width >= 60 else 2)
        self.console.print(
            (self.console.width - len(subtitle)) // 2,
            subtitle_y,
            subtitle,
            fg=(150, 150, 150),
        )

        # セーブデータの情報を表示（セーブデータが存在する場合）
        if self.save_manager.has_save_file():
            save_info = self.save_manager.get_save_info()
            if save_info and "timestamp" in save_info:
                import datetime

                timestamp = datetime.datetime.fromtimestamp(save_info["timestamp"])
                save_text = f"Save: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                self.console.print(
                    (self.console.width - len(save_text)) // 2,
                    subtitle_y + 2,
                    save_text,
                    fg=(100, 100, 100),
                )

        # メニューオプションの表示
        menu_start_y = subtitle_y + (5 if self.save_manager.has_save_file() else 3)
        for i, option in enumerate(self.menu_options):
            text = f"> {option}" if i == self.menu_selection else f"  {option}"
            color = (255, 255, 255) if i == self.menu_selection else (150, 150, 150)
            self.console.print(
                (self.console.width - len(text)) // 2,
                menu_start_y + i * 2,
                text,
                fg=color,
            )

        # 操作説明の表示
        help_text = "Use UP/DOWN arrows to navigate, ENTER to select, ESC to quit"
        self.console.print(
            (self.console.width - len(help_text)) // 2,
            self.console.height - 3,
            help_text,
            fg=(100, 100, 100),
        )

    def handle_input(self, key: tcod.event.KeyDown) -> GameStates | None:
        """
        ユーザー入力の処理。

        メニューナビゲーションとオプション選択を処理します。

        Args:
        ----
            key: キーボード入力イベント

        Returns:
        -------
            選択されたゲーム状態、またはNone

        """
        # 上矢印キーで上のオプションへ移動
        if key.sym == tcod.event.KeySym.UP:
            self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
        # 下矢印キーで下のオプションへ移動
        elif key.sym == tcod.event.KeySym.DOWN:
            self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
        # Enterキーで選択されたオプションを実行
        elif key.sym == tcod.event.KeySym.RETURN:
            # 新しいゲームを開始
            if self.menu_options[self.menu_selection] == "New Game":
                self.engine.new_game()
                return GameStates.PLAYERS_TURN
            # ゲームを継続（セーブデータをロード）
            if self.menu_options[self.menu_selection] == "Load Game":
                return self._load_game()
            # ゲームを終了
            if self.menu_options[self.menu_selection] == "Quit":
                return GameStates.EXIT

        return None

    def _get_menu_options(self) -> list[str]:
        """
        セーブデータの存在に応じてメニューオプションを生成。

        Returns
        -------
            list[str]: メニューオプションのリスト

        """
        options = ["New Game"]

        # セーブデータが存在する場合は「Load Game」を2番目に表示
        if self.save_manager.has_save_file():
            options.append("Load Game")

        options.append("Quit")

        return options

    def _load_game(self) -> GameStates:
        """
        セーブデータをロードしてゲームを継続。

        Returns
        -------
            GameStates: ロード後のゲーム状態

        """
        try:
            # セーブデータをロード
            save_data = self.save_manager.load_game_state()

            if save_data is None:
                # セーブデータがない場合は新しいゲームを開始
                self.engine.new_game()
                return GameStates.PLAYERS_TURN

            # ゲームエンジンにセーブデータを反映
            self._restore_game_state(save_data)

            return GameStates.PLAYERS_TURN

        except Exception as e:
            # ロードに失敗した場合は新しいゲームを開始
            print(f"Failed to load save data: {e}")
            self.engine.new_game()
            return GameStates.PLAYERS_TURN

    def _restore_game_state(self, save_data: dict) -> None:
        """
        セーブデータからゲーム状態を復元。

        Args:
        ----
            save_data: セーブデータ辞書

        """
        # ゲームエンジンのゲームスクリーンを初期化
        self.engine.new_game()

        # ゲームスクリーンが存在する場合はセーブデータを復元
        if hasattr(self.engine, "game_screen") and self.engine.game_screen:
            # 既存のload_gameメソッドを使用してセーブデータを復元
            self.engine.game_screen.load_game()
