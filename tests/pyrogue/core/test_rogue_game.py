import json
import random

import pytest

from pyrogue.core.rogue_game import (
    GAME_VERSION,
    HUNGERTIME,
    ITEM_KIND_WEIGHTS,
    ITEM_NAME_WEIGHTS,
    MAX_FLOOR,
    MAX_SCROLL_TITLE_LENGTH,
    MAX_TREASURE_ITEMS,
    MIN_TREASURE_ITEMS,
    TREASURE_ROOM_CHANCE,
    DungeonGenerator,
    FloorState,
    GameState,
    GameStatus,
    ItemKind,
    ItemState,
    MonsterState,
    Room,
    SaveCompatibilityError,
    Terrain,
    TrapKind,
    TrapState,
)
from pyrogue.core.save_manager import SaveManager

UNIDENTIFIED_ITEM_NAMES = {
    ItemKind.POTION: (
        "confusion potion",
        "hallucination potion",
        "poison potion",
        "strength potion",
        "see invisible potion",
        "healing potion",
        "monster detection potion",
        "magic detection potion",
        "raise level potion",
        "extra healing potion",
        "haste self potion",
        "restore strength potion",
        "blindness potion",
        "levitation potion",
    ),
    ItemKind.SCROLL: (
        "monster confusion scroll",
        "magic mapping scroll",
        "hold monster scroll",
        "sleep scroll",
        "enchant armor scroll",
        "identify potion scroll",
        "identify scroll",
        "identify weapon scroll",
        "identify armor scroll",
        "identify ring, wand or staff scroll",
        "scare monster scroll",
        "food detection scroll",
        "teleportation scroll",
        "enchant weapon scroll",
        "create monster scroll",
        "remove curse scroll",
        "aggravate monsters scroll",
        "protect armor scroll",
    ),
    ItemKind.RING: (
        "ring of protection",
        "ring of add strength",
        "ring of sustain strength",
        "ring of searching",
        "ring of see invisible",
        "ring of adornment",
        "ring of aggravate monster",
        "ring of add hit",
        "ring of add damage",
        "ring of regeneration",
        "ring of slow digestion",
        "ring of teleportation",
        "ring of stealth",
        "ring of maintain armor",
    ),
    ItemKind.WAND: (
        "wand of light",
        "wand of invisibility",
        "wand of lightning",
        "wand of fire",
        "wand of cold",
        "wand of polymorph",
        "wand of magic missile",
        "wand of haste monster",
        "wand of slow monster",
        "wand of drain life",
        "wand of nothing",
        "wand of teleport away",
        "wand of teleport to",
        "wand of cancellation",
    ),
}


def test_seed_reproduces_initial_state() -> None:
    assert GameState(1234).to_dict() == GameState(1234).to_dict()


def test_starting_equipment_matches_rogue_54() -> None:
    game = GameState(1234)
    items = {item.name: item for item in game.player.inventory}

    assert set(items) == {"food ration", "ring mail", "mace", "short bow", "arrow"}
    assert game.player.equipped_weapon == items["mace"].id
    assert game.player.equipped_armor == items["ring mail"].id
    assert game.player.effective_armor_class() == 6
    assert (items["mace"].damage_dice, items["mace"].hit_bonus, items["mace"].damage_bonus) == ((2, 4), 1, 1)
    assert items["short bow"].hit_bonus == 1
    assert 25 <= items["arrow"].quantity <= 39
    assert items["food ration"].nutrition == HUNGERTIME - 200


@pytest.mark.parametrize("seed", [5, 6, 28, 31, 33, 54, 62])
def test_starting_food_is_always_a_food_ration(seed: int) -> None:
    food = next(item for item in GameState(seed).player.inventory if item.kind == ItemKind.FOOD)

    assert food.name == "food ration"


