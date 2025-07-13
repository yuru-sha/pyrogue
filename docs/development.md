---
cache_control: {"type": "ephemeral"}
---
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

PyRogueでは.envファイルによる環境変数管理を採用しています。開発・運用設定の分離が可能です。

### 環境変数設定の手順

1. **.envファイルの作成**：
```bash
# 設定テンプレートをコピー
cp .env.example .env

# .envファイルを編集
vim .env  # または好みのエディタで編集
```

2. **環境変数による設定上書き**：
```bash
# 一時的な設定変更
DEBUG=true WINDOW_WIDTH=100 make run

# 永続的な設定変更は.envファイルで行う
```

### 主要な環境変数

| 環境変数 | デフォルト値 | 説明 | 用途 |
|----------|--------------|------|------|
| `DEBUG` | false | デバッグモード | 開発時の詳細ログ出力 |
| `LOG_LEVEL` | INFO | ログレベル | DEBUG/INFO/WARNING/ERROR |
| `WINDOW_WIDTH` | 80 | ウィンドウ幅（文字数） | 画面サイズ調整 |
| `WINDOW_HEIGHT` | 50 | ウィンドウ高さ（文字数） | 画面サイズ調整 |
| `FPS_LIMIT` | 60 | フレームレート制限 | パフォーマンス調整 |
| `AUTO_SAVE_ENABLED` | true | オートセーブ機能 | セーブ頻度制御 |
| `FONT_PATH` | auto | フォントファイルパス | 表示カスタマイズ |

### 開発・運用環境の分離

**開発環境設定例**（.env）：
```bash
DEBUG=true
LOG_LEVEL=DEBUG
WINDOW_WIDTH=100
WINDOW_HEIGHT=60
AUTO_SAVE_ENABLED=true
```

**運用環境設定例**：
```bash
DEBUG=false
LOG_LEVEL=INFO
WINDOW_WIDTH=80
WINDOW_HEIGHT=50
AUTO_SAVE_ENABLED=false
```

### 実装場所
- `src/pyrogue/config/env.py` - 環境変数管理クラス
- `src/pyrogue/config/legacy.py` - 後方互換性用レガシー設定

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

## 既知の課題 (Known Issues)

### UI関連の課題

#### 1. 入力処理の修正中問題
- **場所**: `src/pyrogue/ui/components/input_handler.py`
- **問題**: キーボード入力処理の一部で不具合が発生
- **詳細**: 特定のキー組み合わせで期待通りの動作がしない場合がある
- **影響範囲**: 特定の操作シナリオでのユーザー体験
- **対応状況**: 修正作業中
- **回避策**: 代替キーバインドの使用

#### 2. 大規模マップでのレンダリングパフォーマンス
- **問題**: マップサイズ拡大時の描画処理負荷増加
- **影響**: フレームレートの低下、操作レスポンス悪化
- **原因**: 全タイル描画によるCPU負荷
- **対策候補**:
  - 視界ベースのカリング実装
  - タイル描画の最適化
  - 差分描画システムの強化
- **優先度**: 中

#### 3. 複雑なゲーム状態のシリアライゼーション
- **場所**: `src/pyrogue/ui/components/save_load_manager.py`
- **問題**: セーブデータの一貫性保証が困難
- **詳細**:
  - フロアデータの完全復元
  - エンティティ状態の複雑な依存関係
  - メモリ効率とデータ整合性のトレードオフ
- **影響**: セーブ・ロード機能の信頼性
- **対応状況**: 継続的改善中
- **関連**: Permadeathシステムとの連携

### 対応予定とロードマップ

#### 短期対応（次リリース）
1. **入力処理問題の修正**
   - 優先度: 高
   - 予定: バグ修正リリース
   - 担当: UI開発チーム

#### 中期対応（2-3リリース後）
2. **レンダリング最適化**
   - 優先度: 中
   - 予定: パフォーマンス改善リリース
   - 実装方針: 段階的最適化

#### 長期対応（メジャーバージョン）
3. **セーブシステム改善**
   - 優先度: 中
   - 予定: アーキテクチャ改善時
   - 実装方針: 設計レベルでの見直し

### 課題報告・修正への貢献

#### バグ報告時の情報
1. **再現手順**: 具体的な操作順序
2. **環境情報**: OS、Python版本、依存関係版本
3. **ログ情報**: エラーメッセージ、デバッグログ
4. **期待動作**: 本来あるべき動作の説明

#### 修正への貢献
1. **Issue作成**: GitHubでの課題報告
2. **Pull Request**: 修正案の提案
3. **テスト**: 修正内容の検証
4. **ドキュメント**: 変更内容の文書化

## 変更履歴

このセクションでは、主要なバグ修正と機能改善の履歴を記録します。

### 2025-07-13: スタック可能アイテムの数量管理修正

#### 問題の概要
- **問題1**: インベントリでスタック可能アイテム（ヒーリングポーション等）を使用（u）すると、1個使用のつもりが全スタック（3個等）がインベントリから消失
- **問題2**: スタック可能アイテムをドロップ（d）すると、1個だけドロップされ、残りがインベントリに残存

#### 根本原因
- `inventory.remove_item()`メソッドがスタック数量を考慮せず、アイテム全体を削除
- ドロップ処理が`remove_item()`をデフォルト引数（count=1）で呼び出し

#### 修正内容
1. **`src/pyrogue/entities/actors/inventory.py`**
   - `remove_item(item, count=1)`に数量パラメータを追加
   - スタック可能アイテムの場合、count分だけstack_countを減算
   - stack_countが0以下になった場合のみアイテム削除

2. **`src/pyrogue/ui/screens/inventory_screen.py`**
   - ドロップ処理で全スタック削除するよう修正：`remove_item(item, item.stack_count)`
   - ドロップメッセージにスタック数を反映

#### テスト結果
- 230個の単体テスト: 229成功、1失敗（無関係なダンジョン生成問題）
- 22個のCLI統合テスト: 全成功
- スタック機能の動作確認: 完全に正常化

#### 修正ファイル
```
src/pyrogue/entities/actors/inventory.py (lines 53-74)
src/pyrogue/ui/screens/inventory_screen.py (lines 279-292)
```
