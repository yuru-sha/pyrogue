from types import SimpleNamespace

import tcod.event

from pyrogue.core.cli_engine import CLIEngine
from pyrogue.core.game_states import GameStates
from pyrogue.core.rogue_game import GameState, ItemKind, ItemState, MonsterState, Terrain
from pyrogue.ui.screens.game_screen import GameScreen
from pyrogue.ui.screens.inventory_screen import InventoryScreen


class RecordingConsole:
    width = 80
    height = 60

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.cells: dict[tuple[int, int], str] = {}

    def clear(self) -> None:
        self.lines.clear()
        self.cells.clear()

    def print(self, *args, **kwargs) -> None:
        x = kwargs.get("x", args[0] if args else 0)
        y = kwargs.get("y", args[1] if len(args) > 1 else 0)
        value = kwargs.get("string", args[2] if len(args) > 2 else "")
        value = str(value)
        self.cells[(x, y)] = value
        self.lines.append(value)


def key_event(key: str) -> SimpleNamespace:
    return SimpleNamespace(sym=ord(key), mod=0, text=key)


def _key(character: str) -> tcod.event.KeyDown:
    return tcod.event.KeyDown(0, ord(character), 0)


def game_and_inventory() -> tuple[GameScreen, InventoryScreen]:
    engine = SimpleNamespace(map_width=80, map_height=45, state=GameStates.PLAYERS_TURN)
    game_screen = GameScreen(engine, seed=1234)
    return game_screen, InventoryScreen(game_screen)


def _walkable_direction(game: GameState) -> tuple[str, tuple[int, int]]:
    directions = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}
    for name, (dx, dy) in directions.items():
        position = (game.player.x + dx, game.player.y + dy)
        if game.floor.is_walkable(position):
            return name, position
    raise AssertionError


def test_headless_gui_key_execution_matches_cli() -> None:
    cli = CLIEngine(seed=1234, spec_mode=True)
    game_screen = GameScreen(None, seed=1234)

    assert game_screen.handle_key(_key(".")) is None
    assert cli.process_command(".") is True

    assert game_screen.rogue_game.to_dict() == cli.spec_game.to_dict()


def test_headless_gui_and_cli_select_the_same_item_and_target_direction() -> None:
    cli = CLIEngine(seed=1234, spec_mode=True)
    gui = GameScreen(None, seed=1234)

    for game in (cli.spec_game, gui.rogue_game):
        game.floor.monsters.clear()
        direction, position = _walkable_direction(game)
        wand = ItemState(1000, ItemKind.WAND, "test wand", effect="magic_missile", charges=2)
        game.floor.monsters.append(MonsterState(2000, "bat", *position, 20))
        game.player.inventory.append(wand)

    direction, _ = _walkable_direction(gui.rogue_game)
    gui_result = gui.rogue_game.execute("zap", [1000, direction])
    cli_result = cli.spec_game.execute("zap", [1000, direction])

    assert gui_result == cli_result
    assert gui.rogue_game.to_dict() == cli.spec_game.to_dict()


def test_headless_gui_zap_key_matches_cli_item_and_direction_selection() -> None:
    cli = CLIEngine(seed=1234, spec_mode=True)
    gui = GameScreen(None, seed=1234)
    inventory = InventoryScreen(gui)

    for game in (cli.spec_game, gui.rogue_game):
        game.floor.monsters.clear()
        position = (game.player.x + 1, game.player.y)
        assert game.floor.is_walkable(position)
        game.player.inventory = []
        game.player.equipped_weapon = None
        game.player.equipped_armor = None
        game.floor.monsters.append(MonsterState(2000, "bat", *position, 20))
        game.player.inventory.append(ItemState(1000, ItemKind.WAND, "test wand", effect="magic_missile", charges=2))

    assert gui.handle_key(_key("z")) == GameStates.SHOW_INVENTORY
    inventory.handle_input(key_event("a"))
    assert gui.handle_key(_key("l")) is None
    assert cli.process_command("zap 1000 east") is True

    gui_state = gui.rogue_game.to_dict()
    cli_state = cli.spec_game.to_dict()
    gui_state.pop("messages")
    cli_state.pop("messages")
    assert gui_state == cli_state


