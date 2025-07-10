"""
モンスターモジュール。

このモジュールは、ゲーム内のモンスターエンティティと
関連機能を定義します。モンスターのステータス、AI行動、
戦闘システムを統合的に管理します。
"""

from __future__ import annotations

import random
from typing import Any

from pyrogue.entities.actors.actor import Actor
from pyrogue.entities.actors.status_effects import StatusEffectManager


class Monster(Actor):
    """
    モンスターの基本クラス。

    ダンジョン内の敵モンスターを表現し、ステータス管理、
    移動、戦闘、AI行動などの機能を提供します。

    Attributes:
        char: 表示文字（A-Z）
        exp_value: 倒した時の経験値
        view_range: 視界範囲
        color: 表示色（RGB）

    """

    def __init__(self, char: str, x: int, y: int, name: str, level: int,
                 hp: int, max_hp: int, attack: int, defense: int, exp_value: int,
                 view_range: int, color: tuple[int, int, int], is_hostile: bool = True,
                 ai_pattern: str = "basic") -> None:
        """
        モンスターの初期化。

        Args:
            char: 表示文字（A-Z）
            x: モンスターのX座標
            y: モンスターのY座標
            name: モンスター名
            level: モンスターレベル
            hp: 現在のHP
            max_hp: 最大HP
            attack: 攻撃力
            defense: 防御力
            exp_value: 倒した時の経験値
            view_range: 視界範囲
            color: 表示色（RGB）
            is_hostile: 敵対的かどうか
            ai_pattern: AIパターン（basic, thief, drain, split, ranged, flee等）

        """
        super().__init__(x, y, name, hp, max_hp, attack, defense, level, is_hostile)

        # Monster固有の属性
        self.char = char
        self.exp_value = exp_value
        self.view_range = view_range
        self.color = color

        # AI行動パターン
        self.ai_pattern = ai_pattern

        # AI特殊能力用の属性
        self.can_steal_items = ai_pattern in ["item_thief", "leprechaun"]
        self.can_steal_gold = ai_pattern in ["gold_thief", "nymph"]
        self.can_drain_level = ai_pattern in ["level_drain", "wraith"]
        self.can_split = ai_pattern in ["split", "split_on_hit"]
        self.can_ranged_attack = ai_pattern in ["ranged", "archer"]
        self.can_flee = ai_pattern in ["flee", "coward"]

        # 特殊能力のクールダウン
        self.special_ability_cooldown = 0

        # 分裂モンスター用の属性
        self.parent_monster = None
        self.split_children = []

        # 逃走モンスター用の属性
        self.flee_threshold = 0.3  # HP30%以下で逃走
        self.is_fleeing = False

        # 遠距離攻撃モンスター用の属性
        self.ranged_attack_range = 5
        self.ranged_attack_damage = self.attack // 2

        # システムの初期化
        self.status_effects = StatusEffectManager()

    # move, take_damage, is_dead, heal は基底クラスから継承

    def can_see_player(self, player_x: int, player_y: int, fov_map: Any) -> bool:
        """
        プレイヤーが視界内にいるかチェック。

        Args:
            player_x: プレイヤーのX座標
            player_y: プレイヤーのY座標
            fov_map: FOVマップオブジェクト

        Returns:
            視界内にプレイヤーがいる場合True

        """
        # 基底クラスの距離計算メソッドを使用
        distance = self.get_distance_to(player_x, player_y)

        # 視界範囲内かつ、壁などで視線が遮られていないか確認
        return distance <= self.view_range and fov_map.transparent[player_y, player_x]

    def get_move_towards_player(self, player_x: int, player_y: int) -> tuple[int, int]:
        """
        プレイヤーに向かう移動方向を計算。

        プレイヤーの位置との距離を計算し、8方向の移動を許可して
        最適な移動方向を決定します。斜め移動も含まれます。

        Args:
            player_x: プレイヤーのX座標
            player_y: プレイヤーのY座標

        Returns:
            (dx, dy)形式の移動方向ベクトル

        """
        dx = player_x - self.x
        dy = player_y - self.y

        # 斜め移動を含む8方向の移動を許可
        if dx != 0:
            dx = dx // abs(dx)
        if dy != 0:
            dy = dy // abs(dy)

        return dx, dy

    def get_random_move(self) -> tuple[int, int]:
        """
        ランダムな移動方向を取得。

        8方向（上下左右＋斜め4方向）からランダムに1つを選択して
        移動方向を返します。待機する場合は(0,0)を返すことも可能です。

        Returns:
            (dx, dy)形式のランダムな移動方向ベクトル

        """
        # 8方向のいずれかにランダムに移動
        directions = [
            (-1, -1),
            (0, -1),
            (1, -1),
            (-1, 0),
            (1, 0),
            (-1, 1),
            (0, 1),
            (1, 1),
        ]
        return random.choice(directions)  # noqa: S311

    def update_status_effects(self, context) -> None:
        """
        状態異常のターン経過処理。

        すべての状態異常の効果を適用し、継続ターン数を更新します。
        効果が切れた状態異常は自動的に削除されます。

        Args:
            context: 効果適用のためのコンテキスト

        """
        self.status_effects.update_effects(context)

    def has_status_effect(self, name: str) -> bool:
        """
        指定された状態異常があるかどうかを判定。

        Args:
            name: 判定する状態異常の名前

        Returns:
            状態異常が存在する場合はTrue、そうでなければFalse

        """
        return self.status_effects.has_effect(name)

    def is_paralyzed(self) -> bool:
        """麻痺状態かどうかを判定。"""
        return self.has_status_effect("Paralysis")

    def is_confused(self) -> bool:
        """混乱状態かどうかを判定。"""
        return self.has_status_effect("Confusion")

    def is_poisoned(self) -> bool:
        """毒状態かどうかを判定。"""
        return self.has_status_effect("Poison")
