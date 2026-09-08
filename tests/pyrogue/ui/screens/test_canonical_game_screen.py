from types import SimpleNamespace

from pyrogue.core.game_states import GameStates
from pyrogue.core.rogue_game import GameState, ItemKind, ItemState
from pyrogue.ui.screens.game_screen import GameScreen
from pyrogue.ui.screens.inventory_screen import InventoryScreen


class RecordingConsole:
    width = 80
    height = 60

    def __init__(self) -> None:
        self.lines: list[str] = []

    def clear(self) -> None:
        self.lines.clear()

    def print(self, *args, **kwargs) -> None:
        value = kwargs.get("string", args[2] if len(args) > 2 else "")
        self.lines.append(str(value))


def key_event(key: str) -> SimpleNamespace:
    return SimpleNamespace(sym=ord(key), mod=0, text=key)


def game_and_inventory() -> tuple[GameScreen, InventoryScreen]:
    engine = SimpleNamespace(map_width=80, map_height=45, state=GameStates.PLAYERS_TURN)
    game_screen = GameScreen(engine, seed=1234)
    return game_screen, InventoryScreen(game_screen)


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
