"""Game screen module."""
from __future__ import annotations

import tcod
import tcod.console
import tcod.event
import numpy as np
from tcod import libtcodpy
from typing import Optional
import random

from pyrogue.utils import game_logger
from pyrogue.map.dungeon import DungeonGenerator
from pyrogue.map.tile import Tile, Floor, Wall, Door, SecretDoor, Stairs, Water, Lava
from pyrogue.entities.actors.monster_spawner import MonsterSpawner
from pyrogue.entities.items.item_spawner import ItemSpawner
from pyrogue.entities.items.item import Item
from pyrogue.ui.screens.inventory_screen import InventoryScreen

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
        
        # モンスター管理用のインスタンスを追加
        self.monster_spawner = None
        
        # アイテム管理用のインスタンスを追加
        self.item_spawner = ItemSpawner(self.current_floor)

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
        
        # モンスターの生成
        self.monster_spawner = MonsterSpawner(self.current_floor)
        self.monster_spawner.spawn_monsters(self.dungeon_tiles, self.dungeon_gen.rooms)
        
        # アイテムの生成
        self.item_spawner.spawn_items(self.dungeon_tiles, self.dungeon_gen.rooms)

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
        """マップの描画"""
        # マップの描画開始位置（ステータス表示の下）
        map_y_offset = 2
        
        # マップを描画
        for y in range(self.dungeon_tiles.shape[0]):
            for x in range(self.dungeon_tiles.shape[1]):
                tile = self.dungeon_tiles[y, x]
                
                # 隠し扉の特別処理（未発見の場合は壁と同じ色を使用）
                if isinstance(tile, SecretDoor) and tile.door_state == "secret":
                    wall_tile = Wall()
                    if not self.fov_enabled or self.visible[y, x]:
                        self.engine.console.print(x, y + map_y_offset, tile.char, wall_tile.light)
                    elif self.explored[y, x]:
                        self.engine.console.print(x, y + map_y_offset, tile.char, wall_tile.dark)
                    continue
                
                if not self.fov_enabled or self.visible[y, x]:
                    # FOV無効時または視界内のタイル
                    self.engine.console.print(x, y + map_y_offset, tile.char, tile.light)
                elif self.explored[y, x]:
                    # 既に探索済みのタイル
                    self.engine.console.print(x, y + map_y_offset, tile.char, tile.dark)
        
        # アイテムを描画（FOV無効時または視界内のみ）
        for item in self.item_spawner.items:
            if not self.fov_enabled or self.visible[item.y, item.x]:
                self.engine.console.print(item.x, item.y + map_y_offset, item.char, item.color)
        
        # モンスターを描画（FOV無効時または視界内のみ）
        for monster in self.monster_spawner.monsters:
            if not self.fov_enabled or self.visible[monster.y, monster.x]:
                self.engine.console.print(monster.x, monster.y + map_y_offset, monster.char, monster.color)
        
        # プレイヤーを描画
        self.engine.console.print(self.player_x, self.player_y + map_y_offset, "@", (255, 255, 255))

    def _render_messages(self) -> None:
        """メッセージログを表示"""
        message_start_y = self.engine.console.height - 3
        for i, message in enumerate(self.message_log[-3:]):  # 最新の3メッセージを表示
            self.engine.console.print(x=1, y=message_start_y + i, string=message)

    def handle_key(self, event: tcod.event.KeyDown) -> Optional[Screen]:
        """キー入力の処理"""
        # TABキーでFOVのトグル
        if event.sym == tcod.event.K_TAB:
            self.fov_enabled = not self.fov_enabled
            return None
        
        # アイテムを拾う
        elif event.sym == tcod.event.K_g:
            self._handle_get()
            return None
        
        # 隠し扉を探す
        elif event.sym == tcod.event.K_s:
            self._handle_search()
            return None
        
        # 扉を開ける
        elif event.sym == tcod.event.K_o:
            self._handle_door_open()
            return None
        
        # 扉を閉める
        elif event.sym == tcod.event.K_c:
            self._handle_door_close()
            return None
        
        # 移動キーの処理
        if event.sym in (tcod.event.K_UP, tcod.event.K_k, tcod.event.K_KP_8):  # 8
            if self._can_move_to(self.player_x, self.player_y - 1):
                self.player_y -= 1
        elif event.sym in (tcod.event.K_DOWN, tcod.event.K_j, tcod.event.K_KP_2):  # 2
            if self._can_move_to(self.player_x, self.player_y + 1):
                self.player_y += 1
        elif event.sym in (tcod.event.K_LEFT, tcod.event.K_h, tcod.event.K_KP_4):  # 4
            if self._can_move_to(self.player_x - 1, self.player_y):
                self.player_x -= 1
        elif event.sym in (tcod.event.K_RIGHT, tcod.event.K_l, tcod.event.K_KP_6):  # 6
            if self._can_move_to(self.player_x + 1, self.player_y):
                self.player_x += 1
        # 斜め移動
        elif event.sym in (tcod.event.K_y, tcod.event.K_KP_7):  # 7: 左上
            if self._can_move_to(self.player_x - 1, self.player_y - 1):
                self.player_x -= 1
                self.player_y -= 1
        elif event.sym in (tcod.event.K_u, tcod.event.K_KP_9):  # 9: 右上
            if self._can_move_to(self.player_x + 1, self.player_y - 1):
                self.player_x += 1
                self.player_y -= 1
        elif event.sym in (tcod.event.K_b, tcod.event.K_KP_1):  # 1: 左下
            if self._can_move_to(self.player_x - 1, self.player_y + 1):
                self.player_x -= 1
                self.player_y += 1
        elif event.sym in (tcod.event.K_n, tcod.event.K_KP_3):  # 3: 右下
            if self._can_move_to(self.player_x + 1, self.player_y + 1):
                self.player_x += 1
                self.player_y += 1
        elif event.sym == tcod.event.K_KP_5:  # 5: その場で待機
            pass  # 待機もターンを消費
        
        # 移動が成功した場合の処理
        if event.sym in (tcod.event.K_UP, tcod.event.K_DOWN, tcod.event.K_LEFT, tcod.event.K_RIGHT, tcod.event.K_y, tcod.event.K_u, tcod.event.K_b, tcod.event.K_n):
            # モンスターの更新
            self.monster_spawner.update_monsters(
                self.player_x,
                self.player_y,
                self.dungeon_tiles,
                self.fov_map
            )
            
            # 視界の更新
            self._compute_fov()
            
            # 隠し扉のヒントをチェック
            self._check_secret_door_hints()

    def _can_move_to(self, x: int, y: int) -> bool:
        """指定の位置に移動できるかを判定"""
        if not (0 <= x < self.dungeon_tiles.shape[1] and 0 <= y < self.dungeon_tiles.shape[0]):
            return False
        
        tile = self.dungeon_tiles[y, x]
        
        # モンスターとの衝突判定
        monster = self.monster_spawner.get_monster_at(x, y)
        if monster:
            # モンスターがいる場合は戦闘を開始
            self._handle_combat(monster)
            return False  # 移動は行わない
        
        return tile.walkable

    def _handle_combat(self, monster: Monster) -> None:
        """モンスターとの戦闘処理"""
        # プレイヤーの攻撃
        damage = max(0, self.player_stats["attack"] - monster.defense)
        monster.take_damage(damage)
        
        if monster.is_dead():
            # モンスター撃破時の処理
            self.message_log.append(f"You defeated the {monster.name}!")
            self.player_stats["exp"] += monster.exp_value
            # モンスターリストから削除（これにより次のターンの update_monsters で occupied_positions も更新される）
            if monster in self.monster_spawner.monsters:
                self.monster_spawner.monsters.remove(monster)
            return
        
        # モンスターの反撃
        damage = max(0, monster.attack - self.player_stats["defense"])
        self.player_stats["hp"] = max(0, self.player_stats["hp"] - damage)
        
        # 戦闘ログ
        self.message_log.append(
            f"You hit the {monster.name} for {damage} damage. "
            f"The {monster.name} hits you for {damage} damage."
        )
        
        # プレイヤーの死亡判定
        if self.player_stats["hp"] <= 0:
            self.message_log.append("You died!")
            self.engine.state = GameStates.PLAYER_DEAD 

    def _handle_door_open(self) -> None:
        """扉を開ける処理"""
        # 隣接する8方向をチェック
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                x = self.player_x + dx
                y = self.player_y + dy
                
                # マップ範囲内かチェック
                if not (0 <= x < self.dungeon_tiles.shape[1] and 0 <= y < self.dungeon_tiles.shape[0]):
                    continue
                
                tile = self.dungeon_tiles[y, x]
                
                # 通常の扉が閉じている場合
                if isinstance(tile, Door) and tile.door_state == "closed":
                    tile.toggle()  # 扉を開ける
                    self._update_fov_map()  # FOVマップを更新
                    self.message_log.append("You open the door.")
                    return
                # 発見済みの隠し扉が閉じている場合
                elif isinstance(tile, SecretDoor) and tile.door_state == "closed":
                    tile.toggle()  # 扉を開ける
                    self._update_fov_map()  # FOVマップを更新
                    self.message_log.append("You open the door.")
                    return
        
        self.message_log.append("There is no door to open.")

    def _handle_door_close(self) -> None:
        """扉を閉める処理"""
        # 隣接する8方向をチェック
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                x = self.player_x + dx
                y = self.player_y + dy
                
                # マップ範囲内かチェック
                if not (0 <= x < self.dungeon_tiles.shape[1] and 0 <= y < self.dungeon_tiles.shape[0]):
                    continue
                
                tile = self.dungeon_tiles[y, x]
                
                # 開いた扉（通常の扉または発見済みの隠し扉）を見つけた場合
                if (isinstance(tile, Door) or 
                    (isinstance(tile, SecretDoor) and tile.door_state != "secret")) and tile.door_state == "open":
                    # モンスターがいないか確認
                    if self.monster_spawner.get_monster_at(x, y):
                        self.message_log.append("There's a monster in the way!")
                        return
                    
                    tile.toggle()  # 扉を閉める
                    self._update_fov_map()  # FOVマップを更新
                    self.message_log.append("You close the door.")
                    return
        
        self.message_log.append("There is no door to close.")

    def _handle_search(self) -> None:
        """隠し扉を探す処理"""
        # 隣接する8方向をチェック
        found = False
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                x = self.player_x + dx
                y = self.player_y + dy
                
                # マップ範囲内かチェック
                if not (0 <= x < self.dungeon_tiles.shape[1] and 0 <= y < self.dungeon_tiles.shape[0]):
                    continue
                
                tile = self.dungeon_tiles[y, x]
                
                # 隠し扉を見つけた場合
                if isinstance(tile, SecretDoor) and tile.door_state == "secret":
                    # 33%の確率で発見
                    if random.random() < 0.33:
                        tile.reveal()  # 隠し扉を発見
                        self._update_fov_map()  # FOVマップを更新
                        self.message_log.append("You found a secret door!")
                        found = True
        
        if not found:
            self.message_log.append("You search but find nothing.")

    def _handle_get(self) -> None:
        """アイテムを拾う"""
        item = self.item_spawner.get_item_at(self.player_x, self.player_y)
        if item:
            self.message_log.append(f"You pick up the {item.name}.")
            self.item_spawner.remove_item(item)
        else:
            self.message_log.append("There is nothing here to pick up.")

    def _check_secret_door_hints(self) -> None:
        """隠し扉の近くにいる場合、ヒントメッセージを表示"""
        # ヒントメッセージのリスト
        hint_messages = [
            "You notice a faint light through a crack in the wall...",
            "You feel a draft coming from somewhere...",
            "You hear faint laughter through the wall..."
        ]
        
        # 隣接する8方向をチェック
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                x = self.player_x + dx
                y = self.player_y + dy
                
                # マップ範囲内かチェック
                if not (0 <= x < self.dungeon_tiles.shape[1] and 0 <= y < self.dungeon_tiles.shape[0]):
                    continue
                
                tile = self.dungeon_tiles[y, x]
                
                # 隠し扉（未発見）を見つけた場合
                if isinstance(tile, SecretDoor) and tile.door_state == "secret":
                    # ランダムなヒントメッセージを表示
                    self.message_log.append(random.choice(hint_messages))
                    return  # 1つ見つかれば終了 