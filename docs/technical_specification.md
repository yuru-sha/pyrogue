---
cache_control: {"type": "ephemeral"}
---
# PyRogue - 技術仕様書

## ドキュメント概要

この技術仕様書は、PyRogueプロジェクトの実装レベルでの技術仕様を詳細に記述します。API設計、データ構造、パフォーマンス要件、セキュリティ仕様、実装ガイドラインを包括的に定義し、開発者が一貫した高品質な実装を行うための技術的指針を提供します。

## 1. システム仕様

### 1.1 環境要件

#### 実行環境
```yaml
Python Version: ">=3.12"
Platform Support:
  - macOS: ">=10.15"
  - Windows: ">=10"
  - Linux: "Ubuntu >=20.04, Fedora >=35"
Architecture: "x86_64, arm64"
Memory: "512MB以上推奨"
Storage: "100MB以上"
```

#### 依存関係
```yaml
Core Dependencies:
  tcod: ">=19.0.0"
  numpy: ">=1.26.3"
  python-dotenv: ">=1.0.0"

Development Dependencies:
  pytest: ">=8.0.0"
  pytest-cov: ">=4.0.0"
  mypy: ">=1.8.0"
  ruff: ">=0.1.0"
  pre-commit: ">=3.6.0"
```

#### パフォーマンス要件
```yaml
Minimum Requirements:
  FPS: ">=30 (ターンベースのため実質制限なし)"
  Memory Usage: "<=256MB"
  Startup Time: "<=3秒"
  Save/Load Time: "<=1秒"

Target Requirements:
  FPS: "60"
  Memory Usage: "<=128MB"
  Startup Time: "<=1秒"
  Save/Load Time: "<=0.5秒"
```

### 1.2 アーキテクチャ仕様

#### レイヤー構成

```yaml
Application Layer:
  - Description: "エントリーポイントと実行制御"
  - Components: ["main.py", "cli_engine.py", "engine.py"]
  - Responsibilities: ["アプリケーション初期化", "実行モード制御", "終了処理"]

Presentation Layer:
  - Description: "ユーザーインターフェースとプレゼンテーション"
  - Components: ["ui/screens/", "ui/components/"]
  - Responsibilities: ["画面表示", "入力処理", "レンダリング"]

Business Logic Layer:
  - Description: "ゲームロジックとビジネスルール"
  - Components: ["core/game_logic.py", "core/managers/"]
  - Responsibilities: ["ゲームルール実装", "状態管理", "計算処理"]

Domain Layer:
  - Description: "ドメインエンティティとビジネスモデル"
  - Components: ["entities/", "map/"]
  - Responsibilities: ["エンティティ定義", "ドメインルール", "不変条件"]

Infrastructure Layer:
  - Description: "外部システムとの接続"
  - Components: ["config/", "utils/", "save_manager.py"]
  - Responsibilities: ["データ永続化", "設定管理", "ユーティリティ"]
```

## 2. API設計仕様

### 2.1 コア API

#### GameLogic インターフェース

```python
class GameLogic:
    """ゲームロジックの中央制御クラス"""
    
    def __init__(self, player: Player, dungeon_manager: DungeonManager) -> None:
        """
        Args:
            player: プレイヤーエンティティ
            dungeon_manager: ダンジョン管理システム
        """
    
    def handle_player_move(self, dx: int, dy: int) -> ActionResult:
        """プレイヤー移動の処理
        
        Args:
            dx: X方向の移動量 (-1, 0, 1)
            dy: Y方向の移動量 (-1, 0, 1)
            
        Returns:
            ActionResult: 移動結果とメッセージ
            
        Raises:
            InvalidMoveError: 移動先が無効な場合
        """
    
    def handle_combat(self, attacker: Actor, target: Actor) -> CombatResult:
        """戦闘処理
        
        Args:
            attacker: 攻撃者
            target: 対象
            
        Returns:
            CombatResult: 戦闘結果（ダメージ、状態変化等）
        """
    
    def handle_item_use(self, item: Item, target: Actor | None = None) -> UseResult:
        """アイテム使用処理
        
        Args:
            item: 使用するアイテム
            target: 対象（必要に応じて）
            
        Returns:
            UseResult: 使用結果とメッセージ
        """
```

#### CommandContext プロトコル

