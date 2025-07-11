# PyRogue - アーキテクチャ設計書

## 概要

PyRogueは、モダンなソフトウェアアーキテクチャの原則に基づいて設計されたローグライクゲームです。責務分離、テスト可能性、拡張性、保守性を重視した設計により、高品質なゲーム体験と継続的な開発を可能にしています。

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
├── dungeon.py            # ダンジョン生成ファサード
├── dungeon_builder.py    # ダンジョン生成ロジック
├── dungeon_manager.py    # マルチフロア管理
├── tile.py              # タイル種別定義
└── dungeon/             # Builder Pattern実装
    ├── director.py      # ダンジョン生成ディレクター
    ├── room_builder.py  # 部屋生成ビルダー
    └── corridor_builder.py # 通路生成ビルダー
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
│   └── inventory_screen.py # インベントリ画面
└── components/          # UI コンポーネント
    ├── fov_manager.py   # 視界管理
    ├── game_renderer.py # ゲーム描画
    └── input_handler.py # 入力処理
```

## 設計パターンの活用

### 1. Builder Pattern
**適用場所**: ダンジョン生成システム
**実装**: `src/pyrogue/map/dungeon/`

```python
# ダンジョン生成の段階的構築
class DungeonDirector:
    def __init__(self):
        self.room_builder = RoomBuilder()
        self.corridor_builder = CorridorBuilder()
        self.door_manager = DoorManager()

    def build_dungeon(self, floor_number: int) -> Dungeon:
        # 段階的にダンジョンを構築
        self.room_builder.build_rooms()
        self.corridor_builder.build_corridors()
        self.door_manager.place_doors()
        return self.room_builder.get_dungeon()
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

## まとめ

PyRogueのアーキテクチャは、以下の要素を統合することで、高品質なゲーム体験と継続的な開発を可能にしています：

1. **明確な責務分離**: 各層・各クラスが明確な役割を持つ
2. **実証済みの設計パターン**: Builder、Manager、State、Commandパターンの適切な活用
3. **テスト可能な設計**: モックしやすい依存関係と層構造
4. **拡張性の考慮**: 新機能の追加が既存機能に影響しない設計
5. **型安全性**: 型ヒントによるコンパイル時エラーの防止
6. **性能最適化**: 差分描画、遅延読み込み、効率的なデータ構造

この設計により、PyRogueは単なるゲームプロジェクトではなく、Pythonゲーム開発のベストプラクティスを示す包括的な教材としても機能しています。
