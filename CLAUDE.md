# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyRogue is a traditional roguelike game built with Python and TCOD (The Coding of Doryen). It features procedurally generated dungeons, turn-based combat, permadeath mechanics, and classic roguelike exploration elements. The game follows traditional roguelike conventions where monsters are represented by A-Z letters and all items are pre-identified.

### Key Features
- Procedural dungeon generation with rooms and corridors
- Turn-based tactical combat system
- Permadeath (permanent death) mechanics
- Exploration-focused gameplay
- Vi-key movement controls (hjkl + diagonals)
- Inventory and equipment system
- Save/load functionality
- Both GUI and CLI modes for testing

### Technology Stack
- **Python 3.12**: Core language
- **TCOD >=19.0.0**: Rendering, input handling, and console management
- **NumPy >=1.26.3**: Numerical operations and array handling
- **UV**: Package manager for fast dependency resolution

## Directory Structure

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
│   ├── __init__.py
│   ├── main.py           # Application entry point
│   ├── config.py         # Game configuration
│   │
│   ├── core/             # Game engine and core systems
│   │   ├── engine.py     # Main game engine (GUI mode)
│   │   ├── cli_engine.py # CLI engine for testing
│   │   ├── game_states.py # Game state enumeration
│   │   ├── input_handlers.py # Input processing
│   │   └── save_manager.py    # Save/load functionality
│   │
│   ├── entities/         # Game entities (actors and items)
│   │   ├── actors/       # Player and monsters
│   │   │   ├── player.py        # Player character
│   │   │   ├── monster.py       # Monster entities
│   │   │   ├── monster_spawner.py # Monster generation
│   │   │   ├── monster_types.py   # Monster definitions
│   │   │   ├── inventory.py     # Inventory system
│   │   │   └── player_status.py # Player stats and status
│   │   └── items/        # Items and equipment
│   │       ├── item.py          # Base item class
│   │       ├── item_spawner.py  # Item generation
│   │       ├── item_types.py    # Item definitions
│   │       └── effects.py       # Item effects
│   │
│   ├── map/              # Dungeon generation and tiles
│   │   ├── dungeon.py           # Main dungeon class
│   │   ├── dungeon_builder.py   # Dungeon generation logic
│   │   └── tile.py              # Tile types (floor, wall, door, stairs)
│   │
│   ├── ui/               # User interface components
│   │   ├── elements/     # UI elements (empty currently)
│   │   └── screens/      # Game screens
│   │       ├── screen.py           # Base screen class
│   │       ├── menu_screen.py      # Main menu
│   │       ├── game_screen.py      # Main gameplay screen
│   │       ├── inventory_screen.py # Inventory management
│   │       ├── game_over_screen.py # Game over screen
│   │       └── victory_screen.py   # Victory screen
│   │
│   └── utils/            # Utility modules
│       └── logger.py     # Logging system
│
├── data/                 # Game assets and data
│   ├── assets/fonts/     # Font files
│   │   └── dejavu10x10_gs_tc.png
│   ├── fonts/           # Additional fonts (empty)
│   └── logs/            # Log files (runtime generated)
│
├── saves/               # Save game files (runtime generated)
├── tests/               # Unit tests
│   └── test_dungeon.py  # Dungeon generation tests
├── test_*.py           # Additional test files (development)
└── docs/               # Documentation
    ├── development.md   # Development guide
    └── task.md         # Task documentation
```

## Development Commands

### Environment Setup
```bash
# Initial setup (creates virtual environment and installs dependencies)
make setup

