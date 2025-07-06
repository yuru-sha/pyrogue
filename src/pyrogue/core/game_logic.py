"""
ゲームロジックモジュール。

このモジュールは、ゲームの核となるロジック処理を担当します。
プレイヤーのアクション処理、戦闘システム、アイテム使用、
モンスターのターン処理などを統合的に管理します。

主要機能:
    - プレイヤーアクション（移動、攻撃、アイテム使用）の処理
    - 戦闘システムの管理
    - ターンベースゲームの進行制御
    - ダンジョン内でのイベント処理
    - ゲーム状態の変更とバリデーション

Example:
    >>> game_logic = GameLogic(game_screen)
    >>> game_logic.handle_player_move(dx=1, dy=0)
    >>> game_logic.process_turn()

"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine
    from pyrogue.entities.actors.monster import Monster
    from pyrogue.entities.actors.player import Player
    from pyrogue.ui.screens.game_screen import GameScreen

from pyrogue.entities.actors.inventory import Inventory
from pyrogue.entities.actors.player import Player
from pyrogue.map.dungeon_manager import DungeonManager


class GameLogic:
    """
    ゲームロジック管理クラス。

    ゲームの核となるロジック処理を担当し、UIから完全に分離された
    ビジネスロジックを統合的に管理します。ゲーム状態の単一の信頼できる
    情報源（Single Source of Truth）として機能します。

    特徴:
        - UIとロジックの完全分離
        - テスト可能な設計
        - 単一責任の原則に基づく責務分離
        - ターンベースゲームの制御
        - ゲーム状態の一元管理

    Attributes:
        engine: ゲームエンジンへの参照
        player: プレイヤーインスタンス
        inventory: プレイヤーのインベントリ
        message_log: ゲームメッセージログ
        dungeon_manager: ダンジョン管理インスタンス

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

        # 互換性のための一時的な参照（段階的移行用）
        self.game_screen: GameScreen | None = None

    @property
    def dungeon(self):
        """EffectContext用のダンジョンプロパティ。"""
        return self.dungeon_manager.get_current_floor_data().dungeon

    def set_game_screen_reference(self, game_screen: GameScreen) -> None:
        """
        GameScreenへの参照を設定（段階的移行用）。

        Args:
            game_screen: GameScreenインスタンス

        """
        self.game_screen = game_screen

    def handle_player_move(self, dx: int, dy: int) -> bool:
        """
        プレイヤーの移動処理。

        指定された方向への移動を試行し、可能であれば移動を実行します。
        壁や障害物への衝突、モンスターとの戦闘判定も行います。

        Args:
            dx: X軸方向の移動量
            dy: Y軸方向の移動量

        Returns:
            移動が成功した場合True、失敗した場合False

        """
        # 麻痺状態では移動できない
        if self.player.is_paralyzed():
            self.add_message("You cannot move while paralyzed!")
            self.process_turn()  # ターンは消費される
            return False

        # 混乱状態では移動方向がランダム化される
        if self.player.is_confused():
            import random
            directions = [
                (-1, -1), (0, -1), (1, -1),
                (-1, 0),           (1, 0),
                (-1, 1),  (0, 1),  (1, 1),
            ]
            dx, dy = random.choice(directions)
            self.add_message("You stumble around in confusion!")

        target_x = self.player.x + dx
        target_y = self.player.y + dy

        # 移動可能かチェック
        if self._can_move_to(target_x, target_y):
            # モンスターとの衝突判定
            current_floor = self.dungeon_manager.get_current_floor_data()
            monster = current_floor.monster_spawner.get_monster_at(target_x, target_y)
            if monster:
                # モンスターがいる場合は戦闘を開始
                self.handle_combat(monster)

                # 戦闘後のターン処理
                self.process_turn()

                return True  # 戦闘は移動扱い

            # 移動を実行
            self.player.move(dx, dy)

            # 金貨のみ自動ピックアップ（オリジナルRogue仕様）
            self._auto_pickup_gold_only()

            # トラップチェック
            self._check_traps()

            # ターン処理（モンスターの行動など）
            self.process_turn()

            return True
        return False

    def _can_move_to(self, x: int, y: int) -> bool:
        """
        指定の位置に移動できるかを判定。

        Args:
            x: X座標
            y: Y座標

        Returns:
            移動可能な場合True

        """
        current_floor = self.dungeon_manager.get_current_floor_data()

        # 境界チェック
        if not (
            0 <= x < current_floor.tiles.shape[1]
            and 0 <= y < current_floor.tiles.shape[0]
        ):
            return False

        tile = current_floor.tiles[y][x]
        return tile.walkable

    def _auto_pickup_gold_only(self) -> None:
        """プレイヤーの現在位置で金貨のみ自動ピックアップ（オリジナルRogue仕様）"""
        current_floor = self.dungeon_manager.get_current_floor_data()
        item = current_floor.item_spawner.get_item_at(self.player.x, self.player.y)

        if item:
            from pyrogue.entities.items.item import Gold

            if isinstance(item, Gold):
                # 金貨のみ自動でピックアップ
                self.player.gold += item.amount
                self.add_message(f"You pick up {item.amount} gold pieces.")
                current_floor.item_spawner.remove_item(item)
            else:
                # その他のアイテムはメッセージのみ
                self.add_message(f"You see {item.name} here. Press 'g' to get it.")

    def _auto_pickup(self) -> None:
        """旧メソッド名での互換性のため、新しいメソッドに委譲"""
        self._auto_pickup_gold_only()

    def handle_combat(self, monster: Monster) -> None:
        """
        戦闘処理。

        プレイヤーとモンスター間の戦闘を処理します。
        ダメージ計算、経験値獲得、モンスター撃破処理を含みます。

        Args:
            monster: 戦闘対象のモンスター

        """
        # プレイヤーの攻撃
        player_damage = max(0, self.player.get_attack() - monster.defense)
        monster.take_damage(player_damage)

        if monster.is_dead():
            # モンスター撃破時の処理
            self.add_message(f"You defeated the {monster.name}!")
            self.player.exp += monster.exp_value

            # レベルアップチェック
            if self.player.gain_exp(0):  # exp は既に加算済みなので0を渡す
                self.add_message(
                    f"You gained a level! You are now level {self.player.level}."
                )

            # モンスターリストから削除
            current_floor = self.dungeon_manager.get_current_floor_data()
            if monster in current_floor.monster_spawner.monsters:
                current_floor.monster_spawner.monsters.remove(monster)
            return

        # モンスターの反撃
        monster_damage = max(0, monster.attack - self.player.get_defense())
        self.player.hp = max(0, self.player.hp - monster_damage)

        # 戦闘ログ
        self.add_message(
            f"You hit the {monster.name} for {player_damage} damage. "
            f"The {monster.name} hits you for {monster_damage} damage."
        )

        # プレイヤーの死亡判定
        if self.player.hp <= 0:
            self.add_message("You died!")
            if self.engine:  # CLIモードでは engine が None の場合がある
                self.engine.game_over(
                    self.player.get_stats_dict(),
                    self.dungeon_manager.current_floor,
                    f"Killed by {monster.name}",
                )

    def handle_item_use(self, item_index: int) -> bool:
        """
        アイテム使用処理。

        指定されたインデックスのアイテムを使用し、効果を適用します。

        Args:
            item_index: 使用するアイテムのインデックス

        Returns:
            アイテム使用が成功した場合True、失敗した場合False

        """
        # TODO: game_screen.pyからアイテム使用ロジックを移行
        return False

    def handle_door_interaction(self, x: int, y: int) -> bool:
        """
        ドア操作処理。

        指定座標のドアの開閉処理を行います。

        Args:
            x: ドアのX座標
            y: ドアのY座標

        Returns:
            ドア操作が成功した場合True、失敗した場合False

        """
        # TODO: game_screen.pyからドア処理ロジックを移行
        return False

    def process_turn(self) -> None:
        """
        ターン処理。

        プレイヤーのアクション後に実行される処理を管理します。
        モンスターのターン、満腹度減少、状態効果の更新などを含みます。

        """
        # モンスターのターン処理
        self._process_monster_turns()

        # 満腹度減少
        hunger_message = self.player.consume_food(1)
        if hunger_message:
            self.add_message(hunger_message)

        # ライト効果の更新
        self.player.update_light_effect()

        # 状態異常の更新
        self.player.update_status_effects(context=self)

    def handle_get_item(self) -> str | None:
        """
        アイテム取得処理。

        プレイヤーの現在位置にあるアイテムを拾う処理を行います。
        ゴールドの場合は直接プレイヤーの所持金に加算し、
        その他のアイテムはインベントリに追加します。

        Returns:
            取得結果のメッセージ。アイテムがない場合はNone

        """
        from pyrogue.entities.items.item import Gold

        current_floor = self.dungeon_manager.get_current_floor_data()
        item = current_floor.item_spawner.get_item_at(self.player.x, self.player.y)
        if item:
            if isinstance(item, Gold):
                self.player.gold += item.amount
                message = f"You pick up {item.amount} gold pieces."
                current_floor.item_spawner.remove_item(item)
                return message
            # インベントリに追加を試行
            if self.inventory.add_item(item):
                pickup_message = item.pick_up()
                current_floor.item_spawner.remove_item(item)
                return pickup_message
            # インベントリが満杯の場合
            return f"Your pack is full. Cannot pick up {item.name}."
        return "There is nothing here to pick up."

    def handle_drop_item(self) -> str:
        """
        アイテム投下処理。

        プレイヤーのインベントリからアイテムを投下する処理を行います。
        インベントリが空の場合は適切なメッセージを返します。

        Returns:
            処理結果のメッセージ

        """
        # インベントリが空の場合
        if not self.inventory.items:
            return "You have nothing to drop."

        return "Press 'i' to open inventory and use 'd' to drop items."

    def can_drop_item_at(self, x: int, y: int) -> bool:
        """
        指定された位置にアイテムをドロップできるかチェック。

        Args:
            x: X座標
            y: Y座標

        Returns:
            ドロップ可能な場合はTrue

        """
        current_floor = self.dungeon_manager.get_current_floor_data()

        # 既にアイテムが存在するかチェック
        if current_floor.item_spawner.get_item_at(x, y) is not None:
            return False

        # 地面がフロアタイルかチェック（壁や扉には置けない）
        from pyrogue.map.tile import Floor

        if (
            0 <= y < current_floor.tiles.shape[0]
            and 0 <= x < current_floor.tiles.shape[1]
        ):
            return isinstance(current_floor.tiles[y][x], Floor)

        return False

    def handle_door_open(self) -> str:
        """
        ドア開放処理。

        プレイヤーの隣接8方向にあるドアを開く処理を行います。
        通常のドアと隠しドア（発見済み）の両方に対応します。

        Returns:
            処理結果のメッセージ

        """
        from pyrogue.map.tile import Door, SecretDoor

        current_floor = self.dungeon_manager.get_current_floor_data()

        # 隣接する8方向をチェック
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                x = self.player.x + dx
                y = self.player.y + dy

                # マップ範囲内かチェック
                if not (
                    0 <= x < current_floor.tiles.shape[1]
                    and 0 <= y < current_floor.tiles.shape[0]
                ):
                    continue

                tile = current_floor.tiles[y][x]

                # 通常の扉が閉じている場合
                if (isinstance(tile, Door) and tile.door_state == "closed") or (
                    isinstance(tile, SecretDoor) and tile.door_state == "closed"
                ):
                    tile.toggle()  # 扉を開ける
                    # FOVマップ更新は呼び出し元で処理
                    return "You open the door."

        return "There is no door to open."

    def handle_door_close(self) -> str:
        """
        ドア閉鎖処理。

        プレイヤーの隣接8方向にある開いたドアを閉める処理を行います。
        モンスターが邪魔している場合は閉められません。

        Returns:
            処理結果のメッセージ

        """
        from pyrogue.map.tile import Door, SecretDoor

        current_floor = self.dungeon_manager.get_current_floor_data()

        # 隣接する8方向をチェック
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                x = self.player.x + dx
                y = self.player.y + dy

                # マップ範囲内かチェック
                if not (
                    0 <= x < current_floor.tiles.shape[1]
                    and 0 <= y < current_floor.tiles.shape[0]
                ):
                    continue

                tile = current_floor.tiles[y][x]

                # 開いた扉（通常の扉または発見済みの隠し扉）を見つけた場合
                if (
                    isinstance(tile, Door)
                    or (isinstance(tile, SecretDoor) and tile.door_state != "secret")
                ) and tile.door_state == "open":
                    # モンスターがいないか確認
                    if current_floor.monster_spawner.get_monster_at(x, y):
                        return "There's a monster in the way!"

                    tile.toggle()  # 扉を閉める
                    # FOVマップ更新は呼び出し元で処理
                    return "You close the door."

        return "There is no door to close."

    def handle_search(self) -> str:
        """
        隠しドア探索処理。

        プレイヤーの隣接8方向で隠しドアを探す処理を行います。
        33%の確率で隠しドアを発見できます。

        Returns:
            処理結果のメッセージ

        """
        import random

        from pyrogue.map.tile import SecretDoor

        current_floor = self.dungeon_manager.get_current_floor_data()

        # 隣接する8方向をチェック
        found = False
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                x = self.player.x + dx
                y = self.player.y + dy

                # マップ範囲内かチェック
                if not (
                    0 <= x < current_floor.tiles.shape[1]
                    and 0 <= y < current_floor.tiles.shape[0]
                ):
                    continue

                tile = current_floor.tiles[y][x]

                # 隠し扉を見つけた場合
                if isinstance(tile, SecretDoor) and tile.door_state == "secret":
                    # 33%の確率で発見
                    if random.random() < 0.33:
                        tile.reveal()  # 隠し扉を発見
                        # FOVマップ更新は呼び出し元で処理
                        found = True
                        break

        if found:
            return "You found a secret door!"
        return "You search but find nothing."

    def add_message(self, message: str) -> None:
        """
        メッセージログに追加。

        Args:
            message: 追加するメッセージ

        """
        self.message_log.append(message)

        # メッセージログのサイズ制限（最新100メッセージを保持）
        if len(self.message_log) > 100:
            self.message_log = self.message_log[-100:]

    def setup_new_game(self) -> None:
        """
        新しいゲームのセットアップ。

        プレイヤー、インベントリ、ダンジョンの状態を初期化します。
        """
        # プレイヤーを初期化
        self.player = Player(x=0, y=0)
        self.inventory = Inventory()

        # メッセージログを初期化
        self.message_log = [
            "Welcome to PyRogue!",
            "Use vi keys (hjklyubn), arrow keys, or numpad (1-9) to move.",
            "Press ESC to return to menu.",
        ]

        # ダンジョンマネージャーをリセット
        self.dungeon_manager.clear_all_floors()

        # 初期装備を追加
        self._setup_initial_equipment()

        # 最初の階層を生成してプレイヤーを配置
        first_floor = self.dungeon_manager.get_floor(1)
        spawn_pos = self.dungeon_manager.get_player_spawn_position(first_floor)
        self.player.x, self.player.y = spawn_pos

    def _setup_initial_equipment(self) -> None:
        """
        初期装備をプレイヤーに設定。

        オリジナルRogueのように基本的な装備を与えます。
        """
        from pyrogue.entities.items.item import Armor, Weapon

        # 初期武器: ダガー
        dagger = Weapon(
            x=0,
            y=0,  # インベントリ内なので位置は無関係
            name="Dagger",
            attack_bonus=2,
        )

        # 初期防具: レザーアーマー
        leather_armor = Armor(
            x=0,
            y=0,  # インベントリ内なので位置は無関係
            name="Leather Armor",
            defense_bonus=1,
        )

        # インベントリに追加して装備
        self.inventory.add_item(dagger)
        self.inventory.add_item(leather_armor)

        # 装備する
        self.inventory.equip(dagger)
        self.inventory.equip(leather_armor)

    def descend_stairs(self) -> bool:
        """
        階段を下りる処理。

        Returns:
            階段を下りることができた場合True

        """
        current_floor = self.dungeon_manager.get_current_floor_data()

        # プレイヤーが下り階段の上にいるかチェック
        from pyrogue.map.tile import StairsDown

        if isinstance(current_floor.tiles[self.player.y][self.player.x], StairsDown):
            next_floor = self.dungeon_manager.descend_stairs()
            spawn_pos = self.dungeon_manager.get_player_spawn_position(next_floor)
            self.player.x, self.player.y = spawn_pos

            self.add_message(f"You descend to B{self.dungeon_manager.current_floor}F.")
            return True

        self.add_message("There are no stairs down here.")
        return False

    def ascend_stairs(self) -> bool:
        """
        階段を上る処理。

        Returns:
            階段を上ることができた場合True

        """
        current_floor = self.dungeon_manager.get_current_floor_data()

        # プレイヤーが上り階段の上にいるかチェック
        from pyrogue.map.tile import StairsUp

        if isinstance(current_floor.tiles[self.player.y][self.player.x], StairsUp):
            if self.dungeon_manager.current_floor > 1:
                next_floor = self.dungeon_manager.ascend_stairs()
                if next_floor:
                    spawn_pos = self.dungeon_manager.get_player_spawn_position(
                        next_floor
                    )
                    self.player.x, self.player.y = spawn_pos

                    self.add_message(
                        f"You ascend to B{self.dungeon_manager.current_floor}F."
                    )
                    return True
            else:
                # 地上への脱出チェック
                return self._check_game_completion()

        self.add_message("There are no stairs up here.")
        return False

    def _check_game_completion(self) -> bool:
        """
        ゲーム完了条件をチェック。

        Returns:
            ゲームが完了した場合True

        """
        # イェンダーの魔除けを持っているかチェック
        from pyrogue.entities.items.item import Item

        has_amulet = False
        for item in self.inventory.items:
            if isinstance(item, Item) and item.name == "The Amulet of Yendor":
                has_amulet = True
                break

        if has_amulet:
            self.add_message("You escaped with the Amulet of Yendor! You win!")
            if self.engine:
                self.engine.victory(
                    self.player.get_stats_dict(), self.dungeon_manager.current_floor
                )
            return True
        self.add_message("You need the Amulet of Yendor to leave the dungeon.")
        return False

    def check_player_death(self) -> bool:
        """
        プレイヤーの死亡状態をチェック。

        Returns:
            プレイヤーが死亡している場合True

        """
        return self.player.hp <= 0

    def _check_traps(self) -> None:
        """
        プレイヤーの現在位置にあるトラップをチェックし、発動処理を行う。

        隠れているトラップがある場合、それを発動させ、
        隣接位置に隠れているトラップがある場合は発見判定を行います。

        """
        current_floor = self.dungeon_manager.get_current_floor_data()
        player_x, player_y = self.player.x, self.player.y

        # 現在位置のトラップをチェック
        trap = current_floor.trap_manager.get_trap_at(player_x, player_y)
        if trap and trap.is_hidden:
            # 隠れているトラップを踏んだ場合、発動
            trap.activate(context=self)

        # 隣接位置のトラップ発見判定
        self._detect_nearby_traps()

    def _detect_nearby_traps(self) -> None:
        """
        プレイヤーの隣接位置にある隠れたトラップの発見判定を行う。

        プレイヤーのレベルや運に基づいて、隣接するトラップを
        発見する可能性があります。

        """
        import random

        current_floor = self.dungeon_manager.get_current_floor_data()
        player_x, player_y = self.player.x, self.player.y

        # 隣接する8方向をチェック
        directions = [
            (-1, -1), (0, -1), (1, -1),
            (-1,  0),          (1,  0),
            (-1,  1), (0,  1), (1,  1),
        ]

        for dx, dy in directions:
            x, y = player_x + dx, player_y + dy

            # 境界チェック
            if not (0 <= x < current_floor.tiles.shape[1] and
                    0 <= y < current_floor.tiles.shape[0]):
                continue

            # 隠れたトラップがあるかチェック
            trap = current_floor.trap_manager.get_trap_at(x, y)
            if trap and trap.is_hidden:
                # レベルベースの発見確率（レベル1で5%、レベル10で50%）
                detection_chance = min(0.5, 0.05 + (self.player.level - 1) * 0.05)

                if random.random() < detection_chance:
                    trap.reveal(context=self)
                    self.add_message(f"You notice something suspicious at ({x}, {y})...")
                    break  # 1ターンに1つまで

    def handle_disarm_trap(self) -> str | None:
        """
        プレイヤーの現在位置または隣接位置にあるトラップの解除を試行。

        Returns:
            解除処理の結果メッセージ。処理しなかった場合はNone

        """
        current_floor = self.dungeon_manager.get_current_floor_data()
        player_x, player_y = self.player.x, self.player.y

        # まず現在位置をチェック
        trap = current_floor.trap_manager.get_trap_at(player_x, player_y)
        if trap and trap.is_visible() and trap.is_active():
            success = trap.disarm(context=self)
            if success:
                return f"You successfully disarmed the {trap.name}!"
            else:
                return f"You failed to disarm the {trap.name}."

        # 隣接位置で発見済みのトラップを探す
        directions = [
            (-1, -1), (0, -1), (1, -1),
            (-1,  0),          (1,  0),
            (-1,  1), (0,  1), (1,  1),
        ]

        visible_traps = []
        for dx, dy in directions:
            x, y = player_x + dx, player_y + dy

            # 境界チェック
            if not (0 <= x < current_floor.tiles.shape[1] and
                    0 <= y < current_floor.tiles.shape[0]):
                continue

            trap = current_floor.trap_manager.get_trap_at(x, y)
            if trap and trap.is_visible() and trap.is_active():
                visible_traps.append((trap, x, y))

        if not visible_traps:
            return "There are no visible traps to disarm nearby."

        if len(visible_traps) == 1:
            # 1つだけの場合は自動的に解除を試行
            trap, x, y = visible_traps[0]
            success = trap.disarm(context=self)
            if success:
                return f"You successfully disarmed the {trap.name} at ({x}, {y})!"
            else:
                return f"You failed to disarm the {trap.name} at ({x}, {y})."
        else:
            # 複数ある場合は最初のものを対象とする（将来的には選択UIを実装）
            trap, x, y = visible_traps[0]
            success = trap.disarm(context=self)
            message = f"You attempt to disarm the {trap.name} at ({x}, {y}). "
            if success:
                message += "Success!"
            else:
                message += "Failed!"
            return message

    def check_victory(self) -> bool:
        """
        勝利条件をチェック。

        Returns:
            勝利条件を満たしている場合True

        """
        from pyrogue.entities.items.item import Item

        # イェンダーの魔除けを持っているかチェック
        for item in self.inventory.items:
            if isinstance(item, Item) and item.name == "The Amulet of Yendor":
                return True
        return False

    def get_current_floor_data(self):
        """
        現在の階層データを取得。

        Returns:
            現在の階層のFloorData

        """
        return self.dungeon_manager.get_current_floor_data()

    def _process_monster_turns(self) -> None:
        """
        すべてのモンスターのターンを処理。

        各モンスターはAIに基づいて移動、攻撃、あるいは待機します。
        """
        current_floor = self.dungeon_manager.get_current_floor_data()

        for monster in current_floor.monster_spawner.monsters[:]:
            if monster.hp <= 0:
                continue  # 死亡したモンスターはスキップ

            # モンスターAI処理
            self._monster_ai(monster, current_floor)

    def _monster_ai(self, monster, current_floor) -> None:
        """
        単体モンスターのAI処理。

        Args:
            monster: モンスターインスタンス
            current_floor: 現在のフロアデータ

        """
        # プレイヤーが視界内にいるかチェック
        if self._can_monster_see_player(monster, current_floor):
            # プレイヤーを追跡
            self._monster_chase_player(monster, current_floor)
        else:
            # ランダムに移動
            self._monster_random_move(monster, current_floor)

    def _can_monster_see_player(self, monster, current_floor) -> bool:
        """
        モンスターがプレイヤーを見ることができるかチェック。

        Args:
            monster: モンスターインスタンス
            current_floor: 現在のフロアデータ

        Returns:
            プレイヤーが視界内にいる場合True

        """
        # ユークリッド距離でチェック
        distance = (
            (monster.x - self.player.x) ** 2 + (monster.y - self.player.y) ** 2
        ) ** 0.5
        return distance <= monster.view_range

    def _monster_chase_player(self, monster, current_floor) -> None:
        """
        モンスターがプレイヤーを追跡。

        Args:
            monster: モンスターインスタンス
            current_floor: 現在のフロアデータ

        """
        dx, dy = monster.get_move_towards_player(self.player.x, self.player.y)
        target_x = monster.x + dx
        target_y = monster.y + dy

        # プレイヤーの位置にいる場合は攻撃
        if target_x == self.player.x and target_y == self.player.y:
            self._monster_attack_player(monster)
        elif self._can_monster_move_to(target_x, target_y, current_floor):
            monster.move(dx, dy)

    def _monster_random_move(self, monster, current_floor) -> None:
        """
        モンスターのランダム移動。

        Args:
            monster: モンスターインスタンス
            current_floor: 現在のフロアデータ

        """
        import random

        # 70%の確率で移動、そうでなければ待機
        if random.random() < 0.7:
            dx, dy = monster.get_random_move()
            target_x = monster.x + dx
            target_y = monster.y + dy

            if self._can_monster_move_to(target_x, target_y, current_floor):
                monster.move(dx, dy)

    def _can_monster_move_to(self, x: int, y: int, current_floor) -> bool:
        """
        モンスターが指定の位置に移動できるかチェック。

        Args:
            x: X座標
            y: Y座標
            current_floor: 現在のフロアデータ

        Returns:
            移動可能な場合True

        """
        # 境界チェック
        if not (
            0 <= x < current_floor.tiles.shape[1]
            and 0 <= y < current_floor.tiles.shape[0]
        ):
            return False

        # タイルが移動可能かチェック
        tile = current_floor.tiles[y][x]
        if not tile.walkable:
            return False

        # プレイヤーの位置かチェック
        if x == self.player.x and y == self.player.y:
            return False

        # 他のモンスターがいるかチェック
        if current_floor.monster_spawner.get_monster_at(x, y):
            return False

        return True

    def _monster_attack_player(self, monster) -> None:
        """
        モンスターがプレイヤーを攻撃。

        Args:
            monster: 攻撃するモンスター

        """
        damage = max(0, monster.attack - self.player.get_defense())
        self.player.hp = max(0, self.player.hp - damage)

        self.add_message(f"The {monster.name} hits you for {damage} damage!")

        # プレイヤーの死亡判定
        if self.player.hp <= 0:
            self.add_message("You died!")
            if self.engine:
                self.engine.game_over(
                    self.player.get_stats_dict(),
                    self.dungeon_manager.current_floor,
                    f"Killed by {monster.name}",
                )
