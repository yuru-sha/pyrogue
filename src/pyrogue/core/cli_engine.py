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

from pyrogue.core.game_states import GameStates
from pyrogue.ui.screens.game_screen import GameScreen
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
        self.game_screen = GameScreen(None)  # CLIモードではコンソールは不要

        game_logger.debug("CLI engine initialized")

    def run(self) -> None:
        """
        CLIメインループを実行。

        標準入力からコマンドを読み取り、処理し、結果を表示します。
        """
        self.running = True
        print("PyRogue CLI Mode - Type 'help' for commands")

        # 新しいゲームを開始
        self.game_screen.setup_new_game()
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
            "w": (-1, 0)
        }

        if direction not in direction_map:
            print(f"Invalid direction: {direction}")
            return False

        dx, dy = direction_map[direction]

        try:
            # GameScreenの移動処理を呼び出し
            success = self.game_screen.try_move_player(dx, dy)
            if success:
                print(f"Moved {direction}")
                self.display_game_state()
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
            success = self.game_screen.try_attack_adjacent_enemy()
            if success:
                print("Attacked enemy!")
                self.display_game_state()
            else:
                print("No enemy to attack")
            return success
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
            success = self.game_screen.try_use_item(item_name)
            if success:
                print(f"Used {item_name}")
                self.display_game_state()
            else:
                print(f"Cannot use {item_name}")
            return success
        except Exception as e:
            print(f"Error using item: {e}")
            return False

    def display_game_state(self) -> None:
        """現在のゲーム状態を表示。"""
        try:
            if not self.game_screen.player:
                print("Game not initialized")
                return

            player = self.game_screen.player
            dungeon = self.game_screen.dungeon

            print("\n" + "="*50)
            print(f"Floor: {dungeon.current_floor}")
            print(f"Player: ({player.x}, {player.y})")
            print(f"HP: {player.hp}/{player.max_hp}")
            print(f"Level: {player.level}")
            print(f"Gold: {player.gold}")

            # 周囲の情報を表示
            self.display_surroundings()

        except Exception as e:
            print(f"Error displaying game state: {e}")

    def display_surroundings(self) -> None:
        """プレイヤーの周囲の情報を表示。"""
        try:
            if not self.game_screen.player or not self.game_screen.dungeon:
                return

            player = self.game_screen.player
            dungeon = self.game_screen.dungeon

            print("\nSurroundings:")

            # 周囲のタイルを確認
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue

                    x, y = player.x + dx, player.y + dy
                    if 0 <= x < len(dungeon.tiles) and 0 <= y < len(dungeon.tiles[0]):
                        tile = dungeon.tiles[x][y]
                        direction = self.get_direction_name(dx, dy)
                        tile_name = getattr(tile, 'name', tile.__class__.__name__)
                        print(f"  {direction}: {tile_name}")

            # 周囲の敵を表示
            try:
                nearby_enemies = self.game_screen.get_nearby_enemies()
                if nearby_enemies:
                    print("\nNearby enemies:")
                    for enemy in nearby_enemies:
                        print(f"  {enemy.name} (HP: {enemy.hp}/{enemy.max_hp})")
            except Exception as e:
                print(f"Error getting nearby enemies: {e}")

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
            if not self.game_screen.player:
                print("Game not initialized")
                return

            player = self.game_screen.player

            print("\n" + "="*30)
            print("PLAYER STATUS")
            print("="*30)
            print(f"Level: {player.level}")
            print(f"HP: {player.hp}/{player.max_hp}")
            print(f"Attack: {player.attack}")
            print(f"Defense: {player.defense}")
            print(f"Gold: {player.gold}")
            print(f"Position: ({player.x}, {player.y})")

        except Exception as e:
            print(f"Error displaying player status: {e}")

    def display_inventory(self) -> None:
        """インベントリを表示。"""
        try:
            if not self.game_screen.player:
                print("Game not initialized")
                return

            player = self.game_screen.player
            inventory = player.inventory

            print("\n" + "="*30)
            print("INVENTORY")
            print("="*30)

            if not inventory.items:
                print("Inventory is empty")
            else:
                for i, item in enumerate(inventory.items):
                    print(f"{i+1}. {item.name}")

        except Exception as e:
            print(f"Error displaying inventory: {e}")

    def update_game_state(self) -> None:
        """ゲーム状態を更新。"""
        try:
            # 敵のターンを処理
            if self.state == GameStates.PLAYERS_TURN:
                self.game_screen.process_enemy_turns()

            # ゲームオーバー・勝利条件をチェック
            if self.game_screen.check_game_over():
                print("\nGAME OVER!")
                self.running = False
            elif self.game_screen.check_victory():
                print("\nVICTORY!")
                self.running = False

        except Exception as e:
            print(f"Error updating game state: {e}")

    def show_help(self) -> None:
        """利用可能なコマンドを表示。"""
        print("\nAvailable Commands:")
        print("  move <direction>  - Move player (north/south/east/west)")
        print("  attack [target]   - Attack adjacent enemy")
        print("  use <item>        - Use an item")
        print("  inventory         - Show inventory")
        print("  status            - Show player status")
        print("  look              - Show current surroundings")
        print("  help              - Show this help message")
        print("  quit/exit         - Exit the game")
        print()