# Install development dependencies
make setup-dev
```

### Running the Game
```bash
# Run the game (release mode)
make run
```

### Development Workflow
```bash
# Run ci check
make ci-checks
```

Note: The project uses `uv` as the package manager. All development commands are run through `uv run`.

## Architecture Overview

### Core Structure
- **Engine (`core/engine.py`)**: Main game engine managing the game loop, state transitions, and event handling
- **Game States (`core/game_states.py`)**: Enum defining all possible game states (MENU, PLAYERS_TURN, GAME_OVER, etc.)
- **Screen System (`ui/screens/`)**: Different screens for menu, game, inventory, and game over states

### Key Components

#### Game Engine
- Manages TCOD console and context
- Handles window resizing dynamically
- Routes input to appropriate screens based on current state
- Coordinates state transitions between menu, gameplay, and game over

#### Entity System
- **Player (`entities/actors/player.py`)**: Player character with stats, inventory, and positioning
- **Monsters (`entities/actors/monster.py`)**: Enemy entities with AI behavior
- **Items (`entities/items/`)**: Equipment, consumables, and treasure with type-based categorization
- **Inventory (`entities/actors/inventory.py`)**: Container system for items

#### Map System
- **Dungeon (`map/dungeon.py`)**: Procedural dungeon generation with rooms and corridors
- **Tiles (`map/tile.py`)**: Floor, wall, door, and stairs tile types
- Room-based generation with door connections

#### UI System
- Screen-based architecture with base Screen class
- Separate screens for different game states
- Console-based rendering with TCOD

### Technical Details

#### Configuration
- Python 3.12 required
- Uses TCOD for rendering and input handling
- Configured with strict linting (ruff, mypy, black, isort)
- Test coverage with pytest

### コーディング規約

- PEP 8準拠（ruffで自動チェック）
- 型ヒント必須（`ruff`チェック通過が必要）
- Google形式のdocstring（日本語で記述）
- 実装コメントは日本語で統一
- ドキュメント（README、docs/配下）は日本語で統一

### コミットメッセージ規約

**英語で統一し、Conventional Commits形式を使用：**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type一覧：**
- `feat`: 新機能追加
- `fix`: バグ修正
- `docs`: ドキュメント変更のみ
- `style`: コードの意味に影響しない変更（フォーマット等）
- `refactor`: バグ修正でも機能追加でもないコード変更
- `perf`: パフォーマンス改善
- `test`: テストの追加や修正
- `chore`: ビルドプロセスや補助ツールの変更

**例：**
```bash
feat(ml): add unkai detection CNN model
fix(dashboard): resolve Streamlit page reload issue
docs(api): update weather data collection documentation
refactor(database): optimize query performance in repository
```

#### Font and Display
- Uses dejavu10x10_gs_tc.png font (located in `data/assets/fonts/`)
- Default screen size: 80x50 characters
- Supports window resizing
- Map area: 80x43 (reserves space for UI elements)

## Testing

Run tests with:
```bash
make test
```

Test files are located in the `tests/` directory. The project uses pytest with coverage reporting.

## Logging

The game uses a custom logger (`utils/logger.py`) with debug mode enabled via `DEBUG=1` environment variable.

## Gemini CLI 連携ガイド

### 目的
ユーザーが **「Geminiと相談しながら進めて」** と指示した場合、
Claude は以降のタスクを **Gemini CLI** と協調しながら進める。

### トリガー
- 正規表現: `/Gemini.*相談しながら/`

### 基本フロー
1. **PROMPT 生成**
   Claude はユーザーの要件を1つのテキストにまとめ、環境変数 `$PROMPT` に格納

2. **Gemini CLI 呼び出し**
```bash
gemini <<EOF
$PROMPT
EOF
```

3. **結果の統合**
   - Gemini の回答を提示
   - Claude の追加分析・コメントを付加

## Gemini活用

### 三位一体の開発原則
人間の**意思決定**、Claude Codeの**分析と実行**、Gemini CLIの**検証と助言**を組み合わせ、開発の質と速度を最大化する：
- **人間 (ユーザー)**：プロジェクトの目的・要件・最終ゴールを定義し、最終的な意思決定を行う**意思決定者**
  - 反面、具体的なコーディングや詳細な計画を立てる力、タスク管理能力ははありません。
- **Claude Code**：高度なタスク分解・高品質な実装・リファクタリング・ファイル操作・タスク管理を担う**実行者**
  - 指示に対して忠実に、順序立てて実行する能力はありますが、意志がなく、思い込みは勘違いも多く、思考力は少し劣ります。
- **Gemini CLI**：API・ライブラリ・エラー解析など**コードレベル**の技術調査・Web検索 (Google検索) による最新情報へのアクセスを行う**コード専門家**
  - ミクロな視点でのコード品質・実装方法・デバッグに優れますが、アーキテクチャ全体の設計判断は専門外です。

### 壁打ち先の自動判定ルール
- **ユーザーの要求を受けたら即座に壁打ち**を必ず実施
- 壁打ち結果は鵜呑みにしすぎず、1意見として判断
- 結果を元に聞き方を変えて多角的な意見を抽出するのも効果的

### 主要な活用場面
1. **実現不可能な依頼**: Claude Codeでは実現できない要求への対処 (例: `今日の天気は？`)
2. **前提確認**: ユーザー、Claude自身に思い込みや勘違い、過信がないかどうか逐一確認 (例: `この前提は正しいか？`）
3. **技術調査**: 最新情報・エラー解決・ドキュメント検索・調査方法の確認（例: `Rails 7.2の新機能を調べて`）
4. **設計検証**: アーキテクチャ・実装方針の妥当性確認（例: `この設計パターンは適切か？`）
5. **問題解決**: Claude自身が自力でエラーを解決できない場合に対処方法を確認 (例: `この問題の対処方法は？`)
6. **コードレビュー**: 品質・保守性・パフォーマンスの評価（例: `このコードの改善点は？`）
7. **計画立案**: タスクの実行計画レビュー・改善提案（例: `この実装計画の問題点は？`）
8. **技術選定**: ライブラリ・手法の比較検討 （例: `このライブラリは他と比べてどうか？`）
9. **実装前リスク評価**: 複雑な実装着手前の事前リスク確認・落とし穴の事前把握（例: `ReactとD3.jsの組み合わせでよくある問題は？`）
10. **設計判断の事前検証**: アーキテクチャ決定前の多角的検証・技術的負債の予防（例: `マイクロサービス化の判断は適切か？`）

## トラブルシューティング

### よくある問題

1. **依存関係エラー**: `make setup-dev`を再実行
