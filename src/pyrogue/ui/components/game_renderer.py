"""
ゲームレンダラーコンポーネント。

このモジュールは、GameScreen から分離された描画処理を担当します。
マップ、ステータス、メッセージログなどの描画を一元管理します。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import random
import tcod
import tcod.console

from pyrogue.map.tile import Floor, StairsDown, StairsUp, Wall, SecretDoor

if TYPE_CHECKING:
    from pyrogue.ui.screens.game_screen import GameScreen


class GameRenderer:
    """
    ゲーム画面の描画処理を担当するクラス。

    GameScreenから描画処理を分離し、単一の責務を持つように設計されています。
    マップ、ステータス、メッセージログなどの描画を管理します。

    Attributes:
        game_screen: メインのゲームスクリーンへの参照

    """

    def __init__(self, game_screen: GameScreen) -> None:
        """
        レンダラーを初期化。

        Args:
            game_screen: メインのゲームスクリーンインスタンス

        """
        self.game_screen = game_screen

    def render(self, console: tcod.Console) -> None:
        """
        メインの描画処理。

        Args:
            console: TCODコンソール

        """
        console.clear()

        # 各要素を描画
        self._render_map(console)
        self._render_status(console)
        self._render_messages(console)

    def _render_map(self, console: tcod.Console) -> None:
        """
        マップの描画処理。

        Args:
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

                if visible or explored:
                    # タイルの描画（Y座標をオフセット）
                    self._render_tile(console, x, y + map_offset_y, tile, visible)

                    # アイテムの描画
                    if visible:
                        self._render_items_at(console, x, y, floor_data, map_offset_y)

                        # モンスターの描画
                        self._render_monsters_at(console, x, y, floor_data, map_offset_y)

                        # NPCの描画
                        self._render_npcs_at(console, x, y, floor_data, map_offset_y)

        # プレイヤーの描画（Y座標をオフセット）
        player = game_screen.player
        if player:
            console.print(player.x, player.y + map_offset_y, "@", fg=(255, 255, 255))

    def _render_tile(self, console: tcod.Console, x: int, y: int, tile: object, visible: bool) -> None:
        """
        タイルの描画処理。

        Args:
            console: TCODコンソール
            x: X座標
            y: Y座標
            tile: タイルオブジェクト
            visible: 現在視界内かどうか

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
            char = tile.char
            color = tile.light if visible else tile.dark
        else:
            char = "?"
            color = (255, 0, 255) if visible else (128, 0, 128)

        console.print(x, y, char, fg=color)

    def _render_items_at(self, console: tcod.Console, x: int, y: int, floor_data, map_offset_y: int) -> None:
        """
        指定座標のアイテムを描画。

        Args:
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
            console: TCODコンソール

        """
        player = self.game_screen.player
        if not player:
            return

        # ステータス情報の描画位置（画面上部）
        status_y = 0

        # 1行目: レベル、HP、MP、攻撃力、防御力、空腹度、経験値、所持金
        mp_display = ""
        if hasattr(player, "mp") and hasattr(player, "max_mp"):
            mp_display = f"MP:{player.mp}/{player.max_mp} "

        status_line1 = (
            f"Lv:{player.level} "
            f"HP:{player.hp}/{player.max_hp} "
            f"{mp_display}"
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
            fg=(255, 255, 255)
        )

        # ステータス異常は必要に応じて別途表示（元の実装では基本2行のみ）

    def _render_messages(self, console: tcod.Console) -> None:
        """
        メッセージログの描画。

        Args:
            console: TCODコンソール

        """
        messages = self.game_screen.game_logic.message_log
        if not messages:
            return

        # メッセージ表示エリアの設定
        message_y_start = self.game_screen.dungeon_height + 4
        max_messages = 3  # 最大3つのメッセージを表示

        # 最新のメッセージから表示
        recent_messages = messages[-max_messages:]
        for i, message in enumerate(recent_messages):
            console.print(0, message_y_start + i, message, fg=(255, 255, 255))

    def _render_npcs_at(self, console: tcod.Console, x: int, y: int, floor_data, map_offset_y: int) -> None:
        """
        指定した位置にいるNPCを描画。

        Args:
            console: TCODコンソール
            x: 描画位置のX座標
            y: 描画位置のY座標
            floor_data: 現在のフロアデータ
            map_offset_y: マップのYオフセット

        """
        if not hasattr(floor_data, "npc_spawner"):
            return

        npc = floor_data.npc_spawner.get_npc_at_position(x, y)
        if npc:
            console.print(x, y + map_offset_y, npc.char, fg=npc.color)

    def _get_hallucination_char(self) -> str:
        """
        幻覚状態でランダムな文字を返す。

        Returns:
            str: ランダムな文字
        """
        chars = ['?', '!', '@', '#', '$', '%', '^', '&', '*', '+', '=', '~']
        return random.choice(chars)

    def _get_hallucination_color(self) -> tuple[int, int, int]:
        """
        幻覚状態でランダムな色を返す。

        Returns:
            tuple[int, int, int]: RGB色値
        """
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