```python
class CommandContext(Protocol):
    """コマンド実行環境の抽象化"""
    
    @property
    def game_logic(self) -> GameLogic:
        """ゲームロジックインスタンス"""
        
    @property
    def player(self) -> Player:
        """プレイヤーエンティティ"""
        
    def add_message(self, message: str) -> None:
        """メッセージの追加"""
        
    def display_player_status(self) -> None:
        """プレイヤーステータス表示"""
        
    def display_inventory(self) -> None:
        """インベントリ表示"""
        
    def display_game_state(self) -> None:
        """ゲーム状態表示"""
```

### 2.2 データ型定義

#### 基本データ型

```python
# 座標型
Position = tuple[int, int]
Direction = tuple[int, int]

# 結果型
@dataclass
class ActionResult:
    success: bool
    message: str
    energy_cost: int = 0
    turn_consumed: bool = True

@dataclass
class CombatResult:
    damage_dealt: int
    critical_hit: bool
    status_effects: list[StatusEffect]
    target_defeated: bool

@dataclass
class UseResult:
    consumed: bool
    effect_applied: bool
    message: str
    status_changes: dict[str, Any]
```

#### ゲーム状態型

```python
class GameStates(Enum):
    """ゲーム状態列挙型"""
    MENU = auto()
    PLAYERS_TURN = auto()
    ENEMY_TURN = auto()
    PLAYER_DEAD = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    SHOW_INVENTORY = auto()
    DROP_INVENTORY = auto()
    SHOW_MAGIC = auto()
    TARGETING = auto()
    DIALOGUE = auto()
    LEVEL_UP = auto()
    CHARACTER_SCREEN = auto()
    EXIT = auto()

@dataclass
class GameState:
    """ゲーム状態データ"""
    current_state: GameStates
    previous_state: GameStates | None
    turn_count: int
    floor_number: int
    message_log: list[str]
```

### 2.3 エンティティ仕様

#### Actor 基底クラス

```python
class Actor:
    """アクター（プレイヤー・モンスター）基底クラス"""
    
    def __init__(
        self,
        x: int,
        y: int,
        char: str,
        name: str,
        hp: int,
        max_hp: int,
        attack: int,
        defense: int,
        color: tuple[int, int, int] = (255, 255, 255)
    ) -> None:
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.attack = attack
        self.defense = defense
        self.color = color
        self.status_effects: list[StatusEffect] = []
    
    def take_damage(self, amount: int) -> int:
        """ダメージ処理
        
        Args:
            amount: ダメージ量
            
        Returns:
            int: 実際に受けたダメージ
        """
        actual_damage = max(1, amount)
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """回復処理
        
        Args:
            amount: 回復量
            
        Returns:
            int: 実際の回復量
        """
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp
    
    def is_alive(self) -> bool:
        """生存判定"""
        return self.hp > 0
```

#### Item システム

```python
class Item:
    """アイテム基底クラス"""
    
    def __init__(
        self,
        name: str,
        char: str,
        item_type: str,
        color: tuple[int, int, int] = (255, 255, 255),
        weight: int = 1,
        stackable: bool = False
    ) -> None:
        self.name = name
        self.char = char
        self.item_type = item_type
        self.color = color
        self.weight = weight
        self.stackable = stackable
        self.quantity = 1
        self.identified = False
    
    def use(self, user: Actor, context: 'EffectContext') -> UseResult:
        """アイテム使用
        
        Args:
            user: 使用者
            context: 効果適用コンテキスト
            
        Returns:
            UseResult: 使用結果
        """
        raise NotImplementedError
    
    def get_display_name(self) -> str:
        """表示名取得（識別状態を考慮）"""
        if self.identified:
            return self.name
        return self._get_unidentified_name()
    
    def _get_unidentified_name(self) -> str:
        """未識別時の表示名"""
        raise NotImplementedError
```

## 3. ダンジョン生成仕様

### 3.1 BSPダンジョン生成

#### アルゴリズム仕様

