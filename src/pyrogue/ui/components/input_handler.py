"""
入力処理コンポーネント。

このモジュールは、GameScreen から分離された入力処理を担当します。
キーボード入力の解釈、コマンドの実行、ターゲット選択モードの管理を行います。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.event

from pyrogue.core.game_states import GameStates

if TYPE_CHECKING:
    from pyrogue.ui.screens.game_screen import GameScreen


class InputHandler:
    """
    入力処理システムの管理クラス。

    キーボード入力の解釈、コマンドの実行、ターゲット選択モードの管理を担当します。

    Attributes
    ----------
        game_screen: メインのゲームスクリーンへの参照
        targeting_mode: ターゲット選択モード状態
        targeting_x: ターゲット選択時のX座標
        targeting_y: ターゲット選択時のY座標

    """

    def __init__(self, game_screen: GameScreen) -> None:
        """
        入力ハンドラーを初期化。

        Args:
        ----
            game_screen: メインのゲームスクリーンインスタンス

        """
        self.game_screen = game_screen
        self.targeting_mode = False
        self.targeting_x = 0
        self.targeting_y = 0

    def handle_key(self, event: tcod.event.KeyDown) -> None:
        """
        キー入力を処理。

        Args:
        ----
            event: TCODキーイベント

        """
        if self.targeting_mode:
            self._handle_targeting_key(event)
        else:
            self._handle_normal_key(event)

    def _handle_normal_key(self, event: tcod.event.KeyDown) -> None:
        """
        通常モードのキー入力を処理。

        Args:
        ----
            event: TCODキーイベント

        """
        key = event.sym
        mod = event.mod
        # TCOD 19.0.0+ では unicode の代わりに text 属性を使用
        unicode_char = getattr(event, 'text', getattr(event, 'unicode', ''))

        # 移動コマンド（Vi-keys + 矢印キー + テンキー）
        movement_keys = {
            # Vi-keys
            ord("h"): (-1, 0),  # 左
            ord("j"): (0, 1),  # 下
            ord("k"): (0, -1),  # 上
            ord("l"): (1, 0),  # 右
            ord("y"): (-1, -1),  # 左上
            ord("u"): (1, -1),  # 右上
            ord("b"): (-1, 1),  # 左下
            ord("n"): (1, 1),  # 右下
            # 矢印キー
            tcod.event.KeySym.LEFT: (-1, 0),
            tcod.event.KeySym.RIGHT: (1, 0),
            tcod.event.KeySym.UP: (0, -1),
            tcod.event.KeySym.DOWN: (0, 1),
            # テンキー
            tcod.event.KeySym.KP_4: (-1, 0),  # 左
            tcod.event.KeySym.KP_6: (1, 0),  # 右
            tcod.event.KeySym.KP_8: (0, -1),  # 上
            tcod.event.KeySym.KP_2: (0, 1),  # 下
            tcod.event.KeySym.KP_7: (-1, -1),  # 左上
            tcod.event.KeySym.KP_9: (1, -1),  # 右上
            tcod.event.KeySym.KP_1: (-1, 1),  # 左下
            tcod.event.KeySym.KP_3: (1, 1),  # 右下
        }

        # 移動処理
        if key in movement_keys:
            dx, dy = movement_keys[key]
            self.game_screen.game_logic.handle_player_move(dx, dy)
            return

        # アクションコマンド
        if key == ord("g"):
            # アイテム取得
            self.game_screen.game_logic.handle_get_item()

        elif key == ord("i"):
            # インベントリ画面
            if self.game_screen.engine:
                self.game_screen.engine.state = GameStates.SHOW_INVENTORY

        elif key == ord("z"):
            # 魔法画面
            if self.game_screen.engine:
                self.game_screen.engine.state = GameStates.SHOW_MAGIC

        elif key == tcod.event.KeySym.TAB:
            # FOV切り替え
            message = self.game_screen.fov_manager.toggle_fov()
            self.game_screen.game_logic.add_message(message)

        elif key == ord("o"):
            # ドア開放
            self._handle_door_action(True)

        elif key == ord("c"):
            # ドア閉鎖
            self._handle_door_action(False)

        elif key == ord("d"):
            # トラップ解除
            self._handle_disarm_action()

        elif (
            key == tcod.event.KeySym.PERIOD and mod & tcod.event.Modifier.SHIFT
        ) or unicode_char == ">" or key == tcod.event.KeySym.GREATER:
            # 階段（下り） - Shift + . または > （JIS配列対応）
            self.game_screen.game_logic.descend_stairs()

        elif (
            key == tcod.event.KeySym.COMMA and mod & tcod.event.Modifier.SHIFT
        ) or unicode_char == "<" or key == tcod.event.KeySym.LESS:
            # 階段（上り） - Shift + , または < （JIS配列対応）
            self.game_screen.game_logic.ascend_stairs()

        # セーブ・ロード（Ctrlキーの組み合わせを先にチェック）
        elif key == ord("s") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+S でセーブ
            self.game_screen.save_load_manager.save_game()

        elif key == ord("l") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+L でロード
            self.game_screen.save_load_manager.load_game()

        elif key == ord("s"):
            # 隠しドア探索（Ctrlが押されていない場合のみ）
            self._handle_search_action()

        elif key == ord("t"):
            # NPCとの対話
            self._handle_talk_action()

        # ゲーム終了
        elif key == tcod.event.KeySym.ESCAPE:
            if self.game_screen.engine:
                self.game_screen.engine.state = GameStates.MENU

    def _handle_targeting_key(self, event: tcod.event.KeyDown) -> None:
        """
        ターゲット選択モードのキー入力を処理。

        Args:
        ----
            event: TCODキーイベント

        """
        key = event.sym

        # ターゲット移動
        if key == tcod.event.KeySym.LEFT or key == ord("h"):
            self.targeting_x = max(0, self.targeting_x - 1)
        elif key == tcod.event.KeySym.RIGHT or key == ord("l"):
            self.targeting_x = min(
                self.game_screen.dungeon_width - 1, self.targeting_x + 1
            )
        elif key == tcod.event.KeySym.UP or key == ord("k"):
            self.targeting_y = max(0, self.targeting_y - 1)
        elif key == tcod.event.KeySym.DOWN or key == ord("j"):
            self.targeting_y = min(
                self.game_screen.dungeon_height - 1, self.targeting_y + 1
            )

        # ターゲット確定
        elif key == tcod.event.KeySym.RETURN:
            self._confirm_target()

        # ターゲット選択キャンセル
        elif key == tcod.event.KeySym.ESCAPE:
            self._cancel_targeting()

    def _handle_door_action(self, open_door: bool) -> None:
        """
        ドアの開閉処理。

        Args:
        ----
            open_door: True=開く、False=閉じる

        """
        player = self.game_screen.player
        if not player:
            return

        # プレイヤーの周囲8方向をチェック
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                x, y = player.x + dx, player.y + dy
                if open_door:
                    if self.game_screen.game_logic.open_door(x, y):
                        return
                elif self.game_screen.game_logic.close_door(x, y):
                    return

        action = "open" if open_door else "close"
        self.game_screen.game_logic.add_message(f"No door to {action} nearby.")

    def _handle_search_action(self) -> None:
        """
        隠しドア探索処理。
        """
        player = self.game_screen.player
        if not player:
            return

        found_secret = False
        # プレイヤーの周囲8方向をチェック
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                x, y = player.x + dx, player.y + dy
                if self.game_screen.game_logic.search_secret_door(x, y):
                    found_secret = True

        if not found_secret:
            self.game_screen.game_logic.add_message("You search but find nothing.")

    def _handle_disarm_action(self) -> None:
        """
        トラップ解除処理。
        """
        player = self.game_screen.player
        if not player:
            return

        # プレイヤーの位置と周囲をチェック
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                x, y = player.x + dx, player.y + dy
                if self.game_screen.game_logic.disarm_trap(x, y):
                    return

        self.game_screen.game_logic.add_message("No trap to disarm nearby.")

    def start_targeting(self, start_x: int = None, start_y: int = None) -> None:
        """
        ターゲット選択モードを開始。

        Args:
        ----
            start_x: 開始X座標（未指定の場合はプレイヤー位置）
            start_y: 開始Y座標（未指定の場合はプレイヤー位置）

        """
        self.targeting_mode = True

        if start_x is not None and start_y is not None:
            self.targeting_x = start_x
            self.targeting_y = start_y
        else:
            player = self.game_screen.player
            if player:
                self.targeting_x = player.x
                self.targeting_y = player.y
            else:
                self.targeting_x = 0
                self.targeting_y = 0

    def _confirm_target(self) -> None:
        """
        ターゲット選択を確定。
        """
        self.targeting_mode = False
        # ターゲット座標をゲームロジックに通知
        self.game_screen.game_logic.handle_target_selection(
            self.targeting_x, self.targeting_y
        )

    def _cancel_targeting(self) -> None:
        """
        ターゲット選択をキャンセル。
        """
        self.targeting_mode = False
        self.game_screen.game_logic.add_message("Targeting cancelled.")

    def get_targeting_info(self) -> tuple[bool, int, int]:
        """
        ターゲット選択の情報を取得。

        Returns
        -------
            (ターゲット選択中か, X座標, Y座標)

        """
        return self.targeting_mode, self.targeting_x, self.targeting_y

    def _handle_talk_action(self) -> None:
        """
        NPCとの対話処理。

        プレイヤーの周囲8方向をチェックし、NPCがいる場合は対話を開始する。
        """
        # NPCシステムの有効性をチェック
        from pyrogue.constants import FeatureConstants

        if not FeatureConstants.ENABLE_NPC_SYSTEM:
            self.game_screen.game_logic.add_message(
                "NPCs are not available in this version."
            )
            return

        player = self.game_screen.player
        if not player:
            return

        # プレイヤーの周囲8方向をチェック
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                target_x = player.x + dx
                target_y = player.y + dy

                # NPCがいるかチェック
                npc = self.game_screen.game_logic.get_npc_at(target_x, target_y)
                if npc:
                    # NPCとの対話を開始
                    self._start_dialogue_with_npc(npc)
                    return

        # 周囲にNPCがいない場合
        self.game_screen.game_logic.add_message("There is no one to talk to.")

    def _start_dialogue_with_npc(self, npc) -> None:
        """
        NPCとの対話を開始。

        Args:
        ----
            npc: 対話するNPC

        """
        if not self.game_screen.engine:
            return

        # NPCの対話IDを取得
        dialogue_id = getattr(npc, "dialogue_id", "default")

        # 対話画面に遷移
        from pyrogue.ui.screens.dialogue_screen import DialogueScreen

        dialogue_screen = DialogueScreen(
            self.game_screen.engine,
            self.game_screen.engine.dialogue_manager,
            dialogue_id,
        )

        # 対話画面を設定
        self.game_screen.engine.dialogue_screen = dialogue_screen
        self.game_screen.engine.state = GameStates.DIALOGUE

        # 対話開始メッセージ
        self.game_screen.game_logic.add_message(f"You talk to {npc.name}.")
