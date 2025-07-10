"""
モンスターAI管理コンポーネント。

このモジュールは、GameLogicから分離されたモンスターAIシステムを担当します。
モンスターの行動決定、プレイヤー追跡、ランダム移動、視界判定を管理します。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from pyrogue.constants import ProbabilityConstants
from pyrogue.utils import game_logger

if TYPE_CHECKING:
    from pyrogue.core.managers.game_context import GameContext
    from pyrogue.entities.actors.monster import Monster


class MonsterAIManager:
    """
    モンスターAIシステムの管理クラス。

    モンスターの行動決定、プレイヤー追跡、
    ランダム移動、視界判定を担当します。
    """

    def __init__(self) -> None:
        """モンスターAIマネージャーを初期化。"""

    def process_monster_ai(self, monster: Monster, context: GameContext) -> None:
        """
        モンスターのAI処理を実行。

        Args:
            monster: 処理するモンスター
            context: ゲームコンテキスト

        """
        player = context.player

        # モンスターが行動可能かチェック
        if not self._can_monster_act(monster):
            return

        # プレイヤーが見えるかチェック
        if self._can_monster_see_player(monster, player, context):
            # プレイヤーを追跡
            self._chase_player(monster, player, context)
        # ランダム移動
        elif random.random() < ProbabilityConstants.MONSTER_MOVE_CHANCE:
            self._random_move(monster, context)

    def _can_monster_act(self, monster: Monster) -> bool:
        """
        モンスターが行動可能かチェック。

        Args:
            monster: チェック対象のモンスター

        Returns:
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
            monster: モンスター
            player: プレイヤー
            context: ゲームコンテキスト

        Returns:
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
            x1, y1: 点1の座標
            x2, y2: 点2の座標

        Returns:
            ユークリッド距離

        """
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def _has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int, context: GameContext) -> bool:
        """
        2点間に視界があるかチェック。

        Args:
            x1, y1: 開始点の座標
            x2, y2: 終了点の座標
            context: ゲームコンテキスト

        Returns:
            視界がある場合True

        """
        floor_data = context.get_current_floor_data()
        if not floor_data:
            return False

        # ブレゼンハム線分アルゴリズムで視界チェック
        points = self._get_line_points(x1, y1, x2, y2)

        for x, y in points[1:-1]:  # 開始点と終了点は除外
            if (0 <= y < floor_data.tiles.shape[0] and
                0 <= x < floor_data.tiles.shape[1]):

                tile = floor_data.tiles[y, x]
                if not getattr(tile, "transparent", True):
                    return False

        return True

    def _get_line_points(self, x1: int, y1: int, x2: int, y2: int) -> list[tuple[int, int]]:
        """
        ブレゼンハム線分アルゴリズムで線上の点を取得。

        Args:
            x1, y1: 開始点の座標
            x2, y2: 終了点の座標

        Returns:
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
            monster: 追跡するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        # プレイヤーとの距離が1の場合は攻撃
        if self._calculate_distance(monster.x, monster.y, player.x, player.y) <= 1.5:
            self._monster_attack_player(monster, context)
            return

        # プレイヤーに向かって移動
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

        # 混乱状態の場合はランダム方向
        if self._is_confused(monster):
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)

        # 移動実行
        self._try_move_monster(monster, dx, dy, context)

    def _random_move(self, monster: Monster, context: GameContext) -> None:
        """
        モンスターがランダムに移動。

        Args:
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
            monster: 移動するモンスター
            dx: X方向の移動量
            dy: Y方向の移動量
            context: ゲームコンテキスト

        Returns:
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
            x: 目標X座標
            y: 目標Y座標
            context: ゲームコンテキスト

        Returns:
            移動可能な場合True

        """
        floor_data = context.get_current_floor_data()
        if not floor_data:
            return False

        # 境界チェック
        if (x < 0 or y < 0 or
            y >= floor_data.tiles.shape[0] or
            x >= floor_data.tiles.shape[1]):
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
            monster: チェック対象のモンスター

        Returns:
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
            monster: 対象モンスター
            context: ゲームコンテキスト

        Returns:
            行動情報辞書

        """
        player = context.player

        return {
            "can_act": self._can_monster_act(monster),
            "can_see_player": self._can_monster_see_player(monster, player, context),
            "distance_to_player": self._calculate_distance(monster.x, monster.y, player.x, player.y),
            "is_confused": self._is_confused(monster),
            "sight_range": getattr(monster, "sight_range", 8),
        }

    def set_monster_aggressive(self, monster: Monster, aggressive: bool = True) -> None:
        """
        モンスターの攻撃性を設定。

        Args:
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
            context: ゲームコンテキスト

        """
        floor_data = context.get_current_floor_data()
        if not floor_data or not hasattr(floor_data, "monster_spawner"):
            return

        # モンスターリストをコピー（処理中の変更に対応）
        monsters = floor_data.monster_spawner.monsters.copy()

        for monster in monsters:
            if monster.hp > 0:  # 生きているモンスターのみ処理
                self.process_monster_ai(monster, context)