```python
class SectionBasedBuilder:
    """BSPアルゴリズムによるダンジョン生成"""
    
    # 定数定義
    MIN_SIZE = 5  # RogueBasin準拠の最小分割サイズ
    ROOM_MIN_SIZE = 3
    ROOM_MAX_SIZE_RATIO = 0.8  # ノードサイズに対する最大部屋サイズ比
    
    def build(self, width: int, height: int) -> np.ndarray:
        """BSPダンジョン生成メイン処理
        
        Args:
            width: ダンジョン幅
            height: ダンジョン高さ
            
        Returns:
            np.ndarray: タイル配列
            
        Raises:
            GenerationError: 生成に失敗した場合
        """
        
    def _create_bsp_tree(self, width: int, height: int) -> tcod.bsp.BSP:
        """BSP木の生成"""
        bsp = tcod.bsp.BSP(x=0, y=0, width=width, height=height)
        bsp.split_recursive(
            depth=5,
            min_width=self.MIN_SIZE,
            min_height=self.MIN_SIZE,
            max_horizontal_ratio=1.5,
            max_vertical_ratio=1.5
        )
        return bsp
    
    def _create_room_in_node(self, node: tcod.bsp.BSP) -> Room:
        """ノード内での部屋生成
        
        Args:
            node: BSPノード
            
        Returns:
            Room: 生成された部屋
        """
        max_room_width = int(node.width * self.ROOM_MAX_SIZE_RATIO)
        max_room_height = int(node.height * self.ROOM_MAX_SIZE_RATIO)
        
        room_width = random.randint(
            self.ROOM_MIN_SIZE,
            max(self.ROOM_MIN_SIZE, max_room_width)
        )
        room_height = random.randint(
            self.ROOM_MIN_SIZE,
            max(self.ROOM_MIN_SIZE, max_room_height)
        )
        
        # 部屋をノード内でランダム配置
        room_x = node.x + random.randint(1, node.width - room_width - 1)
        room_y = node.y + random.randint(1, node.height - room_height - 1)
        
        return Room(room_x, room_y, room_width, room_height)
```

#### ドア配置仕様

```python
class DoorPlacementSystem:
    """戦術的ドア配置システム"""
    
    # 配置確率
    DOOR_CLOSED_RATE = 0.6
    DOOR_OPEN_RATE = 0.3
    DOOR_SECRET_RATE = 0.1
    
    def place_doors_on_corridor(
        self,
        tiles: np.ndarray,
        corridor_path: list[Position]
    ) -> None:
        """通路上でのドア配置
        
        Args:
            tiles: タイル配列
            corridor_path: 通路経路
        """
        for x, y in corridor_path:
            if self._should_place_door(x, y):
                door_type = self._determine_door_type()
                tiles[y, x] = door_type
                self.door_positions.add((x, y))
    
    def _should_place_door(self, x: int, y: int) -> bool:
        """ドア配置判定
        
        Args:
            x: X座標
            y: Y座標
            
        Returns:
            bool: ドア配置すべきかどうか
        """
        # 部屋境界突破チェック
        if not self._is_room_boundary_wall(x, y):
            return False
        
        # 隣接ドア重複チェック
        if self._has_adjacent_door(x, y):
            return False
        
        return True
    
    def _has_adjacent_door(self, x: int, y: int) -> bool:
        """隣接8方向のドア重複チェック"""
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                if (x + dx, y + dy) in self.door_positions:
                    return True
        return False
```

### 3.2 迷路生成仕様

```python
class MazeBuilder:
    """迷路階層生成ビルダー"""
    
    MAZE_GUARANTEED_FLOORS = [7, 13, 19]
    MAZE_COMPLEXITY = 0.75  # 迷路の複雑さ（0.0-1.0）
    
    def build_maze(self, width: int, height: int) -> np.ndarray:
        """迷路生成メイン処理
        
        Args:
            width: 迷路幅
            height: 迷路高さ
            
        Returns:
            np.ndarray: 迷路タイル配列
        """
        # 初期化（すべて壁）
        tiles = np.full((height, width), TileType.WALL, dtype=np.uint8)
        
        # Recursive Backtrackingアルゴリズム
        start_x, start_y = 1, 1
        self._carve_maze(tiles, start_x, start_y, width, height)
        
        # 階段配置
        self._place_stairs(tiles)
        
        return tiles
    
    def _carve_maze(
        self,
        tiles: np.ndarray,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> None:
        """再帰的迷路彫刻"""
        tiles[y, x] = TileType.FLOOR
        
        # ランダムな方向順序で探索
        directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]
        random.shuffle(directions)
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            # 境界チェック
            if 0 < nx < width - 1 and 0 < ny < height - 1:
                if tiles[ny, nx] == TileType.WALL:
                    # 中間地点も床にする
                    tiles[y + dy // 2, x + dx // 2] = TileType.FLOOR
                    self._carve_maze(tiles, nx, ny, width, height)
```

## 4. 戦闘システム仕様

### 4.1 ダメージ計算

#### 基本ダメージ算出

