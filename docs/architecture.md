---
cache_control: {"type": "ephemeral"}
---
# PyRogue - アーキテクチャ設計書

## 概要

PyRogueは、モダンなソフトウェアアーキテクチャの原則に基づいて設計されたローグライクゲームです。責務分離、テスト可能性、拡張性、保守性を重視した設計により、高品質なゲーム体験と継続的な開発を可能にしています。

**v0.1.0（2025年7月17日）**では、Handler Patternの導入により、さらなるモジュラー設計と拡張性を実現しました。

## アーキテクチャの基本原則

### 1. 責務分離 (Separation of Concerns)
- 各クラスが単一の責任を持つ
- ビジネスロジックとUIの分離
- データとロジックの分離

### 2. テスト可能性 (Testability)
- 依存関係の注入
- モックしやすい設計
- CLI/GUIモードの両方をサポート

### 3. 拡張性 (Extensibility)
- 新機能の追加が容易
- 既存機能の変更が他に影響しない
- プラグイン可能な設計

### 4. 保守性 (Maintainability)
- 明確な型ヒント
- 包括的なドキュメント
- 一貫したコーディング規約

## 全体アーキテクチャ

### レイヤー構成

```
┌─────────────────────────────────────────────────┐
│                   UI Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │ MenuScreen  │  │ GameScreen  │  │ Other    │ │
│  │             │  │             │  │ Screens  │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│                Business Logic Layer              │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │ GameLogic   │  │ Managers    │  │ Handlers │ │
│  │             │  │             │  │          │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│                  Entity Layer                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │ Actors      │  │ Items       │  │ Magic    │ │
│  │             │  │             │  │ Traps    │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│                   Data Layer                    │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │ Map/Tiles   │  │ Save Data   │  │ Config   │ │
│  │             │  │             │  │          │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────────────────────────────────────┘
```

### 主要コンポーネント

#### 1. Core (コア)
**役割**: ゲームエンジン、状態管理、入力処理の中核
**場所**: `src/pyrogue/core/`

```
core/
├── engine.py              # メインゲームエンジン
├── cli_engine.py          # CLIモード用エンジン
├── game_states.py         # ゲーム状態列挙
├── game_logic.py          # ゲームロジック管理
├── input_handlers.py      # 入力処理
├── save_manager.py        # セーブ・ロード
├── command_handler.py     # 共通コマンドハンドラー（v0.1.0）
├── auto_explore_handler.py # 自動探索ハンドラー（v0.1.0）
├── debug_command_handler.py # デバッグコマンドハンドラー（v0.1.0）
├── save_load_handler.py   # セーブ・ロードハンドラー（v0.1.0）
├── info_command_handler.py # 情報表示ハンドラー（v0.1.0）
└── managers/              # 各種マネージャー
    ├── game_context.py    # 共有コンテキスト
    ├── turn_manager.py    # ターン管理
    ├── combat_manager.py  # 戦闘管理
    └── monster_ai_manager.py # モンスターAI管理
```

#### 2. Entities (エンティティ)
**役割**: ゲーム内オブジェクトの定義と管理
**場所**: `src/pyrogue/entities/`

```
entities/
├── actors/                # プレイヤー・モンスター
│   ├── player.py         # プレイヤークラス
│   ├── monster.py        # モンスタークラス
│   ├── inventory.py      # インベントリ管理
│   └── status_effects.py # 状態異常システム
├── items/                # アイテム
│   ├── item.py          # アイテム基底クラス
│   ├── item_types.py    # アイテム種別定義
│   └── effects.py       # アイテム効果システム
├── magic/                # 魔法
│   └── spells.py        # 魔法システム
└── traps/                # トラップ
    └── trap.py          # トラップシステム
```

#### 3. Map (マップ)
**役割**: ダンジョン生成、タイル定義、階層管理
**場所**: `src/pyrogue/map/`

```
map/
├── dungeon.py               # ダンジョン生成ファサード
├── dungeon_builder.py       # ダンジョン生成ロジック
├── dungeon_manager.py       # マルチフロア管理
├── tile.py                  # タイル種別定義
└── dungeon/                # Builder Pattern実装
    ├── director.py         # ダンジョン生成ディレクター
    ├── section_based_builder.py # BSPダンジョン生成ビルダー
    ├── maze_builder.py     # 迷路階層生成ビルダー
    └── room_builder.py     # 部屋生成ビルダー
```

#### 4. UI (ユーザーインターフェース)
**役割**: 画面管理、描画処理、ユーザーインターフェース
**場所**: `src/pyrogue/ui/`

