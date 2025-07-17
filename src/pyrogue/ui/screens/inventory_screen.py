"""Inventory screen module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
import tcod.event
from tcod.console import Console

from pyrogue.entities.items.item import Armor, Food, Item, Potion, Ring, Scroll, Wand, Weapon
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
        self.unequip_mode = False

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
        console.print(1, 1, "Inventory", (255, 255, 0))

        # インベントリの内容を描画
        for i, item in enumerate(self.game_screen.game_logic.inventory.items):
            # インデックスを文字に変換（0=a, 1=b, ...）
            index_char = chr(ord("a") + i)

            # 選択中のアイテムはハイライト
            fg = (255, 255, 255) if i != self.selected_index else (255, 255, 0)

            # アイテム情報を表示（識別システムを使用）
            player = self.game_screen.game_logic.player
            display_name = item.get_display_name(player.identification)
            item_text = f"{index_char}) {display_name}"
            if item.stackable and item.stack_count > 1:
                item_text += f" (x{item.stack_count})"

            # 装備状態を表示（統一された方法を使用）
            if self.game_screen.game_logic.inventory.is_equipped(item):
                slot = self.game_screen.game_logic.inventory.get_equipped_slot(item)
                if slot == "ring_left":
                    item_text += " (E-L)"
                elif slot == "ring_right":
                    item_text += " (E-R)"
                else:
                    item_text += " (E)"
                fg = (0, 255, 0) if i != self.selected_index else (255, 255, 0)

            console.print(2, 3 + i, item_text, fg)

        # 装備情報を表示
        equipped = self.game_screen.game_logic.inventory.equipped
        player = self.game_screen.game_logic.player
        console.print(40, 3, "Equipment:", (255, 255, 0))

        # 装備品の表示に識別システムを使用（能力値も表示）
        weapon_info = self._get_equipment_info(equipped["weapon"], player.identification)
        armor_info = self._get_equipment_info(equipped["armor"], player.identification)
        ring_left_info = self._get_equipment_info(equipped["ring_left"], player.identification)
        ring_right_info = self._get_equipment_info(equipped["ring_right"], player.identification)

        console.print(42, 5, f"Weapon: {weapon_info}")
        console.print(42, 6, f"Armor: {armor_info}")
        console.print(42, 7, f"Ring(L): {ring_left_info}")
        console.print(42, 8, f"Ring(R): {ring_right_info}")

        # 装備ボーナス情報を表示
        attack_bonus = self.game_screen.game_logic.inventory.get_attack_bonus()
        defense_bonus = self.game_screen.game_logic.inventory.get_defense_bonus()

        console.print(42, 10, f"Attack Bonus: {attack_bonus:+d}")
        console.print(42, 11, f"Defense Bonus: {defense_bonus:+d}")

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
                console.print(2, console.height - 10 + i, text, (127, 127, 127))

    def _get_equipment_info(self, item: Item | None, identification) -> str:
        """
        装備情報を取得して表示用文字列を作成

        Args:
        ----
            item: 装備アイテム
            identification: アイテム識別システム

        Returns:
        -------
            str: 表示用文字列

        """
        if not item:
            return "None"

        display_name = item.get_display_name(identification)

        # 能力値を表示
        if isinstance(item, Weapon):
            attack_value = item.attack + item.enchantment
            if item.enchantment != 0:
                return f"{display_name} (ATK {attack_value:+d})"
            return f"{display_name} (ATK {attack_value})"
        if isinstance(item, Armor):
            defense_value = item.defense + item.enchantment
            if item.enchantment != 0:
                return f"{display_name} (DEF {defense_value:+d})"
            return f"{display_name} (DEF {defense_value})"
        if isinstance(item, Ring):
            if item.effect and item.bonus != 0:
                # 効果名をより読みやすく表示
                effect_display = {
                    "protection": "DEF",
                    "strength": "ATK",
                    "sustain": "SUSTAIN",
                    "search": "SEARCH",
                    "see_invisible": "SEE INV",
                    "regeneration": "REGEN",
                }.get(item.effect, item.effect.upper())
                return f"{display_name} ({effect_display} {item.bonus:+d})"
            return f"{display_name}"
        return display_name

    def handle_input(self, event: tcod.event.KeyDown) -> None:
        """
        インベントリ画面のキー入力を処理。

        Args:
        ----
            event: キーボードイベント

        """
        from pyrogue.core.game_states import GameStates

        # 装備解除モードの場合は専用処理
        if self.unequip_mode:
            self._handle_unequip_selection(event)
            return

        # ESCでインベントリを閉じる
        if event.sym == tcod.event.KeySym.ESCAPE:
            if self.game_screen.engine:
                self.game_screen.engine.state = GameStates.PLAYERS_TURN
            return

        # ?でヘルプの表示/非表示を切り替え
        # 日本語キーボード対応のため、複数の方法で?キーを検出
        unicode_char = getattr(event, "text", getattr(event, "unicode", ""))
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
            if event.sym == tcod.event.KeySym.DOWN:
                self.selected_index = (self.selected_index + 1) % inventory_size
                return

        # 選択中のアイテムに対する操作
        if len(self.game_screen.game_logic.inventory.items) > 0:
            selected_item = self.game_screen.game_logic.inventory.items[self.selected_index]

            # e: 装備
            if event.sym == tcod.event.KeySym.E:
                if isinstance(selected_item, (Weapon, Armor, Ring)):
                    # 既に装備されているかチェック
                    if self.game_screen.game_logic.inventory.is_equipped(selected_item):
                        self.game_screen.game_logic.add_message(f"The {selected_item.name} is already equipped.")
                    else:
                        # player.equip_itemを使用して装備処理を統一
                        old_item = self.game_screen.game_logic.player.equip_item(selected_item)

                        # 前の装備があった場合のメッセージ
                        if old_item:
                            self.game_screen.game_logic.add_message(
                                f"You unequip the {old_item.name} and equip the {selected_item.name}."
                            )
                        else:
                            self.game_screen.game_logic.add_message(f"You equip the {selected_item.name}.")

                        # 選択インデックスを調整（装備したアイテムが削除されるため）
                        if self.selected_index >= len(self.game_screen.game_logic.inventory.items):
                            self.selected_index = max(0, len(self.game_screen.game_logic.inventory.items) - 1)
                else:
                    self.game_screen.game_logic.add_message(f"You cannot equip the {selected_item.name}.")
                return

            # u: 使用
            if event.sym == tcod.event.KeySym.U:
                if isinstance(selected_item, (Scroll, Potion, Food)):
                    # アイテムを使用
                    player = self.game_screen.game_logic.player
                    success = player.use_item(selected_item, self.game_screen)

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
                        if self.selected_index >= len(self.game_screen.game_logic.inventory.items):
                            self.selected_index = max(0, len(self.game_screen.game_logic.inventory.items) - 1)
                    else:
                        self.game_screen.game_logic.add_message(
                            f"You cannot use the {selected_item.get_display_name(player.identification)}."
                        )
                elif isinstance(selected_item, Wand):
                    # 杖の使用には方向選択が必要
                    player = self.game_screen.game_logic.player
                    display_name = selected_item.get_display_name(player.identification)
                    self.game_screen.game_logic.add_message(
                        f"Use 'z' key to zap the {display_name}. Wands require direction."
                    )
                else:
                    player = self.game_screen.game_logic.player
                    display_name = selected_item.get_display_name(player.identification)
                    self.game_screen.game_logic.add_message(f"You cannot use the {display_name}.")
                return

            # r: 装備解除
            if event.sym == tcod.event.KeySym.R:
                # 装備解除モードに入る
                self._enter_unequip_mode()
                return

            # d: ドロップ
            if event.sym == tcod.event.KeySym.D:
                # インベントリのドロップ処理を使用
                success, dropped_count, message = self.game_screen.game_logic.inventory.drop_item(selected_item)

                if success:
                    # 地面にアイテムを配置
                    if self.game_screen.game_logic.drop_item_at(
                        selected_item,
                        self.game_screen.game_logic.player.x,
                        self.game_screen.game_logic.player.y,
                    ):
                        self.game_screen.game_logic.add_message(message)

                        # 選択インデックスを調整
                        if self.selected_index >= len(self.game_screen.game_logic.inventory.items):
                            self.selected_index = max(0, len(self.game_screen.game_logic.inventory.items) - 1)
                    else:
                        self.game_screen.game_logic.add_message("You cannot drop items here.")
                else:
                    self.game_screen.game_logic.add_message(message)
                return

    def _enter_unequip_mode(self) -> None:
        """装備解除モードに入る"""
        # 装備中のアイテムを確認
        equipped_items = []
        equipped = self.game_screen.game_logic.inventory.equipped

        if equipped["weapon"]:
            equipped_items.append(("weapon", equipped["weapon"]))
        if equipped["armor"]:
            equipped_items.append(("armor", equipped["armor"]))
        if equipped["ring_left"]:
            equipped_items.append(("ring_left", equipped["ring_left"]))
        if equipped["ring_right"]:
            equipped_items.append(("ring_right", equipped["ring_right"]))

        if not equipped_items:
            self.game_screen.game_logic.add_message("You have no equipment to remove.")
            return

        # 装備解除選択画面を表示
        self.game_screen.game_logic.add_message("Select item to unequip:")
        for i, (slot, item) in enumerate(equipped_items):
            slot_name = {"weapon": "Weapon", "armor": "Armor", "ring_left": "Ring(L)", "ring_right": "Ring(R)"}[slot]
            display_name = item.get_display_name(self.game_screen.game_logic.player.identification)
            self.game_screen.game_logic.add_message(f"{chr(ord('a') + i)}) {slot_name}: {display_name}")

        self.unequip_mode = True
        self.equipped_items = equipped_items
        self.game_screen.game_logic.add_message("Press a-z to select, ESC to cancel.")

    def _handle_unequip_selection(self, event: tcod.event.KeyDown) -> None:
        """装備解除選択の処理"""
        if event.sym == tcod.event.KeySym.ESCAPE:
            self.unequip_mode = False
            self.game_screen.game_logic.add_message("Cancelled.")
            return

        # a-z キーの処理
        if event.sym >= ord("a") and event.sym <= ord("z"):
            index = event.sym - ord("a")
            if 0 <= index < len(self.equipped_items):
                slot, item = self.equipped_items[index]

                # 装備を外す
                unequipped_item = self.game_screen.game_logic.inventory.unequip(slot)
                if unequipped_item:
                    # インベントリに追加
                    if self.game_screen.game_logic.inventory.add_item(unequipped_item):
                        self.game_screen.game_logic.add_message(f"You unequip the {unequipped_item.name}.")
                    else:
                        # インベントリが満杯の場合は再装備
                        self.game_screen.game_logic.inventory.equipped[slot] = unequipped_item
                        self.game_screen.game_logic.add_message("Your inventory is full!")
                else:
                    # 呪われたアイテムの場合
                    self.game_screen.game_logic.add_message(f"The {item.name} is cursed and cannot be removed!")
            else:
                self.game_screen.game_logic.add_message("Invalid selection.")

            self.unequip_mode = False
        else:
            self.game_screen.game_logic.add_message("Press a-z to select, ESC to cancel.")