def test_item_generation_weights_match_rogue_54() -> None:
    assert ITEM_KIND_WEIGHTS == (
        (ItemKind.POTION, 26),
        (ItemKind.SCROLL, 36),
        (ItemKind.FOOD, 16),
        (ItemKind.WEAPON, 7),
        (ItemKind.ARMOR, 7),
        (ItemKind.RING, 4),
        (ItemKind.WAND, 4),
    )
    expected = {
        ItemKind.WEAPON: (11, 11, 12, 12, 8, 10, 12, 12, 12),
        ItemKind.ARMOR: (20, 15, 15, 13, 12, 10, 10, 5),
        ItemKind.FOOD: (90, 10),
        ItemKind.POTION: (7, 8, 8, 13, 3, 13, 6, 6, 2, 5, 5, 13, 5, 6),
        ItemKind.SCROLL: (7, 4, 2, 3, 7, 10, 10, 6, 7, 10, 3, 2, 5, 8, 4, 7, 3, 2),
        ItemKind.RING: (9, 9, 5, 10, 10, 1, 10, 8, 8, 4, 9, 5, 7, 5),
        ItemKind.WAND: (12, 6, 3, 3, 3, 15, 10, 10, 11, 9, 1, 6, 6, 5),
    }
    expected_names = {
        ItemKind.WEAPON: (
            "mace",
            "long sword",
            "short bow",
            "arrow",
            "dagger",
            "two handed sword",
            "dart",
            "shuriken",
            "spear",
        ),
        ItemKind.ARMOR: (
            "leather armor",
            "ring mail",
            "studded leather armor",
            "scale mail",
            "chain mail",
            "splint mail",
            "banded mail",
            "plate mail",
        ),
        ItemKind.FOOD: ("food ration", "slime mold"),
        ItemKind.POTION: UNIDENTIFIED_ITEM_NAMES[ItemKind.POTION],
        ItemKind.SCROLL: UNIDENTIFIED_ITEM_NAMES[ItemKind.SCROLL],
        ItemKind.RING: UNIDENTIFIED_ITEM_NAMES[ItemKind.RING],
        ItemKind.WAND: UNIDENTIFIED_ITEM_NAMES[ItemKind.WAND],
    }

    assert {kind: tuple(weights) for kind, weights in ITEM_NAME_WEIGHTS.items() if kind in expected_names} == (
        expected_names
    )
    assert {
        kind: tuple(weights.values())
        for kind, weights in ITEM_NAME_WEIGHTS.items()
        if kind not in {ItemKind.GOLD, ItemKind.AMULET}
    } == expected


def test_treasure_room_generation_adds_a_pile_of_items_and_monsters() -> None:
    game = GameState(4323)
    floor = game.generator.generate(2)
    game.rng.seed(2)

    game._spawn_treasure_room(floor)

    assert TREASURE_ROOM_CHANCE == 20
    assert MIN_TREASURE_ITEMS == 2
    assert MAX_TREASURE_ITEMS == 10
    assert MIN_TREASURE_ITEMS <= len(floor.items) < MAX_TREASURE_ITEMS
    assert len(floor.monsters) >= len(floor.items) + 2
    assert all(monster.mean_override for monster in floor.monsters)


def test_floor_item_generation_keeps_every_successful_spawn(monkeypatch: pytest.MonkeyPatch) -> None:
    class GuaranteedItemRng:
        def randrange(self, stop: int) -> int:
            return 1 if stop in {2, 10, 20} else 0

        def randint(self, start: int, stop: int) -> int:
            return start

        def choices(self, population: tuple[ItemKind, ...], *, weights: list[int], k: int) -> list[ItemKind]:
            return [population[0]] * k

        def choice(self, population: list[tuple[int, int]]) -> tuple[int, int]:
            return population[0]

    game = GameState(4323)
    floor = game.generator.generate(2)
    monkeypatch.setattr(game, "rng", GuaranteedItemRng())

    game._spawn_items(floor)

    assert len(floor.items) == 9


def test_unidentified_items_share_appearance_by_effect() -> None:
    game = GameState(1234)

    first = game._new_item(game.floor, ItemKind.POTION, "healing potion")
    second = game._new_item(game.floor, ItemKind.POTION, "healing potion")

    assert not first.identified
    assert first.appearance == second.appearance
    assert first.display_name == first.appearance

    first.identified = True
    assert first.display_name == first.name


def test_unidentified_appearances_match_rogue_54_item_forms() -> None:
    appearances = GameState(1234)._appearance_names
    scroll_titles = [
        value.removeprefix("scroll titled '").removesuffix("'") for value in appearances[ItemKind.SCROLL].values()
    ]

    assert all(value.endswith(" potion") for value in appearances[ItemKind.POTION].values())
    assert all(2 <= len(title.split()) <= 4 for title in scroll_titles)
    assert all(value.endswith(" ring") for value in appearances[ItemKind.RING].values())
    assert all(value.endswith((" wand", " staff")) for value in appearances[ItemKind.WAND].values())