```
ui/
├── screens/              # 画面システム
│   ├── screen.py        # 画面基底クラス
│   ├── menu_screen.py   # メインメニュー
│   ├── game_screen.py   # ゲームプレイ画面
│   ├── inventory_screen.py # インベントリ画面
│   ├── magic_screen.py  # 魔法詠唱画面
│   ├── game_over_screen.py # ゲームオーバー画面
│   ├── victory_screen.py # 勝利画面
│   └── dialogue_screen.py # NPC対話画面
└── components/          # UI コンポーネント
    ├── fov_manager.py   # 視界管理
    ├── game_renderer.py # ゲーム描画
    ├── input_handler.py # 入力処理
    └── save_load_manager.py # セーブ・ロード管理
```

## 設計パターンの活用

### 1. Handler Pattern (v0.1.0新規導入)
**適用場所**: コマンド処理システム
**実装**: `src/pyrogue/core/command_handler.py` + 専用ハンドラー群

Handler Patternは、機能別の専用ハンドラーによってコマンド処理を分離し、保守性と拡張性を向上させる設計パターンです。

#### アーキテクチャ構造
```
CommonCommandHandler (コア)
├── AutoExploreHandler     # 自動探索機能
├── DebugCommandHandler    # デバッグコマンド
├── SaveLoadHandler        # セーブ・ロード処理
└── InfoCommandHandler     # 情報表示機能
```

#### 実装例
```python
class CommonCommandHandler:
    def __init__(self, context: CommandContext) -> None:
        self.context = context
        # 遅延初期化によるメモリ効率化
        self._auto_explore_handler = None
        self._debug_handler = None
        self._save_load_handler = None
        self._info_handler = None

    def handle_command(self, command: str, args: list[str] | None = None) -> CommandResult:
        if command in ["auto_explore", "O"]:
            return self._get_auto_explore_handler().handle_auto_explore()
        if command == "debug":
            return self._get_debug_handler().handle_debug_command(args)
        # ...

    def _get_auto_explore_handler(self):
        """自動探索ハンドラーを取得（遅延初期化）"""
        if self._auto_explore_handler is None:
            self._auto_explore_handler = AutoExploreHandler(self.context)
        return self._auto_explore_handler
```

#### 利点
- **責務分離**: 各機能を専用ハンドラーに分離
- **拡張性**: 新機能は新ハンドラー追加で対応
- **保守性**: 修正範囲が明確に限定される
- **テスト性**: 各ハンドラーを独立してテスト可能
- **再利用性**: CLI/GUIで同一ハンドラーを共有

### 2. Builder Pattern
**適用場所**: ダンジョン生成システム
**実装**: `src/pyrogue/map/dungeon/`

```python
# BSPダンジョン生成の段階的構築
class DungeonDirector:
    def __init__(self):
        self.bsp_builder = SectionBasedBuilder()
        self.maze_builder = MazeBuilder()

    def build_dungeon(self, floor_number: int) -> Dungeon:
        # フロア番号に応じてビルダーを選択
        dungeon_type = self._determine_dungeon_type(floor_number)

        if dungeon_type == "maze":
            return self.maze_builder.build(self.width, self.height)
        else:
            # BSPダンジョン生成
            return self._build_bsp_dungeon()

    def _build_bsp_dungeon(self) -> Dungeon:
        # BSPアルゴリズムによる段階的構築
        self.bsp_builder.initialize_bsp_tree()
        self.bsp_builder.create_rooms_from_nodes()
        self.bsp_builder.connect_rooms_with_corridors()
        self.bsp_builder.place_doors_at_boundaries()
        return self.bsp_builder.get_dungeon()
```

**利点**:
- 複雑な生成プロセスを段階的に管理
- 生成パラメータの変更が容易
- 新しい生成ルールの追加が容易

### 2. Manager Pattern
**適用場所**: ゲームロジック管理
**実装**: `src/pyrogue/core/managers/`

```python
class GameLogic:
    def __init__(self):
        self.turn_manager = TurnManager()
        self.combat_manager = CombatManager()
        self.monster_ai_manager = MonsterAIManager()

    def process_turn(self):
        # 各マネージャーが責務を分担
        self.turn_manager.advance_turn()
        self.monster_ai_manager.process_monsters()
        self.combat_manager.resolve_combat()
```

**利点**:
- 複雑な処理を機能別に分割
- 個別のテストが容易
- 機能の追加・修正が局所的

### 3. State Pattern
**適用場所**: ゲーム状態管理
**実装**: `src/pyrogue/core/game_states.py`

