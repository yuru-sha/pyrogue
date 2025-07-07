"""
リファクタリングされたゲームロジックモジュール。

このモジュールは、元のGameLogicから責務を分離し、
各マネージャーに処理を委譲する構造になっています。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrogue.core.managers.combat_manager import CombatManager
from pyrogue.core.managers.game_context import GameContext
from pyrogue.core.managers.monster_ai_manager import MonsterAIManager
from pyrogue.core.managers.turn_manager import TurnManager
from pyrogue.entities.actors.inventory import Inventory
from pyrogue.entities.actors.player import Player
from pyrogue.map.dungeon_manager import DungeonManager

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine
    from pyrogue.entities.actors.monster import Monster
    from pyrogue.ui.screens.game_screen import GameScreen


class GameLogic:
    """
    リファクタリングされたゲームロジック管理クラス。

    各責務を専用のマネージャーに委譲し、
    自身はマネージャー間の調整役に徹します。

    Attributes:
        engine: ゲームエンジンインスタンス
        player: プレイヤーインスタンス
        inventory: プレイヤーのインベントリ
        message_log: ゲームメッセージログ
        dungeon_manager: ダンジョン管理インスタンス
        context: 共有ゲームコンテキスト
        combat_manager: 戦闘処理マネージャー
        turn_manager: ターン管理マネージャー
        monster_ai_manager: モンスターAIマネージャー
    """

    def __init__(
        self,
        engine: Engine | None = None,
        dungeon_width: int = 80,
        dungeon_height: int = 45,
    ) -> None:
        """
        ゲームロジックを初期化。

        Args:
            engine: ゲームエンジンインスタンス（CLIモードではNone）
            dungeon_width: ダンジョンの幅
            dungeon_height: ダンジョンの高さ
        """
        self.engine = engine

        # ゲーム状態を直接管理
        self.player = Player(x=0, y=0)
        self.inventory = Inventory()
        self.message_log: list[str] = [
            "Welcome to PyRogue!",
            "Use vi keys (hjklyubn), arrow keys, or numpad (1-9) to move.",
            "Press ESC to return to menu.",
        ]

        # ダンジョン管理
        self.dungeon_manager = DungeonManager(dungeon_width, dungeon_height)

        # 共有コンテキストを作成
        self.context = GameContext(
            player=self.player,
            inventory=self.inventory,
            dungeon_manager=self.dungeon_manager,
            message_log=self.message_log,
            engine=engine
        )

        # 各マネージャーを初期化
        self.combat_manager = CombatManager()
        self.turn_manager = TurnManager()
        self.monster_ai_manager = MonsterAIManager()

        # コンテキストにマネージャーへの参照を追加
        self.context.monster_ai_manager = self.monster_ai_manager

        # GameScreen参照（段階的移行用）
        self.game_screen: GameScreen | None = None

    def setup_new_game(self) -> None:
        """新しいゲームをセットアップ。"""
        # 初期装備の設定
        self._setup_initial_equipment()

        # ダンジョンの生成
        self.dungeon_manager.set_current_floor(1)

        # プレイヤーの開始位置を設定
        floor_data = self.dungeon_manager.get_current_floor_data()
        if floor_data and hasattr(floor_data, 'start_pos'):
            self.player.x, self.player.y = floor_data.start_pos

        self.add_message("You enter the dungeon. Your quest begins!")

    def _setup_initial_equipment(self) -> None:
        """初期装備を設定。"""
        # 基本的な初期装備（アイテムシステムと連携時に実装）
        pass

    # EffectContext用プロパティ
    @property
    def dungeon(self):
        """EffectContext用のダンジョンプロパティ。"""
        return self.get_current_floor_data()

    def set_game_screen_reference(self, game_screen: GameScreen) -> None:
        """GameScreenへの参照を設定（段階的移行用）。"""
        self.game_screen = game_screen
        self.context.game_screen = game_screen

    # 移動処理（MovementManagerに委譲予定）
    def handle_player_move(self, dx: int, dy: int) -> bool:
        """
        プレイヤーの移動処理。

        Args:
            dx: X方向の移動量
            dy: Y方向の移動量

        Returns:
            移動が成功した場合True
        """
        # ターン管理から行動可能かチェック
        if not self.turn_manager.can_act(self.player):
            self.add_message("You are paralyzed and cannot move!")
            return False

        # 混乱状態のチェック
        if self.turn_manager.is_confused(self.player):
            # ランダムな方向に移動
            import random
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            self.add_message("You are confused and move randomly!")

        new_x = self.player.x + dx
        new_y = self.player.y + dy

        # 移動可能性チェック
        if not self._can_move_to(new_x, new_y):
            return False

        # 斜め移動の場合、角抜け（Corner Cutting）を防止（一時的に無効化）
        # if dx != 0 and dy != 0:  # 斜め移動
        #     if not self._can_diagonal_move(self.player.x, self.player.y, dx, dy):
        #         return False

        # モンスターとの戦闘チェック
        monster = self._get_monster_at(new_x, new_y)
        if monster:
            return self.combat_manager.handle_player_combat(monster, self.context)

        # 移動実行
        self.player.x = new_x
        self.player.y = new_y

        # 移動後の処理
        self._handle_post_move_events()

        # ターン進行
        self.turn_manager.process_turn(self.context)

        return True

    def _can_move_to(self, x: int, y: int) -> bool:
        """移動可能性をチェック。"""
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return False

        # 境界チェック
        if (x < 0 or y < 0 or
            y >= floor_data.tiles.shape[0] or
            x >= floor_data.tiles.shape[1]):
            return False

        # タイルチェック
        tile = floor_data.tiles[y, x]
        return getattr(tile, 'walkable', False)

    def _can_diagonal_move(self, from_x: int, from_y: int, dx: int, dy: int) -> bool:
        """
        斜め移動が可能かチェック（角抜け防止）。

        真の角抜けを防ぐため、斜めのコーナーが完全に閉じられている場合のみ移動を制限。
        一方でも通行可能な場合は移動を許可（通常のローグライク動作）。

        Args:
            from_x: 移動元X座標
            from_y: 移動元Y座標
            dx: X方向の移動量
            dy: Y方向の移動量

        Returns:
            斜め移動が可能な場合True
        """
        # 経由する2つのマスをチェック
        path1_x, path1_y = from_x + dx, from_y  # 水平方向の経由マス
        path2_x, path2_y = from_x, from_y + dy  # 垂直方向の経由マス

        path1_walkable = self._can_move_to(path1_x, path1_y)
        path2_walkable = self._can_move_to(path2_x, path2_y)

        # 両方のマスが通行不可能な場合のみ斜め移動を禁止（角抜け防止）
        # どちらか一方でも通行可能なら移動許可
        return path1_walkable or path2_walkable

    def _get_monster_at(self, x: int, y: int) -> Monster | None:
        """指定座標のモンスターを取得。"""
        floor_data = self.get_current_floor_data()
        if not floor_data or not hasattr(floor_data, 'monster_spawner'):
            return None

        return floor_data.monster_spawner.get_monster_at(x, y)

    def _handle_post_move_events(self) -> None:
        """移動後のイベント処理。"""
        # トラップチェック
        self._check_traps()

        # アイテム自動取得
        self._auto_pickup_gold_only()

        # 階段チェック
        self._check_stairs()

    def _check_traps(self) -> None:
        """トラップチェック。"""
        floor_data = self.get_current_floor_data()
        if not floor_data or not hasattr(floor_data, 'trap_manager'):
            return

        # トラップ処理はTrapManagerに委譲
        trap_manager = floor_data.trap_manager
        if hasattr(trap_manager, 'check_player_traps'):
            trap_manager.check_player_traps(self.player, self.context)

    def _auto_pickup_gold_only(self) -> None:
        """金貨の自動取得。"""
        floor_data = self.get_current_floor_data()
        if not floor_data or not hasattr(floor_data, 'item_spawner'):
            return

        items_at_pos = [
            item for item in floor_data.item_spawner.items
            if item.x == self.player.x and item.y == self.player.y
        ]

        for item in items_at_pos:
            if hasattr(item, 'item_type') and item.item_type == "GOLD":
                self.player.gold += getattr(item, 'amount', 1)
                floor_data.item_spawner.items.remove(item)
                self.add_message(f"You picked up {getattr(item, 'amount', 1)} gold.")

    def _check_stairs(self) -> None:
        """階段の存在チェック。"""
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return

        tile = floor_data.tiles[self.player.y, self.player.x]

        if hasattr(tile, '__class__'):
            from pyrogue.map.tile import StairsDown, StairsUp

            if isinstance(tile, StairsDown):
                self.add_message("You see stairs leading down. Press '>' to descend.")
            elif isinstance(tile, StairsUp):
                self.add_message("You see stairs leading up. Press '<' to ascend.")

    # アイテム処理（ItemManagerに委譲予定）
    def handle_get_item(self) -> str | None:
        """アイテム取得処理。"""
        floor_data = self.get_current_floor_data()
        if not floor_data or not hasattr(floor_data, 'item_spawner'):
            return None

        items_at_pos = [
            item for item in floor_data.item_spawner.items
            if item.x == self.player.x and item.y == self.player.y
        ]

        if not items_at_pos:
            return None

        # 最初のアイテムを取得
        item = items_at_pos[0]

        # ゴールドの場合は直接プレイヤーのゴールドに追加
        if hasattr(item, 'item_type') and item.item_type == "GOLD":
            self.player.gold += getattr(item, 'amount', 1)
            floor_data.item_spawner.items.remove(item)
            message = f"You picked up {getattr(item, 'amount', 1)} gold."
            self.add_message(message)
            return message

        # 通常のアイテムはインベントリに追加
        if self.inventory.add_item(item):
            floor_data.item_spawner.items.remove(item)
            message = f"You picked up {item.name}."
            self.add_message(message)
            return message
        else:
            self.add_message("Your inventory is full!")
            return None

    # 階段処理（FloorManagerに委譲予定）
    def descend_stairs(self) -> bool:
        """階段を下る。"""
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return False

        tile = floor_data.tiles[self.player.y, self.player.x]

        from pyrogue.map.tile import StairsDown
        if not isinstance(tile, StairsDown):
            self.add_message("There are no stairs here!")
            return False

        # 次のフロアに移動
        next_floor = self.dungeon_manager.current_floor + 1

        from pyrogue.constants import GameConstants
        if next_floor > GameConstants.MAX_FLOORS:
            self.add_message("You have reached the deepest part of the dungeon!")
            return False

        self.dungeon_manager.set_current_floor(next_floor)
        floor_data = self.get_current_floor_data()

        if floor_data and hasattr(floor_data, 'start_pos'):
            self.player.x, self.player.y = floor_data.start_pos

        self.add_message(f"You descend to floor B{next_floor}F.")
        return True

    def ascend_stairs(self) -> bool:
        """階段を上る。"""
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return False

        tile = floor_data.tiles[self.player.y, self.player.x]

        from pyrogue.map.tile import StairsUp
        if not isinstance(tile, StairsUp):
            self.add_message("There are no stairs here!")
            return False

        # 前のフロアに移動
        prev_floor = self.dungeon_manager.current_floor - 1

        if prev_floor < 1:
            # 勝利条件チェック
            if self.check_victory():
                self.add_message("You have escaped with the Amulet of Yendor! You win!")
                return True
            else:
                self.add_message("You need the Amulet of Yendor to escape!")
                return False

        self.dungeon_manager.move_to_floor(prev_floor)
        floor_data = self.get_current_floor_data()

        if floor_data and hasattr(floor_data, 'end_pos'):
            self.player.x, self.player.y = floor_data.end_pos

        self.add_message(f"You ascend to floor B{prev_floor}F.")
        return True

    # 状態チェック（GameStateManagerに委譲予定）
    def check_player_death(self) -> bool:
        """プレイヤーの死亡をチェック。"""
        return self.player.hp <= 0

    def check_victory(self) -> bool:
        """勝利条件をチェック。"""
        # イェンダーのアミュレットを持っているかチェック
        return getattr(self.player, 'has_amulet', False)

    def check_game_over(self) -> bool:
        """ゲームオーバー状態をチェック。"""
        return self.check_player_death()

    # ターン処理（TurnManagerに委譲済み）
    def process_enemy_turns(self) -> None:
        """敵のターン処理。"""
        self.monster_ai_manager.process_all_monsters(self.context)

    # ドア処理（DoorManagerに委譲予定）
    def open_door(self, x: int, y: int) -> bool:
        """ドアを開く。"""
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return False

        # 座標チェック
        if (x < 0 or y < 0 or
            y >= floor_data.tiles.shape[0] or
            x >= floor_data.tiles.shape[1]):
            return False

        tile = floor_data.tiles[y, x]

        # ドアタイルかチェック
        from pyrogue.map.tile import Door
        if isinstance(tile, Door) and tile.door_state == "closed":
            tile.toggle()  # ドアを開く
            self.add_message("You open the door.")
            # FOVを更新
            self._update_fov()
            return True

        return False

    def close_door(self, x: int, y: int) -> bool:
        """ドアを閉じる。"""
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return False

        # 座標チェック
        if (x < 0 or y < 0 or
            y >= floor_data.tiles.shape[0] or
            x >= floor_data.tiles.shape[1]):
            return False

        tile = floor_data.tiles[y, x]

        # ドアタイルかチェック
        from pyrogue.map.tile import Door
        if isinstance(tile, Door) and tile.door_state == "open":
            # モンスターやプレイヤーがドアの上にいないかチェック
            if not self._is_position_occupied(x, y):
                tile.toggle()  # ドアを閉じる
                self.add_message("You close the door.")
                # FOVを更新
                self._update_fov()
                return True
            else:
                self.add_message("There is something in the way.")
                return False

        return False

    def _is_position_occupied(self, x: int, y: int) -> bool:
        """指定位置にプレイヤーやモンスターがいるかチェック。"""
        # プレイヤーがいるかチェック
        if self.player.x == x and self.player.y == y:
            return True

        # モンスターがいるかチェック
        monster = self._get_monster_at(x, y)
        return monster is not None

    def _update_fov(self) -> None:
        """FOVを更新（ゲームスクリーンが存在する場合）。"""
        if self.game_screen and hasattr(self.game_screen, 'fov_manager'):
            self.game_screen.fov_manager.update_fov()

    def search_secret_door(self, x: int, y: int) -> bool:
        """隠しドアを探索。"""
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return False

        # 座標チェック
        if (x < 0 or y < 0 or
            y >= floor_data.tiles.shape[0] or
            x >= floor_data.tiles.shape[1]):
            return False

        tile = floor_data.tiles[y, x]

        # 隠しドアかチェック
        from pyrogue.map.tile import SecretDoor
        if isinstance(tile, SecretDoor) and tile.door_state == "secret":
            # 発見成功率はプレイヤーレベルに依存（基本30% + レベル*5%）
            import random
            success_rate = min(80, 30 + self.player.level * 5)

            if random.randint(1, 100) <= success_rate:
                tile.reveal()  # 隠しドアを発見
                self.add_message("You found a secret door!")
                # FOVを更新
                self._update_fov()
                return True
            else:
                # 失敗してもメッセージは出さない（まとめて処理される）
                return False

        return False

    # トラップ処理（TrapManagerに委譲予定）
    def disarm_trap(self, x: int, y: int) -> bool:
        """トラップを解除。"""
        # TrapManagerに委譲予定（現在未実装）
        return False

    # 魔法処理（MagicManagerに委譲予定）
    def handle_target_selection(self, x: int, y: int) -> None:
        """ターゲット選択処理。"""
        # MagicManagerに委譲予定（現在未実装）
        pass

    # ユーティリティメソッド
    def add_message(self, message: str) -> None:
        """メッセージログにメッセージを追加。"""
        self.context.add_message(message)

    def get_current_floor_data(self):
        """現在のフロアデータを取得。"""
        return self.dungeon_manager.get_current_floor_data()

    def get_explored_tiles(self):
        """探索済みタイルを取得。"""
        floor_data = self.get_current_floor_data()
        if floor_data and hasattr(floor_data, 'explored'):
            return floor_data.explored

        # デフォルトの探索状態を返す
        import numpy as np
        return np.full((self.dungeon_manager.height, self.dungeon_manager.width), False, dtype=bool)

    def update_explored_tiles(self, visible_tiles) -> None:
        """探索済みタイルを更新。"""
        floor_data = self.get_current_floor_data()
        if floor_data and hasattr(floor_data, 'explored'):
            floor_data.explored |= visible_tiles

    # CLIモード互換メソッド
    def try_attack_adjacent_enemy(self) -> bool:
        """隣接する敵を攻撃。"""
        player = self.player

        # 隣接する8方向をチェック
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                x, y = player.x + dx, player.y + dy
                monster = self._get_monster_at(x, y)
                if monster:
                    return self.combat_manager.handle_player_combat(monster, self.context)

        return False

    def try_use_item(self, item) -> bool:
        """アイテムを使用。"""
        # ItemManagerに委譲予定（現在未実装）
        return False

    def get_nearby_enemies(self) -> list:
        """周囲の敵を取得。"""
        enemies = []
        player = self.player
        floor_data = self.get_current_floor_data()

        if not floor_data or not hasattr(floor_data, 'monster_spawner'):
            return enemies

        for monster in floor_data.monster_spawner.monsters:
            distance = abs(monster.x - player.x) + abs(monster.y - player.y)
            if distance <= 2:  # 周囲2マス以内
                enemies.append(monster)

        return enemies
