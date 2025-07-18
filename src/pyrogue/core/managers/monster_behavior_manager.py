"""
モンスター行動管理コンポーネント。

このモジュールは、モンスターの行動状態と移動処理を管理します。
AI状態機械、移動制御、協調行動を担当します。
"""

from __future__ import annotations

import random
from enum import Enum
from typing import TYPE_CHECKING

from pyrogue.constants import CombatConstants, ProbabilityConstants
from pyrogue.utils import game_logger

if TYPE_CHECKING:
    from pyrogue.core.managers.game_context import GameContext
    from pyrogue.entities.actors.monster import Monster


class MonsterAIState(Enum):
    """
    モンスターのAI状態を管理するEnum。

    状態遷移により、より自然なモンスターの行動パターンを実現します。
    """

    WANDERING = "wandering"  # 徘徊中（プレイヤーを発見していない）
    ALERTED = "alerted"  # 警戒中（プレイヤーの気配を感じている）
    HUNTING = "hunting"  # 追跡中（プレイヤーを発見して追跡している）
    ATTACKING = "attacking"  # 攻撃中（プレイヤーと戦闘している）
    FLEEING = "fleeing"  # 逃走中（HPが低くなり逃げている）
    RETURNING = "returning"  # 帰還中（元の場所に戻っている）