def test_scroll_appearance_titles_respect_rogue_54_length_limit() -> None:
    titles = GameState(25)._appearance_names[ItemKind.SCROLL].values()

    assert all(
        len(title.removeprefix("scroll titled '").removesuffix("'")) <= MAX_SCROLL_TITLE_LENGTH for title in titles
    )


def test_identifying_an_item_remembers_its_type_for_future_items() -> None:
    game = GameState(1235)
    potion = game._new_item(game.floor, ItemKind.POTION, "healing potion")
    game.player.inventory.append(potion)

    assert game.quaff(potion.id).success

    future_potion = game._new_item(game.floor, ItemKind.POTION, "healing potion")
    assert future_potion.identified
    assert future_potion.display_name == "healing potion"


@pytest.mark.parametrize(("kind", "names"), tuple(UNIDENTIFIED_ITEM_NAMES.items()))
def test_different_unidentified_effects_have_unique_appearances(kind: ItemKind, names: tuple[str, ...]) -> None:
    game = GameState(1234)
    items = [game._new_item(game.floor, kind, name) for name in names]

    assert len({item.appearance for item in items}) == len(names)


@pytest.mark.parametrize(
    ("name", "minimum", "maximum"),
    [("wand of light", 10, 19), ("wand of magic missile", 3, 7)],
)
def test_wand_charges_match_rogue_54(name: str, minimum: int, maximum: int) -> None:
    game = GameState(4321)

    charges = [game._new_item(game.floor, ItemKind.WAND, name).charges for _ in range(100)]

    assert min(charges) >= minimum
    assert max(charges) <= maximum


@pytest.mark.parametrize("name", ["ring of aggravate monster", "ring of teleportation"])
def test_source_cursed_rings_are_always_cursed(name: str) -> None:
    game = GameState(4322)

    ring = game._new_item(game.floor, ItemKind.RING, name)

    assert ring.cursed


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
    for seed in (1234, 5678, 9012):
        generator = GameState(seed).generator
        for floor_number in range(1, MAX_FLOOR + 1):
            floor = generator.generate(floor_number)
            assert floor.up_stairs is not None
            if floor_number < MAX_FLOOR:
                assert floor.down_stairs is not None
                assert generator._path_exists(floor, floor.up_stairs, floor.down_stairs)


def test_room_layout_uses_nine_regions_and_varies_by_seed() -> None:
    first = DungeonGenerator(rng=random.Random(1)).generate(1)  # noqa: S311
    second = DungeonGenerator(rng=random.Random(2)).generate(1)  # noqa: S311

    assert 6 <= len(first.rooms) <= 9
    assert 6 <= len(second.rooms) <= 9
    assert {(room.x, room.y, room.width, room.height) for room in first.rooms} != {
        (room.x, room.y, room.width, room.height) for room in second.rooms
    }
    assert first.rooms


def test_dark_rooms_are_seeded_and_not_present_on_first_floor() -> None:
    generator = DungeonGenerator(rng=random.Random(4))  # noqa: S311

    assert not any(room.is_dark for room in generator.generate(1).rooms)
    assert any(room.is_dark for room in generator.generate(MAX_FLOOR).rooms)
    assert any(room.is_maze for room in DungeonGenerator(rng=random.Random(1)).generate(MAX_FLOOR).rooms)  # noqa: S311
    assert generator.generate(7).rooms


