"""
CLI ゲームエンジンモジュール。

このモジュールはコマンドラインインターフェースでゲームを実行するための
エンジンを提供します。主にテストと自動化のために使用されます。

主要機能:
    - コマンドライン入力の解析
    - ゲーム状態の表示
    - 非対話型のゲーム実行
    - 自動テスト用のインターフェース

Example:
    $ python -m pyrogue.main --cli
    > move north
    > attack goblin
    > quit

"""

from __future__ import annotations

import sys
from typing import Optional

from pyrogue.core.game_logic import GameLogic
from pyrogue.core.game_states import GameStates
from pyrogue.utils import game_logger


class CLIEngine:
    """
    コマンドラインインターフェース用のゲームエンジン。

    テキストベースのコマンドでゲームを操作できる簡素化されたエンジン。
    主に自動テスト、デバッグ、および非対話型の実行に使用されます。

    サポートされるコマンド:
        - move <direction>: 移動（north, south, east, west）
        - attack [target]: 攻撃
        - use <item>: アイテム使用
        - inventory: インベントリ表示
        - status: プレイヤー状態表示
        - look: 現在の状況表示
        - help: コマンド一覧表示
        - quit: ゲーム終了

    Attributes:
        state: 現在のゲーム状態
        running: ゲームループ実行フラグ
        game_screen: ゲーム画面インスタンス

    """

    def __init__(self) -> None:
        """CLIエンジンを初期化。"""
        self.state = GameStates.PLAYERS_TURN
        self.running = False
        self.game_logic = GameLogic(None)  # CLIモードではエンジンはNone

        game_logger.debug("CLI engine initialized")

    def run(self) -> None:
        """
        CLIメインループを実行。

        標準入力からコマンドを読み取り、処理し、結果を表示します。
        """
        self.running = True
        print("PyRogue CLI Mode - Type 'help' for commands")

        # 新しいゲームを開始
        self.game_logic.setup_new_game()
        self.display_game_state()

        try:
            while self.running:
                try:
                    command = input("> ").strip()
                    if not command:
                        continue

                    result = self.process_command(command)
                    if result is False:
                        self.running = False
                        break

                    # ゲーム状態を更新
                    self.update_game_state()

                except KeyboardInterrupt:
                    print("\nGame interrupted by user")
                    self.running = False
                    break
                except EOFError:
                    print("\nEnd of input reached")
                    self.running = False
                    break

        except Exception as e:
            game_logger.error(f"Fatal error in CLI loop: {e}")
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def process_command(self, command: str) -> Optional[bool]:
        """
        コマンドを処理し、適切なアクションを実行。

        Args:
            command: ユーザーが入力したコマンド文字列

        Returns:
            False if game should quit, True if game should continue, None for invalid commands
        """
        parts = command.lower().split()
        if not parts:
            return None

        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        if cmd == "help":
            self.show_help()
        elif cmd == "quit" or cmd == "exit":
            print("Goodbye!")
            return False
        elif cmd == "status":
            self.display_player_status()
        elif cmd == "look":
            self.display_game_state()
        elif cmd == "inventory":
            self.display_inventory()
        elif cmd == "move":
            if not args:
                print("Usage: move <direction> (north/south/east/west)")
                return None
            return self.handle_move(args[0])
        elif cmd == "attack":
            return self.handle_attack(args[0] if args else None)
        elif cmd == "use":
            if not args:
                print("Usage: use <item>")
                return None
            return self.handle_use_item(args[0])
        elif cmd == "get":
            return self.handle_get_item()
        elif cmd == "stairs":
            if not args:
                print("Usage: stairs <up/down>")
                return None
            return self.handle_stairs(args[0])
        else:
            print(f"Unknown command: {cmd}. Type 'help' for available commands.")
            return None

        return True

    def handle_move(self, direction: str) -> bool:
        """
        移動コマンドを処理。

        Args:
            direction: 移動方向（north, south, east, west）

        Returns:
            コマンドが成功したかどうか
        """
        direction_map = {
            "north": (0, -1),
            "south": (0, 1),
            "east": (1, 0),
            "west": (-1, 0),
            "n": (0, -1),
            "s": (0, 1),
            "e": (1, 0),
            "w": (-1, 0),
        }

        if direction not in direction_map:
            print(f"Invalid direction: {direction}")
            return False

        dx, dy = direction_map[direction]

        try:
            # GameLogicの移動処理を呼び出し
            success = self.game_logic.handle_player_move(dx, dy)
            if success:
                print(f"Moved {direction}")
                self.display_game_state()
                # メッセージを表示
                self.display_recent_messages()
            else:
                print("Cannot move in that direction")
            return success
        except Exception as e:
            print(f"Error moving: {e}")
            return False

    def handle_attack(self, target: Optional[str]) -> bool:
        """
        攻撃コマンドを処理。

        Args:
            target: 攻撃対象（省略可能）

        Returns:
            コマンドが成功したかどうか
        """
        try:
            # 隣接する敵を攻撃
            player = self.game_logic.player
            current_floor = self.game_logic.get_current_floor_data()

            # 隣接する8方向をチェック
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue

                    x = player.x + dx
                    y = player.y + dy

                    monster = current_floor.monster_spawner.get_monster_at(x, y)
                    if monster:
                        self.game_logic.handle_combat(monster)
                        print(f"Attacked {monster.name}!")
                        self.display_game_state()
                        return True

            print("No enemy to attack")
            return False
        except Exception as e:
            print(f"Error attacking: {e}")
            return False

    def handle_use_item(self, item_name: str) -> bool:
        """
        アイテム使用コマンドを処理。

        Args:
            item_name: 使用するアイテム名

        Returns:
            コマンドが成功したかどうか
        """
        try:
            # アイテム使用処理
            inventory = self.game_logic.inventory

            # インベントリから該当するアイテムを検索
            for item in inventory.items:
                if item.name.lower() == item_name.lower():
                    # 新しいeffectシステムを使用
                    context = type('EffectContext', (), {
                        'player': self.game_logic.player,
                        'dungeon': self.game_logic.get_current_floor_data(),
                        'game_screen': self
                    })()

                    success = self.game_logic.player.use_item(item, context=context)
                    if success:
                        print(f"Used {item.name}")
                        self.display_game_state()
                        return True
                    else:
                        print(f"Cannot use {item.name}")
                        return False

            print(f"You don't have {item_name}")
            return False
        except Exception as e:
            print(f"Error using item: {e}")
            return False

    def handle_get_item(self) -> bool:
        """
        アイテム取得コマンドを処理。

        Returns:
            コマンドが成功したかどうか
        """
        try:
            message = self.game_logic.handle_get_item()
            if message:
                print(message)
                self.display_game_state()
            else:
                print("There is nothing here to pick up.")
            return message is not None
        except Exception as e:
            print(f"Error getting item: {e}")
            return False

    def handle_stairs(self, direction: str) -> bool:
        """
        階段使用コマンドを処理。

        Args:
            direction: 階段の方向（up/down）

        Returns:
            コマンドが成功したかどうか
        """
        try:
            if direction.lower() in ["up", "u"]:
                success = self.game_logic.ascend_stairs()
            elif direction.lower() in ["down", "d"]:
                success = self.game_logic.descend_stairs()
            else:
                print("Invalid direction. Use 'up' or 'down'")
                return False

            if success:
                print(f"Used stairs {direction}")
                self.display_game_state()
                self.display_recent_messages()
            else:
                print(f"Cannot use stairs {direction}")
            return success
        except Exception as e:
            print(f"Error using stairs: {e}")
            return False

    def display_recent_messages(self) -> None:
        """最近のメッセージを表示。"""
        try:
            if self.game_logic.message_log:
                recent_messages = self.game_logic.message_log[-3:]  # 最新の3つ
                if recent_messages:
                    print("\nMessages:")
                    for msg in recent_messages:
                        print(f"  {msg}")
        except Exception as e:
            print(f"Error displaying messages: {e}")

    def display_game_state(self) -> None:
        """現在のゲーム状態を表示。"""
        try:
            if not self.game_logic.player:
                print("Game not initialized")
                return

            player = self.game_logic.player
            floor_data = self.game_logic.get_current_floor_data()

            print("\n" + "=" * 50)
            print(f"Floor: B{self.game_logic.dungeon_manager.current_floor}F")
            print(f"Player: ({player.x}, {player.y})")
            print(f"HP: {player.hp}/{player.max_hp}")
            print(f"Level: {player.level}")
            print(f"Gold: {player.gold}")
            print(f"Hunger: {player.hunger}%")

            # 周囲の情報を表示
            self.display_surroundings()

        except Exception as e:
            print(f"Error displaying game state: {e}")

    def display_surroundings(self) -> None:
        """プレイヤーの周囲の情報を表示。"""
        try:
            if not self.game_logic.player:
                return

            player = self.game_logic.player
            floor_data = self.game_logic.get_current_floor_data()

            print("\nSurroundings:")

            # 周囲のタイルを確認
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue

                    x, y = player.x + dx, player.y + dy
                    if (
                        0 <= y < floor_data.tiles.shape[0]
                        and 0 <= x < floor_data.tiles.shape[1]
                    ):
                        tile = floor_data.tiles[y, x]
                        direction = self.get_direction_name(dx, dy)
                        tile_name = getattr(tile, "name", tile.__class__.__name__)
                        print(f"  {direction}: {tile_name}")

            # 周囲の敵を表示
            nearby_enemies = []
            for monster in floor_data.monster_spawner.monsters:
                distance = abs(monster.x - player.x) + abs(monster.y - player.y)
                if distance <= 2:  # 隣接しているか近く
                    nearby_enemies.append(monster)

            if nearby_enemies:
                print("\nNearby enemies:")
                for enemy in nearby_enemies:
                    print(
                        f"  {enemy.name} at ({enemy.x}, {enemy.y}) - HP: {enemy.hp}/{enemy.max_hp}"
                    )

            # 周囲のアイテムを表示
            nearby_items = []
            for item in floor_data.item_spawner.items:
                distance = abs(item.x - player.x) + abs(item.y - player.y)
                if distance <= 1:  # 隣接または同じ位置
                    nearby_items.append(item)

            if nearby_items:
                print("\nNearby items:")
                for item in nearby_items:
                    if item.x == player.x and item.y == player.y:
                        print(f"  {item.name} (here - type 'get' to pick up)")
                    else:
                        print(f"  {item.name} at ({item.x}, {item.y})")

        except Exception as e:
            print(f"Error displaying surroundings: {e}")

    def get_direction_name(self, dx: int, dy: int) -> str:
        """座標の差から方向名を取得。"""
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

    def display_player_status(self) -> None:
        """プレイヤーの詳細ステータスを表示。"""
        try:
            if not self.game_logic.player:
                print("Game not initialized")
                return

            player = self.game_logic.player

            print("\n" + "=" * 30)
            print("PLAYER STATUS")
            print("=" * 30)
            print(f"Level: {player.level}")
            print(f"HP: {player.hp}/{player.max_hp}")
            print(f"Attack: {player.get_attack()}")
            print(f"Defense: {player.get_defense()}")
            print(f"Gold: {player.gold}")
            print(f"Hunger: {player.hunger}%")
            print(f"Position: ({player.x}, {player.y})")
            print(f"EXP: {player.exp}")

        except Exception as e:
            print(f"Error displaying player status: {e}")

    def display_inventory(self) -> None:
        """インベントリを表示。"""
        try:
            if not self.game_logic.player:
                print("Game not initialized")
                return

            inventory = self.game_logic.inventory

            print("\n" + "=" * 30)
            print("INVENTORY")
            print("=" * 30)

            if not inventory.items:
                print("Inventory is empty")
            else:
                for i, item in enumerate(inventory.items):
                    equipped_str = ""
                    if hasattr(item, "item_type"):
                        if inventory.is_equipped(item):
                            equipped_str = " (equipped)"
                    print(f"{i + 1}. {item.name}{equipped_str}")

            # 装備情報を表示
            equipped = inventory.equipped
            print("\nEquipment:")
            print(
                f"  Weapon: {equipped['weapon'].name if equipped['weapon'] else 'None'}"
            )
            print(f"  Armor: {equipped['armor'].name if equipped['armor'] else 'None'}")
            print(
                f"  Ring(L): {equipped['ring_left'].name if equipped['ring_left'] else 'None'}"
            )
            print(
                f"  Ring(R): {equipped['ring_right'].name if equipped['ring_right'] else 'None'}"
            )

        except Exception as e:
            print(f"Error displaying inventory: {e}")

    def update_game_state(self) -> None:
        """ゲーム状態を更新。"""
        try:
            # ゲームオーバー・勝利条件をチェック
            if self.game_logic.check_player_death():
                print("\nGAME OVER!")
                print(
                    f"You died on floor B{self.game_logic.dungeon_manager.current_floor}F."
                )
                self.running = False
            elif self.game_logic.check_victory():
                print("\nVICTORY!")
                print("You escaped with the Amulet of Yendor!")
                self.running = False

        except Exception as e:
            print(f"Error updating game state: {e}")

    def show_help(self) -> None:
        """利用可能なコマンドを表示。"""
        print("\nAvailable Commands:")
        print("  move <direction>  - Move player (north/south/east/west/n/s/e/w)")
        print("  get               - Pick up item at current position")
        print("  stairs <up/down>  - Use stairs (up/down)")
        print("  inventory         - Show inventory")
        print("  status            - Show player status")
        print("  look              - Show current surroundings")
        print("  help              - Show this help message")
        print("  quit/exit         - Exit the game")
        print()
