# Core コンポーネント

PyRogueのゲームエンジンとコアシステム。ゲームループ、状態管理、入力処理、セーブ・ロード機能を統合管理します。

## 概要

`src/pyrogue/core/`は、PyRogueの心臓部となるゲームエンジンシステムです。GUI/CLIの両対応、ターンベース制御、責務分離されたマネージャーアーキテクチャにより、堅牢で拡張性の高いゲームループを実現しています。

## アーキテクチャ

### ファイル構成

```
core/
├── __init__.py
├── engine.py               # メインゲームエンジン (GUI)
├── cli_engine.py          # CLIテスト用エンジン
├── game_logic.py          # ゲームロジック統合管理
├── game_states.py         # ゲーム状態定義
├── input_handlers.py      # 入力処理システム
├── save_manager.py        # セーブ・ロード機能
├── score_manager.py       # スコアランキング
└── managers/              # 専門マネージャー群
    ├── game_context.py    # 共有コンテキスト
    ├── turn_manager.py    # ターン制御
    ├── combat_manager.py  # 戦闘システム
    ├── monster_ai_manager.py # モンスターAI
    ├── movement_manager.py   # 移動処理
    ├── item_manager.py      # アイテム管理
    ├── floor_manager.py     # フロア管理
    ├── dialogue_manager.py  # 対話システム
    └── trading_manager.py   # 取引システム
```

### 設計原則

- **責務分離**: 各マネージャーが単一責任を持つ
- **依存関係注入**: GameContextによる統一的な依存管理
- **状態管理**: 明確なゲーム状態とその遷移
- **テスタビリティ**: CLI対応による自動テスト可能性

## 主要コンポーネント

### エンジンシステム

#### Engine (GUI版エンジン)

PyRogueのメインゲームエンジン。フルグラフィカルUIとリアルタイム操作を提供。

**主要機能:**
- **レンダリングエンジン**: TCOD使用のフルグラフィカルUI
- **イベント処理**: リアルタイムなキー入力とウィンドウイベント処理
- **画面管理**: 複数画面状態の統合管理
- **リサイズ対応**: 動的ウィンドウサイズ変更サポート

**ゲームループ実装:**
```python
def main_loop(self) -> None:
    """メインゲームループ"""
    while self.running:
        tcod.console_clear(self.root_console)
        self._render_current_state()
        tcod.console_flush()
        self._process_events()
        self._update_game_state()
```

#### CLIEngine (テスト・自動化用エンジン)

テストと自動化に特化したコマンドライン版エンジン。

**特徴:**
- **テキストベース**: コマンド入力による操作
- **自動化対応**: スクリプト実行可能な設計
- **簡素化UI**: 標準出力によるステータス表示
- **デバッグ機能**: 開発用デバッグコマンド豊富

**使用例:**
```python
cli_engine = CLIEngine()
cli_engine.start_new_game()
cli_engine.execute_command("move south")
cli_engine.execute_command("get item")
```

### ゲーム状態管理

#### GameStates (game_states.py)

ゲーム全体の状態を型安全に定義。

```python
class GameStates(Enum):
    MENU = auto()           # メニュー画面
    PLAYERS_TURN = auto()   # プレイヤーターン
    ENEMY_TURN = auto()     # 敵ターン
    PLAYER_DEAD = auto()    # プレイヤー死亡
    GAME_OVER = auto()      # ゲームオーバー
    VICTORY = auto()        # 勝利
    SHOW_INVENTORY = auto() # インベントリ表示
    DROP_INVENTORY = auto() # アイテムドロップ
    SHOW_MAGIC = auto()     # 魔法画面
    TARGETING = auto()      # ターゲット選択
    DIALOGUE = auto()       # 対話
    LEVEL_UP = auto()       # レベルアップ
    CHARACTER_SCREEN = auto() # キャラクター画面
    EXIT = auto()           # 終了
```

### 統合管理システム

#### GameLogic (game_logic.py)

ゲーム全体のビジネスロジックを統合管理する調整役（Coordinator）。

**設計転換:**
- **リファクタリング前**: モノリシックな巨大クラス
- **リファクタリング後**: 責務分離された専門マネージャーの統合

**統合管理機能:**
```python
class GameLogic:
    def __init__(self, game_context: GameContext):
        # 各専門マネージャーの初期化
        self.movement_manager = MovementManager(game_context)
        self.combat_manager = CombatManager(game_context)
        self.item_manager = ItemManager(game_context)
        self.floor_manager = FloorManager(game_context)
        # ... 他のマネージャー
```

### 入力処理システム

#### InputHandlers (input_handlers.py)

GUI/CLI両対応の統一入力処理システム。