```python
class CombatManager:
    """戦闘管理システム"""
    
    CRITICAL_HIT_CHANCE = 0.05
    CRITICAL_HIT_MULTIPLIER = 2.0
    MIN_DAMAGE = 1
    
    def calculate_damage(
        self,
        attacker: Actor,
        target: Actor
    ) -> CombatResult:
        """ダメージ計算メイン処理
        
        Args:
            attacker: 攻撃者
            target: 対象
            
        Returns:
            CombatResult: 戦闘結果
        """
        # 基本ダメージ計算
        base_damage = max(
            self.MIN_DAMAGE,
            attacker.attack - target.defense
        )
        
        # クリティカルヒット判定
        is_critical = random.random() < self.CRITICAL_HIT_CHANCE
        
        # 最終ダメージ
        final_damage = base_damage
        if is_critical:
            final_damage = int(base_damage * self.CRITICAL_HIT_MULTIPLIER)
        
        # 飢餓状態による修正
        if hasattr(attacker, 'hunger_level'):
            final_damage = self._apply_hunger_modifier(
                final_damage,
                attacker.hunger_level
            )
        
        return CombatResult(
            damage_dealt=final_damage,
            critical_hit=is_critical,
            status_effects=[],
            target_defeated=False
        )
    
    def _apply_hunger_modifier(
        self,
        damage: int,
        hunger_level: HungerLevel
    ) -> int:
        """飢餓状態による攻撃力修正"""
        multipliers = {
            HungerLevel.FULL: 1.0,
            HungerLevel.NORMAL: 1.0,
            HungerLevel.HUNGRY: 0.9,
            HungerLevel.STARVING: 0.7,
            HungerLevel.DYING: 0.5
        }
        return int(damage * multipliers.get(hunger_level, 1.0))
```

### 4.2 状態異常システム

```python
class StatusEffect:
    """状態異常基底クラス"""
    
    def __init__(self, duration: int) -> None:
        self.duration = duration
        self.remaining_turns = duration
    
    def apply(self, actor: Actor, context: 'EffectContext') -> None:
        """状態異常効果の適用"""
        raise NotImplementedError
    
    def tick(self) -> bool:
        """ターン経過処理
        
        Returns:
            bool: 効果が継続するかどうか
        """
        self.remaining_turns -= 1
        return self.remaining_turns > 0

class PoisonEffect(StatusEffect):
    """毒状態異常"""
    
    POISON_DAMAGE = 2
    DEFAULT_DURATION = 10
    
    def __init__(self, duration: int = DEFAULT_DURATION) -> None:
        super().__init__(duration)
    
    def apply(self, actor: Actor, context: 'EffectContext') -> None:
        """毒ダメージの適用"""
        damage = self.POISON_DAMAGE
        actor.take_damage(damage)
        context.add_message(f"{actor.name} takes {damage} poison damage!")

class ParalysisEffect(StatusEffect):
    """麻痺状態異常"""
    
    DEFAULT_DURATION = 3
    
    def apply(self, actor: Actor, context: 'EffectContext') -> None:
        """麻痺効果の適用（行動阻害）"""
        # 実際の行動阻害は入力処理側で実装
        context.add_message(f"{actor.name} is paralyzed!")
```

## 5. アイテムシステム仕様

### 5.1 スタックシステム

```python
class StackableItem(Item):
    """スタック可能アイテム"""
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.stackable = True
        self.quantity = 1
    
    def merge_with(self, other: 'StackableItem') -> bool:
        """アイテムのマージ
        
        Args:
            other: マージ対象アイテム
            
        Returns:
            bool: マージ成功かどうか
        """
        if not self.can_merge_with(other):
            return False
        
        self.quantity += other.quantity
        return True
    
    def can_merge_with(self, other: 'StackableItem') -> bool:
        """マージ可能性判定"""
        return (
            self.name == other.name and
            self.item_type == other.item_type and
            self.stackable and
            other.stackable
        )
    
    def split(self, amount: int) -> 'StackableItem | None':
        """スタック分割
        
        Args:
            amount: 分割数量
            
        Returns:
            StackableItem | None: 分割されたアイテム
        """
        if amount >= self.quantity:
            return None
        
        # 新しいアイテムインスタンス作成
        new_item = copy.deepcopy(self)
        new_item.quantity = amount
        self.quantity -= amount
        
        return new_item
    
    def get_display_name(self) -> str:
        """表示名（数量付き）"""
        base_name = super().get_display_name()
        if self.quantity > 1:
            return f"{base_name} (x{self.quantity})"
        return base_name
```

