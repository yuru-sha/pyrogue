"""Game screen module."""
from __future__ import annotations

import tcod
import tcod.console
import tcod.event

from pyrogue.utils import game_logger

class GameScreen:
    """Game screen class."""

    def __init__(self, console: tcod.console.Console):
        self.console = console
        self.player_x = 40
        self.player_y = 25
        
        # プレイヤーステータス（仮）
        self.player_stats = {
            "level": 1,
            "hp": 20,
            "hp_max": 20,
            "attack": 5,
            "defense": 3,
            "hunger": 100,
            "exp": 0,
            "gold": 0,
        }
        
        # 装備（仮）
        self.equipment = {
            "weapon": "Dagger",
            "armor": "Leather Armor",
            "ring_left": "None",
            "ring_right": "None",
        }
        
        # メッセージログ（仮）
        self.messages = [
            "Welcome to PyRogue!",
            "Use vi keys (hjklyubn) or arrow keys to move.",
            "Press ESC to return to menu.",
        ]

    def render(self) -> None:
        """Render the game screen."""
        self.console.clear()
        
        # ステータス表示（上部2行）
        self._render_status()
        
        # マップ表示（中央部分）
        self._render_map()
        
        # メッセージログ（下部3行）
        self._render_messages()

    def _render_status(self) -> None:
        """ステータス情報を表示"""
        # 1行目: レベル、HP、攻撃力、防御力、空腹度、経験値、所持金
        status_line1 = (
            f" Lv:{self.player_stats['level']} "
            f"HP:{self.player_stats['hp']}/{self.player_stats['hp_max']} "
            f"Atk:{self.player_stats['attack']} "
            f"Def:{self.player_stats['defense']} "
            f"Hunger:{self.player_stats['hunger']}% "
            f"Exp:{self.player_stats['exp']} "
            f"Gold:{self.player_stats['gold']}"
        )
        
        # 2行目: 装備情報
        status_line2 = (
            f" Weap:{self.equipment['weapon']} "
            f"Armor:{self.equipment['armor']} "
            f"Ring(L):{self.equipment['ring_left']} "
            f"Ring(R):{self.equipment['ring_right']}"
        )
        
        self.console.print(x=0, y=0, string=status_line1)
        self.console.print(x=0, y=1, string=status_line2)

    def _render_map(self) -> None:
        """マップを表示（仮実装）"""
        map_start_y = 2
        map_end_y = self.console.height - 4
        
        # 仮のマップ表示
        self.console.print(x=1, y=map_start_y, string="#####.....")
        self.console.print(x=1, y=map_start_y + 1, string="#....+...")
        self.console.print(x=1, y=map_start_y + 2, string="###...###")
        self.console.print(x=1, y=map_start_y + 3, string="#...#")
        self.console.print(x=1, y=map_start_y + 4, string="#.#.#")
        
        # プレイヤーキャラクターを表示
        self.console.print(x=self.player_x, y=self.player_y, string="@")

    def _render_messages(self) -> None:
        """メッセージログを表示"""
        message_start_y = self.console.height - 4
        for i, message in enumerate(self.messages[-3:]):  # 最新の3メッセージを表示
            self.console.print(x=1, y=message_start_y + i + 1, string=message)

    def handle_keydown(self, event: tcod.event.KeyDown) -> None:
        """Handle keyboard input."""
        key = event.sym
        
        # Movement keys
        if key in (tcod.event.KeySym.UP, tcod.event.KeySym.k):
            self.player_y = max(3, self.player_y - 1)  # マップ領域の上端を考慮
            game_logger.debug("Move up")
        elif key in (tcod.event.KeySym.DOWN, tcod.event.KeySym.j):
            self.player_y = min(self.console.height - 5, self.player_y + 1)  # マップ領域の下端を考慮
            game_logger.debug("Move down")
        elif key in (tcod.event.KeySym.LEFT, tcod.event.KeySym.h):
            self.player_x = max(1, self.player_x - 1)
            game_logger.debug("Move left")
        elif key in (tcod.event.KeySym.RIGHT, tcod.event.KeySym.l):
            self.player_x = min(self.console.width - 2, self.player_x + 1)
            game_logger.debug("Move right")
        # Diagonal movement
        elif key == tcod.event.KeySym.y:  # Left-up
            self.player_x = max(1, self.player_x - 1)
            self.player_y = max(3, self.player_y - 1)
            game_logger.debug("Move left-up")
        elif key == tcod.event.KeySym.u:  # Right-up
            self.player_x = min(self.console.width - 2, self.player_x + 1)
            self.player_y = max(3, self.player_y - 1)
            game_logger.debug("Move right-up")
        elif key == tcod.event.KeySym.b:  # Left-down
            self.player_x = max(1, self.player_x - 1)
            self.player_y = min(self.console.height - 5, self.player_y + 1)
            game_logger.debug("Move left-down")
        elif key == tcod.event.KeySym.n:  # Right-down
            self.player_x = min(self.console.width - 2, self.player_x + 1)
            self.player_y = min(self.console.height - 5, self.player_y + 1)
            game_logger.debug("Move right-down") 