```python
class GameState(Enum):
    MENU = auto()
    PLAYER_TURN = auto()
    MONSTER_TURN = auto()
    GAME_OVER = auto()
    VICTORY = auto()

class StateManager:
    def __init__(self):
        self.current_state = GameState.MENU
        self.state_handlers = {
            GameState.MENU: self.handle_menu,
            GameState.PLAYER_TURN: self.handle_player_turn,
            # ...
        }
```

**利点**:
- 状態遷移の明確化
- 状態固有の処理を分離
- 新しい状態の追加が容易

### 4. Command Pattern
**適用場所**: 状態異常、魔法効果、コマンド統一化
**実装**: `src/pyrogue/entities/actors/status_effects.py`, `src/pyrogue/core/command_handler.py`

```python
class StatusEffect:
    def apply(self, actor: 'Actor', context: EffectContext) -> None:
        """状態異常の効果を適用"""
        pass

class PoisonEffect(StatusEffect):
    def apply(self, actor: 'Actor', context: EffectContext) -> None:
        damage = self.calculate_damage()
        actor.take_damage(damage)
```

**コマンド統一化の実装**:
```python
class CommonCommandHandler:
    def handle_command(self, command: str, args: list[str] = None) -> CommandResult:
        """共通コマンド処理"""
        if command == "move":
            return self._handle_move_command(args)
        elif command == "get":
            return self._handle_get_item()
        # 他のコマンド処理...

class CommandContext(Protocol):
    """コマンド実行環境の抽象化"""
    @property
    def game_logic(self) -> GameLogic: ...
    def add_message(self, message: str) -> None: ...
```

**利点**:
- 効果の実行と定義を分離
- 新しい効果の追加が容易
- 効果の組み合わせが可能
- **GUIとCLIで統一されたコマンド処理**
- **コマンド実行環境の抽象化**

## 新実装システムアーキテクチャ

### 1. BSPダンジョン生成システム

**概要**: RogueBasinチュートリアル準拠のBinary Space Partitioning実装

```python
class SectionBasedBuilder:
    """BSPアルゴリズムによるダンジョン生成"""

    def build(self, width: int, height: int) -> np.ndarray:
        # BSP木による再帰的空間分割
        bsp = tcod.bsp.BSP(x=0, y=0, width=width, height=height)
        bsp.split_recursive(depth=5, min_width=self._min_size, min_height=self._min_size)

        # 各葉ノードに部屋を生成
        self._process_nodes(bsp, tiles)

        return tiles

    def _process_nodes(self, node: tcod.bsp.BSP, tiles: np.ndarray) -> None:
        """ノード巡回による部屋生成と接続"""
        if node.level == 0:  # 葉ノード
            self._create_room(node, tiles)
        else:  # 非葉ノード
            self._connect_children(node, tiles)
```

**主要特徴**:
- 再帰的空間分割による自然な部屋配置
- 部屋中心間のL字型通路接続
- 全部屋の接続保証

### 2. 高度なドア配置システム

**概要**: 戦術的に意味のある位置でのドア配置と重複防止

```python
class DoorPlacementSystem:
    """戦術的ドア配置システム"""

    def _place_corridor_tile(self, tiles: np.ndarray, x: int, y: int) -> None:
        if self._is_room_boundary_wall(x, y) and not self._has_adjacent_door(x, y):
            door = self._create_random_door()  # 60%閉・30%開・10%隠し
            tiles[y, x] = door
            self.door_positions.add((x, y))

    def _is_room_boundary_wall(self, x: int, y: int) -> bool:
        """部屋の境界（外周）突破判定"""
        for room in self.rooms:
            if self._is_wall_on_room_perimeter(x, y, room):
                return True
        return False

    def _has_adjacent_door(self, x: int, y: int) -> bool:
        """隣接8方向のドア重複チェック"""
        for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
            if (x + dx, y + dy) in self.door_positions:
                return True
        return False
```

**主要特徴**:
- 部屋境界突破箇所のみでドア配置
- 隣接8方向の重複ドア防止
- 確率的ドア状態（クローズド・オープン・隠し扉）

### 3. トラップ探索・解除システム

**概要**: 安全な踏まずに処理システム

```python
class TrapSystem:
    """トラップ探索・解除システム"""

    def search_trap(self, x: int, y: int) -> bool:
        """隣接トラップの安全探索"""
        for trap in floor_data.trap_spawner.traps:
            if trap.x == x and trap.y == y and trap.is_hidden:
                success_rate = min(90, 40 + player.level * 5)  # レベル依存成功率
                if random.randint(1, 100) <= success_rate:
                    trap.reveal()
                    return True
        return False

    def disarm_trap(self, x: int, y: int) -> bool:
        """発見済みトラップの安全解除"""
        for trap in floor_data.trap_spawner.traps:
            if trap.x == x and trap.y == y and not trap.is_hidden:
                return trap.disarm(context)  # 70%成功率、失敗時30%発動
        return False
```

