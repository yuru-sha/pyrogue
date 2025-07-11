"""
DialogueManager モジュール。

このモジュールは、NPCとの会話システムを管理します。
会話データの読み込み、会話の進行管理、選択肢の処理などを行います。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol


class DialogueAction(Enum):
    """会話アクションの種類を定義する列挙型。"""

    CONTINUE = "continue"  # 会話を継続
    END = "end"  # 会話を終了
    TRADE = "trade"  # 取引画面を開く
    QUEST = "quest"  # クエスト関連の処理
    CUSTOM = "custom"  # カスタム処理


@dataclass
class DialogueChoice:
    """
    会話の選択肢を表すデータクラス。

    Attributes
    ----------
        text: 選択肢のテキスト
        next_node: 次の会話ノードID
        action: 実行するアクション
        condition: 選択肢の表示条件

    """

    text: str
    next_node: str | None = None
    action: DialogueAction = DialogueAction.CONTINUE
    condition: str | None = None


@dataclass
class DialogueNode:
    """
    会話ノードを表すデータクラス。

    Attributes
    ----------
        id: ノードID
        text: 表示するテキスト
        speaker: 話者（NPC名など）
        choices: 選択肢のリスト
        action: ノード実行時のアクション
        condition: ノード表示条件

    """

    id: str
    text: str
    speaker: str
    choices: list[DialogueChoice]
    action: DialogueAction = DialogueAction.CONTINUE
    condition: str | None = None


class DialogueContext(Protocol):
    """
    会話コンテキストのプロトコル。

    DialogueManagerが必要とする情報を提供するインターフェース。
    """

    def get_player(self) -> Any:
        """プレイヤーオブジェクトを取得。"""
        ...

    def get_npc(self, npc_id: str) -> Any:
        """指定されたNPCオブジェクトを取得。"""
        ...

    def show_message(self, message: str) -> None:
        """メッセージを表示。"""
        ...

    def open_trade_screen(self, npc_id: str) -> None:
        """取引画面を開く。"""
        ...


class DialogueManager:
    """
    会話システムの管理クラス。

    NPCとの会話を管理し、会話データの読み込み、会話の進行、
    選択肢の処理などを行います。

    Attributes
    ----------
        dialogues: 読み込まれた会話データ
        current_dialogue: 現在の会話ID
        current_node: 現在の会話ノード
        context: 会話コンテキスト

    """

    def __init__(self, data_path: Path | None = None) -> None:
        """
        DialogueManagerの初期化。

        Args:
        ----
            data_path: 会話データファイルのパス

        """
        self.dialogues: dict[str, list[DialogueNode]] = {}
        self.current_dialogue: str | None = None
        self.current_node: DialogueNode | None = None
        self.context: DialogueContext | None = None

        # デフォルトの会話データパス
        if data_path is None:
            data_path = Path(__file__).parent.parent.parent / "data" / "dialogues.json"

        self.data_path = data_path
        self._load_default_dialogues()

    def _load_default_dialogues(self) -> None:
        """デフォルトの会話データを読み込む。"""
        # デフォルトの会話データを設定
        default_dialogues = {
            "friendly_merchant": [
                DialogueNode(
                    id="greeting",
                    text="Welcome to my shop, traveler! I have many fine wares to offer.",
                    speaker="Merchant",
                    choices=[
                        DialogueChoice(
                            text="I'd like to trade.",
                            next_node=None,
                            action=DialogueAction.TRADE,
                        ),
                        DialogueChoice(
                            text="Tell me about your wares.", next_node="about_wares"
                        ),
                        DialogueChoice(
                            text="Goodbye.", next_node=None, action=DialogueAction.END
                        ),
                    ],
                ),
                DialogueNode(
                    id="about_wares",
                    text="I sell weapons, armor, potions, and scrolls. All of the finest quality!",
                    speaker="Merchant",
                    choices=[
                        DialogueChoice(
                            text="I'd like to trade.",
                            next_node=None,
                            action=DialogueAction.TRADE,
                        ),
                        DialogueChoice(
                            text="Maybe later.",
                            next_node=None,
                            action=DialogueAction.END,
                        ),
                    ],
                ),
            ],
            "neutral_guard": [
                DialogueNode(
                    id="greeting",
                    text="Halt! State your business in this area.",
                    speaker="Guard",
                    choices=[
                        DialogueChoice(
                            text="I'm just passing through.",
                            next_node="passing_through",
                        ),
                        DialogueChoice(
                            text="I'm looking for information.", next_node="information"
                        ),
                        DialogueChoice(
                            text="Sorry, I'll be on my way.",
                            next_node=None,
                            action=DialogueAction.END,
                        ),
                    ],
                ),
                DialogueNode(
                    id="passing_through",
                    text="Very well. Be careful in these parts - monsters are active.",
                    speaker="Guard",
                    choices=[
                        DialogueChoice(
                            text="Thanks for the warning.",
                            next_node=None,
                            action=DialogueAction.END,
                        )
                    ],
                ),
                DialogueNode(
                    id="information",
                    text="What kind of information are you seeking?",
                    speaker="Guard",
                    choices=[
                        DialogueChoice(
                            text="About the dungeon.", next_node="dungeon_info"
                        ),
                        DialogueChoice(
                            text="Never mind.",
                            next_node=None,
                            action=DialogueAction.END,
                        ),
                    ],
                ),
                DialogueNode(
                    id="dungeon_info",
                    text="The dungeon goes deep - 26 levels they say. Many have entered, few return.",
                    speaker="Guard",
                    choices=[
                        DialogueChoice(
                            text="I see. Thank you.",
                            next_node=None,
                            action=DialogueAction.END,
                        )
                    ],
                ),
            ],
        }

        self.dialogues = default_dialogues

    def load_dialogues_from_file(self, file_path: Path) -> None:
        """
        ファイルから会話データを読み込む。

        Args:
        ----
            file_path: 会話データファイルのパス

        """
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # JSONデータを DialogueNode に変換
            for dialogue_id, nodes_data in data.items():
                nodes = []
                for node_data in nodes_data:
                    choices = []
                    for choice_data in node_data.get("choices", []):
                        choice = DialogueChoice(
                            text=choice_data["text"],
                            next_node=choice_data.get("next_node"),
                            action=DialogueAction(
                                choice_data.get("action", "continue")
                            ),
                            condition=choice_data.get("condition"),
                        )
                        choices.append(choice)

                    node = DialogueNode(
                        id=node_data["id"],
                        text=node_data["text"],
                        speaker=node_data["speaker"],
                        choices=choices,
                        action=DialogueAction(node_data.get("action", "continue")),
                        condition=node_data.get("condition"),
                    )
                    nodes.append(node)

                self.dialogues[dialogue_id] = nodes

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Failed to load dialogue data: {e}")

    def start_dialogue(self, dialogue_id: str, context: DialogueContext) -> bool:
        """
        会話を開始する。

        Args:
        ----
            dialogue_id: 会話ID
            context: 会話コンテキスト

        Returns:
        -------
            会話開始に成功した場合はTrue

        """
        if dialogue_id not in self.dialogues:
            return False

        self.current_dialogue = dialogue_id
        self.context = context
        self.current_node = self.dialogues[dialogue_id][0]  # 最初のノードを設定

        return True

    def get_current_node(self) -> DialogueNode | None:
        """
        現在の会話ノードを取得。

        Returns
        -------
            現在の会話ノード

        """
        return self.current_node

    def select_choice(self, choice_index: int) -> DialogueAction:
        """
        選択肢を選択して会話を進める。

        Args:
        ----
            choice_index: 選択肢のインデックス

        Returns:
        -------
            実行するアクション

        """
        if not self.current_node or not self.context:
            return DialogueAction.END

        if choice_index < 0 or choice_index >= len(self.current_node.choices):
            return DialogueAction.END

        choice = self.current_node.choices[choice_index]

        # 条件チェック
        if choice.condition and not self._check_condition(choice.condition):
            return DialogueAction.CONTINUE

        # アクション実行
        if choice.action == DialogueAction.TRADE:
            if self.context and self.current_dialogue:
                self.context.open_trade_screen(self.current_dialogue)
            return DialogueAction.TRADE

        if choice.action == DialogueAction.END:
            self.end_dialogue()
            return DialogueAction.END

        if choice.next_node:
            # 次のノードに移動
            self.current_node = self._find_node(choice.next_node)
            if not self.current_node:
                self.end_dialogue()
                return DialogueAction.END
            return DialogueAction.CONTINUE

        self.end_dialogue()
        return DialogueAction.END

    def _find_node(self, node_id: str) -> DialogueNode | None:
        """
        指定されたIDのノードを検索。

        Args:
        ----
            node_id: ノードID

        Returns:
        -------
            見つかったノード、またはNone

        """
        if not self.current_dialogue:
            return None

        nodes = self.dialogues.get(self.current_dialogue, [])
        for node in nodes:
            if node.id == node_id:
                return node

        return None

    def _check_condition(self, condition: str) -> bool:
        """
        条件をチェックする。

        Args:
        ----
            condition: チェックする条件

        Returns:
        -------
            条件が満たされている場合はTrue

        """
        # 簡単な条件チェック実装
        # 実際のゲームでは、より複雑な条件評価が必要
        if not self.context:
            return False

        # 例: "player_level >= 5"
        # 実装は省略（必要に応じて拡張）

        return True

    def end_dialogue(self) -> None:
        """会話を終了する。"""
        self.current_dialogue = None
        self.current_node = None
        self.context = None

    def is_dialogue_active(self) -> bool:
        """
        会話が進行中かどうかを判定。

        Returns
        -------
            会話が進行中の場合はTrue

        """
        return self.current_dialogue is not None and self.current_node is not None

    def get_available_dialogues(self) -> list[str]:
        """
        利用可能な会話IDのリストを取得。

        Returns
        -------
            会話IDのリスト

        """
        return list(self.dialogues.keys())

    def add_dialogue(self, dialogue_id: str, nodes: list[DialogueNode]) -> None:
        """
        会話データを追加。

        Args:
        ----
            dialogue_id: 会話ID
            nodes: 会話ノードのリスト

        """
        self.dialogues[dialogue_id] = nodes

    def remove_dialogue(self, dialogue_id: str) -> None:
        """
        会話データを削除。

        Args:
        ----
            dialogue_id: 削除する会話ID

        """
        if dialogue_id in self.dialogues:
            del self.dialogues[dialogue_id]
