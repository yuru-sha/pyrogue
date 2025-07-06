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

from pyrogue.core.game_logic import GameLogic
from pyrogue.core.save_manager import SaveManager
from pyrogue.entities.actors.monster import Monster
from pyrogue.entities.actors.monster_spawner import MonsterSpawner
from pyrogue.entities.actors.player import Player
from pyrogue.entities.items.effects import EffectContext
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
    """Game Screen that implements EffectContext protocol."""

    """
    メインゲームのビュークラス。

    GameLogicから状態を取得し、画面への描画とユーザー入力の処理のみを担当します。
    ゲーム状態の管理はGameLogicに委譲され、このクラスは純粋なビューコンポーネントとして機能します。

    特徴:
        - GameLogicからの状態取得と描画
        - FOV（Field of View）システムの管理
        - ユーザー入力の解釈とGameLogicへの委譲
        - UI専用の状態管理（FOV設定など）

    Attributes:
        engine: ゲームエンジンインスタンス
        game_logic: ゲームロジック管理インスタンス
        fov_enabled: FOV表示の有効/無効
        fov_map: FOV計算用のマップ
        visible: 現在視界内のタイル
        explored: 探索済みタイル（GameLogicから取得）

    """

    def __init__(self, engine: Engine | None) -> None:
        """
        ゲームスクリーンを初期化。

        Args:
            engine: メインゲームエンジンのインスタンス（CLIモードの場合はNone）

        """
        self.engine = engine

        # ダンジョンサイズ（エンジンから取得、またはデフォルト値）
        if engine:
            self.dungeon_width = getattr(engine, "map_width", 80)
            self.dungeon_height = getattr(engine, "map_height", 45)
        else:
            # CLIモードでは固定値を使用
            self.dungeon_width = 80
            self.dungeon_height = 45

        # ゲームロジックを作成（状態管理はこちらで行う）
        self.game_logic = GameLogic(engine, self.dungeon_width, self.dungeon_height)

        # FOV関連（UI専用の状態）
        self.fov_enabled = True
        self.fov_map = tcod.map.Map(
            width=self.dungeon_width, height=self.dungeon_height
        )
        self.visible = np.full(
            (self.dungeon_height, self.dungeon_width), fill_value=False, dtype=bool
        )

        # セーブ/ロード管理（UI機能として残す）
        self.save_manager = SaveManager()

        # 互換性のためにGameLogicに自身への参照を設定
        self.game_logic.set_game_screen_reference(self)

    # EffectContextプロトコルの実装（GameLogicからの委譲）
    @property
    def player(self) -> Player:
        """プレイヤーオブジェクトへのアクセス。"""
        return self.game_logic.player

    @property
    def dungeon(self):
        """ダンジョンオブジェクトへのアクセス。"""
        return self._create_dungeon_object()

    @property
    def game_screen(self):
        """ゲームスクリーン自身へのアクセス。"""
        return self

    def _create_dungeon_object(self):
        """ダンジョンオブジェクトのプロキシを作成。"""

        class DungeonProxy:
            def __init__(self, game_screen):
                self.game_screen = game_screen

            @property
            def current_floor(self):
                return self.game_screen.game_logic.dungeon_manager.current_floor

            @property
            def tiles(self):
                current_floor = self.game_screen.game_logic.get_current_floor_data()
                return current_floor.tiles

            @property
            def width(self):
                return self.game_screen.dungeon_width

            @property
            def height(self):
                return self.game_screen.dungeon_height

            @property
            def explored(self):
                current_floor = self.game_screen.game_logic.get_current_floor_data()
                return current_floor.explored

            def get_blocking_entity_at(self, x, y):
                # モンスターがその位置にいるかチェック
                current_floor = self.game_screen.game_logic.get_current_floor_data()
                return current_floor.monster_spawner.get_monster_at(x, y)

        return DungeonProxy(self)

    def _update_fov(self) -> None:
        """FOVマップとプレイヤーの視界を更新"""
        current_floor = self.game_logic.get_current_floor_data()
        player = self.game_logic.player

        # FOVマップを更新
        self.fov_map = tcod.map.Map(
            width=self.dungeon_width, height=self.dungeon_height
        )
        for y in range(current_floor.tiles.shape[0]):
            for x in range(current_floor.tiles.shape[1]):
                tile = current_floor.tiles[y, x]
                self.fov_map.transparent[y, x] = tile.transparent
                self.fov_map.walkable[y, x] = tile.walkable

        # FOVを計算
        self.fov_map.compute_fov(
            player.x,
            player.y,
            radius=player.light_radius,
            light_walls=True,
            algorithm=tcod.constants.FOV_RESTRICTIVE,
        )

        # 可視領域を更新
        self.visible = np.full(
            (self.dungeon_height, self.dungeon_width), fill_value=False, dtype=bool
        )
        for y in range(current_floor.tiles.shape[0]):
            for x in range(current_floor.tiles.shape[1]):
                self.visible[y, x] = self.fov_map.fov[y, x]

        # 探索済み領域を更新（GameLogicから取得した探索状態と統合）
        current_floor.explored |= self.visible

    def _save_current_floor(self) -> None:
        """現在のフロアの状態を保存"""
        self.floor_data[self.current_floor] = {
            "dungeon_tiles": self.game_logic.get_current_floor_data().tiles.copy()
            if self.game_logic.get_current_floor_data().tiles is not None
            else None,
            "monster_spawner": self.monster_spawner,
            "item_spawner": self.item_spawner,
            "explored": self.explored.copy() if self.explored is not None else None,
            "up_pos": getattr(self.dungeon_gen, "start_pos", None),
            "down_pos": getattr(self.dungeon_gen, "end_pos", None),
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
            if self.engine:
                dungeon_width = self.engine.map_width
                dungeon_height = self.engine.map_height
            else:
                # CLIモードでは固定値を使用
                dungeon_width = 80
                dungeon_height = 45

            dungeon = DungeonGenerator(
                width=dungeon_width,
                height=dungeon_height,
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
                "explored": np.full((dungeon_height, dungeon_width), False, dtype=bool),
            }

        # 階層データをロード
        floor_data = self.floor_data[floor_number]
        self.game_logic.get_current_floor_data().tiles = floor_data["tiles"]
        self.up_pos = floor_data["up_pos"]
        self.down_pos = floor_data["down_pos"]
        self.monster_spawner = floor_data["monster_spawner"]
        self.item_spawner = floor_data["item_spawner"]
        self.explored = floor_data["explored"]

        # プレイヤーの位置を設定
        if floor_number < self.previous_floor:  # 上の階に戻る場合
            self.game_logic.player.x = self.down_pos[0]
            self.game_logic.player.y = self.down_pos[1]
        else:  # 下の階に降りる場合
            self.game_logic.player.x = self.up_pos[0]
            self.game_logic.player.y = self.up_pos[1]

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
        height, width = self.game_logic.get_current_floor_data().tiles.shape
        self.fov_map = tcod.map.Map(width, height)

        for y in range(height):
            for x in range(width):
                self.fov_map.transparent[y, x] = (
                    self.game_logic.get_current_floor_data().tiles[y, x].transparent
                )
                self.fov_map.walkable[y, x] = (
                    self.game_logic.get_current_floor_data().tiles[y, x].walkable
                )

    def _compute_fov(self) -> None:
        """FOVを計算"""
        # プレイヤーの現在の視野範囲を使用
        radius = self.engine.player.light_radius

        # FOVマップを更新
        self.fov_map.compute_fov(
            self.game_logic.player.x,
            self.game_logic.player.y,
            radius=radius,
            light_walls=True,
            algorithm=tcod.constants.FOV_RESTRICTIVE,
        )

        # 可視領域を更新
        height, width = self.game_logic.get_current_floor_data().tiles.shape
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
        if self.engine:  # CLIモードでは engine が None の場合がある
            self.engine.console = console

    def render(self) -> None:
        """画面の描画"""
        if not self.engine:  # CLIモードでは engine が None
            return
        self.engine.console.clear()

        # ステータス表示（上部2行）
        self._render_status()

        # マップ表示（中央部分）
        self._render_map()

        # メッセージログ（下部3行）
        self._render_messages()

    def _render_status(self) -> None:
        """ステータス情報を表示"""
        player = self.game_logic.player

        # 1行目: レベル、HP、攻撃力、防御力、空腹度、経験値、所持金
        status_line1 = (
            f"Lv:{player.level} "
            f"HP:{player.hp}/{player.max_hp} "
            f"Atk:{player.get_attack()} "
            f"Def:{player.get_defense()} "
            f"Hunger:{player.hunger}% "
            f"Exp:{player.exp} "
            f"Gold:{player.gold}"
        )

        # 2行目: 装備情報
        inventory = self.game_logic.inventory
        status_line2 = (
            f"Weap:{inventory.get_equipped_item_name('weapon')} "
            f"Armor:{inventory.get_equipped_item_name('armor')} "
            f"Ring(L):{inventory.get_equipped_item_name('ring_left')} "
            f"Ring(R):{inventory.get_equipped_item_name('ring_right')}"
        )

        # 地下階層番号を右上に表示
        floor_info = f"B{self.game_logic.dungeon_manager.current_floor}F"

        if self.engine and self.engine.console:
            self.engine.console.print(x=1, y=0, string=status_line1)
            self.engine.console.print(x=1, y=1, string=status_line2)
            # 地下階層番号を右上に表示
            self.engine.console.print(
                x=self.engine.console.width - len(floor_info) - 1,
                y=0,
                string=floor_info,
            )

    def _render_map(self) -> None:
        """マップの描画"""
        if not self.engine or not self.engine.console:
            return

        # GameLogicから現在の階層データを取得
        current_floor = self.game_logic.get_current_floor_data()
        player = self.game_logic.player

        # マップの描画開始位置（ステータス表示の下）
        map_y_offset = 2

        # マップを描画
        for y in range(current_floor.tiles.shape[0]):
            for x in range(current_floor.tiles.shape[1]):
                tile = current_floor.tiles[y][x]

                # 隠し扉の特別処理（未発見の場合は壁と同じ色を使用）
                if isinstance(tile, SecretDoor) and tile.door_state == "secret":
                    wall_tile = Wall()
                    if not self.fov_enabled or self.visible[y, x]:
                        self.engine.console.print(
                            x, y + map_y_offset, tile.char, wall_tile.light
                        )
                    elif current_floor.explored[y, x]:
                        self.engine.console.print(
                            x, y + map_y_offset, tile.char, wall_tile.dark
                        )
                    continue

                if not self.fov_enabled or self.visible[y, x]:
                    # FOV無効時または視界内のタイル
                    self.engine.console.print(
                        x, y + map_y_offset, tile.char, tile.light
                    )
                elif current_floor.explored[y, x]:
                    # 既に探索済みのタイル
                    self.engine.console.print(x, y + map_y_offset, tile.char, tile.dark)

        # アイテムを描画（FOV無効時または視界内のみ）
        for item in current_floor.item_spawner.items:
            if not self.fov_enabled or self.visible[item.y, item.x]:
                self.engine.console.print(
                    item.x, item.y + map_y_offset, item.char, item.color
                )

        # モンスターを描画（FOV無効時または視界内のみ）
        for monster in current_floor.monster_spawner.monsters:
            if not self.fov_enabled or self.visible[monster.y, monster.x]:
                self.engine.console.print(
                    monster.x, monster.y + map_y_offset, monster.char, monster.color
                )

        # プレイヤーを描画
        self.engine.console.print(
            player.x, player.y + map_y_offset, "@", (255, 255, 255)
        )

    def _render_messages(self) -> None:
        """メッセージログを表示"""
        if not self.engine or not self.engine.console:
            return

        message_start_y = self.engine.console.height - 3
        # GameLogicからメッセージログを取得
        messages = self.game_logic.message_log[-3:]  # 最新の3メッセージを表示
        for i, message in enumerate(messages):
            self.engine.console.print(x=1, y=message_start_y + i, string=message)

    def handle_key(self, event: tcod.event.KeyDown) -> None:
        """キー入力の処理"""
        # TABキーでFOVのトグル
        if event.sym == tcod.event.KeySym.TAB:
            self.fov_enabled = not self.fov_enabled
            return

        # アイテムを拾う
        if event.sym == tcod.event.KeySym.G:
            message = self.game_logic.handle_get_item()
            if message:
                self.game_logic.add_message(message)
            return

        # 隠し扉を探す
        if event.sym == tcod.event.KeySym.S:
            message = self.game_logic.handle_search()
            self.game_logic.add_message(message)
            # FOVを更新（隠し扉発見時）
            self._update_fov()
            return

        # 扉を開ける
        if event.sym == tcod.event.KeySym.O:
            message = self.game_logic.handle_door_open()
            self.game_logic.add_message(message)
            # FOVを更新（ドア開閉時）
            self._update_fov()
            return

        # 扉を閉める
        if event.sym == tcod.event.KeySym.C:
            message = self.game_logic.handle_door_close()
            self.game_logic.add_message(message)
            # FOVを更新（ドア開閉時）
            self._update_fov()
            return

        # アイテムを取得（,キー）の処理を削除（階段の上り処理と重複するため）

        # アイテムをドロップ
        if event.sym == tcod.event.KeySym.D:
            message = self.game_logic.handle_drop_item()
            self.game_logic.add_message(message)
            return

        # インベントリを開く
        if event.sym == tcod.event.KeySym.I:
            from pyrogue.core.game_states import GameStates

            if self.engine:
                self.engine.state = GameStates.SHOW_INVENTORY
            return

        # ゲームを保存
        if event.sym == tcod.event.KeySym.S and event.mod & tcod.event.KMOD_CTRL:
            self.save_game()
            return

        # ゲームを読み込み
        if event.sym == tcod.event.KeySym.L and event.mod & tcod.event.KMOD_CTRL:
            if self.save_manager.has_save_file():
                self.load_game()
            else:
                self.game_logic.add_message("No save file found.")
            return

        # 階段の処理
        if (
            event.sym == tcod.event.KeySym.GREATER
            or event.sym == tcod.event.KeySym.PERIOD
        ):  # > キーまたは . キー
            if isinstance(
                self.game_logic.get_current_floor_data().tiles[
                    self.game_logic.player.y
                ][self.game_logic.player.x],
                StairsDown,
            ):
                success = self.game_logic.descend_stairs()
                if success:
                    self._update_fov()  # FOVを更新
                return
            self.game_logic.add_message("There are no stairs down here.")
            return

        if (
            event.sym == tcod.event.KeySym.LESS
            or event.sym == tcod.event.KeySym.COMMA
        ):  # < キーまたは , キー
            if isinstance(
                self.game_logic.get_current_floor_data().tiles[
                    self.game_logic.player.y
                ][self.game_logic.player.x],
                StairsUp,
            ):
                success = self.game_logic.ascend_stairs()
                if success:
                    self._update_fov()  # FOVを更新
                return
            self.game_logic.add_message("There are no stairs up here.")
            return

        # 移動キーの処理
        moved = False
        if event.sym in (
            tcod.event.KeySym.UP,
            tcod.event.KeySym.K,
            tcod.event.KeySym.KP_8,
        ):  # 8
            moved = self.game_logic.handle_player_move(0, -1)
        elif event.sym in (
            tcod.event.KeySym.DOWN,
            tcod.event.KeySym.J,
            tcod.event.KeySym.KP_2,
        ):  # 2
            moved = self.game_logic.handle_player_move(0, 1)
        elif event.sym in (
            tcod.event.KeySym.LEFT,
            tcod.event.KeySym.H,
            tcod.event.KeySym.KP_4,
        ):  # 4
            moved = self.game_logic.handle_player_move(-1, 0)
        elif event.sym in (
            tcod.event.KeySym.RIGHT,
            tcod.event.KeySym.L,
            tcod.event.KeySym.KP_6,
        ):  # 6
            moved = self.game_logic.handle_player_move(1, 0)
        # 斜め移動
        elif event.sym in (tcod.event.KeySym.Y, tcod.event.KeySym.KP_7):  # 7: 左上
            moved = self.game_logic.handle_player_move(-1, -1)
        elif event.sym in (tcod.event.KeySym.U, tcod.event.KeySym.KP_9):  # 9: 右上
            moved = self.game_logic.handle_player_move(1, -1)
        elif event.sym in (tcod.event.KeySym.B, tcod.event.KeySym.KP_1):  # 1: 左下
            moved = self.game_logic.handle_player_move(-1, 1)
        elif event.sym in (tcod.event.KeySym.N, tcod.event.KeySym.KP_3):  # 3: 右下
            moved = self.game_logic.handle_player_move(1, 1)
        elif event.sym == tcod.event.KeySym.KP_5:  # 5: その場で待機
            moved = True  # 待機もターンを消費

        # 移動が成功した場合の処理
        if moved:
            # 視界の更新
            self._update_fov()

            # 隠し扉のヒントをチェック
            self._check_secret_door_hints()

    def _can_move_to(self, x: int, y: int) -> bool:
        """指定の位置に移動できるかを判定"""
        if not (
            0 <= x < len(self.game_logic.get_current_floor_data().tiles[0])
            and 0 <= y < len(self.game_logic.get_current_floor_data().tiles)
        ):
            return False

        tile = self.game_logic.get_current_floor_data().tiles[y][x]

        # モンスターとの衝突判定
        monster = self.monster_spawner.get_monster_at(x, y)
        if monster:
            # モンスターがいる場合は戦闘を開始
            self.game_logic.handle_combat(monster)
            return False  # 移動は行わない

        return tile.walkable

    def save_game(self) -> bool:
        """
        ゲーム状態を保存

        Returns:
            bool: 保存に成功した場合はTrue

        """
        # 現在のフロア状態を保存
        self._save_current_floor()

        # ゲームデータを準備
        game_data = {
            "self.game_logic.player.x": self.game_logic.player.x,
            "self.game_logic.player.y": self.game_logic.player.y,
            "current_floor": self.current_floor,
            "previous_floor": self.previous_floor,
            "player_stats": self.player_stats.copy(),
            "equipment": self.equipment.copy(),
            "inventory_items": self._serialize_inventory(),
            "floor_data": self._serialize_floor_data(),
            "message_log": self.message_log.copy(),
        }

        if self.save_manager.save_game_state(game_data):
            self.game_logic.add_message("Game saved successfully.")
            return True
        else:
            self.game_logic.add_message("Failed to save game.")
            return False

    def load_game(self) -> bool:
        """
        ゲーム状態を読み込み

        Returns:
            bool: 読み込みに成功した場合はTrue

        """
        game_data = self.save_manager.load_game_state()
        if game_data is None:
            self.game_logic.add_message("No save file found or corrupted.")
            return False

        try:
            # ゲーム状態を復元
            self.game_logic.player.x = game_data["player.x"]
            self.game_logic.player.y = game_data["player.y"]
            self.current_floor = game_data["current_floor"]
            self.previous_floor = game_data["previous_floor"]
            self.player_stats = game_data["player_stats"]
            self.equipment = game_data["equipment"]
            self.message_log = game_data["message_log"]

            # インベントリを復元
            self._deserialize_inventory(game_data["inventory_items"])

            # フロアデータを復元
            self._deserialize_floor_data(game_data["floor_data"])

            # 現在のフロアを読み込み
            self._load_floor(self.current_floor)

            self.game_logic.add_message("Game loaded successfully.")
            return True

        except Exception as e:
            self.game_logic.add_message(f"Failed to load game: {e}")
            return False

    def _serialize_inventory(self) -> list:
        """
        インベントリをシリアライズ可能な形式に変換

        Returns:
            list: シリアライズされたアイテムリスト

        """
        serialized_items = []
        for item in self.game_logic.inventory.items:
            item_data = {
                "class_name": item.__class__.__name__,
                "name": item.name,
                "x": item.x,
                "y": item.y,
                "char": item.char,
                "color": item.color,
                "stackable": item.stackable,
                "stack_count": item.stack_count,
            }

            # タイプ固有のデータを追加
            if hasattr(item, "attack"):
                item_data["attack"] = item.attack
            if hasattr(item, "defense"):
                item_data["defense"] = item.defense
            if hasattr(item, "effect"):
                item_data["effect"] = item.effect
            if hasattr(item, "bonus"):
                item_data["bonus"] = item.bonus
            if hasattr(item, "power"):
                item_data["power"] = item.power
            if hasattr(item, "nutrition"):
                item_data["nutrition"] = item.nutrition
            if hasattr(item, "amount"):
                item_data["amount"] = item.amount

            serialized_items.append(item_data)

        return serialized_items

    def _deserialize_inventory(self, serialized_items: list) -> None:
        """
        シリアライズされたインベントリを復元

        Args:
            serialized_items: シリアライズされたアイテムリスト

        """
        self.game_logic.inventory.items.clear()

        for item_data in serialized_items:
            item = self._create_item_from_data(item_data)
            if item:
                self.game_logic.inventory.items.append(item)

    def _create_item_from_data(self, item_data: dict):
        """
        アイテムデータからアイテムインスタンスを作成

        Args:
            item_data: アイテムデータ

        Returns:
            作成されたアイテムインスタンス

        """
        from pyrogue.entities.items.item import (
            Armor,
            Food,
            Gold,
            Potion,
            Ring,
            Scroll,
            Weapon,
        )

        class_name = item_data["class_name"]
        x, y = item_data["x"], item_data["y"]
        name = item_data["name"]

        if class_name == "Weapon":
            item = Weapon(x, y, name, item_data.get("attack", 0))
        elif class_name == "Armor":
            item = Armor(x, y, name, item_data.get("defense", 0))
        elif class_name == "Ring":
            item = Ring(
                x, y, name, item_data.get("effect", ""), item_data.get("bonus", 0)
            )
        elif class_name == "Scroll":
            item = Scroll(x, y, name, item_data.get("effect", ""))
        elif class_name == "Potion":
            item = Potion(
                x, y, name, item_data.get("effect", ""), item_data.get("power", 0)
            )
        elif class_name == "Food":
            item = Food(x, y, name, item_data.get("nutrition", 0))
        elif class_name == "Gold":
            item = Gold(x, y, item_data.get("amount", 1))
        else:
            return None

        item.stack_count = item_data.get("stack_count", 1)
        return item

    def _serialize_floor_data(self) -> dict:
        """
        フロアデータをシリアライズ可能な形式に変換

        Returns:
            dict: シリアライズされたフロアデータ

        """
        # 簡易実装 - 基本的なフロアデータのみ保存
        return {
            floor_num: {
                "explored": data.get("explored", []).tolist()
                if hasattr(data.get("explored", []), "tolist")
                else data.get("explored", []),
                "up_pos": data.get("up_pos"),
                "down_pos": data.get("down_pos"),
            }
            for floor_num, data in self.floor_data.items()
        }

    def _deserialize_floor_data(self, serialized_data: dict) -> None:
        """
        シリアライズされたフロアデータを復元

        Args:
            serialized_data: シリアライズされたフロアデータ

        """
        import numpy as np

        self.floor_data = {}
        for floor_num, data in serialized_data.items():
            floor_data = {
                "up_pos": data.get("up_pos"),
                "down_pos": data.get("down_pos"),
            }

            # exploredデータを復元
            explored_data = data.get("explored")
            if explored_data:
                floor_data["explored"] = np.array(explored_data, dtype=bool)

            self.floor_data[int(floor_num)] = floor_data

    def check_player_death(self) -> None:
        """
        プレイヤーの死亡をチェックし、パーマデスを処理

        """
        if self.game_logic.player.hp <= 0:
            # パーマデスを発動
            game_data = {
                "player_stats": self.player_stats,
            }
            self.save_manager.trigger_permadeath_on_death(game_data)
            self.game_logic.add_message(
                "You have died. Your save data has been deleted."
            )

    def _auto_pickup(self) -> None:
        """プレイヤーの現在位置でアイテムを自動でピックアップ"""
        current_floor = self.game_logic.get_current_floor_data()
        item = current_floor.item_spawner.get_item_at(
            self.game_logic.player.x, self.game_logic.player.y
        )
        if item:
            if isinstance(item, Gold):
                # 金貨は常に自動でピックアップ
                self.game_logic.player.gold += item.amount
                self.game_logic.add_message(f"You pick up {item.amount} gold pieces.")
                current_floor.item_spawner.remove_item(item)
            else:
                # その他のアイテムも自動でピックアップを試行
                if self.game_logic.inventory.add_item(item):
                    pickup_message = item.pick_up()
                    self.game_logic.add_message(pickup_message)
                    current_floor.item_spawner.remove_item(item)
                else:
                    # インベントリが満杯の場合はメッセージのみ
                    self.game_logic.add_message(
                        f"There is {item.name} here, but your pack is full."
                    )

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

                x = self.game_logic.player.x + dx
                y = self.game_logic.player.y + dy

                # マップ範囲内かチェック
                current_floor = self.game_logic.get_current_floor_data()
                if not (
                    0 <= x < current_floor.tiles.shape[1]
                    and 0 <= y < current_floor.tiles.shape[0]
                ):
                    continue

                tile = current_floor.tiles[y][x]

                # 隠し扉（未発見）を見つけた場合
                if isinstance(tile, SecretDoor) and tile.door_state == "secret":
                    # ランダムなヒントメッセージを表示
                    self.game_logic.add_message(random.choice(hint_messages))
                    return  # 1つ見つかれば終了

    def _descend_stairs(self) -> None:
        """階段を下る"""
        self.previous_floor = self.current_floor
        self.current_floor += 1
        self.game_logic.add_message(f"You descend to B{self.current_floor}F.")
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

            self.game_logic.add_message(f"You ascend to B{self.current_floor}F.")
            self._generate_new_floor()
        else:
            # イェンダーの魔除けを持っているかチェック
            has_amulet = False
            for item in self.game_logic.inventory.items:
                if isinstance(item, Item) and item.name == "The Amulet of Yendor":
                    has_amulet = True
                    break

            if has_amulet:
                self.game_logic.add_message(
                    "You escaped with the Amulet of Yendor! You win!"
                )
                # ゲームクリア処理
                if self.engine:  # CLIモードでは engine が None の場合がある
                    player_stats = {
                        "level": self.player.level,
                        "hp": self.player.hp,
                        "max_hp": self.player.max_hp,
                        "exp": self.player.exp,
                        "gold": self.player.gold,
                        "attack": self.player.get_attack(),
                        "defense": self.player.get_defense(),
                        "hunger": self.player.hunger,
                    }
                    self.engine.victory(player_stats, self.current_floor)
            else:
                self.game_logic.add_message(
                    "You need the Amulet of Yendor to leave the dungeon."
                )

    def setup_new_game(self) -> None:
        """新しいゲームのセットアップ"""
        # GameLogicに委譲してゲーム状態を初期化
        self.game_logic.setup_new_game()

        # FOVを更新
        self._update_fov()

    # CLI用のメソッドを追加
    def try_move_player(self, dx: int, dy: int) -> bool:
        """
        プレイヤーの移動を試行（CLI用）。

        Args:
            dx: X方向の移動量
            dy: Y方向の移動量

        Returns:
            移動が成功したかどうか
        """
        # このメソッドはCLIモード用の互換性のため、GameLogicに委譲
        return self.game_logic.handle_player_move(dx, dy)

    def try_attack_adjacent_enemy(self) -> bool:
        """
        隣接する敵を攻撃（CLI用）。

        Returns:
            攻撃が成功したかどうか
        """
        # 隣接する8方向をチェック
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                x = self.game_logic.player.x + dx
                y = self.game_logic.player.y + dy

                current_floor = self.game_logic.get_current_floor_data()
                monster = current_floor.monster_spawner.get_monster_at(x, y)
                if monster:
                    self.game_logic.handle_combat(monster)
                    return True

        return False

    def try_use_item(self, item_name: str) -> bool:
        """
        アイテムを使用（CLI用）。

        Args:
            item_name: 使用するアイテム名

        Returns:
            使用が成功したかどうか
        """
        # インベントリから該当するアイテムを検索
        for item in self.game_logic.inventory.items:
            if item.name.lower() == item_name.lower():
                # 新しいeffectシステムを使用
                success = self.game_logic.player.use_item(item, context=self)
                if success:
                    self.game_logic.add_message(f"You used {item.name}.")
                    return True
                else:
                    self.game_logic.add_message(f"You cannot use {item.name}.")
                    return False

        self.game_logic.add_message(f"You don't have {item_name}.")
        return False

    def get_nearby_enemies(self) -> list:
        """
        周囲の敵を取得（CLI用）。

        Returns:
            周囲にいる敵のリスト
        """
        enemies = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                x = self.game_logic.player.x + dx
                y = self.game_logic.player.y + dy

                current_floor = self.game_logic.get_current_floor_data()
                monster = current_floor.monster_spawner.get_monster_at(x, y)
                if monster:
                    enemies.append(monster)

        return enemies

    def check_game_over(self) -> bool:
        """
        ゲームオーバー状態をチェック（CLI用）。

        Returns:
            ゲームオーバーかどうか
        """
        return self.game_logic.player.hp <= 0

    def check_victory(self) -> bool:
        """
        勝利条件をチェック（CLI用）。

        Returns:
            勝利しているかどうか
        """
        # イェンダーの魔除けを持っているかチェック
        for item in self.game_logic.inventory.items:
            if isinstance(item, Item) and item.name == "The Amulet of Yendor":
                return True
        return False

    def process_enemy_turns(self) -> None:
        """
        敵のターンを処理（CLI用）。

        現在はモンスターAIのTODOとしてある。
        """
        # TODO: モンスターAIの実装
        pass
