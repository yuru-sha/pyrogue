"""通路データ型。"""

from dataclasses import dataclass


@dataclass
class Corridor:
    """通路を表すデータクラス。"""

    start_pos: tuple[int, int]
    end_pos: tuple[int, int]
    points: list[tuple[int, int]]
    connecting_rooms: tuple[int, int] | None = None
