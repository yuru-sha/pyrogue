# Map コンポーネント

PyRogueのダンジョン生成システム。オリジナルRogue準拠の26階層構造と、Builder Patternによる高品質な手続き生成を実現します。

## 概要

`src/pyrogue/map/`は、PyRogueの世界生成の中核となるダンジョンシステムです。オリジナルRogueの3x3グリッド構造を基盤とし、現代的なBuilder Patternにより拡張性の高い手続き生成を実現しています。

## アーキテクチャ

### ディレクトリ構成

```
map/
├── __init__.py
├── dungeon.py              # Builder Patternファサード
├── dungeon_manager.py      # マルチフロア管理
├── tile.py                 # タイル定義システム
└── dungeon/                # Builder Pattern実装
    ├── __init__.py
    ├── director.py         # ダンジョン生成ディレクター
    ├── room_builder.py     # 部屋生成システム
    ├── maze_builder.py     # 迷路生成システム
    ├── corridor_builder.py # 通路生成システム
    ├── section_based_builder.py # BSP生成システム
    ├── stairs_manager.py   # 階段管理
    ├── door_manager.py     # ドア管理
    ├── special_room_builder.py # 特別部屋生成
    └── validation_manager.py   # 生成検証
```

### 設計原則

- **Builder Pattern**: 段階的なダンジョン構築
- **Director Pattern**: 生成プロセスの統括管理
- **Strategy Pattern**: ダンジョンタイプ別の生成戦略
- **オリジナル忠実性**: Rogueの本質的構造の再現
- **Handler Pattern統合**: v0.1.0のHandler Patternとの完全連携

## 基盤システム

### Tile システム (tile.py)

ダンジョンを構成する基本タイル要素。

```python
class Tile:
    """タイルの基底クラス"""
    def __init__(self, walkable: bool, transparent: bool,
                 char: str, color: tuple[int, int, int]):
        self.walkable = walkable      # 歩行可能性
        self.transparent = transparent # 透明性（視線判定）
        self.char = char              # 表示文字
        self.color = color            # 表示色
        self.discovered = False       # 発見済みフラグ
```

**主要タイル種類:**

```python
class Floor(Tile):
    """床タイル（アイテム配置機能内蔵）"""
    def __init__(self):
        super().__init__(True, True, ".", color.LIGHT_GRAY)
        self.has_gold = False
        self.has_potion = False
        self.has_scroll = False
        # アイテム配置用フラグ

class Wall(Tile):
    """壁タイル"""
    def __init__(self):
        super().__init__(False, False, "#", color.WHITE)

class Door(Tile):
    """ドアタイル"""
    def __init__(self):
        super().__init__(True, False, "+", color.BROWN)
        self.open = False  # 開閉状態

class SecretDoor(Tile):
    """隠しドアタイル"""
    def __init__(self):
        super().__init__(False, False, "#", color.WHITE)
        self.discovered = False  # 発見状態

class Stairs(Tile):
    """階段タイル"""
    def __init__(self, is_up: bool):
        char = "<" if is_up else ">"
        super().__init__(True, True, char, color.WHITE)
        self.is_up = is_up
```

### DungeonManager (マルチフロア管理)

26階層全体の統合管理システム。

```python
@dataclass
class FloorData:
    """単一階層のデータ保持"""
    tiles: list[list[Tile]]
    monsters: list[Monster] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)
    traps: list[Trap] = field(default_factory=list)
    up_stairs: tuple[int, int] | None = None
    down_stairs: tuple[int, int] | None = None
    visited: bool = False

class DungeonManager:
    """26階層の統合管理"""
    def __init__(self, width: int = 80, height: int = 24):
        self.width = width
        self.height = height
        self.current_floor = 1
        self.floors: dict[int, FloorData] = {}  # 遅延生成

    def get_current_floor_data(self) -> FloorData:
        """現在階層データの取得（遅延生成）"""
        if self.current_floor not in self.floors:
            self._generate_floor(self.current_floor)
        return self.floors[self.current_floor]
```

## Builder Pattern実装

### DungeonDirector (統括管理)

ダンジョン生成全体を統括するディレクター。

