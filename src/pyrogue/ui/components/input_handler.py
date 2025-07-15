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
        unicode_char = getattr(event, "text", getattr(event, "unicode", ""))

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

        # 移動処理（Ctrl修飾子が押されていない場合のみ）
        if key in movement_keys and not (mod & tcod.event.Modifier.CTRL):
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
            # ワンドを振る（方向選択）
            self._handle_zap_wand_action()

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
            (key == tcod.event.KeySym.PERIOD and mod & tcod.event.Modifier.SHIFT)
            or unicode_char == ">"
            or key == tcod.event.KeySym.GREATER
        ):
            # 階段（下り） - Shift + . または > （JIS配列対応）
            self.game_screen.game_logic.descend_stairs()

        elif (
            (key == tcod.event.KeySym.COMMA and mod & tcod.event.Modifier.SHIFT)
            or unicode_char == "<"
            or key == tcod.event.KeySym.LESS
        ):
            # 階段（上り） - Shift + , または < （JIS配列対応）
            self.game_screen.game_logic.ascend_stairs()

        # セーブ・ロード（Ctrlキーの組み合わせを先にチェック）
        elif key == ord("s") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+S でセーブ - CommonCommandHandler経由で統一処理
            self._handle_save_command()

        elif key == ord("l") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+L でロード - CommonCommandHandler経由で統一処理
            self._handle_load_command()

        elif key == ord("w") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+W でウィザードモード切り替え
            self.game_screen.game_logic.toggle_wizard_mode()

        # ウィザードモード専用コマンド
        elif key == ord("t") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+T で階段にテレポート
            self.game_screen.game_logic.wizard_teleport_to_stairs()

        elif key == ord("u") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+U でレベルアップ
            self.game_screen.game_logic.wizard_level_up()

        elif key == ord("h") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+H で完全回復
            self.game_screen.game_logic.wizard_heal_full()

        elif key == ord("r") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+R で全マップ探索
            self.game_screen.game_logic.wizard_reveal_all()

        elif key == ord("s"):
            # 隠しドア探索（Ctrlが押されていない場合のみ）
            self._handle_search_action()

        elif key == ord("t"):
            # 投げるコマンド
            self._handle_throw_action()

        elif (
            key == tcod.event.KeySym.QUESTION
            or key == tcod.event.KeySym.SLASH
            or unicode_char == "?"
            or unicode_char == "/"
        ):
            # ヘルプ表示（JIS配列対応）
            self._handle_help_action()

        elif key == tcod.event.KeySym.PERIOD or unicode_char == ".":
            # 休憩コマンド（ピリオド）
            self._handle_rest_action()

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
            self.targeting_x = min(self.game_screen.dungeon_width - 1, self.targeting_x + 1)
        elif key == tcod.event.KeySym.UP or key == ord("k"):
            self.targeting_y = max(0, self.targeting_y - 1)
        elif key == tcod.event.KeySym.DOWN or key == ord("j"):
            self.targeting_y = min(self.game_screen.dungeon_height - 1, self.targeting_y + 1)

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
        隠しドア・トラップ探索処理。
        """
        player = self.game_screen.player
        if not player:
            return

        found_secret = False
        found_trap = False

        # プレイヤーの周囲8方向をチェック
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                x, y = player.x + dx, player.y + dy
                # 隠しドア探索
                if self.game_screen.game_logic.search_secret_door(x, y):
                    found_secret = True
                # トラップ探索
                if self.game_screen.game_logic.search_trap(x, y):
                    found_trap = True

        if not found_secret and not found_trap:
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

    def start_targeting(self, start_x: int | None = None, start_y: int | None = None) -> None:
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
        self.game_screen.game_logic.handle_target_selection(self.targeting_x, self.targeting_y)

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

    def _handle_throw_action(self) -> None:
        """
        投げるコマンド処理。

        アイテムを投擲して遠距離攻撃を行う。
        """
        # TODO: 投げるコマンドの実装
        self.game_screen.game_logic.add_message("Throw command not yet implemented.")
        # 将来的にはここで以下の処理を行う：
        # 1. インベントリから投擲可能アイテムを選択
        # 2. 投擲方向を選択
        # 3. 軌道計算とダメージ処理
        # 4. アイテムの消費または回収処理

    def _handle_help_action(self) -> None:
        """
        ヘルプ表示処理。
        
        メインゲーム画面で使用可能な全コマンドの一覧を表示します。
        """
        help_text = """
=== PyRogue Help ===

