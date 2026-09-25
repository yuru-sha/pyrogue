import json
from types import SimpleNamespace

import tcod.event

from pyrogue.core.game_states import GameStates
from pyrogue.core.rogue_game import GAME_VERSION, GameState, ItemKind, ItemState, MonsterState, Terrain
from pyrogue.core.save_manager import SaveManager
from pyrogue.ui.screens.game_screen import GameScreen
from pyrogue.ui.screens.inventory_screen import InventoryScreen
from pyrogue.ui.screens.options_screen import OptionsScreen


def test_gui_fight_key_prompts_for_direction_and_attacks_that_monster() -> None:
    screen = GameScreen(None, seed=108)
    game = screen.rogue_game
    game.floor.monsters.clear()
    x, y = game.player.position
    north = MonsterState(1081, "bat", x, y - 1, 1)
    east = MonsterState(1082, "bat", x + 1, y, 1)
    game.floor.monsters.extend((north, east))

    assert screen.input_handler.handle_key(SimpleNamespace(sym=ord("f"), mod=0, text="f")) is None
    assert screen.input_handler.direction_selection_mode
    screen.input_handler.handle_key(SimpleNamespace(sym=ord("l"), mod=0, text="l"))

    assert east.hp < 1
    assert north.hp == 1
    assert game.player.turns_played == 1


def test_cancelled_fight_direction_does_not_consume_a_turn() -> None:
    screen = GameScreen(None, seed=108)
    turns_before = screen.player.turns_played

    screen.input_handler.handle_key(SimpleNamespace(sym=ord("f"), mod=0, text="f"))
    screen.input_handler.handle_key(SimpleNamespace(sym=tcod.event.KeySym.ESCAPE, mod=0, text=""))

    assert not screen.input_handler.direction_selection_mode
    assert screen.player.turns_played == turns_before


def test_gui_numeric_prefix_repeats_the_canonical_command() -> None:
    screen = GameScreen(None, seed=108)
    game = screen.rogue_game
    game.floor.monsters.clear()
    screen.input_handler.handle_key(SimpleNamespace(sym=ord("3"), mod=0, text="3"))
    screen.input_handler.handle_key(SimpleNamespace(sym=ord("."), mod=0, text="."))

    assert game.player.turns_played == 3


def test_gui_uppercase_direction_runs_through_a_corridor() -> None:
    screen = GameScreen(None, seed=108)
    game = screen.rogue_game
    game.floor.monsters.clear()
    x, y = game.player.position
    for row in range(y - 1, y + 2):
        for column in range(x - 1, x + 4):
            game.floor.set_tile((column, row), Terrain.WALL)
    for column in range(x, x + 3):
        game.floor.set_tile((column, y), Terrain.FLOOR)

    screen.input_handler.handle_key(SimpleNamespace(sym=ord("L"), mod=0, text="L"))

    assert game.player.position == (x + 2, y)
    assert game.player.turns_played == 2


def test_gui_options_key_opens_options_without_consuming_a_turn() -> None:
    screen = GameScreen(None, seed=108)
    turns_before = screen.player.turns_played

    state = screen.input_handler.handle_key(SimpleNamespace(sym=ord("o"), mod=0, text="o"))

    assert state == GameStates.OPTIONS_MENU
    assert screen.player.turns_played == turns_before


def test_gui_call_item_uses_canonical_command_without_consuming_a_turn() -> None:
    screen = GameScreen(None, seed=108)
    game = screen.rogue_game
    item = ItemState(1084, ItemKind.POTION, "healing potion", appearance="red potion", identified=False)
    game.player.inventory.append(item)
    inventory = InventoryScreen(screen)
    inventory.selected_index = game.player.inventory.index(item)

    assert screen.input_handler.handle_key(SimpleNamespace(sym=ord("c"), mod=0, text="c")) == GameStates.SHOW_INVENTORY
    inventory.handle_input(SimpleNamespace(sym=tcod.event.KeySym.RETURN, mod=0, text=""))
    for char in "emergency":
        inventory.handle_input(SimpleNamespace(sym=ord(char), mod=0, text=char))
    inventory.handle_input(SimpleNamespace(sym=tcod.event.KeySym.RETURN, mod=0, text=""))

    assert item.display_name == "red potion called emergency"
    assert game.player.turns_played == 0


