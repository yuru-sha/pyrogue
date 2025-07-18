"""
入力処理コンポーネント。

このモジュールは、GameScreen から分離された入力処理を担当します。
キーボード入力の解釈、コマンドの実行、ターゲット選択モードの管理を行います。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.event

from pyrogue.core.command_handler import CommonCommandHandler, GUICommandContext
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
        self.wand_direction_mode = False
        self.selected_wand = None

        # CommonCommandHandlerを初期化
        self.command_context = GUICommandContext(game_screen)
        self.command_handler = CommonCommandHandler(self.command_context)

    def handle_key(self, event: tcod.event.KeyDown) -> GameStates | None:
        """
        キー入力を処理。

        Args:
        ----
            event: TCODキーイベント

        Returns:
        -------
            新しいゲーム状態、またはNone
        """
        if self.targeting_mode:
            self._handle_targeting_key(event)
        elif self.wand_direction_mode:
            self._handle_wand_direction_key(event)
        else:
            return self._handle_normal_key(event)
        return None

    def _handle_normal_key(self, event: tcod.event.KeyDown) -> GameStates | None:
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

        # JIS配列キー入力デバッグ用ログ（開発時のみ、環境変数で制御）
        from pyrogue.config.env import is_debug_mode

        if is_debug_mode() and hasattr(self.game_screen, "game_logic") and self.game_screen.game_logic:
            # KeySymの実際の値を確認
            sym_name = str(key)
            if hasattr(tcod.event.KeySym, "QUESTION"):
                question_sym = tcod.event.KeySym.QUESTION
                slash_sym = tcod.event.KeySym.SLASH
                debug_msg = f"Key: sym={sym_name}({key}), mod={mod}, unicode='{unicode_char}', char_code={ord(unicode_char) if unicode_char else 'None'}, QUESTION={question_sym}, SLASH={slash_sym}"
            else:
                debug_msg = f"Key: sym={sym_name}({key}), mod={mod}, unicode='{unicode_char}', char_code={ord(unicode_char) if unicode_char else 'None'}"

            self.game_screen.game_logic.add_message(f"DEBUG: {debug_msg}")

            # ログファイルにも記録
            import logging

            logging.getLogger("pyrogue").debug(f"Key input: {debug_msg}")

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

            # Shift修飾子が押されている場合は走る
            if mod & tcod.event.Modifier.SHIFT:
                self._handle_run_action(dx, dy)
            else:
                self.game_screen.game_logic.handle_player_move(dx, dy)
            return None

        # 特殊キー（JIS配列対応のため最優先で処理）
        if (
            key == tcod.event.KeySym.QUESTION
            or unicode_char == "?"
            or (key == tcod.event.KeySym.SLASH and mod & tcod.event.Modifier.SHIFT)
            or key == ord("?")  # 追加の安全策
        ):
            # ヘルプ表示（JIS配列対応・最優先処理）
            return self._handle_help_action()

        # アクションコマンド（大文字小文字順）
        if key == ord("a"):
            # 最後のコマンドを繰り返す (repeat last command)
            self._handle_repeat_last_command_action()
            return None

        elif key == ord("c"):
            # ドア閉鎖
            self._handle_door_action(False)
            return None

        elif key == ord("d"):
            # トラップ解除
            self._handle_disarm_action()
            return None

        elif key == ord("e"):
            # 食べる (eat food)
            self._handle_eat_action()
            return None

        elif key == ord(",") or key == tcod.event.KeySym.COMMA:
            # アイテム取得 (オリジナルローグ準拠)
            self.game_screen.game_logic.handle_get_item()
            return None

        elif key == ord("i"):
            # インベントリ画面
            if self.game_screen.engine:
                return GameStates.SHOW_INVENTORY
            return None

        elif key == ord("o"):
            # ドア開放
            self._handle_door_action(True)
            return None

        elif key == ord("q"):
            # ポーションを飲む (quaff potion)
            self._handle_quaff_action()
            return None

        elif key == ord("Q"):
            # ポーションを飲む（大文字Q）- オリジナルRogue準拠
            self._handle_quaff_action()
            return None

        elif key == ord("r") and not (mod & tcod.event.Modifier.CTRL):
            # 巻物を読む (read scroll) - r (Ctrl+Rではない場合のみ)
            self._handle_read_action()
            return None

        elif key == ord("s") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+S でセーブ - CommonCommandHandler経由で統一処理
            self._handle_save_command()
            return None

        elif key == ord("s") and not (mod & tcod.event.Modifier.CTRL):
            # 隠しドア探索 - s (Ctrl+Sではない場合のみ)
            self._handle_search_action()
            return None

        elif key == ord("t") and not (mod & tcod.event.Modifier.CTRL):
            # 投げる (throw) - t (Ctrl+Tではない場合のみ)
            self._handle_throw_action()
            return None

        elif key == tcod.event.KeySym.PLUS or (key == tcod.event.KeySym.EQUALS and mod & tcod.event.Modifier.SHIFT):
            # 投げる (throw) - +
            self._handle_throw_action()
            return None

        elif key == ord("w") and not (mod & tcod.event.Modifier.CTRL):
            # 武器を装備 (wield weapon) - w (Ctrl+Wではない場合のみ)
            self._handle_wield_action()
            return None

        elif key == ord("z") or (key == tcod.event.KeySym.MINUS and not (mod & tcod.event.Modifier.SHIFT)):
            # ワンドを振る (zap wand) - z または -
            self._handle_zap_wand_action()
            return None

        elif key == ord("D"):
            # 発見済みアイテムリスト (list discovered items)
            self._handle_list_discovered_items_action()
            return None

        elif key == ord("P"):
            # 指輪を装着 (put on ring)
            self._handle_put_on_ring_action()
            return None

        elif key == ord("R"):
            # 指輪を外す (remove ring)
            self._handle_remove_ring_action()
            return None

        elif key == ord("W"):
            # 防具を装備 (wear armor)
            self._handle_wear_action()
            return None

        elif key == tcod.event.KeySym.TAB:
            # FOV切り替え
            message = self.game_screen.fov_manager.toggle_fov()
            self.game_screen.game_logic.add_message(message)
            return None

        elif (
            (key == tcod.event.KeySym.PERIOD and mod & tcod.event.Modifier.SHIFT)
            or unicode_char == ">"
            or key == tcod.event.KeySym.GREATER
        ):
            # 階段（下り） - Shift + . または > （JIS配列対応）
            self.game_screen.game_logic.descend_stairs()
            return None

        elif (
            (key == tcod.event.KeySym.COMMA and mod & tcod.event.Modifier.SHIFT)
            or unicode_char == "<"
            or key == tcod.event.KeySym.LESS
        ):
            # 階段（上り） - Shift + , または < （JIS配列対応）
            self.game_screen.game_logic.ascend_stairs()
            return None

        # セーブ・ロード（Ctrlキーの組み合わせを先にチェック）

        elif key == ord("l") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+L でロード - CommonCommandHandler経由で統一処理
            self._handle_load_command()
            return None

        elif key == ord("w") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+W でウィザードモード切り替え
            self.game_screen.game_logic.toggle_wizard_mode()
            return None

        # ウィザードモード専用コマンド
        elif key == ord("t") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+T で階段にテレポート
            self.game_screen.game_logic.wizard_teleport_to_stairs()
            return None

        elif key == ord("u") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+U でレベルアップ
            self.game_screen.game_logic.wizard_level_up()
            return None

        elif key == ord("h") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+H で完全回復
            self.game_screen.game_logic.wizard_heal_full()
            return None

        elif key == ord("r") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+R で全マップ探索
            self.game_screen.game_logic.wizard_reveal_all()
            return None

        elif key == ord("m") and mod & tcod.event.Modifier.CTRL:
            # Ctrl+M で最後のメッセージ表示（CommonCommandHandler経由）
            result = self.command_handler.handle_command("last_message")
            return None

        # xキーは削除（オリジナルRogueには存在しない）

        elif (key == tcod.event.KeySym.SLASH and not (mod & tcod.event.Modifier.SHIFT)) or (
            unicode_char == "/" and not (mod & tcod.event.Modifier.SHIFT)
        ):
            # シンボル説明（専用画面に遷移・Shift未押下時のみ）
            if self.game_screen.engine:
                return GameStates.SYMBOL_EXPLANATION
            else:
                # エンジンがない場合のフォールバック
                self.game_screen.game_logic.add_message("Symbol explanation not available")
                return None

        elif key == tcod.event.KeySym.PERIOD or unicode_char == ".":
            # 休憩コマンド（ピリオド・CommonCommandHandler経由）
            result = self.command_handler.handle_command("rest")
            if result.should_end_turn:
                self.game_screen.game_logic.handle_turn_end()
            return None

        # ゲーム終了
        elif key == tcod.event.KeySym.ESCAPE:
            if self.game_screen.engine:
                return GameStates.MENU
            return None

        return None

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
        player = self.game_screen.game_logic.player
        inventory = self.game_screen.game_logic.inventory

        # 投擲可能なアイテムを検索
        throwable_items = []
        for item in inventory.items:
            # 武器、ポーション、食料は投擲可能
            if hasattr(item, "attack") or hasattr(item, "effect") or item.name.lower().find("food") != -1:
                throwable_items.append(item)

        if not throwable_items:
            self.game_screen.game_logic.add_message("You have nothing to throw.")
            return

        # 最初の投擲可能アイテムを選択（簡単な実装）
        item_to_throw = throwable_items[0]

        # 8方向から投擲方向を選択（北を選択）
        directions = [
            (-1, -1),
            (0, -1),
            (1, -1),  # 左上、上、右上
            (-1, 0),
            (1, 0),  # 左、右
            (-1, 1),
            (0, 1),
            (1, 1),  # 左下、下、右下
        ]

        # 北方向（上）に投擲
        dx, dy = directions[1]  # (0, -1)
        target_x = player.x + dx
        target_y = player.y + dy

        # 投擲処理
        dungeon = self.game_screen.game_logic.dungeon

        # 範囲チェック
        if not (0 <= target_x < dungeon.width and 0 <= target_y < dungeon.height):
            self.game_screen.game_logic.add_message("You can't throw in that direction.")
            return

        # 投擲実行
        inventory.remove_item(item_to_throw)

        # ダメージ計算
        damage = 1
        if hasattr(item_to_throw, "attack"):
            damage = item_to_throw.attack

        # 投擲先にモンスターがいるかチェック
        target_monster = None
        for monster in dungeon.monsters:
            if monster.x == target_x and monster.y == target_y:
                target_monster = monster
                break

        if target_monster:
            # モンスターに命中
            actual_damage = max(1, damage - target_monster.defense)
            target_monster.hp -= actual_damage

            display_name = item_to_throw.get_display_name(player.identification)
            self.game_screen.game_logic.add_message(
                f"You throw the {display_name} at the {target_monster.name} for {actual_damage} damage!"
            )

            # モンスターが死亡したかチェック
            if target_monster.hp <= 0:
                self.game_screen.game_logic.add_message(f"The {target_monster.name} dies!")
                dungeon.monsters.remove(target_monster)
                player.exp += target_monster.exp
                player.kill_count += 1

                # レベルアップチェック
                if player.exp >= player.exp_to_next_level:
                    player.level_up()
                    self.game_screen.game_logic.add_message(f"Welcome to level {player.level}!")
        else:
            # 何もない場所に投擲
            display_name = item_to_throw.get_display_name(player.identification)
            self.game_screen.game_logic.add_message(f"You throw the {display_name}. It falls to the ground.")

            # アイテムを地面に配置
            self.game_screen.game_logic.drop_item_at(item_to_throw, target_x, target_y)

        # ターン消費
        self.game_screen.game_logic.handle_turn_end()

    def _handle_auto_explore_action(self) -> None:
        """
        自動探索コマンド処理。

        未探索エリアを自動的に探索し、敵発見時は停止します。
        """
        player = self.game_screen.game_logic.player
        dungeon = self.game_screen.game_logic.dungeon

        # 敵が近くにいるかチェック
        for monster in dungeon.monsters:
            dx = abs(monster.x - player.x)
            dy = abs(monster.y - player.y)
            if dx <= 3 and dy <= 3:  # 3マス以内に敵がいる
                self.game_screen.game_logic.add_message("You sense danger nearby. Auto-explore stopped.")
                return

        # 未探索エリアを探索（簡単な実装）
        # 8方向をチェックして、最初の歩ける場所に移動
        directions = [
            (-1, -1),
            (0, -1),
            (1, -1),  # 左上、上、右上
            (-1, 0),
            (1, 0),  # 左、右
            (-1, 1),
            (0, 1),
            (1, 1),  # 左下、下、右下
        ]

        for dx, dy in directions:
            new_x = player.x + dx
            new_y = player.y + dy

            # 境界チェック
            if 0 <= new_x < dungeon.width and 0 <= new_y < dungeon.height:
                tile = dungeon.tiles[new_y][new_x]
                if tile.walkable:
                    # 移動可能な場所を発見
                    self.game_screen.game_logic.handle_player_move(dx, dy)
                    return

        # 移動できる場所がない
        self.game_screen.game_logic.add_message("No unexplored areas found nearby.")

    def _handle_look_action(self) -> None:
        """
        足元・周囲調査コマンド処理。

        プレイヤーの足元と周囲8マスの詳細情報を表示します。
        """
        player = self.game_screen.game_logic.player
        dungeon = self.game_screen.game_logic.dungeon

        look_text = "\n=== Look Around ===\n"

        # プレイヤーの足元をチェック
        look_text += f"\nAt your feet ({player.x}, {player.y}):\n"

        # 足元のアイテムをチェック
        items_at_feet = []
        for item in dungeon.items:
            if item.x == player.x and item.y == player.y:
                items_at_feet.append(item)

        if items_at_feet:
            for item in items_at_feet:
                display_name = item.get_display_name(player.identification)
                look_text += f"  {display_name}\n"
        else:
            look_text += "  Nothing special.\n"

        # 周囲8マスをチェック
        look_text += "\nSurrounding areas:\n"

        directions = [
            (-1, -1, "Northwest"),
            (0, -1, "North"),
            (1, -1, "Northeast"),
            (-1, 0, "West"),
            (1, 0, "East"),
            (-1, 1, "Southwest"),
            (0, 1, "South"),
            (1, 1, "Southeast"),
        ]

        for dx, dy, direction in directions:
            new_x = player.x + dx
            new_y = player.y + dy

            # 境界チェック
            if 0 <= new_x < dungeon.width and 0 <= new_y < dungeon.height:
                tile = dungeon.tiles[new_y][new_x]

                # 地形情報
                terrain_info = ""
                if tile.walkable:
                    terrain_info = "floor"
                else:
                    terrain_info = "wall"

                # モンスターをチェック
                monster_at_pos = None
                for monster in dungeon.monsters:
                    if monster.x == new_x and monster.y == new_y:
                        monster_at_pos = monster
                        break

                if monster_at_pos:
                    look_text += f"  {direction}: {monster_at_pos.name} on {terrain_info}\n"
                else:
                    # アイテムをチェック
                    item_at_pos = None
                    for item in dungeon.items:
                        if item.x == new_x and item.y == new_y:
                            item_at_pos = item
                            break

                    if item_at_pos:
                        display_name = item_at_pos.get_display_name(player.identification)
                        look_text += f"  {direction}: {display_name} on {terrain_info}\n"
                    else:
                        look_text += f"  {direction}: {terrain_info}\n"
            else:
                look_text += f"  {direction}: out of bounds\n"

        look_text += "\nPress any key to continue..."

        self.game_screen.game_logic.add_message(look_text.strip())

    def _handle_help_action(self) -> GameStates | None:
        """
        ヘルプ表示処理。

        メニューのヘルプ画面に遷移します。
        """
        # ゲーム状態をヘルプメニューに変更
        if self.game_screen.engine:
            return GameStates.HELP_MENU
        else:
            # エンジンがない場合のフォールバック
            self.game_screen.game_logic.add_message("Help screen not available")
            return None

    def _handle_symbol_explanation_action(self) -> None:
        """
        シンボル説明表示処理。

        ゲーム内で使用される各シンボルの意味を説明します。
        """
        symbol_text = """