Movement:
  hjkl, yubn  - Vi-style movement (8 directions)
  Arrow keys  - Standard movement
  Numpad 1-9  - Numeric movement

Actions:
  g  - Get item at your feet
  i  - Open inventory
  o  - Open door
  c  - Close door
  s  - Search for hidden doors/traps
  d  - Disarm trap
  t  - Throw item
  z  - Zap a wand in a direction
  .  - Rest for one turn
  >  - Go down stairs
  <  - Go up stairs

Information:
  Tab - Toggle FOV display
  ?   - Show this help

System:
  Ctrl+S - Save game
  Ctrl+L - Load game
  Ctrl+W - Toggle wizard mode (debug)
  ESC    - Return to menu

Wizard Mode (Debug):
  Ctrl+T - Teleport to stairs
  Ctrl+U - Level up
  Ctrl+H - Heal fully
  Ctrl+R - Reveal all map

Press any key to continue...
        """
        
        self.game_screen.game_logic.add_message(help_text.strip())

    def _handle_rest_action(self) -> None:
        """
        休憩コマンド処理。
        
        その場で1ターン休憩し、時間を経過させます。
        - HP/MP自然回復
        - 飢餓進行
        - 状態異常進行
        - 敵のターン処理
        """
        player = self.game_screen.player
        if not player:
            return

        # プレイヤーが死亡している場合は休憩できない
        if player.hp <= 0:
            self.game_screen.game_logic.add_message("You cannot rest while dead.")
            return

        # 休憩メッセージ
        self.game_screen.game_logic.add_message("You rest for a moment.")
        
        # ターン経過処理
        # GameLogicのターン管理メソッドを使用
        if hasattr(self.game_screen.game_logic, 'handle_turn_end'):
            self.game_screen.game_logic.handle_turn_end()
        else:
            # 古いバージョンとの互換性のため、直接処理
            self._process_rest_turn()

    def _process_rest_turn(self) -> None:
        """
        休憩時のターン処理（フォールバック実装）。
        """
        player = self.game_screen.player
        
        # HP自然回復（満腹時）
        if hasattr(player, 'hunger') and player.hunger >= 80:  # 満腹時
            if player.hp < player.max_hp:
                player.hp = min(player.max_hp, player.hp + 1)
                
        # MP自然回復（満腹時）
        if hasattr(player, 'mp') and hasattr(player, 'max_mp') and hasattr(player, 'hunger'):
            if player.hunger >= 80 and player.mp < player.max_mp:
                player.mp = min(player.max_mp, player.mp + 1)
        
        # 飢餓進行
        if hasattr(player, 'consume_food'):
            player.consume_food(1)  # 1ポイント消費
            
        # 状態異常進行
        if hasattr(player, 'status_effects'):
            for effect in list(player.status_effects):
                effect.update()
                if effect.duration <= 0:
                    player.status_effects.remove(effect)

    def _handle_save_command(self) -> None:
        """
        セーブコマンドを CommonCommandHandler 経由で処理。
        """
        from pyrogue.core.command_handler import CommonCommandHandler, GUICommandContext
        
        # GUI用のCommandContextを作成
        context = GUICommandContext(self.game_screen)
        
        # CommonCommandHandlerを使用してセーブ処理を実行
        command_handler = CommonCommandHandler(context)
        result = command_handler.handle_command("save")
        
        # 結果に基づいて追加処理は不要（メッセージはすでに表示済み）

    def _handle_load_command(self) -> None:
        """
        ロードコマンドを CommonCommandHandler 経由で処理。
        """
        from pyrogue.core.command_handler import CommonCommandHandler, GUICommandContext
        
        # GUI用のCommandContextを作成
        context = GUICommandContext(self.game_screen)
        
        # CommonCommandHandlerを使用してロード処理を実行
        command_handler = CommonCommandHandler(context)
        result = command_handler.handle_command("load")
        
        # ロード成功時にFOVを更新
        if result.success:
            self.game_screen.fov_manager.update_fov()

    def _handle_zap_wand_action(self) -> None:
        """
        ワンド使用処理（方向選択）。
        
        プレイヤーが所持するワンドを使用し、方向を選択して発動する。
        オリジナルRogue準拠のワンドシステム。
        """
        # TODO: ワンドシステムの実装
        self.game_screen.game_logic.add_message("Zap wand command not yet implemented.")
        # 将来的にはここで以下の処理を行う：
        # 1. インベントリからワンドを選択
        # 2. 方向選択
        # 3. ワンド効果の発動
        # 4. チャージ消費処理
