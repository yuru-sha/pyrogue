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

    def __init__(self, context: CommandContext) -> None:
        self.context = context
        self._save_load_handler = None
        self._debug_handler = None
        self._auto_explore_handler = None
        self._info_handler = None

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

        if command in ["quaff", "q"]:
            return self._handle_quaff(args)
        if command in ["auto_explore", "O"]:
            return self._get_auto_explore_handler().handle_auto_explore()

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
            return self._get_info_handler().handle_symbol_explanation()
        if command in ["identification_status", "\\"]:
            return self._get_info_handler().handle_identification_status()
        if command in ["character_details", "@"]:
            return self._get_info_handler().handle_character_details()
        if command in ["last_message", "ctrl_m"]:
            return self._get_info_handler().handle_last_message()

        # デバッグコマンド
        if command == "debug":
            return self._get_debug_handler().handle_debug_command(args)

        # システムコマンド
        if command in ["quit", "exit"]:
            return CommandResult(True, "Goodbye!", should_quit=True)
        if command == "help":
            return self._handle_help()
        if command in ["save", "s"]:
            return self._get_save_load_handler().handle_save(args)
        if command == "load":
            return self._get_save_load_handler().handle_load(args)

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

    def _handle_attack(self, _args: list[str]) -> CommandResult:
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
    get/, - Pick up item
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
    quaff/q <potion> - Drink potion
    auto_explore/O - Auto-explore unexplored areas

  Information:
    status/stat - Show player status
    inventory/inv/i - Show inventory
    look/l - Look around
    symbol_explanation/ - Show symbol meanings
    identification_status/\\ - Show item identification status
    character_details/@ - Show detailed character info
    last_message/ctrl_m - Show recent messages

  Special Monsters:
    Dream Eater (@) - Causes hallucinations, psychic attacks
    Phantom Fungus (f) - Spore attacks, causes confusion

  System:
    help - Show this help
    save/s - Save game
    load - Load game
    quit/exit - Quit game

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
        return CommandResult(False, f"The {wand_to_use.name} fizzles.")

    def _handle_quaff(self, args: list[str]) -> CommandResult:
        """ポーションを飲む（quaff）コマンドの処理。"""
        inventory = self.context.game_logic.inventory

        # 引数が指定されている場合、その名前のポーションを検索
        if args:
            potion_name = " ".join(args)
            potion_to_use = None
            for item in inventory.items:
                if (
                    item.name.lower() == potion_name.lower()
                    and hasattr(item, "item_type")
                    and item.item_type == "POTION"
                ):
                    potion_to_use = item
                    break

            if not potion_to_use:
                return CommandResult(False, f"You don't have a potion called {potion_name}")
        else:
            # 引数が指定されていない場合、最初のポーションを使用
            potion_items = [
                item for item in inventory.items if hasattr(item, "item_type") and item.item_type == "POTION"
            ]

            if not potion_items:
                return CommandResult(False, "You have no potions to quaff.")

            potion_to_use = potion_items[0]

        # ポーションを使用
        player = self.context.player
        message = potion_to_use.use()
        self.context.add_message(message)

        # ポーションの効果を適用
        success = potion_to_use.apply_effect(self.context)

        # インベントリからポーションを削除
        inventory.remove_item(potion_to_use)

        return CommandResult(True, should_end_turn=True)

    def _get_direction_name(self, dx: int, dy: int) -> str:
        """方向名を取得。"""
        if dx == 0 and dy == -1:
            return "North"
        if dx == 0 and dy == 1:
            return "South"
        if dx == 1 and dy == 0:
            return "East"
        if dx == -1 and dy == 0:
            return "West"
        if dx == -1 and dy == -1:
            return "Northwest"
        if dx == 1 and dy == -1:
            return "Northeast"
        if dx == -1 and dy == 1:
            return "Southwest"
        if dx == 1 and dy == 1:
            return "Southeast"
        return "Unknown"

    def _get_save_load_handler(self):
        """セーブ/ロードハンドラーを取得（遅延初期化）。"""
        if self._save_load_handler is None:
            from pyrogue.core.save_load_handler import SaveLoadHandler

            self._save_load_handler = SaveLoadHandler(self.context)
        return self._save_load_handler

    def _get_debug_handler(self):
        """デバッグハンドラーを取得（遅延初期化）。"""
        if self._debug_handler is None:
            from pyrogue.core.debug_command_handler import DebugCommandHandler

            self._debug_handler = DebugCommandHandler(self.context)
        return self._debug_handler

    def _get_auto_explore_handler(self):
        """自動探索ハンドラーを取得（遅延初期化）。"""
        if self._auto_explore_handler is None:
            from pyrogue.core.auto_explore_handler import AutoExploreHandler

            self._auto_explore_handler = AutoExploreHandler(self.context)
        return self._auto_explore_handler

    def _get_info_handler(self):
        """情報表示ハンドラーを取得（遅延初期化）。"""
        if self._info_handler is None:
            from pyrogue.core.info_command_handler import InfoCommandHandler

            self._info_handler = InfoCommandHandler(self.context)
        return self._info_handler


class GUICommandContext(CommandContext):
    """GUI用のコマンドコンテキスト実装。"""

    def __init__(self, game_screen) -> None:
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
