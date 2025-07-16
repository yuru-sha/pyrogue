"""
アイテムの基底クラス。

すべてのアイテムが継承する基本的な属性と機能を定義します。
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass


@dataclass
class BaseItem(ABC):
    """
    すべてのアイテムの基底クラス。

    アイテムの基本的な属性（名前、説明、重量、価値など）を定義します。
    """

    name: str
    description: str
    weight: int = 1
    value: int = 0
    stackable: bool = False
    max_stack: int = 1

    def __post_init__(self) -> None:
        """初期化後の処理。"""
        if self.stackable and self.max_stack <= 1:
            self.max_stack = 99  # デフォルトのスタック数

    def get_display_name(self) -> str:
        """表示用の名前を取得。"""
        return self.name

    def get_description(self) -> str:
        """説明を取得。"""
        return self.description

    def get_weight(self) -> int:
        """重量を取得。"""
        return self.weight

    def get_value(self) -> int:
        """価値を取得。"""
        return self.value

    def can_stack_with(self, other: BaseItem) -> bool:
        """
        他のアイテムとスタック可能かチェック。

        Args:
        ----
            other: 比較対象のアイテム

        Returns:
        -------
            スタック可能な場合True

        """
        return self.stackable and other.stackable and self.name == other.name and type(self) == type(other)

    def is_stackable(self) -> bool:
        """スタック可能かチェック。"""
        return self.stackable
