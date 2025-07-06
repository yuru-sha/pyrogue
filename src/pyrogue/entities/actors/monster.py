"""
モンスターモジュール。

このモジュールは、ゲーム内のモンスターエンティティと
関連機能を定義します。モンスターのステータス、AI行動、
戦闘システムを統合的に管理します。
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from pyrogue.entities.actors.status_effects import StatusEffectManager


@dataclass
class Monster:
    """
    モンスターの基本クラス。

    ダンジョン内の敵モンスターを表現し、ステータス管理、
    移動、戦闘、AI行動などの機能を提供します。

    Attributes:
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

    """

    char: str  # 表示文字（A-Z）
    x: int
    y: int
    name: str
    level: int
    hp: int
    max_hp: int
    attack: int
    defense: int
    exp_value: int  # 倒した時の経験値
    view_range: int  # 視界範囲
    color: tuple[int, int, int]  # 表示色
    is_hostile: bool = True  # 敵対的かどうか

    def __post_init__(self) -> None:
        """データクラスの初期化後に実行される処理。"""
        self.status_effects = StatusEffectManager()

    def move(self, dx: int, dy: int) -> None:
        """
        指定した方向にモンスターを移動。

        Args:
            dx: X軸方向の移動量
            dy: Y軸方向の移動量

        """
        self.x += dx
        self.y += dy

    def take_damage(self, amount: int) -> None:
        """
        ダメージを受けてHPを減少。

        Args:
            amount: 受けるダメージ量

        """
        self.hp = max(0, self.hp - max(0, amount - self.defense))

    def is_dead(self) -> bool:
        """
        モンスターが死亡しているかチェック。

        Returns:
            HPが0以下の場合True

        """
        return self.hp <= 0

    def heal(self, amount: int) -> None:
        """
        HPを回復。

        Args:
            amount: 回復するHP量

        """
        self.hp = min(self.max_hp, self.hp + amount)

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
        # モンスターからプレイヤーまでのユークリッド距離を計算
        distance = ((self.x - player_x) ** 2 + (self.y - player_y) ** 2) ** 0.5

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
