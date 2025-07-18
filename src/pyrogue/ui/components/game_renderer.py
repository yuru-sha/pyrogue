"""
ゲームレンダラーコンポーネント。

このモジュールは、GameScreen から分離された描画処理を担当します。
マップ、ステータス、メッセージログなどの描画を一元管理します。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import tcod
import tcod.console

from pyrogue.map.tile import Floor, StairsDown, StairsUp, Wall

if TYPE_CHECKING:
    from pyrogue.ui.screens.game_screen import GameScreen


class GameRenderer:
    """
    ゲーム画面の描画処理を担当するクラス。

    GameScreenから描画処理を分離し、単一の責務を持つように設計されています。
    マップ、ステータス、メッセージログなどの描画を管理します。

    Attributes
    ----------
        game_screen: メインのゲームスクリーンへの参照

    """

    def __init__(self, game_screen: GameScreen) -> None:
        """
        レンダラーを初期化。

        Args:
        ----
            game_screen: メインのゲームスクリーンインスタンス

        """
        self.game_screen = game_screen

    def render(self, console: tcod.Console) -> None:
        """
        メインの描画処理。

        Args:
        ----
            console: TCODコンソール

        """
        console.clear()

        # 各要素を描画
        self._render_map(console)
        self._render_status(console)
        self._render_messages(console)
        self._render_command_hints(console)

    def _render_map(self, console: tcod.Console) -> None:
        """
        マップの描画処理。

        Args:
        ----
            console: TCODコンソール

        """
        game_screen = self.game_screen
        floor_data = game_screen.game_logic.get_current_floor_data()

        if not floor_data or not floor_data.tiles.size:
            return

        # ステータス行の分だけマップをオフセット（2行分）
        map_offset_y = 2

        for y in range(floor_data.tiles.shape[0]):
            for x in range(floor_data.tiles.shape[1]):
                tile = floor_data.tiles[y, x]
                visible = game_screen.fov_manager.visible[y, x]
                explored = game_screen.game_logic.get_explored_tiles()[y, x]

                # ウィザードモード時は全マップを表示
                wizard_mode = game_screen.game_logic.is_wizard_mode()
                should_render = visible or explored or wizard_mode

                if should_render:
                    # タイルの描画（Y座標をオフセット）
                    self._render_tile(console, x, y + map_offset_y, tile, visible, wizard_mode)

                    # アイテムの描画（ウィザードモード時は全て表示）
                    if visible or wizard_mode:
                        self._render_items_at(console, x, y, floor_data, map_offset_y)

                        # モンスターの描画
                        self._render_monsters_at(console, x, y, floor_data, map_offset_y)

                        # ウィザードモード時: トラップの描画
                        if wizard_mode:
                            self._render_traps_at(console, x, y, floor_data, map_offset_y)

        # プレイヤーの描画（Y座標をオフセット）
        player = game_screen.player
        if player:
            console.print(player.x, player.y + map_offset_y, "@", fg=(255, 255, 255))

    def _render_tile(
        self,
        console: tcod.Console,
        x: int,
        y: int,
        tile: object,
        visible: bool,
        wizard_mode: bool = False,
    ) -> None:
        """
        タイルの描画処理。

        Args:
        ----
            console: TCODコンソール
            x: X座標
            y: Y座標
            tile: タイルオブジェクト
            visible: 現在視界内かどうか
            wizard_mode: ウィザードモード有効かどうか

        """
        if isinstance(tile, Wall):
            char = "#"
            color = (130, 110, 50) if visible else (0, 0, 100)  # 元の色設定に戻す
        elif isinstance(tile, Floor):
            char = "."
            color = (192, 192, 192) if visible else (64, 64, 64)  # 元の色設定に戻す
        elif isinstance(tile, StairsDown):
            char = ">"
            color = (255, 255, 255) if visible else (128, 128, 128)
        elif isinstance(tile, StairsUp):
            char = "<"
            color = (255, 255, 255) if visible else (128, 128, 128)
        elif hasattr(tile, "char"):  # Door, SecretDoor等のタイル
            from pyrogue.map.tile import SecretDoor

            if isinstance(tile, SecretDoor) and wizard_mode and tile.door_state == "secret":
                # ウィザードモード時の隠しドア表示（紫色で強調）
                char = "S"  # Secret doorの頭文字
                color = (255, 0, 255) if visible else (128, 0, 128)  # マゼンタ
            else:
                char = tile.char
                color = tile.light if visible else tile.dark
        else:
            char = "?"
            color = (255, 0, 255) if visible else (128, 0, 128)

        # 座標範囲チェック付きの安全な描画
        try:
            if 0 <= x < console.width and 0 <= y < console.height:
                console.print(x, y, char, fg=color)
        except Exception as e:
            # 描画エラーを記録（ゲームを継続）
            print(f"Warning: Drawing error at ({x}, {y}): {e}")

    def _render_traps_at(self, console: tcod.Console, x: int, y: int, floor_data, map_offset_y: int) -> None:
        """
        ウィザードモード時の指定座標のトラップを描画。

        Args:
        ----
            console: TCODコンソール
            x: X座標
            y: Y座標
            floor_data: フロアデータ
            map_offset_y: マップのYオフセット

        """
        if hasattr(floor_data, "trap_spawner") and floor_data.trap_spawner:
            for trap in floor_data.trap_spawner.traps:
                if trap.x == x and trap.y == y:
                    # トラップタイプに応じた色分け
                    if trap.name == "Pit Trap":
                        color = (139, 69, 19)  # 茶色
                        char = "P"
                    elif trap.name == "Poison Needle Trap":
                        color = (0, 255, 0)  # 緑色
                        char = "N"
                    elif trap.name == "Teleport Trap":
                        color = (255, 0, 255)  # マゼンタ
                        char = "T"
                    else:
                        color = (255, 255, 0)  # 黄色（汎用）
                        char = "^"

                    # 隠しトラップは薄い色で表示
                    if trap.is_hidden:
                        color = (color[0] // 2, color[1] // 2, color[2] // 2)  # 色を半分に

                    console.print(x, y + map_offset_y, char, fg=color)
                    break  # 1つの座標に複数トラップがある場合は最初のもののみ表示

    def _render_items_at(self, console: tcod.Console, x: int, y: int, floor_data, map_offset_y: int) -> None:
        """
        指定座標のアイテムを描画。

        Args:
        ----
            console: TCODコンソール
            x: X座標（マップ座標）
            y: Y座標（マップ座標）
            floor_data: フロアデータ
            map_offset_y: マップのYオフセット

        """
        items_at_pos = [item for item in floor_data.item_spawner.items if item.x == x and item.y == y]
        if items_at_pos:
            item = items_at_pos[0]  # 最初のアイテムを描画
            console.print(x, y + map_offset_y, item.char, fg=item.color)

    def _render_monsters_at(self, console: tcod.Console, x: int, y: int, floor_data, map_offset_y: int) -> None:
        """
        指定座標のモンスターを描画。

        Args:
        ----
            console: TCODコンソール
            x: X座標（マップ座標）
            y: Y座標（マップ座標）
            floor_data: フロアデータ
            map_offset_y: マップのYオフセット

        """
        monster = floor_data.monster_spawner.get_monster_at(x, y)
        if monster:
            console.print(x, y + map_offset_y, monster.char, fg=monster.color)

    def _render_status(self, console: tcod.Console) -> None:
        """
        ステータス情報の描画。

        Args:
        ----
            console: TCODコンソール

        """
        player = self.game_screen.player
        if not player:
            return

        # ステータス情報の描画位置（画面上部）
        status_y = 0

        # 1行目: レベル、HP、攻撃力、防御力、空腹度、経験値、所持金
        status_line1 = (
            f"Lv:{player.level} "
            f"HP:{player.hp}/{player.max_hp} "
            f"Atk:{player.get_attack()} "
            f"Def:{player.get_defense()} "
            f"Hunger:{player.hunger}% "
            f"Exp:{player.exp} "
            f"Gold:{player.gold}"
        )

        # 2行目: 装備情報（元の形式に合わせる - 右手/左手表記付き）
        inventory = self.game_screen.game_logic.inventory
        weapon = inventory.equipped["weapon"]
        armor = inventory.equipped["armor"]
        ring_left = inventory.equipped["ring_left"]
        ring_right = inventory.equipped["ring_right"]

        # 各装備の表示形式
        weapon_display = weapon.name if weapon else "None"
        armor_display = armor.name if armor else "None"
        ring_l_display = ring_left.name if ring_left else "None"
        ring_r_display = ring_right.name if ring_right else "None"

        status_line2 = (
            f"Weapon: {weapon_display}  "
            f"Armor: {armor_display}  "
            f"Ring: (L): {ring_l_display}  "
            f"Ring: (R): {ring_r_display}"
        )

        # 地下階層番号を右上に表示
        floor_info = f"B{self.game_screen.game_logic.dungeon_manager.current_floor}F"

        # ステータス描画
        console.print(x=1, y=status_y, string=status_line1, fg=(255, 255, 255))
        console.print(x=1, y=status_y + 1, string=status_line2, fg=(255, 255, 255))

        # 地下階層番号を右上に表示
        console.print(
            x=console.width - len(floor_info) - 1,
            y=status_y,
            string=floor_info,
            fg=(255, 255, 255),
        )

        # 3行目: ゲーム目標とプログレッション情報
        self._render_game_progress(console, status_y + 2)

        # ステータス異常は必要に応じて別途表示（元の実装では基本2行のみ）

    def _render_game_progress(self, console: tcod.Console, y: int) -> None:
        """
        ゲーム進行状況と目標を表示。

        Args:
        ----
            console: TCODコンソール
            y: 表示Y座標

        """
        player = self.game_screen.player
        current_floor = self.game_screen.game_logic.dungeon_manager.current_floor

        if not player:
            return

        # アミュレット所持状況をチェック
        has_amulet = player.has_amulet

        if has_amulet:
            # アミュレット所持時: 脱出目標表示
            progress_text = f"ESCAPE TO SURFACE! ({current_floor}/26 floors climbed)"
            color = (255, 215, 0)  # 金色
        else:
            # 通常時: 探索目標表示
            if current_floor < 26:
                progress_text = f"Goal: Find Amulet of Yendor on B26F  (Currently: B{current_floor}F / B26F)"
                color = (150, 200, 255)  # 薄青色
            else:
                # B26Fに到達済み
                progress_text = "You have reached B26F! Find the Amulet of Yendor!"
                color = (255, 255, 100)  # 黄色

        # 画面幅に収まるように調整
        if len(progress_text) > console.width - 2:
            progress_text = progress_text[: console.width - 5] + "..."

        console.print(
            x=1,
            y=y,
            string=progress_text,
            fg=color,
        )

    def _render_messages(self, console: tcod.Console) -> None:
        """
        メッセージログの描画。

        Args:
        ----
            console: TCODコンソール

        """
        try:
            # 安全な参照アクセス
            if not hasattr(self.game_screen, "game_logic") or not self.game_screen.game_logic:
                return

            messages = self.game_screen.game_logic.message_log
            if not messages:
                return

            # メッセージ表示エリアの設定
            message_y = self.game_screen.dungeon_height + 2
            max_messages = 7  # 最大7つのメッセージを表示

            # 最新のメッセージから表示
            recent_messages = messages[-max_messages:]
            for i, message in enumerate(recent_messages):
                try:
                    # 安全な文字列処理
                    safe_message = str(message)[:80]  # 長すぎるメッセージを切り詰め
                    console.print(0, message_y + i, safe_message, fg=(255, 255, 255))
                except Exception as msg_error:
                    # 個別メッセージの描画エラー
                    console.print(0, message_y + i, f"[Message error: {msg_error}]", fg=(255, 100, 100))
        except Exception as e:
            # 全体的なエラーのフォールバック
            try:
                message_y = self.game_screen.dungeon_height + 2
                console.print(0, message_y, f"Message system error: {e}", fg=(255, 0, 0))
            except Exception:
                # 最後の手段：何もしない（クラッシュを避ける）
                pass

    def _get_hallucination_char(self) -> str:
        """
        幻覚状態でランダムな文字を返す。

        Returns
        -------
            str: ランダムな文字

        """
        chars = ["?", "!", "@", "#", "$", "%", "^", "&", "*", "+", "=", "~"]
        return random.choice(chars)

    def _get_hallucination_color(self) -> tuple[int, int, int]:
        """
        幻覚状態でランダムな色を返す。

        Returns
        -------
            tuple[int, int, int]: RGB色値

        """
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def _render_command_hints(self, console: tcod.Console) -> None:
        """
        重要なコマンドのヒント表示。

        初心者プレイヤー向けに画面下部にコマンドヒントを表示します。

        Args:
        ----
            console: TCODコンソール

        """
        game_screen = self.game_screen
        player = game_screen.player

        if not player:
            return

        # プレイヤーのレベルが低い場合（レベル3以下）のみヒントを表示
        if player.level > 3:
            return

        # 画面下部にヒント表示
        hint_y = console.height - 1

        # 基本的なヒント（状況に応じて動的に変更）
        hints = []

        # アイテムが足元にある場合
        floor_data = game_screen.game_logic.get_current_floor_data()
        if floor_data and floor_data.items:
            items_at_player = [item for item in floor_data.items if item.x == player.x and item.y == player.y]
            if items_at_player:
                hints.append("Press ',' to pick up items")

        # インベントリが満杯でない場合の基本ヒント
        if len(hints) == 0:
            if player.level == 1:
                hints = ["hjkl/arrows: move  ?: help  i: inventory  o/c: doors"]
            elif player.level == 2:
                hints = ["s: search  ,: pick up  Ctrl+S: save  ?: detailed help"]
            else:  # level 3
                hints = ["Goal: Find Amulet of Yendor on B26F  ?: help anytime"]

        if hints:
            hint_text = hints[0]
            # 画面幅に収まるように調整
            if len(hint_text) > console.width - 2:
                hint_text = hint_text[: console.width - 5] + "..."

            # 中央に表示
            x = (console.width - len(hint_text)) // 2
            console.print(
                x,
                hint_y,
                hint_text,
                fg=(100, 150, 100),  # 薄緑色
            )