```python
class DungeonDirector:
    """ダンジョン生成の統括管理"""
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.use_section_based = True  # BSP vs 従来選択

        # 各専門ビルダーの初期化
        self.room_builder = RoomBuilder()
        self.maze_builder = MazeBuilder()
        self.bsp_builder = SectionBasedBuilder()
        self.corridor_builder = CorridorBuilder()
        self.door_manager = DoorManager()
        self.stairs_manager = StairsManager()
        self.special_room_builder = SpecialRoomBuilder()
        self.validation_manager = ValidationManager()

    def generate_dungeon(self, floor: int) -> list[list[Tile]]:
        """統合ダンジョン生成"""
        # 1. ダンジョンタイプ決定
        dungeon_type = self._determine_dungeon_type(floor)

        # 2. 基本構造生成
        if dungeon_type == "maze":
            return self._generate_maze_dungeon(floor)
        else:
            return self._generate_room_dungeon(floor)

        # 3. 各要素の配置
        self._place_stairs(tiles, floor)
        self._place_doors(tiles, rooms)
        self._place_special_rooms(tiles, rooms, floor)

        # 4. 検証と最適化
        self.validation_manager.validate_dungeon(tiles, rooms, floor)

        return tiles
```

**ダンジョンタイプ決定:**
```python
def _determine_dungeon_type(self, floor: int) -> str:
    """階層に応じたダンジョンタイプ決定"""
    # 特定階層は必ず迷路
    if floor in [7, 13, 19]:
        return "maze"

    # 深い階層ほど迷路確率上昇
    if floor <= 5:
        maze_probability = 0.1
    elif floor <= 15:
        maze_probability = 0.2
    else:
        maze_probability = 0.3

    return "maze" if random.random() < maze_probability else "rooms"
```

### RoomBuilder (部屋生成)

オリジナルRogue準拠の3x3グリッド部屋生成。

```python
@dataclass
class Room:
    """部屋データクラス"""
    x: int
    y: int
    width: int
    height: int
    center_x: int
    center_y: int
    doors: list[tuple[int, int]] = field(default_factory=list)
    connected_rooms: list[int] = field(default_factory=list)
    is_special: bool = False
    is_gone: bool = False  # Gone Room (通路のみ)

class RoomBuilder:
    """3x3グリッドシステムによる部屋生成"""
    def generate_rooms(self, width: int, height: int) -> list[Room]:
        """部屋生成メイン処理"""
        rooms = []

        # 3x3グリッドの各セルで部屋生成
        for grid_y in range(3):
            for grid_x in range(3):
                # Gone Room判定（25%確率）
                if random.random() < ProbabilityConstants.GONE_ROOM_CHANCE:
                    continue

                room = self._create_room_in_cell(grid_x, grid_y, width, height)
                if room:
                    rooms.append(room)

        return rooms

    def _create_room_in_cell(self, grid_x: int, grid_y: int,
                           width: int, height: int) -> Room | None:
        """グリッドセル内での部屋生成"""
        # セル境界の計算
        cell_width = width // 3
        cell_height = height // 3
        cell_start_x = grid_x * cell_width
        cell_start_y = grid_y * cell_height

        # 部屋サイズの決定（セルサイズの50-80%）
        room_width = random.randint(
            max(3, cell_width // 2),
            max(4, int(cell_width * 0.8))
        )
        room_height = random.randint(
            max(3, cell_height // 2),
            max(4, int(cell_height * 0.8))
        )

        # 部屋位置の決定（セル内でランダム配置）
        room_x = cell_start_x + random.randint(1, cell_width - room_width - 1)
        room_y = cell_start_y + random.randint(1, cell_height - room_height - 1)

        return Room(
            x=room_x, y=room_y,
            width=room_width, height=room_height,
            center_x=room_x + room_width // 2,
            center_y=room_y + room_height // 2
        )
```

### MazeBuilder (迷路生成)

セルラーオートマタによる自然な迷路生成。

