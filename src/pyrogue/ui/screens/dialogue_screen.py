"""
DialogueScreen モジュール。

このモジュールは、NPCとの会話を表示するスクリーンを実装します。
会話テキストの表示、選択肢の提示、プレイヤーの選択処理を行います。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod

from pyrogue.core.managers.dialogue_manager import DialogueAction, DialogueManager
from pyrogue.ui.screens.screen import Screen

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine


class DialogueScreen(Screen):
    """
    会話画面を管理するクラス。

    NPCとの会話を表示し、プレイヤーの選択を処理します。
    DialogueManagerと連携して会話の進行を管理します。

    Attributes
    ----------
        dialogue_manager: 会話管理システム
        npc_id: 会話中のNPC ID
        selected_choice: 現在選択中の選択肢インデックス
        max_text_width: テキストの最大幅

    """

    def __init__(
        self, engine: Engine, dialogue_manager: DialogueManager, npc_id: str
    ) -> None:
        """
        DialogueScreenの初期化。

        Args:
        ----
            engine: ゲームエンジン
            dialogue_manager: 会話管理システム
            npc_id: 会話中のNPC ID

        """
        super().__init__(engine)
        self.dialogue_manager = dialogue_manager
        self.npc_id = npc_id
        self.selected_choice = 0
        self.max_text_width = 60  # テキストの最大幅

        # 会話開始
        if not self.dialogue_manager.start_dialogue(npc_id, self):
            # 会話開始に失敗した場合は前の画面に戻る
            pass  # 実際にはGameScreenに戻る必要があるが、ここでは何もしない

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

    def open_trade_screen(self, npc_id: str) -> None:
        """取引画面を開く。"""
        # 将来的にTradingScreenを実装する際に使用
        self.engine.message_log.add_message("Trade screen not implemented yet.")

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
            # ESCキーで会話を終了
            self.dialogue_manager.end_dialogue()
            # 前の画面に戻る（通常はGameScreen）
            from pyrogue.ui.screens.game_screen import GameScreen

            return GameScreen(self.engine)

        # 現在のノードを取得
        current_node = self.dialogue_manager.get_current_node()
        if not current_node:
            # ノードがない場合は会話を終了
            from pyrogue.ui.screens.game_screen import GameScreen

            return GameScreen(self.engine)

        # 上下キーで選択肢を移動
        if key_sym == tcod.event.K_UP:
            self.selected_choice = max(0, self.selected_choice - 1)
        elif key_sym == tcod.event.K_DOWN:
            self.selected_choice = min(
                len(current_node.choices) - 1, self.selected_choice + 1
            )

        # Enterキーで選択肢を決定
        elif key_sym == tcod.event.K_RETURN:
            action = self.dialogue_manager.select_choice(self.selected_choice)

            if action == DialogueAction.END:
                # 会話終了
                from pyrogue.ui.screens.game_screen import GameScreen

                return GameScreen(self.engine)
            if action == DialogueAction.TRADE:
                # 取引画面を開く（現在は未実装）
                from pyrogue.ui.screens.game_screen import GameScreen

                return GameScreen(self.engine)
            if action == DialogueAction.CONTINUE:
                # 会話を継続、選択肢をリセット
                self.selected_choice = 0

        # 数字キーで直接選択
        elif tcod.event.K_1 <= key_sym <= tcod.event.K_9:
            choice_index = key_sym - tcod.event.K_1
            if choice_index < len(current_node.choices):
                action = self.dialogue_manager.select_choice(choice_index)

                if action == DialogueAction.END or action == DialogueAction.TRADE:
                    from pyrogue.ui.screens.game_screen import GameScreen

                    return GameScreen(self.engine)
                if action == DialogueAction.CONTINUE:
                    self.selected_choice = 0

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

        # 現在のノードを取得
        current_node = self.dialogue_manager.get_current_node()
        if not current_node:
            # ノードがない場合はエラーメッセージを表示
            console.print(
                console.width // 2,
                console.height // 2,
                "No dialogue available.",
                alignment=tcod.CENTER,
            )
            return

        # タイトルを表示
        title = f"Conversation with {current_node.speaker}"
        console.print(
            console.width // 2, 2, title, fg=tcod.white, alignment=tcod.CENTER
        )

        # 会話テキストを表示
        self._render_dialogue_text(console, current_node.text, start_y=5)

        # 選択肢を表示
        self._render_choices(console, current_node.choices, start_y=15)

        # 操作方法を表示
        self._render_help(console)

    def _render_dialogue_text(
        self, console: tcod.Console, text: str, start_y: int
    ) -> None:
        """
        会話テキストを描画する。

        Args:
        ----
            console: 描画対象のコンソール
            text: 表示するテキスト
            start_y: 開始Y座標

        """
        # テキストを行に分割
        lines = self._wrap_text(text, self.max_text_width)

        # 各行を描画
        for i, line in enumerate(lines):
            console.print(
                console.width // 2,
                start_y + i,
                line,
                fg=tcod.light_gray,
                alignment=tcod.CENTER,
            )

    def _render_choices(
        self, console: tcod.Console, choices: list, start_y: int
    ) -> None:
        """
        選択肢を描画する。

        Args:
        ----
            console: 描画対象のコンソール
            choices: 選択肢のリスト
            start_y: 開始Y座標

        """
        if not choices:
            return

        # 選択肢のタイトル
        console.print(
            console.width // 2,
            start_y,
            "Choose your response:",
            fg=tcod.white,
            alignment=tcod.CENTER,
        )

        # 各選択肢を描画
        for i, choice in enumerate(choices):
            x = console.width // 2
            y = start_y + 2 + i

            # 選択中の選択肢をハイライト
            if i == self.selected_choice:
                fg_color = tcod.yellow
                prefix = "> "
            else:
                fg_color = tcod.light_gray
                prefix = "  "

            # 選択肢テキストを作成
            choice_text = f"{prefix}{i + 1}. {choice.text}"

            # 選択肢を描画
            console.print(x, y, choice_text, fg=fg_color, alignment=tcod.CENTER)

    def _render_help(self, console: tcod.Console) -> None:
        """
        操作方法を描画する。

        Args:
        ----
            console: 描画対象のコンソール

        """
        help_y = console.height - 4

        help_lines = [
            "Controls:",
            "↑/↓: Navigate choices  Enter: Select  1-9: Quick select",
            "Esc: End conversation",
        ]

        for i, line in enumerate(help_lines):
            console.print(
                console.width // 2,
                help_y + i,
                line,
                fg=tcod.dark_gray,
                alignment=tcod.CENTER,
            )

    def _wrap_text(self, text: str, width: int) -> list[str]:
        """
        テキストを指定された幅で折り返す。

        Args:
        ----
            text: 折り返すテキスト
            width: 最大幅

        Returns:
        -------
            折り返されたテキスト行のリスト

        """
        if len(text) <= width:
            return [text]

        lines = []
        words = text.split()
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= width:
                if current_line:
                    current_line += " "
                current_line += word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines
