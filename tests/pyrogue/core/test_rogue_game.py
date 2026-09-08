import json

import pytest

from pyrogue.core.rogue_game import (
    GAME_VERSION,
    MAX_FLOOR,
    GameState,
    GameStatus,
    ItemKind,
    ItemState,
    MonsterState,
    SaveCompatibilityError,
    TrapKind,
    TrapState,
)
from pyrogue.core.save_manager import SaveManager

UNIDENTIFIED_ITEM_NAMES = {
    ItemKind.POTION: (
        "healing potion",
        "extra healing potion",
        "strength potion",
        "restore strength potion",
    ),
    ItemKind.SCROLL: (
        "identify scroll",
        "light scroll",
        "remove curse scroll",
        "enchant weapon scroll",
        "enchant armor scroll",
        "teleportation scroll",
        "magic mapping scroll",
    ),
    ItemKind.RING: (
        "ring of protection",
        "ring of add strength",
        "ring of sustain strength",
        "ring of searching",
        "ring of regeneration",
    ),
    ItemKind.WAND: (
        "wand of magic missile",
        "wand of light",
        "wand of lightning",
        "wand of fire",
        "wand of cold",
        "wand of teleport monster",
    ),
}


def test_seed_reproduces_initial_state() -> None:
    assert GameState(1234).to_dict() == GameState(1234).to_dict()


def test_unidentified_items_share_appearance_by_effect() -> None:
    game = GameState(1234)

    first = game._new_item(game.floor, ItemKind.POTION, "healing potion")
    second = game._new_item(game.floor, ItemKind.POTION, "healing potion")

    assert not first.identified
    assert first.appearance == second.appearance
    assert first.display_name == first.appearance

    first.identified = True
    assert first.display_name == first.name


@pytest.mark.parametrize(("kind", "names"), tuple(UNIDENTIFIED_ITEM_NAMES.items()))
def test_different_unidentified_effects_have_unique_appearances(kind: ItemKind, names: tuple[str, ...]) -> None:
    game = GameState(1234)
    items = [game._new_item(game.floor, kind, name) for name in names]

    assert len({item.appearance for item in items}) == len(names)


def test_appearance_mapping_survives_json_round_trip() -> None:
    game = GameState(1234)
    saved = game.to_dict()

    assert all(isinstance(values, list) for values in saved["appearances"].values())

    restored = GameState.from_dict(json.loads(json.dumps(saved)))

    assert restored._appearance_names == game._appearance_names
    for kind, names in UNIDENTIFIED_ITEM_NAMES.items():
        original = game._new_item(game.floor, kind, names[0])
        loaded = restored._new_item(restored.floor, kind, names[0])
        assert loaded.appearance == original.appearance


def test_every_floor_has_reachable_stairs() -> None:
    generator = GameState(1234).generator

    for floor_number in range(1, MAX_FLOOR + 1):
        floor = generator.generate(floor_number)
        assert floor.up_stairs is not None
        if floor_number < MAX_FLOOR:
            assert floor.down_stairs is not None
            assert generator._path_exists(floor, floor.up_stairs, floor.down_stairs)


def test_vi_commands_do_not_collide_with_search() -> None:
    game = GameState(1234)
    position = game.player.position

    result = game.execute("s")

    assert result.success
    assert result.turn_consumed
    assert game.player.position == position


def test_command_aliases_share_dispatch() -> None:
    rest = GameState(1234)
    wait = GameState(1234)

    assert rest.execute("rest") == wait.execute("wait")
    assert rest.to_dict() == wait.to_dict()
    assert rest.player.equipped_item_ids == {rest.player.equipped_weapon, rest.player.equipped_armor}


def test_json_round_trip_preserves_future_state() -> None:
    game = GameState(1234)
    game.execute(".")

    restored = GameState.from_dict(json.loads(json.dumps(game.to_dict())))

    assert restored.to_dict() == game.to_dict()
    assert restored.execute(".") == game.execute(".")


def test_unidentified_appearances_are_seeded_and_restored() -> None:
    first = GameState(1234)
    second = GameState(1234)
    for game in (first, second):
        game.floor.monsters.clear()
        game.player.position = game.floor.down_stairs
        assert game.execute("descend").success
    expected = sorted(
        (item.kind.value, item.appearance, item.display_name, item.identified)
        for item in first.floor.items
        if not item.identified
    )

    restored = GameState.from_dict(json.loads(json.dumps(first.to_dict())))

    assert expected
    assert first.to_dict()["appearances"] == second.to_dict()["appearances"]
    assert (
        sorted(
            (item.kind.value, item.appearance, item.display_name, item.identified)
            for item in restored.floor.items
            if not item.identified
        )
        == expected
    )


