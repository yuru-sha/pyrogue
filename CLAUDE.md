# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

PyRogueは、Python 3.12とTCODライブラリを使用した**本格的なローグライクゲーム**です。オリジナルRogueの26階層構造を忠実に再現し、手続き生成ダンジョン、ターンベース戦闘、パーマデス、探索重視のゲームプレイを提供します。

### 完成状態
PyRogueは現在、**完全に機能する本格的なローグライクゲーム**として完成しています：
- ✅ 26階層の手続き生成ダンジョン（迷路階層システム含む）
- ✅ ターンベース戦闘・魔法・アイテムシステム
- ✅ 状態異常・トラップシステム（幻覚システム含む）
- ✅ 包括的なUI/UXとセーブ・ロード機能
- ✅ 高品質なアーキテクチャ（責務分離、テスト可能性、拡張性）
- ✅ **NPCシステム**（実装済み・現在無効化中）
- ✅ **完全なPermadeathシステム**（真の一回限りのゲーム体験）
- ✅ **スコアランキングシステム**（成績記録・比較）
- ✅ **完全なアイテム識別システム**（オリジナルRogue風）
- ✅ **多様なモンスターAI**（逃走、特殊攻撃、分裂等）
- ✅ **強化された飢餓システム**（戦闘能力に影響するペナルティ）
- ✅ **環境変数設定システム**（.envファイル対応、開発・運用設定の分離）
- ✅ **完全なインベントリ管理**（装備制限、オリジナルRogue準拠のドロップ動作）
- ✅ **ゴールドオートピックアップシステム**（移動時自動回収・CLIテスト対応）
- ✅ **改善されたアイテム使用メッセージ**（表示問題解決済み・全アイテム対応）

### 技術スタック
- **Python 3.12**: 最新のPython機能を活用
- **TCOD >=19.0.0**: 描画、入力処理、視界計算
- **NumPy >=1.26.3**: 数値計算・配列操作
- **python-dotenv >=1.0.0**: 環境変数管理
- **UV**: 高速パッケージ管理

## ディレクトリ構造

```
pyrogue/
├── CLAUDE.md              # Claude Code guidance (this file)
├── README.md              # Project documentation
├── LICENSE                # MIT license
├── Makefile               # Development commands
├── pyproject.toml         # Project configuration and dependencies
├── uv.lock               # Dependency lock file
│
├── src/pyrogue/           # Main source code
│   ├── main.py           # Application entry point
│   ├── constants.py      # Game constants (recommended)
│   │
│   ├── config/           # Configuration management
│   │   ├── env.py        # Environment variables management
│   │   └── legacy.py     # Legacy configuration (backward compatibility)
│   │
│   ├── core/             # Game engine and core systems
│   │   ├── engine.py     # Main game engine (GUI mode)
│   │   ├── cli_engine.py # CLI engine for testing
│   │   ├── game_states.py # Game state enumeration
│   │   ├── game_logic.py  # Game logic management
│   │   ├── input_handlers.py # Input processing
│   │   ├── save_manager.py    # Save/load functionality
│   │   └── managers/          # Manager classes
│   │       ├── game_context.py    # Shared context
│   │       ├── turn_manager.py    # Turn management
│   │       ├── combat_manager.py  # Combat system
│   │       └── monster_ai_manager.py # Monster AI
│   │
│   ├── entities/         # Game entities (actors and items)
│   │   ├── actors/       # Player and monsters
│   │   ├── items/        # Items and equipment
│   │   ├── magic/        # Magic system
│   │   └── traps/        # Trap system
│   │
│   ├── map/              # Dungeon generation and tiles
│   │   ├── dungeon.py           # Main dungeon class
│   │   ├── dungeon_builder.py   # Dungeon generation logic
│   │   ├── dungeon_manager.py   # Multi-floor management
│   │   ├── tile.py              # Tile types
│   │   └── dungeon/             # Builder Pattern implementation
│   │
│   ├── ui/               # User interface components
│   │   ├── screens/      # Game screens
│   │   └── components/   # UI components
│   │
│   └── utils/            # Utility modules
│       └── logger.py     # Logging system
│
├── data/                 # Game assets and data
├── saves/               # Save game files (runtime generated)
├── tests/               # Unit tests
└── docs/               # Documentation
    ├── overview.md      # Project overview
    ├── architecture.md  # Architecture documentation
    ├── features.md      # Feature documentation
    ├── development.md   # Development guide
    └── task.md         # Task documentation
```

**注意**: 詳細なディレクトリ構造は `docs/architecture.md` を参照してください。

## 開発コマンド

### 環境構築
```bash
make setup      # 初期環境構築（仮想環境作成・依存関係インストール）
make setup-dev  # 開発依存関係インストール
```

