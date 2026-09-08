from types import SimpleNamespace

from pyrogue.core.game_states import GameStates
from pyrogue.core.rogue_game import GameState, ItemKind, ItemState
from pyrogue.ui.screens.game_screen import GameScreen


def test_gui_read_key_uses_the_canonical_scroll_command() -> None:
    screen = GameScreen(None, seed=20)
    game = screen.rogue_game
    game.floor.monsters.clear()
    scroll = ItemState(id=930, kind=ItemKind.SCROLL, name="light scroll", effect="light")
    game.player.inventory.append(scroll)

    screen.input_handler.handle_key(SimpleNamespace(sym=ord("r"), mod=0, text="r"))

    assert scroll not in game.player.inventory
    assert game.player.turns_played == 1


def test_gui_slash_key_uses_canonical_item_identification() -> None:
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

    assert screen.input_handler.handle_key(SimpleNamespace(sym=ord("/"), mod=0, text="/")) is None

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