```python
class MazeBuilder:
    """迷路専用ダンジョン生成"""
    def generate_maze(self, width: int, height: int) -> list[list[Tile]]:
        """迷路生成メイン処理"""
        # 1. 基本格子の生成
        tiles = self._create_base_grid(width, height)

        # 2. セルラーオートマタによる自然化
        for _ in range(2):
            tiles = self._apply_cellular_automata(tiles)

        # 3. デッドエンド除去
        self._remove_dead_ends(tiles, removal_rate=0.6)

        # 4. 連結性保証
        self._ensure_connectivity(tiles)

        # 5. 境界強化
        self._reinforce_boundaries(tiles)

        return tiles

    def _create_base_grid(self, width: int, height: int) -> list[list[Tile]]:
        """基本格子の生成"""
        tiles = [[Wall() for _ in range(width)] for _ in range(height)]

        # 奇数座標に通路配置
        for y in range(1, height - 1, 2):
            for x in range(1, width - 1, 2):
                tiles[y][x] = Floor()

                # ランダムな方向に通路延長
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                direction = random.choice(directions)
                new_x = x + direction[0]
                new_y = y + direction[1]

                if (0 < new_x < width - 1 and 0 < new_y < height - 1):
                    tiles[new_y][new_x] = Floor()

        return tiles

    def _apply_cellular_automata(self, tiles: list[list[Tile]]) -> list[list[Tile]]:
        """セルラーオートマタによる自然化"""
        new_tiles = [row[:] for row in tiles]  # Deep copy

        for y in range(1, len(tiles) - 1):
            for x in range(1, len(tiles[0]) - 1):
                wall_count = self._count_adjacent_walls(tiles, x, y)

                # 自然化ルール
                if wall_count >= 5:
                    new_tiles[y][x] = Wall()
                elif wall_count <= 3:
                    new_tiles[y][x] = Floor()

        return new_tiles
```

### CorridorBuilder (通路生成)

最小スパニングツリーによる全部屋接続。

```python
class CorridorBuilder:
    """部屋間通路生成"""
    def create_corridors(self, tiles: list[list[Tile]],
                        rooms: list[Room]) -> list[Corridor]:
        """通路生成メイン処理"""
        if len(rooms) < 2:
            return []

        # 1. 最小スパニングツリーによる基本接続
        mst_edges = self._calculate_minimum_spanning_tree(rooms)
        corridors = []

        for room1_idx, room2_idx in mst_edges:
            corridor = self._create_corridor(
                tiles, rooms[room1_idx], rooms[room2_idx]
            )
            if corridor:
                corridors.append(corridor)
                self._carve_corridor(tiles, corridor)

        # 2. 追加接続（20%確率でループ構造）
        self._add_extra_connections(tiles, rooms, corridors)

        return corridors

    def _create_corridor(self, tiles: list[list[Tile]],
                        room1: Room, room2: Room) -> Corridor | None:
        """L字型通路の生成"""
        start_x, start_y = room1.center_x, room1.center_y
        end_x, end_y = room2.center_x, room2.center_y

        # L字経路の計算（水平→垂直）
        path = []

        # 水平移動
        x_step = 1 if end_x > start_x else -1
        for x in range(start_x, end_x + x_step, x_step):
            path.append((x, start_y))

        # 垂直移動
        y_step = 1 if end_y > start_y else -1
        for y in range(start_y + y_step, end_y + y_step, y_step):
            path.append((end_x, y))

        return Corridor(
            path=path,
            room1_index=room1.index,
            room2_index=room2.index
        )
```

## 専門管理システム

### StairsManager (階段管理)

26階層構造に対応した階段配置システム。

```python
class StairsManager:
    """階段配置管理"""
    def place_stairs(self, tiles: list[list[Tile]],
                    rooms: list[Room], floor: int) -> dict[str, tuple[int, int]]:
        """階層対応階段配置"""
        stairs_positions = {}

        # 上り階段（1階以外）
        if floor > 1:
            up_pos = self._find_valid_stair_position(tiles, rooms, "up")
            if up_pos:
                tiles[up_pos[1]][up_pos[0]] = Stairs(is_up=True)
                stairs_positions["up"] = up_pos

        # 下り階段（26階以外）
        if floor < GameConstants.MAX_FLOORS:
            down_pos = self._find_valid_stair_position(tiles, rooms, "down")
            if down_pos:
                tiles[down_pos[1]][down_pos[0]] = Stairs(is_up=False)
                stairs_positions["down"] = down_pos

        return stairs_positions

    def _find_valid_stair_position(self, tiles: list[list[Tile]],
                                  rooms: list[Room], stair_type: str) -> tuple[int, int] | None:
        """安全な階段位置の探索"""
        # 部屋がある場合は部屋内に配置
        if rooms:
            room = random.choice(rooms)
            for _ in range(50):  # 最大50回試行
                x = random.randint(room.x + 1, room.x + room.width - 2)
                y = random.randint(room.y + 1, room.y + room.height - 2)

                if isinstance(tiles[y][x], Floor):
                    return (x, y)

        # 迷路の場合は通路から探索
        return self._find_maze_stair_position(tiles)
```

