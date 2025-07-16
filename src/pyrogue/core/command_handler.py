"""
共通コマンドハンドラーモジュール。

GUIエンジンとCLIエンジンで共通のコマンド処理を提供します。
これにより、インターフェースに関係なく一貫したゲーム操作を実現します。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pyrogue.utils import game_logger

if TYPE_CHECKING:
    from pyrogue.core.game_logic import GameLogic
    from pyrogue.entities.actors.player import Player


class CommandResult:
    """コマンド実行結果を表現するクラス。"""

    def __init__(
        self,
        success: bool,
        message: str = "",
        should_end_turn: bool = False,
        should_quit: bool = False,
    ):
        self.success = success
        self.message = message
        self.should_end_turn = should_end_turn
        self.should_quit = should_quit


class CommandContext(ABC):
    """コマンド実行コンテキストの抽象基底クラス。"""

    @property
    @abstractmethod
    def game_logic(self) -> GameLogic:
        """ゲームロジックへのアクセス。"""

    @property
    @abstractmethod
    def player(self) -> Player:
        """プレイヤーへのアクセス。"""

    @abstractmethod
    def add_message(self, message: str) -> None:
        """メッセージの追加。"""

    @abstractmethod
    def display_player_status(self) -> None:
        """プレイヤーステータスの表示。"""

    @abstractmethod
    def display_inventory(self) -> None:
        """インベントリの表示。"""

    @abstractmethod
    def display_game_state(self) -> None:
        """ゲーム状態の表示。"""


class CommonCommandHandler:
    """GUIとCLIで共通のコマンド処理を行うハンドラー。"""

    def __init__(self, context: CommandContext):
        self.context = context

    def handle_command(self, command: str, args: list[str] | None = None) -> CommandResult:
        """
        コマンドを処理し、結果を返す。

        Args:
        ----
            command: 実行するコマンド
            args: コマンドの引数リスト

        Returns:
        -------
            CommandResult: コマンド実行結果

        """
        if args is None:
            args = []

        game_logger.debug(f"Handling command: {command} with args: {args}")

        # 移動コマンド
        if command in ["move", "north", "south", "east", "west", "n", "s", "e", "w"]:
            return self._handle_move_command(command, args)

        # アクションコマンド
        if command in ["get", "pickup", "g"]:
            return self._handle_get_item()
        if command in ["use", "u"]:
            return self._handle_use_item(args)
        if command in ["attack", "a"]:
            return self._handle_attack(args)
        if command in ["stairs", "stair"]:
            return self._handle_stairs(args)
        if command in ["open", "o"]:
            return self._handle_open_door()
        if command in ["close", "c"]:
            return self._handle_close_door()
        if command in ["search", "s"]:
            return self._handle_search()
        if command in ["disarm", "d"]:
            return self._handle_disarm_trap()
        if command in ["examine", "x"]:
            return self._handle_examine()
        if command in ["rest", "."]:
            return self._handle_rest()
        if command in ["long_rest", "R"]:
            return self._handle_long_rest()
        if command in ["throw", "t"]:
            return self._handle_throw(args)
        if command in ["wear", "w"]:
            return self._handle_wear(args)
        if command in ["zap", "z"]:
            return self._handle_zap(args)
        if command in ["auto_explore", "O"]:
            return self._handle_auto_explore()

        # 情報表示コマンド
        if command in ["status", "stat"]:
            self.context.display_player_status()
            return CommandResult(True)
        if command in ["inventory", "inv", "i"]:
            self.context.display_inventory()
            return CommandResult(True)
        if command in ["look", "l"]:
            self.context.display_game_state()
            return CommandResult(True)
        if command in ["symbol_explanation", "/"]:
            return self._handle_symbol_explanation()
        if command in ["identification_status", "\\"]:
            return self._handle_identification_status()
        if command in ["character_details", "@"]:
            return self._handle_character_details()
        if command in ["last_message", "ctrl_m"]:
            return self._handle_last_message()

        # デバッグコマンド
        if command == "debug":
            return self._handle_debug_command(args)

        # システムコマンド
        if command in ["quit", "exit", "q"]:
            return CommandResult(True, "Goodbye!", should_quit=True)
        if command == "help":
            return self._handle_help()
        if command in ["save", "s"]:
            return self._handle_save(args)
        if command == "load":
            return self._handle_load(args)

        return CommandResult(False, f"Unknown command: {command}")

    def _handle_move_command(self, command: str, args: list[str]) -> CommandResult:
        """移動コマンドの処理。"""
        # 方向の決定
        if command in ["north", "n"]:
            dx, dy = 0, -1
        elif command in ["south", "s"]:
            dx, dy = 0, 1
        elif command in ["east", "e"]:
            dx, dy = 1, 0
        elif command in ["west", "w"]:
            dx, dy = -1, 0
        elif command == "move" and args:
            direction = args[0].lower()
            if direction in ["north", "n"]:
                dx, dy = 0, -1
            elif direction in ["south", "s"]:
                dx, dy = 0, 1
            elif direction in ["east", "e"]:
                dx, dy = 1, 0
            elif direction in ["west", "w"]:
                dx, dy = -1, 0
            else:
                return CommandResult(False, "Invalid direction. Use north/south/east/west")
        else:
            return CommandResult(False, "Usage: move <direction> or use n/s/e/w")

        # 移動実行
        success = self.context.game_logic.handle_player_move(dx, dy)
        if success:
            return CommandResult(True, should_end_turn=True)
        return CommandResult(False, "Cannot move in that direction")

    def _handle_get_item(self) -> CommandResult:
        """アイテム取得の処理。"""
        success = self.context.game_logic.handle_get_item()
        if success:
            return CommandResult(True, should_end_turn=True)
        return CommandResult(False, "No item to pick up here")

    def _handle_use_item(self, args: list[str]) -> CommandResult:
        """アイテム使用の処理。"""
        if not args:
            return CommandResult(False, "Usage: use <item_name>")

        item_name = " ".join(args)
        success = self.context.game_logic.handle_use_item(item_name)
        if success:
            return CommandResult(True, should_end_turn=True)
        return CommandResult(False, f"Cannot use {item_name}")

    def _handle_attack(self, args: list[str]) -> CommandResult:
        """攻撃の処理。"""
        # 隣接する敵への攻撃
        success = self.context.game_logic.handle_combat()
        if success:
            return CommandResult(True, should_end_turn=True)
        return CommandResult(False, "No enemy to attack nearby")

    def _handle_stairs(self, args: list[str]) -> CommandResult:
        """階段の処理。"""
        if not args:
            return CommandResult(False, "Usage: stairs <up/down>")

        direction = args[0].lower()
        if direction in ["up", "u"]:
            success = self.context.game_logic.handle_stairs_up()
        elif direction in ["down", "d"]:
            success = self.context.game_logic.handle_stairs_down()
        else:
            return CommandResult(False, "Usage: stairs <up/down>")

        if success:
            return CommandResult(True, should_end_turn=True)
        return CommandResult(False, "No stairs here or cannot use stairs")

    def _handle_open_door(self) -> CommandResult:
        """扉を開く処理。"""
        success = self.context.game_logic.handle_open_door()
        if success:
            return CommandResult(True, should_end_turn=True)
        return CommandResult(False, "No door to open nearby")

    def _handle_close_door(self) -> CommandResult:
        """扉を閉じる処理。"""
        success = self.context.game_logic.handle_close_door()
        if success:
            return CommandResult(True, should_end_turn=True)
        return CommandResult(False, "No door to close nearby")

    def _handle_search(self) -> CommandResult:
        """隠し扉の探索処理。"""
        success = self.context.game_logic.handle_search()
        if success:
            return CommandResult(True, should_end_turn=True)
        return CommandResult(False, "Nothing found")

    def _handle_disarm_trap(self) -> CommandResult:
        """トラップ解除の処理。"""
        success = self.context.game_logic.handle_disarm_trap()
        if success:
            return CommandResult(True, should_end_turn=True)
        return CommandResult(False, "No trap to disarm here")

    def _handle_help(self) -> CommandResult:
        """ヘルプ表示。"""
        help_text = """