### 5.2 識別システム

```python
class IdentificationManager:
    """アイテム識別管理システム"""
    
    def __init__(self) -> None:
        self.identified_types: set[str] = set()
        self.unidentified_names: dict[str, str] = {}
        self._generate_unidentified_names()
    
    def _generate_unidentified_names(self) -> None:
        """未識別名の生成"""
        # ポーション色
        potion_colors = [
            "red", "blue", "green", "yellow", "purple", "orange",
            "black", "white", "pink", "brown", "clear", "bubbly"
        ]
        
        # 巻物呪文
        scroll_labels = [
            "ZELGO MER", "JUYED AWK", "NR 9", "XIXAXA XOXAXA",
            "LEP GEX", "PRIRUTSENIE", "ELBIB YLOH", "VERR YED"
        ]
        
        # 指輪材質
        ring_materials = [
            "wooden", "silver", "gold", "platinum", "copper",
            "iron", "bone", "crystal", "obsidian", "jade"
        ]
        
        # ランダム割り当て
        self._assign_names("POTION", potion_colors, "potion")
        self._assign_names("SCROLL", scroll_labels, "scroll labeled")
        self._assign_names("RING", ring_materials, "ring")
    
    def _assign_names(
        self,
        item_type: str,
        name_list: list[str],
        prefix: str
    ) -> None:
        """未識別名の割り当て"""
        random.shuffle(name_list)
        for i, item_name in enumerate(ITEMS_BY_TYPE[item_type]):
            if i < len(name_list):
                unidentified = f"{name_list[i]} {prefix}"
                self.unidentified_names[item_name] = unidentified
    
    def identify_item(self, item: Item) -> None:
        """アイテムの識別"""
        item.identified = True
        self.identified_types.add(item.name)
    
    def is_identified(self, item_name: str) -> bool:
        """識別済み判定"""
        return item_name in self.identified_types
    
    def get_unidentified_name(self, item_name: str) -> str:
        """未識別名の取得"""
        return self.unidentified_names.get(item_name, item_name)
```

## 6. セーブシステム仕様

### 6.1 Permadeathシステム

```python
class PermadeathManager:
    """パーマデス管理システム"""
    
    def __init__(self, save_path: str) -> None:
        self.save_path = save_path
        self.backup_path = f"{save_path}.backup"
        self.checksum_path = f"{save_path}.checksum"
    
    def save_game(self, game_data: dict[str, Any]) -> bool:
        """ゲームセーブ（チェックサム付き）
        
        Args:
            game_data: セーブデータ
            
        Returns:
            bool: セーブ成功かどうか
        """
        try:
            # バックアップ作成
            if os.path.exists(self.save_path):
                shutil.copy2(self.save_path, self.backup_path)
            
            # データシリアライズ
            serialized_data = json.dumps(game_data, indent=2)
            
            # チェックサム計算
            checksum = self._calculate_checksum(serialized_data)
            
            # セーブファイル書き込み
            with open(self.save_path, 'w', encoding='utf-8') as f:
                f.write(serialized_data)
            
            # チェックサム書き込み
            with open(self.checksum_path, 'w', encoding='utf-8') as f:
                f.write(checksum)
            
            return True
        
        except Exception as e:
            logger.error(f"Save failed: {e}")
            self._restore_backup()
            return False
    
    def load_game(self) -> dict[str, Any] | None:
        """ゲームロード（整合性チェック付き）
        
        Returns:
            dict[str, Any] | None: ロードデータ
        """
        if not os.path.exists(self.save_path):
            return None
        
        try:
            # セーブファイル読み込み
            with open(self.save_path, 'r', encoding='utf-8') as f:
                serialized_data = f.read()
            
            # チェックサム検証
            if not self._verify_checksum(serialized_data):
                logger.warning("Save file corrupted, restoring backup")
                if not self._restore_backup():
                    return None
                # バックアップから再読み込み
                with open(self.save_path, 'r', encoding='utf-8') as f:
                    serialized_data = f.read()
            
            # データデシリアライズ
            game_data = json.loads(serialized_data)
            return game_data
        
        except Exception as e:
            logger.error(f"Load failed: {e}")
            return None
    
    def delete_save_on_death(self) -> None:
        """死亡時のセーブファイル削除"""
        files_to_delete = [
            self.save_path,
            self.backup_path,
            self.checksum_path
        ]
        
        for file_path in files_to_delete:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")
    
    def _calculate_checksum(self, data: str) -> str:
        """SHA256チェックサム計算"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def _verify_checksum(self, data: str) -> bool:
        """チェックサム検証"""
        if not os.path.exists(self.checksum_path):
            return True  # チェックサムファイルがない場合は通す
        
        try:
            with open(self.checksum_path, 'r', encoding='utf-8') as f:
                stored_checksum = f.read().strip()
            
            calculated_checksum = self._calculate_checksum(data)
            return stored_checksum == calculated_checksum
        
        except Exception:
            return False
```

