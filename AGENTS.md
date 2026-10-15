# Repository Guidelines

## Project Overview

PyRogue is a Python 3.12+ terminal/TCOD roguelike implementing the v0.3.1 requirements in `docs/SPEC.md`. Keep game rules shared between CLI and GUI; do not add features or dependencies outside the specification.

## Architecture & Data Flow

`src/pyrogue/core/rogue_game.py` contains canonical `GameState`, seeded RNG, game rules, commands, serialization, and renderer-neutral `DisplayCell` data. Both adapters call `GameState.execute()`:

```text
CLI / TCOD input → GameState.execute(command, args) → GameState
                 → display_cells() → text renderer / TCOD renderer
```

`docs/SPEC.md` is the product-requirements authority. When historical material in `docs/` conflicts with implementation, do not treat it as current behavior. Keep changes focused, read relevant requirements/callers/tests first, and preserve unrelated worktree changes. Generated files, lockfiles, and untracked files must be confirmed in scope before modification.

Code should show how behavior is implemented; tests should specify expected behavior. Comments should explain why an apparently simpler alternative was not chosen, including constraints and intent not evident from the code. Avoid comments that merely restate behavior.

Do not expose secrets or personal data. Do not use destructive Git operations. Make changes on a feature branch and submit them through a pull request; do not edit `main` directly.

Put rules in `GameState`, not in CLI or GUI. Keep TCOD consoles, glyphs, colors, and tile details out of game state. `GameState` owns randomness; preserve seeded determinism, including save/load of RNG state.

## Key Directories

- `src/pyrogue/core/` — canonical game, CLI/GUI lifecycle, and JSON save management.
- `src/pyrogue/presentation/` — conversion of display-cell data to terminal text.
- `src/pyrogue/ui/` — GUI screens and input/rendering adapters.
- `src/pyrogue/config/`, `src/pyrogue/utils/` — configuration and logging support.
- `tests/` — pytest contracts organized around core rules, adapters, persistence, and UI.
- `scripts/` — verification helpers and CLI smoke runner.
- `docs/` — current requirements, architecture, and development guidance; `docs/README.md` describes historical documents.

## Development Commands

```bash
rtk uv sync --locked --extra dev
rtk uv run --locked game --cli --seed 1234
rtk uv run --locked game --seed 1234
rtk make verify
```

The console entry point is `game` (`pyrogue.main:main`); omit `--cli` for the GUI. `rtk make verify` runs secret-pattern scanning, Ruff lint/format checks, mypy, compileall, pytest, and the CLI smoke suite. For focused work, use `rtk uv run --locked --extra dev pytest -q <test-file>`. Prefix shell commands with `rtk` in this repository.

## Code Conventions & Common Patterns

- Follow the existing Python style: Ruff, double-quoted strings, four-space indentation, and a 120-character line limit.
- Use `GameState.execute()` and `CommandResult` for canonical command behavior and result reporting. CLI and GUI translate input and display state; they must not duplicate game rules.
- Use the `GameState`-owned seeded RNG for every game-random outcome. Keep the RNG state and relevant gameplay state round-trippable in JSON.
- Keep rendering dependent on `DisplayCell`, not game entities or TCOD objects.
- Treat incompatible saves as explicit compatibility errors; when changing save formats, update `GAME_VERSION`, compatibility checks, and tests together.

## Important Files

- `docs/SPEC.md` — authoritative requirements, exclusions, and acceptance criteria.
- `docs/README.md` — documentation index and historical-document policy.
- `docs/architecture.md`, `docs/development.md` — current architecture and commands.
- `src/pyrogue/main.py` — CLI/GUI entry point and `--seed` option.
- `src/pyrogue/core/rogue_game.py` — canonical game state and rules.
- `src/pyrogue/core/cli_engine.py`, `src/pyrogue/core/engine.py` — CLI and GUI adapters.
- `src/pyrogue/core/save_manager.py` — JSON persistence and compatibility handling.
- `src/pyrogue/presentation/display_renderer.py` — text display conversion.
- `pyproject.toml`, `uv.lock`, `Makefile` — package, locked dependencies, and development commands.

## Runtime/Tooling Preferences

Use Python 3.12 or later and `uv` with the committed `uv.lock`; install development dependencies with `uv sync --locked --extra dev`. TCOD is required for GUI execution. Do not introduce another package manager or runtime.

## Testing & QA

Use pytest; tests live under `tests/` and pytest adds `src` to the import path. Follow existing deterministic `GameState(seed=...)` tests and use `tmp_path` for save-file cases. Check state changes and turn consumption, not just messages. Cover save compatibility, determinism, and CLI/GUI shared behavior when affected.

Run focused tests and `rtk make verify` for code changes. `scripts/cli_test.sh` is the CLI smoke suite; its seed can be set with `CLI_TEST_SEED`, e.g. `CLI_TEST_SEED=20260908 rtk make test-cli`. Secret-pattern scanning is high-confidence only, not a complete secret scanner.

Before implementing, read the relevant `docs/SPEC.md` section and current callers/tests. Preserve unrelated worktree changes; do not commit, push, or perform destructive Git operations unless explicitly requested.
