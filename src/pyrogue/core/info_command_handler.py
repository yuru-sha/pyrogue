"""
情報表示コマンドハンドラーモジュール。

各種情報表示コマンドの処理を専門に担当します。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrogue.core.command_handler import CommandResult

if TYPE_CHECKING:
    from pyrogue.core.command_handler import CommandContext


class InfoCommandHandler:
    """情報表示コマンド専用のハンドラー。"""

    def __init__(self, context: CommandContext) -> None:
        self.context = context

    def handle_symbol_explanation(self) -> CommandResult:
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

    def handle_identification_status(self) -> CommandResult:
        """アイテム識別状況の処理。"""
        player = self.context.player
        identification = player.identification

        # 識別済みアイテム数を計算
        identified_count = 0
        identified_count += len(identification.identified_potions)
        identified_count += len(identification.identified_scrolls)
        identified_count += len(identification.identified_rings)
        if hasattr(identification, "identified_wands"):
            identified_count += len(identification.identified_wands)

        self.context.add_message("Identification Status:")
        self.context.add_message(f"Identified items: {identified_count}")
        self.context.add_message(f"  Potions: {len(identification.identified_potions)}")
        self.context.add_message(f"  Scrolls: {len(identification.identified_scrolls)}")
        self.context.add_message(f"  Rings: {len(identification.identified_rings)}")
        if hasattr(identification, "identified_wands"):
            self.context.add_message(f"  Wands: {len(identification.identified_wands)}")

        return CommandResult(True)

    def handle_character_details(self) -> CommandResult:
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

    def handle_last_message(self) -> CommandResult:
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
