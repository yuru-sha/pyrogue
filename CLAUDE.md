# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

PyRogueは、Python 3.12とTCODライブラリを使用した**本格的なローグライクゲーム**です。オリジナルRogueの26階層構造を忠実に再現し、手続き生成ダンジョン、ターンベース戦闘、パーマデス、探索重視のゲームプレイを提供します。

### 完成状態
PyRogueは現在、**完全に機能する本格的なローグライクゲーム**として完成しています：
- ✅ **BSPダンジョン生成システム**（RogueBasin準拠・26階層・迷路階層システム含む）
- ✅ **高度なドア配置システム**（連続ドア防止・ランダム状態・戦術的配置）
- ✅ **トラップ探索・解除システム**（安全な発見・解除・レベル依存成功率）
- ✅ ターンベース戦闘・魔法・アイテムシステム
- ✅ 状態異常・トラップシステム（幻覚システム含む）
- ✅ 包括的なUI/UXとセーブ・ロード機能
- ✅ **ウィザードモード**（全マップ表示・無敵・デバッグ機能）
- ✅ **高品質なアーキテクチャ**（Handler Pattern、責務分離、テスト可能性、拡張性）
- ✅ **完全なPermadeathシステム**（真の一回限りのゲーム体験）
- ✅ **スコアランキングシステム**（成績記録・比較）
- ✅ **完全なアイテム識別システム**（オリジナルRogue風）
- ✅ **多様なモンスターAI**（逃走、特殊攻撃、分裂等）
- ✅ **強化された飢餓システム**（戦闘能力に影響するペナルティ）
- ✅ **環境変数設定システム**（.envファイル対応、開発・運用設定の分離）
- ✅ **完全なインベントリ管理**（装備制限、オリジナルRogue準拠のドロップ動作）
- ✅ **ゴールドオートピックアップシステム**（移動時自動回収・CLIテスト対応）
- ✅ **改善されたアイテム使用メッセージ**（表示問題解決済み・全アイテム対応）
- ✅ **スタック可能アイテムの数量管理修正**（2025-07-13修正・USE/DROP動作正常化）
- ✅ **IDベースセーブシステム**（2025-07-16実装・アイテム名変更耐性・後方互換性維持）
- ✅ **Handler Patternアーキテクチャ**（2025-07-17実装・モジュラー設計・拡張性向上）

### 技術スタック
- **Python 3.12**: 最新のPython機能を活用
- **TCOD >=19.0.0**: 描画、入力処理、視界計算
- **NumPy >=1.26.3**: 数値計算・配列操作
- **python-dotenv >=1.0.0**: 環境変数管理
- **UV**: 高速パッケージ管理

### 重要な技術的注意事項

#### JIS配列キーボード対応
**問題**: TCODライブラリのキーイベント処理はUS配列キーボードを前提としており、JIS配列では一部のキー入力が正しく認識されない。

**対応方針**:
```python
# ❌ 不適切（US配列のみ対応）
if event.sym == tcod.event.KeySym.QUESTION:

# ✅ 適切（JIS/US両配列対応）
if (event.sym == tcod.event.KeySym.QUESTION or
    event.sym == tcod.event.KeySym.SLASH or
    event.unicode == "?" or
    event.unicode == "/"):
```

**実装原則**:
- `event.sym`（キーシンボル）と`event.unicode`（実際の文字）の両方をチェック
- 特殊文字キー（`?`, `!`, `@`等）は複数の検出方法を併用
- 日本のユーザーの利便性を最優先に考慮

**修正済み箇所**:
- インベントリ画面のヘルプ切り替え（`?`キー）: `inventory_screen.py:130-133`
- 階段操作コマンド（`>`/`<`キー）: `input_handler.py:141-149`

**実装されている対応**:
- `?`, `/` → ヘルプ表示切り替え（複数検出方式）
- `>`, `<` → 階段昇降操作（unicode文字検出併用）

## Handler Patternアーキテクチャ（v0.1.0）