=== PyRogue Symbol Guide ===

Terrain:
  .  - Floor (walkable ground)
  #  - Wall (blocks movement and vision)
  +  - Closed door (can be opened with 'o')
  /  - Open door (can be closed with 'c')
  <  - Stairs up (ascend with '<')
  >  - Stairs down (descend with '>')
  ^  - Trap (can be disarmed with 'd')

Items:
  $  - Gold pieces
  !  - Potion (quaff with 'u' in inventory)
  ?  - Scroll (read with 'u' in inventory)
  )  - Weapon (equip with 'e' in inventory)
  [  - Armor (equip with 'e' in inventory)
  =  - Ring (equip with 'e' in inventory)
  %  - Food (eat with 'u' in inventory)
  /  - Wand (zap with 'z' command)
  *  - Amulet of Yendor (victory item!)

Creatures:
  @  - You (the player)

Monsters (A-Z):
  A  - Aquator          N  - Nymph
  B  - Bat              O  - Orc
  C  - Centaur          P  - Phantom
  D  - Dragon           Q  - Quagga
  E  - Emu              R  - Rattlesnake
  F  - Venus Flytrap    S  - Snake
  G  - Griffin          T  - Troll
  H  - Hobgoblin        U  - Ur-Vile
  I  - Ice Monster      V  - Vampire
  J  - Jabberwock       W  - Wraith
  K  - Kestrel          X  - Xeroc
  L  - Leprechaun       Y  - Yeti
  M  - Medusa           Z  - Zombie

Special Monsters:
  f  - Phantom Fungus (hallucination inducer)

Press any key to continue...
        """

        self.game_screen.game_logic.add_message(symbol_text.strip())

    def _handle_last_message_action(self) -> None:
        """
        最後のメッセージ表示処理。

        メッセージ履歴から最近のメッセージを表示し、見落としを防ぎます。
        """
        # メッセージ履歴を取得
        messages = self.game_screen.game_logic.get_message_history()

        if not messages:
            self.game_screen.game_logic.add_message("No messages in history.")
            return

        # 最後の10件のメッセージを表示
        recent_messages = messages[-10:]

        history_text = "\n=== Recent Messages ===\n"
        for i, msg in enumerate(recent_messages, 1):
            history_text += f"{i:2d}. {msg}\n"
        history_text += "\nPress any key to continue..."

        self.game_screen.game_logic.add_message(history_text.strip())

    def _handle_identification_status_action(self) -> None:
        """
        アイテム識別状況表示処理。

        発見済みアイテムの識別状況を一覧表示します。
        """
        player = self.game_screen.game_logic.player
        identification = player.identification

        status_text = "\n=== Item Identification Status ===\n"

        # ポーション識別状況
        status_text += "\nPotions:\n"
        potion_types = ["Healing Potion", "Poison Potion", "Strength Potion", "Restore Potion"]
        for potion_type in potion_types:
            if identification.is_discovered(potion_type, "POTION"):
                if identification.is_identified(potion_type, "POTION"):
                    status_text += f"  {potion_type}: Identified\n"
                else:
                    display_name = identification.get_display_name(potion_type, "POTION")
                    status_text += f"  {display_name}: Unknown\n"

        # 巻物識別状況
        status_text += "\nScrolls:\n"
        scroll_types = ["Scroll of Identify", "Scroll of Teleport", "Scroll of Magic Mapping", "Scroll of Light"]
        for scroll_type in scroll_types:
            if identification.is_discovered(scroll_type, "SCROLL"):
                if identification.is_identified(scroll_type, "SCROLL"):
                    status_text += f"  {scroll_type}: Identified\n"
                else:
                    display_name = identification.get_display_name(scroll_type, "SCROLL")
                    status_text += f"  {display_name}: Unknown\n"

        # 指輪識別状況
        status_text += "\nRings:\n"
        ring_types = ["Ring of Strength", "Ring of Defense", "Ring of Regeneration"]
        for ring_type in ring_types:
            if identification.is_discovered(ring_type, "RING"):
                if identification.is_identified(ring_type, "RING"):
                    status_text += f"  {ring_type}: Identified\n"
                else:
                    display_name = identification.get_display_name(ring_type, "RING")
                    status_text += f"  {display_name}: Unknown\n"

        status_text += "\nPress any key to continue..."

        self.game_screen.game_logic.add_message(status_text.strip())

    def _handle_character_details_action(self) -> None:
        """
        キャラクター詳細表示処理。

        プレイヤーのステータス、装備、能力値を詳細表示します。
        """
        player = self.game_screen.game_logic.player
        inventory = self.game_screen.game_logic.inventory

        details_text = "\n=== Character Details ===\n"

        # 基本ステータス
        details_text += f"\nLevel: {player.level}\n"
        details_text += f"Experience: {player.exp}/{player.exp_to_next_level}\n"
        details_text += f"HP: {player.hp}/{player.max_hp}\n"
        details_text += f"Gold: {player.gold}\n"
        details_text += f"Hunger: {player.hunger_status}\n"
        details_text += f"Turn: {player.turn_count}\n"

        # 能力値
        base_attack = player.attack
        base_defense = player.defense
        attack_bonus = inventory.get_attack_bonus()
        defense_bonus = inventory.get_defense_bonus()

        details_text += "\nAttributes:\n"
        details_text += f"  Attack: {base_attack} + {attack_bonus} = {base_attack + attack_bonus}\n"
        details_text += f"  Defense: {base_defense} + {defense_bonus} = {base_defense + defense_bonus}\n"

        # 装備状況
        details_text += "\nEquipment:\n"
        equipped = inventory.equipped

        weapon_name = equipped["weapon"].name if equipped["weapon"] else "None"
        armor_name = equipped["armor"].name if equipped["armor"] else "None"
        ring_left_name = equipped["ring_left"].name if equipped["ring_left"] else "None"
        ring_right_name = equipped["ring_right"].name if equipped["ring_right"] else "None"

        details_text += f"  Weapon: {weapon_name}\n"
        details_text += f"  Armor: {armor_name}\n"
        details_text += f"  Ring (Left): {ring_left_name}\n"
        details_text += f"  Ring (Right): {ring_right_name}\n"

        # 状態異常
        if player.status_effects:
            details_text += "\nStatus Effects:\n"
            for effect in player.status_effects:
                details_text += f"  {effect.name}: {effect.duration} turns\n"

        details_text += "\nPress any key to continue..."

        self.game_screen.game_logic.add_message(details_text.strip())

    def _handle_direct_wear_action(self) -> None:
        """
        直接装備コマンド処理。

        メインゲーム画面から直接装備可能なアイテムを選択・装備します。
        """
        player = self.game_screen.game_logic.player
        inventory = self.game_screen.game_logic.inventory

        # 装備可能なアイテムを検索
        equippable_items = []
        for item in inventory.items:
            if hasattr(item, "attack") or hasattr(item, "defense") or hasattr(item, "effect"):
                equippable_items.append(item)

        if not equippable_items:
            self.game_screen.game_logic.add_message("You have no items to equip.")
            return

        # 簡単な選択UI（最初の装備可能アイテムを装備）
        item_to_equip = equippable_items[0]

        # 装備処理
        if not inventory.is_equipped(item_to_equip):
            old_item = inventory.equip(item_to_equip)
            inventory.remove_item(item_to_equip)

            # 前の装備をインベントリに戻す
            if old_item:
                if inventory.add_item(old_item):
                    self.game_screen.game_logic.add_message(
                        f"You unequip the {old_item.name} and equip the {item_to_equip.name}."
                    )
                # インベントリが満杯の場合は地面にドロップ
                elif self.game_screen.game_logic.drop_item_at(old_item, player.x, player.y):
                    self.game_screen.game_logic.add_message(
                        f"You drop the {old_item.name} and equip the {item_to_equip.name}."
                    )
            else:
                self.game_screen.game_logic.add_message(f"You equip the {item_to_equip.name}.")
        else:
            self.game_screen.game_logic.add_message(f"The {item_to_equip.name} is already equipped.")

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
        if hasattr(self.game_screen.game_logic, "handle_turn_end"):
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
        if hasattr(player, "hunger") and player.hunger >= 80:  # 満腹時
            if player.hp < player.max_hp:
                player.hp = min(player.max_hp, player.hp + 1)

        # 飢餓進行
        if hasattr(player, "consume_food"):
            player.consume_food(1)  # 1ポイント消費

        # 状態異常進行
        if hasattr(player, "status_effects"):
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
        ワンド使用処理（カーソル選択）。

        プレイヤーが所持するワンドを使用し、カーソルで選択して発動する。
        インベントリ画面と統一されたUI。
        """
        wands = self._get_available_wands()

        if not wands:
            self.game_screen.game_logic.add_message("You have no wands to zap.")
            return

        # ワンドが1つだけの場合は自動選択
        if len(wands) == 1:
            self._proceed_with_wand_selection(wands[0])
        else:
            # 複数のワンドがある場合はワンド選択画面を表示
            self._show_wand_selection_screen()

    def _get_available_wands(self) -> list:
        """
        プレイヤーが持っているワンドのリストを取得。

        Returns
        -------
            ワンドのリスト

        """
        player = self.game_screen.player
        return [item for item in player.inventory.items if hasattr(item, "item_type") and item.item_type == "WAND"]

    def _show_wand_selection_screen(self) -> None:
        """
        ワンド選択画面を表示する。
        """
        from pyrogue.ui.screens.wand_selection_screen import WandSelectionScreen

        if self.game_screen.engine:
            wand_screen = WandSelectionScreen(self.game_screen)
            wand_screen.setup()
            self.game_screen.engine.wand_selection_screen = wand_screen
            self.game_screen.engine.last_state = self.game_screen.engine.state
            self.game_screen.engine.state = GameStates.SHOW_WAND_SELECTION

    def _proceed_with_wand_selection(self, selected_wand) -> None:
        """
        選択されたワンドで処理を続行。

        Args:
        ----
            selected_wand: 選択されたワンド

        """
        # チャージをチェック
        if hasattr(selected_wand, "has_charges") and not selected_wand.has_charges():
            self.game_screen.game_logic.add_message(f"The {selected_wand.name} has no charges left.")
            return

        # 方向選択モードに入る
        self.game_screen.game_logic.add_message("Zap wand in which direction?")
        self._start_wand_direction_selection(selected_wand)

    def _start_wand_direction_selection(self, wand) -> None:
        """
        ワンド方向選択モードを開始。

        Args:
        ----
            wand: 使用するワンド

        """
        # 方向選択モードの状態を設定
        self.wand_direction_mode = True
        self.selected_wand = wand

    def _handle_wand_direction_key(self, event) -> None:
        """
        ワンド方向選択のキー処理。

        Args:
        ----
            event: キーイベント

        """
        key = event.sym

        # 方向キーの処理
        direction_keys = {
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

        if key in direction_keys:
            direction = direction_keys[key]
            self._execute_wand_zap(direction)
        elif key == tcod.event.KeySym.ESCAPE:
            # キャンセル
            self.wand_direction_mode = False
            self.selected_wand = None
            self.game_screen.game_logic.add_message("Cancelled.")
        else:
            self.game_screen.game_logic.add_message("Choose a direction (use movement keys).")

    def _execute_wand_zap(self, direction: tuple[int, int]) -> None:
        """
        ワンドの発動処理。

        Args:
        ----
            direction: 発動方向

        """
        if not hasattr(self, "selected_wand") or not self.selected_wand:
            return

        wand = self.selected_wand

        # 方向選択モードを終了
        self.wand_direction_mode = False
        self.selected_wand = None

        # ワンドの効果を適用
        if hasattr(wand, "apply_effect"):
            success = wand.apply_effect(self.game_screen.game_logic, direction)
            if success:
                # 使用メッセージを表示
                if hasattr(wand, "use"):
                    self.game_screen.game_logic.add_message(wand.use())

                # チャージが0になった場合の処理
                if hasattr(wand, "charges") and wand.charges <= 0:
                    self.game_screen.game_logic.add_message(f"The {wand.name} crumbles to dust.")
                    # インベントリから削除
                    if wand in self.game_screen.player.inventory.items:
                        self.game_screen.player.inventory.items.remove(wand)
            else:
                self.game_screen.game_logic.add_message(f"The {wand.name} fails to work.")
        else:
            self.game_screen.game_logic.add_message(f"The {wand.name} is not functional.")

    def _handle_examine_action(self) -> None:
        """
        調査・検査コマンドの処理。

        プレイヤーの足元と隣接する8タイルを調査し、
        アイテム、モンスター、地形の詳細情報を表示する。
        """
        player = self.game_screen.game_logic.player
        dungeon = self.game_screen.game_logic.dungeon

        # 調査結果を格納するリスト
        examination_results = []

        # プレイヤーの足元を調査
        player_tile_info = self._examine_tile(player.x, player.y, dungeon)
        if player_tile_info:
            examination_results.append(f"Here: {player_tile_info}")

        # 隣接する8タイルを調査
        directions = [
            (-1, -1),
            (0, -1),
            (1, -1),  # 上列
            (-1, 0),
            (1, 0),  # 中列
            (-1, 1),
            (0, 1),
            (1, 1),  # 下列
        ]

        for dx, dy in directions:
            x, y = player.x + dx, player.y + dy

            # マップ範囲内かチェック
            if 0 <= x < dungeon.width and 0 <= y < dungeon.height:
                tile_info = self._examine_tile(x, y, dungeon)
                if tile_info:
                    direction_name = self._get_direction_name(dx, dy)
                    examination_results.append(f"{direction_name}: {tile_info}")

        # 結果をメッセージとして表示
        if examination_results:
            self.game_screen.game_logic.add_message("=== Examination Results ===")
            for result in examination_results:
                self.game_screen.game_logic.add_message(result)
        else:
            self.game_screen.game_logic.add_message("Nothing interesting nearby.")

    def _examine_tile(self, x: int, y: int, dungeon) -> str | None:
        """
        指定されたタイルの詳細情報を取得。

        Args:
        ----
            x: X座標
            y: Y座標
            dungeon: ダンジョンインスタンス

        Returns:
        -------
            タイルの詳細情報文字列（何もない場合はNone）

        """
        info_parts = []

        # モンスターをチェック
        monster = dungeon.get_monster_at(x, y)
        if monster:
            info_parts.append(f"Monster: {monster.name} (HP: {monster.hp}/{monster.max_hp})")

        # アイテムをチェック
        items = dungeon.get_items_at(x, y)
        if items:
            player = self.game_screen.game_logic.player
            for item in items:
                display_name = item.get_display_name(player.identification)
                if item.stackable and item.stack_count > 1:
                    info_parts.append(f"Item: {display_name} (x{item.stack_count})")
                else:
                    info_parts.append(f"Item: {display_name}")

        # トラップをチェック
        trap = dungeon.get_trap_at(x, y)
        if trap and trap.discovered:
            info_parts.append(f"Trap: {trap.name} ({'disarmed' if trap.disarmed else 'armed'})")

        # 地形をチェック
        tile = dungeon.get_tile(x, y)
        if tile:
            terrain_info = self._get_terrain_info(tile)
            if terrain_info:
                info_parts.append(f"Terrain: {terrain_info}")

        return "; ".join(info_parts) if info_parts else None

    def _get_direction_name(self, dx: int, dy: int) -> str:
        """
        方向ベクトルから方向名を取得。

        Args:
        ----
            dx: X方向の差分
            dy: Y方向の差分

        Returns:
        -------
            方向名の文字列

        """
        direction_map = {
            (-1, -1): "NW",
            (0, -1): "N",
            (1, -1): "NE",
            (-1, 0): "W",
            (1, 0): "E",
            (-1, 1): "SW",
            (0, 1): "S",
            (1, 1): "SE",
        }
        return direction_map.get((dx, dy), "Unknown")

    def _get_terrain_info(self, tile) -> str | None:
        """
        地形タイルの情報を取得。

        Args:
        ----
            tile: タイルインスタンス

        Returns:
        -------
            地形情報の文字列

        """
        from pyrogue.map.tile import TileType

        if not tile:
            return None

        # タイルタイプによる地形情報
        terrain_descriptions = {
            TileType.FLOOR: "floor",
            TileType.WALL: "wall",
            TileType.DOOR_OPEN: "open door",
            TileType.DOOR_CLOSED: "closed door",
            TileType.DOOR_SECRET: "secret door" if tile.discovered else "wall",
            TileType.STAIRS_UP: "stairs up",
            TileType.STAIRS_DOWN: "stairs down",
            TileType.STAIRS_EXIT: "exit stairs",
        }

        return terrain_descriptions.get(tile.tile_type, "unknown terrain")

    def _handle_long_rest_action(self) -> None:
        """
        長時間休憩コマンドの処理。

        プレイヤーを完全に回復するまで休憩する。
        モンスターが近くにいる場合は休憩できない。
        """
        player = self.game_screen.game_logic.player

        # プレイヤーが既に最大HPの場合
        if player.hp >= player.max_hp:
            self.game_screen.game_logic.add_message("You are already at full health.")
            return

        # 近くにモンスターがいるかチェック
        if self._check_nearby_monsters():
            self.game_screen.game_logic.add_message("You cannot rest with monsters nearby!")
            return

        # 休憩開始メッセージ
        self.game_screen.game_logic.add_message("You begin to rest...")

        # 回復が必要なターン数を計算
        hp_to_recover = player.max_hp - player.hp
        turns_needed = hp_to_recover * 2  # 2ターンで1HP回復

        # 休憩ループ
        turns_rested = 0
        while player.hp < player.max_hp and turns_rested < turns_needed:
            # ターンを進める
            self.game_screen.game_logic.advance_turn()

            # 2ターンごとに1HP回復
            if turns_rested % 2 == 1:
                player.hp = min(player.max_hp, player.hp + 1)

            turns_rested += 1

            # 途中でモンスターが近づいてきたら休憩を中断
            if self._check_nearby_monsters():
                self.game_screen.game_logic.add_message("Your rest is interrupted by a monster!")
                return

            # プレイヤーが死亡した場合は休憩を中断
            if player.hp <= 0:
                return

        # 休憩完了メッセージ
        if player.hp >= player.max_hp:
            self.game_screen.game_logic.add_message(f"You feel fully rested. (Rested for {turns_rested} turns)")
        else:
            self.game_screen.game_logic.add_message(f"You feel somewhat better. (Rested for {turns_rested} turns)")

    def _check_nearby_monsters(self) -> bool:
        """
        プレイヤーの近くにモンスターがいるかチェック。

        Returns
        -------
            近くにモンスターがいる場合True

        """
        player = self.game_screen.game_logic.player
        dungeon = self.game_screen.game_logic.dungeon

        # 視界内のモンスターをチェック
        for monster in dungeon.monsters:
            if monster.hp > 0:  # 生きているモンスターのみ
                distance = abs(monster.x - player.x) + abs(monster.y - player.y)
                if distance <= 10:  # 10タイル以内にモンスターがいる
                    return True
        return False

    def _handle_run_action(self, dx: int, dy: int) -> None:
        """
        走るコマンドの処理。

        指定された方向に障害物にぶつかるまで連続して移動する。
        モンスター、アイテム、ドア、少ないHPなどの場合は停止します。

        Args:
        ----
            dx: X方向の移動量
            dy: Y方向の移動量

        """
        player = self.game_screen.game_logic.player
        dungeon = self.game_screen.game_logic.dungeon

        # 走る前のチェック
        if not self._can_start_running():
            # 通常の移動にフォールバック
            self.game_screen.game_logic.handle_player_move(dx, dy)
            return

        self.game_screen.game_logic.add_message("You start running...")

        steps_taken = 0
        max_steps = 20  # 最大ステップ数制限

        while steps_taken < max_steps:
            next_x = player.x + dx
            next_y = player.y + dy

            # 進行可能かチェック
            if not self._can_continue_running(next_x, next_y):
                break

            # 移動を実行
            if not self.game_screen.game_logic.handle_player_move(dx, dy):
                break

            steps_taken += 1

            # 移動後のチェック
            if not self._can_continue_running_after_move():
                break

            # プレイヤーが死亡した場合は停止
            if player.hp <= 0:
                break

        if steps_taken > 0:
            self.game_screen.game_logic.add_message(f"You stop running. (Ran for {steps_taken} steps)")
        else:
            self.game_screen.game_logic.add_message("You cannot run in that direction.")

    def _can_start_running(self) -> bool:
        """
        走ることができるかチェック。

        Returns
        -------
            走ることができる場合True

        """
        player = self.game_screen.game_logic.player

        # HPが低い場合は走れない
        if player.hp < player.max_hp * 0.3:
            self.game_screen.game_logic.add_message("You are too injured to run.")
            return False

        # 近くにモンスターがいる場合は走れない
        if self._check_nearby_monsters():
            self.game_screen.game_logic.add_message("You cannot run with monsters nearby!")
            return False

        return True

    def _can_continue_running(self, next_x: int, next_y: int) -> bool:
        """
        走り続けることができるかチェック。

        Args:
        ----
            next_x: 次のX座標
            next_y: 次のY座標

        Returns:
        -------
            走り続けることができる場合True

        """
        dungeon = self.game_screen.game_logic.dungeon

        # マップ範囲外の場合は停止
        if not (0 <= next_x < dungeon.width and 0 <= next_y < dungeon.height):
            return False

        # モンスターがいる場合は停止
        if dungeon.get_monster_at(next_x, next_y):
            return False

        # アイテムがある場合は停止
        if dungeon.get_items_at(next_x, next_y):
            return False

        # ドアがある場合は停止
        tile = dungeon.get_tile(next_x, next_y)
        if tile:
            from pyrogue.map.tile import TileType

            if tile.tile_type in (TileType.DOOR_CLOSED, TileType.DOOR_SECRET):
                return False

        return True

    def _can_continue_running_after_move(self) -> bool:
        """
        移動後に走り続けることができるかチェック。

        Returns
        -------
            走り続けることができる場合True

        """
        player = self.game_screen.game_logic.player
        dungeon = self.game_screen.game_logic.dungeon

        # 足元にアイテムがある場合は停止
        if dungeon.get_items_at(player.x, player.y):
            return False

        # 近くにモンスターが現れた場合は停止
        if self._check_nearby_monsters():
            return False

        # HPが低くなった場合は停止
        if player.hp < player.max_hp * 0.3:
            return False

        return True

    def _handle_eat_action(self) -> None:
        """
        食べるコマンド処理 (e キー)。
        インベントリから食料を選択して食べる。
        """
        player = self.game_screen.player
        inventory = self.game_screen.game_logic.inventory

        # 食料アイテムを検索
        food_items = [item for item in inventory.items if hasattr(item, "item_type") and item.item_type == "FOOD"]

        if not food_items:
            self.game_screen.game_logic.add_message("You have no food to eat.")
            return

        # 最初の食料を食べる（簡易実装）
        food = food_items[0]
        result = self.command_handler.handle_command("eat", [food.name])
        if result.should_end_turn:
            self.game_screen.game_logic.handle_turn_end()

    def _handle_quaff_action(self) -> None:
        """
        ポーションを飲むコマンド処理 (q キー)。
        インベントリからポーションを選択して飲む。
        """
        player = self.game_screen.player
        inventory = self.game_screen.game_logic.inventory

        # ポーションアイテムを検索
        potion_items = [item for item in inventory.items if hasattr(item, "item_type") and item.item_type == "POTION"]

        if not potion_items:
            self.game_screen.game_logic.add_message("You have no potions to quaff.")
            return

        # 最初のポーションを飲む（簡易実装）
        potion = potion_items[0]
        result = self.command_handler.handle_command("quaff", [potion.name])
        if result.should_end_turn:
            self.game_screen.game_logic.handle_turn_end()

    def _handle_read_action(self) -> None:
        """
        巻物を読むコマンド処理 (r キー)。
        インベントリから巻物を選択して読む。
        """
        player = self.game_screen.player
        inventory = self.game_screen.game_logic.inventory

        # 巻物アイテムを検索
        scroll_items = [item for item in inventory.items if hasattr(item, "item_type") and item.item_type == "SCROLL"]

        if not scroll_items:
            self.game_screen.game_logic.add_message("You have no scrolls to read.")
            return

        # 最初の巻物を読む（簡易実装）
        scroll = scroll_items[0]
        result = self.command_handler.handle_command("read", [scroll.name])
        if result.should_end_turn:
            self.game_screen.game_logic.handle_turn_end()

    def _handle_wield_action(self) -> None:
        """
        武器を装備するコマンド処理 (w キー)。
        インベントリから武器を選択して装備する。
        """
        player = self.game_screen.player
        inventory = self.game_screen.game_logic.inventory

        # 武器アイテムを検索
        weapon_items = [
            item
            for item in inventory.items
            if hasattr(item, "attack") and hasattr(item, "item_type") and item.item_type == "WEAPON"
        ]

        if not weapon_items:
            self.game_screen.game_logic.add_message("You have no weapons to wield.")
            return

        # 最初の武器を装備（簡易実装）
        weapon = weapon_items[0]
        result = self.command_handler.handle_command("wield", [weapon.name])
        if result.should_end_turn:
            self.game_screen.game_logic.handle_turn_end()

    def _handle_wear_action(self) -> None:
        """
        防具を装備するコマンド処理 (W キー)。
        インベントリから防具を選択して装備する。
        """
        player = self.game_screen.player
        inventory = self.game_screen.game_logic.inventory

        # 防具アイテムを検索
        armor_items = [
            item
            for item in inventory.items
            if hasattr(item, "defense") and hasattr(item, "item_type") and item.item_type == "ARMOR"
        ]

        if not armor_items:
            self.game_screen.game_logic.add_message("You have no armor to wear.")
            return

        # 最初の防具を装備（簡易実装）
        armor = armor_items[0]
        result = self.command_handler.handle_command("wear", [armor.name])
        if result.should_end_turn:
            self.game_screen.game_logic.handle_turn_end()

    def _handle_put_on_ring_action(self) -> None:
        """
        指輪を装着するコマンド処理 (P キー)。
        インベントリから指輪を選択して装着する。
        """
        player = self.game_screen.player
        inventory = self.game_screen.game_logic.inventory

        # 指輪アイテムを検索
        ring_items = [item for item in inventory.items if hasattr(item, "item_type") and item.item_type == "RING"]

        if not ring_items:
            self.game_screen.game_logic.add_message("You have no rings to put on.")
            return

        # 最初の指輪を装着（簡易実装）
        ring = ring_items[0]
        result = self.command_handler.handle_command("put_on", [ring.name])
        if result.should_end_turn:
            self.game_screen.game_logic.handle_turn_end()

    def _handle_remove_ring_action(self) -> None:
        """
        指輪を外すコマンド処理 (R キー)。
        装備中の指輪を選択して外す。
        """
        inventory = self.game_screen.game_logic.inventory
        equipped = inventory.equipped

        # 装備中の指輪をチェック
        if not equipped["ring_left"] and not equipped["ring_right"]:
            self.game_screen.game_logic.add_message("You are not wearing any rings.")
            return

        # 左手の指輪を優先的に外す（簡易実装）
        ring_to_remove = equipped["ring_left"] if equipped["ring_left"] else equipped["ring_right"]
        result = self.command_handler.handle_command("remove", [ring_to_remove.name])
        if result.should_end_turn:
            self.game_screen.game_logic.handle_turn_end()

    def _handle_repeat_last_command_action(self) -> None:
        """
        最後のコマンドを繰り返すコマンド処理 (a キー)。
        """
        # TODO: 最後のコマンドを記録・実行する機能の実装
        self.game_screen.game_logic.add_message("Repeat last command not yet implemented.")

    def _handle_list_discovered_items_action(self) -> None:
        """
        発見済みアイテムリスト表示処理 (D キー)。
        """
        player = self.game_screen.player
        identification = player.identification

        discovered_text = "\n=== Discovered Items ===\n"
        has_discovered = False

        # ポーション
        potion_types = ["Healing Potion", "Poison Potion", "Strength Potion", "Restore Potion"]
        discovered_potions = []
        for potion_type in potion_types:
            if identification.is_discovered(potion_type, "POTION"):
                display_name = identification.get_display_name(potion_type, "POTION")
                if identification.is_identified(potion_type, "POTION"):
                    discovered_potions.append(f"  {display_name} ({potion_type})")
                else:
                    discovered_potions.append(f"  {display_name} (unidentified)")
                has_discovered = True

        if discovered_potions:
            discovered_text += "\nPotions:\n" + "\n".join(discovered_potions) + "\n"

        # 巻物
        scroll_types = ["Scroll of Identify", "Scroll of Teleport", "Scroll of Magic Mapping", "Scroll of Light"]
        discovered_scrolls = []
        for scroll_type in scroll_types:
            if identification.is_discovered(scroll_type, "SCROLL"):
                display_name = identification.get_display_name(scroll_type, "SCROLL")
                if identification.is_identified(scroll_type, "SCROLL"):
                    discovered_scrolls.append(f"  {display_name} ({scroll_type})")
                else:
                    discovered_scrolls.append(f"  {display_name} (unidentified)")
                has_discovered = True

        if discovered_scrolls:
            discovered_text += "\nScrolls:\n" + "\n".join(discovered_scrolls) + "\n"

        # 指輪
        ring_types = ["Ring of Strength", "Ring of Defense", "Ring of Regeneration"]
        discovered_rings = []
        for ring_type in ring_types:
            if identification.is_discovered(ring_type, "RING"):
                display_name = identification.get_display_name(ring_type, "RING")
                if identification.is_identified(ring_type, "RING"):
                    discovered_rings.append(f"  {display_name} ({ring_type})")
                else:
                    discovered_rings.append(f"  {display_name} (unidentified)")
                has_discovered = True

        if discovered_rings:
            discovered_text += "\nRings:\n" + "\n".join(discovered_rings) + "\n"

        if not has_discovered:
            discovered_text = "You have not discovered any items yet."
        else:
            discovered_text += "\nPress any key to continue..."

        self.game_screen.game_logic.add_message(discovered_text.strip())