**アーキテクチャ:**
- **StateManager**: ゲーム状態別入力処理
- **CommonCommandHandler**: 共通コマンド処理
- **Strategy Pattern**: 状態別ハンドリング

**実装例:**
```python
def handle_input(self, key: tcod.event.KeyDown) -> Optional[Action]:
    """状態に応じた入力処理"""
    current_state = self.game_logic.game_state

    if current_state == GameStates.PLAYERS_TURN:
        return self._handle_player_turn(key)
    elif current_state == GameStates.SHOW_INVENTORY:
        return self._handle_inventory(key)
    # ... 他の状態処理
```

### 永続化システム

#### SaveManager (save_manager.py)

Permadeathシステムに対応したセーブ・ロード機能。

**重要機能:**
```python
class SaveManager:
    def save_game(self, game_context: GameContext) -> bool:
        """ゲーム状態の保存"""
        # セーブデータの生成
        # SHA256チェックサムによる整合性保証
        # メイン/バックアップの二重保存

    def delete_save_on_death(self) -> None:
        """Permadeath: 死亡時のセーブデータ削除"""
        # 真のローグライクゲーム体験の実現
```

**Permadeath実装:**
- 死亡時の自動セーブデータ削除
- 改ざん検出によるチート防止
- バックアップ機能による安全性

#### ScoreManager (score_manager.py)

ランキングシステムとゲーム記録管理。

**記録項目:**
- プレイヤー名、レベル、階層到達度
- ゴールド獲得量、モンスター撃破数
- ゲーム結果（勝利/死亡）とその詳細

**機能:**
```python
def record_score(self, game_context: GameContext,
                death_reason: str = None, victory: bool = False) -> None:
    """スコア記録"""
    score_entry = {
        "player_name": game_context.player.name,
        "level": game_context.player.level,
        "floor": game_context.dungeon_manager.current_floor,
        "gold": game_context.player.gold,
        "monsters_killed": game_context.player.monsters_killed,
        "result": "Victory" if victory else f"Died: {death_reason}",
        "timestamp": datetime.now().isoformat()
    }
```

## Manager アーキテクチャ

### GameContext (共有コンテキスト)

全マネージャー間の共有データハブ。依存関係注入のコンテナ役割。

```python
@dataclass
class GameContext:
    """ゲーム全体の共有コンテキスト"""
    player: Player
    inventory: Inventory
    dungeon_manager: DungeonManager
    message_log: MessageLog
    game_state: GameStates = GameStates.PLAYERS_TURN
    turn_count: int = 0
```

### 専門マネージャー群

#### TurnManager (ターン制御)

**責務:**
- ターン進行制御
- ステータス異常処理
- 満腹度システム更新
- MP自然回復処理

**ターン処理フロー:**
```python
def execute_turn(self) -> None:
    """1ターンの実行"""
    self._process_status_effects()    # 状態異常処理
    self._update_hunger_system()      # 満腹度更新
    self._process_mp_regeneration()   # MP回復
    self._check_win_condition()       # 勝利条件確認
    self._increment_turn_counter()    # ターン数増加
```

#### CombatManager (戦闘システム)

**責務:**
- 戦闘処理とダメージ計算
- レベルアップシステム
- モンスタードロップ処理
- 死亡判定

#### MonsterAIManager (モンスターAI)

**責務:**
- AI行動決定
- 視界判定
- 特殊攻撃実行
- 分裂処理

**AI行動パターン:**
```python
def execute_monster_ai(self, monster: Monster) -> None:
    """モンスターAI実行"""
    if self._can_see_player(monster):
        if self._is_adjacent_to_player(monster):
            self._attack_player(monster)
        else:
            self._move_towards_player(monster)
    else:
        self._random_movement(monster)
```

#### MovementManager (移動処理)

**責務:**
- 移動処理と衝突判定
- 移動後イベント（アイテム自動取得等）
- 階段移動トリガー

#### ItemManager (アイテム管理)

**責務:**
- アイテム取得・使用・装備
- ドロップ処理
- 呪われたアイテム制御

#### FloorManager (フロア管理)

**責務:**
- 階層移動処理
- 扉操作（開閉）
- 隠し扉探索
- トラップ処理

## ゲームループ詳細

### メインゲームループ (Engine)

```python
def main_loop(self) -> None:
    """統合ゲームループ"""
    while self.running:
        # 1. 画面クリア
        tcod.console_clear(self.root_console)

        # 2. 現在状態のレンダリング
        self._render_current_state()

        # 3. 画面更新
        tcod.console_flush()

        # 4. イベント処理
        self._process_events()

        # 5. ゲーム状態更新
        self._update_game_state()
```

### ターン制御フロー

