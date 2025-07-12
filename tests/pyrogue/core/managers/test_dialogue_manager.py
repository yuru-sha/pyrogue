"""
DialogueManager のテストモジュール。

会話システムの機能テストを提供します。
"""

from unittest.mock import Mock

from pyrogue.core.managers.dialogue_manager import (
    DialogueAction,
    DialogueChoice,
    DialogueManager,
    DialogueNode,
)


class TestDialogueManager:
    """DialogueManager のテストクラス。"""

    def test_dialogue_manager_initialization(self):
        """DialogueManagerの初期化テスト。"""
        manager = DialogueManager()

        # 基本属性の確認
        assert manager.dialogues is not None
        assert manager.current_dialogue is None
        assert manager.current_node is None
        assert manager.context is None

        # デフォルトの会話データが読み込まれることを確認
        assert "friendly_merchant" in manager.dialogues
        assert "neutral_guard" in manager.dialogues
        assert len(manager.dialogues["friendly_merchant"]) > 0
        assert len(manager.dialogues["neutral_guard"]) > 0

    def test_dialogue_manager_start_dialogue(self):
        """会話開始のテスト。"""
        manager = DialogueManager()
        mock_context = Mock()

        # 有効な会話IDで開始
        success = manager.start_dialogue("friendly_merchant", mock_context)
        assert success is True
        assert manager.current_dialogue == "friendly_merchant"
        assert manager.current_node is not None
        assert manager.context == mock_context

        # 無効な会話IDで開始
        success = manager.start_dialogue("invalid_dialogue", mock_context)
        assert success is False

    def test_dialogue_manager_get_current_node(self):
        """現在の会話ノード取得のテスト。"""
        manager = DialogueManager()
        mock_context = Mock()

        # 会話開始前
        assert manager.get_current_node() is None

        # 会話開始後
        manager.start_dialogue("friendly_merchant", mock_context)
        node = manager.get_current_node()
        assert node is not None
        assert node.id == "greeting"
        assert "Welcome to my shop" in node.text
        assert len(node.choices) > 0

    def test_dialogue_manager_select_choice(self):
        """選択肢選択のテスト。"""
        manager = DialogueManager()
        mock_context = Mock()

        # 会話開始
        manager.start_dialogue("friendly_merchant", mock_context)

        # 有効な選択肢を選択
        action = manager.select_choice(1)  # "Tell me about your wares."
        assert action == DialogueAction.CONTINUE
        assert manager.current_node is not None
        assert manager.current_node.id == "about_wares"

        # 無効な選択肢インデックス
        action = manager.select_choice(999)
        assert action == DialogueAction.END

    def test_dialogue_manager_trade_action(self):
        """取引アクションのテスト。"""
        manager = DialogueManager()
        mock_context = Mock()

        # 会話開始
        manager.start_dialogue("friendly_merchant", mock_context)

        # 取引を選択
        action = manager.select_choice(0)  # "I'd like to trade."
        assert action == DialogueAction.TRADE

        # コンテキストの open_trade_screen が呼び出されることを確認
        mock_context.open_trade_screen.assert_called_once()

    def test_dialogue_manager_end_action(self):
        """終了アクションのテスト。"""
        manager = DialogueManager()
        mock_context = Mock()

        # 会話開始
        manager.start_dialogue("friendly_merchant", mock_context)

        # 終了を選択
        action = manager.select_choice(2)  # "Goodbye."
        assert action == DialogueAction.END
        assert manager.current_dialogue is None
        assert manager.current_node is None
        assert manager.context is None

    def test_dialogue_manager_end_dialogue(self):
        """会話終了のテスト。"""
        manager = DialogueManager()
        mock_context = Mock()

        # 会話開始
        manager.start_dialogue("friendly_merchant", mock_context)
        assert manager.is_dialogue_active() is True

        # 会話終了
        manager.end_dialogue()
        assert manager.is_dialogue_active() is False
        assert manager.current_dialogue is None
        assert manager.current_node is None
        assert manager.context is None

    def test_dialogue_manager_is_dialogue_active(self):
        """会話進行中判定のテスト。"""
        manager = DialogueManager()
        mock_context = Mock()

        # 会話開始前
        assert manager.is_dialogue_active() is False

        # 会話開始後
        manager.start_dialogue("friendly_merchant", mock_context)
        assert manager.is_dialogue_active() is True

        # 会話終了後
        manager.end_dialogue()
        assert manager.is_dialogue_active() is False

    def test_dialogue_manager_get_available_dialogues(self):
        """利用可能な会話リスト取得のテスト。"""
        manager = DialogueManager()

        dialogues = manager.get_available_dialogues()
        assert isinstance(dialogues, list)
        assert "friendly_merchant" in dialogues
        assert "neutral_guard" in dialogues

    def test_dialogue_manager_add_dialogue(self):
        """会話データ追加のテスト。"""
        manager = DialogueManager()

        # 新しい会話を追加
        custom_nodes = [
            DialogueNode(
                id="test_greeting",
                text="Hello, this is a test dialogue!",
                speaker="Test NPC",
                choices=[
                    DialogueChoice(
                        text="Test choice", next_node=None, action=DialogueAction.END
                    )
                ],
            )
        ]

        manager.add_dialogue("test_dialogue", custom_nodes)

        # 追加された会話を確認
        assert "test_dialogue" in manager.dialogues
        assert len(manager.dialogues["test_dialogue"]) == 1
        assert manager.dialogues["test_dialogue"][0].id == "test_greeting"

    def test_dialogue_manager_remove_dialogue(self):
        """会話データ削除のテスト。"""
        manager = DialogueManager()

        # 既存の会話を削除
        manager.remove_dialogue("friendly_merchant")
        assert "friendly_merchant" not in manager.dialogues

        # 存在しない会話を削除（エラーなし）
        manager.remove_dialogue("non_existent_dialogue")  # エラーが発生しないことを確認

    def test_dialogue_manager_neutral_guard_dialogue(self):
        """中立的な警備員との会話のテスト。"""
        manager = DialogueManager()
        mock_context = Mock()

        # 中立的な警備員の会話開始
        manager.start_dialogue("neutral_guard", mock_context)

        # 初期ノードの確認
        node = manager.get_current_node()
        assert node is not None
        assert node.id == "greeting"
        assert "Halt! State your business" in node.text
        assert len(node.choices) == 3

        # "I'm just passing through." を選択
        action = manager.select_choice(0)
        assert action == DialogueAction.CONTINUE
        assert manager.current_node.id == "passing_through"

        # "Thanks for the warning." を選択
        action = manager.select_choice(0)
        assert action == DialogueAction.END
        assert manager.current_dialogue is None

    def test_dialogue_manager_information_path(self):
        """情報を求める会話パスのテスト。"""
        manager = DialogueManager()
        mock_context = Mock()

        # 中立的な警備員の会話開始
        manager.start_dialogue("neutral_guard", mock_context)

        # "I'm looking for information." を選択
        action = manager.select_choice(1)
        assert action == DialogueAction.CONTINUE
        assert manager.current_node.id == "information"

        # "About the dungeon." を選択
        action = manager.select_choice(0)
        assert action == DialogueAction.CONTINUE
        assert manager.current_node.id == "dungeon_info"
        assert "26 levels" in manager.current_node.text

        # 最後の選択肢
        action = manager.select_choice(0)
        assert action == DialogueAction.END

    def test_dialogue_node_and_choice_creation(self):
        """DialogueNodeとDialogueChoiceの作成テスト。"""
        # DialogueChoice の作成
        choice = DialogueChoice(
            text="Test choice",
            next_node="test_node",
            action=DialogueAction.CONTINUE,
            condition="test_condition",
        )

        assert choice.text == "Test choice"
        assert choice.next_node == "test_node"
        assert choice.action == DialogueAction.CONTINUE
        assert choice.condition == "test_condition"

        # DialogueNode の作成
        node = DialogueNode(
            id="test_node",
            text="Test dialogue text",
            speaker="Test Speaker",
            choices=[choice],
            action=DialogueAction.CONTINUE,
            condition="test_condition",
        )

        assert node.id == "test_node"
        assert node.text == "Test dialogue text"
        assert node.speaker == "Test Speaker"
        assert len(node.choices) == 1
        assert node.choices[0] == choice
        assert node.action == DialogueAction.CONTINUE
        assert node.condition == "test_condition"

    def test_dialogue_manager_find_node(self):
        """ノード検索のテスト。"""
        manager = DialogueManager()
        mock_context = Mock()

        # 会話開始
        manager.start_dialogue("friendly_merchant", mock_context)

        # 存在するノードを検索
        node = manager._find_node("about_wares")
        assert node is not None
        assert node.id == "about_wares"

        # 存在しないノードを検索
        node = manager._find_node("non_existent_node")
        assert node is None