def test_amulet_requires_returning_to_surface() -> None:
    game = GameState(1234)

    for _ in range(1, MAX_FLOOR):
        game.floor.monsters.clear()
        game.player.position = game.floor.down_stairs
        assert game.descend().success

    game.floor.monsters.clear()
    amulet = next(item for item in game.floor.items if item.name == "amulet of yendor")
    game.player.position = amulet.position
    assert game.pickup().success
    assert game.status == GameStatus.PLAYING

    for _ in range(1, MAX_FLOOR):
        game.floor.monsters.clear()
        game.player.position = game.floor.up_stairs
        assert game.ascend().success

    game.player.position = game.floor.up_stairs
    result = game.ascend()

    assert result.success
    assert game.status == GameStatus.VICTORY


def test_old_save_version_is_rejected() -> None:
    game = GameState(1234).to_dict()
    game["spec_version"] = "0.2.0"

    with pytest.raises(SaveCompatibilityError):
        GameState.from_dict(game)

    assert GAME_VERSION == "0.3.0"


def test_save_manager_persists_canonical_json(tmp_path) -> None:
    game = GameState(1234)
    manager = SaveManager(tmp_path)

    assert manager.save_game_state(game.to_dict())
    assert manager.save_file.suffix == ".json"
    restored = GameState.from_dict(manager.load_game_state())

    assert restored.to_dict() == game.to_dict()


def test_death_is_terminal_and_reports_score() -> None:
    game = GameState(1234)
    game._die("test")

    assert game.is_dead
    assert game.death_summary == {"score": game.score, "deepest_floor": 1, "cause": "test"}
    assert not game.execute(".").success


@pytest.mark.parametrize(
    ("effect", "initial_hp", "initial_strength", "expected_hp", "expected_strength"),
    [
        ("healing", 1, 16, 9, 16),
        ("extra_healing", 1, 16, 12, 16),
        ("strength", 12, 10, 12, 11),
        ("restore_strength", 12, 10, 12, 16),
    ],
)
def test_potion_effects_change_canonical_player_state(
    effect: str,
    initial_hp: int,
    initial_strength: int,
    expected_hp: int,
    expected_strength: int,
) -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    game.player.hp = initial_hp
    game.player.strength = initial_strength
    potion = ItemState(1000, ItemKind.POTION, "test potion", effect=effect, position=None)
    game.player.inventory.append(potion)

    result = game.execute("quaff", [potion.id])

    assert result.success
    assert result.turn_consumed
    assert game.player.hp == expected_hp
    assert game.player.strength == expected_strength
    assert game.player.turns_played == 1
    assert potion not in game.player.inventory


def test_identify_scroll_identifies_unknown_pack_items() -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    scroll = ItemState(1000, ItemKind.SCROLL, "identify scroll", identified=False, effect="identify")
    potion = ItemState(1001, ItemKind.POTION, "healing potion", identified=False, appearance="red", effect="healing")
    ring = ItemState(
        1002, ItemKind.RING, "ring of protection", identified=False, appearance="opal", effect="protection"
    )
    wand = ItemState(
        1003,
        ItemKind.WAND,
        "wand of magic missile",
        identified=False,
        appearance="glass",
        effect="magic_missile",
    )
    game.player.inventory.extend((scroll, potion, ring, wand))

    result = game.execute("read", [scroll.id])

    assert result.success
    assert all(item.identified for item in (scroll, potion, ring, wand))


def test_remove_curse_scroll_clears_curses() -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    scroll = ItemState(1000, ItemKind.SCROLL, "remove curse scroll", effect="remove_curse")
    cursed_ring = ItemState(1001, ItemKind.RING, "ring of protection", cursed=True, effect="protection")
    game.player.inventory.extend((scroll, cursed_ring))

    result = game.execute("read", [scroll.id])

    assert result.success
    assert cursed_ring.cursed is False


@pytest.mark.parametrize("effect", ["enchant_weapon", "enchant_armor"])
def test_enchant_scroll_changes_equipped_item(effect: str) -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    item = game.player.equipped(ItemKind.WEAPON if effect == "enchant_weapon" else ItemKind.ARMOR)
    assert item is not None
    before = item.enchantment
    scroll = ItemState(1000, ItemKind.SCROLL, f"{effect} scroll", effect=effect)
    game.player.inventory.append(scroll)

    result = game.execute("read", [scroll.id])

    assert result.success
    assert item.enchantment == before + 1


