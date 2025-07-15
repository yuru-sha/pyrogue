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

  Information:
    status/stat - Show player status
    inventory/inv/i - Show inventory
    look/l - Look around

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
        
        Returns:
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
                self.context.game_logic.message_log = message_log
            
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
        """
        inventory = self.context.game_logic.inventory
        
        # アイテムリストの復元
        items_data = inventory_data.get("items", [])
        inventory.items = [self._deserialize_item(item_data) for item_data in items_data]
        
        # 装備品の復元
        equipped_data = inventory_data.get("equipped", {})
        inventory.equipped = {
            "weapon": self._deserialize_item(equipped_data["weapon"]) if equipped_data.get("weapon") else None,
            "armor": self._deserialize_item(equipped_data["armor"]) if equipped_data.get("armor") else None,
            "ring_left": self._deserialize_item(equipped_data["ring_left"]) if equipped_data.get("ring_left") else None,
            "ring_right": self._deserialize_item(equipped_data["ring_right"]) if equipped_data.get("ring_right") else None,
        }

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
        
        return {
            "items": [self._serialize_item(item) for item in inventory.items],
            "equipped": {
                "weapon": self._serialize_item(inventory.equipped["weapon"]) if inventory.equipped.get("weapon") else None,
                "armor": self._serialize_item(inventory.equipped["armor"]) if inventory.equipped.get("armor") else None,
                "ring_left": self._serialize_item(inventory.equipped["ring_left"]) if inventory.equipped.get("ring_left") else None,
                "ring_right": self._serialize_item(inventory.equipped["ring_right"]) if inventory.equipped.get("ring_right") else None,
            },
        }

    def _serialize_item(self, item) -> dict[str, Any]:
        """
        アイテムをシリアライズ。
        """
        return {
            "item_type": item.item_type,
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

    def _deserialize_item(self, item_data: dict[str, Any]):
        """
        アイテムデータをデシリアライズ。
        """
        from pyrogue.entities.items.item import Item
        
        # 基本的なアイテム復元（必須フィールドを含む）
        item = Item(
            x=item_data.get("x", 0),
            y=item_data.get("y", 0),
            name=item_data.get("name", "Unknown Item"),
            char=item_data.get("char", "?"),
            color=item_data.get("color", (255, 255, 255)),
            item_type=item_data.get("item_type", "MISC"),
            cursed=item_data.get("cursed", False)
        )
        
        # 後から追加された属性のチェック
        if "quantity" in item_data:
            item.quantity = item_data["quantity"]
        if "enchantment" in item_data:
            item.enchantment = item_data["enchantment"]
        if "stack_count" in item_data:
            item.stack_count = item_data["stack_count"]
        
        return item

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
            "traps": [self._serialize_trap(trap) for trap in getattr(getattr(floor_data, "trap_manager", None), "traps", [])],
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
        フロアデータを復元。
        """
        # フロアデータの完全復元は複雑なため、現在は簡略化
        # 将来的にはフロアデータの完全復元を実装予定
        dungeon_manager = self.context.game_logic.dungeon_manager
        
        # 既存のフロアをクリア（現在は再生成に依存）
        dungeon_manager.floors.clear()
        
        # セーブされたフロアデータを記録（デバッグ用）
        if floor_data:
            self.context.add_message(f"Loaded floor data for {len(floor_data)} floors")
        else:
            self.context.add_message("No saved floor data found - floors will be regenerated")

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
        pass

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