## 7. パフォーマンス仕様

### 7.1 描画最適化

```python
class OptimizedRenderer:
    """最適化された描画システム"""
    
    def __init__(self) -> None:
        self.dirty_rectangles: list[tuple[int, int, int, int]] = []
        self.frame_cache: dict[str, Any] = {}
        self.last_render_time = 0.0
        self.target_fps = 60
        self.frame_time = 1.0 / self.target_fps
    
    def mark_dirty(self, x: int, y: int, width: int = 1, height: int = 1) -> None:
        """描画領域を更新対象としてマーク"""
        self.dirty_rectangles.append((x, y, width, height))
    
    def render_frame(self, console: tcod.Console) -> None:
        """フレーム描画（差分描画）"""
        current_time = time.time()
        
        # フレームレート制限
        if current_time - self.last_render_time < self.frame_time:
            return
        
        # 差分描画
        if self.dirty_rectangles:
            self._render_dirty_regions(console)
            self.dirty_rectangles.clear()
        
        self.last_render_time = current_time
    
    def _render_dirty_regions(self, console: tcod.Console) -> None:
        """ダーティ領域の描画"""
        for x, y, width, height in self.dirty_rectangles:
            self._render_region(console, x, y, width, height)
    
    def _render_region(
        self,
        console: tcod.Console,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> None:
        """指定領域の描画"""
        # 具体的な描画処理
        pass
```

### 7.2 メモリ管理

```python
class MemoryManager:
    """メモリ使用量管理"""
    
    def __init__(self) -> None:
        self.memory_threshold = 256 * 1024 * 1024  # 256MB
        self.cache_size_limit = 50  # キャッシュ数制限
        self.floor_cache: dict[int, Any] = {}
    
    def get_floor_data(self, floor_number: int) -> Any:
        """フロアデータの取得（遅延読み込み）"""
        if floor_number not in self.floor_cache:
            if len(self.floor_cache) >= self.cache_size_limit:
                self._evict_old_floors()
            self.floor_cache[floor_number] = self._generate_floor(floor_number)
        
        return self.floor_cache[floor_number]
    
    def _evict_old_floors(self) -> None:
        """古いフロアデータの削除"""
        # LRU方式で古いデータを削除
        if len(self.floor_cache) > 5:  # 最低5フロアは保持
            oldest_floor = min(self.floor_cache.keys())
            del self.floor_cache[oldest_floor]
    
    def check_memory_usage(self) -> None:
        """メモリ使用量チェック"""
        import psutil
        process = psutil.Process()
        memory_usage = process.memory_info().rss
        
        if memory_usage > self.memory_threshold:
            logger.warning(f"High memory usage: {memory_usage / 1024 / 1024:.1f}MB")
            self._cleanup_memory()
    
    def _cleanup_memory(self) -> None:
        """メモリクリーンアップ"""
        # キャッシュサイズ削減
        while len(self.floor_cache) > 3:
            oldest_floor = min(self.floor_cache.keys())
            del self.floor_cache[oldest_floor]
        
        # ガベージコレクション実行
        import gc
        gc.collect()
```

## 8. セキュリティ仕様

### 8.1 データ検証

