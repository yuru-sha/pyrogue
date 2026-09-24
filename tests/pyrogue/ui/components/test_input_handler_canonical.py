import json
from types import SimpleNamespace

import tcod.event

from pyrogue.core.game_states import GameStates
from pyrogue.core.rogue_game import GAME_VERSION, GameState, ItemKind, ItemState
from pyrogue.core.save_manager import SaveManager
from pyrogue.ui.screens.game_screen import GameScreen
from pyrogue.ui.screens.inventory_screen import InventoryScreen


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


def test_gui_targeting_uses_shared_cardinal_direction_mapping() -> None:
    screen = GameScreen(None, seed=23)
    handler = screen.input_handler
    handler.start_targeting(5, 5)

    for key, expected in (
        (tcod.event.KeySym.LEFT, (4, 5)),
        (ord("l"), (5, 5)),
        (tcod.event.KeySym.UP, (5, 4)),
        (ord("j"), (5, 5)),
        (ord("y"), (5, 5)),
    ):
        handler.handle_key(SimpleNamespace(sym=key, mod=0, text=""))
        assert (handler.targeting_x, handler.targeting_y) == expected


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