Available Commands:
  Movement:
    north/n, south/s, east/e, west/w - Move in direction
    move <direction> - Move in specified direction

  Actions:
    get/g - Pick up item
    use <item> - Use item from inventory
    attack/a - Attack nearby enemy
    stairs <up/down> - Use stairs
    open/o - Open door
    close/c - Close door
    search/s - Search for hidden doors
    disarm/d - Disarm trap
    examine/x - Examine surroundings
    rest/. - Rest for one turn
    long_rest/R - Rest until fully healed
    throw/t <item> - Throw item
    wear/w <item> - Wear/equip item
    zap/z <wand> <direction> - Zap wand in direction
    auto_explore/O - Auto-explore unexplored areas

  Information:
    status/stat - Show player status
    inventory/inv/i - Show inventory
    look/l - Look around
    symbol_explanation/ - Show symbol meanings
    identification_status/\\ - Show item identification status
    character_details/@ - Show detailed character info
    last_message/ctrl_m - Show recent messages

  System:
    help - Show this help
    save/s - Save game
    load - Load game
    quit/exit/q - Quit game

  Debug:
    debug yendor - Get Amulet of Yendor
    debug floor <number> - Teleport to floor
    debug pos <x> <y> - Teleport to position
    debug hp <value> - Set HP to value
    debug damage <value> - Take damage
    debug gold <amount> - Place gold at current position
        """
        self.context.add_message(help_text.strip())
        return CommandResult(True)

    def _handle_debug_command(self, args: list[str]) -> CommandResult:
        """
        デバッグコマンドの処理。

        Args:
        ----
            args: コマンド引数

        Returns:
        -------
            コマンド実行結果

        """
        if not args:
            self.context.add_message(
                "Debug commands: yendor, floor <number>, pos <x> <y>, hp <value>, damage <value>, gold <amount>"
            )
            return CommandResult(True)

        debug_cmd = args[0].lower()

        if debug_cmd == "yendor":
            # イェンダーのアミュレットを付与
            player = self.context.player
            player.has_amulet = True
            self.context.add_message("You now possess the Amulet of Yendor!")

            # B1Fに脱出階段を生成
            from pyrogue.entities.items.amulet import AmuletOfYendor

            amulet = AmuletOfYendor(0, 0)  # 位置は関係ない
            game_logic = self.context.game_logic

            # 現在B1Fにいる場合は、階段を生成してプレイヤーを配置
            if game_logic.dungeon_manager.current_floor == 1:
                b1f_data = game_logic.dungeon_manager.get_floor(1)
                if b1f_data:
                    stairs_pos = amulet._place_escape_stairs_on_floor(b1f_data)
                    if stairs_pos:
                        player.x, player.y = stairs_pos
                        self.context.add_message(
                            f"You are teleported to the escape stairs at ({stairs_pos[0]}, {stairs_pos[1]})"
                        )
            else:
                amulet._create_escape_stairs(self.context)

            return CommandResult(True)

        if debug_cmd == "floor" and len(args) > 1:
            try:
                floor_num = int(args[1])
                game_logic = self.context.game_logic
                game_logic.dungeon_manager.set_current_floor(floor_num)

                # プレイヤーの位置を新しい階層に設定
                floor_data = game_logic.dungeon_manager.get_current_floor_data()
                if floor_data:
                    player = self.context.player
                    # 適当な位置を探す
                    spawn_pos = game_logic.dungeon_manager.get_player_spawn_position(floor_data)
                    player.x, player.y = spawn_pos
                    player.update_deepest_floor(floor_num)

                self.context.add_message(f"Teleported to floor B{floor_num}F")
                return CommandResult(True)
            except Exception as e:
                self.context.add_message(f"Floor teleport failed: {e}")
                return CommandResult(False)

        elif debug_cmd == "pos" and len(args) > 2:
            try:
                x = int(args[1])
                y = int(args[2])
                player = self.context.player
                player.x = x
                player.y = y
                self.context.add_message(f"Player teleported to ({x}, {y})")
                return CommandResult(True)
            except Exception as e:
                self.context.add_message(f"Position teleport failed: {e}")
                return CommandResult(False)

        elif debug_cmd == "hp" and len(args) > 1:
            try:
                hp_value = int(args[1])
                player = self.context.player
                player.hp = max(0, hp_value)
                self.context.add_message(f"Player HP set to {player.hp}")

                # 死亡チェック
                if player.hp <= 0:
                    self.context.add_message("You have died!")
                    self.context.add_message("GAME OVER")
                    # 死亡処理
                    if hasattr(self.context, "game_logic") and self.context.game_logic:
                        self.context.game_logic.record_game_over("Debug death")

                return CommandResult(True)
            except Exception as e:
                self.context.add_message(f"HP set failed: {e}")
                return CommandResult(False)

        elif debug_cmd == "damage" and len(args) > 1:
            try:
                damage_value = int(args[1])
                player = self.context.player
                player.hp = max(0, player.hp - damage_value)
                self.context.add_message(f"Player takes {damage_value} damage! HP: {player.hp}")

                # 死亡チェック
                if player.hp <= 0:
                    self.context.add_message("You have died!")
                    self.context.add_message("GAME OVER")
                    # 死亡処理
                    if hasattr(self.context, "game_logic") and self.context.game_logic:
                        self.context.game_logic.record_game_over("Debug damage")

                return CommandResult(True)
            except Exception as e:
                self.context.add_message(f"Damage failed: {e}")
                return CommandResult(False)

        elif debug_cmd == "gold" and len(args) > 1:
            try:
                gold_amount = int(args[1])
                player = self.context.player

                # プレイヤーの位置にゴールドアイテムを配置
                from pyrogue.entities.items.item import Gold

                gold_item = Gold(player.x, player.y, gold_amount)

                # 現在のフロアにアイテムを追加
                if hasattr(self.context, "dungeon_manager"):
                    floor_data = self.context.dungeon_manager.get_current_floor_data()
                    if floor_data:
                        floor_data.items.append(gold_item)
                        self.context.add_message(f"Placed {gold_amount} gold at your location.")
                    else:
                        self.context.add_message("Failed to get floor data.")
                else:
                    self.context.add_message("Dungeon manager not available.")

                return CommandResult(True)
            except Exception as e:
                self.context.add_message(f"Gold placement failed: {e}")
                return CommandResult(False)

        else:
            self.context.add_message("Unknown debug command")
            return CommandResult(False)

    def _handle_examine(self) -> CommandResult:
        """調査・検査コマンドの処理。"""
        player = self.context.player
        game_logic = self.context.game_logic

        # プレイヤーの足元と周囲8マスを調査
        examination_results = []

        # 足元
        current_floor = game_logic.get_current_floor_data()
        if current_floor:
            # 足元のタイル
            tile = current_floor.tiles[player.y, player.x]
            examination_results.append(f"You are standing on {tile.__class__.__name__}")

            # 足元のアイテム
            items_here = [
                item for item in current_floor.item_spawner.items if item.x == player.x and item.y == player.y
            ]
            if items_here:
                examination_results.append(f"Items here: {', '.join(item.name for item in items_here)}")

            # 周囲8マス
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue

                    x, y = player.x + dx, player.y + dy
                    if 0 <= x < current_floor.tiles.shape[1] and 0 <= y < current_floor.tiles.shape[0]:
                        tile = current_floor.tiles[y, x]
                        direction = self._get_direction_name(dx, dy)
                        examination_results.append(f"{direction}: {tile.__class__.__name__}")

        for result in examination_results:
            self.context.add_message(result)

        return CommandResult(True, should_end_turn=True)

    def _handle_rest(self) -> CommandResult:
        """休憩コマンドの処理。"""
        # 1ターン休憩
        self.context.add_message("You rest for a moment.")
        return CommandResult(True, should_end_turn=True)

    def _handle_long_rest(self) -> CommandResult:
        """長時間休憩コマンドの処理。"""
        player = self.context.player
        game_logic = self.context.game_logic

        # 敵が近くにいる場合は休憩不可
        current_floor = game_logic.get_current_floor_data()
        if current_floor:
            for monster in current_floor.monster_spawner.monsters:
                distance = abs(monster.x - player.x) + abs(monster.y - player.y)
                if distance <= 5:
                    self.context.add_message("You cannot rest with enemies nearby!")
                    return CommandResult(False)

        # 完全回復するまで休憩
        turns_rested = 0
        while player.hp < player.max_hp:
            player.hp = min(player.max_hp, player.hp + 1)
            turns_rested += 1

            # 100ターン以上は無理
            if turns_rested >= 100:
                break

        self.context.add_message(f"You rest for {turns_rested} turns and recover {turns_rested} HP.")
        return CommandResult(True, should_end_turn=True)

    def _handle_throw(self, args: list[str]) -> CommandResult:
        """投げるコマンドの処理。"""
        if not args:
            return CommandResult(False, "Usage: throw <item_name>")

        item_name = " ".join(args)
        player = self.context.player
        inventory = self.context.game_logic.inventory

        # アイテムを検索
        item_to_throw = None
        for item in inventory.items:
            if item.name.lower() == item_name.lower():
                item_to_throw = item
                break

        if not item_to_throw:
            return CommandResult(False, f"You don't have {item_name}")

        # 投擲処理（簡単な実装）
        inventory.remove_item(item_to_throw)
        self.context.add_message(f"You throw the {item_to_throw.name}.")

        return CommandResult(True, should_end_turn=True)

    def _handle_wear(self, args: list[str]) -> CommandResult:
        """装備コマンドの処理。"""
        if not args:
            return CommandResult(False, "Usage: wear <item_name>")

        item_name = " ".join(args)
        player = self.context.player
        inventory = self.context.game_logic.inventory

        # アイテムを検索
        item_to_equip = None
        for item in inventory.items:
            if item.name.lower() == item_name.lower():
                item_to_equip = item
                break

        if not item_to_equip:
            return CommandResult(False, f"You don't have {item_name}")

        # 装備処理
        old_item = player.equip_item(item_to_equip)
        if old_item:
            self.context.add_message(f"You remove the {old_item.name} and wear the {item_to_equip.name}.")
        else:
            self.context.add_message(f"You wear the {item_to_equip.name}.")

        return CommandResult(True, should_end_turn=True)

    def _handle_zap(self, args: list[str]) -> CommandResult:
        """ワンド使用コマンドの処理。"""
        if not args:
            return CommandResult(False, "Usage: zap <wand_name> <direction>")

        if len(args) < 2:
            return CommandResult(False, "Usage: zap <wand_name> <direction>")

        wand_name = args[0]
        direction = args[1]

        player = self.context.player
        inventory = self.context.game_logic.inventory

        # ワンドを検索
        wand_to_use = None
        for item in inventory.items:
            if item.name.lower() == wand_name.lower() and hasattr(item, "charges"):
                wand_to_use = item
                break

        if not wand_to_use:
            return CommandResult(False, f"You don't have a wand called {wand_name}")

        if not wand_to_use.has_charges():
            return CommandResult(False, f"The {wand_to_use.name} has no charges left.")

        # 方向を解析
        direction_map = {
            "north": (0, -1),
            "n": (0, -1),
            "south": (0, 1),
            "s": (0, 1),
            "east": (1, 0),
            "e": (1, 0),
            "west": (-1, 0),
            "w": (-1, 0),
        }

        if direction.lower() not in direction_map:
            return CommandResult(False, "Invalid direction. Use north/south/east/west")

        dx, dy = direction_map[direction.lower()]

        # ワンドを使用
        context = self.context
        success = wand_to_use.apply_effect(context, (dx, dy))

        if success:
            self.context.add_message(f"You zap the {wand_to_use.name} {direction}.")
            return CommandResult(True, should_end_turn=True)
        else:
            return CommandResult(False, f"The {wand_to_use.name} fizzles.")

    def _handle_auto_explore(self) -> CommandResult:
        """自動探索コマンドの処理。"""
        try:
            player = self.context.player
            game_logic = self.context.game_logic
            current_floor = game_logic.get_current_floor_data()

            if not current_floor:
                self.context.add_message("Cannot auto-explore: no floor data available.")
                return CommandResult(False)

            # 敵が近くにいる場合は自動探索を停止
            nearby_enemies = self._check_nearby_enemies(current_floor, player)
            if nearby_enemies:
                self.context.add_message(f"Auto-explore stopped: {nearby_enemies[0].name} nearby!")
                return CommandResult(False)

            # 未探索エリアを探す
            target_pos = self._find_nearest_unexplored_area(current_floor, player)

            if target_pos is None:
                self.context.add_message("Auto-explore complete: all areas explored.")
                return CommandResult(True)

            # 目標地点への次の一歩を計算
            next_move = self._calculate_next_move(current_floor, player, target_pos)

            if next_move is None:
                self.context.add_message("Auto-explore stopped: no safe path found.")
                return CommandResult(False)

            # 移動を実行
            dx, dy = next_move
            success = game_logic.handle_player_move(dx, dy)

            if success:
                self.context.add_message(f"Auto-exploring... (target: {target_pos[0]}, {target_pos[1]})")
                return CommandResult(True, should_end_turn=True)
            else:
                self.context.add_message("Auto-explore stopped: movement blocked.")
                return CommandResult(False)

        except Exception as e:
            self.context.add_message(f"Auto-explore error: {e}")
            return CommandResult(False)

    def _check_nearby_enemies(self, current_floor, player) -> list:
        """プレイヤー周囲の敵をチェック。"""
        nearby_enemies = []

        for monster in current_floor.monster_spawner.monsters:
            distance = abs(monster.x - player.x) + abs(monster.y - player.y)
            if distance <= 3:  # 3マス以内
                nearby_enemies.append(monster)

        return nearby_enemies

    def _find_nearest_unexplored_area(self, current_floor, player) -> tuple[int, int] | None:
        """最も近い未探索エリアを見つける。"""
        from pyrogue.map.tile import Floor

        explored = current_floor.explored
        tiles = current_floor.tiles
        player_pos = (player.x, player.y)

        min_distance = float("inf")
        target_pos = None

        # 探索済みエリアの境界付近で未探索の床タイルを探す
        for y in range(1, tiles.shape[0] - 1):
            for x in range(1, tiles.shape[1] - 1):
                # 未探索の床タイルかチェック
                if not explored[y, x] and isinstance(tiles[y, x], Floor):
                    # 隣接する探索済みエリアがあるかチェック
                    has_explored_neighbor = False
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < explored.shape[0] and 0 <= nx < explored.shape[1] and explored[ny, nx]:
                                has_explored_neighbor = True
                                break
                        if has_explored_neighbor:
                            break

                    # 探索境界の未探索エリアを優先
                    if has_explored_neighbor:
                        distance = abs(x - player_pos[0]) + abs(y - player_pos[1])
                        if distance < min_distance:
                            min_distance = distance
                            target_pos = (x, y)

        return target_pos

    def _calculate_next_move(self, current_floor, player, target_pos) -> tuple[int, int] | None:
        """目標地点への次の移動を計算（簡易A*アルゴリズム）。"""
        from pyrogue.map.tile import Door, Floor

        tiles = current_floor.tiles
        player_pos = (player.x, player.y)
        target_x, target_y = target_pos

        # 目標への大まかな方向を計算
        dx = 0
        dy = 0

        if target_x > player.x:
            dx = 1
        elif target_x < player.x:
            dx = -1

        if target_y > player.y:
            dy = 1
        elif target_y < player.y:
            dy = -1

        # 候補移動方向のリスト（優先順位付き）
        moves = []

        # 直接的な移動を最優先
        if dx != 0 or dy != 0:
            moves.append((dx, dy))

        # 斜め移動が不可能な場合の代替案
        if dx != 0:
            moves.append((dx, 0))
        if dy != 0:
            moves.append((0, dy))

        # 各移動候補をチェック
        for move_dx, move_dy in moves:
            new_x = player.x + move_dx
            new_y = player.y + move_dy

            # 境界チェック
            if new_x < 0 or new_x >= tiles.shape[1] or new_y < 0 or new_y >= tiles.shape[0]:
                continue

            # タイルの通行可能性をチェック
            tile = tiles[new_y, new_x]
            if isinstance(tile, (Floor, Door)):
                # 扉の場合は開いているかチェック
                if isinstance(tile, Door) and not tile.is_open:
                    continue

                # モンスターがいないかチェック
                monster_at_pos = current_floor.monster_spawner.get_monster_at(new_x, new_y)
                if monster_at_pos is None:
                    return (move_dx, move_dy)

        return None

    def _handle_symbol_explanation(self) -> CommandResult:
        """シンボル説明の処理。"""
        explanation = """