### DoorManager (ドア管理)

通路と部屋の接続点における適切なドア配置。

```python
class DoorManager:
    """ドア配置管理"""
    def place_doors(self, tiles: list[list[Tile]],
                   rooms: list[Room], corridors: list[Corridor]) -> None:
        """ドア配置メイン処理"""
        for room in rooms:
            if room.is_special:
                continue  # 特別部屋は通常ドアのみ

            door_positions = self._find_door_positions(tiles, room, corridors)

            # 部屋あたり最大2個まで
            for pos in door_positions[:2]:
                door_type = self._determine_door_type(room)
                if door_type == "secret":
                    tiles[pos[1]][pos[0]] = SecretDoor()
                else:
                    tiles[pos[1]][pos[0]] = Door()

    def _determine_door_type(self, room: Room) -> str:
        """ドア種類の決定"""
        if room.is_special:
            return "normal"  # 特別部屋は通常ドアのみ

        # 15%確率で隠しドア
        return "secret" if random.random() < ProbabilityConstants.SECRET_DOOR_CHANCE else "normal"

    def _find_door_positions(self, tiles: list[list[Tile]],
                           room: Room, corridors: list[Corridor]) -> list[tuple[int, int]]:
        """部屋境界での通路接続点検出"""
        door_positions = []

        # 部屋境界をスキャン
        for x in range(room.x, room.x + room.width):
            for y in range(room.y, room.y + room.height):
                if self._is_door_candidate(tiles, x, y, room):
                    door_positions.append((x, y))

        return door_positions
```

### ValidationManager (生成検証)

品質保証とエラー検出システム。

```python
class ValidationManager:
    """ダンジョン生成検証"""
    def validate_dungeon(self, tiles: list[list[Tile]],
                        rooms: list[Room], floor: int) -> ValidationResult:
        """多段階検証実行"""
        result = ValidationResult()

        # 1. 基本構造検証
        result.merge(self._validate_basic_structure(tiles))

        # 2. 接続性検証
        result.merge(self._validate_connectivity(tiles))

        # 3. 境界制約検証
        result.merge(self._validate_boundaries(tiles))

        # 4. 階段配置検証
        result.merge(self._validate_stairs_placement(tiles, floor))

        # 5. 迷路専用検証
        if not rooms:  # 迷路の場合
            result.merge(self._validate_maze_specific(tiles))

        return result

    def _validate_connectivity(self, tiles: list[list[Tile]]) -> ValidationResult:
        """連結性検証（フラッドフィル）"""
        result = ValidationResult()

        # 歩行可能エリアの検出
        walkable_positions = []
        for y in range(len(tiles)):
            for x in range(len(tiles[0])):
                if tiles[y][x].walkable:
                    walkable_positions.append((x, y))

        if not walkable_positions:
            result.add_error("No walkable tiles found")
            return result

        # フラッドフィルによる連結性確認
        visited = set()
        start_pos = walkable_positions[0]
        self._flood_fill(tiles, start_pos[0], start_pos[1], visited)

        # 到達不可能エリアの検出
        unreachable_count = len(walkable_positions) - len(visited)
        if unreachable_count > 0:
            result.add_warning(f"{unreachable_count} unreachable tiles found")

        return result
```

## 迷路階層システム

### 迷路生成の特徴

**階層決定ロジック:**
- 特定階層（7, 13, 19階）: 必ず迷路
- 深い階層ほど高確率: 15階以下30%、5階以下10%
- 複雑度の階層補正: 深いほど複雑な構造

