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

        # デバッグコマンド
        if command == "debug":
            return self._handle_debug_command(args)

        # システムコマンド
        if command in ["quit", "exit", "q"]:
            return CommandResult(True, "Goodbye!", should_quit=True)
        if command == "help":
            return self._handle_help()

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

  Information:
    status/stat - Show player status
    inventory/inv/i - Show inventory
    look/l - Look around

  System:
    help - Show this help
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
