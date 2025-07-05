# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

# Run in development mode (debug logging enabled)
make dev
```

### Development Workflow
```bash
# Format code
make format

# Run linting and type checking
make lint

# Run tests
make test

# Full release build (clean, format, lint, test)
make release
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

#### Code Style
- Line length: 88 characters
- Type hints required (mypy strict mode)
- Docstrings for public functions
- Import sorting with isort

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
