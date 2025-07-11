"""
BSPベースのダンジョン生成システム。

参考: https://www.ilikerogue.com/posts/2022/02/13/dungeon/
BSP(Binary Space Partitioning)によりマップを再帰的に分割し、
構造化された直角通路でダンジョンを生成する。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np

from pyrogue.map.dungeon.room_builder import Room
from pyrogue.map.tile import Door, Floor, Wall
from pyrogue.utils import game_logger


@dataclass
class BSPSection:
    """BSP分割によるセクション。"""

    x: int
    y: int
    width: int
    height: int
    children: list[BSPSection] = field(default_factory=list)
    parent: BSPSection | None = None
    purpose: str = "unassigned"  # "room", "nothing"
    room: Room | None = None

    @property
    def center(self) -> tuple[int, int]:
        """セクションの中心座標。"""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def is_leaf(self) -> bool:
        """葉ノード（末端セクション）かどうか。"""
        return len(self.children) == 0


class BSPDungeonBuilder:
    """
    BSP（Binary Space Partitioning）ベースのダンジョン生成ビルダー。

    マップを再帰的に分割し、構造化された部屋と直角通路を生成する。
    """

    def __init__(self, width: int, height: int, min_section_size: int = 10) -> None:
        """
        BSPダンジョンビルダーを初期化。

        Args:
        ----
            width: ダンジョンの幅
            height: ダンジョンの高さ
            min_section_size: セクションの最小サイズ

        """
        self.width = width
        self.height = height
        self.min_section_size = min_section_size

        # BSP木のルート
        self.root = BSPSection(0, 0, width, height)
        self.rooms: list[Room] = []

        game_logger.info(
            f"BSPDungeonBuilder initialized: {width}x{height}, min_size={min_section_size}"
        )

    def build_dungeon(self, tiles: np.ndarray) -> list[Room]:
        """
        BSPベースのダンジョンを生成。

        Args:
        ----
            tiles: タイル配列

        Returns:
        -------
            生成された部屋のリスト

        """
        # 1. BSP分割を実行
        self._split_section(self.root)

        # 2. 葉ノードに部屋の用途を割り当て
        self._assign_purposes(room_chance=0.8)

        # 3. 部屋を生成
        self._create_rooms(tiles)

        # 4. セクション間を接続
        self._connect_sections(tiles)

        # 5. ドアを配置
        self._place_doors(tiles)

        game_logger.info(f"BSP dungeon built: {len(self.rooms)} rooms")
        return self.rooms

    def _split_section(self, section: BSPSection) -> None:
        """セクションを再帰的に分割。"""
        # 分割が不可能な場合は停止
        if (
            section.width < self.min_section_size * 2
            or section.height < self.min_section_size * 2
        ):
            return

        # 分割方向を決定（より正方形に近いセクションになるように）
        width_height_ratio = section.width / section.height

        if section.width < self.min_section_size * 2:
            split_horizontally = True  # 水平分割しかできない
        elif section.height < self.min_section_size * 2:
            split_horizontally = False  # 垂直分割しかできない
        elif width_height_ratio > 1.25:  # 幅が高さの1.25倍以上なら垂直分割を優先
            split_horizontally = False
        elif width_height_ratio < 0.8:  # 高さが幅の1.25倍以上なら水平分割を優先
            split_horizontally = True
        else:
            split_horizontally = random.choice([True, False])

        if split_horizontally:
            # 水平分割（高さを分割）
            if section.height < self.min_section_size * 2:
                return  # 分割不可

            split_pos = random.randint(
                self.min_section_size, section.height - self.min_section_size
            )
            child1 = BSPSection(
                section.x, section.y, section.width, split_pos, parent=section
            )
            child2 = BSPSection(
                section.x,
                section.y + split_pos,
                section.width,
                section.height - split_pos,
                parent=section,
            )
        else:
            # 垂直分割（幅を分割）
            if section.width < self.min_section_size * 2:
                return  # 分割不可

            split_pos = random.randint(
                self.min_section_size, section.width - self.min_section_size
            )
            child1 = BSPSection(
                section.x, section.y, split_pos, section.height, parent=section
            )
            child2 = BSPSection(
                section.x + split_pos,
                section.y,
                section.width - split_pos,
                section.height,
                parent=section,
            )

        section.children = [child1, child2]

        # 再帰的に分割
        self._split_section(child1)
        self._split_section(child2)

    def _get_leaf_sections(self) -> list[BSPSection]:
        """葉ノード（末端セクション）のリストを取得。"""
        leaves = []
        nodes_to_visit = [self.root]

        while nodes_to_visit:
            current = nodes_to_visit.pop(0)
            if current.is_leaf:
                leaves.append(current)
            else:
                nodes_to_visit.extend(current.children)

        return leaves

    def _assign_purposes(self, room_chance: float = 0.8) -> None:
        """葉ノードに部屋の用途を割り当て。"""
        leaf_sections = self._get_leaf_sections()

        for section in leaf_sections:
            if random.random() < room_chance:
                section.purpose = "room"
            else:
                section.purpose = "nothing"

        game_logger.debug(
            f"Assigned purposes: {sum(1 for s in leaf_sections if s.purpose == 'room')} rooms, "
            f"{sum(1 for s in leaf_sections if s.purpose == 'nothing')} empty"
        )

    def _create_rooms(self, tiles: np.ndarray) -> None:
        """部屋を生成してタイルに配置。"""
        self.rooms = []
        room_id = 0

        for section in self._get_leaf_sections():
            if section.purpose == "room":
                # セクション内により正方形に近い部屋を作成
                margin = 2

                # セクションの利用可能サイズ
                available_width = section.width - margin * 2
                available_height = section.height - margin * 2

                # より正方形に近い部屋にするため、最小サイズを調整
                min_size = 4  # 最小部屋サイズ

                # 利用可能サイズに基づいて最適な部屋サイズを計算
                # アスペクト比を2:1以下に制限
                target_width = min(available_width, available_height * 2)
                target_height = min(available_height, available_width * 2)

                # 最小サイズと最大サイズの範囲を設定
                min_width = max(min_size, target_width // 2)
                max_width = min(available_width, target_width)
                min_height = max(min_size, target_height // 2)
                max_height = min(available_height, target_height)

                # 範囲の妥当性チェック
                max_width = max(max_width, min_width)
                max_height = max(max_height, min_height)

                # 実際の部屋サイズを決定
                room_width = random.randint(min_width, max_width)
                room_height = random.randint(min_height, max_height)

                # アスペクト比チェックと調整
                aspect_ratio = max(room_width, room_height) / min(
                    room_width, room_height
                )
                if aspect_ratio > 2.0:  # 2:1より細長い場合は調整
                    if room_width > room_height:
                        room_width = min(room_width, room_height * 2)
                    else:
                        room_height = min(room_height, room_width * 2)

                # 部屋を中央寄りに配置（少しのランダム性を保持）
                center_x = section.x + section.width // 2 - room_width // 2
                center_y = section.y + section.height // 2 - room_height // 2

                # 中央位置から少しずらす（±1マスの範囲内）
                offset_range = 1
                room_x = max(
                    section.x + margin,
                    min(
                        center_x + random.randint(-offset_range, offset_range),
                        section.x + section.width - room_width - margin,
                    ),
                )
                room_y = max(
                    section.y + margin,
                    min(
                        center_y + random.randint(-offset_range, offset_range),
                        section.y + section.height - room_height - margin,
                    ),
                )

                # 境界チェック
                room_x = max(1, min(room_x, self.width - room_width - 1))
                room_y = max(1, min(room_y, self.height - room_height - 1))
                room_width = min(room_width, self.width - room_x - 1)
                room_height = min(room_height, self.height - room_y - 1)

                room = Room(
                    id=room_id, x=room_x, y=room_y, width=room_width, height=room_height
                )

                self.rooms.append(room)
                section.room = room
                room_id += 1

                # タイルに部屋を配置
                self._place_room_on_tiles(room, tiles)

    def _place_room_on_tiles(self, room: Room, tiles: np.ndarray) -> None:
        """個別の部屋をタイルに配置。"""
        # 部屋内部を床に
        for y in range(room.y + 1, room.y + room.height - 1):
            for x in range(room.x + 1, room.x + room.width - 1):
                if 0 <= x < self.width and 0 <= y < self.height:
                    tiles[y, x] = Floor()

        # 部屋の境界を壁に（後で通路がドアに変更される）
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= x < self.width and 0 <= y < self.height:
                    if (
                        x == room.x
                        or x == room.x + room.width - 1
                        or y == room.y
                        or y == room.y + room.height - 1
                    ):
                        # 既に床でない場合のみ壁に設定
                        if not isinstance(tiles[y, x], Floor):
                            tiles[y, x] = Wall()

    def _connect_sections(self, tiles: np.ndarray) -> None:
        """BSP木の兄弟セクション間を接続。"""
        nodes_to_visit = [self.root]

        while nodes_to_visit:
            current = nodes_to_visit.pop(0)

            if not current.children:
                continue

            nodes_to_visit.extend(current.children)

            child1, child2 = current.children

            # 両方の子に部屋があるかチェック
            if not (
                self._has_room_descendant(child1) and self._has_room_descendant(child2)
            ):
                continue

            # 分割線に沿って通路を作成
            if child1.y == child2.y:  # 垂直分割
                split_x = child2.x
                corridor_y = random.randint(
                    max(child1.y + 1, child2.y + 1),
                    min(child1.y + child1.height - 2, child2.y + child2.height - 2),
                )

                room1_center = self._find_room_center_in_section(child1)
                room2_center = self._find_room_center_in_section(child2)

                if room1_center and room2_center:
                    # L字型通路を作成
                    self._create_corridor(
                        tiles, room1_center[0], room1_center[1], split_x, corridor_y
                    )
                    self._create_corridor(
                        tiles, split_x, corridor_y, room2_center[0], room2_center[1]
                    )

            else:  # 水平分割
                split_y = child2.y
                corridor_x = random.randint(
                    max(child1.x + 1, child2.x + 1),
                    min(child1.x + child1.width - 2, child2.x + child2.width - 2),
                )

                room1_center = self._find_room_center_in_section(child1)
                room2_center = self._find_room_center_in_section(child2)

                if room1_center and room2_center:
                    # L字型通路を作成
                    self._create_corridor(
                        tiles, room1_center[0], room1_center[1], corridor_x, split_y
                    )
                    self._create_corridor(
                        tiles, corridor_x, split_y, room2_center[0], room2_center[1]
                    )

    def _has_room_descendant(self, section: BSPSection) -> bool:
        """セクションまたはその子孫に部屋があるかチェック。"""
        if section.purpose == "room":
            return True
        if section.is_leaf:
            return False
        return any(self._has_room_descendant(child) for child in section.children)

    def _find_room_center_in_section(
        self, section: BSPSection
    ) -> tuple[int, int] | None:
        """セクション内の部屋の中心座標を見つける。"""
        if section.purpose == "room" and section.room:
            return section.room.center()
        if section.is_leaf:
            return None

        for child in section.children:
            center = self._find_room_center_in_section(child)
            if center:
                return center
        return None

    def _create_corridor(
        self, tiles: np.ndarray, x1: int, y1: int, x2: int, y2: int
    ) -> None:
        """2点間にL字型通路を作成。"""
        if random.random() < 0.5:
            # 水平 → 垂直
            self._carve_path(tiles, x1, y1, x2, y1)
            self._carve_path(tiles, x2, y1, x2, y2)
        else:
            # 垂直 → 水平
            self._carve_path(tiles, x1, y1, x1, y2)
            self._carve_path(tiles, x1, y2, x2, y2)

    def _carve_path(
        self, tiles: np.ndarray, x1: int, y1: int, x2: int, y2: int
    ) -> None:
        """直線通路を彫る。"""
        if x1 == x2:  # 垂直線
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= y < self.height and 0 <= x1 < self.width:
                    tiles[y, x1] = Floor()
        else:  # 水平線
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= y1 < self.height and 0 <= x < self.width:
                    tiles[y1, x] = Floor()

    def _place_doors(self, tiles: np.ndarray) -> None:
        """部屋と通路の適切な接続点にドアを配置。"""
        for room in self.rooms:
            # 各壁ごとにドア候補を分類
            wall_candidates = {
                "north": [],  # 上壁
                "south": [],  # 下壁
                "west": [],  # 左壁
                "east": [],  # 右壁
            }

            # 部屋の境界で通路と接続している点を壁ごとに分類
            for y in range(room.y, room.y + room.height):
                for x in range(room.x, room.x + room.width):
                    # 境界が床で、かつ真の入り口である場合
                    if isinstance(tiles[y, x], Floor) and self._is_room_entrance(
                        x, y, room, tiles
                    ):
                        if y == room.y:  # 上壁
                            wall_candidates["north"].append((x, y))
                        elif y == room.y + room.height - 1:  # 下壁
                            wall_candidates["south"].append((x, y))
                        elif x == room.x:  # 左壁
                            wall_candidates["west"].append((x, y))
                        elif x == room.x + room.width - 1:  # 右壁
                            wall_candidates["east"].append((x, y))

            # 各壁から最大1個のドアを選択
            selected_doors = []
            for wall, candidates in wall_candidates.items():
                if candidates:
                    # 各壁の中央に最も近い候補を選択
                    best_door = self._select_best_door_for_wall(candidates, room, wall)
                    if best_door:
                        selected_doors.append(best_door)

            # 最大2個までのドアに制限
            if len(selected_doors) > 2:
                selected_doors = random.sample(selected_doors, 2)

            for x, y in selected_doors:
                tiles[y, x] = Door()
                room.add_door(x, y)

    def _is_room_entrance(self, x: int, y: int, room: Room, tiles: np.ndarray) -> bool:
        """指定された位置が部屋の真の入り口かどうかを判定。"""
        # 部屋の境界上にあることを確認
        is_on_boundary = (
            x == room.x
            or x == room.x + room.width - 1
            or y == room.y
            or y == room.y + room.height - 1
        )

        if not is_on_boundary:
            return False

        # 隣接する通路タイルの数をカウント
        corridor_neighbors = 0
        room_neighbors = 0

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if self._is_inside_room(nx, ny, room):
                    room_neighbors += 1
                elif isinstance(tiles[ny, nx], Floor):
                    corridor_neighbors += 1

        # 部屋の内部と通路の両方に接している場合のみ入り口とみなす
        return room_neighbors > 0 and corridor_neighbors > 0

    def _is_inside_room(self, x: int, y: int, room: Room) -> bool:
        """指定された位置が部屋の内部にあるかチェック。"""
        return (
            room.x < x < room.x + room.width - 1
            and room.y < y < room.y + room.height - 1
        )

    def _select_best_door_for_wall(
        self, candidates: list[tuple[int, int]], room: Room, wall: str
    ) -> tuple[int, int] | None:
        """各壁の最適なドア位置を選択。"""
        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # 壁の中央に最も近い候補を選択
        if wall in ["north", "south"]:
            # 水平方向の壁：中央のX座標に最も近い位置
            center_x = room.x + room.width // 2
            best_candidate = min(candidates, key=lambda pos: abs(pos[0] - center_x))
        else:  # west, east
            # 垂直方向の壁：中央のY座標に最も近い位置
            center_y = room.y + room.height // 2
            best_candidate = min(candidates, key=lambda pos: abs(pos[1] - center_y))

        return best_candidate

    def reset(self) -> None:
        """ビルダーの状態をリセット。"""
        self.root = BSPSection(0, 0, self.width, self.height)
        self.rooms = []

    def get_statistics(self) -> dict:
        """生成統計を取得。"""
        leaf_count = len(self._get_leaf_sections())
        room_count = len(self.rooms)

        return {
            "builder_type": "BSP",
            "leaf_sections": leaf_count,
            "room_count": room_count,
            "room_ratio": f"{room_count / leaf_count * 100:.1f}%"
            if leaf_count > 0
            else "0%",
            "min_section_size": self.min_section_size,
        }
