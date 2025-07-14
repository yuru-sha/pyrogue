"""
Actor基底クラス。

このモジュールは、Player、Monster、NPCの共通基底クラスを定義します。
移動、ダメージ処理、状態異常管理などの共通機能を提供します。
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Actor(ABC):
    """
    Player、Monster、NPCの共通基底クラス。

    すべてのアクターが持つ基本的な属性と機能を定義します。
    位置、HP、基本ステータス、移動、ダメージ処理、状態異常管理など
    の共通機能を提供します。

    Attributes
    ----------
        x: アクターのX座標
        y: アクターのY座標
        name: アクターの名前
        hp: 現在のHP
        max_hp: 最大HP
        attack: 基本攻撃力
        defense: 基本防御力
        level: レベル
        is_hostile: 敵対的かどうか

    """

    def __init__(
        self,
        x: int,
        y: int,
        name: str,
        hp: int,
        max_hp: int,
        attack: int,
        defense: int,
        level: int,
        is_hostile: bool = True,
    ) -> None:
        """
        アクターの初期化。

        Args:
        ----
            x: アクターのX座標
            y: アクターのY座標
            name: アクターの名前
            hp: 現在のHP
            max_hp: 最大HP
            attack: 基本攻撃力
            defense: 基本防御力
            level: レベル
            is_hostile: 敵対的かどうか

        """
        self.x = x
        self.y = y
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.attack = attack
        self.defense = defense
        self.level = level
        self.is_hostile = is_hostile

    def move(self, dx: int, dy: int) -> None:
        """
        指定した方向にアクターを移動。

        Args:
        ----
            dx: X軸方向の移動量
            dy: Y軸方向の移動量

        """
        self.x += dx
        self.y += dy

    def take_damage(self, amount: int) -> None:
        """
        ダメージを受けてHPを減少。

        防御力を考慮した実ダメージを計算し、HPから差し引きます。
        HPは0未満にはなりません。

        Args:
        ----
            amount: 受けるダメージ量

        """
        self.hp = max(0, self.hp - max(0, amount - self.defense))

    def heal(self, amount: int) -> None:
        """
        HPを回復。

        指定された量だけHPを回復します。最大HPを超えて回復することはありません。

        Args:
        ----
            amount: 回復するHP量

        """
        self.hp = min(self.max_hp, self.hp + amount)

    def is_dead(self) -> bool:
        """
        アクターが死亡しているかチェック。

        Returns
        -------
            HPが0以下の場合True

        """
        return self.hp <= 0

    @property
    def is_alive(self) -> bool:
        """
        アクターが生存しているかどうかを返す。

        Returns
        -------
            生存している場合True、死亡している場合False

        """
        return not self.is_dead()

    def get_distance_to(self, x: int, y: int) -> float:
        """
        指定した座標までの距離を計算。

        Args:
        ----
            x: 目標のX座標
            y: 目標のY座標

        Returns:
        -------
            ユークリッド距離

        """
        return ((self.x - x) ** 2 + (self.y - y) ** 2) ** 0.5

    @abstractmethod
    def update_status_effects(self, context) -> None:
        """
        状態異常のターン経過処理。

        サブクラスで実装してください。

        Args:
        ----
            context: 効果適用のためのコンテキスト

        """

    @abstractmethod
    def has_status_effect(self, name: str) -> bool:
        """
        指定された状態異常があるかどうかを判定。

        サブクラスで実装してください。

        Args:
        ----
            name: 判定する状態異常の名前

        Returns:
        -------
            状態異常が存在する場合はTrue、そうでなければFalse

        """

    def is_paralyzed(self) -> bool:
        """麻痺状態かどうかを判定。"""
        return self.has_status_effect("Paralysis")

    def is_confused(self) -> bool:
        """混乱状態かどうかを判定。"""
        return self.has_status_effect("Confusion")

    def is_poisoned(self) -> bool:
        """毒状態かどうかを判定。"""
        return self.has_status_effect("Poison")