**生成アルゴリズム:**
1. **基本格子**: 奇数座標に通路配置
2. **セルラーオートマタ**: 自然化処理（2イテレーション）
3. **デッドエンド除去**: 60%除去率で複雑度調整
4. **連結性保証**: フラッドフィル + 成分接続
5. **境界強化**: 外壁の完全性確保

**迷路専用検証:**
```python
def _validate_maze_specific(self, tiles: list[list[Tile]]) -> ValidationResult:
    """迷路固有の検証項目"""
    result = ValidationResult()

    # 密度チェック（歩行可能タイルが20-60%）
    walkable_ratio = self._calculate_walkable_ratio(tiles)
    if walkable_ratio < 0.2:
        result.add_error("Maze too sparse")
    elif walkable_ratio > 0.6:
        result.add_error("Maze too dense")

    # デッドエンド率チェック
    dead_end_ratio = self._calculate_dead_end_ratio(tiles)
    if dead_end_ratio > 0.4:
        result.add_warning("Too many dead ends")

    return result
```

## オリジナルRogueとの忠実性

### 構造的忠実性

**26階層構造:**
```python
GameConstants.MAX_FLOORS = 26  # オリジナル準拠
```

**3x3グリッドシステム:**
```python
# オリジナルRogueの部屋配置概念
grid_width, grid_height = 3, 3
cell_width = dungeon_width // 3
cell_height = dungeon_height // 3
```

**Gone Room概念:**
```python
# 25%確率で部屋なし（通路のみセル）
GONE_ROOM_CHANCE = 0.25
```

### 確率パラメータの忠実性

```python
class ProbabilityConstants:
    GONE_ROOM_CHANCE = 0.25          # Gone Room確率
    SECRET_DOOR_CHANCE = 0.15        # 隠しドア確率
    SPECIAL_ROOM_CHANCE = 0.33       # 特別部屋確率
    EXTRA_CONNECTION_CHANCE = 0.2    # 追加接続確率
```

### 拡張機能

**BSPアルゴリズム:**
- TCOD BSPライブラリによる高品質生成
- 再帰分割深度5、アスペクト比1.5制約
- L字型通路による自然な接続

**迷路階層:**
- オリジナルにない新機能
- セルラーオートマタによる有機的構造
- 段階的複雑度制御

**検証システム:**
- 自動品質保証
- 詳細な統計レポート
- 段階的エラー検出

## 使用パターン

### 基本的なダンジョン生成

```python
from pyrogue.map.dungeon_manager import DungeonManager

# ダンジョンマネージャーの初期化
dungeon_manager = DungeonManager(width=80, height=24)

# 現在階層のダンジョン取得
floor_data = dungeon_manager.get_current_floor_data()
tiles = floor_data.tiles

# 階層移動
dungeon_manager.move_to_floor(5)
```

### カスタム生成パラメータ

```python
from pyrogue.map.dungeon.director import DungeonDirector

# ディレクターでの直接生成
director = DungeonDirector(width=100, height=30)
director.use_section_based = True  # BSP使用

# 特定階層の生成
tiles = director.generate_dungeon(floor=10)
```

### 迷路生成の強制

```python
# 迷路階層の強制生成
maze_builder = MazeBuilder()
maze_tiles = maze_builder.generate_maze(width=80, height=24)
```

## 拡張ガイド

### 新しいダンジョンタイプの追加

```python
class CaveBuilder:
    """洞窟型ダンジョン生成"""
    def generate_cave(self, width: int, height: int) -> list[list[Tile]]:
        # セルラーオートマタによる洞窟生成
        tiles = self._cellular_automata_cave(width, height)
        return tiles

# ディレクターに統合
class DungeonDirector:
    def _determine_dungeon_type(self, floor: int) -> str:
        # 新しいタイプの追加
        if floor in [10, 20]:
            return "cave"
        # 既存ロジック...
```

### カスタム部屋配置

```python
class CustomRoomBuilder(RoomBuilder):
    """カスタム部屋配置システム"""
    def generate_rooms(self, width: int, height: int) -> list[Room]:
        # 5x5グリッドでの部屋生成
        return self._generate_5x5_grid_rooms(width, height)
```

### 新しい検証ルール