def test_rooms_occupy_distinct_cells_and_doors_are_on_room_edges() -> None:
    floor = DungeonGenerator(rng=random.Random(4)).generate(7)  # noqa: S311
    cell_width, cell_height = floor.width // 3, floor.height // 3
    cells = {
        ((room.x + room.width // 2) // cell_width, (room.y + room.height // 2) // cell_height) for room in floor.rooms
    }
    doors = [
        (x, y) for y, row in enumerate(floor.tiles) for x, terrain in enumerate(row) if terrain == Terrain.DOOR_CLOSED
    ]

    assert len(cells) == len(floor.rooms)
    assert doors
    assert all(
        any(
            room.contains(x, y) and (x in {room.x, room.x + room.width - 1} or y in {room.y, room.y + room.height - 1})
            for room in floor.rooms
        )
        for x, y in doors
    )
    for x, y in doors:
        room = next(room for room in floor.rooms if room.contains(x, y))
        dx, dy = (
            (-1, 0) if x == room.x else (1, 0) if x == room.x + room.width - 1 else (0, -1) if y == room.y else (0, 1)
        )
        assert floor.tile_at((x - dx, y - dy)) != Terrain.WALL
        assert floor.tile_at((x + dx, y + dy)) != Terrain.WALL


def test_maze_room_keeps_a_connected_lattice_of_passages() -> None:
    generator = DungeonGenerator(rng=random.Random(1))  # noqa: S311
    floor = generator.generate(MAX_FLOOR)
    maze_room = next(room for room in floor.rooms if room.is_maze)
    passages = {
        (x, y)
        for y in range(maze_room.y + 1, maze_room.y + maze_room.height - 1)
        for x in range(maze_room.x + 1, maze_room.x + maze_room.width - 1)
        if floor.tile_at((x, y)) != Terrain.WALL
    }

    assert any(
        floor.tile_at((x, y)) == Terrain.WALL
        for y in range(maze_room.y + 1, maze_room.y + maze_room.height - 1)
        for x in range(maze_room.x + 1, maze_room.x + maze_room.width - 1)
    )
    assert passages <= generator._reachable_positions(floor.tiles, next(iter(passages)))
    assert all(
        floor.tile_at((x, y)) != Terrain.DOOR_CLOSED
        for y in range(maze_room.y, maze_room.y + maze_room.height)
        for x in range(maze_room.x, maze_room.x + maze_room.width)
    )
    maze_exits = {
        (x, y)
        for y in range(maze_room.y, maze_room.y + maze_room.height)
        for x in range(maze_room.x, maze_room.x + maze_room.width)
        if (
            x in {maze_room.x, maze_room.x + maze_room.width - 1}
            or y in {maze_room.y, maze_room.y + maze_room.height - 1}
        )
        and floor.tile_at((x, y)) != Terrain.WALL
    }
    assert maze_exits
    assert floor.up_stairs is not None
    assert maze_exits <= generator._reachable_positions(floor.tiles, floor.up_stairs)
    assert all(
        sum(floor.tile_at((x + dx, y + dy)) != Terrain.WALL for dx in range(2) for dy in range(2)) < 4
        for y in range(maze_room.y + 1, maze_room.y + maze_room.height - 2)
        for x in range(maze_room.x + 1, maze_room.x + maze_room.width - 2)
    )


def test_room_graph_can_have_additional_corridors() -> None:
    class CountingGenerator(DungeonGenerator):
        region_corridors = 0

        def _carve_corridor(self, tiles: list[list[Terrain]], first: tuple[int, int], second: tuple[int, int]) -> None:
            cell_width, cell_height = self.width // 3, self.height // 3
            first_region = first[0] // cell_width, first[1] // cell_height
            second_region = second[0] // cell_width, second[1] // cell_height
            if first_region != second_region:
                self.region_corridors += 1
            super()._carve_corridor(tiles, first, second)

    generator = CountingGenerator(rng=random.Random(9))  # noqa: S311
    generator.generate(1)

    assert 8 < generator.region_corridors <= 12


def _use_generated_dark_room(game: GameState) -> Room:
    floor = DungeonGenerator(rng=random.Random(4)).generate(MAX_FLOOR)  # noqa: S311
    room = next(room for room in floor.rooms if room.is_dark)
    game.floor.tiles = floor.tiles
    game.floor.rooms = floor.rooms
    game.player.position = room.center
    return room


def test_visibility_is_limited_inside_a_dark_room() -> None:
    game = GameState(1234)
    room = _use_generated_dark_room(game)

    visible = game.visible_positions(update_explored=False)

    assert visible <= {(game.player.x + dx, game.player.y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}


def test_light_illuminates_a_dark_room_and_survives_saving() -> None:
    game = GameState(1234)
    room = _use_generated_dark_room(game)
    game.floor.monsters.clear()
    scroll = ItemState(1000, ItemKind.SCROLL, "light scroll", effect="light")
    game.player.inventory.append(scroll)

    assert game.read(scroll.id).success

    assert game.floor.rooms[0].is_lit
    assert all(
        (x, y) in game.visible_positions(update_explored=False)
        for y in range(room.y, room.y + room.height)
        for x in range(room.x, room.x + room.width)
        if game.floor.tile_at((x, y)) != Terrain.WALL
    )
    restored = GameState.from_dict(json.loads(json.dumps(game.to_dict())))
    assert restored.floor.rooms[0].is_lit


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


def test_slash_identifies_one_unknown_item() -> None:
    game = GameState(1234)
    item = ItemState(
        1000,
        ItemKind.POTION,
        "healing potion",
        appearance="red",
        identified=False,
        effect="healing",
    )
    game.player.inventory.append(item)

    result = game.execute("/")

    assert result.success
    assert result.message == "You identify the healing potion."
    assert not result.turn_consumed
    assert item.identified


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


def test_new_destination_floor_monsters_wait_until_the_next_player_action(monkeypatch: pytest.MonkeyPatch) -> None:
    game = GameState(1234)
    spawned: list[MonsterState] = []
    spawn_positions: list[tuple[int, int]] = []

    def spawn_arrival_monster(destination: FloorState) -> None:
        arrival = destination.up_stairs
        monster_position = (arrival[0] + 1, arrival[1])
        destination.set_tile(monster_position, Terrain.FLOOR)
        monster = MonsterState(900, "snake", *monster_position, 100)
        destination.monsters.append(monster)
        spawned.append(monster)
        spawn_positions.append(monster_position)

    monkeypatch.setattr(game, "_spawn_monsters", spawn_arrival_monster)
    game.player.position = game.floor.down_stairs

    result = game.descend()

    monster = spawned[0]
    assert result.turn_consumed
    assert not monster.running
    assert (monster.x, monster.y) == spawn_positions[0]


def test_cached_destination_floor_monsters_act_on_arrival() -> None:
    game = GameState(1235)
    destination = game.generator.generate(2)
    arrival = destination.up_stairs
    width = len(destination.tiles[0])
    dx = 1 if arrival[0] + 3 < width - 1 else -1
    monster_position = (arrival[0] + 3 * dx, arrival[1])
    for offset in range(4):
        destination.set_tile((arrival[0] + offset * dx, arrival[1]), Terrain.FLOOR)
    monster = MonsterState(901, "snake", *monster_position, 100, running=True)
    destination.monsters.append(monster)
    game.floors[2] = destination
    game.player.position = game.floor.down_stairs

    result = game.descend()

    assert result.turn_consumed
    assert abs(monster.x - arrival[0]) < 3


def test_monsters_get_carry_packs_at_the_current_deepest_floor(monkeypatch: pytest.MonkeyPatch) -> None:
    game = GameState(1236)
    game.player.deepest_floor = MAX_FLOOR
    game.rng.seed(2)
    randrange = game.rng.randrange

    def force_carry_roll(stop: int, *args: int) -> int:
        return 0 if stop == 100 and not args else randrange(stop, *args)

    monkeypatch.setattr("pyrogue.core.rogue_game.MONSTER_SPAWN_ORDER", ("centaur",) * 26)
    monkeypatch.setattr(game.rng, "randrange", force_carry_roll)
    deepest_floor = game.generator.generate(MAX_FLOOR)
    previous_floor = game.generator.generate(2)

    game._spawn_monsters(deepest_floor)
    game._spawn_monsters(previous_floor)

    assert all(monster.carried_items for monster in deepest_floor.monsters)
    assert all(monster.carried_items[0].position is None for monster in deepest_floor.monsters)
    assert all(not monster.carried_items for monster in previous_floor.monsters)


@pytest.mark.parametrize(
    ("item_roll", "expected_kind"),
    [
        (0, ItemKind.POTION),
        (26, ItemKind.SCROLL),
        (62, ItemKind.FOOD),
        (78, ItemKind.WEAPON),
        (85, ItemKind.ARMOR),
        (92, ItemKind.RING),
        (96, ItemKind.WAND),
    ],
)
def test_monster_pack_item_kind_uses_rogue_54_probabilities(
    monkeypatch: pytest.MonkeyPatch, item_roll: int, expected_kind: ItemKind
) -> None:
    game = GameState(1238)
    floor = game.generator.generate(1)
    monkeypatch.setattr("pyrogue.core.rogue_game.MONSTER_SPAWN_ORDER", ("centaur",) * 26)
    randrange = game.rng.randrange
    rolls = iter((0, item_roll, 99, 99, 99, 99))

    def force_pack_rolls(stop: int, *args: int) -> int:
        if stop == 100 and not args:
            return next(rolls)
        if stop in {5, 10} and not args:
            return 0
        return randrange(stop, *args)

    monkeypatch.setattr(game.rng, "randrange", force_pack_rolls)

    game._spawn_monsters(floor)

    assert floor.monsters[0].carried_items[0].kind == expected_kind
    assert all(not monster.carried_items for monster in floor.monsters[1:])


def test_killing_monster_drops_its_carried_items() -> None:
    game = GameState(1237)
    game.floor.monsters.clear()
    monster = MonsterState(902, "centaur", 10, 10, 1)
    carried_item = ItemState(903, ItemKind.POTION, "healing potion")
    monster.carried_items.append(carried_item)
    game.floor.monsters.append(monster)

    game._defeat_monster(monster)

    assert carried_item.position == (monster.x, monster.y)
    assert carried_item in game.floor.items


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


def test_victory_summary_preserves_deepest_floor_after_return() -> None:
    game = GameState(1234)

    for _ in range(1, MAX_FLOOR):
        game.floor.monsters.clear()
        game.player.position = game.floor.down_stairs
        assert game.descend().success

    assert game.player.deepest_floor == MAX_FLOOR
    game.floor.monsters.clear()
    amulet = next(item for item in game.floor.items if item.name == "amulet of yendor")
    game.player.position = amulet.position
    assert game.pickup().success

    for _ in range(1, MAX_FLOOR):
        game.floor.monsters.clear()
        game.player.position = game.floor.up_stairs
        assert game.ascend().success

    game.player.position = game.floor.up_stairs
    result = game.ascend()

    assert result.data == {"deepest_floor": MAX_FLOOR, "score": game.score}
    saved = game.to_dict()
    assert saved["current_floor"] == 1
    assert saved["player"]["deepest_floor"] == MAX_FLOOR


def test_old_save_version_is_rejected() -> None:
    game = GameState(1234).to_dict()
    game["spec_version"] = "0.3.4"

    with pytest.raises(SaveCompatibilityError):
        GameState.from_dict(game)

    assert GAME_VERSION == "0.3.5"


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
        ("healing", 1, 16, 5, 16),
        ("extra_healing", 1, 16, 9, 16),
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
    game.rng.seed(1234)
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


def test_enchant_armor_scroll_changes_equipped_item() -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    item = game.player.equipped(ItemKind.ARMOR)
    assert item is not None
    before = item.enchantment
    scroll = ItemState(1000, ItemKind.SCROLL, "enchant armor scroll", effect="enchant_armor")
    game.player.inventory.append(scroll)

    result = game.execute("read", [scroll.id])

    assert result.success
    assert item.enchantment == before + 1


@pytest.mark.parametrize(("roll", "bonus"), [(0, "hit_bonus"), (1, "damage_bonus")])
def test_enchant_weapon_scroll_adds_to_one_bonus_only(monkeypatch, roll: int, bonus: str) -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    weapon = game.player.equipped(ItemKind.WEAPON)
    assert weapon is not None
    before = weapon.hit_bonus, weapon.damage_bonus
    scroll = ItemState(1000, ItemKind.SCROLL, "enchant weapon scroll", effect="enchant_weapon")
    game.player.inventory.append(scroll)
    original_randrange = game.rng.randrange

    def choose_enchantment(stop: int) -> int:
        return roll if stop == 2 else original_randrange(stop)

    monkeypatch.setattr(game.rng, "randrange", choose_enchantment)

    result = game.execute("read", [scroll.id])

    assert result.success
    assert weapon.hit_bonus == before[0] + (bonus == "hit_bonus")
    assert weapon.damage_bonus == before[1] + (bonus == "damage_bonus")


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


def test_trap_door_moves_the_player_down_one_floor_without_damage() -> None:
    game = GameState(1234)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    trap = TrapState(1000, TrapKind.TRAP_DOOR, *position)
    game.floor.traps = [trap]

    result = game.execute("move", [direction])

    assert result.success
    assert trap.discovered
    assert game.player.hp == game.player.max_hp
    assert game.current_floor == 2
    assert game.player.deepest_floor == 2
    assert game.player.position == game.floor.up_stairs
