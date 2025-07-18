"""
戦闘管理コンポーネント。

このモジュールは、GameLogicから分離された戦闘システムを担当します。
プレイヤーとモンスター間の戦闘、ダメージ計算、経験値獲得を管理します。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from pyrogue.constants import CombatConstants
from pyrogue.utils import game_logger

if TYPE_CHECKING:
    from pyrogue.core.managers.game_context import GameContext
    from pyrogue.entities.actors.monster import Monster
    from pyrogue.entities.actors.player import Player


class CombatManager:
    """
    戦闘システムの管理クラス。

    プレイヤーとモンスター間の戦闘処理、ダメージ計算、
    経験値獲得、死亡処理を担当します。

    Attributes
    ----------
        context: ゲームコンテキスト

    """

    def __init__(self) -> None:
        """戦闘マネージャーを初期化。"""

    def handle_player_attack(self, monster: Monster, context: GameContext) -> bool:
        """
        プレイヤーがモンスターと戦闘。

        Args:
        ----
            monster: 攻撃対象のモンスター
            context: ゲームコンテキスト

        Returns:
        -------
            戦闘が発生した場合True

        """
        player = context.player

        # プレイヤーの攻撃処理
        damage = self._calculate_damage(player, monster)
        monster.hp -= damage

        # 攻撃メッセージ
        context.add_message(f"You attack the {monster.name} for {damage} damage!")

        # モンスター分裂判定（ダメージを受けた時）
        if monster.hp > 0 and hasattr(context, "monster_ai_manager") and context.monster_ai_manager:
            try:
                context.monster_ai_manager.split_monster_on_damage(monster, context)
            except Exception as e:
                # 分裂処理エラーを記録（ゲームを継続）
                if hasattr(context, "add_message"):
                    context.add_message(f"Monster split error: {e}")
                else:
                    print(f"Warning: Monster split error: {e}")

        # モンスターの死亡判定
        if monster.hp <= 0:
            self._handle_monster_death(monster, context)
            return True

        # モンスターの反撃
        self._handle_monster_attack(monster, context)

        return True

    def _handle_monster_attack(self, monster: Monster, context: GameContext) -> None:
        """
        モンスターがプレイヤーを攻撃。

        Args:
        ----
            monster: 攻撃するモンスター
            context: ゲームコンテキスト

        """
        player = context.player

        # モンスターの攻撃処理
        damage = self._calculate_damage(monster, player)

        # ウィザードモード時はダメージを受けない（無敵モード）
        if hasattr(context, "game_logic") and context.game_logic.is_wizard_mode():
            context.add_message(f"[Wizard] The {monster.name} attacks you for {damage} damage, but you are invincible!")
        else:
            player.hp -= damage
            # 攻撃メッセージ
            context.add_message(f"The {monster.name} attacks you for {damage} damage!")

        # 特殊攻撃効果の判定
        self._handle_special_attack_effects(monster, context)

        # プレイヤーの死亡判定
        if player.hp <= 0:
            self._handle_player_death(context, f"Killed by {monster.name}")

    def _handle_special_attack_effects(self, monster: Monster, context: GameContext) -> None:
        """
        モンスターの特殊攻撃効果を処理。

        Args:
        ----
            monster: 攻撃したモンスター
            context: ゲームコンテキスト

        """
        player = context.player

        # 幻覚を引き起こすモンスターの攻撃（30%の確率）
        if hasattr(monster, "ai_pattern") and monster.ai_pattern in [
            "hallucinogenic",
            "psychic",
        ]:
            if random.random() < CombatConstants.HALLUCINATION_EFFECT_CHANCE:
                from pyrogue.entities.actors.status_effects import HallucinationEffect

                hallucination = HallucinationEffect(duration=6)
                player.status_effects.add_effect(hallucination)
                context.add_message(f"The {monster.name}'s attack makes you see strange visions!")

        # その他の特殊攻撃効果もここに追加可能
        # 例：毒攻撃、麻痺攻撃など

    def _calculate_damage(self, attacker, defender) -> int:
        """
        ダメージを計算。

        Args:
        ----
            attacker: 攻撃者
            defender: 防御者

        Returns:
        -------
            計算されたダメージ

        """
        # 基本攻撃力を取得
        base_attack = self._get_attack_power(attacker)

        # クリティカルヒット判定
        is_critical = random.random() < CombatConstants.CRITICAL_HIT_CHANCE
        if is_critical:
            base_attack = int(base_attack * CombatConstants.CRITICAL_HIT_MULTIPLIER)

        # 防御力を取得
        defense = self._get_defense_power(defender)

        # ダメージ計算（防御力による軽減）
        damage = base_attack - int(defense * CombatConstants.DEFENSE_REDUCTION_FACTOR)

        # 最小ダメージ保証
        damage = max(damage, CombatConstants.MIN_DAMAGE)

        # ランダム要素を追加（±20%）
        variance = int(damage * 0.2)
        if variance > 0:
            damage += random.randint(-variance, variance)
            damage = max(damage, CombatConstants.MIN_DAMAGE)

        # クリティカルメッセージ
        if is_critical and hasattr(attacker, "name"):
            if attacker.name == "Player":
                game_logger.debug("Critical hit by player!")
            else:
                game_logger.debug(f"Critical hit by {attacker.name}!")

        return damage

    def _get_attack_power(self, entity) -> int:
        """
        エンティティの攻撃力を取得。

        Args:
        ----
            entity: 攻撃者エンティティ

        Returns:
        -------
            攻撃力

        """
        if hasattr(entity, "get_attack"):
            return entity.get_attack()
        if hasattr(entity, "attack"):
            return entity.attack
        return CombatConstants.BASE_ATTACK_DAMAGE

    def _get_defense_power(self, entity) -> int:
        """
        エンティティの防御力を取得。

        Args:
        ----
            entity: 防御者エンティティ

        Returns:
        -------
            防御力

        """
        if hasattr(entity, "get_defense"):
            return entity.get_defense()
        if hasattr(entity, "defense"):
            return entity.defense
        return 0

    def _handle_monster_death(self, monster: Monster, context: GameContext) -> None:
        """
        モンスターの死亡処理。

        Args:
        ----
            monster: 死亡したモンスター
            context: ゲームコンテキスト

        """
        player = context.player
        floor_data = context.get_current_floor_data()

        # 経験値獲得
        exp_gained = self._calculate_exp_reward(monster, player)
        player.exp += exp_gained

        # モンスター撃破を記録
        player.record_monster_kill()

        context.add_message(f"You defeated the {monster.name}! (+{exp_gained} EXP)")

        # レベルアップチェック
        self._check_level_up(player, context)

        # モンスターをフロアから削除
        if floor_data and hasattr(floor_data, "monster_spawner"):
            floor_data.monster_spawner.remove_monster(monster)

        # ドロップアイテム処理
        self._handle_monster_drops(monster, context)

    def _calculate_exp_reward(self, monster: Monster, player: Player) -> int:
        """
        モンスター撃破時の経験値を計算。

        Args:
        ----
            monster: 撃破されたモンスター
            player: プレイヤー

        Returns:
        -------
            獲得経験値

        """
        # 基本経験値（モンスターのレベルベース）
        base_exp = getattr(monster, "level", 1) * 10

        # プレイヤーレベルによる調整
        level_diff = getattr(monster, "level", 1) - player.level
        if level_diff < 0:
            # 低レベルモンスターからの経験値減少
            base_exp = max(1, base_exp + level_diff * 5)

        return base_exp

    def _check_level_up(self, player: Player, context: GameContext) -> None:
        """
        レベルアップチェック。

        Args:
        ----
            player: プレイヤー
            context: ゲームコンテキスト

        """
        required_exp = self._get_required_exp_for_level(player.level + 1)

        if player.exp >= required_exp:
            # レベルアップ
            old_level = player.level
            player.level += 1

            # ステータス上昇
            hp_gain = CombatConstants.HP_GAIN_PER_LEVEL

            player.max_hp += hp_gain
            player.hp += hp_gain  # HPも回復

            context.add_message(f"Level up! You are now level {player.level}! (+{hp_gain} HP)")

            game_logger.info(f"Player leveled up: {old_level} -> {player.level}")

    def _get_required_exp_for_level(self, level: int) -> int:
        """
        指定レベルに必要な経験値を計算。

        Args:
        ----
            level: 目標レベル

        Returns:
        -------
            必要経験値

        """
        base = CombatConstants.EXP_PER_LEVEL_BASE
        multiplier = CombatConstants.EXP_LEVEL_MULTIPLIER
        return int(base * (multiplier ** (level - 1)))

    def _handle_monster_drops(self, monster: Monster, context: GameContext) -> None:
        """
        モンスターのドロップアイテム処理。

        Args:
        ----
            monster: 死亡したモンスター
            context: ゲームコンテキスト

        """
        floor_data = context.get_current_floor_data()
        if not floor_data:
            return

        # 金貨ドロップの可能性
        if random.random() < CombatConstants.GOLD_DROP_CHANCE:  # 30%の確率で金貨ドロップ
            from pyrogue.entities.items.item import Gold

            gold_amount = random.randint(1, monster.level * 5)
            gold = Gold(monster.x, monster.y, gold_amount)

            floor_data.item_spawner.items.append(gold)
            context.add_message(f"The {monster.name} dropped {gold_amount} gold!")

    def _handle_player_death(self, context: GameContext, death_cause: str = "Unknown") -> None:
        """
        プレイヤーの死亡処理。

        Args:
        ----
            context: ゲームコンテキスト
            death_cause: 死因

        """
        player = context.player
        player.hp = 0  # 確実に0にする

        context.add_message("You have died!")
        game_logger.info(f"Player died in combat: {death_cause}")

        # スコアを記録（GameLogicに委譲）
        if hasattr(context, "game_logic") and context.game_logic:
            context.game_logic.record_game_over(death_cause)

        # ゲームオーバー処理をエンジンに通知
        if context.engine and hasattr(context.engine, "game_over"):
            player_stats = player.get_stats_dict()
            final_floor = context.get_current_floor_number()
            context.engine.game_over(player_stats, final_floor, death_cause)

    def can_attack(self, attacker, x: int, y: int, context: GameContext) -> bool:
        """
        指定座標への攻撃が可能かチェック。

        Args:
        ----
            attacker: 攻撃者
            x: 目標X座標
            y: 目標Y座標
            context: ゲームコンテキスト

        Returns:
        -------
            攻撃可能な場合True

        """
        # 隣接チェック
        dx = abs(attacker.x - x)
        dy = abs(attacker.y - y)

        return dx <= 1 and dy <= 1 and (dx != 0 or dy != 0)

    def get_combat_statistics(self, player: Player) -> dict:
        """
        戦闘統計情報を取得。

        Args:
        ----
            player: プレイヤー

        Returns:
        -------
            戦闘統計辞書

        """
        return {
            "level": player.level,
            "exp": player.exp,
            "next_level_exp": self._get_required_exp_for_level(player.level + 1),
            "attack_power": self._get_attack_power(player),
            "defense_power": self._get_defense_power(player),
            "hp": f"{player.hp}/{player.max_hp}",
        }
