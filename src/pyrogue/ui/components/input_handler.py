"""Translate GUI key events into the shared Rogue command map."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.event

from pyrogue.core.game_states import GameStates
from pyrogue.core.rogue_game import ItemKind

if TYPE_CHECKING:
    from pyrogue.ui.screens.game_screen import GameScreen


_DIRECTION_KEYS = {
    ord("h"): (-1, 0),
    ord("j"): (0, 1),
    ord("k"): (0, -1),
    ord("l"): (1, 0),
    ord("y"): (-1, -1),
    ord("u"): (1, -1),
    ord("b"): (-1, 1),
    ord("n"): (1, 1),
    tcod.event.KeySym.LEFT: (-1, 0),
    tcod.event.KeySym.RIGHT: (1, 0),
    tcod.event.KeySym.UP: (0, -1),
    tcod.event.KeySym.DOWN: (0, 1),
    tcod.event.KeySym.KP_4: (-1, 0),
    tcod.event.KeySym.KP_6: (1, 0),
    tcod.event.KeySym.KP_8: (0, -1),
    tcod.event.KeySym.KP_2: (0, 1),
    tcod.event.KeySym.KP_7: (-1, -1),
    tcod.event.KeySym.KP_9: (1, -1),
    tcod.event.KeySym.KP_1: (-1, 1),
    tcod.event.KeySym.KP_3: (1, 1),
}
_DIRECTION_NAMES = {
    (-1, 0): "west",
    (0, 1): "south",
    (0, -1): "north",
    (1, 0): "east",
    (-1, -1): "northwest",
    (1, -1): "northeast",
    (-1, 1): "southwest",
    (1, 1): "southeast",
}
_KEY_COMMANDS = {
    tcod.event.KeySym.LEFT: "h",
    tcod.event.KeySym.RIGHT: "l",
    tcod.event.KeySym.UP: "k",
    tcod.event.KeySym.DOWN: "j",
    tcod.event.KeySym.KP_4: "h",
    tcod.event.KeySym.KP_6: "l",
    tcod.event.KeySym.KP_8: "k",
    tcod.event.KeySym.KP_2: "j",
    tcod.event.KeySym.KP_7: "y",
    tcod.event.KeySym.KP_9: "u",
    tcod.event.KeySym.KP_1: "b",
    tcod.event.KeySym.KP_3: "n",
}


class InputHandler:
    """Manage canonical commands and temporary inventory selections."""

    def __init__(self, game_screen: GameScreen) -> None:
        self.game_screen = game_screen
        self.count_prefix = ""
        self.item_selection_action: str | None = None
        self.direction_selection_action: str | None = None
        self.direction_selection_mode = False
        self.selected_item_id: int | None = None
        self.pending_count = ""

    def handle_key(self, event: tcod.event.KeyDown) -> GameStates | None:
        """Handle one TCOD key event using the shared command map."""
        if self.direction_selection_mode:
            return self._handle_direction_selection_key(event)
        key, mod = event.sym, event.mod
        if key == tcod.event.KeySym.TAB:
            self.count_prefix = ""
            self.game_screen.toggle_fov()
            return None
        text = getattr(event, "text", getattr(event, "unicode", ""))
        digit = text if len(text) == 1 else chr(key) if isinstance(key, int) and ord("0") <= key <= ord("9") else ""
        if digit.isdigit():
            self.count_prefix = str(min(255, int(self.count_prefix + digit)))
            return None
        if mod & tcod.event.Modifier.SHIFT:
            key = {
                ord("w"): ord("W"),
                ord("t"): ord("T"),
                ord("p"): ord("P"),
                ord("r"): ord("R"),
                ord("s"): ord("S"),
                ord("q"): ord("Q"),
                tcod.event.KeySym.SLASH: ord("?"),
            }.get(key, key)
        if key == ord("S"):
            self.count_prefix = ""
            self.game_screen.save_game()
            return None
        if key == tcod.event.KeySym.ESCAPE:
            self.count_prefix = ""
            return GameStates.MENU if self.game_screen.engine else None
        if key == ord("i"):
            self.count_prefix = ""
            self.game_screen.execute("inventory")
            return GameStates.SHOW_INVENTORY
        if key == ord("o"):
            self.count_prefix = ""
            return self._execute("o")
        if key == ord("c"):
            self.count_prefix = ""
            return self._start_item_selection("call")
        if key == ord("f"):
            self.count_prefix = ""
            self.begin_direction_selection("attack", None)
            return None
        if key in {ord("t"), ord("z"), ord("r")}:
            action = {ord("t"): "throw", ord("z"): "zap", ord("r"): "read"}[key]
            self.pending_count, self.count_prefix = self.count_prefix, ""
            return self._start_item_selection(action)
        if mod & tcod.event.Modifier.CTRL and key in {ord("s"), ord("S")}:
            self.count_prefix = ""
            self.game_screen.save_game()
            return None
        if mod & tcod.event.Modifier.CTRL and key in {ord("l"), ord("L")}:
            self.count_prefix = ""
            self.game_screen.load_game()
            return None
        command = (
            ">"
            if key == tcod.event.KeySym.GREATER
            or text == ">"
            or (event.sym == tcod.event.KeySym.PERIOD and mod & tcod.event.Modifier.SHIFT)
            else "<"
            if key == tcod.event.KeySym.LESS
            or text == "<"
            or (event.sym == tcod.event.KeySym.COMMA and mod & tcod.event.Modifier.SHIFT)
            else _KEY_COMMANDS.get(key)
        )
        if command is None:
            command = (
                text if text and text in "HJKLYUBN" else chr(key) if isinstance(key, int) and 32 <= key <= 126 else text
            )
        if self.count_prefix:
            prefix, self.count_prefix = self.count_prefix, ""
            if command in self.game_screen.rogue_game.COUNTABLE_COMMANDS:
                command = prefix + command
        if not command or not command.isprintable():
            return None
        return self._execute(command)

    def _execute(self, command: str) -> GameStates | None:
        result = self.game_screen.execute(command)
        if command in {"o", "options"}:
            return GameStates.OPTIONS_MENU
        return {
            "quit": GameStates.EXIT,
            "dead": GameStates.GAME_OVER,
            "victory": GameStates.VICTORY,
        }.get(result.state.value)

    def _start_item_selection(self, action: str) -> GameStates | None:
        items = self.game_screen.player.inventory
        if action == "zap":
            items = [item for item in items if item.kind == ItemKind.WAND]
        elif action == "read":
            items = [item for item in items if item.kind == ItemKind.SCROLL]
        if not items:
            message = {
                "call": "You have no items to call.",
                "zap": "You have no wands to zap.",
                "read": "You have no scrolls to read.",
            }.get(action, "You have nothing to throw.")
            self.game_screen.add_message(message)
            self.pending_count = ""
            return None
        self.item_selection_action = action
        self.direction_selection_action = None
        self.direction_selection_mode = False
        self.selected_item_id = None
        return GameStates.SHOW_INVENTORY

    def begin_direction_selection(self, action: str, item_id: int | None = None) -> None:
        """Wait for a direction before executing an attack or item action."""
        self.item_selection_action = None
        self.direction_selection_action = action
        self.direction_selection_mode = True
        self.selected_item_id = item_id
        verb = {"attack": "fight", "throw": "throw", "zap": "zap"}[action]
        self.game_screen.add_message(f"In which direction do you want to {verb}?")
        if self.game_screen.engine:
            self.game_screen.engine.state = GameStates.PLAYERS_TURN

    def reset_selection(self) -> None:
        """Clear an unfinished item or direction selection."""
        self.item_selection_action = None
        self.direction_selection_action = None
        self.direction_selection_mode = False
        self.selected_item_id = None

    def _handle_direction_selection_key(self, event: tcod.event.KeyDown) -> GameStates | None:
        if event.sym == tcod.event.KeySym.ESCAPE:
            self.pending_count = ""
            self.reset_selection()
            self.game_screen.add_message("Cancelled.")
            return None
        direction = _DIRECTION_KEYS.get(event.sym)
        text = getattr(event, "text", "")
        if direction is None and len(text) == 1:
            direction = _DIRECTION_KEYS.get(ord(text))
        if direction is None:
            self.game_screen.add_message("Choose a direction (use movement keys).")
            return None
        action, item_id = self.direction_selection_action, self.selected_item_id
        count = self.pending_count
        self.reset_selection()
        if action is None:
            return None
        args = [_DIRECTION_NAMES[direction]] if item_id is None else [item_id, _DIRECTION_NAMES[direction]]
        command = {"throw": "t", "zap": "z"}.get(action, action)
        if count and command in self.game_screen.rogue_game.COUNTABLE_COMMANDS:
            command = count + command
        self.pending_count = ""
        result = self.game_screen.execute(command, args)
        return {"dead": GameStates.GAME_OVER, "victory": GameStates.VICTORY}.get(result.state.value)
