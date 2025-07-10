"""
NPC クラスのテストモジュール。

NPCの基本機能、会話、取引、クエストシステムのテストを提供します。
"""

import pytest
from unittest.mock import Mock

from pyrogue.entities.actors.npc import NPC, NPCDisposition, NPCType
from pyrogue.entities.actors.inventory import Inventory
from pyrogue.entities.items.item import Gold, Weapon


class TestNPC:
    """NPC クラスのテストクラス。"""

    def test_npc_initialization(self):
        """NPCの初期化テスト。"""
        inventory = Inventory()
        npc = NPC(
            char='@',
            x=5,
            y=10,
            name='Merchant Bob',
            level=1,
            hp=50,
            max_hp=50,
            attack=10,
            defense=5,
            color=(255, 255, 0),
            disposition=NPCDisposition.FRIENDLY,
            npc_type=NPCType.MERCHANT,
            dialogue_id='merchant_bob_intro',
            inventory=inventory,
            quest_ids=['quest_1', 'quest_2']
        )

        # 基本属性の確認
        assert npc.char == '@'
        assert npc.x == 5
        assert npc.y == 10
        assert npc.name == 'Merchant Bob'
        assert npc.level == 1
        assert npc.hp == 50
        assert npc.max_hp == 50
        assert npc.attack == 10
        assert npc.defense == 5
        assert npc.color == (255, 255, 0)
        assert npc.disposition == NPCDisposition.FRIENDLY
        assert npc.npc_type == NPCType.MERCHANT
        assert npc.dialogue_id == 'merchant_bob_intro'
        assert npc.inventory == inventory
        assert npc.quest_ids == ['quest_1', 'quest_2']

        # 友好的なNPCは非敵対的
        assert not npc.is_hostile

        # システムの初期化確認
        assert npc.status_effects is not None
        assert npc.dialogue_state == {}
        assert npc.last_interaction_turn == 0

    def test_npc_hostile_initialization(self):
        """敵対的NPCの初期化テスト。"""
        npc = NPC(
            char='!',
            x=5,
            y=10,
            name='Hostile Guard',
            level=5,
            hp=100,
            max_hp=100,
            attack=20,
            defense=15,
            color=(255, 0, 0),
            disposition=NPCDisposition.HOSTILE,
            npc_type=NPCType.GUARD,
            dialogue_id='hostile_guard'
        )

        # 敵対的なNPCは敵対的
        assert npc.is_hostile
        assert npc.disposition == NPCDisposition.HOSTILE

    def test_npc_can_trade(self):
        """NPC取引可能性テスト。"""
        inventory = Inventory()

        # 友好的な商人 - 取引可能
        friendly_merchant = NPC(
            char='@', x=5, y=10, name='Friendly Merchant', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(255, 255, 0),
            disposition=NPCDisposition.FRIENDLY, npc_type=NPCType.MERCHANT,
            dialogue_id='friendly_merchant', inventory=inventory
        )
        assert friendly_merchant.can_trade()

        # 中立的な商人 - 取引可能
        neutral_merchant = NPC(
            char='@', x=5, y=10, name='Neutral Merchant', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(255, 255, 0),
            disposition=NPCDisposition.NEUTRAL, npc_type=NPCType.MERCHANT,
            dialogue_id='neutral_merchant', inventory=inventory
        )
        assert neutral_merchant.can_trade()

        # 敵対的な商人 - 取引不可
        hostile_merchant = NPC(
            char='@', x=5, y=10, name='Hostile Merchant', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(255, 0, 0),
            disposition=NPCDisposition.HOSTILE, npc_type=NPCType.MERCHANT,
            dialogue_id='hostile_merchant', inventory=inventory
        )
        assert not hostile_merchant.can_trade()

        # 村人 - 取引不可
        villager = NPC(
            char='@', x=5, y=10, name='Villager', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(0, 255, 0),
            disposition=NPCDisposition.FRIENDLY, npc_type=NPCType.VILLAGER,
            dialogue_id='villager'
        )
        assert not villager.can_trade()

        # インベントリなしの商人 - 取引不可
        no_inventory_merchant = NPC(
            char='@', x=5, y=10, name='No Inventory Merchant', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(255, 255, 0),
            disposition=NPCDisposition.FRIENDLY, npc_type=NPCType.MERCHANT,
            dialogue_id='no_inventory_merchant', inventory=None
        )
        assert not no_inventory_merchant.can_trade()

    def test_npc_can_talk(self):
        """NPC会話可能性テスト。"""
        # 友好的なNPC - 会話可能
        friendly_npc = NPC(
            char='@', x=5, y=10, name='Friendly NPC', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(0, 255, 0),
            disposition=NPCDisposition.FRIENDLY, npc_type=NPCType.VILLAGER,
            dialogue_id='friendly_npc'
        )
        assert friendly_npc.can_talk()

        # 中立的なNPC - 会話可能
        neutral_npc = NPC(
            char='@', x=5, y=10, name='Neutral NPC', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(128, 128, 128),
            disposition=NPCDisposition.NEUTRAL, npc_type=NPCType.GUARD,
            dialogue_id='neutral_npc'
        )
        assert neutral_npc.can_talk()

        # 敵対的なNPC - 会話不可
        hostile_npc = NPC(
            char='@', x=5, y=10, name='Hostile NPC', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(255, 0, 0),
            disposition=NPCDisposition.HOSTILE, npc_type=NPCType.GUARD,
            dialogue_id='hostile_npc'
        )
        assert not hostile_npc.can_talk()

        # dialogue_idなしのNPC - 会話不可
        no_dialogue_npc = NPC(
            char='@', x=5, y=10, name='No Dialogue NPC', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(0, 255, 0),
            disposition=NPCDisposition.FRIENDLY, npc_type=NPCType.VILLAGER,
            dialogue_id=None
        )
        assert not no_dialogue_npc.can_talk()

    def test_npc_quest_management(self):
        """NPCクエスト管理テスト。"""
        npc = NPC(
            char='@', x=5, y=10, name='Quest Giver', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(0, 0, 255),
            disposition=NPCDisposition.FRIENDLY, npc_type=NPCType.PRIEST,
            dialogue_id='quest_giver', quest_ids=['quest_1']
        )

        # 初期クエスト
        assert npc.has_quest('quest_1')
        assert not npc.has_quest('quest_2')

        # クエスト追加
        npc.add_quest('quest_2')
        assert npc.has_quest('quest_2')
        assert 'quest_2' in npc.quest_ids

        # 重複クエスト追加（追加されない）
        npc.add_quest('quest_1')
        assert npc.quest_ids.count('quest_1') == 1

        # クエスト削除
        npc.remove_quest('quest_1')
        assert not npc.has_quest('quest_1')
        assert 'quest_1' not in npc.quest_ids

        # 存在しないクエスト削除（エラーなし）
        npc.remove_quest('non_existent_quest')  # エラーが発生しないことを確認

    def test_npc_dialogue_state(self):
        """NPC会話状態管理テスト。"""
        npc = NPC(
            char='@', x=5, y=10, name='Dialogue NPC', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(0, 255, 0),
            disposition=NPCDisposition.FRIENDLY, npc_type=NPCType.VILLAGER,
            dialogue_id='dialogue_npc'
        )

        # 初期状態
        assert npc.get_dialogue_state('visited') is None
        assert npc.get_dialogue_state('visited', False) is False

        # 状態設定
        npc.set_dialogue_state('visited', True)
        assert npc.get_dialogue_state('visited') is True

        # 複数の状態管理
        npc.set_dialogue_state('conversation_stage', 'introduction')
        npc.set_dialogue_state('trust_level', 5)

        assert npc.get_dialogue_state('conversation_stage') == 'introduction'
        assert npc.get_dialogue_state('trust_level') == 5

    def test_npc_interaction_cooldown(self):
        """NPC相互作用クールダウンテスト。"""
        npc = NPC(
            char='@', x=5, y=10, name='Cooldown NPC', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(0, 255, 0),
            disposition=NPCDisposition.FRIENDLY, npc_type=NPCType.VILLAGER,
            dialogue_id='cooldown_npc'
        )

        # 初期状態
        assert npc.get_interaction_cooldown(0) == 0
        assert npc.get_interaction_cooldown(10) == 0

        # 相互作用後のクールダウン
        npc.update_interaction_turn(5)
        assert npc.get_interaction_cooldown(5) == 3  # 直後なので3ターン
        assert npc.get_interaction_cooldown(6) == 2  # 1ターン後なので2ターン
        assert npc.get_interaction_cooldown(7) == 1  # 2ターン後なので1ターン
        assert npc.get_interaction_cooldown(8) == 0  # 3ターン後なのでクールダウン終了

    def test_npc_trading_functionality(self):
        """NPC取引機能テスト。"""
        inventory = Inventory()
        weapon = Weapon(x=0, y=0, name='Test Sword', attack_bonus=5)
        inventory.add_item(weapon)

        merchant = NPC(
            char='@', x=5, y=10, name='Trading Merchant', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(255, 255, 0),
            disposition=NPCDisposition.FRIENDLY, npc_type=NPCType.MERCHANT,
            dialogue_id='trading_merchant', inventory=inventory
        )

        # 販売テスト
        assert merchant.buy_item(weapon) is True
        assert weapon not in merchant.inventory.items

        # 買い取りテスト
        new_weapon = Weapon(x=0, y=0, name='New Sword', attack_bonus=10)
        assert merchant.sell_item(new_weapon) is True
        assert new_weapon in merchant.inventory.items

        # 取引不可能なNPCのテスト
        villager = NPC(
            char='@', x=5, y=10, name='Villager', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(0, 255, 0),
            disposition=NPCDisposition.FRIENDLY, npc_type=NPCType.VILLAGER,
            dialogue_id='villager'
        )
        assert villager.sell_item(new_weapon) is False
        assert villager.buy_item(new_weapon) is False

    def test_npc_greeting_and_farewell_messages(self):
        """NPC挨拶・別れメッセージテスト。"""
        # 友好的なNPC
        friendly_npc = NPC(
            char='@', x=5, y=10, name='Alice', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(0, 255, 0),
            disposition=NPCDisposition.FRIENDLY, npc_type=NPCType.VILLAGER,
            dialogue_id='alice'
        )
        assert "Hello there, adventurer!" in friendly_npc.get_greeting_message()
        assert "Alice" in friendly_npc.get_greeting_message()
        assert "Farewell, and may fortune favor you!" in friendly_npc.get_farewell_message()

        # 中立的なNPC
        neutral_npc = NPC(
            char='@', x=5, y=10, name='Bob', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(128, 128, 128),
            disposition=NPCDisposition.NEUTRAL, npc_type=NPCType.GUARD,
            dialogue_id='bob'
        )
        assert "Greetings. I am Bob." in neutral_npc.get_greeting_message()
        assert "Until we meet again." in neutral_npc.get_farewell_message()

        # 敵対的なNPC
        hostile_npc = NPC(
            char='@', x=5, y=10, name='Charlie', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(255, 0, 0),
            disposition=NPCDisposition.HOSTILE, npc_type=NPCType.GUARD,
            dialogue_id='charlie'
        )
        assert "glares at you suspiciously" in hostile_npc.get_greeting_message()
        assert "turns away coldly" in hostile_npc.get_farewell_message()

    def test_npc_status_effects(self):
        """NPC状態異常テスト。"""
        npc = NPC(
            char='@', x=5, y=10, name='Status NPC', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(0, 255, 0),
            disposition=NPCDisposition.FRIENDLY, npc_type=NPCType.VILLAGER,
            dialogue_id='status_npc'
        )

        # 初期状態
        assert not npc.is_paralyzed()
        assert not npc.is_confused()
        assert not npc.is_poisoned()
        assert not npc.has_status_effect("NonExistent")

        # 状態異常の更新（モックコンテキストを使用）
        mock_context = Mock()
        npc.update_status_effects(mock_context)

        # status_effects.update_effects が呼び出されることを確認
        assert hasattr(npc.status_effects, 'update_effects')

    def test_npc_string_representation(self):
        """NPC文字列表現テスト。"""
        npc = NPC(
            char='@', x=5, y=10, name='Test NPC', level=1,
            hp=50, max_hp=50, attack=10, defense=5, color=(0, 255, 0),
            disposition=NPCDisposition.FRIENDLY, npc_type=NPCType.MERCHANT,
            dialogue_id='test_npc'
        )

        # __str__ テスト
        assert str(npc) == "Test NPC (merchant)"

        # __repr__ テスト
        repr_str = repr(npc)
        assert "Test NPC" in repr_str
        assert "merchant" in repr_str
        assert "friendly" in repr_str
        assert "(5, 10)" in repr_str
