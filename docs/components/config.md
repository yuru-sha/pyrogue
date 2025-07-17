# Config コンポーネント

PyRogueの設定管理システム。環境変数とゲーム設定の統合管理を担当します。

## 概要

`src/pyrogue/config/`は、現代的な環境変数管理と後方互換性を両立した設定システムです。`.env`ファイルによる外部設定、型安全なアクセスAPI、レガシーシステムとの統合を提供します。

## アーキテクチャ

### ファイル構成

```
config/
├── __init__.py      # 統合APIの提供
├── env.py           # 現代的な環境変数管理
└── legacy.py        # 後方互換性維持
```

### 設計原則

- **型安全性**: 環境変数の型変換とバリデーション
- **後方互換性**: 既存のCONFIGインターフェースの維持
- **責務分離**: 環境変数管理とゲーム設定の分離
- **拡張性**: 新しい設定項目の容易な追加
- **Handler Pattern連携**: v0.1.0のHandler Patternとの統合設計

## 主要コンポーネント

### EnvConfig クラス (env.py)

環境変数の読み込みと型安全なアクセスを提供する中核クラス。

#### 機能

**自動的な.envファイル探索**
```python
def load_env(self, env_file: str | Path | None = None) -> None:
    """
    .envファイルを自動探索・読み込み
    指定がない場合、現在ディレクトリから親に向かって探索
    """
```

**型安全な値取得API**
```python
def get_bool(self, key: str, default: bool = False) -> bool:
    """真偽値として取得（true/1/yes/onを真として認識）"""

def get_int(self, key: str, default: int = 0) -> int:
    """整数値として取得（変換エラー時はdefault返却）"""

def get_float(self, key: str, default: float = 0.0) -> float:
    """浮動小数点値として取得（変換エラー時はdefault返却）"""
```

#### 実装例

```python
from pyrogue.config.env import env_config

# 環境変数の読み込み
env_config.load_env()

# 型安全なアクセス
debug_mode = env_config.get_bool("DEBUG", False)
window_width = env_config.get_int("WINDOW_WIDTH", 80)
log_level = env_config.get("LOG_LEVEL", "INFO")
```

### アクセサー関数

設定項目ごとの専用アクセサー関数を提供し、タイポ防止と一元管理を実現。

```python
def get_debug_mode() -> bool:
    """デバッグモードの設定を取得"""
    return env_config.get_bool("DEBUG", False)

def get_log_level() -> str:
    """ログレベルの設定を取得"""
    return env_config.get("LOG_LEVEL", "INFO")

def get_auto_save_enabled() -> bool:
    """オートセーブ機能の設定を取得"""
    return env_config.get_bool("AUTO_SAVE_ENABLED", True)
```

### レガシー設定 (legacy.py)

後方互換性を維持するため、既存のDataClass構造とグローバル`CONFIG`インスタンスを提供。

```python
@dataclass
class GameConfig:
    """メインゲーム設定"""
    display: DisplayConfig = field(default_factory=DisplayConfig)
    player: PlayerConfig = field(default_factory=PlayerConfig)
    monster: MonsterConfig = field(default_factory=MonsterConfig)
    item: ItemConfig = field(default_factory=ItemConfig)

# グローバル設定インスタンス
CONFIG = GameConfig()
```

## 対応設定項目

### 環境変数 (.env)

| 変数名 | 型 | デフォルト値 | 説明 |
|--------|----|-----------:|------|
| `DEBUG` | bool | false | デバッグモード |
| `LOG_LEVEL` | str | INFO | ログレベル |
| `SAVE_DIRECTORY` | str | saves | セーブディレクトリ |
| `AUTO_SAVE_ENABLED` | bool | true | オートセーブ |
| `FONT_PATH` | str | auto | フォントファイルパス |

### ゲーム定数

`legacy.py`を通じて以下の定数群を管理：

- **CombatConstants**: 戦闘関連の定数
- **GameConstants**: ゲーム全般の定数
- **HungerConstants**: 飢餓システムの定数
- **ItemConstants**: アイテム関連の定数
- **ProbabilityConstants**: 確率値の定数

## 使用パターン

### 基本的な使用方法

```python
from pyrogue.config.env import (
    env_config,
    get_debug_mode,
    get_auto_save_enabled,
    get_log_level
)

# 環境設定の初期化
env_config.load_env()

# 型安全なアクセス
if get_debug_mode():
    print(f"Debug mode enabled, auto save: {get_auto_save_enabled()}")
    print(f"Log level: {get_log_level()}")
```