**主要特徴**:
- 隣接8方向からの安全な探索・解除
- プレイヤーレベル依存の成功率
- 発見→解除の段階的処理

### 4. ウィザードモード（デバッグシステム）

**概要**: 包括的な開発・テスト支援システム

```python
class WizardMode:
    """統合デバッグシステム"""

    def toggle_wizard_mode(self) -> None:
        """ウィザードモード切り替え"""
        self.wizard_mode = not self.wizard_mode
        from pyrogue.config.env import get_debug_mode
        if get_debug_mode():  # 環境変数連携
            self.wizard_mode = True

    # 可視化機能
    def render_with_wizard_info(self, console: tcod.Console) -> None:
        if self.wizard_mode:
            self._render_all_map()      # FOV無視全表示
            self._render_hidden_doors() # 隠し扉表示
            self._render_all_traps()    # 全トラップ表示

    # 無敵機能
    def apply_damage_with_wizard_check(self, damage: int) -> None:
        if self.wizard_mode:
            context.add_message(f"[Wizard] Damage {damage} blocked!")
        else:
            player.hp -= damage
```

**主要特徴**:
- 可視化（全マップ・隠し要素・エンティティ表示）
- 無敵機能（ダメージ・トラップ無効化）
- 操作機能（テレポート・レベルアップ・全回復・全探索）
- 環境変数連携（DEBUG=true自動有効化）

## データフロー

### 1. ゲームループのデータフロー

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Input     │───▶│  GameLogic  │───▶│   Render    │
│  Handler    │    │   Manager   │    │   System    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │                   ▼                   │
       │            ┌─────────────┐            │
       │            │   Entities  │            │
       │            │  (Player,   │            │
       │            │ Monsters,   │            │
       │            │  Items)     │            │
       │            └─────────────┘            │
       │                   │                   │
       │                   ▼                   │
       │            ┌─────────────┐            │
       │            │   Dungeon   │            │
       │            │    Map      │            │
       │            └─────────────┘            │
       │                                       │
       └──────────────────────────────────────────┘
```

### 2. 戦闘システムのデータフロー

```
Player Action ─────┐
                   │
                   ▼
            ┌─────────────┐
            │   Combat    │
            │  Manager    │
            └─────────────┘
                   │
                   ▼
            ┌─────────────┐
            │   Damage    │
            │ Calculation │
            └─────────────┘
                   │
                   ▼
            ┌─────────────┐
            │   Status    │
            │  Effects    │
            └─────────────┘
                   │
                   ▼
            ┌─────────────┐
            │   Monster   │
            │    AI       │
            └─────────────┘
```

## 依存関係の管理

### 1. 依存関係の方向

```
UI Layer ──────────────────▶ Business Logic Layer
                                       │
                                       ▼
Business Logic Layer ──────────▶ Entity Layer
                                       │
                                       ▼
Entity Layer ──────────────────▶ Data Layer
```

### 2. 依存関係注入の例

```python
class GameScreen:
    def __init__(self, game_logic: GameLogic):
        self.game_logic = game_logic  # 依存関係注入

    def process_input(self, action: Action):
        # UIがビジネスロジックを呼び出す
        self.game_logic.process_action(action)
```

## テストアーキテクチャ

### 1. テストの層構造

```
┌─────────────────────────────────────────────────┐
│                Integration Tests                │
│  ゲーム全体のワークフローテスト                      │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│                  Unit Tests                     │
│  個別クラス・メソッドのテスト                       │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│                Property Tests                   │
│  確率的生成の検証テスト                           │
└─────────────────────────────────────────────────┘
```

### 2. テストダブルの活用

```python
class MockDungeon:
    """テスト用のダンジョンモック"""
    def __init__(self):
        self.width = 80
        self.height = 50
        self.tiles = self.create_test_tiles()

class TestCombatManager:
    def test_combat_calculation(self):
        # モックを使用したテスト
        mock_player = MockPlayer(attack=10, defense=5)
        mock_monster = MockMonster(attack=8, defense=3)

        combat_manager = CombatManager()
        result = combat_manager.calculate_damage(mock_player, mock_monster)

        assert result == 5  # 10 - 5 = 5
```

## 性能に関する考慮

### 1. 描画最適化

```python
class GameRenderer:
    def __init__(self):
        self.dirty_tiles = set()  # 更新が必要なタイルのみ描画

    def render(self, console: tcod.Console):
        # 差分描画による最適化
        for x, y in self.dirty_tiles:
            self.render_tile(console, x, y)
        self.dirty_tiles.clear()
