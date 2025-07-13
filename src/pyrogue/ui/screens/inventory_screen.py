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
        super().__init__(game_screen.engine)
        self.game_screen = game_screen
        self.selected_index = 0
        self.show_help = False

    def render(self, console: Console) -> None:
        """
        画面を描画

        Args:
        ----
            console: 描画対象のコンソール

        """
        # 背景を塗りつぶし
        console.clear()

        # タイトルを描画
        console.print(1, 1, "Inventory", tcod.yellow)

        # インベントリの内容を描画
        for i, item in enumerate(self.game_screen.game_logic.inventory.items):
            # インデックスを文字に変換（0=a, 1=b, ...）
            index_char = chr(ord("a") + i)

            # 選択中のアイテムはハイライト
            fg = tcod.white if i != self.selected_index else tcod.yellow

            # アイテム情報を表示（識別システムを使用）
            player = self.game_screen.game_logic.player
            display_name = item.get_display_name(player.identification)
            item_text = f"{index_char}) {display_name}"
            if item.stackable and item.stack_count > 1:
                item_text += f" (x{item.stack_count})"

            # 装備状態を表示
            equipped = self.game_screen.game_logic.inventory.equipped
            if (
                (isinstance(item, Weapon) and equipped["weapon"] == item)
                or (isinstance(item, Armor) and equipped["armor"] == item)
                or (
                    isinstance(item, Ring)
                    and (
                        equipped["ring_left"] == item or equipped["ring_right"] == item
                    )
                )
            ):
                item_text += " (equipped)"
                fg = tcod.green if i != self.selected_index else tcod.yellow

            console.print(2, 3 + i, item_text, fg)

        # 装備情報を表示
        equipped = self.game_screen.game_logic.inventory.equipped
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
                "[↑/↓] Select item",
                "[e] Equip selected item",
                "[u] Use selected item",
                "[d] Drop selected item",
                "[r] Remove equipment",
                "[ESC] Close inventory",
                "[?] Toggle help",
            ]
            for i, text in enumerate(help_text):
                console.print(2, console.height - 10 + i, text, tcod.gray)

    def handle_input(self, event: tcod.event.KeyDown) -> None:
        """
        インベントリ画面のキー入力を処理。

        Args:
        ----
            event: キーボードイベント

        """
        from pyrogue.core.game_states import GameStates

        # ESCでインベントリを閉じる
        if event.sym == tcod.event.KeySym.ESCAPE:
            if self.game_screen.engine:
                self.game_screen.engine.state = GameStates.PLAYERS_TURN
            return

        # ?でヘルプの表示/非表示を切り替え
        # 日本語キーボード対応のため、複数の方法で?キーを検出
        unicode_char = getattr(event, 'text', getattr(event, 'unicode', ''))
        if (
            event.sym == tcod.event.KeySym.QUESTION
            or event.sym == tcod.event.KeySym.SLASH
            or unicode_char == "?"
            or unicode_char == "/"
        ):
            self.show_help = not self.show_help
            return

        # カーソルキーでアイテム選択
        inventory_size = len(self.game_screen.game_logic.inventory.items)
        if inventory_size > 0:
            if event.sym == tcod.event.KeySym.UP:
                self.selected_index = (self.selected_index - 1) % inventory_size
                return
            elif event.sym == tcod.event.KeySym.DOWN:
                self.selected_index = (self.selected_index + 1) % inventory_size
                return

        # 選択中のアイテムに対する操作
        if len(self.game_screen.game_logic.inventory.items) > 0:
            selected_item = self.game_screen.game_logic.inventory.items[
                self.selected_index
            ]

            # e: 装備
            if event.sym == tcod.event.KeySym.E:
                if isinstance(selected_item, (Weapon, Armor, Ring)):
                    if self.game_screen.game_logic.inventory.equip(selected_item):
                        self.game_screen.game_logic.add_message(
                            f"You equip the {selected_item.name}."
                        )
                    else:
                        self.game_screen.game_logic.add_message(
                            f"You cannot equip the {selected_item.name}."
                        )
                else:
                    self.game_screen.game_logic.add_message(
                        f"You cannot equip the {selected_item.name}."
                    )
                return

            # u: 使用
            if event.sym == tcod.event.KeySym.U:
                if isinstance(selected_item, (Scroll, Potion, Food)):
                    # アイテムを使用
                    player = self.game_screen.game_logic.player
                    success = player.use_item(
                        selected_item, self.game_screen.game_logic
                    )

                    if success:
                        # 使用成功時に識別
                        was_identified = player.identification.identify_item(
                            selected_item.name, selected_item.item_type
                        )

                        if was_identified:
                            msg = player.identification.get_identification_message(
                                selected_item.name, selected_item.item_type
                            )
                            self.game_screen.game_logic.add_message(msg)

                        # 選択インデックスを調整
                        if self.selected_index >= len(
                            self.game_screen.game_logic.inventory.items
                        ):
                            self.selected_index = max(
                                0, len(self.game_screen.game_logic.inventory.items) - 1
                            )
                    else:
                        self.game_screen.game_logic.add_message(
                            f"You cannot use the {selected_item.get_display_name(player.identification)}."
                        )
                else:
                    player = self.game_screen.game_logic.player
                    display_name = selected_item.get_display_name(player.identification)
                    self.game_screen.game_logic.add_message(
                        f"You cannot use the {display_name}."
                    )
                return

            # r: 装備解除
            if event.sym == tcod.event.KeySym.R:
                if isinstance(selected_item, (Weapon, Armor, Ring)):
                    # 装備されているかチェック
                    equipped = self.game_screen.game_logic.inventory.equipped
                    unequipped = False

                    if (
                        isinstance(selected_item, Weapon)
                        and equipped["weapon"] == selected_item
                    ):
                        self.game_screen.game_logic.inventory.unequip("weapon")
                        unequipped = True
                    elif (
                        isinstance(selected_item, Armor)
                        and equipped["armor"] == selected_item
                    ):
                        self.game_screen.game_logic.inventory.unequip("armor")
                        unequipped = True
                    elif isinstance(selected_item, Ring):
                        if equipped["ring_left"] == selected_item:
                            self.game_screen.game_logic.inventory.unequip("ring_left")
                            unequipped = True
                        elif equipped["ring_right"] == selected_item:
                            self.game_screen.game_logic.inventory.unequip("ring_right")
                            unequipped = True

                    if unequipped:
                        self.game_screen.game_logic.add_message(
                            f"You unequip the {selected_item.name}."
                        )
                    else:
                        self.game_screen.game_logic.add_message(
                            f"The {selected_item.name} is not equipped."
                        )
                else:
                    self.game_screen.game_logic.add_message(
                        f"You cannot unequip the {selected_item.name}."
                    )
                return

            # d: ドロップ
            if event.sym == tcod.event.KeySym.D:
                # 呪われた装備中のアイテムかチェック
                if (
                    self.game_screen.game_logic.inventory.is_equipped(selected_item)
                    and hasattr(selected_item, "cursed")
                    and selected_item.cursed
                ):
                    self.game_screen.game_logic.add_message(
                        f"You cannot drop the cursed {selected_item.name}! You must first remove the curse."
                    )
                else:
                    # 装備中のアイテムの場合は先に装備解除メッセージを表示
                    if self.game_screen.game_logic.inventory.is_equipped(selected_item):
                        self.game_screen.game_logic.add_message(
                            f"You first unequip the {selected_item.name}."
                        )

                    # ドロップ処理を実行
                    if self.game_screen.game_logic.drop_item_at(
                        selected_item,
                        self.game_screen.game_logic.player.x,
                        self.game_screen.game_logic.player.y,
                    ):
                        # インベントリからアイテムを削除（remove_itemが装備スロットもクリア）
                        self.game_screen.game_logic.inventory.remove_item(selected_item)
                        self.game_screen.game_logic.add_message(
                            f"You drop the {selected_item.name}."
                        )

                        # 選択インデックスを調整
                        if self.selected_index >= len(
                            self.game_screen.game_logic.inventory.items
                        ):
                            self.selected_index = max(
                                0, len(self.game_screen.game_logic.inventory.items) - 1
                            )
                    else:
                        self.game_screen.game_logic.add_message(
                            "You cannot drop items here."
                        )
                return