### 環境変数設定（.env）
```bash
cp .env.example .env  # 設定例をコピー
# .envファイルを編集して設定をカスタマイズ
```

**主要な環境変数:**
- `DEBUG`: デバッグモード有効化 (true/false)
- `LOG_LEVEL`: ログレベル設定 (DEBUG/INFO/WARNING/ERROR)
- `WINDOW_WIDTH/HEIGHT`: ウィンドウサイズ設定
- `FPS_LIMIT`: FPS制限設定
- `AUTO_SAVE_ENABLED`: オートセーブ機能 (true/false)

### ゲーム実行
```bash
make run        # ゲーム実行（リリースモード）
```

### 開発ワークフロー
```bash
make test       # テスト実行
make ci-checks  # CI検証（リント・型チェック・テスト）
```

**注意**: プロジェクトは `uv` をパッケージマネージャーとして使用。すべての開発コマンドは `uv run` を通じて実行されます。

## アーキテクチャ概要

### 設計原則
- **責務分離**: 各クラスが単一責任を持つ
- **テスト可能性**: 依存関係注入、モックしやすい設計
- **拡張性**: 新機能の追加が容易
- **保守性**: 明確な型ヒント、包括的なドキュメント

### 主要コンポーネント
- **Config**: 環境変数管理、設定システム
- **Core**: ゲームエンジン、状態管理、入力処理
- **Entities**: プレイヤー、モンスター、アイテム、魔法、トラップ
- **Map**: ダンジョン生成、タイル定義、階層管理
- **UI**: スクリーンシステム、描画処理、ユーザーインターフェース

### 設計パターン
- **Builder Pattern**: ダンジョン生成の段階的構築
- **Manager Pattern**: 機能を管理クラスに分割
- **State Pattern**: ゲーム状態の明確な管理
- **Command Pattern**: 状態異常・魔法効果の実行

**詳細**: 包括的なアーキテクチャ情報は `docs/architecture.md` を参照してください。

## 開発ガイドライン

### コーディング規約
- **PEP 8準拠**: ruffで自動チェック
- **型ヒント必須**: mypy・ruffチェック通過が必要
- **Google形式のdocstring**: 日本語で記述
- **実装コメント**: 日本語で統一
- **ドキュメント**: README、docs/配下は日本語で統一

### コミットメッセージ規約
**英語で統一し、Conventional Commits形式を使用：**

```
<type>(<scope>): <subject>
```

**Type一覧：**
- `feat`: 新機能追加
- `fix`: バグ修正
- `docs`: ドキュメント変更のみ
- `refactor`: バグ修正でも機能追加でもないコード変更
- `test`: テストの追加や修正
- `chore`: ビルドプロセスや補助ツールの変更

### コーディング三原則
- **YAGNI**: 今必要じゃない機能は作らない
- **DRY**: 同じコードを繰り返さない
- **KISS**: シンプルに保つ

## ゲーム操作

### 基本移動
- **Vi-keys**: hjkl + 対角線移動 (yubn)
- **矢印キー**: 標準的な方向移動
- **テンキー**: 1-9による移動（対角線含む）

### アクション
- **g**: アイテム取得
- **i**: インベントリ画面
- **o**: 扉を開く
- **c**: 扉を閉じる
- **s**: 隠し扉の探索
- **d**: トラップ解除
- **z**: 魔法書（spellbook）
- **Tab**: FOV表示切り替え

### インベントリ操作（iキーでアクセス）
- **↑/↓**: アイテム選択
- **u**: アイテム使用
- **e**: 装備・装備解除
- **r**: 装備解除のみ
- **d**: アイテムドロップ（装備中は自動的に装備解除）
- **?**: ヘルプ表示切り替え
- **ESC**: インベントリを閉じる

**注意**: 呪われたアイテムは装備解除・ドロップ不可

### セーブ・ロード
- **Ctrl+S**: ゲームセーブ
- **Ctrl+L**: ゲームロード

**詳細**: 完全なゲーム機能一覧は `docs/features.md` を参照してください。

## テスト・ログ

### テスト実行
```bash
make test  # pytest + カバレッジレポート
```

### デバッグログ
```bash
DEBUG=1 make run  # デバッグモードで実行
```

カスタムロガー（`utils/logger.py`）を使用。

## 品質保証プロセス

### 必須QAタスク

**リファクタリング時**:
```bash
make qa-after-refactor  # 回帰テスト + CLI統合テスト + コード品質チェック
```

**新機能追加時**:
```bash
make qa-after-feature   # 新機能テスト + 統合テスト + コード品質チェック
```

**包括的品質チェック**:
```bash
make qa-all            # 全テスト + CLI統合テスト + コード品質チェック
```

### 自動品質チェック

