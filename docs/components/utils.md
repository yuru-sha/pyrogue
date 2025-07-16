# Utils コンポーネント

PyRogueのユーティリティシステム。ロギング機能を中心とした共通機能を提供し、プロジェクト全体のデバッグ支援と品質向上を担います。

## 概要

`src/pyrogue/utils/`は、PyRogueプロジェクトの基盤となるユーティリティ機能を提供します。現在は高品質なロギングシステムを中核とし、プロジェクト全体（23ファイル）で広く活用されています。

## アーキテクチャ

### ディレクトリ構成

```
utils/
├── __init__.py          # モジュールエクスポート
└── logger.py           # メインロガー実装
```

### 設計原則

- **シンプルさ**: 理解しやすく保守しやすい設計
- **標準準拠**: Python標準loggingライブラリベース
- **環境対応**: 開発・本番環境での柔軟な制御
- **一貫性**: プロジェクト全体での統一されたログ出力

## ロギングシステム

### GameLogger クラス

プロジェクト全体で使用される統一ロガー。

```python
class GameLogger:
    """簡素化されたゲームロガークラス"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def info(self, message: str, extra: dict | None = None) -> None:
        """情報レベルログ出力"""
        extra_str = f" - {extra}" if extra else ""
        self.logger.info(f"{message}{extra_str}")

    def debug(self, message: str, extra: dict | None = None) -> None:
        """デバッグレベルログ出力"""
        extra_str = f" - {extra}" if extra else ""
        self.logger.debug(f"{message}{extra_str}")

    def warning(self, message: str, extra: dict | None = None) -> None:
        """警告レベルログ出力"""
        extra_str = f" - {extra}" if extra else ""
        self.logger.warning(f"{message}{extra_str}")

    def error(self, message: str, extra: dict | None = None) -> None:
        """エラーレベルログ出力"""
        extra_str = f" - {extra}" if extra else ""
        self.logger.error(f"{message}{extra_str}")
```

### セットアップ機能

環境に応じた動的ロガー設定。

```python
def setup_game_logger() -> logging.Logger:
    """シンプルなゲームロガーを設定"""
    logger = logging.getLogger("pyrogue")

    # 重複ハンドラー防止
    if logger.handlers:
        return logger

    # 環境変数による動的制御
    debug_mode = os.getenv("DEBUG", "0") == "1"
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # ログディレクトリの自動作成
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # ファイルハンドラー（常時有効）
    handler = logging.FileHandler(log_dir / "game.log", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # コンソールハンドラー（デバッグモード時のみ）
    if debug_mode:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
```

## 環境設定システム

### 環境変数による制御

柔軟なログレベル制御とモード切り替え。

```bash
# .env設定例
DEBUG=true              # デバッグモード有効化
LOG_LEVEL=DEBUG         # ログレベル設定（将来対応）
```

**サポートされるログレベル:**
- `DEBUG`: 詳細なデバッグ情報
- `INFO`: 一般的な情報（デフォルト）
- `WARNING`: 警告メッセージ
- `ERROR`: エラー情報

### 出力先管理

```python
# デュアル出力システム
outputs = {
    "file": "logs/game.log",      # 常時ファイル出力
    "console": debug_mode_only         # デバッグ時のみコンソール出力
}
```

## 利用状況と統計

### プロジェクト全体での活用

**利用ファイル数:** 23ファイル
**蓄積ログ行数:** 122,776行（実績）
**メインログファイルサイズ:** 10.8MB

**主要利用箇所:**
```python
# コアエンジン
core/engine.py              # メインゲームループ
core/cli_engine.py          # CLI テストエンジン

# ダンジョン生成システム（11ファイル）
map/dungeon/director.py     # ダンジョン統括管理
map/dungeon/room_builder.py # 部屋生成
map/dungeon/maze_builder.py # 迷路生成
# ... 他8ファイル

# ゲーム管理（3ファイル）
core/managers/turn_manager.py    # ターン制御
core/managers/combat_manager.py  # 戦闘システム
core/managers/item_manager.py    # アイテム管理

# エンティティシステム
entities/items/light_items.py    # 光源アイテム管理
```