def test_options_screen_changes_display_only_state_and_returns_to_game() -> None:
    game_screen = GameScreen(None, seed=108)
    options = OptionsScreen(SimpleNamespace(game_screen=game_screen, console=None))
    enabled_before = game_screen.fov_manager.fov_enabled
    turns_before = game_screen.player.turns_played

    assert options.handle_input(SimpleNamespace(sym=tcod.event.KeySym.TAB)) is None
    assert game_screen.fov_manager.fov_enabled is not enabled_before
    assert options.handle_input(SimpleNamespace(sym=tcod.event.KeySym.ESCAPE)) == GameStates.PLAYERS_TURN
    assert game_screen.player.turns_played == turns_before


def test_gui_routes_commands_without_legacy_game_logic_or_handler() -> None:
    screen = GameScreen(None, seed=20)

    assert not hasattr(screen, "game_logic")
    assert not hasattr(screen.input_handler, "command_handler")


def test_gui_read_key_selects_a_scroll_for_the_canonical_command() -> None:
    screen = GameScreen(None, seed=20)
    game = screen.rogue_game
    game.floor.monsters.clear()
    scroll = ItemState(id=930, kind=ItemKind.SCROLL, name="light scroll", effect="light")
    game.player.inventory.append(scroll)
    inventory = InventoryScreen(screen)

    assert screen.input_handler.handle_key(SimpleNamespace(sym=ord("r"), mod=0, text="r")) == GameStates.SHOW_INVENTORY
    inventory.handle_input(SimpleNamespace(sym=ord("a"), mod=0, text="a"))

    assert scroll not in game.player.inventory
    assert game.player.turns_played == 1


def test_gui_slash_key_uses_canonical_item_identification(monkeypatch) -> None:
    screen = GameScreen(None, seed=22)
    game = screen.rogue_game
    item = ItemState(
        id=932,
        kind=ItemKind.POTION,
        name="healing potion",
        appearance="red",
        identified=False,
        effect="healing",
    )
    game.player.inventory.append(item)
    results = []
    execute = game.execute

    def record_execute(command, args=(), **kwargs):
        result = execute(command, args, **kwargs)
        results.append(result)
        return result

    monkeypatch.setattr(game, "execute", record_execute)

    assert screen.input_handler.handle_key(SimpleNamespace(sym=ord("/"), mod=0, text="/")) is None

    result = results[-1]
    assert result.success
    assert result.message == "You identify the healing potion."
    assert not result.turn_consumed
    assert item.identified


def test_gui_zap_direction_uses_the_canonical_wand_command() -> None:
    screen = GameScreen(None, seed=21)
    game: GameState = screen.rogue_game
    game.floor.monsters.clear()
    wand = ItemState(id=931, kind=ItemKind.WAND, name="wand of magic missile", effect="magic_missile", charges=1)
    game.player.inventory.append(wand)

    assert screen.input_handler.handle_key(SimpleNamespace(sym=ord("z"), mod=0, text="z")) == GameStates.SHOW_INVENTORY

    screen.input_handler.begin_direction_selection("zap", wand.id)
    screen.input_handler.handle_key(SimpleNamespace(sym=ord("l"), mod=0, text="l"))

    assert not screen.input_handler.direction_selection_mode
    assert wand.charges == 0
    assert game.player.turns_played == 1


def test_gui_tab_toggles_canonical_fov_without_mutating_state() -> None:
    screen = GameScreen(None, seed=22)
    game = screen.rogue_game
    game.floor.explored.clear()
    state_before = game.to_dict()

    assert screen.fov_manager.fov_enabled
    assert screen.input_handler.handle_key(SimpleNamespace(sym=tcod.event.KeySym.TAB, mod=0, text="")) is None

    assert not screen.fov_manager.fov_enabled
    assert game.floor.explored == set()
    assert game.to_dict() == state_before

    assert screen.input_handler.handle_key(SimpleNamespace(sym=tcod.event.KeySym.TAB, mod=0, text="")) is None
    assert screen.fov_manager.fov_enabled
    assert game.floor.explored == set()
    assert game.to_dict() == state_before


def test_gui_ctrl_l_reports_legacy_save_incompatibility_and_preserves_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAVE_DIRECTORY", str(tmp_path))
    screen = GameScreen(None, seed=24)
    manager = SaveManager(tmp_path)
    manager.save_file.write_text(
        json.dumps({"spec_version": GAME_VERSION, "player_stats": {}, "current_floor": 1}),
        encoding="utf-8",
    )
    before = manager.save_file.read_bytes()

    screen.input_handler.handle_key(SimpleNamespace(sym=ord("l"), mod=tcod.event.Modifier.CTRL, text="l"))

    assert any("Unsupported legacy save format" in message for message in screen.rogue_game.messages)
    assert manager.save_file.read_bytes() == before
