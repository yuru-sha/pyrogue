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
            command: 実行するコマンド
            args: コマンドの引数リスト

        Returns:
            CommandResult: コマンド実行結果
        """
        if args is None:
            args = []

        game_logger.debug(f"Handling command: {command} with args: {args}")

        # 移動コマンド
        if command in ["move", "north", "south", "east", "west", "n", "s", "e", "w"]:
            return self._handle_move_command(command, args)

        # アクションコマンド
        elif command in ["get", "pickup", "g"]:
            return self._handle_get_item()
        elif command in ["use", "u"]:
            return self._handle_use_item(args)
        elif command in ["attack", "a"]:
            return self._handle_attack(args)
        elif command in ["stairs", "stair"]:
            return self._handle_stairs(args)
        elif command in ["open", "o"]:
            return self._handle_open_door()
        elif command in ["close", "c"]:
            return self._handle_close_door()
        elif command in ["search", "s"]:
            return self._handle_search()
        elif command in ["disarm", "d"]:
            return self._handle_disarm_trap()

        # 情報表示コマンド
        elif command in ["status", "stat"]:
            self.context.display_player_status()
            return CommandResult(True)
        elif command in ["inventory", "inv", "i"]:
            self.context.display_inventory()
            return CommandResult(True)
        elif command in ["look", "l"]:
            self.context.display_game_state()
            return CommandResult(True)

        # システムコマンド
        elif command in ["quit", "exit", "q"]:
            return CommandResult(True, "Goodbye!", should_quit=True)
        elif command == "help":
            return self._handle_help()

        else:
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
        else:
            return CommandResult(False, "Cannot move in that direction")

    def _handle_get_item(self) -> CommandResult:
        """アイテム取得の処理。"""
        success = self.context.game_logic.handle_get_item()
        if success:
            return CommandResult(True, should_end_turn=True)
        else:
            return CommandResult(False, "No item to pick up here")

    def _handle_use_item(self, args: list[str]) -> CommandResult:
        """アイテム使用の処理。"""
        if not args:
            return CommandResult(False, "Usage: use <item_name>")

        item_name = " ".join(args)
        success = self.context.game_logic.handle_use_item(item_name)
        if success:
            return CommandResult(True, should_end_turn=True)
        else:
            return CommandResult(False, f"Cannot use {item_name}")

    def _handle_attack(self, args: list[str]) -> CommandResult:
        """攻撃の処理。"""
        # 隣接する敵への攻撃
        success = self.context.game_logic.handle_combat()
        if success:
            return CommandResult(True, should_end_turn=True)
        else:
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
        else:
            return CommandResult(False, "No stairs here or cannot use stairs")

    def _handle_open_door(self) -> CommandResult:
        """扉を開く処理。"""
        success = self.context.game_logic.handle_open_door()
        if success:
            return CommandResult(True, should_end_turn=True)
        else:
            return CommandResult(False, "No door to open nearby")

    def _handle_close_door(self) -> CommandResult:
        """扉を閉じる処理。"""
        success = self.context.game_logic.handle_close_door()
        if success:
            return CommandResult(True, should_end_turn=True)
        else:
            return CommandResult(False, "No door to close nearby")

    def _handle_search(self) -> CommandResult:
        """隠し扉の探索処理。"""
        success = self.context.game_logic.handle_search()
        if success:
            return CommandResult(True, should_end_turn=True)
        else:
            return CommandResult(False, "Nothing found")

    def _handle_disarm_trap(self) -> CommandResult:
        """トラップ解除の処理。"""
        success = self.context.game_logic.handle_disarm_trap()
        if success:
            return CommandResult(True, should_end_turn=True)
        else:
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
        """
        self.context.add_message(help_text.strip())
        return CommandResult(True)


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
        pass

    def display_inventory(self) -> None:
        """インベントリの表示。"""
        # GUIでは別画面で処理されるため何もしない
        pass

    def display_game_state(self) -> None:
        """ゲーム状態の表示。"""
        # GUIでは常時表示されているため何もしない
        pass
