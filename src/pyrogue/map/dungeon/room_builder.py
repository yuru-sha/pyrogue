"""Room data shared by the remaining legacy dungeon components."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Room:
    x: int
    y: int
    width: int
    height: int
    connected_rooms: set[int] | None = None
    doors: list[tuple[int, int]] | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if self.connected_rooms is None:
            self.connected_rooms = set()
        if self.doors is None:
            self.doors = []

    def center(self) -> tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2

    def is_connected_to(self, other_room: Room) -> bool:
        return bool(other_room.id and self.connected_rooms and other_room.id in self.connected_rooms)

    def add_connection(self, other_room: Room) -> None:
        if other_room.id and self.connected_rooms is not None and other_room.connected_rooms is not None:
            self.connected_rooms.add(other_room.id)
            other_room.connected_rooms.add(self.id)

    def add_door(self, x: int, y: int) -> None:
        if self.doors is not None:
            self.doors.append((x, y))

    @property
    def inner(self) -> list[tuple[int, int]]:
        return [
            (x, y)
            for y in range(self.y + 1, self.y + self.height - 1)
            for x in range(self.x + 1, self.x + self.width - 1)
        ]
