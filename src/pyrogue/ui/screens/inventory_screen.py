"""Inventory screen module."""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import tcod
import tcod.event
from tcod.console import Console

from pyrogue.entities.items.item import Item, Weapon, Armor, Ring, Scroll, Potion, Food
from pyrogue.ui.screens.screen import Screen

if TYPE_CHECKING:
    from pyrogue.ui.screens.game_screen import GameScreen

class InventoryScreen(Screen):
    """インベントリ画面"""
    
    def __init__(self, game_screen: GameScreen):
        self.game_screen = game_screen
        self.selected_index = 0
        self.show_help = True
    
    def render(self, console: Console) -> None:
        """画面を描画
        
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
            index_char = chr(ord('a') + i)
            
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
        console.print(42, 5, f"Weapon: {equipped['weapon'].name if equipped['weapon'] else 'None'}")
        console.print(42, 6, f"Armor: {equipped['armor'].name if equipped['armor'] else 'None'}")
        console.print(42, 7, f"Ring(L): {equipped['ring_left'].name if equipped['ring_left'] else 'None'}")
        console.print(42, 8, f"Ring(R): {equipped['ring_right'].name if equipped['ring_right'] else 'None'}")
        
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
                "[?] Toggle help"
            ]
            for i, text in enumerate(help_text):
                console.print(2, console.height - 10 + i, text, tcod.gray)
    
    def handle_key(self, key: tcod.event.KeyDown) -> Optional[Screen]:
        """キー入力を処理
        
        Args:
            key: キー入力イベント
            
        Returns:
            Optional[Screen]: 次の画面（Noneの場合は現在の画面を維持）
        """
        # ESCでインベントリを閉じる
        if key.sym == tcod.event.KeySym.ESCAPE:
            return self.game_screen
        
        # ?でヘルプの表示/非表示を切り替え
        elif key.sym == tcod.event.KeySym.QUESTION:
            self.show_help = not self.show_help
            return None
        
        # アイテムの選択（a-z）
        elif tcod.event.KeySym.a <= key.sym <= tcod.event.KeySym.z:
            index = key.sym - tcod.event.KeySym.a
            if index < len(self.game_screen.player.inventory.items):
                self.selected_index = index
            return None
        
        # 選択中のアイテムに対する操作
        selected_item = self.game_screen.player.inventory.get_item(self.selected_index)
        if not selected_item:
            return None
        
        # e: 装備
        if key.sym == tcod.event.KeySym.e:
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
        elif key.sym == tcod.event.KeySym.u:
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
        elif key.sym == tcod.event.K_d:
            # プレイヤーの位置にアイテムを配置
            selected_item.x = self.game_screen.player.x
            selected_item.y = self.game_screen.player.y
            self.game_screen.item_spawner.items.append(selected_item)
            self.game_screen.item_spawner.occupied_positions.add((selected_item.x, selected_item.y))
            self.game_screen.player.inventory.remove_item(selected_item)
            self.game_screen.message_log.append(
                f"You drop the {selected_item.name}."
            )
            
            # 選択インデックスを調整
            if self.selected_index >= len(self.game_screen.player.inventory.items):
                self.selected_index = max(0, len(self.game_screen.player.inventory.items) - 1)
        
        # r: 装備を外す
        elif key.sym == tcod.event.KeySym.r:
            # 装備スロットを選択するサブメニューを表示
            return EquipmentRemovalScreen(self)
        
        return None

class EquipmentRemovalScreen(Screen):
    """装備解除画面"""
    
    def __init__(self, inventory_screen: InventoryScreen):
        self.inventory_screen = inventory_screen
        self.game_screen = inventory_screen.game_screen
    
    def render(self, console: Console) -> None:
        """画面を描画
        
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
            "[ESC] Cancel"
        ]
        
        for i, text in enumerate(menu_text):
            console.print(30, 15 + i, text, tcod.white)
    
    def handle_key(self, key: tcod.event.KeyDown) -> Optional[Screen]:
        """キー入力を処理
        
        Args:
            key: キー入力イベント
            
        Returns:
            Optional[Screen]: 次の画面（Noneの場合は現在の画面を維持）
        """
        if key.sym == tcod.event.KeySym.ESCAPE:
            return self.inventory_screen
        
        slot = None
        if key.sym == tcod.event.KeySym.w:
            slot = "weapon"
        elif key.sym == tcod.event.KeySym.a:
            slot = "armor"
        elif key.sym == tcod.event.KeySym.l:
            slot = "ring_left"
        elif key.sym == tcod.event.KeySym.r:
            slot = "ring_right"
        
        if slot:
            item = self.game_screen.player.unequip_item(slot)
            if item:
                self.game_screen.message_log.append(
                    f"You unequip the {item.name}."
                )
            else:
                self.game_screen.message_log.append(
                    f"You have nothing equipped in that slot."
                )
            return self.inventory_screen
        
        return None 