"""
デバッグコマンドハンドラーモジュール。

開発・デバッグ用のコマンド処理を専門に担当します。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrogue.core.command_handler import CommandResult

if TYPE_CHECKING:
    from pyrogue.core.command_handler import CommandContext


class DebugCommandHandler:
    """デバッグコマンド専用のハンドラー。"""

    def __init__(self, context: CommandContext):
        self.context = context

    def handle_debug_command(self, args: list[str]) -> CommandResult:
        """
        デバッグコマンドの処理。

        Args:
        ----
            args: コマンド引数

        Returns:
        -------
            CommandResult: コマンド実行結果

        """
        if not args:
            self.context.add_message(
                "Debug commands: yendor, floor <number>, pos <x> <y>, hp <value>, damage <value>, gold <amount>"
            )
            return CommandResult(True)

        debug_cmd = args[0].lower()

        if debug_cmd == "yendor":
            return self._handle_yendor_debug()
        if debug_cmd == "floor" and len(args) > 1:
            return self._handle_floor_debug(args[1])
        if debug_cmd == "pos" and len(args) > 2:
            return self._handle_position_debug(args[1], args[2])
        if debug_cmd == "hp" and len(args) > 1:
            return self._handle_hp_debug(args[1])
        if debug_cmd == "damage" and len(args) > 1:
            return self._handle_damage_debug(args[1])
        if debug_cmd == "gold" and len(args) > 1:
            return self._handle_gold_debug(args[1])
        self.context.add_message("Unknown debug command")
        return CommandResult(False)

    def _handle_yendor_debug(self) -> CommandResult:
        """イェンダーのアミュレット付与デバッグ。"""
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
            b1f_data = game_logic.dungeon_manager.get_floor(1, player)
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

    def _handle_floor_debug(self, floor_str: str) -> CommandResult:
        """フロア移動デバッグ。"""
        try:
            floor_num = int(floor_str)
            game_logic = self.context.game_logic
            player = self.context.player
            game_logic.dungeon_manager.set_current_floor(floor_num, player)

            # プレイヤーの位置を新しい階層に設定
            floor_data = game_logic.dungeon_manager.get_current_floor_data(player)
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

    def _handle_position_debug(self, x_str: str, y_str: str) -> CommandResult:
        """位置移動デバッグ。"""
        try:
            x = int(x_str)
            y = int(y_str)
            player = self.context.player
            player.x = x
            player.y = y
            self.context.add_message(f"Player teleported to ({x}, {y})")
            return CommandResult(True)
        except Exception as e:
            self.context.add_message(f"Position teleport failed: {e}")
            return CommandResult(False)

    def _handle_hp_debug(self, hp_str: str) -> CommandResult:
        """HP設定デバッグ。"""
        try:
            hp_value = int(hp_str)
            player = self.context.player
            player.hp = max(0, hp_value)
            self.context.add_message(f"Player HP set to {player.hp}")

            # 死亡チェック
            if player.hp <= 0:
                self._handle_debug_death("Debug death")

            return CommandResult(True)
        except Exception as e:
            self.context.add_message(f"HP set failed: {e}")
            return CommandResult(False)

    def _handle_damage_debug(self, damage_str: str) -> CommandResult:
        """ダメージ適用デバッグ。"""
        try:
            damage_value = int(damage_str)
            player = self.context.player
            player.hp = max(0, player.hp - damage_value)
            self.context.add_message(f"Player takes {damage_value} damage! HP: {player.hp}")

            # 死亡チェック
            if player.hp <= 0:
                self._handle_debug_death("Debug damage")

            return CommandResult(True)
        except Exception as e:
            self.context.add_message(f"Damage failed: {e}")
            return CommandResult(False)

    def _handle_gold_debug(self, gold_str: str) -> CommandResult:
        """ゴールド配置デバッグ。"""
        try:
            gold_amount = int(gold_str)
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

    def _handle_debug_death(self, death_reason: str) -> None:
        """デバッグによる死亡処理。"""
        self.context.add_message("You have died!")
        self.context.add_message("GAME OVER")

        # 死亡処理
        if hasattr(self.context, "game_logic") and self.context.game_logic:
            self.context.game_logic.record_game_over(death_reason)