```

### 2. メモリ管理

```python
class DungeonManager:
    def __init__(self):
        self.floors = {}  # 階層の遅延読み込み

    def get_floor(self, floor_number: int) -> Dungeon:
        if floor_number not in self.floors:
            self.floors[floor_number] = self.generate_floor(floor_number)
        return self.floors[floor_number]
```

## コマンド統一化アーキテクチャ

### 概要
PyRogueは、GUIとCLIの両エンジンで統一されたコマンド処理を実現するアーキテクチャを採用しています。これにより、インターフェースに関係なく一貫したゲーム操作を提供します。

### アーキテクチャ構成

```
┌─────────────────────────────────────────────────────────────┐
│                   Interface Layer                          │
│  ┌─────────────────┐      ┌─────────────────┐               │
│  │   CLI Engine    │      │   GUI Engine    │               │
│  │ CLICommandContext │    │ GUICommandContext │             │
│  └─────────────────┘      └─────────────────┘               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Command Handler Layer                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │          CommonCommandHandler                          │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │ │
│  │  │   Movement  │ │   Actions   │ │ Information │     │ │
│  │  │   Commands  │ │   Commands  │ │   Commands  │     │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 GameLogic                               │ │
│  │  handle_player_move() handle_get_item()                │ │
│  │  handle_combat() handle_use_item() ...                 │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 主要コンポーネント

#### 1. CommandContext (抽象化レイヤー)
```python
class CommandContext(Protocol):
    """コマンド実行環境の統一インターフェース"""
    @property
    def game_logic(self) -> GameLogic: ...
    @property
    def player(self) -> Player: ...
    def add_message(self, message: str) -> None: ...
    def display_player_status(self) -> None: ...
    def display_inventory(self) -> None: ...
    def display_game_state(self) -> None: ...
```

#### 2. CommonCommandHandler (共通処理レイヤー)
```python
class CommonCommandHandler:
    """GUIとCLIで共通のコマンド処理"""
    def handle_command(self, command: str, args: list[str]) -> CommandResult:
        # 統一されたコマンド処理ロジック
        if command in ["move", "north", "south", "east", "west"]:
            return self._handle_move_command(command, args)
        elif command in ["get", "pickup", "g"]:
            return self._handle_get_item()
        # ... 他のコマンド処理
```

#### 3. 実装クラス
- **CLICommandContext**: CLI環境での実装
- **GUICommandContext**: GUI環境での実装

### 統一されたコマンドセット

| カテゴリ | コマンド | エイリアス | 説明 |
|----------|----------|------------|------|
| **移動** | move \<direction\> | north/n, south/s, east/e, west/w | 方向移動 |
| **アクション** | get | g | アイテム取得 |
| | use \<item\> | u | アイテム使用 |
| | attack | a | 攻撃 |
| | open | o | 扉を開く |
| | close | c | 扉を閉じる |
| | search | s | 隠し扉探索 |
| | disarm | d | トラップ解除 |
| | stairs \<up/down\> | | 階段使用 |
| **情報** | status | stat | ステータス表示 |
| | inventory | inv, i | インベントリ表示 |
| | look | l | 周囲確認 |
| **システム** | help | | ヘルプ表示 |
| | quit | exit, q | ゲーム終了 |

### キー入力の統一化

#### GUI環境でのキー→コマンド変換
```python
def _key_to_command(self, event: tcod.event.KeyDown) -> str | None:
    """キーイベントをコマンド文字列に変換"""
    key = event.sym

    # viキー + 矢印キー対応
    if key in (ord('h'), tcod.event.KeySym.LEFT):
        return "west"
    elif key in (ord('j'), tcod.event.KeySym.DOWN):
        return "south"
    # ... 他のキーマッピング
```

### 利点

1. **一貫性**: GUIとCLIで同じコマンドセット
2. **保守性**: コマンド処理の共通化によりバグ修正が一箇所で完了
3. **拡張性**: 新しいコマンドの追加が両環境で自動適用
4. **テスト性**: 共通ロジックの単一テストで両環境をカバー

## 拡張性の設計

### 1. プラグイン可能な設計

```python
class ItemEffect:
    """アイテム効果の基底クラス"""
    def apply(self, target: Actor, context: EffectContext) -> None:
        pass

class HealingEffect(ItemEffect):
    def apply(self, target: Actor, context: EffectContext) -> None:
        target.heal(self.amount)

# 新しい効果の追加が容易
class TeleportEffect(ItemEffect):
    def apply(self, target: Actor, context: EffectContext) -> None:
        target.teleport_random()
```