```
Player Action Input
        ↓
Action Validation
        ↓
Execute Player Action
        ↓
Process Status Effects
        ↓
Execute Monster Turns
        ↓
Update Systems (Hunger, MP)
        ↓
Check Win/Lose Conditions
        ↓
Increment Turn Counter
        ↓
[Loop continues]
```

## 依存関係注入とテスタビリティ

### 依存関係注入パターン

```python
class GameLogic:
    def __init__(self, game_context: GameContext):
        """依存関係の注入"""
        self.game_context = game_context

        # 各マネージャーに共通コンテキストを注入
        self.turn_manager = TurnManager(game_context)
        self.combat_manager = CombatManager(game_context)
        self.movement_manager = MovementManager(game_context)
```

### テスタビリティ向上策

**CLIEngine活用:**
```python
def test_combat_system():
    """戦闘システムのテスト"""
    cli_engine = CLIEngine()
    cli_engine.start_new_game()

    # モンスターとの戦闘をシミュレート
    cli_engine.execute_command("move north")  # モンスターに近づく
    cli_engine.execute_command("attack")      # 攻撃実行

    # 結果の検証
    assert cli_engine.game_logic.game_context.player.health > 0
```

**モック対応:**
```python
# Protocol定義による抽象化
class GameContextProtocol(Protocol):
    player: Player
    dungeon_manager: DungeonManager

# テストでのモック利用
def test_movement_manager():
    mock_context = create_mock_game_context()
    movement_manager = MovementManager(mock_context)
    # テスト実行...
```

## 使用パターン

### 基本的なゲーム開始

```python
from pyrogue.core.engine import Engine

# ゲームエンジンの初期化
engine = Engine()

# ゲームループ開始
engine.run()
```

### CLIモードでのテスト

```python
from pyrogue.core.cli_engine import CLIEngine

# CLIエンジンでの自動テスト
cli = CLIEngine()
cli.start_new_game()

# 自動的なゲームプレイ
commands = ["move north", "get gold", "move east", "attack"]
for command in commands:
    cli.execute_command(command)
```

### マネージャーの個別利用

```python
# 戦闘システムの直接利用
combat_manager = CombatManager(game_context)
damage = combat_manager.calculate_damage(attacker, defender)
combat_manager.apply_damage(defender, damage)
```

## 拡張ガイド

### 新しいマネージャーの追加

1. **マネージャークラスの作成**
```python
class NewFeatureManager:
    def __init__(self, game_context: GameContext):
        self.game_context = game_context

    def execute_new_feature(self) -> None:
        """新機能の実行"""
        pass
```

2. **GameLogicへの統合**
```python
class GameLogic:
    def __init__(self, game_context: GameContext):
        # 既存マネージャー...
        self.new_feature_manager = NewFeatureManager(game_context)
```

### 新しいゲーム状態の追加

```python
class GameStates(Enum):
    # 既存状態...
    NEW_STATE = auto()
```

### カスタムコマンドの追加

```python
def handle_custom_command(self, command: str) -> bool:
    """カスタムコマンドの処理"""
    if command == "custom_action":
        self._execute_custom_action()
        return True
    return False
```

## パフォーマンス最適化

### 効率的なレンダリング

- 差分更新による描画最適化
- 視界外オブジェクトの描画スキップ
- コンソールバッファリングの活用

### メモリ管理

- オブジェクトプールパターンの活用
- 不要なオブジェクトの早期解放
- 循環参照の回避

## トラブルシューティング

### よくある問題

**状態遷移の問題:**
```python
# 状態が正しく設定されているか確認
if game_logic.game_state != expected_state:
    logger.warning(f"Unexpected state: {game_logic.game_state}")
```

**マネージャー間の依存関係:**
```python
# GameContextの正しい共有を確認
assert all_managers_share_same_context(game_context)
```

### デバッグ支援

```python
# ゲーム状態のダンプ
def dump_game_state(game_context: GameContext) -> dict:
    """デバッグ用のゲーム状態出力"""
    return {
        "player_pos": (game_context.player.x, game_context.player.y),
        "health": game_context.player.health,
        "level": game_context.player.level,
        "current_floor": game_context.dungeon_manager.current_floor,
        "game_state": game_context.game_state.name
    }
```

## まとめ

Core コンポーネントは、PyRogueプロジェクトの中核として以下の価値を提供します：

- **統合管理**: 複雑なゲームロジックの整理された統合
- **責務分離**: 保守性と拡張性を高める明確な役割分担
- **テスタビリティ**: CLI対応による包括的な自動テスト
- **状態管理**: 型安全で明確なゲーム状態制御
- **永続化**: Permadeathとランキングによる本格ローグライク体験

この設計により、オリジナルRogueの複雑なゲームメカニクスを現代的なソフトウェア設計パターンで実現し、高い品質と保守性を両立したゲームエンジンを提供しています。
