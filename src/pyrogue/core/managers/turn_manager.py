"""
ターン管理コンポーネント。

このモジュールは、GameLogicから分離されたターン管理システムを担当します。
プレイヤーターン、モンスターターン、ステータス異常、満腹度システムを管理します。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrogue.constants import HungerConstants, MagicConstants
from pyrogue.utils import game_logger

if TYPE_CHECKING:
    from pyrogue.core.managers.game_context import GameContext


class TurnManager:
    """
    ターン管理システムの管理クラス。

    ゲームのターン進行、モンスターターン処理、
    ステータス異常の経過、満腹度システムを担当します。

    Attributes
    ----------
        turn_count: 経過ターン数

    """

    def __init__(self) -> None:
        """ターンマネージャーを初期化。"""
        self.turn_count = 0

    def process_turn(self, context: GameContext) -> None:
        """
        1ターンの処理を実行。

        Args:
        ----
            context: ゲームコンテキスト

        """
        self.turn_count += 1

        # プレイヤーのターン数を増加
        context.player.increment_turn()

        # プレイヤーのステータス異常処理
        self._process_player_status_effects(context)

        # モンスターターンの処理
        self._process_monster_turns(context)

        # 満腹度システムの処理
        self._process_hunger_system(context)

        # MP自然回復の処理
        self._process_mp_recovery(context)

        # ターン終了後の状態チェック
        self._check_end_turn_conditions(context)

        game_logger.debug(f"Turn {self.turn_count} processed")

    def _process_player_status_effects(self, context: GameContext) -> None:
        """
        プレイヤーのステータス異常を処理。

        Args:
        ----
            context: ゲームコンテキスト

        """
        player = context.player

        if not hasattr(player, "status_effect_manager"):
            return

        # ステータス異常の経過処理
        player.status_effect_manager.process_turn()

        # ステータス異常によるダメージや効果
        active_effects = player.status_effect_manager.get_active_effects()

        for effect in active_effects:
            if effect.name == "Poison":
                # 毒ダメージ
                damage = 1
                player.take_damage(damage, context)
                context.add_message(f"You take {damage} poison damage!")

                if player.hp <= 0:
                    context.add_message("You died from poison!")

                    # 毒死時のゲームオーバー処理
                    if hasattr(context, "game_logic") and context.game_logic:
                        context.game_logic.record_game_over("Poison")

                    if context.engine and hasattr(context.engine, "game_over"):
                        player_stats = player.get_stats_dict()
                        final_floor = context.get_current_floor_number()
                        context.engine.game_over(player_stats, final_floor, "Poison")

                    return

            elif effect.name == "Paralysis":
                # 麻痺状態の表示（移動処理で制限）
                if self.turn_count % 5 == 0:  # 5ターンごとにメッセージ
                    context.add_message("You are paralyzed!")

            elif effect.name == "Confusion":
                # 混乱状態の表示（移動処理で方向ランダム化）
                if self.turn_count % 3 == 0:  # 3ターンごとにメッセージ
                    context.add_message("You are confused!")

    def _process_monster_turns(self, context: GameContext) -> None:
        """
        モンスターターンを処理。

        Args:
        ----
            context: ゲームコンテキスト

        """
        floor_data = context.get_current_floor_data()
        if not floor_data or not hasattr(floor_data, "monster_spawner"):
            return

        # モンスターターンの処理はMonsterAIManagerに委譲
        # ここでは基本的なターン進行のみ管理
        monsters = floor_data.monster_spawner.monsters.copy()

        for monster in monsters:
            # モンスターが生きている場合のみ処理
            if monster.hp > 0:
                # モンスターのステータス異常処理
                self._process_monster_status_effects(monster)

        # すべてのモンスターのAI処理をMonsterAIManagerに委譲
        if hasattr(context, "monster_ai_manager") and context.monster_ai_manager:
            context.monster_ai_manager.process_all_monsters(context)

    def _process_monster_status_effects(self, monster) -> None:
        """
        モンスターのステータス異常を処理。

        Args:
        ----
            monster: 処理するモンスター

        """
        if not hasattr(monster, "status_effect_manager"):
            return

        # ステータス異常の経過処理
        monster.status_effect_manager.process_turn()

        # モンスターの毒ダメージ処理
        active_effects = monster.status_effect_manager.get_active_effects()

        for effect in active_effects:
            if effect.name == "Poison":
                damage = 1
                monster.hp = max(0, monster.hp - damage)

                if monster.hp <= 0:
                    game_logger.debug(f"{monster.name} died from poison")

    def _process_hunger_system(self, context: GameContext) -> None:
        """
        満腹度システムを処理。

        Args:
        ----
            context: ゲームコンテキスト

        """
        player = context.player

        if not hasattr(player, "hunger"):
            return

        # 満腹度の減少（一定ターンごと）
        if self.turn_count % HungerConstants.HUNGER_DECREASE_INTERVAL == 0:
            old_hunger = player.hunger
            player.hunger = max(0, player.hunger - HungerConstants.HUNGER_DECREASE_RATE)

            # 状態変化のメッセージ
            self._handle_hunger_state_changes(context, old_hunger, player.hunger)

        # 満腹時のボーナス効果
        if player.hunger >= HungerConstants.FULL_THRESHOLD:
            self._apply_full_bonus_effects(context, player)

        # ダメージ処理
        self._process_hunger_damage(context, player)

    def _handle_hunger_state_changes(self, context: GameContext, old_hunger: int, new_hunger: int) -> None:
        """
        飢餓状態変化のメッセージを処理。

        Args:
        ----
            context: ゲームコンテキスト
            old_hunger: 変化前の満腹度
            new_hunger: 変化後の満腹度

        """
        # 状態が変化した場合のメッセージ
        if old_hunger >= HungerConstants.FULL_THRESHOLD and new_hunger < HungerConstants.FULL_THRESHOLD:
            context.add_message("You are no longer full.")
        elif old_hunger >= HungerConstants.CONTENT_THRESHOLD and new_hunger < HungerConstants.CONTENT_THRESHOLD:
            context.add_message("You are starting to feel peckish.")
        elif old_hunger >= HungerConstants.HUNGRY_THRESHOLD and new_hunger < HungerConstants.HUNGRY_THRESHOLD:
            context.add_message("You are getting hungry.")
        elif old_hunger >= HungerConstants.VERY_HUNGRY_THRESHOLD and new_hunger < HungerConstants.VERY_HUNGRY_THRESHOLD:
            context.add_message("You are very hungry and feel weakened!")
        elif old_hunger >= HungerConstants.STARVING_THRESHOLD and new_hunger < HungerConstants.STARVING_THRESHOLD:
            context.add_message("You are starving! Your strength is failing!")

    def _apply_full_bonus_effects(self, context: GameContext, player) -> None:
        """
        満腹時のボーナス効果を適用。

        Args:
        ----
            context: ゲームコンテキスト
            player: プレイヤー

        """
        import random

        # HP自然回復
        if player.hp < player.max_hp and random.random() < HungerConstants.FULL_HP_REGEN_CHANCE:
            player.hp = min(player.max_hp, player.hp + 1)
            context.add_message("You feel refreshed!")

    def _process_hunger_damage(self, context: GameContext, player) -> None:
        """
        飢餓によるダメージを処理。

        Args:
        ----
            context: ゲームコンテキスト
            player: プレイヤー

        """
        # 飢餓状態でのダメージ
        if (
            player.hunger <= HungerConstants.STARVING_THRESHOLD
            and self.turn_count % HungerConstants.STARVING_DAMAGE_INTERVAL == 0
        ):
            damage = HungerConstants.STARVING_DAMAGE
            # 飢餓ダメージは防御力を無視して適用
            if context and hasattr(context, "game_logic") and context.game_logic.is_wizard_mode():
                context.add_message(f"[Wizard] Hunger damage {damage} blocked!")
            else:
                player.hp = max(0, player.hp - damage)
            context.add_message(f"Starvation deals {damage} damage!")

            if player.hp <= 0:
                context.add_message("You died of starvation!")
                # 飢餓死時のゲームオーバー処理
                if hasattr(context, "game_logic") and context.game_logic:
                    context.game_logic.record_game_over("Starvation")

                if context.engine and hasattr(context.engine, "game_over"):
                    player_stats = player.get_stats_dict()
                    final_floor = context.get_current_floor_number()
                    context.engine.game_over(player_stats, final_floor, "Starvation")

        # 非常に空腹状態でのダメージ
        elif (
            player.hunger <= HungerConstants.VERY_HUNGRY_THRESHOLD
            and self.turn_count % HungerConstants.VERY_HUNGRY_DAMAGE_INTERVAL == 0
        ):
            damage = 1
            # 飢餓ダメージは防御力を無視して適用
            if context and hasattr(context, "game_logic") and context.game_logic.is_wizard_mode():
                context.add_message(f"[Wizard] Hunger damage {damage} blocked!")
            else:
                player.hp = max(0, player.hp - damage)
            context.add_message(f"Extreme hunger weakens you for {damage} damage!")

            if player.hp <= 0:
                context.add_message("You collapsed from hunger!")
                # 飢餓死時のゲームオーバー処理
                if hasattr(context, "game_logic") and context.game_logic:
                    context.game_logic.record_game_over("Hunger")

                if context.engine and hasattr(context.engine, "game_over"):
                    player_stats = player.get_stats_dict()
                    final_floor = context.get_current_floor_number()
                    context.engine.game_over(player_stats, final_floor, "Hunger")

    def _process_mp_recovery(self, context: GameContext) -> None:
        """
        MP自然回復を処理。

        Args:
        ----
            context: ゲームコンテキスト

        """
        player = context.player

        if not hasattr(player, "mp") or not hasattr(player, "max_mp"):
            return

        # MP回復（一定ターンごと、満腹度が十分な場合のみ）
        if (
            self.turn_count % MagicConstants.MP_RECOVERY_INTERVAL == 0
            and player.hunger > HungerConstants.HUNGRY_THRESHOLD
        ):
            if player.mp < player.max_mp:
                recovery = MagicConstants.MP_RECOVERY_RATE
                old_mp = player.mp
                player.mp = min(player.max_mp, player.mp + recovery)

                if player.mp > old_mp:
                    game_logger.debug(f"MP recovered: {old_mp} -> {player.mp}")

    def _check_end_turn_conditions(self, context: GameContext) -> None:
        """
        ターン終了時の状態チェック。

        Args:
        ----
            context: ゲームコンテキスト

        """
        player = context.player

        # プレイヤー死亡チェック
        if player.hp <= 0:
            game_logger.info("Player died during turn processing")
            if context.engine and hasattr(context.engine, "state"):
                from pyrogue.core.game_states import GameStates

                context.engine.state = GameStates.GAME_OVER

    def get_turn_statistics(self) -> dict:
        """
        ターン統計情報を取得。

        Returns
        -------
            ターン統計辞書

        """
        return {
            "turn_count": self.turn_count,
            "next_hunger_decrease": HungerConstants.HUNGER_DECREASE_INTERVAL
            - (self.turn_count % HungerConstants.HUNGER_DECREASE_INTERVAL),
            "next_mp_recovery": MagicConstants.MP_RECOVERY_INTERVAL
            - (self.turn_count % MagicConstants.MP_RECOVERY_INTERVAL),
        }

    def reset_turn_count(self) -> None:
        """ターンカウントをリセット。"""
        self.turn_count = 0
        game_logger.debug("Turn count reset")

    def advance_turns(self, count: int, context: GameContext) -> None:
        """
        指定ターン数を一度に進める（休憩などで使用）。

        Args:
        ----
            count: 進めるターン数
            context: ゲームコンテキスト

        """
        for _ in range(count):
            self.process_turn(context)

            # プレイヤーが死亡した場合は中断
            if context.player.hp <= 0:
                break

    def can_act(self, entity) -> bool:
        """
        エンティティが行動可能かチェック。

        Args:
        ----
            entity: チェック対象のエンティティ

        Returns:
        -------
            行動可能な場合True

        """
        if not hasattr(entity, "status_effect_manager"):
            return True

        # 麻痺状態のチェック
        active_effects = entity.status_effect_manager.get_active_effects()
        for effect in active_effects:
            if effect.name == "Paralysis":
                return False

        return True

    def is_confused(self, entity) -> bool:
        """
        エンティティが混乱状態かチェック。

        Args:
        ----
            entity: チェック対象のエンティティ

        Returns:
        -------
            混乱状態の場合True

        """
        if not hasattr(entity, "status_effect_manager"):
            return False

        active_effects = entity.status_effect_manager.get_active_effects()
        for effect in active_effects:
            if effect.name == "Confusion":
                return True

        return False