### レガシーAPIの継続利用

```python
from pyrogue.config import CONFIG

# 既存コードとの互換性
display_config = CONFIG.display
player_config = CONFIG.player
```

### .envファイル設定例

```bash
# .env
DEBUG=true
LOG_LEVEL=DEBUG
AUTO_SAVE_ENABLED=false
```

## エラー処理

### 型変換エラーの安全な処理

```python
# 不正な値が設定されていてもクラッシュしない
window_width = env_config.get_int("WINDOW_WIDTH", 80)  # 変換エラー時は80を返却
debug_mode = env_config.get_bool("DEBUG", False)       # 不正値時はFalseを返却
```

### ファイル不在時の処理

```python
# .envファイルが存在しなくてもエラーにならない
env_config.load_env()  # デフォルト値で動作継続
```

## テスト戦略

### 単体テストでの活用

```python
def test_env_config():
    """環境設定のテスト"""
    config = EnvConfig()

    # モック環境変数での検証
    with patch.dict(os.environ, {"DEBUG": "true", "WINDOW_WIDTH": "100"}):
        config.load_env()
        assert config.get_bool("DEBUG") is True
        assert config.get_int("WINDOW_WIDTH") == 100
```

## 拡張ガイド

### 新しい環境変数の追加

1. **アクセサー関数の定義**
```python
def get_new_setting() -> str:
    """新しい設定項目の取得"""
    return env_config.get("NEW_SETTING", "default_value")
```

2. **.env.exampleの更新**
```bash
NEW_SETTING=default_value
```

3. **ドキュメントの更新**
上記の対応設定項目テーブルに追加

### レガシー設定の拡張

```python
@dataclass
class NewConfig:
    """新しい設定カテゴリ"""
    new_option: str = "default"

@dataclass
class GameConfig:
    # 既存設定...
    new_category: NewConfig = field(default_factory=NewConfig)
```

## 技術的特徴

### 現代的なPython機能

- **Union型**: `str | Path | None`による型安全性
- **dataclass**: 設定構造の簡潔な定義
- **pathlib**: ファイルパス操作の現代的な手法

### 依存関係

- **python-dotenv**: .envファイル読み込み
- **pathlib**: ファイルパス操作
- **dataclasses**: 設定構造定義

### パフォーマンス特性

- **遅延読み込み**: 必要時にのみ.envファイルを読み込み
- **キャッシュ**: 一度読み込んだ設定値はos.environに保存
- **軽量**: 最小限の依存関係とメモリ使用量

## Handler Pattern連携（v0.1.0）

### Handler Patternでの設定活用

各Handlerは環境設定を適切に参照し、機能の可用性を制御します：

```python
class DebugCommandHandler:
    def __init__(self, context: CommandContext):
        self.context = context
        self.debug_enabled = get_debug_mode()

    def handle_debug_command(self, args: list[str]) -> CommandResult:
        """デバッグコマンド処理（設定依存）"""
        if not self.debug_enabled:
            return CommandResult.failure("Debug mode is disabled")

        # デバッグ機能の実行
        return self._execute_debug_action(args)
```

### 設定ベースの機能制御

```python
class SaveLoadHandler:
    def handle_auto_save(self) -> CommandResult:
        """オートセーブ処理（設定依存）"""
        if not get_auto_save_enabled():
            return CommandResult.success("Auto-save disabled")

        # オートセーブの実行
        return self._perform_auto_save()
```

### ハンドラー初期化時の設定注入

```python
class CommonCommandHandler:
    def __init__(self, context: CommandContext):
        self.context = context
        # 設定値に基づくハンドラー初期化制御
        self._init_handlers_based_on_config()

    def _init_handlers_based_on_config(self):
        """設定に基づくハンドラー初期化"""
        if get_debug_mode():
            self._debug_handler = DebugCommandHandler(self.context)
        else:
            self._debug_handler = None
```

## まとめ

Config コンポーネントは、PyRogueプロジェクトの設定管理において以下の価値を提供します：

- **開発効率**: .envファイルによる環境依存設定の外部化
- **型安全性**: 実行時エラーを防ぐ型安全なAPI
- **保守性**: 後方互換性を保ちながらの段階的移行
- **拡張性**: 新しい設定項目の容易な追加
- **Handler Pattern統合**: v0.1.0のHandler Patternとの完全な連携

この設計により、開発・テスト・本番環境での設定管理が統一され、プロジェクトの成長に対応できる柔軟なシステムを実現しています。