### 2. 設定による動作変更

```python
class GameConfig:
    """ゲーム設定の集中管理"""
    DUNGEON_DEPTH = 26
    PLAYER_STARTING_HP = 100
    MONSTER_SPAWN_RATE = 0.15

    @classmethod
    def load_from_file(cls, filename: str) -> 'GameConfig':
        # 設定ファイルからの読み込み
        pass
```

## セキュリティ・セーフティの考慮

### 1. 型安全性

```python
from typing import Protocol, TypeVar, Generic

class Actor(Protocol):
    """アクターの共通インターフェース"""
    def take_damage(self, amount: int) -> None: ...
    def heal(self, amount: int) -> None: ...

T = TypeVar('T', bound=Actor)

class StatusEffect(Generic[T]):
    """型安全な状態異常システム"""
    def apply(self, target: T) -> None: ...
```

### 2. エラーハンドリング

```python
class GameError(Exception):
    """ゲーム固有のエラー基底クラス"""
    pass

class InvalidMoveError(GameError):
    """無効な移動エラー"""
    pass

class CombatManager:
    def process_attack(self, attacker: Actor, target: Actor) -> None:
        try:
            damage = self.calculate_damage(attacker, target)
            target.take_damage(damage)
        except InvalidMoveError as e:
            logger.warning(f"Invalid attack: {e}")
            # 適切な回復処理
```

## 開発・運用の支援

### 1. ログ・デバッグ

```python
class GameLogger:
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.setup_logging()

    def log_combat(self, attacker: str, target: str, damage: int):
        if self.debug_mode:
            logger.debug(f"Combat: {attacker} → {target} ({damage} damage)")
```

### 2. 開発モード

```python
class Engine:
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        if debug_mode:
            self.enable_debug_features()

    def enable_debug_features(self):
        # FOV表示、座標表示、無敵モードなど
        pass
```

## UIシステム詳細設計

### アーキテクチャ概要

PyRogueのUIシステムは、**状態駆動型アーキテクチャ**と**責務分離による組み込み型設計**を採用しています。TCODライブラリを基盤とした文字ベースの描画システムで、レスポンシブ対応と高いユーザビリティを実現しています。

### 主要設計原則

1. **状態ベースの画面管理**: GameStates列挙型による明確な状態遷移
2. **コンポーネント化**: 単一責務の原則に基づく機能分離
3. **統一された入力処理**: Vi-keys、矢印キー、テンキーの包括的サポート
4. **レスポンシブ描画**: ウィンドウサイズに適応する動的レイアウト

### 画面システム

#### Screen基底クラス設計

```python
class Screen:
    """画面の基本クラス"""
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def render(self, console: Console) -> None:
        """画面を描画"""
        raise NotImplementedError

    def handle_key(self, key: tcod.event.KeyDown) -> Screen | None:
        """キー入力を処理"""
        raise NotImplementedError
```

**設計思想**:
- 最小限のインターフェース定義
- 各画面の独立性確保
- エンジンへの参照による状態アクセス

#### 画面クラス構成

| 画面クラス | 責務 | 主要機能 |
|------------|------|----------|
| **MenuScreen** | メインメニュー表示 | アスキーアートタイトル、ナビゲーション |
| **GameScreen** | ゲームプレイ統合管理 | コンポーネント統合、状態中継 |
| **InventoryScreen** | インベントリ管理 | アイテム表示、装備操作、使用・ドロップ |
| **MagicScreen** | 魔法詠唱メニュー | 魔法一覧、MP管理、ターゲット選択連携 |
| **GameOverScreen** | ゲームオーバー表示 | 統計情報、スコア表示、死因表示 |
| **VictoryScreen** | 勝利画面表示 | 最終スコア計算、達成統計表示 |

### 状態管理システム

#### GameStates列挙型

```python
class GameStates(Enum):
    MENU = auto()                # メインメニュー表示中
    PLAYERS_TURN = auto()        # プレイヤーの入力待ち
    ENEMY_TURN = auto()          # 敵の行動処理中
    PLAYER_DEAD = auto()         # プレイヤー死亡時の処理
    GAME_OVER = auto()           # ゲームオーバー画面表示
    VICTORY = auto()             # ゲーム勝利画面表示
    SHOW_INVENTORY = auto()      # インベントリ一覧表示
    DROP_INVENTORY = auto()      # アイテム破棄モード
    SHOW_MAGIC = auto()          # 魔法一覧表示
    TARGETING = auto()           # ターゲット選択モード
    DIALOGUE = auto()            # NPC対話状態
    LEVEL_UP = auto()           # レベルアップ時の選択
    CHARACTER_SCREEN = auto()    # キャラクター情報表示
    EXIT = auto()               # ゲーム終了シグナル
```

