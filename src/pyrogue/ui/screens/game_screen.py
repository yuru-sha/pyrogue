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

    def update_console(self, console: tcod.console.Console) -> None:
        """コンソールの更新"""
        self.console = console
        # プレイヤーの位置を新しい画面サイズに合わせて調整
        self.player_x = min(self.player_x, self.console.width - 2)
        self.player_y = min(self.player_y, self.console.height - 5)

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
            f"Lv:{self.player_stats['level']} "
            f"HP:{self.player_stats['hp']}/{self.player_stats['hp_max']} "
            f"Atk:{self.player_stats['attack']} "
            f"Def:{self.player_stats['defense']} "
            f"Hunger:{self.player_stats['hunger']}% "
            f"Exp:{self.player_stats['exp']} "
            f"Gold:{self.player_stats['gold']}"
        )
        
        # 2行目: 装備情報
        status_line2 = (
            f"Weap:{self.equipment['weapon']} "
            f"Armor:{self.equipment['armor']} "
            f"Ring(L):{self.equipment['ring_left']} "
            f"Ring(R):{self.equipment['ring_right']}"
        )
        
        self.console.print(x=1, y=0, string=status_line1)
        self.console.print(x=1, y=1, string=status_line2)

    def _render_map(self) -> None:
        """マップを表示（仮実装）"""
        map_start_y = 2
        map_end_y = self.console.height - 3
        
        # マップの表示範囲を計算
        visible_width = min(self.console.width - 2, 80)  # 最大80文字まで
        visible_height = map_end_y - map_start_y
        
        # 仮のマップ表示（画面サイズに合わせて調整）
        map_lines = [
            "#" * 5 + "." * 5,
            "#" * 4 + "+" + "." * 4,
            "#" * 3 + "." * 3 + "#" * 3,
            "#" * 3 + "." + "#",
            "#" + "." + "#" + "." + "#"
        ]
        
        for i, line in enumerate(map_lines):
            if i < visible_height:
                self.console.print(x=1, y=map_start_y + i, string=line[:visible_width])
        
        # プレイヤーキャラクターを表示
        self.console.print(x=self.player_x, y=self.player_y, string="@")

    def _render_messages(self) -> None:
        """メッセージログを表示"""
        message_start_y = self.console.height - 3
        for i, message in enumerate(self.messages[-3:]):  # 最新の3メッセージを表示
            # メッセージが長い場合は画面幅に合わせて切り詰める
            max_length = self.console.width - 2
            if len(message) > max_length:
                message = message[:max_length-3] + "..."
            self.console.print(x=1, y=message_start_y + i, string=message)

    def handle_keydown(self, event: tcod.event.KeyDown) -> None:
        """Handle keyboard input."""
        key = event.sym
        
        # Movement keys
        if key in (tcod.event.KeySym.UP, tcod.event.KeySym.k):
            self.player_y = max(2, self.player_y - 1)  # マップ領域の上端を考慮
            game_logger.debug("Move up")
        elif key in (tcod.event.KeySym.DOWN, tcod.event.KeySym.j):
            self.player_y = min(self.console.height - 4, self.player_y + 1)  # マップ領域の下端を考慮
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
            self.player_y = max(2, self.player_y - 1)
            game_logger.debug("Move left-up")
        elif key == tcod.event.KeySym.u:  # Right-up
            self.player_x = min(self.console.width - 2, self.player_x + 1)
            self.player_y = max(2, self.player_y - 1)
            game_logger.debug("Move right-up")
        elif key == tcod.event.KeySym.b:  # Left-down
            self.player_x = max(1, self.player_x - 1)
            self.player_y = min(self.console.height - 4, self.player_y + 1)
            game_logger.debug("Move left-down")
        elif key == tcod.event.KeySym.n:  # Right-down
            self.player_x = min(self.console.width - 2, self.player_x + 1)
            self.player_y = min(self.console.height - 4, self.player_y + 1)
            game_logger.debug("Move right-down") 