def test_headless_gui_tab_changes_canonical_render_visibility() -> None:
    game_screen = GameScreen(None, seed=1234)
    console = RecordingConsole()
    hidden_position = next(
        position
        for position, cell in game_screen.rogue_game.display_cells().items()
        if not cell.visible and not cell.explored
    )
    terrain = game_screen.rogue_game.floor.tile_at(hidden_position)
    expected_glyph = {
        Terrain.WALL: "#",
        Terrain.FLOOR: ".",
        Terrain.DOOR_CLOSED: "+",
        Terrain.DOOR_OPEN: "/",
        Terrain.STAIRS_UP: "<",
        Terrain.STAIRS_DOWN: ">",
    }[terrain]
    map_position = (hidden_position[0], hidden_position[1] + 2)

    game_screen.render(console)
    assert map_position not in console.cells

    tab = SimpleNamespace(sym=tcod.event.KeySym.TAB, mod=0, text="")
    game_screen.handle_key(tab)
    game_screen.render(console)
    assert console.cells[map_position] == expected_glyph

    game_screen.handle_key(tab)
    game_screen.render(console)
    assert map_position not in console.cells


def test_inventory_hotkey_opens_and_renders_canonical_inventory() -> None:
    game_screen, inventory_screen = game_and_inventory()

    assert game_screen.handle_key(key_event("i")) == GameStates.SHOW_INVENTORY
    assert not hasattr(game_screen, "game_logic")
    assert not any("Unknown command" in message for message in game_screen.rogue_game.messages)

    console = RecordingConsole()
    inventory_screen.render(console)

    assert any("food ration" in line for line in console.lines)
    assert any("ring mail" in line for line in console.lines)


def test_inventory_equips_item_through_canonical_game_state() -> None:
    game_screen, inventory_screen = game_and_inventory()
    weapon = ItemState(id=1000, kind=ItemKind.WEAPON, name="test sword", identified=True)
    game_screen.player.inventory.append(weapon)

    game_screen.handle_key(key_event("i"))
    inventory_screen.handle_input(key_event("f"))
    inventory_screen.handle_input(key_event("e"))

    assert game_screen.player.equipped_weapon == weapon.id


def test_inventory_unequips_weapon_through_canonical_game_state() -> None:
    game_screen, inventory_screen = game_and_inventory()
    weapon = game_screen.player.equipped(ItemKind.WEAPON)
    assert weapon is not None

    game_screen.handle_key(key_event("i"))
    inventory_screen.handle_input(key_event("r"))

    assert any(item.id == weapon.id for _, item in inventory_screen.equipped_items)
    assert any(f"Weapon: {weapon.display_name}" in message for message in game_screen.rogue_game.messages)
    inventory_screen.handle_input(key_event("a"))

    assert game_screen.player.equipped_weapon is None


def test_throw_selects_item_then_direction_in_canonical_game_state() -> None:
    game_screen, inventory_screen = game_and_inventory()
    food = game_screen.player.inventory[0]
    turns_before = game_screen.player.turns_played

    assert game_screen.handle_key(key_event("t")) == GameStates.SHOW_INVENTORY
    inventory_screen.handle_input(key_event("a"))
    assert game_screen.input_handler.direction_selection_mode
    assert game_screen.input_handler.selected_item_id == food.id

    game_screen.handle_key(key_event("l"))

    assert not game_screen.input_handler.direction_selection_mode
    assert food not in game_screen.player.inventory
    assert game_screen.player.turns_played == turns_before + 1


def test_zap_selects_wand_then_direction_in_canonical_game_state() -> None:
    game_screen, inventory_screen = game_and_inventory()
    wand = ItemState(
        id=1001,
        kind=ItemKind.WAND,
        name="magic missile",
        identified=True,
        charges=2,
        effect="magic_missile",
    )
    game_screen.player.inventory.append(wand)

    assert game_screen.handle_key(key_event("z")) == GameStates.SHOW_INVENTORY
    inventory_screen.handle_input(key_event("a"))
    game_screen.handle_key(key_event("h"))

    assert wand.charges == 1
    assert wand in game_screen.player.inventory
    assert not game_screen.input_handler.direction_selection_mode


def test_load_restores_canonical_inventory_and_clears_stale_selection(monkeypatch) -> None:
    from pyrogue.core import save_manager

    stored: dict[str, object] = {}

    class FakeSaveManager:
        def save_game_state(self, data):
            stored.clear()
            stored.update(data)
            return True

        def load_game_state(self):
            return stored.copy()

    monkeypatch.setattr(save_manager, "SaveManager", FakeSaveManager)
    game_screen, inventory_screen = game_and_inventory()
    wand = ItemState(id=1002, kind=ItemKind.WAND, name="light", identified=True, charges=1, effect="light")
    game_screen.player.inventory.append(wand)

    game_screen.handle_key(key_event("z"))
    inventory_screen.handle_input(key_event("a"))
    assert game_screen.input_handler.direction_selection_mode
    assert game_screen.save_game()

    game_screen.rogue_game = GameState(seed=999)
    assert game_screen.load_game()

    assert any(item.id == wand.id for item in game_screen.player.inventory)
    assert not game_screen.input_handler.direction_selection_mode
    assert game_screen.input_handler.selected_item_id is None
