"""
ダンジョン構築コンポーネント - 複雑な生成ロジックを分解するための個別クラス。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from pyrogue.map.tile import Door, Floor, SecretDoor, Wall

if TYPE_CHECKING:
    from pyrogue.map.dungeon import DungeonGenerator, Room


class RoomConnector:
    """部屋間の通路接続を処理。"""

    def __init__(self, generator: DungeonGenerator):
        self.generator = generator

    def connect_rooms_rogue_style(self) -> None:
        """Connect rooms using original Rogue-style algorithm."""
        # Initialize with starting room
        if self.generator.rooms:
            start_room = self.generator.rooms[0]
            start_pos = self.generator._get_room_grid_position(start_room)
            if start_pos:
                self.generator.connected_rooms.add(start_pos)

        # Connect rooms until all are connected
        while len(self.generator.connected_rooms) < len(self.generator.rooms):
            if not self._connect_adjacent_rooms():
                self._connect_distant_rooms()

    def _connect_adjacent_rooms(self) -> bool:
        """Try to connect adjacent rooms to already connected ones."""
        for connected_pos in list(self.generator.connected_rooms):
            neighbors = self.generator._get_adjacent_grid_positions(connected_pos)

            for neighbor_pos in neighbors:
                if neighbor_pos not in self.generator.connected_rooms:
                    if self._connect_to_neighbor(connected_pos, neighbor_pos):
                        return True
        return False

    def _connect_to_neighbor(self, connected_pos: tuple[int, int], neighbor_pos: tuple[int, int]) -> bool:
        """Connect to a specific neighbor position."""
        if neighbor_pos in self.generator.gone_rooms:
            self.generator._create_gone_room_corridor(connected_pos, neighbor_pos)
        else:
            neighbor_room = self.generator.room_grid[neighbor_pos[1]][neighbor_pos[0]]
            if neighbor_room:
                self.generator._create_corridor_between_grid_cells(connected_pos, neighbor_pos)
                self._record_room_connection(connected_pos, neighbor_pos)

        self.generator.connected_rooms.add(neighbor_pos)
        return True

    def _connect_distant_rooms(self) -> None:
        """Connect to distant rooms when no adjacent rooms are available."""
        unconnected_rooms = self._find_unconnected_rooms()

        if unconnected_rooms:
            target_pos = random.choice(unconnected_rooms)
            closest_connected = self._find_closest_connected_room(target_pos)

            self.generator._create_corridor_between_grid_cells(closest_connected, target_pos)
            self._record_room_connection(closest_connected, target_pos)
            self.generator.connected_rooms.add(target_pos)

    def _find_unconnected_rooms(self) -> list[tuple[int, int]]:
        """Find all unconnected room positions."""
        unconnected = []
        for y in range(self.generator.grid_height):
            for x in range(self.generator.grid_width):
                if (x, y) not in self.generator.connected_rooms:
                    if (x, y) not in self.generator.gone_rooms and self.generator.room_grid[y][x]:
                        unconnected.append((x, y))
        return unconnected

    def _find_closest_connected_room(self, target_pos: tuple[int, int]) -> tuple[int, int]:
        """Find the closest connected room to the target position."""
        return min(
            self.generator.connected_rooms,
            key=lambda pos: abs(pos[0] - target_pos[0]) + abs(pos[1] - target_pos[1])
        )

    def _record_room_connection(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> None:
        """Record the connection between two rooms."""
        room1 = self.generator.room_grid[pos1[1]][pos1[0]]
        room2 = self.generator.room_grid[pos2[1]][pos2[0]]

        if room1 and room2:
            room1.connected_rooms.add(room2.id)
            room2.connected_rooms.add(room1.id)


class CorridorBuilder:
    """部屋間の通路作成を処理。"""

    def __init__(self, generator: DungeonGenerator):
        self.generator = generator

    def create_corridor_between_grid_cells(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> None:
        """Create corridor between two grid cells using original Rogue style."""
        x1, y1 = pos1
        x2, y2 = pos2

        # Calculate center points of grid cells
        center1_x = x1 * self.generator.cell_width + self.generator.cell_width // 2
        center1_y = y1 * self.generator.cell_height + self.generator.cell_height // 2
        center2_x = x2 * self.generator.cell_width + self.generator.cell_width // 2
        center2_y = y2 * self.generator.cell_height + self.generator.cell_height // 2

        # Create L-shaped corridor
        if random.random() < 0.5:
            # Horizontal then vertical
            self._create_line(center1_x, center1_y, center2_x, center1_y)
            self._create_line(center2_x, center1_y, center2_x, center2_y)
        else:
            # Vertical then horizontal
            self._create_line(center1_x, center1_y, center1_x, center2_y)
            self._create_line(center1_x, center2_y, center2_x, center2_y)

    def _create_line(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Create a line between two points with door placement."""
        if x1 == x2:  # Vertical line
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= x1 < self.generator.width and 0 <= y < self.generator.height:
                    self._place_corridor_tile(x1, y)
        else:  # Horizontal line
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= x < self.generator.width and 0 <= y1 < self.generator.height:
                    self._place_corridor_tile(x, y1)

    def _place_corridor_tile(self, x: int, y: int) -> None:
        """Place appropriate tile (door or floor) at corridor position."""
        current_tile = self.generator.tiles[y, x]

        if isinstance(current_tile, Wall):
            if self.generator._is_room_wall(x, y):
                self._place_door(x, y)
            else:
                self.generator.tiles[y, x] = Floor()
                self.generator.corridors.add((x, y))

    def _place_door(self, x: int, y: int) -> None:
        """Place door at room wall position."""
        room = self.generator._find_room_at_wall(x, y)

        if room and room.is_special:
            door = Door()
        else:
            door = SecretDoor() if random.random() < 0.15 else Door()

        self.generator.tiles[y, x] = door

        if room:
            room.doors.append((x, y))