### ログフォーマット

```
# 標準ログフォーマット
2025-07-13 13:30:32,296 - pyrogue - INFO - TCOD BSP dungeon built: 10 rooms
2025-07-13 13:30:32,297 - pyrogue - DEBUG - Dungeon generation completed for floor 5
2025-07-13 13:30:32,298 - pyrogue - INFO - Game started - {'player': 'test'}
```

## 使用パターン

### 基本的な使用方法

```python
from pyrogue.utils import game_logger

# 基本ログ出力
game_logger.info("Game started")
game_logger.debug("Player moved to position (10, 5)")
game_logger.warning("Low health detected")
game_logger.error("Failed to load save file")
```

### 構造化データ付きログ

```python
# 追加データでの詳細記録
game_logger.info("Player leveled up", {
    "old_level": 3,
    "new_level": 4,
    "experience": 1250
})

game_logger.debug("Dungeon generated", {
    "floor": 5,
    "rooms": 8,
    "type": "BSP"
})
```

### デバッグモードでの活用

```python
# 開発時の詳細トレース
def generate_dungeon(self, floor: int) -> list[list[Tile]]:
    game_logger.debug(f"Starting dungeon generation for floor {floor}")

    tiles = self._create_base_structure()
    game_logger.debug(f"Base structure created: {len(tiles)}x{len(tiles[0])}")

    rooms = self._generate_rooms()
    game_logger.debug(f"Generated {len(rooms)} rooms")

    return tiles
```

## ファイルローテーション

### 現在の状況

```bash
# 実際のログファイル構成
logs/
├── game.log      (10.8MB - アクティブ)
├── game.log.1    (1.9KB)
├── game.log.2    (1.1KB)
├── game.log.3    (340B)
├── game.log.4    (948B)
└── game.log.5    (577B)
```

**注意:** 現在は手動または外部ツールによるローテーション。将来的には自動ローテーション機能の実装予定。

### ローテーション戦略

```python
# 将来実装予定の自動ローテーション
rotation_config = {
    "max_size": "10MB",
    "backup_count": 5,
    "when": "midnight"  # 日次ローテーション
}
```

## デバッグ支援機能

### 環境別モード切り替え

```python
# 開発環境での詳細ログ
if debug_mode:
    game_logger.debug("Detailed monster AI calculation")
    game_logger.debug(f"Player stats: HP={player.hp}, Level={player.level}")

# 本番環境では重要な情報のみ
game_logger.info("Game session started")
game_logger.warning("Performance degradation detected")
```

### エラートレーシング

```python
try:
    save_manager.save_game(context)
    game_logger.info("Game saved successfully")
except Exception as e:
    game_logger.error(f"Save failed: {str(e)}", {
        "player_level": context.player.level,
        "current_floor": context.current_floor,
        "error_type": type(e).__name__
    })
```

### パフォーマンス監視

```python
import time

def generate_dungeon_with_logging(self, floor: int):
    start_time = time.time()
    game_logger.info(f"Starting dungeon generation for floor {floor}")

    result = self._generate_dungeon(floor)

    elapsed = time.time() - start_time
    game_logger.info(f"Dungeon generation completed", {
        "floor": floor,
        "elapsed_time": f"{elapsed:.3f}s",
        "room_count": len(result.rooms)
    })

    return result
```

## パフォーマンス特性

### 現在の実装影響

**メモリ使用量:**
- 最小限のメモリ使用（バッファリングなし）
- ハンドラー数は最大2個（ファイル + コンソール）

**I/O 特性:**
- 各ログ出力毎のファイル書き込み
- UTF-8エンコーディング対応
- ディスク容量の適度な使用（10.8MB/長期使用）

**CPU オーバーヘッド:**
- 文字列フォーマット処理
- 環境変数チェック（初期化時のみ）
- ログレベル判定（効率的）

### パフォーマンス最適化

```python
# 効率的なデバッグログ
if game_logger.logger.isEnabledFor(logging.DEBUG):
    expensive_debug_info = calculate_complex_stats()
    game_logger.debug(f"Complex stats: {expensive_debug_info}")
```

## 拡張ガイド

### 新しいログレベルの追加

