# PyRogue 開発者ガイド

このドキュメントでは、PyRogueの開発に必要な情報を提供します。

## 目次

1. [開発環境のセットアップ](#開発環境のセットアップ)
2. [プロジェクト構造](#プロジェクト構造)
3. [設定管理](#設定管理)
4. [開発ワークフロー](#開発ワークフロー)
5. [テスト](#テスト)
6. [コーディング規約](#コーディング規約)

## 開発環境のセットアップ

### 必要条件

- Python 3.12以上
- uv（パッケージマネージャー）
- make（ビルドツール）

### セットアップ手順

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/pyrogue.git
cd pyrogue

# 開発環境のセットアップ
make setup
```

## プロジェクト構造

```
pyrogue/
├── docs/               # ドキュメント
├── data/              # ゲームデータ
│   ├── assets/        # アセット（フォント、画像など）
│   └── logs/          # ログファイル
├── src/               # ソースコード
│   └── pyrogue/
│       ├── core/      # コアゲームロジック
│       ├── entities/  # ゲーム内エンティティ
│       ├── map/       # マップ生成
│       ├── ui/        # ユーザーインターフェース
│       └── utils/     # ユーティリティ
└── tests/             # テストコード
```

## 設定管理

ゲームの設定は`config.py`で一元管理されています。設定は以下の方法で上書きできます：

1. 環境変数による設定：
```bash
export PYROGUE_SCREEN_WIDTH=100
export PYROGUE_SCREEN_HEIGHT=60
make run
```

2. コードでの設定：
```python
from pyrogue.config import GameConfig

config = GameConfig(
    screen_width=100,
    screen_height=60
)
engine = Engine(config)
```

### 利用可能な設定項目

| 設定項目 | 環境変数 | デフォルト値 | 説明 |
|----------|----------|--------------|------|
| 画面幅 | PYROGUE_SCREEN_WIDTH | 80 | ゲーム画面の幅（文字数） |
| 画面高さ | PYROGUE_SCREEN_HEIGHT | 50 | ゲーム画面の高さ（文字数） |
| マップ幅 | PYROGUE_MAP_WIDTH | 80 | ゲームマップの幅 |
| マップ高さ | PYROGUE_MAP_HEIGHT | 43 | ゲームマップの高さ |
| ダンジョン幅 | PYROGUE_DUNGEON_WIDTH | 80 | ダンジョンの幅 |
| ダンジョン高さ | PYROGUE_DUNGEON_HEIGHT | 45 | ダンジョンの高さ |
| タイトル | PYROGUE_TITLE | "PyRogue" | ウィンドウタイトル |
| フォントパス | PYROGUE_FONT_PATH | "data/assets/fonts/dejavu10x10_gs_tc.png" | フォントファイルのパス |
| デバッグモード | PYROGUE_DEBUG | false | デバッグモードの有効/無効 |

## 開発ワークフロー

1. 新機能の開発：
```bash
# 新しいブランチを作成
git checkout -b feature/new-feature

# コードの変更
make watch-format  # 自動フォーマット
make watch-test   # 自動テスト

# 変更のコミット
git add .
git commit -m "Add new feature"
```

2. コードの検証：
```bash
make lint    # リンターとタイプチェック
make test    # テストの実行
```

## テスト

テストは`pytest`を使用して実行します：

```bash
# 全てのテストを実行
make test

# 特定のテストを実行
pytest tests/test_specific.py

# カバレッジレポートの生成
pytest --cov=pyrogue tests/
```

## コーディング規約

- コードフォーマット：`black`
- インポートの整理：`isort`
- 型チェック：`mypy`
- リンター：`pylint`

これらのツールは`make lint`で一括実行できます。

## コマンド統一化システムの開発

### 概要

PyRogueは、GUIとCLIの両エンジンで統一されたコマンド処理システムを実装しています。新しいコマンドを追加する際は、以下の手順に従ってください。

### 新しいコマンドの追加手順

#### 1. CommonCommandHandlerの拡張

```python
# src/pyrogue/core/command_handler.py
class CommonCommandHandler:
    def handle_command(self, command: str, args: list[str] | None = None) -> CommandResult:
        # 既存のコマンド処理...

        # 新しいコマンドを追加
        elif command in ["newcommand", "nc"]:
            return self._handle_new_command(args)

    def _handle_new_command(self, args: list[str]) -> CommandResult:
        """新しいコマンドの処理実装"""
        success = self.context.game_logic.handle_new_action()
        if success:
            return CommandResult(True, should_end_turn=True)
        else:
            return CommandResult(False, "Cannot perform action")
```

#### 2. GameLogicの拡張

```python
# src/pyrogue/core/game_logic.py
class GameLogic:
    def handle_new_action(self) -> bool:
        """新しいアクションの実装"""
        # ビジネスロジックを実装
        if self._can_perform_action():
            self._execute_action()
            self.add_message("Action performed successfully")
            return True
        return False
```

#### 3. キー入力マッピングの追加（GUI用）

```python
# src/pyrogue/core/input_handlers.py
def _key_to_command(self, event: tcod.event.KeyDown) -> str | None:
    # 既存のキーマッピング...

    # 新しいキーマッピングを追加
    elif key == ord('x'):  # Xキーに新しいコマンドを割り当て
        return "newcommand"
```

#### 4. ヘルプテキストの更新

```python
# src/pyrogue/core/command_handler.py
def _handle_help(self) -> CommandResult:
    help_text = """
Available Commands:
  ...existing commands...

  New Commands:
    newcommand/nc - Perform new action
    """
    self.context.add_message(help_text.strip())
    return CommandResult(True)
```

#### 5. テストの作成

```python
# tests/pyrogue/core/test_command_handler.py
def test_new_command():
    """新しいコマンドのテスト"""
    context = MockCommandContext()
    handler = CommonCommandHandler(context)

    result = handler.handle_command("newcommand")
    assert result.success
    assert result.should_end_turn
```

### 開発のベストプラクティス

#### コマンド設計の原則

1. **一貫性**: 既存コマンドとの命名規則を統一
2. **直感性**: ユーザーが理解しやすいコマンド名
3. **エイリアス**: 短縮形と完全形の両方を提供
4. **エラーハンドリング**: 適切なエラーメッセージの提供

#### 実装の注意点

1. **両環境対応**: CLIとGUIの両方で動作することを確認
2. **テスト**: 新機能のテストケースを必ず作成
3. **ドキュメント**: ヘルプテキストとドキュメントの更新
4. **型安全性**: 型ヒントの適切な使用

### デバッグとテスト

#### CLIモードでのテスト

```bash
# CLIモードで新しいコマンドをテスト
python -m pyrogue.main --cli
> help           # ヘルプの確認
> newcommand     # 新しいコマンドのテスト
```

#### 単体テストの実行

```bash
# 新しいコマンドのテストを実行
pytest tests/pyrogue/core/test_command_handler.py::test_new_command -v
```

### トラブルシューティング

#### よくある問題

1. **コマンドが認識されない**
   - `handle_command`メソッドでの条件分岐を確認
   - コマンド名のスペルチェック

2. **キー入力が反応しない**
   - `_key_to_command`メソッドのキーマッピングを確認
   - キーコードの正確性をチェック

3. **テストが失敗する**
   - MockObjectの設定を確認
   - 期待される戻り値の検証
