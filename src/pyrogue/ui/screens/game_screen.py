"""
ゲームスクリーンモジュール。

このモジュールは、メインゲームのプレイ画面を担当します。
ダンジョンのレンダリング、プレイヤーの入力処理、
モンスターとの戦闘、アイテム管理などを統合的に管理します。

Example:
    >>> engine = Engine()
    >>> game_screen = GameScreen(engine)
    >>> game_screen.render(console)

"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import numpy as np
import tcod
import tcod.console
import tcod.constants
import tcod.event

from pyrogue.entities.actors.inventory import Inventory
from pyrogue.entities.actors.monster_spawner import MonsterSpawner
from pyrogue.entities.items.item import Gold, Item
from pyrogue.entities.items.item_spawner import ItemSpawner
from pyrogue.map.dungeon import DungeonGenerator
from pyrogue.map.tile import (
    Door,
    SecretDoor,
    StairsDown,
    StairsUp,
    Wall,
)

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine


class GameScreen:
    """
    メインゲームのスクリーンクラス。
    
    プレイヤーのゲームプレイ体験を管理し、ダンジョンの探索、戦闘、
    アイテム管理、ステータス表示などを統合的に処理します。
    
    特徴:
        - マルチフロアダンジョン管理
        - FOV（Field of View）システム
        - モンスターとアイテムのスポーン管理
        - ゲーム状態の持続性
        - ユーザー入力の処理
    
    Attributes:
        engine: ゲームエンジンインスタンス
        current_floor: 現在の階層
        player_stats: プレイヤーのステータス
        inventory: プレイヤーのインベントリ
        floor_data: 各階層のデータを保持する辞書

    """

    def __init__(self, engine: Engine) -> None:
        """
        ゲームスクリーンを初期化。
        
        Args:
            engine: メインゲームエンジンのインスタンス

        """
        self.engine = engine

        # 現在の階層と前の階層
        self.current_floor = 1
        self.previous_floor = 1

        # 各階層のデータを保持する辞書
        self.floor_data = {}  # Dict[int, FloorData]

        # ダンジョンの生成
        self.dungeon_width = 80
        self.dungeon_height = 45  # ステータス2行 + マップ + メッセージ3行
        self.dungeon_gen = DungeonGenerator(
            width=self.dungeon_width,
            height=self.dungeon_height,
            floor=self.current_floor,  # 現在の階層を渡す
        )
        self.dungeon_tiles = None

        # FOVの初期化
        self.fov_enabled = True
        self.fov_map = tcod.map.Map(
            width=self.dungeon_width, height=self.dungeon_height
        )
        self.visible = np.full(
            (self.dungeon_height, self.dungeon_width), fill_value=False, dtype=bool
        )
        self.explored = np.full(
            (self.dungeon_height, self.dungeon_width), fill_value=False, dtype=bool
        )

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

        # プレイヤーのインベントリ
        self.inventory = Inventory()

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

        # モンスター管理用のインスタンスを追加
        self.monster_spawner = None

        # アイテム管理用のインスタンスを追加
        self.item_spawner = ItemSpawner(self.current_floor)

    def _save_current_floor(self) -> None:
        """現在のフロアの状態を保存"""
        self.floor_data[self.current_floor] = {
            "dungeon_tiles": self.dungeon_tiles.copy(),
            "monster_spawner": self.monster_spawner,
            "item_spawner": self.item_spawner,
            "explored": self.explored.copy(),
            "up_pos": self.dungeon_gen.start_pos,
            "down_pos": self.dungeon_gen.end_pos,
        }

    def _load_floor(self, floor_number: int) -> None:
        """指定された階層のデータをロード"""
        # 新しい階層を生成する必要があるかチェック
        if (
            floor_number not in self.floor_data  # 初めて訪れる階
            or (floor_number > self.previous_floor)  # 下の階に降りる場合
            or (floor_number < self.previous_floor)
        ):  # 上の階に戻る場合
            # 新しい階層を生成
            dungeon = DungeonGenerator(
                width=self.engine.map_width,
                height=self.engine.map_height,
                floor=floor_number,
            )
            tiles, up_pos, down_pos = dungeon.generate()

            # モンスターとアイテムを生成
            monster_spawner = MonsterSpawner(floor_number)
            monster_spawner.spawn_monsters(tiles, dungeon.rooms)

            item_spawner = ItemSpawner(floor_number)
            item_spawner.spawn_items(tiles, dungeon.rooms)

            # 階層データを保存
            self.floor_data[floor_number] = {
                "tiles": tiles,
                "up_pos": up_pos,
                "down_pos": down_pos,
                "monster_spawner": monster_spawner,
                "item_spawner": item_spawner,
                "explored": np.full(
                    (self.engine.map_height, self.engine.map_width), False, dtype=bool
                ),
            }

        # 階層データをロード
        floor_data = self.floor_data[floor_number]
        self.dungeon_tiles = floor_data["tiles"]
        self.up_pos = floor_data["up_pos"]
        self.down_pos = floor_data["down_pos"]
        self.monster_spawner = floor_data["monster_spawner"]
        self.item_spawner = floor_data["item_spawner"]
        self.explored = floor_data["explored"]

        # プレイヤーの位置を設定
        if floor_number < self.previous_floor:  # 上の階に戻る場合
            self.player_x = self.down_pos[0]
            self.player_y = self.down_pos[1]
        else:  # 下の階に降りる場合
            self.player_x = self.up_pos[0]
            self.player_y = self.up_pos[1]

        # FOVを更新
        self._update_fov_map()
        self._compute_fov()

    def _generate_new_floor(self) -> None:
        """新しい階層に移動"""
        # 現在のフロアの状態を保存
        self._save_current_floor()

        # 新しいフロアを読み込む
        self._load_floor(self.current_floor)

    def _update_fov_map(self) -> None:
        """FOV計算用のマップを更新"""
        height, width = self.dungeon_tiles.shape
        self.fov_map = tcod.map.Map(width, height)

        for y in range(height):
            for x in range(width):
                self.fov_map.transparent[y, x] = self.dungeon_tiles[y, x].transparent
                self.fov_map.walkable[y, x] = self.dungeon_tiles[y, x].walkable

    def _compute_fov(self) -> None:
        """FOVを計算"""
        # FOVマップを更新
        self.fov_map.compute_fov(
            self.player_x,
            self.player_y,
            radius=10,
            light_walls=True,
            algorithm=tcod.constants.FOV_RESTRICTIVE,
        )

        # 可視領域を更新
        height, width = self.dungeon_tiles.shape
        self.visible = np.full((height, width), fill_value=False, dtype=bool)
        for y in range(height):
            for x in range(width):
                self.visible[y, x] = self.fov_map.fov[y, x]

        # 探索済み領域を更新
        if self.explored is None or self.explored.shape != self.visible.shape:
            self.explored = np.full_like(self.visible, False)
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

        # フロア番号を右上に表示
        floor_info = f"Floor: {self.current_floor}"

        self.engine.console.print(x=1, y=0, string=status_line1)
        self.engine.console.print(x=1, y=1, string=status_line2)
        # フロア番号を右上に表示（コンソールの幅から文字列の長さを引いて位置を調整）
        self.engine.console.print(
            x=self.engine.console.width - len(floor_info) - 1, y=0, string=floor_info
        )

    def _render_map(self) -> None:
        """マップの描画"""
        # マップの描画開始位置（ステータス表示の下）
        map_y_offset = 2

        # マップを描画
        for y in range(len(self.dungeon_tiles)):
            for x in range(len(self.dungeon_tiles[y])):
                tile = self.dungeon_tiles[y][x]

                # 隠し扉の特別処理（未発見の場合は壁と同じ色を使用）
                if isinstance(tile, SecretDoor) and tile.door_state == "secret":
                    wall_tile = Wall()
                    if not self.fov_enabled or self.visible[y, x]:
                        self.engine.console.print(
                            x, y + map_y_offset, tile.char, wall_tile.light
                        )
                    elif self.explored[y, x]:
                        self.engine.console.print(
                            x, y + map_y_offset, tile.char, wall_tile.dark
                        )
                    continue

                if not self.fov_enabled or self.visible[y, x]:
                    # FOV無効時または視界内のタイル
                    self.engine.console.print(
                        x, y + map_y_offset, tile.char, tile.light
                    )
                elif self.explored[y, x]:
                    # 既に探索済みのタイル
                    self.engine.console.print(x, y + map_y_offset, tile.char, tile.dark)

        # アイテムを描画（FOV無効時または視界内のみ）
        for item in self.item_spawner.items:
            if not self.fov_enabled or self.visible[item.y, item.x]:
                self.engine.console.print(
                    item.x, item.y + map_y_offset, item.char, item.color
                )

        # モンスターを描画（FOV無効時または視界内のみ）
        for monster in self.monster_spawner.monsters:
            if not self.fov_enabled or self.visible[monster.y, monster.x]:
                self.engine.console.print(
                    monster.x, monster.y + map_y_offset, monster.char, monster.color
                )

        # プレイヤーを描画
        self.engine.console.print(
            self.player_x, self.player_y + map_y_offset, "@", (255, 255, 255)
        )

    def _render_messages(self) -> None:
        """メッセージログを表示"""
        message_start_y = self.engine.console.height - 3
        for i, message in enumerate(self.message_log[-3:]):  # 最新の3メッセージを表示
            self.engine.console.print(x=1, y=message_start_y + i, string=message)

    def handle_key(self, event: tcod.event.KeyDown) -> Screen | None:
        """キー入力の処理"""
        # TABキーでFOVのトグル
        if event.sym == tcod.event.KeySym.TAB:
            self.fov_enabled = not self.fov_enabled
            return None

        # アイテムを拾う
        if event.sym == tcod.event.KeySym.g:
            self._handle_get()
            return None

        # 隠し扉を探す
        if event.sym == tcod.event.KeySym.s:
            self._handle_search()
            return None

        # 扉を開ける
        if event.sym == tcod.event.KeySym.o:
            self._handle_door_open()
            return None

        # 扉を閉める
        if event.sym == tcod.event.KeySym.c:
            self._handle_door_close()
            return None

        # 階段の処理
        if (
            event.sym == tcod.event.KeySym.GREATER
            or event.sym == tcod.event.KeySym.PERIOD
        ):  # > キーまたは . キー
            if isinstance(self.dungeon_tiles[self.player_y][self.player_x], StairsDown):
                self._descend_stairs()
                return None
            self.message_log.append("There are no stairs down here.")
            return None

        if (
            event.sym == tcod.event.KeySym.LESS or event.sym == tcod.event.KeySym.COMMA
        ):  # < キーまたは , キー
            if isinstance(self.dungeon_tiles[self.player_y][self.player_x], StairsUp):
                self._ascend_stairs()
                return None
            self.message_log.append("There are no stairs up here.")
            return None

        # 移動キーの処理
        if event.sym in (
            tcod.event.KeySym.UP,
            tcod.event.KeySym.k,
            tcod.event.KeySym.KP_8,
        ):  # 8
            if self._can_move_to(self.player_x, self.player_y - 1):
                self.player_y -= 1
        elif event.sym in (
            tcod.event.KeySym.DOWN,
            tcod.event.KeySym.j,
            tcod.event.KeySym.KP_2,
        ):  # 2
            if self._can_move_to(self.player_x, self.player_y + 1):
                self.player_y += 1
        elif event.sym in (
            tcod.event.KeySym.LEFT,
            tcod.event.KeySym.h,
            tcod.event.KeySym.KP_4,
        ):  # 4
            if self._can_move_to(self.player_x - 1, self.player_y):
                self.player_x -= 1
        elif event.sym in (
            tcod.event.KeySym.RIGHT,
            tcod.event.KeySym.l,
            tcod.event.KeySym.KP_6,
        ):  # 6
            if self._can_move_to(self.player_x + 1, self.player_y):
                self.player_x += 1
        # 斜め移動
        elif event.sym in (tcod.event.KeySym.y, tcod.event.KeySym.KP_7):  # 7: 左上
            if self._can_move_to(self.player_x - 1, self.player_y - 1):
                self.player_x -= 1
                self.player_y -= 1
        elif event.sym in (tcod.event.KeySym.u, tcod.event.KeySym.KP_9):  # 9: 右上
            if self._can_move_to(self.player_x + 1, self.player_y - 1):
                self.player_x += 1
                self.player_y -= 1
        elif event.sym in (tcod.event.KeySym.b, tcod.event.KeySym.KP_1):  # 1: 左下
            if self._can_move_to(self.player_x - 1, self.player_y + 1):
                self.player_x -= 1
                self.player_y += 1
        elif event.sym in (tcod.event.KeySym.n, tcod.event.KeySym.KP_3):  # 3: 右下
            if self._can_move_to(self.player_x + 1, self.player_y + 1):
                self.player_x += 1
                self.player_y += 1
        elif event.sym == tcod.event.KeySym.KP_5:  # 5: その場で待機
            pass  # 待機もターンを消費

        # 移動が成功した場合の処理
        if event.sym in (
            tcod.event.KeySym.UP,
            tcod.event.KeySym.DOWN,
            tcod.event.KeySym.LEFT,
            tcod.event.KeySym.RIGHT,
            tcod.event.KeySym.y,
            tcod.event.KeySym.u,
            tcod.event.KeySym.b,
            tcod.event.KeySym.n,
        ):
            # モンスターの更新
            self.monster_spawner.update_monsters(
                self.player_x, self.player_y, self.dungeon_tiles, self.fov_map
            )

            # 視界の更新
            self._compute_fov()

            # 隠し扉のヒントをチェック
            self._check_secret_door_hints()

    def _can_move_to(self, x: int, y: int) -> bool:
        """指定の位置に移動できるかを判定"""
        if not (
            0 <= x < len(self.dungeon_tiles[0]) and 0 <= y < len(self.dungeon_tiles)
        ):
            return False

        tile = self.dungeon_tiles[y][x]

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
            self.engine.game_over(
                self.player_stats, self.current_floor, f"Killed by {monster.name}"
            )

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
                if not (
                    0 <= x < len(self.dungeon_tiles[0])
                    and 0 <= y < len(self.dungeon_tiles)
                ):
                    continue

                tile = self.dungeon_tiles[y][x]

                # 通常の扉が閉じている場合
                if (isinstance(tile, Door) and tile.door_state == "closed") or (
                    isinstance(tile, SecretDoor) and tile.door_state == "closed"
                ):
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
                if not (
                    0 <= x < len(self.dungeon_tiles[0])
                    and 0 <= y < len(self.dungeon_tiles)
                ):
                    continue

                tile = self.dungeon_tiles[y][x]

                # 開いた扉（通常の扉または発見済みの隠し扉）を見つけた場合
                if (
                    isinstance(tile, Door)
                    or (isinstance(tile, SecretDoor) and tile.door_state != "secret")
                ) and tile.door_state == "open":
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
                if not (
                    0 <= x < len(self.dungeon_tiles[0])
                    and 0 <= y < len(self.dungeon_tiles)
                ):
                    continue

                tile = self.dungeon_tiles[y][x]

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
            if isinstance(item, Gold):
                self.player_stats["gold"] += item.amount
                self.message_log.append(f"You pick up {item.amount} gold pieces.")
            else:
                self.message_log.append(f"You pick up the {item.name}.")
                # TODO: インベントリに追加する処理を実装
            self.item_spawner.remove_item(item)
        else:
            self.message_log.append("There is nothing here to pick up.")

    def _check_secret_door_hints(self) -> None:
        """隠し扉の近くにいる場合、ヒントメッセージを表示"""
        # ヒントメッセージのリスト
        hint_messages = [
            "You notice a faint light through a crack in the wall...",
            "You feel a draft coming from somewhere...",
            "You hear faint laughter through the wall...",
        ]

        # 隣接する8方向をチェック
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                x = self.player_x + dx
                y = self.player_y + dy

                # マップ範囲内かチェック
                if not (
                    0 <= x < len(self.dungeon_tiles[0])
                    and 0 <= y < len(self.dungeon_tiles)
                ):
                    continue

                tile = self.dungeon_tiles[y][x]

                # 隠し扉（未発見）を見つけた場合
                if isinstance(tile, SecretDoor) and tile.door_state == "secret":
                    # ランダムなヒントメッセージを表示
                    self.message_log.append(random.choice(hint_messages))
                    return  # 1つ見つかれば終了

    def _descend_stairs(self) -> None:
        """階段を下る"""
        self.previous_floor = self.current_floor
        self.current_floor += 1
        self.message_log.append(f"You descend to floor {self.current_floor}.")
        self._generate_new_floor()

    def _ascend_stairs(self) -> None:
        """階段を上る"""
        if self.current_floor > 1:
            # 現在のフロアを一時的に保存
            temp_floor = self.current_floor
            # 移動先のフロアを設定
            self.current_floor -= 1
            # 移動元のフロアを previous_floor に設定
            self.previous_floor = temp_floor

            self.message_log.append(f"You ascend to floor {self.current_floor}.")
            self._generate_new_floor()
        else:
            # イェンダーの魔除けを持っているかチェック
            has_amulet = False
            for item in self.inventory.items:
                if isinstance(item, Item) and item.name == "The Amulet of Yendor":
                    has_amulet = True
                    break

            if has_amulet:
                self.message_log.append(
                    "You escaped with the Amulet of Yendor! You win!"
                )
                # TODO: ゲームクリア処理を実装
            else:
                self.message_log.append(
                    "You need the Amulet of Yendor to leave the dungeon."
                )

    def setup_new_game(self) -> None:
        """新しいゲームのセットアップ"""
        # 状態を初期化
        self.current_floor = 1
        self.previous_floor = 1
        self.floor_data.clear()  # 保存されているフロアデータをクリア

        # プレイヤーステータスを初期化
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

        # インベントリを初期化
        self.inventory = Inventory()

        # 装備を初期化
        self.equipment = {
            "weapon": "Dagger",
            "armor": "Leather Armor",
            "ring_left": "None",
            "ring_right": "None",
        }

        # メッセージログを初期化
        self.message_log = [
            "Welcome to PyRogue!",
            "Use vi keys (hjklyubn), arrow keys, or numpad (1-9) to move.",
            "Press ESC to return to menu.",
        ]

        # 最初のフロアを生成
        self._load_floor(self.current_floor)
