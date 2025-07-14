"""
光源アイテムシステム。

暗い部屋で視界を確保するためのアイテム（たいまつ、光る指輪など）を実装。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pyrogue.entities.items.base_item import BaseItem
from pyrogue.utils import game_logger


@dataclass
class LightSource(ABC):
    """
    光源の基底クラス。

    光源アイテムが提供する光の特性を定義する。
    """

    name: str
    light_radius: int
    duration: int  # 使用可能時間（ターン数、-1は無限）
    intensity: float  # 光の強度（0.0-1.0）

    @abstractmethod
    def use_light(self) -> bool:
        """
        光源を使用。

        Returns
        -------
            使用可能な場合True
        """

    @abstractmethod
    def is_depleted(self) -> bool:
        """
        光源が使い切られているかチェック。

        Returns
        -------
            使い切られている場合True
        """


class Torch(BaseItem, LightSource):
    """
    たいまつクラス。

    一定時間光を提供する使い捨ての光源。
    """

    def __init__(self, duration: int = 200) -> None:
        """
        たいまつを初期化。

        Args:
        ----
            duration: 燃焼時間（ターン数）
        """
        BaseItem.__init__(
            self,
            name="Torch",
            description="A wooden torch that provides light for a limited time",
            weight=3,
            value=10,
            stackable=True,
            max_stack=5,
        )

        LightSource.__init__(self, name="Torch", light_radius=4, duration=duration, intensity=0.8)

        self.remaining_duration = duration
        self.is_lit = False

    def use_light(self) -> bool:
        """たいまつを点灯。"""
        if self.remaining_duration > 0:
            self.is_lit = True
            return True
        return False

    def is_depleted(self) -> bool:
        """燃料が切れているかチェック。"""
        return self.remaining_duration <= 0

    def consume_fuel(self, turns: int = 1) -> None:
        """
        燃料を消費。

        Args:
        ----
            turns: 消費するターン数
        """
        if self.is_lit:
            self.remaining_duration = max(0, self.remaining_duration - turns)
            if self.remaining_duration <= 0:
                self.is_lit = False
                game_logger.info("Your torch burns out!")

    def get_light_radius(self) -> int:
        """現在の光の範囲を取得。"""
        if self.is_lit and not self.is_depleted():
            return self.light_radius
        return 0


class Lantern(BaseItem, LightSource):
    """
    ランタンクラス。

    より長時間光を提供する高級な光源。
    """

    def __init__(self, duration: int = 500) -> None:
        """
        ランタンを初期化。

        Args:
        ----
            duration: 燃料持続時間（ターン数）
        """
        BaseItem.__init__(
            self,
            name="Lantern",
            description="A reliable lantern that provides bright light",
            weight=5,
            value=50,
            stackable=False,
        )

        LightSource.__init__(self, name="Lantern", light_radius=6, duration=duration, intensity=1.0)

        self.remaining_duration = duration
        self.is_lit = False

    def use_light(self) -> bool:
        """ランタンを点灯。"""
        if self.remaining_duration > 0:
            self.is_lit = True
            return True
        return False

    def is_depleted(self) -> bool:
        """燃料が切れているかチェック。"""
        return self.remaining_duration <= 0

    def consume_fuel(self, turns: int = 1) -> None:
        """
        燃料を消費。

        Args:
        ----
            turns: 消費するターン数
        """
        if self.is_lit:
            self.remaining_duration = max(0, self.remaining_duration - turns)
            if self.remaining_duration <= 0:
                self.is_lit = False
                game_logger.info("Your lantern runs out of fuel!")

    def get_light_radius(self) -> int:
        """現在の光の範囲を取得。"""
        if self.is_lit and not self.is_depleted():
            return self.light_radius
        return 0


class LightRing(BaseItem, LightSource):
    """
    光る指輪クラス。

    装備すると常時光を提供する魔法のアイテム。
    """

    def __init__(self, light_radius: int = 3) -> None:
        """
        光る指輪を初期化。

        Args:
        ----
            light_radius: 光の範囲
        """
        BaseItem.__init__(
            self,
            name="Ring of Light",
            description="A magical ring that glows with eternal light",
            weight=1,
            value=200,
            stackable=False,
        )

        LightSource.__init__(
            self,
            name="Ring of Light",
            light_radius=light_radius,
            duration=-1,  # 無限
            intensity=0.6,
        )

        self.is_equipped = False

    def use_light(self) -> bool:
        """光る指輪を装備。"""
        self.is_equipped = True
        return True

    def is_depleted(self) -> bool:
        """魔法の指輪は使い切られない。"""
        return False

    def get_light_radius(self) -> int:
        """現在の光の範囲を取得。"""
        if self.is_equipped:
            return self.light_radius
        return 0


class LightManager:
    """
    光源管理システム。

    プレイヤーの光源アイテムを管理し、暗い部屋での視界を制御する。
    """

    def __init__(self) -> None:
        """光源マネージャーを初期化。"""
        self.active_light_sources: list[LightSource] = []

    def add_light_source(self, light_source: LightSource) -> None:
        """
        光源を追加。

        Args:
        ----
            light_source: 追加する光源
        """
        if light_source not in self.active_light_sources:
            self.active_light_sources.append(light_source)
            game_logger.debug(f"Added light source: {light_source.name}")

    def remove_light_source(self, light_source: LightSource) -> None:
        """
        光源を削除。

        Args:
        ----
            light_source: 削除する光源
        """
        if light_source in self.active_light_sources:
            self.active_light_sources.remove(light_source)
            game_logger.debug(f"Removed light source: {light_source.name}")

    def get_total_light_radius(self) -> int:
        """
        すべての光源の合計光量を取得。

        Returns
        -------
            合計光の範囲
        """
        max_radius = 0

        for light_source in self.active_light_sources:
            if hasattr(light_source, "get_light_radius"):
                radius = light_source.get_light_radius()
                max_radius = max(max_radius, radius)

        return max_radius

    def has_active_light(self) -> bool:
        """
        有効な光源があるかチェック。

        Returns
        -------
            有効な光源がある場合True
        """
        return self.get_total_light_radius() > 0

    def consume_fuel(self, turns: int = 1) -> None:
        """
        すべての光源の燃料を消費。

        Args:
        ----
            turns: 消費するターン数
        """
        depleted_sources = []

        for light_source in self.active_light_sources:
            if hasattr(light_source, "consume_fuel"):
                light_source.consume_fuel(turns)

                if light_source.is_depleted():
                    depleted_sources.append(light_source)

        # 使い切られた光源を削除
        for depleted_source in depleted_sources:
            self.remove_light_source(depleted_source)

    def get_light_intensity(self) -> float:
        """
        現在の光の強度を取得。

        Returns
        -------
            光の強度（0.0-1.0）
        """
        max_intensity = 0.0

        for light_source in self.active_light_sources:
            if hasattr(light_source, "get_light_radius") and light_source.get_light_radius() > 0:
                max_intensity = max(max_intensity, light_source.intensity)

        return max_intensity

    def get_statistics(self) -> dict:
        """光源の統計情報を取得。"""
        return {
            "active_sources": len(self.active_light_sources),
            "total_light_radius": self.get_total_light_radius(),
            "light_intensity": self.get_light_intensity(),
            "has_light": self.has_active_light(),
            "light_sources": [source.name for source in self.active_light_sources],
        }