class MonsterBehaviorManager:
    """
    モンスター行動システムの管理クラス。

    モンスターの状態管理、移動処理、協調行動を担当します。
    """

    def __init__(self) -> None:
        """モンスター行動マネージャーを初期化。"""
        # AI状態管理
        self._monster_states: dict[int, MonsterAIState] = {}
        self._monster_target_positions: dict[int, tuple[int, int]] = {}
        self._monster_alert_timers: dict[int, int] = {}

    def get_monster_state(self, monster_id: int) -> MonsterAIState:
        """
        モンスターの現在の状態を取得。

        Args:
        ----
            monster_id: モンスターID

        Returns:
        -------
            モンスターの現在の状態

        """
        return self._monster_states.get(monster_id, MonsterAIState.WANDERING)

    def set_monster_state(self, monster_id: int, new_state: MonsterAIState) -> None:
        """
        モンスターの状態を設定。

        Args:
        ----
            monster_id: モンスターID
            new_state: 新しい状態

        """
        self._monster_states[monster_id] = new_state

    def process_wandering_state(
        self, monster: Monster, can_see_player: bool, distance: float, context: GameContext
    ) -> None:
        """徘徊状態の処理。"""
        monster_id = id(monster)

        if can_see_player:
            # プレイヤーを発見 → 警戒状態に遷移
            self.set_monster_state(monster_id, MonsterAIState.ALERTED)
            self._monster_alert_timers[monster_id] = 3  # 3ターン警戒
            self._monster_target_positions[monster_id] = (context.player.x, context.player.y)

            # 周囲のモンスターに警告を発する
            self._alert_nearby_monsters(monster, context)

            game_logger.debug(f"{monster.name} spotted player - entering ALERTED state")
        # ランダム移動
        elif random.random() < ProbabilityConstants.MONSTER_MOVE_CHANCE:
            self._random_move(monster, context)

    def process_alerted_state(
        self, monster: Monster, can_see_player: bool, distance: float, context: GameContext
    ) -> None:
        """警戒状態の処理。"""
        monster_id = id(monster)

        if can_see_player:
            # プレイヤーが見える → 追跡状態に遷移
            self.set_monster_state(monster_id, MonsterAIState.HUNTING)
            self._monster_target_positions[monster_id] = (context.player.x, context.player.y)
            game_logger.debug(f"{monster.name} confirmed player presence - entering HUNTING state")
        else:
            # 警戒タイマーを減少
            timer = self._monster_alert_timers.get(monster_id, 0)
            if timer > 0:
                self._monster_alert_timers[monster_id] = timer - 1
                # 最後に見た位置に向かう
                target_pos = self._monster_target_positions.get(monster_id)
                if target_pos:
                    self._move_towards_position(monster, target_pos, context)
            else:
                # タイマー終了 → 徘徊状態に戻る
                self.set_monster_state(monster_id, MonsterAIState.WANDERING)
                game_logger.debug(f"{monster.name} lost interest - returning to WANDERING state")

    def process_hunting_state(
        self, monster: Monster, can_see_player: bool, distance: float, context: GameContext
    ) -> None:
        """追跡状態の処理。"""
        monster_id = id(monster)

        if can_see_player:
            # プレイヤーの位置を更新
            self._monster_target_positions[monster_id] = (context.player.x, context.player.y)

            # 隣接している場合は攻撃状態に遷移
            if distance <= CombatConstants.ADJACENT_DISTANCE_THRESHOLD:
                self.set_monster_state(monster_id, MonsterAIState.ATTACKING)
                return  # 攻撃状態の処理は呼び出し元で行う

            # 追跡継続（呼び出し元で処理）
            return
        # プレイヤーを見失った → 警戒状態に遷移
        self.set_monster_state(monster_id, MonsterAIState.ALERTED)
        self._monster_alert_timers[monster_id] = 5  # 5ターン警戒
        game_logger.debug(f"{monster.name} lost sight of player - entering ALERTED state")

    def process_attacking_state(
        self, monster: Monster, can_see_player: bool, distance: float, context: GameContext
    ) -> None:
        """攻撃状態の処理。"""
        monster_id = id(monster)

        if can_see_player and distance <= CombatConstants.ADJACENT_DISTANCE_THRESHOLD:
            # 攻撃継続（呼び出し元で処理）
            return
        # 距離が離れた → 追跡状態に遷移
        self.set_monster_state(monster_id, MonsterAIState.HUNTING)

    def process_fleeing_state(self, monster: Monster, context: GameContext) -> None:
        """逃走状態の処理。"""
        monster_id = id(monster)

        # HP回復判定
        if not self._should_flee(monster):
            # 逃走の必要がなくなった → 警戒状態に遷移
            self.set_monster_state(monster_id, MonsterAIState.ALERTED)
            self._monster_alert_timers[monster_id] = 3
            game_logger.debug(f"{monster.name} recovered - entering ALERTED state")
        else:
            # 逃走継続
            self._flee_from_player(monster, context.player, context)

    def process_returning_state(self, monster: Monster, can_see_player: bool, context: GameContext) -> None:
        """帰還状態の処理。"""
        monster_id = id(monster)

        if can_see_player:
            # プレイヤーを発見 → 警戒状態に遷移
            self.set_monster_state(monster_id, MonsterAIState.ALERTED)
            self._monster_alert_timers[monster_id] = 3
            game_logger.debug(f"{monster.name} spotted player while returning - entering ALERTED state")
        # 帰還動作（現在は単純にランダム移動）
        elif random.random() < ProbabilityConstants.MONSTER_MOVE_CHANCE:
            self._random_move(monster, context)

    def try_move_monster(self, monster: Monster, dx: int, dy: int, context: GameContext) -> bool:
        """
        モンスターの移動を試行。

        Args:
        ----
            monster: 移動するモンスター
            dx: X方向の移動量
            dy: Y方向の移動量
            context: ゲームコンテキスト

        Returns:
        -------
            移動が成功した場合True

        """
        new_x = monster.x + dx
        new_y = monster.y + dy

        # 移動可能かチェック
        if self._can_monster_move_to(new_x, new_y, context):
            # MonsterSpawnerの占有位置も更新
            floor_data = context.get_current_floor_data()
            if hasattr(floor_data, "monster_spawner"):
                spawner = floor_data.monster_spawner
                # 古い位置を削除
                old_pos = (monster.x, monster.y)
                if old_pos in spawner.occupied_positions:
                    spawner.occupied_positions.remove(old_pos)

                # 新しい位置を追加
                spawner.occupied_positions.add((new_x, new_y))

            # モンスターの位置を更新
            monster.x = new_x
            monster.y = new_y
            return True

        return False

    def _can_monster_move_to(self, x: int, y: int, context: GameContext) -> bool:
        """
        モンスターが指定座標に移動可能かチェック。

        Args:
        ----
            x: 目標X座標
            y: 目標Y座標
            context: ゲームコンテキスト

        Returns:
        -------
            移動可能な場合True

        """
        floor_data = context.get_current_floor_data()
        if not floor_data:
            return False

        # 境界チェック
        if x < 0 or y < 0 or y >= floor_data.tiles.shape[0] or x >= floor_data.tiles.shape[1]:
            return False

        # タイルチェック
        tile = floor_data.tiles[y, x]
        if not getattr(tile, "walkable", False):
            return False

        # プレイヤーの位置チェック
        player = context.player
        if player.x == x and player.y == y:
            return False

        # 他のモンスターとの重複チェック
        if hasattr(floor_data, "monster_spawner"):
            for other_monster in floor_data.monster_spawner.monsters:
                if other_monster.x == x and other_monster.y == y:
                    return False

        return True

    def _random_move(self, monster: Monster, context: GameContext) -> None:
        """
        モンスターがランダムに移動。

        Args:
        ----
            monster: 移動するモンスター
            context: ゲームコンテキスト

        """
        # ランダムな方向を選択
        dx = random.randint(-1, 1)
        dy = random.randint(-1, 1)

        # 移動実行
        self.try_move_monster(monster, dx, dy, context)

    def _move_towards_position(self, monster: Monster, target_pos: tuple[int, int], context: GameContext) -> None:
        """
        指定された位置に向かって移動。

        Args:
        ----
            monster: 移動するモンスター
            target_pos: 目標位置
            context: ゲームコンテキスト

        """
        target_x, target_y = target_pos
        dx = 0
        dy = 0

        if monster.x < target_x:
            dx = 1
        elif monster.x > target_x:
            dx = -1

        if monster.y < target_y:
            dy = 1
        elif monster.y > target_y:
            dy = -1

        # 混乱状態の場合はランダム方向
        if self._is_confused(monster):
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)

        # 移動実行
        self.try_move_monster(monster, dx, dy, context)

    def _alert_nearby_monsters(self, alerting_monster: Monster, context: GameContext) -> None:
        """
        周囲のモンスターを警戒状態にする。

        Args:
        ----
            alerting_monster: 警告を発するモンスター
            context: ゲームコンテキスト

        """
        floor_data = context.get_current_floor_data()
        if not floor_data or not hasattr(floor_data, "monster_spawner"):
            return

        alert_radius = 5  # 警告範囲
        alerted_count = 0

        for monster in floor_data.monster_spawner.monsters:
            if monster == alerting_monster:
                continue

            # 距離チェック
            distance = self._calculate_distance(alerting_monster.x, alerting_monster.y, monster.x, monster.y)

            if distance <= alert_radius:
                monster_id = id(monster)
                current_state = self.get_monster_state(monster_id)

                # 既に警戒状態以上の場合はスキップ
                if current_state in [MonsterAIState.ALERTED, MonsterAIState.HUNTING, MonsterAIState.ATTACKING]:
                    continue

                # 警戒状態に遷移
                self.set_monster_state(monster_id, MonsterAIState.ALERTED)
                self._monster_alert_timers[monster_id] = 3
                self._monster_target_positions[monster_id] = (context.player.x, context.player.y)

                alerted_count += 1

        if alerted_count > 0:
            game_logger.debug(f"{alerting_monster.name} alerted {alerted_count} nearby monsters")

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
        if not hasattr(monster, "can_flee") or not monster.can_flee:
            return False

        # HP比率による逃走判定
        hp_ratio = monster.hp / monster.max_hp
        flee_threshold = getattr(monster, "flee_threshold", ProbabilityConstants.MONSTER_FLEE_THRESHOLD)

        if hp_ratio <= flee_threshold:
            monster.is_fleeing = True
            return True

        return getattr(monster, "is_fleeing", False)

    def _flee_from_player(self, monster: Monster, player, context: GameContext) -> None:
        """
        プレイヤーから逃走する。

        Args:
        ----
            monster: 逃走するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        # プレイヤーから遠ざかる方向を計算
        dx = monster.x - player.x
        dy = monster.y - player.y

        # 正規化（-1, 0, 1のいずれか）
        if dx != 0:
            dx = dx // abs(dx)
        if dy != 0:
            dy = dy // abs(dy)

        # 逃走方向に移動を試行
        if not self.try_move_monster(monster, dx, dy, context):
            # 直線的に逃げられない場合はランダム移動
            self._random_move(monster, context)

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
        if not hasattr(monster, "status_effect_manager"):
            return False

        active_effects = monster.status_effect_manager.get_active_effects()
        for effect in active_effects:
            if effect.name == "Confusion":
                return True

        return False

    def _calculate_distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """
        2点間の距離を計算。

        Args:
        ----
            x1, y1: 点1の座標
            x2, y2: 点2の座標

        Returns:
        -------
            ユークリッド距離

        """
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def get_monster_behavior_info(self, monster: Monster) -> dict:
        """
        モンスターの行動情報を取得。

        Args:
        ----
            monster: 対象モンスター

        Returns:
        -------
            行動情報辞書

        """
        monster_id = id(monster)
        return {
            "ai_state": self.get_monster_state(monster_id).value,
            "alert_timer": self._monster_alert_timers.get(monster_id, 0),
            "target_position": self._monster_target_positions.get(monster_id),
            "is_fleeing": getattr(monster, "is_fleeing", False),
        }