```python
class CustomValidationManager(ValidationManager):
    """カスタム検証ルール"""
    def validate_custom_rules(self, tiles: list[list[Tile]]) -> ValidationResult:
        result = ValidationResult()

        # カスタム検証ロジック
        if self._check_custom_condition(tiles):
            result.add_warning("Custom condition violated")

        return result
```

## パフォーマンス最適化

### 遅延生成

```python
# 必要時のみ階層生成
def get_floor_data(self, floor: int) -> FloorData:
    if floor not in self.floors:
        self._generate_floor(floor)  # 遅延生成
    return self.floors[floor]
```

### メモリ効率化

```python
# 不要階層の解放
def cleanup_distant_floors(self, current_floor: int, keep_range: int = 2):
    """現在階層から離れた階層のメモリ解放"""
    floors_to_remove = [
        floor for floor in self.floors.keys()
        if abs(floor - current_floor) > keep_range
    ]

    for floor in floors_to_remove:
        del self.floors[floor]
```

### 生成品質の最適化

```python
# 品質重視の再生成
def generate_with_quality_check(self, floor: int, max_attempts: int = 5) -> list[list[Tile]]:
    """品質チェック付き生成"""
    for attempt in range(max_attempts):
        tiles = self.generate_dungeon(floor)
        validation_result = self.validation_manager.validate_dungeon(tiles, [], floor)

        if not validation_result.has_errors():
            return tiles

    # フォールバック: 最後の結果を返却
    return tiles
```

## Handler Pattern連携（v0.1.0）

### ダンジョンシステムとHandler Patternの統合

v0.1.0で導入されたHandler Patternとダンジョンシステムは密接に連携し、以下の統合された処理を実現しています：

#### 階層移動の統合処理

```python
class InfoCommandHandler:
    def handle_floor_info(self) -> CommandResult:
        """現在階層情報表示"""
        dungeon_manager = self.context.game_context.dungeon_manager
        current_floor = dungeon_manager.current_floor
        floor_data = dungeon_manager.get_current_floor_data()

        # ダンジョンタイプの判定
        dungeon_type = "maze" if not floor_data.rooms else "rooms"
        room_count = len(floor_data.rooms) if floor_data.rooms else 0

        info_msg = f"Floor {current_floor}/26 ({dungeon_type}, {room_count} rooms)"
        self.context.add_message(info_msg)
        return CommandResult.success()
```

#### デバッグコマンドでのダンジョン操作

```python
class DebugCommandHandler:
    def handle_teleport_to_stairs(self) -> CommandResult:
        """階段にテレポート（デバッグ）"""
        dungeon_manager = self.context.game_context.dungeon_manager
        floor_data = dungeon_manager.get_current_floor_data()
        player = self.context.game_context.player

        # 下り階段の位置を取得
        if floor_data.down_stairs:
            player.x, player.y = floor_data.down_stairs
            self.context.add_message("Teleported to down stairs")
            return CommandResult.success_with_turn()

        return CommandResult.failure("No stairs found on this floor")

    def handle_reveal_map(self) -> CommandResult:
        """全マップ探索（デバッグ）"""
        dungeon_manager = self.context.game_context.dungeon_manager
        floor_data = dungeon_manager.get_current_floor_data()

        # 全タイルを発見済みにする
        for row in floor_data.tiles:
            for tile in row:
                tile.discovered = True

        self.context.add_message("Full map revealed")
        return CommandResult.success()
```

#### 自動探索でのダンジョン解析

```python
class AutoExploreHandler:
    def _analyze_dungeon_structure(self) -> dict[str, any]:
        """ダンジョン構造の解析"""
        dungeon_manager = self.context.game_context.dungeon_manager
        floor_data = dungeon_manager.get_current_floor_data()

        analysis = {
            'unexplored_tiles': [],
            'secret_doors': [],
            'unreachable_areas': []
        }

        # 未探索タイルの検出
        for y, row in enumerate(floor_data.tiles):
            for x, tile in enumerate(row):
                if tile.walkable and not tile.discovered:
                    analysis['unexplored_tiles'].append((x, y))

                # 隠しドアの検出
                if isinstance(tile, SecretDoor) and not tile.discovered:
                    analysis['secret_doors'].append((x, y))

        return analysis

    def handle_auto_explore(self) -> CommandResult:
        """自動探索（ダンジョン構造活用）"""
        analysis = self._analyze_dungeon_structure()

        if not analysis['unexplored_tiles']:
            self.context.add_message("No more areas to explore")
            return CommandResult.success()

        # 最も近い未探索タイルへの移動
        player = self.context.game_context.player
        target = self._find_nearest_unexplored(player.x, player.y, analysis['unexplored_tiles'])

        if target:
            # パスファインディングとダンジョン構造を使った移動
            return self._move_towards_target(target)

        return CommandResult.failure("Cannot find path to unexplored area")
```

