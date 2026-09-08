# PyRogue

PyRogue is a small Python 3.12 roguelike inspired by Rogue 5.4. Version 0.3.0
uses a deterministic, seedable game state and a text-cell renderer for both CLI
and TCOD GUI play.

## Run

```bash
uv sync --locked --extra dev
uv run --locked game --cli --seed 1234
uv run --locked game --seed 1234
```

Omit `--seed` for an automatically generated seed. The same game version,
seed, and command sequence produces the same game state.

## Rules at a glance

- 26 floors, ordinary room-and-corridor floors, and maze floors at 7, 13, and 19.
- Field of view, explored-map memory, reachable stairs, turn-based combat, and permadeath.
- Rogue-style A-Z monsters, original traps, hunger, food, equipment, potions, scrolls, wands, rings, gold, and the Amulet.
- The Amulet is carried back to the surface; merely reaching floor 26 does not win.
- A dead game cannot be resumed. The final screen records score, deepest floor, and death cause.
- `current_floor` is the player's current position; victory and death summaries use the separately saved `player.deepest_floor` progress value.
- CLI and GUI use the same death cleanup; the active save is removed on death, but not on victory.

Movement uses vi keys (`h`, `j`, `k`, `l`, `y`, `u`, `b`, `n`) and `.` waits.
Press `/` to identify one unknown item in the pack without consuming a turn.
Use `?` in-game for the complete command list.
In the TCOD GUI, Tab temporarily disables FOV masking to show the complete map; toggling it back restores normal FOV without changing explored-map memory.

## Architecture

The canonical path is deliberately small:

```text
GameState -> DisplayCell -> CLI / GameRenderer
       ^          ^
       +-- commands / JSON save
```

`GameState` owns the RNG, floor state, entities, inventory, combat, hunger,
visibility, and terminal status. The CLI and TCOD renderer share the same
`DisplayCell` input and turn it into characters and colors. JSON saves include the version, complete state, RNG
state, death/win status, and permadeath metadata; incompatible versions are
rejected explicitly.

## Development

```bash
make verify
```

See [SPEC.md](SPEC.md) for the authoritative 0.3.0 behavior and [docs/README.md](docs/README.md)
for the current documentation map.
