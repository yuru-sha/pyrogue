"""
モンスターAI管理コンポーネント。

このモジュールは、GameLogicから分離されたモンスターAIシステムを担当します。
モンスターの行動決定、プレイヤー追跡、ランダム移動、視界判定を管理します。
"""

from __future__ import annotations

import random
from enum import Enum
from typing import TYPE_CHECKING

import tcod

from pyrogue.constants import CombatConstants, GameConstants, ProbabilityConstants
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


class MonsterAIManager:
    """
    モンスターAIシステムの管理クラス。

    モンスターの行動決定、プレイヤー追跡、
    ランダム移動、視界判定を担当します。
    """

    def __init__(self) -> None:
        """モンスターAIマネージャーを初期化。"""
        # パフォーマンス最適化用の視界キャッシュ
        self._vision_cache: dict[tuple[int, int], bool] = {}
        self._last_player_position: tuple[int, int] = (-1, -1)

        # AI状態管理
        self._monster_states: dict[int, MonsterAIState] = {}
        self._monster_target_positions: dict[int, tuple[int, int]] = {}
        self._monster_alert_timers: dict[int, int] = {}

        # 経路探索キャッシュ
        self._pathfinding_cache: dict[tuple[int, int, int, int], list[tuple[int, int]]] = {}
        self._last_pathfinding_update: int = 0

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
        current_state = self._monster_states.get(monster_id, MonsterAIState.WANDERING)

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
            self._set_monster_state(monster_id, MonsterAIState.FLEEING)
            self._flee_from_player(monster, player, context)
            return

        # プレイヤーが見えるかチェック（キャッシュ付き）
        can_see_player = self._can_monster_see_player_cached(monster, player, context)
        distance = self._calculate_distance(monster.x, monster.y, player.x, player.y)

        if state == MonsterAIState.WANDERING:
            self._process_wandering_state(monster, can_see_player, distance, context)
        elif state == MonsterAIState.ALERTED:
            self._process_alerted_state(monster, can_see_player, distance, context)
        elif state == MonsterAIState.HUNTING:
            self._process_hunting_state(monster, can_see_player, distance, context)
        elif state == MonsterAIState.ATTACKING:
            self._process_attacking_state(monster, can_see_player, distance, context)
        elif state == MonsterAIState.FLEEING:
            self._process_fleeing_state(monster, context)
        elif state == MonsterAIState.RETURNING:
            self._process_returning_state(monster, can_see_player, context)

    def _process_wandering_state(
        self, monster: Monster, can_see_player: bool, distance: float, context: GameContext
    ) -> None:
        """徘徊状態の処理。"""
        monster_id = id(monster)

        if can_see_player:
            # プレイヤーを発見 → 警戒状態に遷移
            self._set_monster_state(monster_id, MonsterAIState.ALERTED)
            self._monster_alert_timers[monster_id] = 3  # 3ターン警戒
            self._monster_target_positions[monster_id] = (context.player.x, context.player.y)

            # 周囲のモンスターに警告を発する
            self._alert_nearby_monsters(monster, context)

            game_logger.debug(f"{monster.name} spotted player - entering ALERTED state")
        # ランダム移動
        elif random.random() < ProbabilityConstants.MONSTER_MOVE_CHANCE:
            self._random_move(monster, context)

    def _process_alerted_state(
        self, monster: Monster, can_see_player: bool, distance: float, context: GameContext
    ) -> None:
        """警戒状態の処理。"""
        monster_id = id(monster)

        if can_see_player:
            # プレイヤーが見える → 追跡状態に遷移
            self._set_monster_state(monster_id, MonsterAIState.HUNTING)
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
                self._set_monster_state(monster_id, MonsterAIState.WANDERING)
                game_logger.debug(f"{monster.name} lost interest - returning to WANDERING state")

    def _process_hunting_state(
        self, monster: Monster, can_see_player: bool, distance: float, context: GameContext
    ) -> None:
        """追跡状態の処理。"""
        monster_id = id(monster)

        if can_see_player:
            # プレイヤーの位置を更新
            self._monster_target_positions[monster_id] = (context.player.x, context.player.y)

            # 隣接している場合は攻撃状態に遷移
            if distance <= CombatConstants.ADJACENT_DISTANCE_THRESHOLD:
                self._set_monster_state(monster_id, MonsterAIState.ATTACKING)
                self._process_attacking_state(monster, can_see_player, distance, context)
            # 遠距離攻撃可能かチェック
            elif self._can_use_ranged_attack(monster, context.player):
                self._use_ranged_attack(monster, context.player, context)
            else:
                # プレイヤーを追跡
                self._chase_player(monster, context.player, context)
        else:
            # プレイヤーを見失った → 警戒状態に遷移
            self._set_monster_state(monster_id, MonsterAIState.ALERTED)
            self._monster_alert_timers[monster_id] = 5  # 5ターン警戒
            game_logger.debug(f"{monster.name} lost sight of player - entering ALERTED state")

    def _process_attacking_state(
        self, monster: Monster, can_see_player: bool, distance: float, context: GameContext
    ) -> None:
        """攻撃状態の処理。"""
        monster_id = id(monster)

        if can_see_player and distance <= CombatConstants.ADJACENT_DISTANCE_THRESHOLD:
            # 隣接している場合は攻撃
            if self._can_use_special_attack(monster):
                self._use_special_attack(monster, context.player, context)
            else:
                self._monster_attack_player(monster, context)
        else:
            # 距離が離れた → 追跡状態に遷移
            self._set_monster_state(monster_id, MonsterAIState.HUNTING)
            self._process_hunting_state(monster, can_see_player, distance, context)

    def _process_fleeing_state(self, monster: Monster, context: GameContext) -> None:
        """逃走状態の処理。"""
        monster_id = id(monster)

        # HP回復判定
        if not self._should_flee(monster):
            # 逃走の必要がなくなった → 警戒状態に遷移
            self._set_monster_state(monster_id, MonsterAIState.ALERTED)
            self._monster_alert_timers[monster_id] = 3
            game_logger.debug(f"{monster.name} recovered - entering ALERTED state")
        else:
            # 逃走継続
            self._flee_from_player(monster, context.player, context)

    def _process_returning_state(self, monster: Monster, can_see_player: bool, context: GameContext) -> None:
        """帰還状態の処理。"""
        monster_id = id(monster)

        if can_see_player:
            # プレイヤーを発見 → 警戒状態に遷移
            self._set_monster_state(monster_id, MonsterAIState.ALERTED)
            self._monster_alert_timers[monster_id] = 3
            game_logger.debug(f"{monster.name} spotted player while returning - entering ALERTED state")
        # 帰還動作（現在は単純にランダム移動）
        elif random.random() < ProbabilityConstants.MONSTER_MOVE_CHANCE:
            self._random_move(monster, context)

    def _set_monster_state(self, monster_id: int, new_state: MonsterAIState) -> None:
        """
        モンスターの状態を設定。

        Args:
        ----
            monster_id: モンスターID
            new_state: 新しい状態

        """
        self._monster_states[monster_id] = new_state

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
        self._try_move_monster(monster, dx, dy, context)

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
                current_state = self._monster_states.get(monster_id, MonsterAIState.WANDERING)

                # 既に警戒状態以上の場合はスキップ
                if current_state in [MonsterAIState.ALERTED, MonsterAIState.HUNTING, MonsterAIState.ATTACKING]:
                    continue

                # 警戒状態に遷移
                self._set_monster_state(monster_id, MonsterAIState.ALERTED)
                self._monster_alert_timers[monster_id] = 3
                self._monster_target_positions[monster_id] = (context.player.x, context.player.y)

                alerted_count += 1

        if alerted_count > 0:
            game_logger.debug(f"{alerting_monster.name} alerted {alerted_count} nearby monsters")

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
        distance = self._calculate_distance(monster.x, monster.y, player.x, player.y)
        sight_range = getattr(monster, "sight_range", 8)  # デフォルト視界範囲

        if distance > sight_range:
            return False

        # 障害物チェック（壁越しには見えない）
        return self._has_line_of_sight(monster.x, monster.y, player.x, player.y, context)

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

    def _has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int, context: GameContext) -> bool:
        """
        2点間に視界があるかチェック。

        Args:
        ----
            x1, y1: 開始点の座標
            x2, y2: 終了点の座標
            context: ゲームコンテキスト

        Returns:
        -------
            視界がある場合True

        """
        floor_data = context.get_current_floor_data()
        if not floor_data:
            return False

        # ブレゼンハム線分アルゴリズムで視界チェック
        points = self._get_line_points(x1, y1, x2, y2)

        for x, y in points[1:-1]:  # 開始点と終了点は除外
            if 0 <= y < floor_data.tiles.shape[0] and 0 <= x < floor_data.tiles.shape[1]:
                tile = floor_data.tiles[y, x]
                if not getattr(tile, "transparent", True):
                    return False

        return True

    def _get_line_points(self, x1: int, y1: int, x2: int, y2: int) -> list[tuple[int, int]]:
        """
        ブレゼンハム線分アルゴリズムで線上の点を取得。

        Args:
        ----
            x1, y1: 開始点の座標
            x2, y2: 終了点の座標

        Returns:
        -------
            線上の点のリスト

        """
        points = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        x_inc = 1 if x1 < x2 else -1
        y_inc = 1 if y1 < y2 else -1
        error = dx - dy

        while True:
            points.append((x, y))
            if x == x2 and y == y2:
                break

            e2 = 2 * error
            if e2 > -dy:
                error -= dy
                x += x_inc
            if e2 < dx:
                error += dx
                y += y_inc

        return points

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
        if (
            self._calculate_distance(monster.x, monster.y, player.x, player.y)
            <= CombatConstants.ADJACENT_DISTANCE_THRESHOLD
        ):
            self._monster_attack_player(monster, context)
            return

        # 混乱状態の場合はランダム方向
        if self._is_confused(monster):
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            self._try_move_monster(monster, dx, dy, context)
            return

        # 高度な経路探索を試行
        if self._use_pathfinding(monster, player, context):
            return

        # フォールバック: 単純な直線移動
        self._move_towards_player_simple(monster, player, context)

    def _use_pathfinding(self, monster: Monster, player, context: GameContext) -> bool:
        """
        A*アルゴリズムを使用した経路探索でプレイヤーを追跡。

        Args:
        ----
            monster: 追跡するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        Returns:
        -------
            経路探索に成功した場合True

        """
        # 距離が遠い場合は経路探索を使用しない（パフォーマンス最適化）
        distance = self._calculate_distance(monster.x, monster.y, player.x, player.y)
        if distance > 15:
            return False

        # キャッシュから経路を取得
        cache_key = (monster.x, monster.y, player.x, player.y)
        if cache_key in self._pathfinding_cache:
            path = self._pathfinding_cache[cache_key]
            if len(path) > 1:
                next_pos = path[1]  # 次の位置
                dx = next_pos[0] - monster.x
                dy = next_pos[1] - monster.y
                return self._try_move_monster(monster, dx, dy, context)
            return False

        # 経路探索を実行
        path = self._find_path(monster.x, monster.y, player.x, player.y, context)
        if path and len(path) > 1:
            # キャッシュに保存
            self._pathfinding_cache[cache_key] = path

            # 次の位置に移動
            next_pos = path[1]
            dx = next_pos[0] - monster.x
            dy = next_pos[1] - monster.y
            return self._try_move_monster(monster, dx, dy, context)

        return False

    def _find_path(
        self, start_x: int, start_y: int, end_x: int, end_y: int, context: GameContext
    ) -> list[tuple[int, int]] | None:
        """
        A*アルゴリズムを使用して経路を探索。

        Args:
        ----
            start_x, start_y: 開始位置
            end_x, end_y: 終了位置
            context: ゲームコンテキスト

        Returns:
        -------
            経路のリスト（見つからない場合はNone）

        """
        floor_data = context.get_current_floor_data()
        if not floor_data:
            return None

        # コストマップを作成
        cost_map = self._create_cost_map(context)
        if cost_map is None:
            return None

        # A*アルゴリズムを実行
        try:
            path = tcod.path.find_path(
                cost_map,
                start=(start_x, start_y),
                end=(end_x, end_y),
                diagonal=True,
                algorithm=tcod.path.DIJKSTRA,  # オリジナルRogue感を保つため、より単純なアルゴリズムを使用
            )
            return [(x, y) for x, y in path]
        except Exception as e:
            game_logger.debug(f"Pathfinding failed: {e}")
            return None

    def _create_cost_map(self, context: GameContext) -> tcod.path.Pathfinder | None:
        """
        経路探索用のコストマップを作成。

        Args:
        ----
            context: ゲームコンテキスト

        Returns:
        -------
            コストマップ（作成に失敗した場合はNone）

        """
        floor_data = context.get_current_floor_data()
        if not floor_data:
            return None

        try:
            # タイルの歩行可能性に基づいてコストを設定
            height, width = floor_data.tiles.shape
            cost_array = tcod.numpy.zeros((height, width), dtype=tcod.numpy.int8)

            for y in range(height):
                for x in range(width):
                    tile = floor_data.tiles[y, x]
                    if getattr(tile, "walkable", False):
                        cost_array[y, x] = 1  # 歩行可能
                    else:
                        cost_array[y, x] = 0  # 歩行不可

            return tcod.path.Pathfinder(cost_array)
        except Exception as e:
            game_logger.debug(f"Cost map creation failed: {e}")
            return None

    def _move_towards_player_simple(self, monster: Monster, player, context: GameContext) -> None:
        """
        単純な直線移動でプレイヤーに向かう。

        Args:
        ----
            monster: 移動するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        dx = 0
        dy = 0

        if monster.x < player.x:
            dx = 1
        elif monster.x > player.x:
            dx = -1

        if monster.y < player.y:
            dy = 1
        elif monster.y > player.y:
            dy = -1

        # 移動実行
        self._try_move_monster(monster, dx, dy, context)

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
        self._try_move_monster(monster, dx, dy, context)

    def _try_move_monster(self, monster: Monster, dx: int, dy: int, context: GameContext) -> bool:
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

        monster_id = id(monster)
        return {
            "can_act": self._can_monster_act(monster),
            "can_see_player": self._can_monster_see_player(monster, player, context),
            "distance_to_player": self._calculate_distance(monster.x, monster.y, player.x, player.y),
            "is_confused": self._is_confused(monster),
            "sight_range": getattr(monster, "sight_range", 8),
            "ai_state": self._monster_states.get(monster_id, MonsterAIState.WANDERING).value,
            "alert_timer": self._monster_alert_timers.get(monster_id, 0),
            "target_position": self._monster_target_positions.get(monster_id),
        }

    def set_monster_aggressive(self, monster: Monster, aggressive: bool = True) -> None:
        """
        モンスターの攻撃性を設定。

        Args:
        ----
            monster: 対象モンスター
            aggressive: 攻撃的にするかどうか

        """
        monster.aggressive = aggressive
        if aggressive:
            monster.sight_range = getattr(monster, "sight_range", 8) * 2
        else:
            monster.sight_range = getattr(monster, "sight_range", 8) // 2

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

        # プレイヤーの位置が変わった場合、視界キャッシュをクリア
        player_pos = (context.player.x, context.player.y)
        if player_pos != self._last_player_position:
            self._vision_cache.clear()
            self._pathfinding_cache.clear()  # 経路探索キャッシュもクリア
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

        プレイヤーの周囲一定範囲内のモンスターのみを返すことで、
        パフォーマンスを最適化します。

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
            distance = self._calculate_distance(monster.x, monster.y, player.x, player.y)

            # アクティブエリア内のモンスターのみ処理
            if distance <= active_radius:
                active_monsters.append(monster)

        game_logger.debug(f"Active monsters: {len(active_monsters)}/{len(monsters)}")
        return active_monsters

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

    # ========== 特殊AI行動パターンのメソッド ==========

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
        if not self._try_move_monster(monster, dx, dy, context):
            # 直線的に逃げられない場合はランダム移動
            self._random_move(monster, context)

    def _can_use_ranged_attack(self, monster: Monster, player) -> bool:
        """
        遠距離攻撃が使用可能かチェック。

        Args:
        ----
            monster: チェック対象のモンスター
            player: プレイヤー

        Returns:
        -------
            遠距離攻撃可能な場合True

        """
        if not hasattr(monster, "can_ranged_attack") or not monster.can_ranged_attack:
            return False

        if hasattr(monster, "special_ability_cooldown") and monster.special_ability_cooldown > 0:
            return False

        distance = self._calculate_distance(monster.x, monster.y, player.x, player.y)
        ranged_range = getattr(monster, "ranged_attack_range", 5)

        # 射程内かつ隣接していない場合
        return CombatConstants.ADJACENT_DISTANCE_THRESHOLD < distance <= ranged_range

    def _use_ranged_attack(self, monster: Monster, player, context: GameContext) -> None:
        """
        遠距離攻撃を実行。

        Args:
        ----
            monster: 攻撃するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        damage = getattr(monster, "ranged_attack_damage", monster.attack // 2)

        # 攻撃命中判定
        if random.random() < ProbabilityConstants.MONSTER_RANGED_ATTACK_HIT_RATE:  # 80%の命中率
            actual_damage = max(1, damage - player.get_defense())
            player.take_damage(actual_damage, context)
            context.add_message(f"{monster.name} shoots you for {actual_damage} damage!")
        else:
            context.add_message(f"{monster.name}'s ranged attack misses!")

        # クールダウン設定
        monster.special_ability_cooldown = 3

        game_logger.debug(f"{monster.name} used ranged attack on player")

    def _can_use_special_attack(self, monster: Monster) -> bool:
        """
        特殊攻撃が使用可能かチェック。

        Args:
        ----
            monster: チェック対象のモンスター

        Returns:
        -------
            特殊攻撃可能な場合True

        """
        if hasattr(monster, "special_ability_cooldown") and monster.special_ability_cooldown > 0:
            return False

        # 30%の確率で特殊攻撃を使用
        return random.random() < ProbabilityConstants.MONSTER_SPECIAL_ATTACK_CHANCE and (
            getattr(monster, "can_steal_items", False)
            or getattr(monster, "can_steal_gold", False)
            or getattr(monster, "can_drain_level", False)
        )

    def _use_special_attack(self, monster: Monster, player, context: GameContext) -> None:
        """
        特殊攻撃を実行。

        Args:
        ----
            monster: 攻撃するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        # アイテム盗取
        if getattr(monster, "can_steal_items", False):
            self._steal_item(monster, player, context)
        # ゴールド盗取
        elif getattr(monster, "can_steal_gold", False):
            self._steal_gold(monster, player, context)
        # レベル下げ攻撃
        elif getattr(monster, "can_drain_level", False):
            self._drain_level(monster, player, context)
        else:
            # 通常攻撃にフォールバック
            self._monster_attack_player(monster, context)

        # クールダウン設定
        monster.special_ability_cooldown = 5

    def _steal_item(self, monster: Monster, player, context: GameContext) -> None:
        """
        アイテム盗取攻撃。

        Args:
        ----
            monster: 攻撃するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        # インベントリからランダムなアイテムを盗む
        items = player.inventory.items
        if items:
            stolen_item = random.choice(items)

            # スタック可能アイテムの場合は1個だけ盗む
            if stolen_item.stackable and stolen_item.stack_count > 1:
                player.inventory.remove_item(stolen_item, 1)
                context.add_message(f"{monster.name} steals one {stolen_item.name}!")
                game_logger.debug(f"{monster.name} stole 1 {stolen_item.name} from player")
            else:
                player.inventory.remove_item(stolen_item)
                context.add_message(f"{monster.name} steals your {stolen_item.name}!")
                game_logger.debug(f"{monster.name} stole {stolen_item.name} from player")

            # モンスターが逃走を開始
            monster.is_fleeing = True
        else:
            context.add_message(f"{monster.name} tries to steal from you, but you have nothing!")

    def _steal_gold(self, monster: Monster, player, context: GameContext) -> None:
        """
        ゴールド盗取攻撃。

        Args:
        ----
            monster: 攻撃するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        if player.gold > 0:
            stolen_amount = min(player.gold, random.randint(10, 50))
            player.gold -= stolen_amount
            context.add_message(f"{monster.name} steals {stolen_amount} gold from you!")

            # モンスターが逃走を開始
            monster.is_fleeing = True

            game_logger.debug(f"{monster.name} stole {stolen_amount} gold from player")
        else:
            context.add_message(f"{monster.name} searches for gold, but you have none!")

    def _drain_level(self, monster: Monster, player, context: GameContext) -> None:
        """
        レベル下げ攻撃。

        Args:
        ----
            monster: 攻撃するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        if player.level > 1:
            # レベルを1下げる
            player.level -= 1

            # ステータスも減少
            player.max_hp = max(10, player.max_hp - 5)
            player.hp = min(player.hp, player.max_hp)
            # player.max_mp = max(5, player.max_mp - 3)
            # player.mp = min(player.mp, player.max_mp)
            player.attack = max(1, player.attack - 2)
            player.defense = max(0, player.defense - 1)

            context.add_message(f"{monster.name} drains your life force! You feel weaker!")
            game_logger.debug(f"{monster.name} drained player level from {player.level + 1} to {player.level}")
        else:
            # 通常ダメージを与える
            damage = max(1, monster.attack - player.get_defense())
            player.take_damage(damage, context)
            context.add_message(f"{monster.name} attacks you for {damage} damage!")

    def split_monster_on_damage(self, monster: Monster, context: GameContext) -> None:
        """
        ダメージを受けた時のモンスター分裂処理。

        Args:
        ----
            monster: 分裂するモンスター
            context: ゲームコンテキスト

        """
        if not getattr(monster, "can_split", False):
            return

        # 既に分裂している場合はスキップ
        if getattr(monster, "parent_monster", None) is not None:
            return

        # 分裂判定（30%の確率）
        if random.random() > ProbabilityConstants.MONSTER_SPLIT_CHANCE:
            return

        floor_data = context.get_current_floor_data()
        if not floor_data or not hasattr(floor_data, "monster_spawner"):
            return

        # 分裂先の座標を探す
        spawn_positions = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                new_x = monster.x + dx
                new_y = monster.y + dy

                if self._can_monster_move_to(new_x, new_y, context):
                    spawn_positions.append((new_x, new_y))

        if spawn_positions:
            # 分裂モンスターを作成
            spawn_x, spawn_y = random.choice(spawn_positions)

            # 元のモンスターの属性をコピーして分裂体を作成
            from pyrogue.entities.actors.monster import Monster as MonsterClass

            split_monster = MonsterClass(
                char=monster.char,
                x=spawn_x,
                y=spawn_y,
                name=f"{monster.name} (split)",
                level=monster.level,
                hp=monster.hp // 2,  # HPは半分
                max_hp=monster.max_hp // 2,
                attack=monster.attack,
                defense=monster.defense,
                exp_value=monster.exp_value // 2,  # 経験値も半分
                view_range=monster.view_range,
                color=monster.color,
                ai_pattern=monster.ai_pattern,
            )

            # 親子関係を設定
            split_monster.parent_monster = monster
            monster.split_children.append(split_monster)

            # 元のモンスターのHPも半分に
            monster.hp = monster.hp // 2
            monster.max_hp = monster.max_hp // 2

            # スポナーに追加
            floor_data.monster_spawner.monsters.append(split_monster)
            floor_data.monster_spawner.occupied_positions.add((spawn_x, spawn_y))

            context.add_message(f"{monster.name} splits into two!")
            game_logger.debug(f"{monster.name} split into two monsters")
