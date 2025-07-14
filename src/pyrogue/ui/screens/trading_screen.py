"""
TradingScreen モジュール。

このモジュールは、NPCとの取引を表示するスクリーンを実装します。
取引可能なアイテムの表示、売買の実行、価格の表示などを行います。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod

from pyrogue.core.managers.trading_manager import TradeItem, TradingManager
from pyrogue.ui.screens.screen import Screen

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine


class TradingScreen(Screen):
    """
    取引画面を管理するクラス。

    NPCとの取引を表示し、プレイヤーの売買を処理します。
    TradingManagerと連携して取引の実行を管理します。

    Attributes
    ----------
        trading_manager: 取引管理システム
        npc_id: 取引中のNPC ID
        view_mode: 表示モード（"buy" or "sell"）
        selected_item: 現在選択中のアイテムインデックス
        current_items: 現在表示中のアイテムリスト

    """

    def __init__(self, engine: Engine, trading_manager: TradingManager, npc_id: str) -> None:
        """
        TradingScreenの初期化。

        Args:
        ----
            engine: ゲームエンジン
            trading_manager: 取引管理システム
            npc_id: 取引中のNPC ID

        """
        super().__init__(engine)
        self.trading_manager = trading_manager
        self.npc_id = npc_id
        self.view_mode = "buy"  # デフォルトは購入モード
        self.selected_item = 0
        self.current_items: list[TradeItem] = []

        # 取引開始
        if not self.trading_manager.start_trading(npc_id, self):
            # 取引開始に失敗した場合は前の画面に戻る
            pass  # 実際にはGameScreenに戻る必要がある

        # 初期アイテムリストを更新
        self._update_item_list()

    def get_player(self):
        """プレイヤーオブジェクトを取得。"""
        return self.engine.player

    def get_npc(self, npc_id: str):
        """指定されたNPCオブジェクトを取得。"""
        # 実際の実装では、エンジンからNPCを取得する
        # 現在は簡単な実装として None を返す
        return

    def show_message(self, message: str) -> None:
        """メッセージを表示。"""
        self.engine.message_log.add_message(message)

    def update_display(self) -> None:
        """表示を更新。"""
        self._update_item_list()

    def _update_item_list(self) -> None:
        """現在のモードに応じてアイテムリストを更新。"""
        if self.view_mode == "buy":
            self.current_items = self.trading_manager.get_buy_items()
        else:
            self.current_items = self.trading_manager.get_sell_items()

        # 選択インデックスを調整
        if self.selected_item >= len(self.current_items):
            self.selected_item = max(0, len(self.current_items) - 1)

    def handle_key(self, key: tcod.event.KeyDown) -> Screen | None:
        """
        キーダウンイベントを処理する。

        Args:
        ----
            key: キーダウンイベント

        Returns:
        -------
            次の画面（Noneの場合は現在の画面を維持）

        """
        key_sym = key.sym

        if key_sym == tcod.event.K_ESCAPE:
            # ESCキーで取引を終了
            self.trading_manager.end_trading()
            from pyrogue.ui.screens.game_screen import GameScreen

            return GameScreen(self.engine)

        if not self.current_items:
            return None

        # 上下キーでアイテム選択
        if key_sym == tcod.event.K_UP:
            self.selected_item = max(0, self.selected_item - 1)
        elif key_sym == tcod.event.K_DOWN:
            self.selected_item = min(len(self.current_items) - 1, self.selected_item + 1)

        # 左右キーで表示モード切り替え
        elif key_sym == tcod.event.K_LEFT:
            if self.view_mode == "sell":
                self.view_mode = "buy"
                self._update_item_list()
        elif key_sym == tcod.event.K_RIGHT:
            if self.view_mode == "buy":
                self.view_mode = "sell"
                self._update_item_list()

        # Tabキーで表示モード切り替え
        elif key_sym == tcod.event.K_TAB:
            self.view_mode = "sell" if self.view_mode == "buy" else "buy"
            self._update_item_list()

        # Enterキーで取引実行
        elif key_sym == tcod.event.K_RETURN:
            if self.current_items:
                selected_trade_item = self.current_items[self.selected_item]
                success = self.trading_manager.execute_trade(selected_trade_item)

                if success:
                    # 取引成功時はアイテムリストを更新
                    self._update_item_list()

                    # 取引成功メッセージは TradingManager から送信される
                else:
                    # 取引失敗時のメッセージも TradingManager から送信される
                    pass

        # 数字キーで直接選択
        elif tcod.event.K_1 <= key_sym <= tcod.event.K_9:
            item_index = key_sym - tcod.event.K_1
            if item_index < len(self.current_items):
                selected_trade_item = self.current_items[item_index]
                success = self.trading_manager.execute_trade(selected_trade_item)

                if success:
                    self._update_item_list()

        return None  # 現在の画面を維持

    def render(self, console: tcod.Console) -> None:
        """
        画面を描画する。

        Args:
        ----
            console: 描画対象のコンソール

        """
        # 画面をクリア
        console.clear()

        # NPCの情報を取得
        npc = self.trading_manager.get_current_npc()
        if not npc:
            console.print(
                console.width // 2,
                console.height // 2,
                "No merchant available.",
                alignment=tcod.CENTER,
            )
            return

        # タイトルを表示
        title = f"Trading with {npc.name}"
        console.print(console.width // 2, 2, title, fg=tcod.white, alignment=tcod.CENTER)

        # プレイヤーの金貨を表示
        player = self.engine.player
        console.print(
            console.width // 2,
            4,
            f"Your Gold: {player.gold}",
            fg=tcod.yellow,
            alignment=tcod.CENTER,
        )

        # モード表示
        self._render_mode_tabs(console)

        # アイテムリストを表示
        self._render_item_list(console)

        # 操作方法を表示
        self._render_help(console)

    def _render_mode_tabs(self, console: tcod.Console) -> None:
        """
        モードタブを描画する。

        Args:
        ----
            console: 描画対象のコンソール

        """
        y = 6
        center_x = console.width // 2

        # タブの描画
        buy_text = "[ BUY ]"
        sell_text = "[ SELL ]"

        # 購入タブ
        buy_color = tcod.yellow if self.view_mode == "buy" else tcod.gray
        console.print(center_x - 8, y, buy_text, fg=buy_color, alignment=tcod.CENTER)

        # 売却タブ
        sell_color = tcod.yellow if self.view_mode == "sell" else tcod.gray
        console.print(center_x + 8, y, sell_text, fg=sell_color, alignment=tcod.CENTER)

        # 現在のモードを明示
        mode_text = f"Mode: {self.view_mode.upper()}"
        console.print(center_x, y + 1, mode_text, fg=tcod.white, alignment=tcod.CENTER)

    def _render_item_list(self, console: tcod.Console) -> None:
        """
        アイテムリストを描画する。

        Args:
        ----
            console: 描画対象のコンソール

        """
        start_y = 10

        if not self.current_items:
            console.print(
                console.width // 2,
                start_y + 2,
                "No items available.",
                fg=tcod.gray,
                alignment=tcod.CENTER,
            )
            return

        # ヘッダー
        header_text = f"Available Items ({len(self.current_items)} items):"
        console.print(
            console.width // 2,
            start_y,
            header_text,
            fg=tcod.white,
            alignment=tcod.CENTER,
        )

        # アイテムリスト
        for i, trade_item in enumerate(self.current_items):
            y = start_y + 2 + i

            # 選択中のアイテムをハイライト
            if i == self.selected_item:
                fg_color = tcod.yellow
                prefix = "> "
            else:
                fg_color = tcod.light_gray
                prefix = "  "

            # アイテム情報を構築
            item_name = trade_item.item.name
            price = trade_item.price
            quantity = trade_item.quantity

            if quantity > 1:
                item_text = f"{prefix}{i + 1}. {item_name} x{quantity} - {price}g"
            else:
                item_text = f"{prefix}{i + 1}. {item_name} - {price}g"

            # アイテムを描画
            console.print(console.width // 2, y, item_text, fg=fg_color, alignment=tcod.CENTER)

            # 画面に収まる範囲でのみ表示
            if y > console.height - 8:
                break

    def _render_help(self, console: tcod.Console) -> None:
        """
        操作方法を描画する。

        Args:
        ----
            console: 描画対象のコンソール

        """
        help_y = console.height - 6

        help_lines = [
            "Controls:",
            "↑/↓: Navigate items  ←/→: Switch modes  Tab: Switch modes",
            "Enter: Execute trade  1-9: Quick trade",
            "Esc: Exit trading",
        ]

        for i, line in enumerate(help_lines):
            console.print(
                console.width // 2,
                help_y + i,
                line,
                fg=tcod.dark_gray,
                alignment=tcod.CENTER,
            )

    def _get_color_for_item(self, item) -> tuple[int, int, int]:
        """
        アイテムの種類に応じた色を取得する。

        Args:
        ----
            item: アイテム

        Returns:
        -------
            RGB色のタプル

        """
        # アイテムの色を取得（既に item.color が設定されている場合）
        if hasattr(item, "color"):
            return item.color

        # アイテムタイプに応じたデフォルト色
        class_name = item.__class__.__name__.lower()

        if "weapon" in class_name:
            return (192, 192, 192)  # 銀色
        if "armor" in class_name:
            return (139, 69, 19)  # 茶色
        if "potion" in class_name:
            return (255, 0, 255)  # マゼンタ
        if "scroll" in class_name:
            return (255, 255, 0)  # 黄色
        if "food" in class_name:
            return (165, 42, 42)  # 茶色
        if "ring" in class_name:
            return (255, 215, 0)  # 金色
        return (128, 128, 128)  # グレー
