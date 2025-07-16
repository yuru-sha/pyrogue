"""
リファクタリングされたゲームロジックモジュール。

このモジュールは、元のGameLogicから責務を分離し、
各マネージャーに処理を委譲する構造になっています。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrogue.core.managers.combat_manager import CombatManager
from pyrogue.core.managers.floor_manager import FloorManager
from pyrogue.core.managers.game_context import GameContext
from pyrogue.core.managers.item_manager import ItemManager
from pyrogue.core.managers.monster_ai_manager import MonsterAIManager
from pyrogue.core.managers.movement_manager import MovementManager
from pyrogue.core.managers.turn_manager import TurnManager
from pyrogue.core.score_manager import ScoreManager
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

    Attributes
    ----------
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
        ----
            engine: ゲームエンジンインスタンス（CLIモードではNone）
            dungeon_width: ダンジョンの幅
            dungeon_height: ダンジョンの高さ

        """
        self.engine = engine

        # ゲーム状態を直接管理
        self.player = Player(x=0, y=0)
        self.inventory = self.player.inventory  # プレイヤーのインベントリを参照
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
            engine=engine,
        )

        # 各マネージャーを初期化
        self.combat_manager = CombatManager()
        self.turn_manager = TurnManager()
        self.monster_ai_manager = MonsterAIManager()
        self.score_manager = ScoreManager()

        # ウィザードモード（デバッグ用）
        from pyrogue.config.env import get_debug_mode

        self.wizard_mode = get_debug_mode()

        # 新しいマネージャーを初期化
        self.movement_manager = MovementManager(self.context)
        self.item_manager = ItemManager(self.context)
        self.floor_manager = FloorManager(self.context)

        # コンテキストにマネージャーへの参照を追加
        self.context.monster_ai_manager = self.monster_ai_manager
        self.context.game_logic = self
        self.context.combat_manager = self.combat_manager
        self.context.turn_manager = self.turn_manager
        self.context.movement_manager = self.movement_manager
        self.context.item_manager = self.item_manager
        self.context.floor_manager = self.floor_manager

        # GameScreen参照（段階的移行用）
        self.game_screen: GameScreen | None = None

        # 初期化状態を追跡
        self._is_initialized = False

    def toggle_wizard_mode(self) -> None:
        """ウィザードモードの切り替え。"""
        self.wizard_mode = not self.wizard_mode
        status = "enabled" if self.wizard_mode else "disabled"
        self.add_message(f"Wizard mode {status}!")

    def is_wizard_mode(self) -> bool:
        """ウィザードモードの状態を取得。"""
        return self.wizard_mode

    def wizard_teleport_to_stairs(self) -> None:
        """ウィザード機能: 階段位置にテレポート。"""
        if not self.wizard_mode:
            self.add_message("Wizard mode required!")
            return

        floor_data = self.get_current_floor_data()
        if not floor_data:
            return

        # 下り階段を探す
        for y in range(floor_data.tiles.shape[0]):
            for x in range(floor_data.tiles.shape[1]):
                from pyrogue.map.tile import StairsDown

                if isinstance(floor_data.tiles[y, x], StairsDown):
                    self.player.x = x
                    self.player.y = y
                    self.add_message(f"[Wizard] Teleported to stairs at ({x}, {y})!")
                    self._update_fov()
                    return

        self.add_message("[Wizard] No stairs found on this floor!")

    def wizard_level_up(self) -> None:
        """ウィザード機能: レベルアップ。"""
        if not self.wizard_mode:
            self.add_message("Wizard mode required!")
            return

        from pyrogue.constants import get_exp_for_level

        # 次のレベルに必要な経験値を設定してレベルアップ
        next_level = self.player.level + 1
        required_exp = get_exp_for_level(next_level)
        self.player.exp = required_exp
        self.player.level_up()  # 正規のレベルアップ処理を使用
        self.add_message(f"[Wizard] Level up! Now level {self.player.level}")

    def wizard_heal_full(self) -> None:
        """ウィザード機能: 完全回復。"""
        if not self.wizard_mode:
            self.add_message("Wizard mode required!")
            return

        self.player.hp = self.player.max_hp
        self.player.mp = self.player.max_mp
        self.add_message("[Wizard] Fully healed!")

    def wizard_reveal_all(self) -> None:
        """ウィザード機能: 全マップ探索済みにする。"""
        if not self.wizard_mode:
            self.add_message("Wizard mode required!")
            return

        floor_data = self.get_current_floor_data()
        if not floor_data:
            return

        # 全タイルを探索済みにする
        explored = self.get_explored_tiles()
        explored.fill(True)

        # 全隠しドア・トラップを発見済みにする
        for y in range(floor_data.tiles.shape[0]):
            for x in range(floor_data.tiles.shape[1]):
                from pyrogue.map.tile import SecretDoor

                tile = floor_data.tiles[y, x]
                if isinstance(tile, SecretDoor) and tile.door_state == "secret":
                    tile.reveal()

        if hasattr(floor_data, "trap_spawner") and floor_data.trap_spawner:
            for trap in floor_data.trap_spawner.traps:
                if trap.is_hidden:
                    trap.reveal()

        self.add_message("[Wizard] All map revealed!")
        self._update_fov()

    def setup_new_game(self) -> None:
        """新しいゲームをセットアップ。"""
        # 重複初期化を防ぐ
        if self._is_initialized:
            return

        # 初期装備の設定
        self._setup_initial_equipment()

        # ダンジョンの生成
        self.dungeon_manager.set_current_floor(1)

        # プレイヤーの開始位置を設定
        floor_data = self.dungeon_manager.get_current_floor_data()
        if floor_data and hasattr(floor_data, "start_pos"):
            self.player.x, self.player.y = floor_data.start_pos

        self.add_message("You enter the dungeon. Your quest begins!")

        # 初期化完了をマーク
        self._is_initialized = True

    def reset_game(self) -> None:
        """ゲームの状態をリセット。"""
        import random
        import time

        self._is_initialized = False

        # ランダムシードを時間ベースで再初期化（新しいマップ生成のため）
        random.seed(int(time.time() * 1000) % (2**31))

        # プレイヤーの状態をリセット
        self.player = Player(x=0, y=0)
        self.inventory = self.player.inventory

        # メッセージログをクリア
        self.message_log.clear()
        self.message_log.extend(
            [
                "Welcome to PyRogue!",
                "Use vi keys (hjklyubn), arrow keys, or numpad (1-9) to move.",
                "Press ESC to return to menu.",
            ]
        )

        # ダンジョンマネージャーのキャッシュをクリア（新しいマップ生成のため）
        self.dungeon_manager.clear_all_floors()

        # コンテキストを更新
        self.context.player = self.player
        self.context.inventory = self.inventory

    def _setup_initial_equipment(self) -> None:
        """初期装備と初期アイテムを設定。"""
        from pyrogue.entities.items.effects import (
            HealingEffect,
            LightEffect,
            NutritionEffect,
        )
        from pyrogue.entities.items.item import Armor, Food, Potion, Scroll, Weapon

        # 初期武器: Dagger (攻撃力+2) - item_types.pyのWEAPONSと統一
        dagger = Weapon(x=0, y=0, name="Dagger", attack_bonus=2)
        self.inventory.add_item(dagger)
        self.inventory.equip(dagger)

        # 初期防具: Leather Armor (防御力+1)
        leather_armor = Armor(x=0, y=0, name="Leather Armor", defense_bonus=1)
        self.inventory.add_item(leather_armor)
        self.inventory.equip(leather_armor)

        # 初期アイテム

        # Potion of Healing x2（HP10-15回復）
        healing_potion1 = Potion(x=0, y=0, name="Potion of Healing", effect=HealingEffect(heal_amount=12))
        healing_potion2 = Potion(x=0, y=0, name="Potion of Healing", effect=HealingEffect(heal_amount=12))
        self.inventory.add_item(healing_potion1)
        self.inventory.add_item(healing_potion2)

        # Food Ration x2（満腹度25回復）
        food_ration1 = Food(x=0, y=0, name="Food Ration", effect=NutritionEffect(nutrition_value=25))
        food_ration2 = Food(x=0, y=0, name="Food Ration", effect=NutritionEffect(nutrition_value=25))
        self.inventory.add_item(food_ration1)
        self.inventory.add_item(food_ration2)

        # Scroll of Light x1（視野拡大50ターン）
        light_scroll = Scroll(x=0, y=0, name="Scroll of Light", effect=LightEffect(duration=50, radius=15))
        self.inventory.add_item(light_scroll)

        self.add_message("You are equipped with a Dagger and Leather Armor.")
        self.add_message("You start with some basic supplies: potions, food, and a scroll.")

    # EffectContext用プロパティ
    @property
    def dungeon(self):
        """EffectContext用のダンジョンプロパティ。"""
        return self.get_current_floor_data()

    def set_game_screen_reference(self, game_screen: GameScreen) -> None:
        """GameScreenへの参照を設定（段階的移行用）。"""
        self.game_screen = game_screen
        self.context.game_screen = game_screen

    # 移動処理（MovementManagerに委譲）
    def handle_player_move(self, dx: int, dy: int) -> bool:
        """
        プレイヤーの移動処理。

        Args:
        ----
            dx: X方向の移動量
            dy: Y方向の移動量

        Returns:
        -------
            移動が成功した場合True

        """
        # MovementManagerに処理を委譲
        result = self.movement_manager.handle_player_move(dx, dy)

        # 成功した場合はターン進行
        if result:
            self.turn_manager.process_turn(self.context)

        return result

    def _can_move_to(self, x: int, y: int) -> bool:
        """移動可能性をチェック。"""
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return False

        # 境界チェック
        if x < 0 or y < 0 or y >= floor_data.tiles.shape[0] or x >= floor_data.tiles.shape[1]:
            return False

        # タイルチェック
        tile = floor_data.tiles[y, x]
        return getattr(tile, "walkable", False)

    def _can_diagonal_move(self, from_x: int, from_y: int, dx: int, dy: int) -> bool:
        """
        斜め移動が可能かチェック（角抜け防止）。

        真の角抜けを防ぐため、斜めのコーナーが完全に閉じられている場合のみ移動を制限。
        一方でも通行可能な場合は移動を許可（通常のローグライク動作）。

        Args:
        ----
            from_x: 移動元X座標
            from_y: 移動元Y座標
            dx: X方向の移動量
            dy: Y方向の移動量

        Returns:
        -------
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
        if not floor_data or not hasattr(floor_data, "monster_spawner"):
            return None

        return floor_data.monster_spawner.get_monster_at(x, y)

    # アイテム処理（ItemManagerに委譲）
    def handle_get_item(self) -> str | None:
        """アイテム取得処理。"""
        return self.item_manager.handle_get_item()

    def can_drop_item_at(self, x: int, y: int) -> bool:
        """
        指定した位置にアイテムをドロップできるかチェック。

        Args:
        ----
            x: X座標
            y: Y座標

        Returns:
        -------
            ドロップ可能な場合True

        """
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return False

        # 座標の境界チェック
        if x < 0 or y < 0 or y >= floor_data.tiles.shape[0] or x >= floor_data.tiles.shape[1]:
            return False

        # タイルが歩行可能かチェック
        tile = floor_data.tiles[y, x]
        if not getattr(tile, "walkable", False):
            return False

        # モンスターがいないかチェック
        if self._get_monster_at(x, y):
            return False

        return True

    def drop_item_at(self, item, x: int, y: int) -> bool:
        """
        指定した位置にアイテムをドロップ。

        Args:
        ----
            item: ドロップするアイテム
            x: X座標
            y: Y座標

        Returns:
        -------
            ドロップが成功した場合True

        """
        if not self.can_drop_item_at(x, y):
            return False

        floor_data = self.get_current_floor_data()
        if not floor_data or not hasattr(floor_data, "item_spawner"):
            return False

        # アイテムの位置を設定
        item.x = x
        item.y = y

        # アイテムスポナーに追加
        floor_data.item_spawner.items.append(item)

        return True

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

        if floor_data:
            spawn_pos = self.dungeon_manager.get_player_spawn_position(floor_data)
            self.player.x, self.player.y = spawn_pos

        # 最深階層を更新
        self.player.update_deepest_floor(next_floor)

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
                self.record_victory()

                # 勝利処理をエンジンに通知
                if self.engine and hasattr(self.engine, "victory"):
                    player_stats = self.player.get_stats_dict()
                    final_floor = self.dungeon_manager.current_floor
                    self.engine.victory(player_stats, final_floor)

                return True
            self.add_message("You need the Amulet of Yendor to escape!")
            return False

        self.dungeon_manager.set_current_floor(prev_floor)
        floor_data = self.get_current_floor_data()

        if floor_data:
            spawn_pos = self.dungeon_manager.get_player_spawn_position(floor_data)
            self.player.x, self.player.y = spawn_pos

        self.add_message(f"You ascend to floor B{prev_floor}F.")
        return True

    # 状態チェック（GameStateManagerに委譲予定）
    def check_player_death(self) -> bool:
        """プレイヤーの死亡をチェック。"""
        return self.player.hp <= 0

    def check_victory(self) -> bool:
        """勝利条件をチェック。"""
        # イェンダーのアミュレットを持っているかチェック
        return getattr(self.player, "has_amulet", False)

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
        if x < 0 or y < 0 or y >= floor_data.tiles.shape[0] or x >= floor_data.tiles.shape[1]:
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
        if x < 0 or y < 0 or y >= floor_data.tiles.shape[0] or x >= floor_data.tiles.shape[1]:
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
        if self.game_screen and hasattr(self.game_screen, "fov_manager"):
            self.game_screen.fov_manager.update_fov()

    def search_secret_door(self, x: int, y: int) -> bool:
        """隠しドアを探索。"""
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return False

        # 座標チェック
        if x < 0 or y < 0 or y >= floor_data.tiles.shape[0] or x >= floor_data.tiles.shape[1]:
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
            # 失敗してもメッセージは出さない（まとめて処理される）
            return False

        return False

    def search_trap(self, x: int, y: int) -> bool:
        """隠しトラップを探索。"""
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return False

        # 座標チェック
        if x < 0 or y < 0 or y >= floor_data.tiles.shape[0] or x >= floor_data.tiles.shape[1]:
            return False

        # トラップスポナーからトラップを検索
        if hasattr(floor_data, "trap_spawner") and floor_data.trap_spawner:
            for trap in floor_data.trap_spawner.traps:
                if trap.x == x and trap.y == y and trap.is_hidden:
                    # 発見成功率はプレイヤーレベルに依存（基本40% + レベル*5%）
                    import random

                    success_rate = min(90, 40 + self.player.level * 5)

                    if random.randint(1, 100) <= success_rate:
                        trap.reveal()  # トラップを発見
                        self.add_message(f"You found a {trap.name}!")
                        return True
                    # 失敗してもメッセージは出さない（まとめて処理される）
                    return False

        return False

    # トラップ処理（TrapManagerに委譲予定）
    def disarm_trap(self, x: int, y: int) -> bool:
        """トラップを解除。"""
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return False

        # 座標チェック
        if x < 0 or y < 0 or y >= floor_data.tiles.shape[0] or x >= floor_data.tiles.shape[1]:
            return False

        # トラップスポナーからトラップを検索
        if hasattr(floor_data, "trap_spawner") and floor_data.trap_spawner:
            for trap in floor_data.trap_spawner.traps:
                if trap.x == x and trap.y == y and not trap.is_hidden:
                    # 発見済みトラップのみ解除可能
                    return trap.disarm(self.context)

        return False

    # 魔法処理（MagicManagerに委譲予定）
    def handle_target_selection(self, x: int, y: int) -> None:
        """ターゲット選択処理。"""
        # MagicManagerに委譲予定（現在未実装）

    def handle_use_item(self, item_name: str) -> bool:
        """アイテム使用処理。"""
        return self.item_manager.handle_use_item(item_name)

    def handle_combat(self) -> bool:
        """戦闘処理。"""
        # 隣接する敵を検索して攻撃
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return False

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                target_x = self.player.x + dx
                target_y = self.player.y + dy

                monster = floor_data.get_monster_at(target_x, target_y)
                if monster:
                    # 戦闘処理を実行
                    self.combat_manager.handle_player_attack(monster, self.context)
                    return True

        self.add_message("No enemy to attack nearby")
        return False

    def handle_stairs_up(self) -> bool:
        """上り階段の処理。"""
        return self.floor_manager.handle_stairs_up()

    def handle_stairs_down(self) -> bool:
        """下り階段の処理。"""
        return self.floor_manager.handle_stairs_down()

    def handle_open_door(self) -> bool:
        """扉を開く処理。"""
        return self.floor_manager.handle_open_door()

    def handle_close_door(self) -> bool:
        """扉を閉じる処理。"""
        return self.floor_manager.handle_close_door()

    def handle_search(self) -> bool:
        """隠し扉の探索処理。"""
        return self.floor_manager.handle_search()

    def handle_disarm_trap(self) -> bool:
        """トラップ解除の処理。"""
        return self.floor_manager.handle_disarm_trap()

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
        if floor_data and hasattr(floor_data, "explored"):
            return floor_data.explored

        # デフォルトの探索状態を返す
        import numpy as np

        return np.full((self.dungeon_manager.height, self.dungeon_manager.width), False, dtype=bool)

    def update_explored_tiles(self, visible_tiles) -> None:
        """探索済みタイルを更新。"""
        floor_data = self.get_current_floor_data()
        if floor_data and hasattr(floor_data, "explored"):
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
                    return self.combat_manager.handle_player_attack(monster, self.context)

        return False

    def try_use_item(self, item) -> bool:
        """アイテムを使用。"""
        # ItemManagerに委譲予定（現在未実装）
        return False

    def get_nearby_enemies(self) -> list[Monster]:
        """周囲の敵を取得。"""
        enemies: list[Monster] = []
        player = self.player
        floor_data = self.get_current_floor_data()

        if not floor_data or not hasattr(floor_data, "monster_spawner"):
            return enemies

        for monster in floor_data.monster_spawner.monsters:
            distance = abs(monster.x - player.x) + abs(monster.y - player.y)
            if distance <= 2:  # 周囲2マス以内
                enemies.append(monster)

        return enemies

    def record_game_over(self, death_cause: str = "Unknown") -> None:
        """ゲームオーバー時のスコア記録"""
        self.score_manager.add_score(
            self.player,
            death_cause=death_cause,
            game_result="death",
            player_name="Player",
        )

    def record_victory(self) -> None:
        """勝利時のスコア記録"""
        self.score_manager.add_score(
            self.player,
            death_cause="Victory",
            game_result="victory",
            player_name="Player",
        )

    def get_high_score(self) -> int:
        """最高スコアを取得"""
        return self.score_manager.get_high_score()

    def get_score_table(self, limit: int = 10) -> str:
        """スコアテーブルを取得"""
        return self.score_manager.format_score_table(limit)

    def handle_turn_end(self) -> None:
        """
        ターン終了時の処理。

        ターンマネージャーによるターン処理とオートセーブ機能を実行します。
        """
        # TurnManagerによるターン処理
        self.turn_manager.process_turn(self.context)

        # オートセーブ機能の実行
        self._handle_auto_save()

    def _handle_auto_save(self) -> None:
        """
        オートセーブ機能の処理。

        環境変数でオートセーブが有効な場合、一定間隔でゲームを自動保存します。
        """
        from pyrogue.config.env import get_auto_save_enabled

        # オートセーブが無効の場合は処理しない
        if not get_auto_save_enabled():
            return

        # 一定ターン数毎にオートセーブを実行（10ターン毎）
        if self.turn_manager.turn_count % 10 == 0:
            self._perform_auto_save()

    def _perform_auto_save(self) -> None:
        """
        実際のオートセーブを実行。

        CommonCommandHandlerのセーブ機能を使用してゲームを保存します。
        """
        try:
            # プレイヤーが死亡している場合はオートセーブしない
            if self.player.hp <= 0:
                return

            # SaveManagerを直接使用してオートセーブを実行
            from pyrogue.core.save_manager import SaveManager

            save_manager = SaveManager()

            # 現在のゲーム状態を収集
            save_data = self._create_auto_save_data()

            # オートセーブを実行
            success = save_manager.save_game_state(save_data)

            if success:
                # オートセーブ成功メッセージ（デバッグモード時のみ）
                if self.wizard_mode:
                    self.add_message(f"[Auto-save] Game saved at turn {self.turn_manager.turn_count}")
            else:
                # オートセーブ失敗時のメッセージ
                if self.wizard_mode:
                    self.add_message("[Auto-save] Failed to save game")

        except Exception as e:
            # エラーが発生した場合のログ出力
            from pyrogue.utils import game_logger

            game_logger.error(f"Auto-save failed: {e}")

    def _create_auto_save_data(self) -> dict:
        """
        オートセーブ用のデータを作成。

        Returns
        -------
            dict: セーブデータ辞書
        """
        # CommonCommandHandlerと同じ形式でセーブデータを作成
        save_data = {
            "player": self._serialize_player(self.player),
            "inventory": self._serialize_inventory(self.inventory),
            "current_floor": self.dungeon_manager.current_floor,
            "floor_data": self._serialize_all_floors(self.dungeon_manager.floors),
            "message_log": self.message_log,
            "has_amulet": getattr(self.player, "has_amulet", False),
            "turn_count": self.turn_manager.turn_count,
            "auto_save": True,  # オートセーブフラグ
            "version": "1.0",
        }

        return save_data

    def _serialize_player(self, player) -> dict:
        """プレイヤーオブジェクトをシリアライズ。"""
        return {
            "x": player.x,
            "y": player.y,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "level": player.level,
            "exp": player.exp,
            "gold": player.gold,
            "attack": player.attack,
            "defense": player.defense,
            "hunger": getattr(player, "hunger", 100),
            "mp": getattr(player, "mp", 0),
            "max_mp": getattr(player, "max_mp", 0),
            "has_amulet": getattr(player, "has_amulet", False),
            "monsters_killed": getattr(player, "monsters_killed", 0),
            "deepest_floor": getattr(player, "deepest_floor", 1),
            "turns_played": getattr(player, "turns_played", 0),
        }

    def _serialize_inventory(self, inventory) -> dict:
        """インベントリをシリアライズ。"""
        if inventory is None:
            return {"items": [], "equipped": {"weapon": None, "armor": None, "ring_left": None, "ring_right": None}}

        return {
            "items": [self._serialize_item(item) for item in inventory.items],
            "equipped": {
                "weapon": self._serialize_item(inventory.equipped["weapon"])
                if inventory.equipped.get("weapon")
                else None,
                "armor": self._serialize_item(inventory.equipped["armor"]) if inventory.equipped.get("armor") else None,
                "ring_left": self._serialize_item(inventory.equipped["ring_left"])
                if inventory.equipped.get("ring_left")
                else None,
                "ring_right": self._serialize_item(inventory.equipped["ring_right"])
                if inventory.equipped.get("ring_right")
                else None,
            },
        }

    def _serialize_item(self, item) -> dict:
        """アイテムをシリアライズ。"""
        if item is None:
            return None

        return {
            "item_type": getattr(item, "item_type", "MISC"),
            "name": item.name,
            "char": getattr(item, "char", "?"),
            "color": getattr(item, "color", (255, 255, 255)),
            "x": getattr(item, "x", 0),
            "y": getattr(item, "y", 0),
            "quantity": getattr(item, "quantity", 1),
            "stack_count": getattr(item, "stack_count", 1),
            "enchantment": getattr(item, "enchantment", 0),
            "cursed": getattr(item, "cursed", False),
        }

    def _serialize_all_floors(self, floors: dict) -> dict:
        """すべてのフロアデータをシリアライズ。"""
        serialized_floors = {}
        for floor_num, floor_data in floors.items():
            if floor_data is not None:
                serialized_floors[floor_num] = self._serialize_floor_data_object(floor_data)
        return serialized_floors

    def _serialize_floor_data_object(self, floor_data) -> dict:
        """フロアデータオブジェクトをシリアライズ。"""
        return {
            "tiles": floor_data.tiles.tolist(),
            "monsters": [self._serialize_monster(monster) for monster in floor_data.monster_spawner.monsters],
            "items": [self._serialize_item(item) for item in floor_data.item_spawner.items],
            "explored": floor_data.explored.tolist(),
            "traps": [
                self._serialize_trap(trap) for trap in getattr(getattr(floor_data, "trap_manager", None), "traps", [])
            ],
        }

    def _serialize_monster(self, monster) -> dict:
        """モンスターをシリアライズ。"""
        return {
            "name": monster.name,
            "char": monster.char,
            "x": monster.x,
            "y": monster.y,
            "hp": monster.hp,
            "max_hp": monster.max_hp,
            "attack": monster.attack,
            "defense": monster.defense,
            "level": monster.level,
            "exp_value": getattr(monster, "exp_value", 0),
            "ai_pattern": getattr(monster, "ai_pattern", "basic"),
        }

    def _serialize_trap(self, trap) -> dict:
        """トラップをシリアライズ。"""
        return {
            "trap_type": getattr(trap, "trap_type", "PitTrap"),
            "x": trap.x,
            "y": trap.y,
            "hidden": getattr(trap, "is_hidden", True),
        }

    def get_message_history(self) -> list[str]:
        """
        メッセージ履歴を取得。

        Returns
        -------
            メッセージ履歴のリスト
        """
        return self.message_log.copy()