def test_magic_mapping_scroll_reveals_the_floor() -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    game.floor.explored.clear()
    scroll = ItemState(1000, ItemKind.SCROLL, "magic mapping scroll", effect="magic_mapping")
    game.player.inventory.append(scroll)

    result = game.execute("read", [scroll.id])

    assert result.success
    assert len(game.floor.explored) == game.width * game.height


def test_teleportation_scroll_moves_the_player() -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    scroll = ItemState(1000, ItemKind.SCROLL, "teleportation scroll", effect="teleport")
    game.player.inventory.append(scroll)
    before = game.player.position

    result = game.execute("read", [scroll.id])

    assert result.success
    assert game.player.position != before


def _walkable_direction(game: GameState) -> tuple[str, tuple[int, int]]:
    directions = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}
    for name, (dx, dy) in directions.items():
        position = (game.player.x + dx, game.player.y + dy)
        if game.floor.is_walkable(position):
            return name, position
    raise AssertionError


@pytest.mark.parametrize("effect", ["magic_missile", "lightning", "fire", "cold"])
def test_damage_wands_hit_a_monster_and_consume_a_charge(effect: str) -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    monster = MonsterState(2000, "bat", *position, 20)
    wand = ItemState(1000, ItemKind.WAND, f"{effect} wand", effect=effect, charges=2, identified=False)
    game.floor.monsters.append(monster)
    game.player.inventory.append(wand)

    result = game.execute("zap", [wand.id, direction])

    assert result.success
    assert monster.hp < 20
    assert wand.charges == 1
    assert wand.identified
    assert game.player.turns_played == 1


def test_teleport_monster_wand_moves_the_target() -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    monster = MonsterState(2000, "bat", *position, 5)
    wand = ItemState(1000, ItemKind.WAND, "teleport wand", effect="teleport_monster", charges=1)
    game.floor.monsters.append(monster)
    game.player.inventory.append(wand)
    before = monster.x, monster.y

    result = game.execute("zap", [wand.id, direction])

    assert result.success
    assert (monster.x, monster.y) != before
    assert wand.charges == 0


@pytest.mark.parametrize("effect", ["protection", "strength", "sustain", "search", "regeneration"])
def test_ring_effects_are_preserved_when_equipped(effect: str) -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    ring = ItemState(1000, ItemKind.RING, f"{effect} ring", effect=effect, enchantment=1, identified=False)
    game.player.inventory.append(ring)
    before_defense = game.player.defense

    result = game.execute("put_on_ring", [ring.id])

    assert result.success
    assert ring.id in game.player.equipped_rings
    assert ring.effect == effect
    if effect == "protection":
        assert game.player.defense == before_defense - 1


def test_cursed_ring_cannot_be_removed() -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    ring = ItemState(1000, ItemKind.RING, "cursed ring", effect="protection", cursed=True)
    game.player.inventory.append(ring)

    assert game.execute("put_on_ring", [ring.id]).success
    result = game.execute("remove_ring", [ring.id])

    assert not result.success
    assert ring.id in game.player.equipped_rings


@pytest.mark.parametrize(
    ("kind", "expected_hp"),
    [
        (TrapKind.BEAR, 10),
        (TrapKind.ARROW, 9),
    ],
)
def test_damage_traps_reveal_and_damage_the_player(kind: TrapKind, expected_hp: int) -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    trap = TrapState(1000, kind, *position)
    game.floor.traps = [trap]

    result = game.execute("move", [direction])

    assert result.success
    assert trap.discovered
    assert game.player.hp == expected_hp
    assert game.current_floor == 1


def test_poison_dart_trap_deals_randomized_damage_and_weakens_the_player() -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    trap = TrapState(1000, TrapKind.POISON_DART, *position)
    game.floor.traps = [trap]

    result = game.execute("move", [direction])

    assert result.success
    assert trap.discovered
    assert 8 <= game.player.hp <= 11
    assert game.player.strength == 15
    assert game.current_floor == 1


def test_teleport_trap_reveals_and_moves_the_player() -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    trap = TrapState(1000, TrapKind.TELEPORT, *position)
    game.floor.traps = [trap]
    before = game.player.position

    result = game.execute("move", [direction])

    assert result.success
    assert trap.discovered
    assert game.player.hp == game.player.max_hp
    assert game.player.position != before


def test_trap_door_damages_and_moves_the_player_down_one_floor() -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    trap = TrapState(1000, TrapKind.TRAP_DOOR, *position)
    game.floor.traps = [trap]

    result = game.execute("move", [direction])

    assert result.success
    assert trap.discovered
    assert game.player.hp == 8
    assert game.current_floor == 2
    assert game.player.deepest_floor == 2
    assert game.player.position == game.floor.up_stairs