### 概要
2025年7月17日のv0.1.0リリースで実装された次世代アーキテクチャ。責務分離とモジュラー設計により、保守性と拡張性が大幅に向上。

### 設計原則
- **Handler Pattern**: 機能別の専用ハンドラーによる責務分離
- **遅延初期化**: 必要時のみハンドラーインスタンス生成
- **CLI/GUI統合**: 共通のCommandContextによる統一インターフェース
- **拡張性**: 新機能追加時の影響範囲最小化

### Handler構成
```
CommonCommandHandler（コア）
├── AutoExploreHandler（自動探索機能）
├── DebugCommandHandler（デバッグコマンド）
├── SaveLoadHandler（セーブ・ロード処理）
└── InfoCommandHandler（情報表示機能）
```

### 実装ファイル
- `src/pyrogue/core/command_handler.py`: CommonCommandHandler（コア）
- `src/pyrogue/core/auto_explore_handler.py`: 自動探索専用ハンドラー
- `src/pyrogue/core/debug_command_handler.py`: デバッグコマンド専用ハンドラー
- `src/pyrogue/core/save_load_handler.py`: セーブ・ロード専用ハンドラー
- `src/pyrogue/core/info_command_handler.py`: 情報表示専用ハンドラー

### 利点
- ✅ **保守性向上**: 機能別の明確な分離により修正範囲を限定
- ✅ **拡張性**: 新ハンドラー追加による機能拡張が容易
- ✅ **テスト性**: 各ハンドラーを独立してテスト可能
- ✅ **再利用性**: CLI/GUIで同一ハンドラーを共有

## IDベースセーブシステム

### 概要
2025年7月16日に実装された次世代セーブシステム。アイテム名変更に対する完全な耐性を持ち、長期的な開発・保守に対応。

### 設計原則
- **IDベース復元**: 各アイテムタイプに固有数値IDを割り当て
- **後方互換性**: 既存の名前ベースセーブデータとの共存
- **段階的フォールバック**: ID→名前→基本アイテムの3段階復元

### アイテムID範囲
```
武器:      100-199  (例: Dagger=101, Long Sword=103)
防具:      200-299  (例: Leather Armor=201, Chain Mail=205)
ポーション: 300-399  (例: Potion of Healing=301)
巻物:      400-499  (例: Scroll of Light=402)
指輪:      500-599  (例: Ring of Protection=501)
杖:        600-699  (例: Wand of Light=602)
食料:      700-799  (例: Food Ration=701)
特殊:      800-899  (例: Gold=801, Amulet of Yendor=802)
```

### セーブデータ形式
```json
{
  "item_id": 101,          // 主キー（IDベース復元）
  "name": "Dagger",        // 後方互換性用
  "count": 1,              // 状態データ
  "identified": true,
  "blessed": false,
  "cursed": false,
  "enchantment": 0,
  "bonus": 0,              // Ring等用
  "charges": 3             // Wand等用
}
```

### 実装ファイル
- `src/pyrogue/entities/items/item_factory.py`: ID→アイテム生成マッピング
- `src/pyrogue/entities/items/item_types.py`: アイテムタイプ定義（ID追加）
- `src/pyrogue/entities/items/item.py`: ItemクラスにIDフィールド追加
- `src/pyrogue/core/command_handler.py`: セーブ・ロードシステム更新

### 利点
- ✅ **名前変更耐性**: アイテム名が変更されても復元可能
- ✅ **バージョン安全性**: ゲーム更新時のセーブデータ破損防止
- ✅ **後方互換性**: 既存セーブデータとの完全互換
- ✅ **拡張性**: 新アイテム追加時の体系的ID管理

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
│   │   ├── command_handler.py # Common command handler (core)
│   │   ├── auto_explore_handler.py # Auto-explore functionality
│   │   ├── debug_command_handler.py # Debug commands
│   │   ├── save_load_handler.py # Save/load processing
│   │   ├── info_command_handler.py # Information display
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
├── assets/                 # Game assets
├── saves/               # Save game files (runtime generated)
├── tests/               # Unit tests
└── docs/               # Documentation
    ├── overview.md      # Project overview
    ├── architecture.md  # Architecture documentation
    ├── features.md      # Feature documentation
    ├── development.md   # Development guide
    ├── task.md         # Task documentation (Phase 2)
    └── task-phase1.md  # Phase 1 completion documentation
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
- **Handler Pattern**: コマンド処理の専門的分離（v0.1.0で導入）
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
- **s**: 隠し扉・トラップの探索
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