#### StateManager（入力ルーティング）

```python
class StateManager:
    """異なるゲーム状態に対する入力処理を管理"""

    def handle_input(self, event: tcod.event.KeyDown,
                    current_state: GameStates,
                    context: Any) -> tuple[bool, GameStates | None]:
        # 状態別の入力処理を適切な画面に委譲
        if current_state == GameStates.MENU:
            new_state = context.handle_input(event)
        elif current_state == GameStates.PLAYERS_TURN:
            context.handle_key(event)
        # ... 他の状態処理
```

**利点**:
- 状態遷移の一元管理
- 入力処理の責務分離
- エスケープキーのフォールバック処理

### UIコンポーネントシステム

#### 1. GameRenderer（描画システム）

```python
class GameRenderer:
    """ゲーム画面の描画処理を担当するクラス"""

    def render(self, console: tcod.Console) -> None:
        """レイヤー化描画"""
        console.clear()
        self._render_map(console)      # マップ層
        self._render_status(console)   # ステータス層
        self._render_messages(console) # メッセージ層
```

**主要機能**:
- **レイヤー化描画**: マップ→ステータス→メッセージの順序描画
- **FOV統合**: 可視/探索済み状態による動的描画制御
- **マップオフセット**: ステータス行を考慮した座標調整
- **エンティティ描画**: アイテム、モンスター、NPCの統合描画

**色彩システム**:
```python
# 視界状態による色彩変化
color = (130, 110, 50) if visible else (0, 0, 100)  # 壁
color = (192, 192, 192) if visible else (64, 64, 64)  # 床
```

#### 2. InputHandler（入力処理システム）

```python
class InputHandler:
    """入力処理システムの管理クラス"""

    def handle_key(self, event: tcod.event.KeyDown) -> None:
        if self.targeting_mode:
            self._handle_targeting_key(event)
        else:
            self._handle_normal_key(event)
```

**入力マッピング**:
```python
movement_keys = {
    # Vi-keys
    ord('h'): (-1, 0),  ord('j'): (0, 1),   ord('k'): (0, -1),  ord('l'): (1, 0),
    ord('y'): (-1, -1), ord('u'): (1, -1),  ord('b'): (-1, 1),  ord('n'): (1, 1),
    # 矢印キー
    tcod.event.KeySym.LEFT: (-1, 0), tcod.event.KeySym.RIGHT: (1, 0),
    tcod.event.KeySym.UP: (0, -1),   tcod.event.KeySym.DOWN: (0, 1),
    # テンキー
    tcod.event.KeySym.KP_4: (-1, 0), tcod.event.KeySym.KP_6: (1, 0),
    tcod.event.KeySym.KP_8: (0, -1), tcod.event.KeySym.KP_2: (0, 1),
    tcod.event.KeySym.KP_7: (-1, -1), tcod.event.KeySym.KP_9: (1, -1),
    tcod.event.KeySym.KP_1: (-1, 1), tcod.event.KeySym.KP_3: (1, 1),
}
```

**特殊機能**:
- **ターゲット選択モード**: 魔法詠唱時のターゲット指定
- **修飾キー対応**: Ctrl+S/L（セーブ・ロード）、Shift+./,（階段）
- **周囲検索**: ドア開閉、隠し扉探索、トラップ解除の8方向検索

#### 3. FOVManager（視界管理システム）

```python
class FOVManager:
    """FOV（視界）システムの管理クラス"""

    def update_fov(self) -> None:
        if not self.fov_enabled:
            self.visible.fill(True)  # FOV無効時は全体可視
            return

        self._update_fov_map()
        player = self.game_screen.player
        if player:
            self._compute_fov(player.x, player.y)
```

**技術詳細**:
- **TCODアルゴリズム**: `libtcodpy.FOV_SHADOW`による高精度視界計算
- **暗い部屋対応**: 光源アイテムによる視界半径変動
- **探索システム**: 累積的な探索済みエリア管理
- **透明度マップ**: 壁・ドアの状態による動的透明度設定

**効果的FOV半径計算**:
```python
def _calculate_effective_fov_radius(self, x: int, y: int) -> int:
    # 基本半径: 8
    # 暗い部屋での制限: 2-3
    # 光源アイテム使用時: 基本半径復帰
    return dark_room_builder.get_visibility_range_at(
        x, y, rooms, has_light, light_radius
    )
```

#### 4. SaveLoadManager（状態永続化システム）