Symbol Explanation:
  @ - Player
  # - Wall
  . - Floor
  + - Closed door
  / - Open door
  % - Food
  ! - Potion
  ? - Scroll
  ) - Weapon
  [ - Armor
  = - Ring
  / - Wand
  $ - Gold
  < - Stairs up
  > - Stairs down
  ^ - Trap
  A-Z - Monsters
        """
        self.context.add_message(explanation.strip())
        return CommandResult(True)

    def _handle_identification_status(self) -> CommandResult:
        """アイテム識別状況の処理。"""
        player = self.context.player
        identification = player.identification

        self.context.add_message("Identification Status:")
        self.context.add_message(f"Identified items: {len(identification.identified_items)}")

        return CommandResult(True)

    def _handle_character_details(self) -> CommandResult:
        """キャラクター詳細の処理。"""
        player = self.context.player

        details = f"""
Character Details:
  Name: {player.name}
  Level: {player.level}
  HP: {player.hp}/{player.max_hp}
  Attack: {player.get_attack()}
  Defense: {player.get_defense()}
  Gold: {player.gold}
  Hunger: {player.hunger}%
  Experience: {player.exp}
  Monsters Killed: {player.monsters_killed}
  Deepest Floor: {player.deepest_floor}
  Turns Played: {player.turns_played}
  Score: {player.calculate_score()}
        """
        self.context.add_message(details.strip())
        return CommandResult(True)

    def _handle_last_message(self) -> CommandResult:
        """最後のメッセージ表示の処理。"""
        game_logic = self.context.game_logic

        if hasattr(game_logic, "message_log") and game_logic.message_log:
            recent_messages = game_logic.message_log[-5:]  # 最新の5つ
            self.context.add_message("Recent messages:")
            for msg in recent_messages:
                self.context.add_message(f"  {msg}")
        else:
            self.context.add_message("No recent messages.")

        return CommandResult(True)

    def _get_direction_name(self, dx: int, dy: int) -> str:
        """方向名を取得。"""
        if dx == 0 and dy == -1:
            return "North"
        elif dx == 0 and dy == 1:
            return "South"
        elif dx == 1 and dy == 0:
            return "East"
        elif dx == -1 and dy == 0:
            return "West"
        elif dx == -1 and dy == -1:
            return "Northwest"
        elif dx == 1 and dy == -1:
            return "Northeast"
        elif dx == -1 and dy == 1:
            return "Southwest"
        elif dx == 1 and dy == 1:
            return "Southeast"
        else:
            return "Unknown"

    def _handle_save(self, args: list[str]) -> CommandResult:
        """
        セーブコマンドの処理。

        Args:
        ----
            args: コマンド引数（現在未使用）

        Returns:
        -------
            CommandResult: セーブ実行結果
        """
        # SaveManagerを使用してセーブを実行
        from pyrogue.core.save_manager import SaveManager

        save_manager = SaveManager()

        # 現在のゲーム状態を取得
        try:
            game_data = self._create_save_data()
            success = save_manager.save_game_state(game_data)

            if success:
                self.context.add_message("Game saved successfully!")
                return CommandResult(True)
            else:
                self.context.add_message("Failed to save game.")
                return CommandResult(False)

        except Exception as e:
            self.context.add_message(f"Error saving game: {e}")
            return CommandResult(False)

    def _handle_load(self, args: list[str]) -> CommandResult:
        """
        ロードコマンドの処理。

        Args:
        ----
            args: コマンド引数（現在未使用）

        Returns:
        -------
            CommandResult: ロード実行結果
        """
        # SaveManagerを使用してロードを実行
        from pyrogue.core.save_manager import SaveManager

        save_manager = SaveManager()

        try:
            save_data = save_manager.load_game_state()

            if save_data is None:
                self.context.add_message("No save file found.")
                return CommandResult(False)

            # セーブデータの復元
            success = self._restore_save_data(save_data)

            if success:
                self.context.add_message("Game loaded successfully!")
                return CommandResult(True)
            else:
                self.context.add_message("Failed to load game.")
                return CommandResult(False)

        except Exception as e:
            self.context.add_message(f"Error loading game: {e}")
            return CommandResult(False)

    def _create_save_data(self) -> dict[str, Any]:
        """
        セーブデータを作成（GUIモードと同じ完全保存）。

        Returns
        -------
            dict: セーブデータ辞書
        """
        player = self.context.player
        dungeon_manager = self.context.game_logic.dungeon_manager

        # GUIモードと同じ完全なセーブデータを作成
        save_data = {
            "player": self._serialize_player(player),
            "inventory": self._serialize_inventory(self.context.game_logic.inventory),
            "current_floor": dungeon_manager.current_floor,
            "floor_data": self._serialize_all_floors(dungeon_manager.floors),
            "message_log": self.context.game_logic.message_log,
            "has_amulet": getattr(player, "has_amulet", False),
            "version": "1.0",
        }

        return save_data

    def _restore_save_data(self, save_data: dict[str, Any]) -> bool:
        """
        セーブデータからゲーム状態を復元（GUIモードと同じ完全復元）。

        Args:
        ----
            save_data: セーブデータ辞書

        Returns:
        -------
            bool: 復元に成功した場合True
        """
        try:
            # プレイヤー状態の復元
            player_data = save_data.get("player", {})
            if player_data:
                self._deserialize_player(player_data)

            # インベントリの復元
            inventory_data = save_data.get("inventory", {})
            if inventory_data:
                self._deserialize_inventory(inventory_data)

            # ダンジョン状態の復元
            dungeon_manager = self.context.game_logic.dungeon_manager
            dungeon_manager.current_floor = save_data.get("current_floor", 1)

            # フロアデータを正しく復元
            floor_data = save_data.get("floor_data", {})
            if floor_data:
                self._restore_floor_data(floor_data)

            # メッセージログの復元
            message_log = save_data.get("message_log", [])
            if hasattr(self.context.game_logic, "message_log"):
                # GameLogicのmessage_logを更新
                self.context.game_logic.message_log.clear()
                self.context.game_logic.message_log.extend(message_log)

                # GameContextのmessage_logも同じリストを参照するよう更新
                self.context.message_log = self.context.game_logic.message_log

            # アミュレット状態の復元
            if "has_amulet" in save_data:
                self.context.player.has_amulet = save_data["has_amulet"]

            # 現在のフロアを読み込み
            self._load_current_floor()

            return True

        except Exception as e:
            print(f"Error restoring save data: {e}")
            return False

    def _deserialize_player(self, player_data: dict[str, Any]) -> None:
        """
        プレイヤーデータをデシリアライズ。
        """
        player = self.context.player

        player.x = player_data.get("x", player.x)
        player.y = player_data.get("y", player.y)
        player.hp = player_data.get("hp", player.hp)
        player.max_hp = player_data.get("max_hp", player.max_hp)
        player.level = player_data.get("level", player.level)
        player.exp = player_data.get("exp", player.exp)
        player.gold = player_data.get("gold", player.gold)
        player.attack = player_data.get("attack", player.attack)
        player.defense = player_data.get("defense", player.defense)

        # オプション属性の復元
        if "hunger" in player_data:
            player.hunger = player_data["hunger"]
        if "mp" in player_data:
            player.mp = player_data["mp"]
        if "max_mp" in player_data:
            player.max_mp = player_data["max_mp"]
        if "has_amulet" in player_data:
            player.has_amulet = player_data["has_amulet"]

    def _deserialize_inventory(self, inventory_data: dict[str, Any]) -> None:
        """
        インベントリデータをデシリアライズ。
        軽量な状態データから完全なアイテムオブジェクトを復元する。
        """
        inventory = self.context.game_logic.inventory

        # アイテムリストの復元
        items_data = inventory_data.get("items", [])
        inventory.items = [self._deserialize_item(item_data) for item_data in items_data]

        # 装備品の復元（インデックスベース）
        equipped_data = inventory_data.get("equipped", {})
        inventory.equipped = {
            "weapon": None,
            "armor": None,
            "ring_left": None,
            "ring_right": None,
        }

        # インデックスから実際のアイテムオブジェクトに変換
        for slot, index in equipped_data.items():
            if index is not None and 0 <= index < len(inventory.items):
                inventory.equipped[slot] = inventory.items[index]

    def _serialize_player(self, player) -> dict[str, Any]:
        """
        プレイヤーオブジェクトをシリアライズ。
        """
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
        }

    def _serialize_inventory(self, inventory) -> dict[str, Any]:
        """
        インベントリをシリアライズ。
        """
        if inventory is None:
            return {"items": [], "equipped": {"weapon": None, "armor": None, "ring_left": None, "ring_right": None}}

        # アイテムリストのシリアライズ
        items_data = [self._serialize_item(item) for item in inventory.items]

        # 装備状態をインデックスベースで保存
        equipped_indices = {}
        for slot, item in inventory.equipped.items():
            if item is not None:
                # インベントリ内でのインデックスを検索
                try:
                    index = inventory.items.index(item)
                    equipped_indices[slot] = index
                except ValueError:
                    # インベントリに見つからない場合はNone
                    equipped_indices[slot] = None
            else:
                equipped_indices[slot] = None

        return {
            "items": items_data,
            "equipped": equipped_indices,
        }

    def _serialize_item(self, item) -> dict[str, Any]:
        """
        アイテムを軽量な状態データとしてシリアライズ。
        IDベース＋状態データで実装詳細に依存しない形式。
        """
        from pyrogue.entities.items.item_factory import ItemFactory

        # アイテムIDを取得（オブジェクトから直接、または名前から）
        item_id = getattr(item, "item_id", None)
        if item_id is None or item_id == 0:
            # IDが設定されていない場合は名前から取得
            item_id = ItemFactory.get_id_by_name(item.name)

        data = {
            "item_id": item_id,  # 主キー：アイテムID
            "name": item.name,  # 後方互換性用：アイテム名
            "count": getattr(item, "stack_count", 1),
            "identified": getattr(item, "identified", True),
            "blessed": getattr(item, "blessed", False),
            "cursed": getattr(item, "cursed", False),
            "enchantment": getattr(item, "enchantment", 0),
        }

        # アイテム固有の状態属性
        if hasattr(item, "charges"):
            data["charges"] = item.charges
        if hasattr(item, "amount"):  # Gold用
            data["amount"] = item.amount
        if hasattr(item, "bonus"):  # Ring用
            data["bonus"] = item.bonus
        if hasattr(item, "effect") and hasattr(item, "item_type") and item.item_type == "RING":
            # Ringの効果名のみ保存（文字列として）
            data["effect_name"] = (
                getattr(item.effect, "name", item.effect) if isinstance(item.effect, str) else item.effect
            )

        return data

    def _deserialize_item(self, item_data: dict[str, Any]):
        """
        IDベースでアイテムオブジェクトを復元。名前変更に対応し、後方互換性も維持。
        """
        from pyrogue.entities.items.item_factory import ItemFactory
        from pyrogue.entities.items.item_spawner import ItemSpawner

        item_id = item_data.get("item_id")
        name = item_data.get("name", "Unknown Item")

        # IDベース復元を優先
        if item_id is not None:
            try:
                item = ItemFactory.create_by_id(item_id, 0, 0)
            except ValueError:
                # 不明なIDの場合は名前ベースにフォールバック
                spawner = ItemSpawner(floor=1)
                item = self._create_item_by_name(spawner, name)
        else:
            # IDがない場合（旧セーブデータ）は名前ベース
            spawner = ItemSpawner(floor=1)
            item = self._create_item_by_name(spawner, name)

        if item is None:
            # フォールバック: 基本的なアイテムを作成
            from pyrogue.entities.items.item import Item

            item = Item(x=0, y=0, name=name, char="?", color=(255, 255, 255), item_type="MISC", cursed=False)

        # 保存された状態を適用
        self._apply_item_state(item, item_data)

        return item

    def _create_item_by_name(self, spawner, name: str):
        """
        アイテム名から適切なアイテムオブジェクトを直接生成。
        ItemSpawnerは使用せず、直接アイテムクラスを使用する。
        """
        from pyrogue.entities.items.amulet import AmuletOfYendor
        from pyrogue.entities.items.effects import (
            ConfusionPotionEffect,
            EnchantArmorEffect,
            EnchantWeaponEffect,
            HallucinationPotionEffect,
            HealingEffect,
            IdentifyEffect,
            LightEffect,
            LightningWandEffect,
            LightWandEffect,
            MagicMappingEffect,
            MagicMissileWandEffect,
            NothingWandEffect,
            NutritionEffect,
            ParalysisPotionEffect,
            PoisonPotionEffect,
            RemoveCurseEffect,
            TeleportEffect,
        )
        from pyrogue.entities.items.item import Armor, Food, Gold, Potion, Ring, Scroll, Wand, Weapon

        try:
            # 食料
            if name == "Food Ration":
                return Food(0, 0, "Food Ration", NutritionEffect(25))

            # ポーション
            elif name == "Potion of Healing":
                return Potion(0, 0, "Potion of Healing", HealingEffect(25))
            elif name == "Potion of Extra Healing":
                return Potion(0, 0, "Potion of Extra Healing", HealingEffect(50))
            elif name == "Potion of Poison":
                return Potion(0, 0, "Potion of Poison", PoisonPotionEffect())
            elif name == "Potion of Paralysis":
                return Potion(0, 0, "Potion of Paralysis", ParalysisPotionEffect())
            elif name == "Potion of Confusion":
                return Potion(0, 0, "Potion of Confusion", ConfusionPotionEffect())
            elif name == "Potion of Hallucination":
                return Potion(0, 0, "Potion of Hallucination", HallucinationPotionEffect())

            # 巻物
            elif name == "Scroll of Light":
                return Scroll(0, 0, "Scroll of Light", LightEffect())
            elif name == "Scroll of Teleportation":
                return Scroll(0, 0, "Scroll of Teleportation", TeleportEffect())
            elif name == "Scroll of Magic Mapping":
                return Scroll(0, 0, "Scroll of Magic Mapping", MagicMappingEffect())
            elif name == "Scroll of Identify":
                return Scroll(0, 0, "Scroll of Identify", IdentifyEffect())
            elif name == "Scroll of Remove Curse":
                return Scroll(0, 0, "Scroll of Remove Curse", RemoveCurseEffect())
            elif name == "Scroll of Enchant Weapon":
                return Scroll(0, 0, "Scroll of Enchant Weapon", EnchantWeaponEffect())
            elif name == "Scroll of Enchant Armor":
                return Scroll(0, 0, "Scroll of Enchant Armor", EnchantArmorEffect())

            # 杖
            elif name == "Wand of Magic Missile":
                return Wand(0, 0, "Wand of Magic Missile", MagicMissileWandEffect(), 3)
            elif name == "Wand of Lightning":
                return Wand(0, 0, "Wand of Lightning", LightningWandEffect(), 3)
            elif name == "Wand of Light":
                return Wand(0, 0, "Wand of Light", LightWandEffect(), 3)
            elif name == "Wand of Nothing":
                return Wand(0, 0, "Wand of Nothing", NothingWandEffect(), 3)

            # 武器
            elif name == "Dagger":
                return Weapon(0, 0, "Dagger", 2)
            elif name == "Short Sword":
                return Weapon(0, 0, "Short Sword", 3)
            elif name == "Long Sword":
                return Weapon(0, 0, "Long Sword", 4)
            elif name == "Mace":
                return Weapon(0, 0, "Mace", 3)

            # 防具
            elif name == "Leather Armor":
                return Armor(0, 0, "Leather Armor", 2)
            elif name == "Chain Mail":
                return Armor(0, 0, "Chain Mail", 3)
            elif name == "Plate Mail":
                return Armor(0, 0, "Plate Mail", 4)

            # 指輪
            elif name == "Ring of Protection":
                return Ring(0, 0, "Ring of Protection", "protection", 1)
            elif name == "Ring of Add Strength":
                return Ring(0, 0, "Ring of Add Strength", "strength", 1)
            elif name == "Ring of Sustain Strength":
                return Ring(0, 0, "Ring of Sustain Strength", "sustain", 1)
            elif name == "Ring of Searching":
                return Ring(0, 0, "Ring of Searching", "search", 1)
            elif name == "Ring of See Invisible":
                return Ring(0, 0, "Ring of See Invisible", "see_invisible", 1)
            elif name == "Ring of Regeneration":
                return Ring(0, 0, "Ring of Regeneration", "regeneration", 1)

            # 特別なアイテム
            elif name == "Gold":
                return Gold(0, 0, 1)
            elif name == "Amulet of Yendor":
                return AmuletOfYendor(0, 0)

        except Exception as e:
            print(f"Warning: Failed to create item '{name}': {e}")

        return None

    def _apply_item_state(self, item, item_data: dict[str, Any]):
        """
        保存された状態データをアイテムに適用。
        """
        # 基本状態の適用
        if "count" in item_data and hasattr(item, "stack_count"):
            item.stack_count = max(1, item_data["count"])

        if "identified" in item_data and hasattr(item, "identified"):
            item.identified = item_data["identified"]

        if "blessed" in item_data and hasattr(item, "blessed"):
            item.blessed = item_data["blessed"]

        if "cursed" in item_data and hasattr(item, "cursed"):
            item.cursed = item_data["cursed"]

        if "enchantment" in item_data and hasattr(item, "enchantment"):
            item.enchantment = item_data["enchantment"]

        # アイテム固有状態の適用
        if "charges" in item_data and hasattr(item, "charges"):
            item.charges = max(0, item_data["charges"])

        if "amount" in item_data and hasattr(item, "amount"):
            item.amount = max(1, item_data["amount"])

        if "bonus" in item_data and hasattr(item, "bonus"):
            item.bonus = item_data["bonus"]

        if "effect_name" in item_data and hasattr(item, "effect"):
            # Ringの効果名を文字列として保存している場合
            item.effect = item_data["effect_name"]

    def _serialize_all_floors(self, floors: dict[int, Any]) -> dict[str, Any]:
        """
        すべてのフロアデータをシリアライズ。
        """
        serialized_floors = {}
        for floor_num, floor_data in floors.items():
            if floor_data is not None:
                serialized_floors[floor_num] = self._serialize_floor_data_object(floor_data)
        return serialized_floors

    def _serialize_floor_data_object(self, floor_data) -> dict[str, Any]:
        """
        フロアデータオブジェクトをシリアライズ。
        """
        return {
            "tiles": floor_data.tiles.tolist(),
            "monsters": [self._serialize_monster(monster) for monster in floor_data.monster_spawner.monsters],
            "items": [self._serialize_item(item) for item in floor_data.item_spawner.items],
            "explored": floor_data.explored.tolist(),
            "traps": [
                self._serialize_trap(trap) for trap in getattr(getattr(floor_data, "trap_manager", None), "traps", [])
            ],
        }

    def _serialize_floor_data(self) -> dict[str, Any]:
        """
        フロアデータをシリアライズ（現在のフロアのみ）。
        """
        # 現在のフロアデータを取得
        current_floor_data = self.context.game_logic.dungeon_manager.get_current_floor_data()
        if current_floor_data is None:
            return {
                "tiles": [],
                "monsters": [],
                "items": [],
                "explored": [],
                "traps": [],
            }

        return self._serialize_floor_data_object(current_floor_data)

    def _restore_floor_data(self, floor_data: dict[str, Any]) -> None:
        """
        フロアデータを復元（完全実装）。
        """
        import numpy as np

        from pyrogue.entities.actors.monster_spawner import MonsterSpawner
        from pyrogue.entities.items.item_spawner import ItemSpawner
        from pyrogue.entities.traps.trap import TrapManager
        from pyrogue.map.dungeon_manager import FloorData

        dungeon_manager = self.context.game_logic.dungeon_manager

        # 既存のフロアをクリア（復元成功時のみ）
        floors_backup = dungeon_manager.floors.copy()

        # セーブされたフロアデータを復元
        if not floor_data:
            self.context.add_message("No saved floor data found - floors will be regenerated")
            return

        try:
            # 復元成功時のみ既存フロアをクリア
            dungeon_manager.floors.clear()

            for floor_num_str, saved_floor_data in floor_data.items():
                floor_num = int(floor_num_str)

                # タイルデータを復元
                tiles_list = saved_floor_data.get("tiles", [])
                if tiles_list:
                    tiles = np.array(tiles_list, dtype=object)
                else:
                    continue  # タイルデータがない場合はスキップ

                # 探索済みデータを復元
                explored_list = saved_floor_data.get("explored", [])
                if explored_list:
                    explored = np.array(explored_list, dtype=bool)
                else:
                    explored = np.zeros_like(tiles, dtype=bool)

                # MonsterSpawnerを復元
                monster_spawner = MonsterSpawner(floor_num)
                monsters_data = saved_floor_data.get("monsters", [])
                for monster_data in monsters_data:
                    monster = self._deserialize_monster(monster_data)
                    if monster:
                        monster_spawner.monsters.append(monster)

                # ItemSpawnerを復元
                item_spawner = ItemSpawner(floor_num)
                items_data = saved_floor_data.get("items", [])
                for item_data in items_data:
                    item = self._deserialize_item(item_data)
                    if item:
                        item_spawner.items.append(item)

                # TrapManagerを復元
                trap_manager = TrapManager()
                traps_data = saved_floor_data.get("traps", [])
                for trap_data in traps_data:
                    trap = self._deserialize_trap(trap_data)
                    if trap:
                        trap_manager.traps.append(trap)

                # 階段位置を検索
                up_pos = None
                down_pos = None

                for y in range(tiles.shape[0]):
                    for x in range(tiles.shape[1]):
                        tile = tiles[y, x]
                        tile_name = tile.__class__.__name__ if hasattr(tile, "__class__") else str(tile)
                        if "StairsUp" in tile_name or "UpStairs" in tile_name:
                            up_pos = (x, y)
                        elif "StairsDown" in tile_name or "DownStairs" in tile_name:
                            down_pos = (x, y)

                # 階段が見つからない場合のデフォルト値
                if up_pos is None:
                    up_pos = (1, 1)  # デフォルト位置
                if down_pos is None:
                    down_pos = (tiles.shape[1] - 2, tiles.shape[0] - 2)  # デフォルト位置

                # FloorDataオブジェクトを作成
                restored_floor = FloorData(
                    floor_number=floor_num,
                    tiles=tiles,
                    up_pos=up_pos,
                    down_pos=down_pos,
                    monster_spawner=monster_spawner,
                    item_spawner=item_spawner,
                    trap_manager=trap_manager,
                    explored=explored,
                )

                # DungeonManagerに追加
                dungeon_manager.floors[floor_num] = restored_floor

            self.context.add_message(f"Successfully restored {len(floor_data)} floors from save data")

        except Exception as e:
            self.context.add_message(f"Error restoring floor data: {e}")
            # エラーが発生した場合はバックアップから復元
            dungeon_manager.floors = floors_backup
            self.context.add_message("Floor data restored from backup - some floors may be regenerated")

    def _load_current_floor(self) -> None:
        """
        現在のフロアをロード。
        """
        current_floor = self.context.game_logic.dungeon_manager.current_floor
        floor_data = self.context.game_logic.dungeon_manager.floors.get(current_floor)

        if floor_data:
            # 既存のフロアデータを復元
            self._deserialize_floor_data(floor_data)
        else:
            # フロアデータが存在しない場合は新規生成
            self.context.game_logic.dungeon_manager._generate_floor(current_floor)

    def _deserialize_floor_data(self, floor_data: dict[str, Any]) -> None:
        """
        フロアデータをデシリアライズ。
        """
        # 実装は複雑になるため、基本的な復元のみ
        # 詳細な復元はGameLogic側で実装

    def _serialize_monster(self, monster) -> dict[str, Any]:
        """
        モンスターをシリアライズ。
        """
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
            "color": getattr(monster, "color", (255, 255, 255)),
            "view_range": getattr(monster, "view_range", 3),
        }

    def _serialize_trap(self, trap) -> dict[str, Any]:
        """
        トラップをシリアライズ。
        """
        return {
            "trap_type": trap.trap_type,
            "x": trap.x,
            "y": trap.y,
            "hidden": trap.is_hidden,
        }

    def _deserialize_monster(self, monster_data: dict[str, Any]):
        """
        モンスターデータをデシリアライズ。
        """
        from pyrogue.entities.actors.monster import Monster

        try:
            monster = Monster(
                x=monster_data.get("x", 0),
                y=monster_data.get("y", 0),
                name=monster_data.get("name", "Unknown Monster"),
                char=monster_data.get("char", "?"),
                hp=monster_data.get("hp", 1),
                max_hp=monster_data.get("max_hp", 1),
                attack=monster_data.get("attack", 1),
                defense=monster_data.get("defense", 0),
                level=monster_data.get("level", 1),
                exp_value=monster_data.get("exp_value", 10),
                view_range=monster_data.get("view_range", 3),
                color=monster_data.get("color", (255, 255, 255)),
            )

            # AI パターンの復元
            if "ai_pattern" in monster_data:
                monster.ai_pattern = monster_data["ai_pattern"]

            return monster

        except Exception as e:
            self.context.add_message(f"Error deserializing monster: {e}")
            return None

    def _deserialize_trap(self, trap_data: dict[str, Any]):
        """
        トラップデータをデシリアライズ。
        """
        try:
            trap_type = trap_data.get("trap_type", "PitTrap")
            x = trap_data.get("x", 0)
            y = trap_data.get("y", 0)
            is_hidden = trap_data.get("hidden", True)

            # トラップタイプに応じてインスタンスを作成
            if trap_type == "PitTrap":
                from pyrogue.entities.traps.trap import PitTrap

                trap = PitTrap(x, y)
            elif trap_type == "PoisonNeedleTrap":
                from pyrogue.entities.traps.trap import PoisonNeedleTrap

                trap = PoisonNeedleTrap(x, y)
            elif trap_type == "TeleportTrap":
                from pyrogue.entities.traps.trap import TeleportTrap

                trap = TeleportTrap(x, y)
            else:
                # 不明なトラップタイプの場合はPitTrapをデフォルトに
                from pyrogue.entities.traps.trap import PitTrap

                trap = PitTrap(x, y)

            # 隠し状態を設定
            trap.is_hidden = is_hidden

            return trap

        except Exception as e:
            self.context.add_message(f"Error deserializing trap: {e}")
            return None


class GUICommandContext(CommandContext):
    """GUI用のコマンドコンテキスト実装。"""

    def __init__(self, game_screen):
        self.game_screen = game_screen

    @property
    def game_logic(self):
        """ゲームロジックへのアクセス。"""
        return self.game_screen.game_logic

    @property
    def player(self):
        """プレイヤーへのアクセス。"""
        return self.game_screen.game_logic.player

    def add_message(self, message: str) -> None:
        """メッセージの追加。"""
        self.game_screen.game_logic.add_message(message)

    def display_player_status(self) -> None:
        """プレイヤーステータスの表示。"""
        # GUIでは常時表示されているため何もしない

    def display_inventory(self) -> None:
        """インベントリの表示。"""
        # GUIでは別画面で処理されるため何もしない

    def display_game_state(self) -> None:
        """ゲーム状態の表示。"""
        # GUIでは常時表示されているため何もしない