### ウィザードモード（デバッグ用）
- **Ctrl+W**: ウィザードモード切り替え
- **Ctrl+T**: 階段にテレポート（ウィザードモード時）
- **Ctrl+U**: レベルアップ（ウィザードモード時）
- **Ctrl+H**: 完全回復（ウィザードモード時）
- **Ctrl+R**: 全マップ探索（ウィザードモード時）

**ウィザードモード機能:**
- 無敵モード（トラップ・モンスターダメージ無効）
- 全マップ表示（FOV無視）
- 隠しドア・トラップの可視化
- 環境変数`DEBUG=true`で自動有効化

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
- CLI統合テスト（25シナリオ）
- 単体テスト（285 tests）
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

**成功基準**: 25/25テスト成功（100%）

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

## Gemini活用

### 三位一体の開発原則
人間の**意思決定**、Claude Codeの**分析と実行**、Gemini MCPの**検証と助言**を組み合わせ、開発の質と速度を最大化する：
- **人間 (ユーザー)**：プロジェクトの目的・要件・最終ゴールを定義し、最終的な意思決定を行う**意思決定者**
  - 反面、具体的なコーディングや詳細な計画を立てる力、タスク管理能力ははありません。
- **Claude Code**：高度なタスク分解・高品質な実装・リファクタリング・ファイル操作・タスク管理を担う**実行者**
  - 指示に対して忠実に、順序立てて実行する能力はありますが、意志がなく、思い込みは勘違いも多く、思考力は少し劣ります。
- **Gemini MCP**：API・ライブラリ・エラー解析など**コードレベル**の技術調査・Web検索 (Google検索) による最新情報へのアクセスを行う**コード専門家**
  - ミクロな視点でのコード品質・実装方法・デバッグに優れますが、アーキテクチャ全体の設計判断は専門外です。

### 壁打ち先の自動判定ルール
- **ユーザーの要求を受けたら即座に壁打ち**を必ず実施
- 壁打ち結果は鵜呑みにしすぎず、1意見として判断
- 結果を元に聞き方を変えて多角的な意見を抽出するのも効果的

### 主要な活用場面
1. **実現不可能な依頼**: Claude Code では実現できない要求への対処 (例: `最新のニュース記事を取得して`)
2. **前提確認**: 要求の理解や実装方針の妥当性を確認 (例: `この実装方針で要件を満たせるか確認して`)
3. **技術調査**: 最新情報・エラー解決・ドキュメント検索 (例: `Rails 7.2の新機能を調べて`)
4. **設計立案**: 新機能の設計・アーキテクチャ構築 (例: `認証システムの設計案を作成して`)
5. **問題解決**: エラーや不具合の原因究明と対処 (例: `このTypeScriptエラーの解決方法を教えて`)
6. **コードレビュー**: 品質・保守性・パフォーマンスの評価 (例: `このコードの改善点は？`)
7. **計画立案**: タスク分解・実装方針の策定 (例: `ユーザー認証機能を実装するための計画を立てて`)
8. **技術選定**: ライブラリ・フレームワークの比較検討 (例: `状態管理にReduxとZustandどちらが適切か？`)
9. **リスク評価**: 実装前の潜在的問題の洗い出し (例: `この実装のセキュリティリスクは？`)
10. **設計検証**: 既存設計の妥当性確認・改善提案 (例: `現在のAPI設計の問題点と改善案は？`)

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