```python
class SaveLoadManager:
    """セーブ・ロード処理の管理クラス"""

    def save_game(self) -> bool:
        save_data = self._create_save_data()
        return self.save_manager.save_game(save_data)

    def _create_save_data(self) -> dict[str, Any]:
        return {
            "player": self._serialize_player(player),
            "inventory": self._serialize_inventory(inventory),
            "current_floor": dungeon_manager.current_floor,
            "floor_data": dungeon_manager.floor_data,
            "message_log": game_logic.message_log,
        }
```

**シリアライゼーション機能**:
- プレイヤー状態の完全保存
- インベントリ・装備情報の詳細保存
- フロアデータの遅延読み込み対応
- メッセージログの継続性確保

### TCODライブラリ統合

#### 初期化とコンテキスト管理

```python
class Engine:
    def initialize(self) -> None:
        # フォントとタイルセット
        tileset = tcod.tileset.load_tilesheet(
            "assets/fonts/dejavu10x10_gs_tc.png",
            32, 8, tcod.tileset.CHARMAP_TCOD
        )

        # リサイズ対応コンテキスト
        self.context = tcod.context.new(
            columns=self.screen_width,
            rows=self.screen_height,
            tileset=tileset,
            title=self.title,
            vsync=True,
            sdl_window_flags=tcod.context.SDL_WINDOW_RESIZABLE,
        )
```

#### ウィンドウリサイズ対応

```python
def handle_resize(self, event: tcod.event.WindowEvent) -> None:
    pixel_width = getattr(event, "width", 800)
    pixel_height = getattr(event, "height", 600)

    # 文字数計算
    self.screen_width = max(MIN_SCREEN_WIDTH, pixel_width // font_width)
    self.screen_height = max(MIN_SCREEN_HEIGHT, pixel_height // font_height)

    # コンソール再作成
    self.console = tcod.console.Console(self.screen_width, self.screen_height)

    # 各画面のコンソール参照更新
    self.menu_screen.update_console(self.console)
    self.game_screen.update_console(self.console)
```

### パフォーマンス最適化

#### 1. 描画最適化

- **差分描画**: 変更されたタイルのみ更新
- **FOVベース描画**: 視界外のエンティティ描画を省略
- **レイヤー分離**: マップ、エンティティ、UIの独立レンダリング

#### 2. メモリ効率

- **遅延生成**: フロアデータの必要時生成
- **状態キャッシュ**: 探索済みエリアの効率的格納
- **リソース管理**: 不要なコンソール参照の適切な解放

### ユーザビリティ設計

#### 1. アクセシビリティ

- **多様な入力方式**: Vi-keys、矢印キー、テンキーの包括サポート
- **色彩コントラスト**: 視認性を考慮した色彩選択
- **レスポンシブレイアウト**: 画面サイズに適応するUI要素配置

#### 2. 操作の一貫性

- **共通ナビゲーション**: 全画面での矢印キー+Enterパターン
- **ESCキーの統一**: 一段階戻る動作の一貫性
- **ヘルプ表示**: ?キーによるコンテキストヘルプ

#### 3. 視覚的フィードバック

- **選択状態の明示**: ハイライト表示による現在選択位置の明確化
- **装備状態表示**: 装備中アイテムの視覚的区別
- **ステータス色分け**: HP/MP残量による色彩変化

### 既知の技術的課題

#### 1. 入力処理の修正中問題
- **場所**: `src/pyrogue/ui/components/input_handler.py`
- **問題**: キーボード入力処理の一部で不具合
- **影響**: 特定のキー組み合わせで期待通りの動作がしない

#### 2. 大規模マップでのレンダリングパフォーマンス
- **問題**: マップサイズ拡大時の描画処理負荷
- **対策候補**: 視界ベースのカリング、タイル描画最適化

#### 3. 複雑なゲーム状態のシリアライゼーション
- **問題**: セーブデータの一貫性保証
- **課題**: フロアデータ、エンティティ状態の完全復元

## まとめ

PyRogueのアーキテクチャは、以下の要素を統合することで、高品質なゲーム体験と継続的な開発を可能にしています：

1. **明確な責務分離**: 各層・各クラスが明確な役割を持つ
2. **実証済みの設計パターン**: Builder、Manager、State、Commandパターンの適切な活用
3. **テスト可能な設計**: モックしやすい依存関係と層構造
4. **拡張性の考慮**: 新機能の追加が既存機能に影響しない設計
5. **型安全性**: 型ヒントによるコンパイル時エラーの防止
6. **性能最適化**: 差分描画、遅延読み込み、効率的なデータ構造

この設計により、PyRogueは単なるゲームプロジェクトではなく、Pythonゲーム開発のベストプラクティスを示す包括的な教材としても機能しています。
