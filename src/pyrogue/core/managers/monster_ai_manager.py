"""
リファクタリング済みモンスターAI管理コンポーネント。

このモジュールは、分離されたマネージャーを統合してモンスターAIシステムを提供します。
責務分離により、保守性と拡張性が向上しています。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from pyrogue.constants import CombatConstants, GameConstants
from pyrogue.core.managers.monster_behavior_manager import MonsterAIState, MonsterBehaviorManager
from pyrogue.core.managers.monster_combat_manager import MonsterCombatManager
from pyrogue.core.managers.pathfinding_manager import PathfindingManager
from pyrogue.utils import game_logger
from pyrogue.utils.coordinate_utils import calculate_distance, get_direction_to_target, has_line_of_sight

if TYPE_CHECKING:
    from pyrogue.core.managers.game_context import GameContext
    from pyrogue.entities.actors.monster import Monster


class MonsterAIManager:
    """
    リファクタリング済みモンスターAIシステムの管理クラス。

    分離されたマネージャーを統合し、モンスターの行動決定、
    プレイヤー追跡、戦闘、経路探索を管理します。
    """

    def __init__(self) -> None:
        """モンスターAIマネージャーを初期化。"""
        # 専門マネージャーの初期化
        self._behavior_manager = MonsterBehaviorManager()
        self._combat_manager = MonsterCombatManager()
        self._pathfinding_manager = PathfindingManager()

        # パフォーマンス最適化用の視界キャッシュ
        self._vision_cache: dict[tuple[int, int], bool] = {}
        self._last_player_position: tuple[int, int] = (-1, -1)

    def process_monster_ai(self, monster: Monster, context: GameContext) -> None:
        """
        モンスターのAI処理を実行。

        Args:
        ----
            monster: 処理するモンスター
            context: ゲームコンテキスト

        """
        # モンスターが行動可能かチェック
        if not self._can_monster_act(monster):
            return

        # 特殊能力のクールダウンを減少
        if hasattr(monster, "special_ability_cooldown") and monster.special_ability_cooldown > 0:
            monster.special_ability_cooldown -= 1

        # モンスターIDを取得（状態管理用）
        monster_id = id(monster)

        # 現在の状態を取得（初回はWANDERING）
        current_state = self._behavior_manager.get_monster_state(monster_id)

        # 状態に基づいたAI処理
        self._process_monster_ai_by_state(monster, current_state, context)

    def _process_monster_ai_by_state(self, monster: Monster, state: MonsterAIState, context: GameContext) -> None:
        """
        状態に基づいたモンスターAI処理。

        Args:
        ----
            monster: 処理するモンスター
            state: 現在のAI状態
            context: ゲームコンテキスト

        """
        player = context.player
        monster_id = id(monster)

        # 逃走判定（全状態で優先）
        if self._should_flee(monster):
            self._behavior_manager.set_monster_state(monster_id, MonsterAIState.FLEEING)
            self._behavior_manager.process_fleeing_state(monster, context)
            return

        # プレイヤーが見えるかチェック（キャッシュ付き）
        can_see_player = self._can_monster_see_player_cached(monster, player, context)
        distance = calculate_distance(monster.x, monster.y, player.x, player.y)

        if state == MonsterAIState.WANDERING:
            self._behavior_manager.process_wandering_state(monster, can_see_player, distance, context)
        elif state == MonsterAIState.ALERTED:
            self._behavior_manager.process_alerted_state(monster, can_see_player, distance, context)
        elif state == MonsterAIState.HUNTING:
            self._process_hunting_state(monster, can_see_player, distance, context)
        elif state == MonsterAIState.ATTACKING:
            self._process_attacking_state(monster, can_see_player, distance, context)
        elif state == MonsterAIState.FLEEING:
            self._behavior_manager.process_fleeing_state(monster, context)
        elif state == MonsterAIState.RETURNING:
            self._behavior_manager.process_returning_state(monster, can_see_player, context)

    def _process_hunting_state(
        self, monster: Monster, can_see_player: bool, distance: float, context: GameContext
    ) -> None:
        """追跡状態の処理。"""
        # 行動管理処理
        self._behavior_manager.process_hunting_state(monster, can_see_player, distance, context)

        # 攻撃状態に遷移した場合は攻撃処理
        monster_id = id(monster)
        if self._behavior_manager.get_monster_state(monster_id) == MonsterAIState.ATTACKING:
            self._process_attacking_state(monster, can_see_player, distance, context)
            return

        # 追跡継続
        if can_see_player:
            # 遠距離攻撃可能かチェック
            if self._combat_manager.can_use_ranged_attack(monster, context.player):
                self._combat_manager.use_ranged_attack(monster, context.player, context)
            else:
                # プレイヤーを追跡
                self._chase_player(monster, context.player, context)

    def _process_attacking_state(
        self, monster: Monster, can_see_player: bool, distance: float, context: GameContext
    ) -> None:
        """攻撃状態の処理。"""
        # 行動管理処理
        self._behavior_manager.process_attacking_state(monster, can_see_player, distance, context)

        # 攻撃実行
        if can_see_player and distance <= CombatConstants.ADJACENT_DISTANCE_THRESHOLD:
            if self._combat_manager.can_use_special_attack(monster):
                self._combat_manager.use_special_attack(monster, context.player, context)
            else:
                self._monster_attack_player(monster, context)

    def _chase_player(self, monster: Monster, player, context: GameContext) -> None:
        """
        モンスターがプレイヤーを追跡。

        Args:
        ----
            monster: 追跡するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        # プレイヤーとの距離が1の場合は攻撃
        if calculate_distance(monster.x, monster.y, player.x, player.y) <= CombatConstants.ADJACENT_DISTANCE_THRESHOLD:
            self._monster_attack_player(monster, context)
            return

        # 混乱状態の場合はランダム方向
        if self._is_confused(monster):
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            self._behavior_manager.try_move_monster(monster, dx, dy, context)
            return

        # 高度な経路探索を試行
        if self._use_pathfinding(monster, player, context):
            return

        # フォールバック: 単純な直線移動
        self._move_towards_player_simple(monster, player, context)

    def _use_pathfinding(self, monster: Monster, player, context: GameContext) -> bool:
        """
        経路探索を使用してプレイヤーを追跡。

        Args:
        ----
            monster: 追跡するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        Returns:
        -------
            経路探索に成功した場合True

        """
        # 経路を探索
        path = self._pathfinding_manager.find_path(monster.x, monster.y, player.x, player.y, context)

        if path and len(path) > 1:
            # 次の位置に移動
            next_pos = path[1]
            dx = next_pos[0] - monster.x
            dy = next_pos[1] - monster.y
            return self._behavior_manager.try_move_monster(monster, dx, dy, context)

        return False

    def _move_towards_player_simple(self, monster: Monster, player, context: GameContext) -> None:
        """
        単純な直線移動でプレイヤーに向かう。

        Args:
        ----
            monster: 移動するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        dx, dy = get_direction_to_target(monster.x, monster.y, player.x, player.y)
        self._behavior_manager.try_move_monster(monster, dx, dy, context)

    def _can_monster_act(self, monster: Monster) -> bool:
        """
        モンスターが行動可能かチェック。

        Args:
        ----
            monster: チェック対象のモンスター

        Returns:
        -------
            行動可能な場合True

        """
        # HPチェック
        if monster.hp <= 0:
            return False

        # ステータス異常チェック
        if hasattr(monster, "status_effect_manager"):
            active_effects = monster.status_effect_manager.get_active_effects()
            for effect in active_effects:
                if effect.name == "Paralysis":
                    return False

        return True

    def _can_monster_see_player_cached(self, monster: Monster, player, context: GameContext) -> bool:
        """
        モンスターがプレイヤーを見ることができるかキャッシュ付きでチェック。

        Args:
        ----
            monster: モンスター
            player: プレイヤー
            context: ゲームコンテキスト

        Returns:
        -------
            プレイヤーが見える場合True

        """
        monster_pos = (monster.x, monster.y)

        # キャッシュから結果を取得
        if monster_pos in self._vision_cache:
            return self._vision_cache[monster_pos]

        # キャッシュにない場合は計算
        can_see = self._can_monster_see_player(monster, player, context)
        self._vision_cache[monster_pos] = can_see

        return can_see

    def _can_monster_see_player(self, monster: Monster, player, context: GameContext) -> bool:
        """
        モンスターがプレイヤーを見ることができるかチェック。

        Args:
        ----
            monster: モンスター
            player: プレイヤー
            context: ゲームコンテキスト

        Returns:
        -------
            プレイヤーが見える場合True

        """
        # 距離チェック（視界範囲内か）
        distance = calculate_distance(monster.x, monster.y, player.x, player.y)
        sight_range = getattr(monster, "sight_range", 8)  # デフォルト視界範囲

        if distance > sight_range:
            return False

        # 障害物チェック（壁越しには見えない）
        return has_line_of_sight(monster.x, monster.y, player.x, player.y, context)

    def _should_flee(self, monster: Monster) -> bool:
        """
        モンスターが逃走すべきかチェック。

        Args:
        ----
            monster: チェック対象のモンスター

        Returns:
        -------
            逃走すべき場合True

        """
        return self._behavior_manager._should_flee(monster)

    def _is_confused(self, monster: Monster) -> bool:
        """
        モンスターが混乱状態かチェック。

        Args:
        ----
            monster: チェック対象のモンスター

        Returns:
        -------
            混乱状態の場合True

        """
        return self._behavior_manager._is_confused(monster)

    def _monster_attack_player(self, monster: Monster, context: GameContext) -> None:
        """
        モンスターがプレイヤーを攻撃。

        Args:
        ----
            monster: 攻撃するモンスター
            context: ゲームコンテキスト

        """
        # 戦闘処理はCombatManagerに委譲
        # ここではAIの観点での攻撃決定のみ
        game_logger.debug(f"{monster.name} attacks player")

    def process_all_monsters(self, context: GameContext) -> None:
        """
        全モンスターのAI処理を実行。

        Args:
        ----
            context: ゲームコンテキスト

        """
        floor_data = context.get_current_floor_data()
        if not floor_data or not hasattr(floor_data, "monster_spawner"):
            return

        # プレイヤーの位置が変わった場合、キャッシュをクリア
        player_pos = (context.player.x, context.player.y)
        if player_pos != self._last_player_position:
            self._vision_cache.clear()
            self._pathfinding_manager.clear_cache()
            self._last_player_position = player_pos

        # モンスターリストをコピー（処理中の変更に対応）
        monsters = floor_data.monster_spawner.monsters.copy()

        # アクティブエリア内のモンスターのみ処理
        active_monsters = self._get_active_monsters(monsters, context)

        for monster in active_monsters:
            if monster.hp > 0:  # 生きているモンスターのみ処理
                self.process_monster_ai(monster, context)

    def _get_active_monsters(self, monsters: list[Monster], context: GameContext) -> list[Monster]:
        """
        アクティブエリア内のモンスターを取得。

        Args:
        ----
            monsters: 全モンスターのリスト
            context: ゲームコンテキスト

        Returns:
        -------
            アクティブエリア内のモンスターのリスト

        """
        active_monsters = []
        player = context.player
        active_radius = GameConstants.AI_ACTIVE_AREA_RADIUS

        for monster in monsters:
            # プレイヤーとの距離を計算
            distance = calculate_distance(monster.x, monster.y, player.x, player.y)

            # アクティブエリア内のモンスターのみ処理
            if distance <= active_radius:
                active_monsters.append(monster)

        game_logger.debug(f"Active monsters: {len(active_monsters)}/{len(monsters)}")
        return active_monsters

    def get_monster_behavior_info(self, monster: Monster, context: GameContext) -> dict:
        """
        モンスターの行動情報を取得。

        Args:
        ----
            monster: 対象モンスター
            context: ゲームコンテキスト

        Returns:
        -------
            行動情報辞書

        """
        player = context.player
        behavior_info = self._behavior_manager.get_monster_behavior_info(monster)

        return {
            "can_act": self._can_monster_act(monster),
            "can_see_player": self._can_monster_see_player(monster, player, context),
            "distance_to_player": calculate_distance(monster.x, monster.y, player.x, player.y),
            "is_confused": self._is_confused(monster),
            "sight_range": getattr(monster, "sight_range", 8),
            **behavior_info,
        }

    def set_monster_aggressive(self, monster: Monster, aggressive: bool = True) -> None:
        """
        モンスターの攻撃性を設定。

        Args:
        ----
            monster: 対象モンスター
            aggressive: 攻撃的にするかどうか

        """
        if hasattr(monster, "aggressive"):
            monster.aggressive = aggressive  # type: ignore
        if hasattr(monster, "sight_range"):
            if aggressive:
                monster.sight_range = getattr(monster, "sight_range", 8) * 2  # type: ignore
            else:
                monster.sight_range = getattr(monster, "sight_range", 8) // 2  # type: ignore

    def split_monster_on_damage(self, monster: Monster, context: GameContext) -> None:
        """
        ダメージを受けた時のモンスター分裂処理。

        Args:
        ----
            monster: 分裂するモンスター
            context: ゲームコンテキスト

        """
        self._combat_manager.split_monster_on_damage(monster, context)