class StairsManager:
    """ダンジョン内の階段配置を管理。"""

    def __init__(self, generator: DungeonGenerator):
        self.generator = generator

    def place_stairs(self) -> None:
        """Place up and down stairs in appropriate rooms."""
        if not self.generator.rooms:
            return

        # Place up stairs in first room (if not on floor 1)
        if self.generator.floor > 1:
            self._place_up_stairs()
        else:
            # For floor 1, set start position to an empty floor tile in first room
            self._set_floor_one_start_position()

        # Always place down stairs (unless it's a final floor)
        self._place_down_stairs()

    def _place_up_stairs(self) -> None:
        """Place up stairs in the starting room."""
        from pyrogue.map.tile import StairsUp

        start_room = self.generator.rooms[0]
        center_x, center_y = start_room.center
        self.generator.tiles[center_y, center_x] = StairsUp()
        self.generator.start_pos = (center_x, center_y)

    def _place_down_stairs(self) -> None:
        """Place down stairs in a connected room."""
        from pyrogue.map.tile import StairsDown, Floor

        # Try to place stairs in the last connected room first
        if self.generator.connected_rooms:
            last_connected = list(self.generator.connected_rooms)[-1]
            if last_connected not in self.generator.gone_rooms:
                last_room = self.generator.room_grid[last_connected[1]][last_connected[0]]
                if last_room:
                    center_x, center_y = last_room.center
                    self.generator.tiles[center_y, center_x] = StairsDown()
                    self.generator.end_pos = (center_x, center_y)
                    return

        # Fallback: place stairs in any room if the above fails
        if self.generator.rooms:
            # Find a room that's not the starting room
            for room in reversed(self.generator.rooms):
                if room != self.generator.rooms[0]:  # Not the starting room
                    center_x, center_y = room.center
                    # Make sure it's a floor tile
                    if isinstance(self.generator.tiles[center_y, center_x], Floor):
                        self.generator.tiles[center_y, center_x] = StairsDown()
                        self.generator.end_pos = (center_x, center_y)
                        return

            # Last resort: use the last room
            if len(self.generator.rooms) > 1:
                last_room = self.generator.rooms[-1]
                center_x, center_y = last_room.center
                self.generator.tiles[center_y, center_x] = StairsDown()
                self.generator.end_pos = (center_x, center_y)

    def _set_floor_one_start_position(self) -> None:
        """Set start position for floor 1 to an empty floor tile."""
        from pyrogue.map.tile import Floor

        start_room = self.generator.rooms[0]
        # Find first available floor tile in the room
        for y in range(start_room.y + 1, start_room.y + start_room.height - 1):
            for x in range(start_room.x + 1, start_room.x + start_room.width - 1):
                if isinstance(self.generator.tiles[y, x], Floor):
                    self.generator.start_pos = (x, y)
                    return

        # Fallback to center if no floor tile found
        center_x, center_y = start_room.center
        self.generator.start_pos = (center_x, center_y)