```python
class DataValidator:
    """データ検証システム"""
    
    @staticmethod
    def validate_player_data(data: dict[str, Any]) -> bool:
        """プレイヤーデータ検証"""
        required_fields = ['name', 'hp', 'max_hp', 'level', 'x', 'y']
        
        # 必須フィールドチェック
        for field in required_fields:
            if field not in data:
                return False
        
        # 値の範囲チェック
        if not (0 <= data['hp'] <= data['max_hp']):
            return False
        
        if not (1 <= data['level'] <= 50):
            return False
        
        if not (0 <= data['x'] < 80 and 0 <= data['y'] < 50):
            return False
        
        return True
    
    @staticmethod
    def validate_item_data(data: dict[str, Any]) -> bool:
        """アイテムデータ検証"""
        required_fields = ['name', 'item_type']
        
        for field in required_fields:
            if field not in data:
                return False
        
        # アイテムタイプの妥当性
        valid_types = [
            'WEAPON', 'ARMOR', 'POTION', 'SCROLL', 'FOOD', 'RING', 'GOLD'
        ]
        if data['item_type'] not in valid_types:
            return False
        
        return True
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 100) -> str:
        """文字列のサニタイゼーション"""
        # 長さ制限
        if len(text) > max_length:
            text = text[:max_length]
        
        # 特殊文字の除去
        import re
        text = re.sub(r'[^\w\s-]', '', text)
        
        return text.strip()
```

### 8.2 エラーハンドリング

```python
class ErrorHandler:
    """エラーハンドリングシステム"""
    
    def __init__(self) -> None:
        self.error_log: list[str] = []
        self.max_log_size = 1000
    
    def handle_exception(
        self,
        exception: Exception,
        context: str = ""
    ) -> None:
        """例外の適切な処理"""
        error_message = f"{context}: {type(exception).__name__}: {exception}"
        
        # ログ記録
        logger.error(error_message)
        self.error_log.append(error_message)
        
        # ログサイズ制限
        if len(self.error_log) > self.max_log_size:
            self.error_log = self.error_log[-self.max_log_size:]
        
        # エラー種別による処理分岐
        if isinstance(exception, SaveError):
            self._handle_save_error(exception)
        elif isinstance(exception, LoadError):
            self._handle_load_error(exception)
        elif isinstance(exception, GenerationError):
            self._handle_generation_error(exception)
        else:
            self._handle_generic_error(exception)
    
    def _handle_save_error(self, error: 'SaveError') -> None:
        """セーブエラーの処理"""
        # バックアップからの復旧試行
        pass
    
    def _handle_load_error(self, error: 'LoadError') -> None:
        """ロードエラーの処理"""
        # 新規ゲーム開始の提案
        pass
    
    def _handle_generation_error(self, error: 'GenerationError') -> None:
        """生成エラーの処理"""
        # 再生成の試行
        pass
    
    def _handle_generic_error(self, error: Exception) -> None:
        """一般的なエラーの処理"""
        # 安全な状態への復帰
        pass
```

## 9. テスト仕様

### 9.1 テスト戦略

#### テストピラミッド

```yaml
Integration Tests (10%):
  - Description: "統合テスト・E2Eテスト"
  - Examples: ["cli_test.sh", "ゲーム全体フロー"]
  - Coverage: "主要ワークフロー"

Unit Tests (80%):
  - Description: "単体テスト"
  - Examples: ["戦闘計算", "アイテム効果", "ダンジョン生成"]
  - Coverage: "各クラス・メソッド"

Property Tests (10%):
  - Description: "プロパティベーステスト"
  - Examples: ["ダンジョン生成不変条件", "確率的動作"]
  - Coverage: "確率的挙動・不変条件"
```

#### テストカテゴリ

```python
class TestCategories:
    """テストカテゴリ定義"""
    
    UNIT = "unit"  # 単体テスト
    INTEGRATION = "integration"  # 統合テスト
    PROPERTY = "property"  # プロパティテスト
    PERFORMANCE = "performance"  # パフォーマンステスト
    SECURITY = "security"  # セキュリティテスト
```

### 9.2 CLIテスト仕様

```bash
#!/bin/bash
# CLI統合テストスクリプト

# テストシナリオ定義
declare -A test_scenarios=(
    ["basic_movement"]="north,south,east,west,status"
    ["item_interaction"]="get,inventory,use healing_potion"
    ["combat_test"]="attack,status,inventory"
    ["magic_system"]="magic,cast heal,status"
    ["game_over_poison"]="use poison_potion,status,quit"
    ["game_over_starvation"]="wait,wait,wait,status"
    ["stairs_navigation"]="stairs down,look,stairs up"
    ["trap_interaction"]="search,disarm,move north"
    ["amulet_victory"]="teleport_to_amulet,get,stairs up"
)

# テスト実行関数
run_cli_test() {
    local test_name=$1
    local commands=$2
    
    echo "Running test: $test_name"
    
    # CLIモードでテスト実行
    echo "$commands" | python -m pyrogue.main --cli --test > test_output.txt 2>&1
    
    # 結果検証
    if validate_test_output "$test_name" "test_output.txt"; then
        echo "✅ $test_name: PASSED"
        return 0
    else
        echo "❌ $test_name: FAILED"
        return 1
    fi
}

# 出力検証関数
validate_test_output() {
    local test_name=$1
    local output_file=$2
    
    case $test_name in
        "basic_movement")
            grep -q "Player Status" "$output_file"
            ;;
        "item_interaction")
            grep -q "healing" "$output_file"
            ;;
        "combat_test")
            grep -q "damage" "$output_file"
            ;;
        "magic_system")
            grep -q "MP" "$output_file"
            ;;
        "game_over_poison")
            grep -q "died" "$output_file"
            ;;
        *)
            return 0
            ;;
    esac
}
```

