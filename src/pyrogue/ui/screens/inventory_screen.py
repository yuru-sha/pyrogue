"""Canonical inventory screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
import tcod.event
from tcod.console import Console

from pyrogue.core.game_states import GameStates
from pyrogue.core.rogue_game import ItemKind, ItemState
from pyrogue.ui.screens.screen import Screen

if TYPE_CHECKING:
    from pyrogue.ui.screens.game_screen import GameScreen


class InventoryScreen(Screen):
    """Display and operate on the player's canonical inventory."""

    def __init__(self, game_screen: GameScreen) -> None:
        super().__init__(game_screen.engine)
        self.game_screen = game_screen
        self.selected_index = 0
        self.show_help = False
        self.unequip_mode = False
        self.equipped_items: list[tuple[str, ItemState]] = []

    def _items(self) -> list[ItemState]:
        """Return the current inventory, filtered for a pending action."""
        items = self.game_screen.player.inventory
        if self.game_screen.input_handler.item_selection_action == "zap":
            return [item for item in items if item.kind == ItemKind.WAND]
        return items

    def _clamp_selection(self, items: list[ItemState]) -> None:
        self.selected_index = min(self.selected_index, max(0, len(items) - 1))

    def _equipped_slot(self, item: ItemState) -> str | None:
        player = self.game_screen.player
        if player.equipped_weapon == item.id:
            return "weapon"
        if player.equipped_armor == item.id:
            return "armor"
        if item.id in player.equipped_rings:
            return "ring_left" if player.equipped_rings.index(item.id) == 0 else "ring_right"
        return None

    def render(self, console: Console) -> None:
        """Render the canonical inventory and equipment."""
        console.clear()
        items = self._items()
        self._clamp_selection(items)
        action = self.game_screen.input_handler.item_selection_action
        title = f"Select item to {action}" if action else "Inventory"
        console.print(1, 1, title, (255, 255, 0))

        for index, item in enumerate(items):
            suffix = f" (x{item.quantity})" if item.quantity > 1 else ""
            slot = self._equipped_slot(item)
            if slot:
                suffix += f" ({slot.replace('_', ' ').upper()})"
            fg = (255, 255, 0) if index == self.selected_index else (255, 255, 255)
            console.print(2, 3 + index, f"{chr(ord('a') + index)}) {item.display_name}{suffix}", fg)

        console.print(40, 3, "Equipment:", (255, 255, 0))
        player = self.game_screen.player
        console.print(42, 5, f"Weapon: {self._get_equipment_info(player.equipped(ItemKind.WEAPON))}")
        console.print(42, 6, f"Armor: {self._get_equipment_info(player.equipped(ItemKind.ARMOR))}")
        rings = [player.item(item_id) for item_id in player.equipped_rings]
        console.print(42, 7, f"Ring(L): {self._get_equipment_info(rings[0] if rings else None)}")
        console.print(42, 8, f"Ring(R): {self._get_equipment_info(rings[1] if len(rings) > 1 else None)}")
        console.print(42, 10, f"Attack Bonus: {player.attack - player.level:+d}")
        console.print(42, 11, f"Defense Bonus: {player.armor_class - player.defense:+d}")

        if action:
            console.print(2, console.height - 2, "Select an item by letter; movement keys also work.", (127, 127, 127))
        elif self.show_help:
            help_text = [
                "Commands:",
                "[↑/↓] Select item",
                "[e] Equip selected item",
                "[u] Use selected item",
                "[d] Drop selected item",
                "[r] Remove equipment",
                "[ESC] Close inventory",
                "[?] Toggle help",
                "[a-z] Select item by letter",
            ]
            for index, text in enumerate(help_text):
                console.print(2, console.height - 10 + index, text, (127, 127, 127))

    @staticmethod
    def _get_equipment_info(item: ItemState | None) -> str:
        """Return a compact canonical equipment description."""
        if item is None:
            return "None"
        if item.kind == ItemKind.WEAPON:
            return f"{item.display_name} (ATK {item.damage_bonus + item.enchantment:+d})"
        if item.kind == ItemKind.ARMOR:
            return f"{item.display_name} (DEF {item.armor_bonus + item.enchantment:+d})"
        if item.kind == ItemKind.RING and item.enchantment:
            return f"{item.display_name} ({item.effect.upper()} {item.enchantment:+d})"
        return item.display_name

    def handle_input(self, event: tcod.event.KeyDown) -> None:
        """Handle inventory navigation and canonical item commands."""
        if self.unequip_mode:
            self._handle_unequip_selection(event)
            return

        if event.sym == tcod.event.KeySym.ESCAPE:
            self.game_screen.input_handler.item_selection_action = None
            if self.game_screen.engine:
                self.game_screen.engine.state = GameStates.PLAYERS_TURN
            return

        unicode_char = getattr(event, "text", getattr(event, "unicode", ""))
        if event.sym in {tcod.event.KeySym.QUESTION, tcod.event.KeySym.SLASH} or unicode_char in {"?", "/"}:
            self.show_help = not self.show_help
            return

        items = self._items()
        self._clamp_selection(items)
        action = self.game_screen.input_handler.item_selection_action
        if action:
            if not items:
                return
            selection_delta = {
                tcod.event.KeySym.LEFT: -1,
                tcod.event.KeySym.RIGHT: 1,
                tcod.event.KeySym.UP: -1,
                tcod.event.KeySym.DOWN: 1,
                ord("h"): -1,
                ord("l"): 1,
                ord("k"): -1,
                ord("j"): 1,
            }
            if delta := selection_delta.get(event.sym):
                self.selected_index = (self.selected_index + delta) % len(items)
                return
            if event.sym == tcod.event.KeySym.RETURN:
                if items:
                    self._begin_pending_action(items[self.selected_index])
                return
            if ord("a") <= event.sym <= ord("z"):
                item_index = event.sym - ord("a")
                if item_index < len(items):
                    self._begin_pending_action(items[item_index])
                return
            return

        if not items:
            return
        if event.sym == tcod.event.KeySym.UP:
            self.selected_index = (self.selected_index - 1) % len(items)
            return
        if event.sym == tcod.event.KeySym.DOWN:
            self.selected_index = (self.selected_index + 1) % len(items)
            return
        if ord("a") <= event.sym <= ord("z") and event.sym not in map(ord, "uedr"):
            item_index = event.sym - ord("a")
            if item_index < len(items):
                self.selected_index = item_index
            return

        item = items[self.selected_index]
        if event.sym == ord("e"):
            command = {
                ItemKind.WEAPON: "wield",
                ItemKind.ARMOR: "wear",
                ItemKind.RING: "put_on_ring",
            }.get(item.kind)
            if command:
                self.game_screen.execute(command, [item.id])
            else:
                self.game_screen.add_message(f"You cannot equip the {item.display_name}.")
        elif event.sym == ord("u"):
            if item.kind == ItemKind.WAND:
                self.game_screen.input_handler.begin_direction_selection("zap", item.id)
            elif item.kind in {ItemKind.FOOD, ItemKind.POTION, ItemKind.SCROLL}:
                self.game_screen.execute("use", [item.id])
            else:
                self.game_screen.add_message(f"You cannot use the {item.display_name}.")
        elif event.sym == ord("d"):
            self.game_screen.execute("drop", [item.id])
            self._clamp_selection(self._items())
        elif event.sym == ord("r"):
            self._enter_unequip_mode()

    def _begin_pending_action(self, item: ItemState) -> None:
        """Pass the selected canonical item to the direction selector."""
        action = self.game_screen.input_handler.item_selection_action
        if action == "zap" and item.kind != ItemKind.WAND:
            self.game_screen.add_message("You can only zap a wand.")
            return
        self.game_screen.input_handler.begin_direction_selection(action or "throw", item.id)

    def _enter_unequip_mode(self) -> None:
        """Show the currently equipped canonical armor and rings."""
        player = self.game_screen.player
        equipped: list[tuple[str, ItemState]] = []
        weapon = player.equipped(ItemKind.WEAPON)
        if weapon:
            equipped.append(("unequip_weapon", weapon))
        armor = player.equipped(ItemKind.ARMOR)
        if armor:
            equipped.append(("unequip_armor", armor))
        equipped.extend(
            ("remove_ring", item)
            for item in (player.item(item_id) for item_id in player.equipped_rings)
            if item is not None
        )
        if not equipped:
            self.game_screen.add_message("You have no equipment to remove.")
            return
        self.equipped_items = equipped
        self.unequip_mode = True
        self.game_screen.add_message("Select item to unequip:")
        for index, (command, item) in enumerate(equipped):
            label = {"unequip_weapon": "Weapon", "unequip_armor": "Armor"}.get(command, "Ring")
            self.game_screen.add_message(f"{chr(ord('a') + index)}) {label}: {item.display_name}")

    def _handle_unequip_selection(self, event: tcod.event.KeyDown) -> None:
        """Apply a canonical unequip command or cancel."""
        if event.sym == tcod.event.KeySym.ESCAPE:
            self.unequip_mode = False
            self.game_screen.add_message("Cancelled.")
            return
        if ord("a") <= event.sym <= ord("z"):
            index = event.sym - ord("a")
            if index < len(self.equipped_items):
                command, item = self.equipped_items[index]
                self.game_screen.execute(command, [item.id])
                self.unequip_mode = False