**Pre-commit フック**:
```bash
make pre-commit-install  # 自動品質チェック設定
```

設定後、コミット時に自動実行される項目：
- CLI統合テスト（19シナリオ）
- 単体テスト（230+ tests）
- コード品質チェック（ruff, mypy）

### CLI統合テストの重要性

**テストカバレッジ**:
- 基本機能テスト（9項目）
- ゲームオーバーテスト（4項目）
- イェンダーのアミュレットテスト（5項目）
- 統合動作テスト（1項目）

**実行方法**:
```bash
make test-cli           # CLI統合テスト単体実行
./scripts/cli_test.sh   # スクリプト直接実行
```

**成功基準**: 19/19テスト成功（100%）

### 品質保証の意義

**リファクタリング安全性**:
- 既存機能の回帰テスト
- 統合動作の確認
- コード品質維持

**新機能信頼性**:
- 新機能の動作確認
- 既存機能との統合確認
- 品質基準の達成

**重要**: リファクタリングや新機能追加時は、必ず該当するQAタスクを実行してください。詳細は `docs/quality_assurance.md` を参照。

## Gemini CLI 協調開発

### 三位一体の開発原則
人間の**意思決定**、Claude Codeの**分析と実行**、Gemini CLIの**検証と助言**を組み合わせ、開発の質と速度を最大化：

- **人間 (ユーザー)**: プロジェクトの目的・要件・最終ゴールを定義し、最終的な意思決定を行う**意思決定者**
- **Claude Code**: 高度なタスク分解・高品質な実装・リファクタリング・ファイル操作・タスク管理を担う**実行者**
- **Gemini CLI**: API・ライブラリ・エラー解析など**コードレベル**の技術調査・Web検索による最新情報へのアクセスを行う**コード専門家**

### 活用トリガー
ユーザーが **「Geminiと相談しながら進めて」** と指示した場合、Claude は以降のタスクを **Gemini CLI** と協調しながら進める。

### 基本フロー
1. **PROMPT 生成**: ユーザーの要件を1つのテキストにまとめ、環境変数 `$PROMPT` に格納
2. **Gemini CLI 呼び出し**: `gemini <<EOF\n$PROMPT\nEOF`
3. **結果の統合**: Gemini の回答を提示し、Claude の追加分析・コメントを付加

### 主要な活用場面
1. **前提確認**: ユーザー、Claude自身に思い込みや勘違い、過信がないかどうか逐一確認
2. **技術調査**: 最新情報・エラー解決・ドキュメント検索・調査方法の確認
3. **設計検証**: アーキテクチャ・実装方針の妥当性確認
4. **問題解決**: Claude自身が自力でエラーを解決できない場合に対処方法を確認
5. **コードレビュー**: 品質・保守性・パフォーマンスの評価
6. **計画立案**: タスクの実行計画レビュー・改善提案
7. **技術選定**: ライブラリ・手法の比較検討
8. **実装前リスク評価**: 複雑な実装着手前の事前リスク確認・落とし穴の事前把握
9. **設計判断の事前検証**: アーキテクチャ決定前の多角的検証・技術的負債の予防

### 壁打ち先の自動判定ルール
- **ユーザーの要求を受けたら即座に壁打ち**を必ず実施
- 壁打ち結果は鵜呑みにしすぎず、1意見として判断
- 結果を元に聞き方を変えて多角的な意見を抽出するのも効果的

## TDD開発手法（t-wada流）

### 基本サイクル
- 🔴 **Red**: 失敗するテストを書く
- 🟢 **Green**: テストを通す最小限の実装
- 🔵 **Refactor**: リファクタリング

### 実践原則
- **小さなステップ**: 一度に1つの機能のみ
- **仮実装**: テストを通すためにベタ書きでもOK（例：`return 42`）
- **三角測量**: 2つ目、3つ目のテストケースで一般化する
- **TODOリスト更新**: 実装中に思いついたことはすぐリストに追加
- **不安なところから**: 不安な箇所を優先的にテスト
- **即座にコミット**: テストが通ったらすぐコミット

### TDDコミットルール
- 🔴 テストを書いたら: `test: add failing test for [feature]`
- 🟢 テストを通したら: `feat: implement [feature] to pass test`
- 🔵 リファクタリングしたら: `refactor: [description]`

## トラブルシューティング

### よくある問題
1. **依存関係エラー**: `make setup-dev`を再実行
2. **型チェックエラー**: `mypy src/pyrogue/`でチェック
3. **テスト失敗**: `make test -v`で詳細確認

### 参考資料
- **詳細な概要**: `docs/overview.md`
- **アーキテクチャ**: `docs/architecture.md`
- **機能一覧**: `docs/features.md`
- **開発ガイド**: `docs/development.md`