#### セーブ・ロードでのダンジョン状態管理

```python
class SaveLoadHandler:
    def _save_dungeon_states(self, game_context: GameContext) -> dict:
        """ダンジョン状態の保存"""
        dungeon_manager = game_context.dungeon_manager

        # 全階層データの保存
        floors_data = {}
        for floor_num, floor_data in dungeon_manager.floors.items():
            floors_data[floor_num] = {
                'tiles': self._serialize_tiles(floor_data.tiles),
                'monsters': [self._serialize_monster(m) for m in floor_data.monsters],
                'items': [self._serialize_item(i) for i in floor_data.items],
                'traps': [self._serialize_trap(t) for t in floor_data.traps],
                'up_stairs': floor_data.up_stairs,
                'down_stairs': floor_data.down_stairs,
                'visited': floor_data.visited
            }

        return {
            'current_floor': dungeon_manager.current_floor,
            'floors': floors_data,
            'dungeon_seed': dungeon_manager.generation_seed  # 再現可能性のため
        }

    def _serialize_tiles(self, tiles: list[list[Tile]]) -> list[list[dict]]:
        """タイル状態のシリアライズ"""
        serialized = []
        for row in tiles:
            serialized_row = []
            for tile in row:
                tile_data = {
                    'type': tile.__class__.__name__,
                    'discovered': tile.discovered
                }

                # タイル固有の状態保存
                if isinstance(tile, Door):
                    tile_data['open'] = tile.open
                elif isinstance(tile, SecretDoor):
                    tile_data['found'] = tile.discovered

                serialized_row.append(tile_data)
            serialized.append(serialized_row)

        return serialized
```

### ダンジョン生成の統合ワークフロー

```python
class CommonCommandHandler:
    def _handle_floor_transition(self, direction: str) -> CommandResult:
        """階層移動の統合処理"""
        dungeon_manager = self.context.game_context.dungeon_manager
        player = self.context.game_context.player

        # 現在階層のクリーンアップ
        current_floor_data = dungeon_manager.get_current_floor_data()
        current_floor_data.visited = True

        # 新階層の準備
        if direction == "down":
            new_floor = dungeon_manager.current_floor + 1
        else:
            new_floor = dungeon_manager.current_floor - 1

        # 階層移動の実行
        dungeon_manager.move_to_floor(new_floor)
        new_floor_data = dungeon_manager.get_current_floor_data()

        # プレイヤー位置の設定
        if direction == "down" and new_floor_data.up_stairs:
            player.x, player.y = new_floor_data.up_stairs
        elif direction == "up" and new_floor_data.down_stairs:
            player.x, player.y = new_floor_data.down_stairs

        self.context.add_message(f"Entered floor {new_floor}")
        return CommandResult.success_with_turn()
```

## まとめ

Map コンポーネントは、PyRogueプロジェクトの世界生成において以下の価値を提供します：

- **オリジナル忠実性**: Rogueの本質的なダンジョン構造の再現
- **現代的設計**: Builder Patternによる高い拡張性と保守性
- **品質保証**: 自動検証による安定したダンジョン生成
- **多様性**: 部屋型・迷路型・BSP型の多彩な生成戦略
- **スケーラビリティ**: 26階層の効率的な管理システム
- **Handler Pattern統合**: v0.1.0のHandler Patternとの完全な連携

この設計により、オリジナルRogueの魅力的なダンジョン探索体験を現代的な技術で実現し、さらなる拡張可能性を提供する堅牢なシステムを構築しています。
