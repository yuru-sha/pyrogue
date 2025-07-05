"""Inventory screen module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
import tcod.event
from tcod.console import Console

from pyrogue.entities.items.item import Armor, Food, Potion, Ring, Scroll, Weapon
from pyrogue.ui.screens.screen import Screen

if TYPE_CHECKING:
    from pyrogue.ui.screens.game_screen import GameScreen


class InventoryScreen(Screen):
    """インベントリ画面"""

    def __init__(self, game_screen: GameScreen) -> None:
        self.game_screen = game_screen
        self.selected_index = 0
        self.show_help = True

    def render(self, console: Console) -> None:
        """
        画面を描画

        Args:
            console: 描画対象のコンソール

        """
        # 背景を塗りつぶし
        console.clear()

        # タイトルを描画
        console.print(1, 1, "Inventory", tcod.yellow)

        # インベントリの内容を描画
        for i, item in enumerate(self.game_screen.player.inventory.items):
            # インデックスを文字に変換（0=a, 1=b, ...）
            index_char = chr(ord("a") + i)

            # 選択中のアイテムはハイライト
            fg = tcod.white if i != self.selected_index else tcod.yellow

            # アイテム情報を表示
            item_text = f"{index_char}) {item.name}"
            if item.stackable and item.stack_count > 1:
                item_text += f" (x{item.stack_count})"
            console.print(2, 3 + i, item_text, fg)

        # 装備情報を表示
        equipped = self.game_screen.player.inventory.equipped
        console.print(40, 3, "Equipment:", tcod.yellow)
        console.print(
            42,
            5,
            f"Weapon: {equipped['weapon'].name if equipped['weapon'] else 'None'}",
        )
        console.print(
            42, 6, f"Armor: {equipped['armor'].name if equipped['armor'] else 'None'}"
        )
        console.print(
            42,
            7,
            f"Ring(L): {equipped['ring_left'].name if equipped['ring_left'] else 'None'}",
        )
        console.print(
            42,
            8,
            f"Ring(R): {equipped['ring_right'].name if equipped['ring_right'] else 'None'}",
        )

        # ヘルプを表示
        if self.show_help:
            help_text = [
                "Commands:",
                "[a-z] Select item",
                "[e] Equip selected item",
                "[u] Use selected item",
                "[d] Drop selected item",
                "[r] Remove equipment",
                "[ESC] Close inventory",
                "[?] Toggle help",
            ]
            for i, text in enumerate(help_text):
                console.print(2, console.height - 10 + i, text, tcod.gray)

    def handle_key(self, key: tcod.event.KeyDown) -> Screen | None:
        """
        キー入力を処理

        Args:
            key: キー入力イベント

        Returns:
            Optional[Screen]: 次の画面（Noneの場合は現在の画面を維持）

        """
        # ESCでインベントリを閉じる
        if key.sym == tcod.event.KeySym.ESCAPE:
            return self.game_screen

        # ?でヘルプの表示/非表示を切り替え
        if key.sym == tcod.event.KeySym.QUESTION:
            self.show_help = not self.show_help
            return None

        # アイテムの選択（a-z）
        if tcod.event.KeySym.A <= key.sym <= tcod.event.KeySym.Z:
            index = key.sym - tcod.event.KeySym.A
            if index < len(self.game_screen.player.inventory.items):
                self.selected_index = index
            return None

        # 選択中のアイテムに対する操作
        selected_item = self.game_screen.player.inventory.get_item(self.selected_index)
        if not selected_item:
            return None

        # e: 装備
        if key.sym == tcod.event.KeySym.E:
            if isinstance(selected_item, (Weapon, Armor, Ring)):
                old_item = self.game_screen.player.equip_item(selected_item)
                if old_item:
                    self.game_screen.message_log.append(
                        f"You unequip the {old_item.name} and equip the {selected_item.name}."
                    )
                else:
                    self.game_screen.message_log.append(
                        f"You equip the {selected_item.name}."
                    )
            else:
                self.game_screen.message_log.append(
                    f"You cannot equip the {selected_item.name}."
                )

        # u: 使用
        elif key.sym == tcod.event.KeySym.U:
            if isinstance(selected_item, (Scroll, Potion, Food)):
                if self.game_screen.player.use_item(selected_item):
                    self.game_screen.message_log.append(
                        f"You use the {selected_item.name}."
                    )
                else:
                    self.game_screen.message_log.append(
                        f"You cannot use the {selected_item.name}."
                    )
            else:
                self.game_screen.message_log.append(
                    f"You cannot use the {selected_item.name}."
                )

        # d: ドロップ
        elif key.sym == tcod.event.KeySym.D:
            # ドロップできるかチェック
            if self._can_drop_item_at(
                self.game_screen.player_x, self.game_screen.player_y
            ):
                # プレイヤーの位置にアイテムを配置
                selected_item.x = self.game_screen.player_x
                selected_item.y = self.game_screen.player_y

                # アイテムを地面に追加
                if self.game_screen.item_spawner.add_item(selected_item):
                    self.game_screen.inventory.remove_item(selected_item)
                    drop_message = selected_item.drop()
                    self.game_screen.message_log.append(drop_message)

                    # 選択インデックスを調整
                    if self.selected_index >= len(self.game_screen.inventory.items):
                        self.selected_index = max(
                            0, len(self.game_screen.inventory.items) - 1
                        )
                else:
                    self.game_screen.message_log.append(
                        "You cannot drop items here. Something is blocking the way."
                    )
            else:
                self.game_screen.message_log.append(
                    "You cannot drop items here. There is already an item or obstacle."
                )

        # r: 装備を外す
        elif key.sym == tcod.event.KeySym.R:
            # 装備スロットを選択するサブメニューを表示
            return EquipmentRemovalScreen(self)

        return None

    def _can_drop_item_at(self, x: int, y: int) -> bool:
        """
        指定された位置にアイテムをドロップできるかチェック

        Args:
            x: X座標
            y: Y座標

        Returns:
            bool: ドロップ可能な場合はTrue

        """
        # 既にアイテムが存在するかチェック
        if self.game_screen.item_spawner.get_item_at(x, y) is not None:
            return False

        # 地面がフロアタイルかチェック（壁や扉には置けない）
        if (
            self.game_screen.dungeon_tiles
            and 0 <= y < len(self.game_screen.dungeon_tiles)
            and 0 <= x < len(self.game_screen.dungeon_tiles[0])
        ):
            from pyrogue.map.tile import Floor

            tile = self.game_screen.dungeon_tiles[y][x]
            return isinstance(tile, Floor)

        return False


class EquipmentRemovalScreen(Screen):
    """装備解除画面"""

    def __init__(self, inventory_screen: InventoryScreen) -> None:
        self.inventory_screen = inventory_screen
        self.game_screen = inventory_screen.game_screen

    def render(self, console: Console) -> None:
        """
        画面を描画

        Args:
            console: 描画対象のコンソール

        """
        # インベントリ画面を描画
        self.inventory_screen.render(console)

        # 装備解除メニューを描画
        menu_text = [
            "Remove which equipment?",
            "[w] Weapon",
            "[a] Armor",
            "[l] Left ring",
            "[r] Right ring",
            "[ESC] Cancel",
        ]

        for i, text in enumerate(menu_text):
            console.print(30, 15 + i, text, tcod.white)

    def handle_key(self, key: tcod.event.KeyDown) -> Screen | None:
        """
        キー入力を処理

        Args:
            key: キー入力イベント

        Returns:
            Optional[Screen]: 次の画面（Noneの場合は現在の画面を維持）

        """
        if key.sym == tcod.event.KeySym.ESCAPE:
            return self.inventory_screen

        slot = None
        if key.sym == tcod.event.KeySym.W:
            slot = "weapon"
        elif key.sym == tcod.event.KeySym.A:
            slot = "armor"
        elif key.sym == tcod.event.KeySym.L:
            slot = "ring_left"
        elif key.sym == tcod.event.KeySym.R:
            slot = "ring_right"

        if slot:
            item = self.game_screen.player.unequip_item(slot)
            if item:
                self.game_screen.message_log.append(f"You unequip the {item.name}.")
            else:
                self.game_screen.message_log.append(
                    "You have nothing equipped in that slot."
                )
            return self.inventory_screen

        return None
