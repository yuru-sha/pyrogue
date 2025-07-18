# PyRogue
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/yuru-sha/pyrogue)

A **full-featured roguelike game** built with Python 3.12 and TCOD library. PyRogue faithfully recreates the 26-level structure of the original Rogue, featuring procedural dungeon generation, turn-based combat, permadeath, and exploration-focused gameplay.

## Completion Status

PyRogue is now complete as a **fully functional, authentic roguelike game**:

- ✅ **BSP Dungeon Generation System** (RogueBasin compliant, includes maze levels)
- ✅ **Advanced Door Placement System** (prevents consecutive doors, random states, tactical placement)
- ✅ **Trap Search & Disarm System** (safe discovery and disarming, level-dependent success rates)
- ✅ Turn-based combat, magic, and item systems
- ✅ Status effects and trap systems (including hallucination system)
- ✅ Comprehensive UI/UX and save/load functionality
- ✅ **Wizard Mode** (full map display, invincibility, debug features)
- ✅ High-quality architecture (separation of concerns, testability, extensibility)
- ✅ **NPC System** (implemented, currently disabled)
- ✅ **Complete Permadeath System** (true one-time gaming experience)
- ✅ **Score Ranking System** (performance recording and comparison)
- ✅ **Complete Item Identification System** (original Rogue-style)
- ✅ **Diverse Monster AI** (fleeing, special attacks, splitting, etc.)
- ✅ **Enhanced Hunger System** (penalties affecting combat abilities)
- ✅ **Optimized Monster AI** (AI state machine, A* pathfinding, cooperation system)
- ✅ **Codebase Optimization** (type safety, quality improvement, modular structure optimization)

## Features

### 🎯 **Core Gameplay**
- **BSP Dungeon Generation**: RogueBasin-compliant Binary Space Partitioning
- **Advanced Door Placement**: Room boundary breach detection, consecutive door prevention, random states
- **Trap Search & Disarm**: Safe discovery and disarming system (process without stepping on traps)
- **Turn-based Combat**: Strategic combat system
- **Permadeath**: True roguelike experience with permanent death
- **Exploration Focus**: Hidden doors, traps, secret rooms
- **Complete Item Identification**: Original Rogue-style unidentified system

### 🏗️ **Advanced Game Systems**
- **⭐NPC System**: Implemented (currently disabled for future expansion)
- **⭐Diverse Monster AI**: Fleeing, special attacks, splitting, theft, etc.
- **⭐Enhanced Hunger System**: Penalties affecting combat abilities
- **⭐Hallucination System**: Visual confusion with display changes
- **⭐Score Ranking**: Performance recording and comparison system
- **⭐Complete Permadeath**: True one-time gaming experience

### 🔧 **Technical Features**
- **CLI/GUI Dual Mode**: Balances development efficiency and usability
- **Wizard Mode**: Complete debug environment (visualization, invincibility, operation features)
- **Comprehensive Testing**: 285 unit tests + 25 CLI integration tests (100% success)
- **High-quality Architecture**: Handler Pattern, separation of concerns, single responsibility principle
- **Complete Type Hints**: High maintainability and development efficiency, mypy compliant
- **Optimized AI**: State machine, A* pathfinding, cooperation system
- **Codebase Optimization**: 32,360 lines, 185 classes, 1,351 methods

## Technology Stack

- **Python 3.12**: Leverages latest Python features
- **TCOD >=19.0.0**: Rendering, input processing, field of view calculations
- **NumPy >=1.26.3**: Numerical computation and array operations
- **UV**: Fast package management

## Requirements

- Python 3.12
- uv (package manager)

## Installation

### Environment Setup
```bash
# Initial setup (create virtual environment and install dependencies)
make setup

# Install development dependencies
make setup-dev
```

### Running the Game
```bash
# Run game (release mode)
make run

# Run in debug mode
DEBUG=1 make run
```

## For Developers

### Development Workflow
```bash
# Run tests
make test

# CI validation (lint, type check, test)
make ci-checks
```

### Development Tools
The development environment includes the following tools:

- **ruff**: Code formatter and linter
- **mypy**: Type checking
- **pytest**: Test execution and coverage measurement

For detailed developer guide, see [docs/development.md](docs/development.md).

## Controls

### Basic Movement
- **Vi-keys**: hjkl + diagonal movement (yubn)
- **Arrow keys**: Standard directional movement
- **Numpad**: 1-9 for movement (including diagonals)

### Actions
- **,**: Pick up items
- **i**: Inventory screen
- **w**: Equipment screen
- **q**: Use item
- **o**: Open door
- **c**: Close door
- **s**: Search for hidden doors
- **d**: Disarm trap
- **z**: Spellbook
- **t**: Talk to NPC (currently disabled)
- **Tab**: Toggle FOV display
- **?**: Help

### Save/Load
- **Ctrl+S**: Save game
- **Ctrl+L**: Load game

## Architecture Overview

PyRogue employs a high-quality architecture:

### Design Principles
- **Separation of Concerns**: Each class has a single responsibility
- **Testability**: Dependency injection, easily mockable design
- **Extensibility**: Easy addition of new features
- **Maintainability**: Clear type hints, comprehensive documentation

### Major Components
- **Core**: Game engine, state management, input processing
- **Entities**: Player, monsters, items, magic, traps
- **Map**: Dungeon generation, tile definitions, floor management
- **UI**: Screen system, rendering, user interface

### Design Patterns
- **Builder Pattern**: Stepwise dungeon generation construction
- **Manager Pattern**: Dividing functionality into manager classes
- **State Pattern**: Clear game state management
- **Command Pattern**: Status effects and magic effect execution

For detailed architecture information, see [docs/architecture.md](docs/architecture.md).