```python
class ExtendedGameLogger(GameLogger):
    """拡張ログレベル対応"""

    def trace(self, message: str, extra: dict | None = None) -> None:
        """トレースレベルログ（TRACE = 5）"""
        if self.logger.isEnabledFor(5):
            extra_str = f" - {extra}" if extra else ""
            self.logger.log(5, f"{message}{extra_str}")

    def performance(self, message: str, timing_data: dict) -> None:
        """パフォーマンス専用ログ"""
        self.info(f"PERF: {message}", timing_data)
```

### JSON形式ログの実装

```python
import json

class JSONGameLogger(GameLogger):
    """JSON形式ログ出力"""

    def info(self, message: str, extra: dict | None = None) -> None:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": message,
            "extra": extra or {}
        }
        self.logger.info(json.dumps(log_entry))
```

### 自動ローテーション実装

```python
from logging.handlers import RotatingFileHandler

def setup_rotating_logger() -> logging.Logger:
    """自動ローテーション対応ロガー"""
    logger = logging.getLogger("pyrogue")

    # ローテーションハンドラー
    handler = RotatingFileHandler(
        "logs/game.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
```

### カスタムフィルター

```python
class GameComponentFilter(logging.Filter):
    """ゲームコンポーネント別フィルタリング"""

    def __init__(self, component: str):
        super().__init__()
        self.component = component

    def filter(self, record: logging.LogRecord) -> bool:
        return self.component in record.getMessage()

# 使用例
dungeon_filter = GameComponentFilter("dungeon")
handler.addFilter(dungeon_filter)
```

## セキュリティ考慮事項

### ログデータの保護

```python
# 機密情報の除外
def sanitize_log_data(data: dict) -> dict:
    """ログデータのサニタイズ"""
    sensitive_keys = ["password", "secret", "token"]
    return {
        k: "***HIDDEN***" if k in sensitive_keys else v
        for k, v in data.items()
    }

game_logger.info("User action", sanitize_log_data(user_data))
```

### ログファイルアクセス制御

```python
# ログファイルの権限設定
log_file = Path("logs/game.log")
if log_file.exists():
    log_file.chmod(0o600)  # 所有者のみ読み書き可能
```

## トラブルシューティング

### よくある問題

**ログファイルが作成されない:**
```python
# ディレクトリ権限の確認
log_dir = Path("logs")
try:
    log_dir.mkdir(parents=True, exist_ok=True)
    game_logger.info("Log directory created successfully")
except PermissionError:
    print("Error: Cannot create log directory. Check permissions.")
```

**ログ出力されない:**
```python
# ログレベルの確認
current_level = game_logger.logger.getEffectiveLevel()
print(f"Current log level: {logging.getLevelName(current_level)}")

# 強制的にログレベル設定
game_logger.logger.setLevel(logging.DEBUG)
```

**パフォーマンス問題:**
```python
# 同期I/Oから非同期I/Oへの切り替え検討
# または、バッファリング機能の追加
```

## 品質保証

### テストでの活用

```python
def test_logging_functionality():
    """ログ機能のテスト"""
    with patch('pyrogue.utils.logger.game_logger') as mock_logger:
        game_function_that_logs()
        mock_logger.info.assert_called_with("Expected message")
```

### ログ分析

```bash
# ログ統計の取得
grep "ERROR" logs/game.log | wc -l
grep "WARNING" logs/game.log | wc -l

# パフォーマンス分析
grep "PERF:" logs/game.log | tail -20
```

## まとめ

Utils コンポーネントは、PyRogueプロジェクトの基盤として以下の価値を提供します：

- **統一性**: プロジェクト全体での一貫したログ出力
- **柔軟性**: 環境に応じた動的な制御機能
- **拡張性**: 将来の機能追加に対応できる設計
- **実用性**: 23ファイル、122,776行の実績が示す高い実用性
- **保守性**: シンプルで理解しやすい実装

現在のシンプルで効果的な実装は、プロジェクトの成長と共に段階的な拡張が可能な堅実な基盤を提供しています。標準Python loggingライブラリベースの設計により、高い互換性と将来への拡張性を両立しています。