## 10. 運用仕様

### 10.1 ログ仕様

```python
class GameLogger:
    """ゲーム専用ログシステム"""
    
    def __init__(self, debug_mode: bool = False) -> None:
        self.debug_mode = debug_mode
        self.setup_logging()
    
    def setup_logging(self) -> None:
        """ロガー設定"""
        logger = logging.getLogger('pyrogue')
        
        # ハンドラー設定
        if self.debug_mode:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        else:
            handler = logging.FileHandler('pyrogue.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
    
    def log_combat(
        self,
        attacker: str,
        target: str,
        damage: int,
        critical: bool = False
    ) -> None:
        """戦闘ログ"""
        crit_text = " (CRITICAL)" if critical else ""
        logger.info(f"Combat: {attacker} → {target}: {damage} damage{crit_text}")
    
    def log_dungeon_generation(
        self,
        floor: int,
        generation_time: float,
        room_count: int
    ) -> None:
        """ダンジョン生成ログ"""
        logger.info(
            f"Dungeon generated: Floor {floor}, "
            f"{generation_time:.3f}s, {room_count} rooms"
        )
    
    def log_player_action(self, action: str, result: str) -> None:
        """プレイヤー行動ログ"""
        logger.debug(f"Player action: {action} → {result}")
```

### 10.2 設定管理

```python
class ConfigManager:
    """設定管理システム"""
    
    def __init__(self, config_path: str = ".env") -> None:
        self.config_path = config_path
        self.config: dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """設定ファイル読み込み"""
        from dotenv import load_dotenv
        load_dotenv(self.config_path)
        
        # 環境変数から設定読み込み
        self.config = {
            'DEBUG': self._get_bool('DEBUG', False),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'WINDOW_WIDTH': self._get_int('WINDOW_WIDTH', 80),
            'WINDOW_HEIGHT': self._get_int('WINDOW_HEIGHT', 50),
            'FPS_LIMIT': self._get_int('FPS_LIMIT', 60),
            'AUTO_SAVE_ENABLED': self._get_bool('AUTO_SAVE_ENABLED', True),
            'SAVE_INTERVAL': self._get_int('SAVE_INTERVAL', 10),
        }
    
    def _get_bool(self, key: str, default: bool) -> bool:
        """Bool値の取得"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _get_int(self, key: str, default: int) -> int:
        """Int値の取得"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def get(self, key: str, default: Any = None) -> Any:
        """設定値の取得"""
        return self.config.get(key, default)
    
    def update(self, key: str, value: Any) -> None:
        """設定値の更新"""
        self.config[key] = value
```

## まとめ

この技術仕様書は、PyRogueプロジェクトの実装レベルでの技術的詳細を包括的に定義しています。

### 🏗️ **実装指針**
- **API設計**: 型安全性と拡張性を重視したインターフェース
- **データ構造**: 効率的で保守しやすいデータモデル  
- **エラーハンドリング**: 堅牢で回復可能なエラー処理
- **パフォーマンス**: 最適化された描画とメモリ管理

### 🔒 **品質保証**
- **テスト戦略**: 包括的なテストカバレッジ
- **セキュリティ**: データ検証とPermadeathシステム
- **運用サポート**: ログシステムと設定管理
- **モニタリング**: パフォーマンス監視と問題検出

### 📊 **技術的価値**
- **保守性**: 明確な仕様による一貫した実装
- **拡張性**: 新機能追加への対応
- **信頼性**: 堅牢なエラー処理とデータ保護
- **効率性**: 最適化されたパフォーマンス

この仕様書に従うことで、開発チームは一貫した高品質な実装を行い、PyRogueプロジェクトの技術的優秀性を維持・発展させることができます。