"""Game screen module."""
from __future__ import annotations

import tcod
import tcod.console
import tcod.event
import numpy as np
from tcod import libtcodpy

from pyrogue.utils import game_logger
from pyrogue.map.dungeon import DungeonGenerator
from pyrogue.map.tile import Tile, Floor, Wall, Door, SecretDoor, Stairs, Water, Lava

class GameScreen(object):
    """Game screen class."""

    def __init__(self, engine: Engine) -> None:
        """初期化"""
        self.engine = engine
        
        # 現在の階層
        self.current_floor = 1
        
        # ダンジョンの生成
        self.dungeon_width = 80
        self.dungeon_height = 45  # ステータス2行 + マップ + メッセージ3行
        self.dungeon_gen = DungeonGenerator(
            width=self.dungeon_width,
            height=self.dungeon_height,
            floor=self.current_floor,  # 現在の階層を渡す
            min_room_size=(6, 6),
            max_room_size=(10, 10)
        )
        self.dungeon_tiles = None
        
        # プレイヤーの位置
        self.player_x = 0
        self.player_y = 0
        
        # プレイヤーステータス
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
        
        # 装備
        self.equipment = {
            "weapon": "Dagger",
            "armor": "Leather Armor",
            "ring_left": "None",
            "ring_right": "None",
        }
        
        # メッセージログ
        self.message_log = [
            "Welcome to PyRogue!",
            "Use vi keys (hjklyubn), arrow keys, or numpad (1-9) to move.",
            "Press ESC to return to menu.",
        ]
        
        # 視界の計算用
        self.fov_enabled = True
        self.fov_map = None
        self.visible = None
        self.explored = None

    def setup_new_game(self) -> None:
        """新しいゲームのセットアップ"""
        # ダンジョンの生成
        self.dungeon_tiles, start_pos, _ = self.dungeon_gen.generate()
        
        # プレイヤーの初期位置を設定
        self.player_x, self.player_y = start_pos
        
        # FOVマップの初期化
        self.fov_map = tcod.map.Map(width=self.dungeon_tiles.shape[1], height=self.dungeon_tiles.shape[0])
        self._update_fov_map()
        
        # 視界の初期化
        self.visible = np.full((self.dungeon_tiles.shape[0], self.dungeon_tiles.shape[1]), fill_value=False, dtype=bool)
        self.explored = np.full((self.dungeon_tiles.shape[0], self.dungeon_tiles.shape[1]), fill_value=False, dtype=bool)
        self._compute_fov()

    def _update_fov_map(self) -> None:
        """FOVマップを更新"""
        for y in range(self.dungeon_tiles.shape[0]):
            for x in range(self.dungeon_tiles.shape[1]):
                if y < len(self.dungeon_tiles) and x < len(self.dungeon_tiles[y]):
                    self.fov_map.transparent[y, x] = self.dungeon_tiles[y, x].transparent
                    self.fov_map.walkable[y, x] = self.dungeon_tiles[y, x].walkable

    def _compute_fov(self) -> None:
        """視界を計算"""
        self.visible = tcod.map.compute_fov(
            transparency=self.fov_map.transparent,
            pov=(self.player_y, self.player_x),
            radius=10,
            algorithm=libtcodpy.FOV_RESTRICTIVE,
        )
        self.explored |= self.visible 

    def update_console(self, console: tcod.console.Console) -> None:
        """コンソールの更新"""
        self.engine.console = console

    def render(self) -> None:
        """画面の描画"""
        self.engine.console.clear()
        
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
        
        self.engine.console.print(x=1, y=0, string=status_line1)
        self.engine.console.print(x=1, y=1, string=status_line2)

    def _render_map(self) -> None:
        """マップを表示"""
        # マップの表示範囲を設定
        map_start_y = 2  # ステータス表示の下から
        
        # マップを描画
        for y in range(self.dungeon_tiles.shape[0]):
            for x in range(self.dungeon_tiles.shape[1]):
                if not self.fov_enabled or self.visible[y, x]:
                    # FOV無効時または可視範囲内
                    tile = self.dungeon_tiles[y, x]
                    char = tile.char
                    fg = tile.light
                elif self.explored[y, x]:
                    # 探索済みだが現在は見えない
                    tile = self.dungeon_tiles[y, x]
                    char = tile.char
                    fg = tile.dark
                else:
                    # 未探索
                    char = " "
                    fg = (0, 0, 0)
                
                self.engine.console.print(x=x, y=y+map_start_y, string=char, fg=fg)
        
        # プレイヤーを描画
        self.engine.console.print(
            x=self.player_x,
            y=self.player_y + map_start_y,
            string="@",
            fg=(255, 255, 255)
        )

    def _render_messages(self) -> None:
        """メッセージログを表示"""
        message_start_y = self.engine.console.height - 3
        for i, message in enumerate(self.message_log[-3:]):  # 最新の3メッセージを表示
            self.engine.console.print(x=1, y=message_start_y + i, string=message)

    def handle_keydown(self, event: tcod.event.KeyDown) -> None:
        """キー入力の処理"""
        key = event.sym
        old_x, old_y = self.player_x, self.player_y
        moved = False
        
        # FOVの切り替え
        if key == tcod.event.KeySym.TAB:
            self.fov_enabled = not self.fov_enabled
            self.message_log.append("FOV " + ("enabled" if self.fov_enabled else "disabled"))
            return
        
        # 移動キーの処理
        if key in (tcod.event.KeySym.UP, tcod.event.KeySym.k, tcod.event.KeySym.KP_8):  # 8
            if self._can_move_to(self.player_x, self.player_y - 1):
                self.player_y -= 1
                moved = True
        elif key in (tcod.event.KeySym.DOWN, tcod.event.KeySym.j, tcod.event.KeySym.KP_2):  # 2
            if self._can_move_to(self.player_x, self.player_y + 1):
                self.player_y += 1
                moved = True
        elif key in (tcod.event.KeySym.LEFT, tcod.event.KeySym.h, tcod.event.KeySym.KP_4):  # 4
            if self._can_move_to(self.player_x - 1, self.player_y):
                self.player_x -= 1
                moved = True
        elif key in (tcod.event.KeySym.RIGHT, tcod.event.KeySym.l, tcod.event.KeySym.KP_6):  # 6
            if self._can_move_to(self.player_x + 1, self.player_y):
                self.player_x += 1
                moved = True
        # 斜め移動
        elif key in (tcod.event.KeySym.y, tcod.event.KeySym.KP_7):  # 7: 左上
            if self._can_move_to(self.player_x - 1, self.player_y - 1):
                self.player_x -= 1
                self.player_y -= 1
                moved = True
        elif key in (tcod.event.KeySym.u, tcod.event.KeySym.KP_9):  # 9: 右上
            if self._can_move_to(self.player_x + 1, self.player_y - 1):
                self.player_x += 1
                self.player_y -= 1
                moved = True
        elif key in (tcod.event.KeySym.b, tcod.event.KeySym.KP_1):  # 1: 左下
            if self._can_move_to(self.player_x - 1, self.player_y + 1):
                self.player_x -= 1
                self.player_y += 1
                moved = True
        elif key in (tcod.event.KeySym.n, tcod.event.KeySym.KP_3):  # 3: 右下
            if self._can_move_to(self.player_x + 1, self.player_y + 1):
                self.player_x += 1
                self.player_y += 1
                moved = True
        elif key == tcod.event.KeySym.KP_5:  # 5: その場で待機
            moved = True  # 待機もターンを消費
        
        # 移動が成功した場合、視界を更新
        if moved:
            self._compute_fov()
            
            # 階段の処理
            current_tile = self.dungeon_tiles[self.player_y, self.player_x]
            if isinstance(current_tile, Stairs):
                if current_tile.down:
                    self.message_log.append("There is a staircase leading down.")
                else:
                    self.message_log.append("There is a staircase leading up.")

    def _can_move_to(self, x: int, y: int) -> bool:
        """指定の位置に移動できるかを判定"""
        if not (0 <= x < self.dungeon_tiles.shape[1] and 0 <= y < self.dungeon_tiles.shape[0]):
            return False
        
        tile = self.dungeon_tiles[y, x]
        
        # ドアの場合は開ける
        if isinstance(tile, Door) and tile.door_state == "closed":
            tile.toggle()  # ドアを開ける
            self._update_fov_map()  # FOVマップを更新
            self.message_log.append("You open the door.")
            return False  # このターンは移動せず、ドアを開けるだけ
        
        # 隠し扉の場合は発見
        if isinstance(tile, SecretDoor) and tile.door_state == "secret":
            tile.reveal()  # 隠し扉を発見
            self._update_fov_map()  # FOVマップを更新
            self.message_log.append("You found a secret door!")
            return False  # このターンは移動せず、扉を発見するだけ
        
        return tile.walkable 