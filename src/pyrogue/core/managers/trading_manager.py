"""
TradingManager モジュール。

このモジュールは、NPCとの取引システムを管理します。
アイテムの売買、価格計算、取引の実行などを行います。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pyrogue.entities.actors.npc import NPC
    from pyrogue.entities.actors.player import Player
    from pyrogue.entities.items.item import Item


class TradeType(Enum):
    """取引の種類を定義する列挙型。"""

    BUY = "buy"  # プレイヤーがNPCから購入
    SELL = "sell"  # プレイヤーがNPCに売却


@dataclass
class TradeItem:
    """
    取引アイテムを表すデータクラス。

    Attributes
    ----------
        item: 取引対象のアイテム
        price: 取引価格
        quantity: 取引数量
        trade_type: 取引の種類

    """

    item: Item
    price: int
    quantity: int
    trade_type: TradeType


class TradingContext(Protocol):
    """
    取引コンテキストのプロトコル。

    TradingManagerが必要とする情報を提供するインターフェース。
    """

    def get_player(self) -> Player:
        """プレイヤーオブジェクトを取得。"""
        ...

    def get_npc(self, npc_id: str) -> NPC:
        """指定されたNPCオブジェクトを取得。"""
        ...

    def show_message(self, message: str) -> None:
        """メッセージを表示。"""
        ...

    def update_display(self) -> None:
        """表示を更新。"""
        ...


class TradingManager:
    """
    取引システムの管理クラス。

    NPCとの取引を管理し、アイテムの売買、価格計算、
    取引の実行などを行います。

    Attributes
    ----------
        current_npc: 現在取引中のNPC
        context: 取引コンテキスト
        available_items: 取引可能なアイテムリスト

    """

    def __init__(self) -> None:
        """TradingManagerの初期化。"""
        self.current_npc: NPC | None = None
        self.context: TradingContext | None = None
        self.available_items: list[TradeItem] = []

        # 価格設定
        self.base_price_multiplier = 1.0  # 基本価格倍率
        self.buy_price_multiplier = 1.5  # 購入価格倍率
        self.sell_price_multiplier = 0.6  # 売却価格倍率

    def start_trading(self, npc_id: str, context: TradingContext) -> bool:
        """
        取引を開始する。

        Args:
        ----
            npc_id: 取引するNPC ID
            context: 取引コンテキスト

        Returns:
        -------
            取引開始に成功した場合はTrue

        """
        self.context = context
        self.current_npc = context.get_npc(npc_id)

        if not self.current_npc or not self.current_npc.can_trade():
            # 取引開始失敗時にはリセット
            self.current_npc = None
            self.context = None
            return False

        # 取引可能なアイテムリストを更新
        self._update_available_items()

        return True

    def _update_available_items(self) -> None:
        """取引可能なアイテムリストを更新。"""
        self.available_items = []

        if not self.current_npc or not self.current_npc.inventory or not self.context:
            return

        player = self.context.get_player()

        # NPCの商品（プレイヤーが購入できる）
        for item in self.current_npc.inventory.items:
            price = self._calculate_buy_price(item)
            trade_item = TradeItem(
                item=item,
                price=price,
                quantity=item.stack_count if item.stackable else 1,
                trade_type=TradeType.BUY,
            )
            self.available_items.append(trade_item)

        # プレイヤーのアイテム（NPCに売却できる）
        for item in player.inventory.items:
            if self._can_sell_item(item):
                price = self._calculate_sell_price(item)
                trade_item = TradeItem(
                    item=item,
                    price=price,
                    quantity=item.stack_count if item.stackable else 1,
                    trade_type=TradeType.SELL,
                )
                self.available_items.append(trade_item)

    def _calculate_buy_price(self, item: Item) -> int:
        """
        購入価格を計算する。

        Args:
        ----
            item: 価格を計算するアイテム

        Returns:
        -------
            計算された購入価格

        """
        base_price = self._get_base_price(item)
        return int(base_price * self.buy_price_multiplier)

    def _calculate_sell_price(self, item: Item) -> int:
        """
        売却価格を計算する。

        Args:
        ----
            item: 価格を計算するアイテム

        Returns:
        -------
            計算された売却価格

        """
        base_price = self._get_base_price(item)
        return int(base_price * self.sell_price_multiplier)

    def _get_base_price(self, item: Item) -> int:
        """
        アイテムの基本価格を取得する。

        Args:
        ----
            item: 価格を取得するアイテム

        Returns:
        -------
            基本価格

        """
        # アイテムの種類に応じた基本価格
        base_prices = {
            "weapon": 100,
            "armor": 80,
            "potion": 25,
            "scroll": 50,
            "food": 10,
            "ring": 200,
            "gold": 1,
        }

        item_type = getattr(item, "item_type", "unknown")
        if item_type in base_prices:
            return base_prices[item_type]

        # アイテムクラス名から推定
        class_name = item.__class__.__name__.lower()
        if "weapon" in class_name:
            return 100
        if "armor" in class_name:
            return 80
        if "potion" in class_name:
            return 25
        if "scroll" in class_name:
            return 50
        if "food" in class_name:
            return 10
        if "ring" in class_name:
            return 200
        if "gold" in class_name:
            return 1
        return 50  # デフォルト価格

    def _can_sell_item(self, item: Item) -> bool:
        """
        アイテムが売却可能かどうかを判定する。

        Args:
        ----
            item: 判定するアイテム

        Returns:
        -------
            売却可能な場合はTrue

        """
        # 呪われたアイテムは売却不可
        if getattr(item, "cursed", False):
            return False

        # 装備中のアイテムは売却不可（実装によって異なる）
        # 現在は簡単な実装として全てのアイテムを売却可能とする
        return True

    def execute_trade(self, trade_item: TradeItem) -> bool:
        """
        取引を実行する。

        Args:
        ----
            trade_item: 取引するアイテム

        Returns:
        -------
            取引に成功した場合はTrue

        """
        if not self.current_npc or not self.context:
            return False

        player = self.context.get_player()

        if trade_item.trade_type == TradeType.BUY:
            # プレイヤーが購入
            return self._execute_buy(player, trade_item)
        if trade_item.trade_type == TradeType.SELL:
            # プレイヤーが売却
            return self._execute_sell(player, trade_item)

        return False

    def _execute_buy(self, player: Player, trade_item: TradeItem) -> bool:
        """
        購入を実行する。

        Args:
        ----
            player: プレイヤー
            trade_item: 購入するアイテム

        Returns:
        -------
            購入に成功した場合はTrue

        """
        # 金貨の確認
        if player.gold < trade_item.price:
            if self.context:
                self.context.show_message("You don't have enough gold.")
            return False

        # インベントリの空きを確認（簡単な実装）
        # 実際のcan_add_itemメソッドがない場合は、一旦スキップ
        # if not player.inventory.can_add_item(trade_item.item):
        #     if self.context:
        #         self.context.show_message("Your inventory is full.")
        #     return False

        # 取引実行
        if self.current_npc.buy_item(trade_item.item):
            player.gold -= trade_item.price
            player.inventory.add_item(trade_item.item)

            if self.context:
                self.context.show_message(
                    f"You bought {trade_item.item.name} for {trade_item.price} gold."
                )
                self.context.update_display()

            # 取引可能なアイテムリストを更新
            self._update_available_items()
            return True

        return False

    def _execute_sell(self, player: Player, trade_item: TradeItem) -> bool:
        """
        売却を実行する。

        Args:
        ----
            player: プレイヤー
            trade_item: 売却するアイテム

        Returns:
        -------
            売却に成功した場合はTrue

        """
        # アイテムの確認
        if trade_item.item not in player.inventory.items:
            if self.context:
                self.context.show_message("You don't have this item.")
            return False

        # 取引実行
        if self.current_npc.sell_item(trade_item.item):
            # 指定された数量だけアイテムを削除
            player.inventory.remove_item(trade_item.item, trade_item.quantity)
            player.gold += trade_item.price

            if self.context:
                if trade_item.quantity > 1:
                    self.context.show_message(
                        f"You sold {trade_item.quantity} {trade_item.item.name} for {trade_item.price} gold."
                    )
                else:
                    self.context.show_message(
                        f"You sold {trade_item.item.name} for {trade_item.price} gold."
                    )
                self.context.update_display()

            # 取引可能なアイテムリストを更新
            self._update_available_items()
            return True

        return False

    def get_buy_items(self) -> list[TradeItem]:
        """
        購入可能なアイテムリストを取得。

        Returns
        -------
            購入可能なアイテムリスト

        """
        return [
            item for item in self.available_items if item.trade_type == TradeType.BUY
        ]

    def get_sell_items(self) -> list[TradeItem]:
        """
        売却可能なアイテムリストを取得。

        Returns
        -------
            売却可能なアイテムリスト

        """
        return [
            item for item in self.available_items if item.trade_type == TradeType.SELL
        ]

    def get_all_items(self) -> list[TradeItem]:
        """
        すべての取引可能なアイテムリストを取得。

        Returns
        -------
            すべての取引可能なアイテムリスト

        """
        return self.available_items.copy()

    def end_trading(self) -> None:
        """取引を終了する。"""
        self.current_npc = None
        self.context = None
        self.available_items = []

    def is_trading_active(self) -> bool:
        """
        取引が進行中かどうかを判定。

        Returns
        -------
            取引が進行中の場合はTrue

        """
        return self.current_npc is not None and self.context is not None

    def get_current_npc(self) -> NPC | None:
        """
        現在取引中のNPCを取得。

        Returns
        -------
            現在取引中のNPC

        """
        return self.current_npc

    def set_price_multipliers(
        self, buy_multiplier: float, sell_multiplier: float
    ) -> None:
        """
        価格倍率を設定。

        Args:
        ----
            buy_multiplier: 購入価格倍率
            sell_multiplier: 売却価格倍率

        """
        self.buy_price_multiplier = buy_multiplier
        self.sell_price_multiplier = sell_multiplier

        # 価格変更後は取引可能なアイテムリストを更新
        if self.is_trading_active():
            self._update_available_items()
