"""
TradingManager のテストモジュール。

取引システムの機能テストを提供します。
"""

from unittest.mock import Mock

from pyrogue.core.managers.trading_manager import TradeItem, TradeType, TradingManager
from pyrogue.entities.actors.inventory import Inventory
from pyrogue.entities.actors.npc import NPC, NPCDisposition, NPCType
from pyrogue.entities.actors.player import Player
from pyrogue.entities.items.item import Armor, Weapon


class TestTradingManager:
    """TradingManager のテストクラス。"""

    def test_trading_manager_initialization(self):
        """TradingManagerの初期化テスト。"""
        manager = TradingManager()

        # 基本属性の確認
        assert manager.current_npc is None
        assert manager.context is None
        assert manager.available_items == []

        # 価格設定の確認
        assert manager.base_price_multiplier == 1.0
        assert manager.buy_price_multiplier == 1.5
        assert manager.sell_price_multiplier == 0.6

    def test_trading_manager_start_trading_success(self):
        """取引開始成功のテスト。"""
        manager = TradingManager()

        # NPCとプレイヤーの設定
        inventory = Inventory()
        weapon = Weapon(x=0, y=0, name="Test Sword", attack_bonus=5)
        inventory.add_item(weapon)

        merchant = NPC(
            char="@",
            x=5,
            y=10,
            name="Merchant",
            level=1,
            hp=50,
            max_hp=50,
            attack=10,
            defense=5,
            color=(255, 255, 0),
            disposition=NPCDisposition.FRIENDLY,
            npc_type=NPCType.MERCHANT,
            dialogue_id="merchant",
            inventory=inventory,
        )

        player = Player(x=10, y=10)
        player.gold = 500

        # モックコンテキストの設定
        mock_context = Mock()
        mock_context.get_npc.return_value = merchant
        mock_context.get_player.return_value = player

        # 取引開始
        success = manager.start_trading("merchant", mock_context)

        assert success is True
        assert manager.current_npc == merchant
        assert manager.context == mock_context
        assert len(manager.available_items) > 0

    def test_trading_manager_start_trading_failure(self):
        """取引開始失敗のテスト。"""
        manager = TradingManager()

        # 取引不可能なNPC
        non_merchant = NPC(
            char="@",
            x=5,
            y=10,
            name="Villager",
            level=1,
            hp=50,
            max_hp=50,
            attack=10,
            defense=5,
            color=(0, 255, 0),
            disposition=NPCDisposition.FRIENDLY,
            npc_type=NPCType.VILLAGER,
            dialogue_id="villager",
        )

        mock_context = Mock()
        mock_context.get_npc.return_value = non_merchant

        # 取引開始（失敗）
        success = manager.start_trading("villager", mock_context)

        assert success is False
        assert manager.current_npc is None

    def test_trading_manager_calculate_prices(self):
        """価格計算のテスト。"""
        manager = TradingManager()

        # テストアイテム
        weapon = Weapon(x=0, y=0, name="Test Sword", attack_bonus=5)

        # 基本価格の取得
        base_price = manager._get_base_price(weapon)
        assert base_price == 100  # 武器の基本価格

        # 購入価格の計算
        buy_price = manager._calculate_buy_price(weapon)
        assert buy_price == int(base_price * 1.5)  # 150

        # 売却価格の計算
        sell_price = manager._calculate_sell_price(weapon)
        assert sell_price == int(base_price * 0.6)  # 60

    def test_trading_manager_get_base_price(self):
        """基本価格取得のテスト。"""
        manager = TradingManager()

        # 各アイテムタイプの基本価格をテスト
        weapon = Weapon(x=0, y=0, name="Test Sword", attack_bonus=5)
        armor = Armor(x=0, y=0, name="Test Armor", defense_bonus=3)
        # Potionクラスは effect パラメータが必要なので、簡単なモックを使用
        potion = Mock()
        potion.__class__.__name__ = "Potion"

        assert manager._get_base_price(weapon) == 100
        assert manager._get_base_price(armor) == 80
        assert manager._get_base_price(potion) == 25

    def test_trading_manager_can_sell_item(self):
        """アイテム売却可能性のテスト。"""
        manager = TradingManager()

        # 通常のアイテム
        weapon = Weapon(x=0, y=0, name="Test Sword", attack_bonus=5)
        assert manager._can_sell_item(weapon) is True

        # 呪われたアイテム
        cursed_weapon = Weapon(x=0, y=0, name="Cursed Sword", attack_bonus=5)
        cursed_weapon.cursed = True
        assert manager._can_sell_item(cursed_weapon) is False

    def test_trading_manager_execute_buy(self):
        """購入実行のテスト。"""
        manager = TradingManager()

        # NPCとプレイヤーの設定
        inventory = Inventory()
        weapon = Weapon(x=0, y=0, name="Test Sword", attack_bonus=5)
        inventory.add_item(weapon)

        merchant = NPC(
            char="@",
            x=5,
            y=10,
            name="Merchant",
            level=1,
            hp=50,
            max_hp=50,
            attack=10,
            defense=5,
            color=(255, 255, 0),
            disposition=NPCDisposition.FRIENDLY,
            npc_type=NPCType.MERCHANT,
            dialogue_id="merchant",
            inventory=inventory,
        )

        player = Player(x=10, y=10)
        player.gold = 500

        mock_context = Mock()
        mock_context.get_npc.return_value = merchant
        mock_context.get_player.return_value = player

        # 取引開始
        manager.start_trading("merchant", mock_context)

        # 購入アイテムを取得
        buy_items = manager.get_buy_items()
        assert len(buy_items) > 0

        # 購入実行
        trade_item = buy_items[0]
        initial_gold = player.gold
        initial_inventory_size = len(player.inventory.items)

        success = manager.execute_trade(trade_item)

        assert success is True
        assert player.gold == initial_gold - trade_item.price
        assert len(player.inventory.items) == initial_inventory_size + 1
        assert weapon in player.inventory.items
        assert weapon not in merchant.inventory.items

    def test_trading_manager_execute_sell(self):
        """売却実行のテスト。"""
        manager = TradingManager()

        # NPCとプレイヤーの設定
        inventory = Inventory()
        merchant = NPC(
            char="@",
            x=5,
            y=10,
            name="Merchant",
            level=1,
            hp=50,
            max_hp=50,
            attack=10,
            defense=5,
            color=(255, 255, 0),
            disposition=NPCDisposition.FRIENDLY,
            npc_type=NPCType.MERCHANT,
            dialogue_id="merchant",
            inventory=inventory,
        )

        player = Player(x=10, y=10)
        player.gold = 100
        weapon = Weapon(x=0, y=0, name="Test Sword", attack_bonus=5)
        player.inventory.add_item(weapon)

        mock_context = Mock()
        mock_context.get_npc.return_value = merchant
        mock_context.get_player.return_value = player

        # 取引開始
        manager.start_trading("merchant", mock_context)

        # 売却アイテムを取得
        sell_items = manager.get_sell_items()
        assert len(sell_items) > 0

        # 売却実行
        trade_item = sell_items[0]
        initial_gold = player.gold
        initial_inventory_size = len(player.inventory.items)

        success = manager.execute_trade(trade_item)

        assert success is True
        assert player.gold == initial_gold + trade_item.price
        assert len(player.inventory.items) == initial_inventory_size - 1
        assert weapon not in player.inventory.items
        assert weapon in merchant.inventory.items

    def test_trading_manager_execute_buy_insufficient_gold(self):
        """金貨不足での購入失敗のテスト。"""
        manager = TradingManager()

        # NPCとプレイヤーの設定
        inventory = Inventory()
        weapon = Weapon(x=0, y=0, name="Test Sword", attack_bonus=5)
        inventory.add_item(weapon)

        merchant = NPC(
            char="@",
            x=5,
            y=10,
            name="Merchant",
            level=1,
            hp=50,
            max_hp=50,
            attack=10,
            defense=5,
            color=(255, 255, 0),
            disposition=NPCDisposition.FRIENDLY,
            npc_type=NPCType.MERCHANT,
            dialogue_id="merchant",
            inventory=inventory,
        )

        player = Player(x=10, y=10)
        player.gold = 10  # 不十分な金額

        mock_context = Mock()
        mock_context.get_npc.return_value = merchant
        mock_context.get_player.return_value = player

        # 取引開始
        manager.start_trading("merchant", mock_context)

        # 購入アイテムを取得
        buy_items = manager.get_buy_items()
        trade_item = buy_items[0]

        # 購入実行（失敗）
        success = manager.execute_trade(trade_item)

        assert success is False
        assert player.gold == 10  # 金額変化なし
        assert weapon not in player.inventory.items

    def test_trading_manager_get_item_lists(self):
        """アイテムリスト取得のテスト。"""
        manager = TradingManager()

        # NPCとプレイヤーの設定
        inventory = Inventory()
        weapon = Weapon(x=0, y=0, name="NPC Sword", attack_bonus=5)
        inventory.add_item(weapon)

        merchant = NPC(
            char="@",
            x=5,
            y=10,
            name="Merchant",
            level=1,
            hp=50,
            max_hp=50,
            attack=10,
            defense=5,
            color=(255, 255, 0),
            disposition=NPCDisposition.FRIENDLY,
            npc_type=NPCType.MERCHANT,
            dialogue_id="merchant",
            inventory=inventory,
        )

        player = Player(x=10, y=10)
        player_weapon = Weapon(x=0, y=0, name="Player Sword", attack_bonus=3)
        player.inventory.add_item(player_weapon)

        mock_context = Mock()
        mock_context.get_npc.return_value = merchant
        mock_context.get_player.return_value = player

        # 取引開始
        manager.start_trading("merchant", mock_context)

        # アイテムリストの取得
        buy_items = manager.get_buy_items()
        sell_items = manager.get_sell_items()
        all_items = manager.get_all_items()

        assert len(buy_items) == 1
        assert len(sell_items) == 1
        assert len(all_items) == 2

        assert buy_items[0].trade_type == TradeType.BUY
        assert sell_items[0].trade_type == TradeType.SELL

    def test_trading_manager_end_trading(self):
        """取引終了のテスト。"""
        manager = TradingManager()

        # 取引開始
        inventory = Inventory()
        merchant = NPC(
            char="@",
            x=5,
            y=10,
            name="Merchant",
            level=1,
            hp=50,
            max_hp=50,
            attack=10,
            defense=5,
            color=(255, 255, 0),
            disposition=NPCDisposition.FRIENDLY,
            npc_type=NPCType.MERCHANT,
            dialogue_id="merchant",
            inventory=inventory,
        )

        mock_context = Mock()
        mock_context.get_npc.return_value = merchant
        mock_context.get_player.return_value = Player(x=10, y=10)

        manager.start_trading("merchant", mock_context)

        # 取引中であることを確認
        assert manager.is_trading_active() is True

        # 取引終了
        manager.end_trading()

        assert manager.is_trading_active() is False
        assert manager.current_npc is None
        assert manager.context is None
        assert manager.available_items == []

    def test_trading_manager_price_multipliers(self):
        """価格倍率設定のテスト。"""
        manager = TradingManager()

        # 価格倍率の変更
        manager.set_price_multipliers(2.0, 0.8)

        assert manager.buy_price_multiplier == 2.0
        assert manager.sell_price_multiplier == 0.8

        # 価格計算の確認
        weapon = Weapon(x=0, y=0, name="Test Sword", attack_bonus=5)
        base_price = manager._get_base_price(weapon)

        buy_price = manager._calculate_buy_price(weapon)
        sell_price = manager._calculate_sell_price(weapon)

        assert buy_price == int(base_price * 2.0)
        assert sell_price == int(base_price * 0.8)

    def test_trade_item_creation(self):
        """TradeItemの作成テスト。"""
        weapon = Weapon(x=0, y=0, name="Test Sword", attack_bonus=5)

        trade_item = TradeItem(item=weapon, price=150, quantity=1, trade_type=TradeType.BUY)

        assert trade_item.item == weapon
        assert trade_item.price == 150
        assert trade_item.quantity == 1
        assert trade_item.trade_type == TradeType.BUY
