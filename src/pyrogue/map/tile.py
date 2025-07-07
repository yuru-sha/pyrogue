"""Tile module."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Tile:
    """タイルの基底クラス"""

    walkable: bool
    transparent: bool
    dark: tuple[int, int, int]  # RGB color when not in FOV
    light: tuple[int, int, int]  # RGB color when in FOV
    char: str


class Floor(Tile):
    """床タイル"""

    def __init__(
        self,
        has_gold: bool = False,
        has_potion: bool = False,
        has_scroll: bool = False,
        has_weapon: bool = False,
        has_armor: bool = False,
        has_ring: bool = False,
        has_food: bool = False,
        has_amulet: bool = False,
    ) -> None:
        super().__init__(
            walkable=True,
            transparent=True,
            dark=(64, 64, 64),
            light=(192, 192, 192),
            char=".",
        )
        self.has_gold = has_gold
        self.has_potion = has_potion
        self.has_scroll = has_scroll
        self.has_weapon = has_weapon
        self.has_armor = has_armor
        self.has_ring = has_ring
        self.has_food = has_food
        self.has_amulet = has_amulet

    @property
    def has_item(self) -> bool:
        """アイテムを持っているかどうか"""
        return any(
            [
                self.has_gold,
                self.has_potion,
                self.has_scroll,
                self.has_weapon,
                self.has_armor,
                self.has_ring,
                self.has_food,
                self.has_amulet,
            ]
        )

    @property
    def item_char(self) -> str:
        """アイテムの表示文字を返す"""
        if self.has_gold:
            return "$"
        if self.has_potion:
            return "!"
        if self.has_scroll:
            return "?"
        if self.has_weapon:
            return ")"
        if self.has_armor:
            return "["
        if self.has_ring:
            return "="
        if self.has_food:
            return "%"
        if self.has_amulet:
            return "&"
        return "."


class Wall(Tile):
    """壁タイル"""

    def __init__(self) -> None:
        super().__init__(
            walkable=False,
            transparent=False,
            dark=(0, 0, 100),
            light=(130, 110, 50),
            char="#",
        )


class Door(Tile):
    """扉タイル"""

    def __init__(self, state: str = "closed") -> None:
        super().__init__(
            walkable=False,
            transparent=False,
            dark=(139, 69, 19),
            light=(139, 69, 19),
            char="+",
        )
        self.door_state = state
        self._update_state()

    def _update_state(self) -> None:
        """扉の状態に応じてタイルの属性を更新"""
        if self.door_state == "open":
            self.walkable = True
            self.transparent = True
            self.char = "/"
        else:
            self.walkable = False
            self.transparent = False
            self.char = "+"

    def toggle(self) -> None:
        """扉の開閉を切り替える"""
        self.door_state = "open" if self.door_state == "closed" else "closed"
        self._update_state()


class SecretDoor(Door):
    """隠し扉タイル"""

    def __init__(self) -> None:
        super().__init__(state="secret")
        self.char = "#"  # 未発見時は壁として表示
        self.walkable = False
        self.transparent = False
        # 未発見時は通常の壁と同じ色にする
        self.dark = (0, 0, 100)
        self.light = (130, 110, 50)

    def reveal(self) -> None:
        """隠し扉を発見する"""
        self.door_state = "closed"
        self.char = "+"
        # 発見時はドアの色に変更
        self.dark = (139, 69, 19)
        self.light = (139, 69, 19)


class Stairs(Tile):
    """階段の基底クラス"""

    def __init__(self, char: str) -> None:
        super().__init__(
            walkable=True,
            transparent=True,
            dark=(128, 128, 128),  # 暗い場所での色
            light=(200, 200, 200),  # 明るい場所での色
            char=char,
        )


class StairsUp(Stairs):
    """上り階段"""

    def __init__(self) -> None:
        super().__init__(char="<")


class StairsDown(Stairs):
    """下り階段"""

    def __init__(self) -> None:
        super().__init__(char=">")


class Water(Tile):
    """水タイル"""

    def __init__(self) -> None:
        super().__init__(
            walkable=False,
            transparent=True,
            dark=(0, 32, 64),
            light=(0, 128, 255),
            char="~",
        )


class Lava(Tile):
    """溶岩タイル"""

    def __init__(self) -> None:
        super().__init__(
            walkable=False,
            transparent=True,
            dark=(64, 16, 0),
            light=(255, 64, 0),
            char="^",
        )
