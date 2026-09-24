import pytest

from pyrogue.core.rogue_game import (
    MONSTER_TYPES,
    EntityKind,
    GameState,
    ItemKind,
    ItemState,
    MonsterState,
    Terrain,
    TrapKind,
    TrapState,
)
from pyrogue.core.save_manager import SaveManager


def _walkable_direction(game: GameState) -> tuple[str, tuple[int, int]]:
    for name, (dx, dy) in (("east", (1, 0)), ("west", (-1, 0)), ("south", (0, 1)), ("north", (0, -1))):
        position = game.player.x + dx, game.player.y + dy
        if game.floor.is_walkable(position):
            return name, position
    raise AssertionError


def test_reading_light_scroll_illuminates_current_room() -> None:
    game = GameState(seed=1)
    game.floor.monsters.clear()
    game.floor.explored.clear()
    scroll = ItemState(
        id=900,
        kind=ItemKind.SCROLL,
        name="light scroll",
        effect="light",
        identified=False,
    )
    game.player.inventory.append(scroll)

    result = game.read()

    assert result.success
    assert result.turn_consumed
    assert result.message == "The room is lit."
    assert scroll not in game.player.inventory
    assert any(game.floor.tile_at(position).value != "wall" for position in game.floor.explored)


def test_reading_teleport_scroll_moves_player_without_changing_floor() -> None:
    game = GameState(seed=2)
    game.floor.monsters.clear()
    old_position = game.player.position
    scroll = ItemState(id=901, kind=ItemKind.SCROLL, name="teleport scroll", effect="teleport")
    game.player.inventory.append(scroll)

    result = game.read(scroll.id)

    assert result.success
    assert result.turn_consumed
    assert game.current_floor == 1
    assert game.player.position != old_position
    assert "teleport" in result.message.lower()
    assert scroll not in game.player.inventory


def test_quaffing_hallucination_potion_starts_the_rogue_duration() -> None:
    game = GameState(seed=22)
    game.floor.monsters.clear()
    potion = ItemState(
        id=922,
        kind=ItemKind.POTION,
        name="hallucination potion",
        effect="hallucination",
        identified=False,
    )
    game.player.inventory.append(potion)

    result = game.quaff(potion.id)

    assert result.success
    assert result.turn_consumed
    assert game.player.hallucination_turns == 849
    assert potion not in game.player.inventory


def test_poison_potion_reduces_strength_unless_sustain_ring_is_worn() -> None:
    without_ring = GameState(seed=23)
    without_ring.floor.monsters.clear()
    poison = ItemState(923, ItemKind.POTION, "poison potion", effect="poison")
    without_ring.player.inventory.append(poison)
    without_ring.rng.seed(23)
    strength = without_ring.player.strength

    result = without_ring.quaff(poison.id)

    assert result.success
    assert result.turn_consumed
    assert 1 <= strength - without_ring.player.strength <= 3
    assert poison not in without_ring.player.inventory

    with_ring = GameState(seed=23)
    with_ring.floor.monsters.clear()
    poison = ItemState(924, ItemKind.POTION, "poison potion", effect="poison")
    ring = ItemState(925, ItemKind.RING, "ring of sustain strength", effect="sustain")
    with_ring.player.inventory.extend((poison, ring))
    assert with_ring.equip(ring.id, ItemKind.RING).success
    strength = with_ring.player.strength
    with_ring.rng.seed(23)

    result = with_ring.quaff(poison.id)

    assert result.success
    assert result.turn_consumed
    assert with_ring.player.strength == strength
    assert poison not in with_ring.player.inventory


@pytest.mark.parametrize(
    ("name", "effect", "state"),
    [
        ("confusion potion", "confusion", "confused_turns"),
        ("see invisible potion", "see_invisible", "see_invisible_turns"),
        ("blindness potion", "blindness", "blind_turns"),
        ("levitation potion", "levitation", "levitation_turns"),
        ("haste self potion", "haste_self", "haste_turns"),
    ],
)
def test_rogue_potions_apply_their_status_effects(name: str, effect: str, state: str) -> None:
    game = GameState(seed=24)
    game.floor.monsters.clear()
    potion = ItemState(930, ItemKind.POTION, name, effect=effect)
    game.player.inventory.append(potion)

    result = game.quaff(potion.id)

    assert result.success
    assert result.turn_consumed
    assert getattr(game.player, state) > 0


def test_detection_and_raise_level_potions_change_game_state() -> None:
    game = GameState(seed=241)
    game.floor.monsters.clear()
    detection = ItemState(945, ItemKind.POTION, "monster detection potion", effect="monster_detection")
    game.player.inventory.append(detection)

    assert game.quaff(detection.id).success
    assert game.player.monster_detection_turns > 0

    raise_level = ItemState(946, ItemKind.POTION, "raise level potion", effect="raise_level")
    game.player.inventory.append(raise_level)
    old_level = game.player.level

    assert game.quaff(raise_level.id).success
    assert game.player.level == old_level + 1


def test_magic_detection_potion_reports_magic_item_positions() -> None:
    game = GameState(seed=242)
    game.floor.monsters.clear()
    item = ItemState(947, ItemKind.WAND, "wand of light", position=(game.player.x + 1, game.player.y))
    potion = ItemState(948, ItemKind.POTION, "magic detection potion", effect="magic_detection")
    game.floor.items.append(item)
    game.player.inventory.append(potion)

    result = game.quaff(potion.id)

    assert result.success
    assert str(item.position) in result.message


def test_magic_detection_potion_reports_monsters_carrying_magic_items() -> None:
    game = GameState(seed=243)
    game.floor.monsters.clear()
    game.floor.items.clear()
    position = next(
        position
        for position in game.visible_positions()
        if max(abs(position[0] - game.player.x), abs(position[1] - game.player.y)) > 1
        and game.floor.is_walkable(position)
    )
    monster = MonsterState(949, "snake", *position, 20)
    monster.carried_items.append(ItemState(950, ItemKind.WAND, "wand of light", effect="light"))
    game.floor.monsters.append(monster)
    potion = ItemState(951, ItemKind.POTION, "magic detection potion", effect="magic_detection")
    game.player.inventory.append(potion)

    result = game.quaff(potion.id)

    assert result.success
    assert str(position) in result.message


def test_haste_self_uses_a_source_duration_and_requaff_causes_exhaustion() -> None:
    class HasteRng:
        def __init__(self, value: int) -> None:
            self.value = value

        def randrange(self, stop: int) -> int:
            assert stop in {4, 8}
            return self.value

    game = GameState(seed=244)
    game.floor.monsters.clear()
    potion = ItemState(952, ItemKind.POTION, "haste self potion", effect="haste_self")
    game.player.inventory.append(potion)
    game.rng = HasteRng(3)

    assert game.quaff(potion.id).success
    assert game.player.haste_turns == 6

    repeat = ItemState(953, ItemKind.POTION, "haste self potion", effect="haste_self")
    game.player.inventory.append(repeat)
    game.rng = HasteRng(5)
    result = game.quaff(repeat.id)

    assert result.success
    assert result.message == "You faint from exhaustion."
    assert game.player.haste_turns == 0
    assert game.player.sleep_turns == 5


def test_restore_strength_restores_the_previous_maximum() -> None:
    game = GameState(seed=245)
    game.floor.monsters.clear()
    potion = ItemState(954, ItemKind.POTION, "restore strength potion", effect="restore_strength")
    game.player.inventory.append(potion)
    game.player.max_strength = 21
    game.player.strength = 13

    assert game.quaff(potion.id).success

    assert game.player.strength == 21


def test_monster_detection_reveals_invisible_monsters() -> None:
    game = GameState(seed=246)
    game.floor.monsters.clear()
    position = next(
        position
        for position in game.visible_positions()
        if max(abs(position[0] - game.player.x), abs(position[1] - game.player.y)) > 1
        and game.floor.is_walkable(position)
    )
    monster = MonsterState(955, "snake", *position, 20, invisible=True)
    game.floor.monsters.append(monster)
    game.player.monster_detection_turns = 3

    cell = game.display_cells()[position]

    assert cell.entity == EntityKind.MONSTER


def test_monster_will_not_step_on_a_dropped_scare_scroll() -> None:
    game = GameState(seed=247)
    game.floor.monsters.clear()
    game.floor.rooms.clear()
    game.player.position = (5, 5)
    monster = MonsterState(956, "snake", 10, 5, 20, running=True)
    game.floor.monsters.append(monster)
    for x in range(5, 11):
        game.floor.set_tile((x, 5), Terrain.FLOOR)
    scare_scroll = ItemState(
        957,
        ItemKind.SCROLL,
        "scare monster scroll",
        effect="scare_monster",
        position=(9, 5),
    )
    game.floor.items.append(scare_scroll)

    game._process_monsters()

    assert (monster.x, monster.y) != scare_scroll.position


def test_new_monsters_run_when_the_player_wears_an_aggravate_ring() -> None:
    game = GameState(seed=248)
    game.floor.monsters.clear()
    ring = ItemState(958, ItemKind.RING, "ring of aggravate monster", effect="aggravate")
    game.player.inventory.append(ring)
    game.player.equipped_rings.append(ring.id)

    monster = game._new_monster(game.floor)

    assert monster.running


def test_invisibility_wand_hides_an_already_revealed_monster() -> None:
    game = GameState(seed=249)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    monster = MonsterState(959, "snake", *position, 20, revealed=True, held=True)
    game.floor.monsters.append(monster)
    wand = ItemState(960, ItemKind.WAND, "wand of invisibility", effect="invisibility", charges=1)
    game.player.inventory.append(wand)

    result = game.zap(wand.id, {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}[direction])

    assert result.success
    assert monster.invisible
    assert not monster.revealed
    assert game.display_cells()[position].entity is None


def test_reading_a_category_identification_scroll_only_identifies_its_targets() -> None:
    game = GameState(seed=25)
    game.floor.monsters.clear()
    scroll = ItemState(931, ItemKind.SCROLL, "identify potion scroll", effect="identify_potion")
    potion = ItemState(932, ItemKind.POTION, "healing potion", identified=False, effect="healing")
    ring = ItemState(933, ItemKind.RING, "ring of protection", identified=False, effect="protection")
    game.player.inventory.extend((scroll, potion, ring))

    result = game.read(scroll.id, potion.id)

    assert result.success
    assert result.turn_consumed
    assert potion.identified
    assert not ring.identified


@pytest.mark.parametrize(
    ("effect", "targets"),
    [
        ("identify_weapon", {ItemKind.WEAPON}),
        ("identify_armor", {ItemKind.ARMOR}),
        ("identify_ring_wand", {ItemKind.RING, ItemKind.WAND}),
    ],
)
def test_identification_scroll_variants_target_their_source_categories(effect: str, targets: set[ItemKind]) -> None:
    game = GameState(seed=251)
    game.floor.monsters.clear()
    scroll = ItemState(940, ItemKind.SCROLL, "identify test scroll", effect=effect)
    items = [
        ItemState(941 + index, kind, f"test {kind.value}", identified=False) for index, kind in enumerate(ItemKind)
    ]
    game.player.inventory.extend((scroll, *items))
    target = next(item for item in items if item.kind in targets)

    result = game.read(scroll.id, target.id)

    assert result.success
    assert target.identified
    assert all(item.identified == (item is target) for item in items)


def test_hold_and_aggravate_scrolls_change_monster_state() -> None:
    game = GameState(seed=26)
    monster = game.floor.monsters[0]
    monster.x, monster.y = game.player.x + 1, game.player.y
    monster.running = True
    hold = ItemState(934, ItemKind.SCROLL, "hold monster scroll", effect="hold_monster")
    game.player.inventory.append(hold)

    result = game.read(hold.id)

    assert result.success
    assert monster.held

    aggravate = ItemState(935, ItemKind.SCROLL, "aggravate monsters scroll", effect="aggravate_monsters")
    game.player.inventory.append(aggravate)
    monster.asleep = True
    monster.running = False

    result = game.read(aggravate.id)

    assert result.success
    assert not monster.asleep
    assert monster.running


def test_monster_confusion_scroll_confuses_the_next_successfully_hit_monster() -> None:
    game = GameState(seed=261)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    monster = MonsterState(938, "bat", *position, 50)
    scroll = ItemState(939, ItemKind.SCROLL, "monster confusion scroll", effect="monster_confusion")
    game.floor.monsters.append(monster)
    game.player.inventory.append(scroll)

    assert game.read(scroll.id).success
    game.rng.seed(7)
    game.player.hp = game.player.max_hp = 1000
    for _ in range(10):
        result = game.execute("attack", [direction])
        if result.data.hit:
            break

    assert result.success
    assert monster.confused_turns > 0
    assert not game.player.monster_confusion_ready


def test_control_wands_apply_their_effect_to_the_target_monster() -> None:
    game = GameState(seed=27)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    monster = MonsterState(936, "bat", *position, 20)
    wand = ItemState(937, ItemKind.WAND, "wand of invisibility", effect="invisibility", charges=1)
    game.floor.monsters.append(monster)
    game.player.inventory.append(wand)

    result = game.execute("zap", [wand.id, direction])

    assert result.success
    assert result.turn_consumed
    assert monster.invisible
    assert wand.charges == 0


def test_cancellation_wand_removes_monster_special_state() -> None:
    game = GameState(seed=271)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    monster = MonsterState(942, "bat", *position, 20, invisible=True, hasted=True)
    wand = ItemState(943, ItemKind.WAND, "wand of cancellation", effect="cancellation", charges=1)
    game.floor.monsters.append(monster)
    game.player.inventory.append(wand)

    result = game.execute("zap", [wand.id, direction])

    assert result.success
    assert monster.cancelled
    assert not monster.invisible
    assert not monster.hasted


def test_cancellation_wand_reveals_a_disguised_xeroc() -> None:
    game = GameState(seed=2711)
    game.floor.monsters.clear()
    game.player.position = (5, 5)
    for x in range(6, 10):
        game.floor.set_tile((x, 5), Terrain.FLOOR)
    monster = MonsterState(970, "xeroc", 8, 5, 20, disguise="potion")
    wand = ItemState(971, ItemKind.WAND, "wand of cancellation", effect="cancellation", charges=1)
    game.floor.monsters.append(monster)
    game.player.inventory.append(wand)
    position = (monster.x, monster.y)
    assert game.display_cells()[position].entity == EntityKind.ITEM

    result = game.execute("zap", [wand.id, "east"])

    assert result.success
    assert monster.cancelled
    assert monster.disguise is None
    assert game.display_cells()[position].entity == EntityKind.MONSTER


@pytest.mark.parametrize(("effect", "state"), [("haste_monster", "hasted"), ("slow_monster", "slowed")])
def test_haste_and_slow_wands_change_monster_speed(effect: str, state: str) -> None:
    game = GameState(seed=272)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    monster = MonsterState(960, "bat", *position, 20)
    wand = ItemState(961, ItemKind.WAND, f"{effect} wand", effect=effect, charges=1)
    game.floor.monsters.append(monster)
    game.player.inventory.append(wand)

    result = game.execute("zap", [wand.id, direction])

    assert result.success
    assert getattr(monster, state)
    assert wand.charges == 0


def test_polymorph_wand_replaces_target_monster_stats() -> None:
    game = GameState(seed=273)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    monster = MonsterState(962, "bat", *position, 100)
    wand = ItemState(963, ItemKind.WAND, "wand of polymorph", effect="polymorph", charges=1)
    game.floor.monsters.append(monster)
    game.player.inventory.append(wand)

    result = game.execute("zap", [wand.id, direction])

    assert result.success
    assert monster.max_hp < 100
    assert monster.hp == monster.max_hp


def test_polymorph_resets_monster_state_and_preserves_carried_items(monkeypatch) -> None:
    game = GameState(seed=2731)
    game.floor.monsters.clear()
    game._finish_turn = lambda: None
    direction, position = _walkable_direction(game)
    carried = ItemState(967, ItemKind.POTION, "healing potion")
    monster = MonsterState(968, "bat", *position, 100)
    monster.asleep = monster.running = monster.gaze_attempted = monster.revealed = True
    monster.disguise = "potion"
    monster.carried_items.append(carried)
    monster.target_item_id = 969
    monster.carry_search_room_index = 2
    monster.held = monster.invisible = monster.hasted = monster.slowed = monster.cancelled = True
    monster.confused_turns = 3
    monster.mean_override = True
    wand = ItemState(970, ItemKind.WAND, "wand of polymorph", effect="polymorph", charges=1)
    game.floor.monsters.append(monster)
    game.player.inventory.append(wand)
    monkeypatch.setattr(type(game.rng), "choice", lambda _rng, choices: choices[0])
    monkeypatch.setattr(type(game.rng), "randrange", lambda _rng, *args: 0)

    result = game.execute("zap", [wand.id, direction])

    assert result.success
    assert monster.type_id == MONSTER_TYPES[0].id
    assert monster.hp == monster.max_hp
    assert not any(
        (
            monster.asleep,
            monster.running,
            monster.gaze_attempted,
            monster.revealed,
            monster.disguise,
            monster.target_item_id,
            monster.carry_search_room_index,
            monster.held,
            monster.invisible,
            monster.hasted,
            monster.slowed,
            monster.cancelled,
            monster.confused_turns,
            monster.mean_override,
        )
    )
    assert monster.carried_items == [carried]


@pytest.mark.parametrize("effect", ["invisibility", "polymorph", "teleport_away", "teleport_to", "cancellation"])
def test_directed_wand_effects_release_venus_flytrap_hold(monkeypatch, effect: str) -> None:
    game = GameState(seed=2732)
    game.floor.monsters.clear()
    monkeypatch.setattr(game, "_finish_turn", lambda: None)
    direction, position = _walkable_direction(game)
    monster = MonsterState(971, "venus_flytrap", *position, 30)
    wand = ItemState(972, ItemKind.WAND, f"wand of {effect}", effect=effect, charges=1)
    game.floor.monsters.append(monster)
    game.player.inventory.append(wand)
    game.player.held = True

    result = game.execute("zap", [wand.id, direction])

    assert result.success
    assert not game.player.held


def test_identifying_item_reveals_existing_items_with_same_effect() -> None:
    game = GameState(seed=2733)
    game.floor.monsters.clear()
    consumed = ItemState(973, ItemKind.POTION, "healing potion", effect="healing", identified=False)
    sibling_in_pack = ItemState(974, ItemKind.POTION, "healing potion", effect="healing", identified=False)
    sibling_on_floor = ItemState(
        975, ItemKind.POTION, "healing potion", effect="healing", identified=False, position=(1, 1)
    )
    inactive_floor = game._ensure_floor(2)
    sibling_on_inactive_floor = game._new_item(inactive_floor, ItemKind.POTION, "healing potion")
    carrier = MonsterState(976, "bat", 10, 10, 20)
    sibling_in_monster_pack = game._new_item(inactive_floor, ItemKind.POTION, "healing potion", on_floor=False)
    carrier.carried_items.append(sibling_in_monster_pack)
    inactive_floor.monsters.append(carrier)
    game.player.inventory.extend((consumed, sibling_in_pack))
    game.floor.items.append(sibling_on_floor)
    inactive_floor.items.append(sibling_on_inactive_floor)

    result = game.quaff(consumed.id)

    assert result.success
    assert sibling_in_pack.identified
    assert sibling_in_pack.display_name == sibling_in_pack.name
    assert sibling_on_floor.identified
    assert sibling_on_floor.display_name == sibling_on_floor.name
    assert sibling_on_inactive_floor.identified
    assert sibling_on_inactive_floor.display_name == sibling_on_inactive_floor.name
    assert sibling_in_monster_pack.identified
    assert sibling_in_monster_pack.display_name == sibling_in_monster_pack.name


def test_teleport_away_and_nothing_wands_consume_charges() -> None:
    game = GameState(seed=274)
    game.floor.monsters.clear()
    direction, position = _walkable_direction(game)
    monster = MonsterState(964, "bat", *position, 20)
    away = ItemState(965, ItemKind.WAND, "wand of teleport away", effect="teleport_away", charges=1)
    game.floor.monsters.append(monster)
    game.player.inventory.append(away)
    before = monster.x, monster.y

    assert game.execute("zap", [away.id, direction]).success
    assert (monster.x, monster.y) != before
    assert away.charges == 0

    nothing = ItemState(966, ItemKind.WAND, "wand of nothing", effect="nothing", charges=1)
    game.player.inventory.append(nothing)
    assert game.execute("zap", [nothing.id, direction]).success
    assert nothing.charges == 0


def test_drain_life_wand_transfers_half_current_hp_to_room_monsters(monkeypatch) -> None:
    game = GameState(seed=275)
    game.floor.monsters.clear()
    room = next(room for room in game.floor.rooms if not room.is_maze)
    game.player.position = room.center
    positions = [
        (x, y)
        for y in range(room.y + 1, room.y + room.height - 1)
        for x in range(room.x + 1, room.x + room.width - 1)
        if (x, y) != game.player.position and game.floor.is_walkable((x, y))
    ]
    first, second = positions[:2]
    monsters = [
        MonsterState(967, "bat", *first, 100),
        MonsterState(969, "snake", *second, 100),
    ]
    wand = ItemState(968, ItemKind.WAND, "wand of drain life", effect="drain_life", charges=1)
    game.floor.monsters.extend(monsters)
    game.player.inventory.append(wand)
    game.player.hp = 20
    monkeypatch.setattr(game, "_finish_turn", lambda: None)

    result = game.execute("zap", [wand.id])

    assert result.success
    assert game.player.hp == 10
    assert [monster.hp for monster in monsters] == [95, 95]
    assert all(monster.running for monster in monsters)


def test_failed_enchantment_target_keeps_scroll_and_does_not_consume_turn() -> None:
    game = GameState(seed=28)
    game.floor.monsters.clear()
    weapon = game.player.equipped(ItemKind.WEAPON)
    assert weapon is not None
    game.player.equipped_weapon = None
    scroll = ItemState(944, ItemKind.SCROLL, "enchant weapon scroll", effect="enchant_weapon")
    game.player.inventory.append(scroll)

    result = game.read(scroll.id)

    assert not result.success
    assert not result.turn_consumed
    assert scroll in game.player.inventory
    assert game.player.turns_played == 0


def test_identification_scroll_requires_a_matching_item_without_spending_a_turn() -> None:
    game = GameState(seed=281)
    game.floor.monsters.clear()
    scroll = ItemState(949, ItemKind.SCROLL, "identify potion scroll", effect="identify_potion")
    ring = ItemState(950, ItemKind.RING, "ring of protection", identified=False, effect="protection")
    game.player.inventory.extend((scroll, ring))

    result = game.read(scroll.id, ring.id)

    assert not result.success
    assert not result.turn_consumed
    assert scroll in game.player.inventory
    assert not ring.identified
    assert game.player.turns_played == 0


def test_food_detection_and_protect_armor_scrolls_apply_effects() -> None:
    game = GameState(seed=282)
    game.floor.monsters.clear()
    food = ItemState(951, ItemKind.FOOD, "food ration", position=(game.player.x + 2, game.player.y))
    armor = game.player.equipped(ItemKind.ARMOR)
    assert armor is not None
    game.floor.items.append(food)
    food_scroll = ItemState(952, ItemKind.SCROLL, "food detection scroll", effect="food_detection")
    game.player.inventory.append(food_scroll)

    result = game.read(food_scroll.id)

    assert result.success
    assert str(food.position) in result.message

    protect_scroll = ItemState(953, ItemKind.SCROLL, "protect armor scroll", effect="protect_armor")
    game.player.inventory.append(protect_scroll)
    assert game.read(protect_scroll.id).success
    assert armor.armor_protected
    enchantment = armor.enchantment
    assert not game._rust_armor()
    assert armor.enchantment == enchantment


def test_create_monster_scroll_spawns_a_monster() -> None:
    game = GameState(seed=283)
    game.floor.monsters.clear()
    scroll = ItemState(954, ItemKind.SCROLL, "create monster scroll", effect="create_monster")
    game.player.inventory.append(scroll)

    result = game.read(scroll.id)

    assert result.success
    assert result.turn_consumed
    assert len(game.floor.monsters) == 1


def test_equipped_strength_and_protection_rings_change_combat_stats() -> None:
    game = GameState(seed=3)
    game.floor.monsters.clear()
    base_attack = game.player.attack
    base_defense = game.player.defense
    strength_ring = ItemState(
        id=902,
        kind=ItemKind.RING,
        name="ring of add strength",
        effect="strength",
        enchantment=2,
    )
    protection_ring = ItemState(
        id=903,
        kind=ItemKind.RING,
        name="ring of protection",
        effect="protection",
        enchantment=2,
    )
    game.player.inventory.extend((strength_ring, protection_ring))

    assert game.equip(strength_ring.id, ItemKind.RING).success
    assert game.equip(protection_ring.id, ItemKind.RING).success

    assert game.player.attack == base_attack + 1
    assert game.player.defense == base_defense - 2


def test_see_invisible_ring_reveals_a_phantom() -> None:
    game = GameState(seed=31)
    game.floor.monsters.clear()
    _, position = _walkable_direction(game)
    phantom = MonsterState(955, "phantom", *position, 20)
    ring = ItemState(956, ItemKind.RING, "ring of see invisible", effect="see_invisible")
    game.floor.monsters.append(phantom)
    game.player.inventory.append(ring)

    assert game.display_cells()[position].entity is None
    assert game.equip(ring.id, ItemKind.RING).success

    assert game.display_cells()[position].entity == EntityKind.MONSTER


def test_stealth_ring_can_prevent_mean_monsters_from_waking(monkeypatch: pytest.MonkeyPatch) -> None:
    class StealthRng:
        def randrange(self, stop: int) -> int:
            assert stop == 3
            return 1

    game = GameState(seed=32)
    game.floor.monsters.clear()
    position = next(
        position
        for position in game.visible_positions()
        if max(abs(position[0] - game.player.x), abs(position[1] - game.player.y)) > 1
        and game.floor.is_walkable(position)
    )
    monster = MonsterState(957, "snake", *position, 20)
    ring = ItemState(958, ItemKind.RING, "ring of stealth", effect="stealth")
    game.floor.monsters.append(monster)
    game.player.inventory.append(ring)
    game.player.equipped_rings.append(ring.id)
    monkeypatch.setattr(game, "rng", StealthRng())

    game._process_monsters()

    assert not monster.running


def test_stealth_and_levitation_can_still_allow_mean_monsters_to_wake(monkeypatch: pytest.MonkeyPatch) -> None:
    class WakeRng:
        def __init__(self) -> None:
            self.values = iter((0, 0, 1))
            self.calls = 0

        def randrange(self, stop: int) -> int:
            assert stop == 3
            self.calls += 1
            return next(self.values)

        def choice(self, population: list[tuple[int, int]]) -> tuple[int, int]:
            return population[0]

    game = GameState(seed=33)
    game.floor.monsters.clear()
    game.floor.rooms.clear()
    game.player.position = (5, 5)
    game.player.levitation_turns = 10
    monster = MonsterState(960, "snake", 10, 5, 20)
    ring = ItemState(961, ItemKind.RING, "ring of stealth", effect="stealth")
    game.floor.monsters.append(monster)
    game.player.inventory.append(ring)
    game.player.equipped_rings.append(ring.id)
    for x in range(5, 11):
        game.floor.set_tile((x, 5), Terrain.FLOOR)
    monkeypatch.setattr(game, "rng", WakeRng())

    game._process_monsters()

    assert monster.running
    assert game.rng.calls == 3


def test_slow_digestion_ring_can_skip_food_consumption() -> None:
    game = GameState(seed=33)
    game.floor.monsters.clear()
    ring = ItemState(959, ItemKind.RING, "ring of slow digestion", effect="slow_digestion")
    game.player.inventory.append(ring)
    assert game.equip(ring.id, ItemKind.RING).success
    game.player.food_units = 1000
    game.rng.seed(1)

    assert game.wait().success

    assert game.player.food_units == 1000


def test_searching_ring_reveals_adjacent_traps_after_a_turn() -> None:
    game = GameState(seed=4)
    game.floor.monsters.clear()
    ring = ItemState(id=905, kind=ItemKind.RING, name="ring of searching", effect="search")
    game.player.inventory.append(ring)
    assert game.equip(ring.id, ItemKind.RING).success
    px, py = game.player.position
    trap_position = next(
        position
        for position in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1))
        if game.floor.is_walkable(position)
    )
    trap = TrapState(904, TrapKind.BEAR, *trap_position)
    game.floor.traps.append(trap)

    result = game.wait()

    assert result.success
    assert trap.discovered


def test_regeneration_ring_heals_one_hp_per_turn() -> None:
    game = GameState(seed=5)
    game.floor.monsters.clear()
    ring = ItemState(
        id=906,
        kind=ItemKind.RING,
        name="ring of regeneration",
        effect="regeneration",
    )
    game.player.inventory.append(ring)
    assert game.equip(ring.id, ItemKind.RING).success
    game.player.hp = 5

    result = game.wait()

    assert result.success
    assert result.turn_consumed
    assert game.player.hp == 6


def test_sustain_ring_prevents_poison_dart_strength_loss() -> None:
    def adjacent_target(game: GameState) -> tuple[int, int, int, int]:
        px, py = game.player.position
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if game.floor.is_walkable((px + dx, py + dy)):
                return px + dx, py + dy, dx, dy
        raise AssertionError

    without_ring = GameState(seed=6)
    without_ring.floor.monsters.clear()
    tx, ty, dx, dy = adjacent_target(without_ring)
    without_ring.floor.traps.append(TrapState(907, TrapKind.POISON_DART, tx, ty))
    without_ring.move(dx, dy)

    with_ring = GameState(seed=6)
    with_ring.floor.monsters.clear()
    ring = ItemState(id=908, kind=ItemKind.RING, name="ring of sustain strength", effect="sustain")
    with_ring.player.inventory.append(ring)
    assert with_ring.equip(ring.id, ItemKind.RING).success
    tx, ty, dx, dy = adjacent_target(with_ring)
    with_ring.floor.traps.append(TrapState(909, TrapKind.POISON_DART, tx, ty))
    with_ring.move(dx, dy)

    assert without_ring.player.strength == 15
    assert with_ring.player.strength == 16


def test_zap_rejects_missing_direction_without_consuming_wand_charge() -> None:
    game = GameState(seed=7)
    game.floor.monsters.clear()
    wand = ItemState(id=910, kind=ItemKind.WAND, name="wand of magic missile", effect="magic_missile", charges=2)
    game.player.inventory.append(wand)

    result = game.zap(wand.id)

    assert not result.success
    assert not result.turn_consumed
    assert wand.charges == 2
    assert "direction" in result.message.lower()

    result = game.execute("zap", [wand.id, "invalid"])

    assert not result.success
    assert not result.turn_consumed
    assert wand.charges == 2


def test_teleport_monster_wand_moves_the_first_target_in_line() -> None:
    game = GameState(seed=8)
    game.floor.monsters.clear()
    px, py = game.player.position
    target_position = next(
        position
        for position in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1))
        if game.floor.is_walkable(position)
    )
    target = MonsterState(911, "bat", *target_position, hp=5)
    game.floor.monsters.append(target)
    wand = ItemState(id=912, kind=ItemKind.WAND, name="wand of teleport monster", effect="teleport_monster", charges=1)
    game.player.inventory.append(wand)

    result = game.zap(wand.id, (target.x - px, target.y - py))

    assert result.success
    assert result.turn_consumed
    assert wand.charges == 0
    assert (target.x, target.y) != target_position
    assert (target.x, target.y) != game.player.position


def test_damage_wand_hits_and_removes_a_monster_in_line() -> None:
    game = GameState(seed=9)
    game.floor.monsters.clear()
    px, py = game.player.position
    target_position = next(
        position
        for position in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1))
        if game.floor.is_walkable(position)
    )
    target = MonsterState(913, "bat", *target_position, hp=1)
    game.floor.monsters.append(target)
    wand = ItemState(id=914, kind=ItemKind.WAND, name="wand of magic missile", effect="magic_missile", charges=1)
    game.player.inventory.append(wand)

    result = game.zap(wand.id, (target.x - px, target.y - py))

    assert result.success
    assert target not in game.floor.monsters
    assert game.player.monsters_killed == 1
    assert "hits" in result.message.lower()


def test_light_wand_illuminates_without_a_target() -> None:
    game = GameState(seed=10)
    game.floor.monsters.clear()
    game.floor.explored.clear()
    wand = ItemState(id=915, kind=ItemKind.WAND, name="wand of light", effect="light", charges=1)
    game.player.inventory.append(wand)

    result = game.zap(None, (0, 0))

    assert result.success
    assert result.turn_consumed
    assert wand.charges == 0
    assert result.message == "The room is lit."
    assert any(game.floor.tile_at(position).value != "wall" for position in game.floor.explored)


def test_trapdoor_moves_player_to_the_next_floor() -> None:
    game = GameState(seed=11)
    game.floor.monsters.clear()
    px, py = game.player.position
    target_position, direction = next(
        (
            (position, (position[0] - px, position[1] - py))
            for position in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1))
            if game.floor.is_walkable(position)
        ),
    )
    game.floor.traps.append(TrapState(916, TrapKind.TRAP_DOOR, *target_position))
    initial_hp = game.player.hp

    result = game.move(*direction)

    assert result.success
    assert result.turn_consumed
    assert game.current_floor == 2
    assert game.player.position == game.floor.up_stairs
    assert game.player.hp == initial_hp
    assert "trap door" in result.message.lower()


def test_rust_trap_weakens_equipped_nonleather_armor() -> None:
    game = GameState(seed=12)
    game.floor.monsters.clear()
    px, py = game.player.position
    target_position, direction = next(
        (
            (position, (position[0] - px, position[1] - py))
            for position in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1))
            if game.floor.is_walkable(position)
        ),
    )
    armor = game.player.equipped(ItemKind.ARMOR)
    assert armor is not None
    initial_enchantment = armor.enchantment
    game.floor.traps.append(TrapState(917, TrapKind.RUST, *target_position))

    result = game.move(*direction)

    assert result.success
    assert armor.enchantment == initial_enchantment - 1
    assert "armor" in result.message.lower()


def test_sleeping_gas_blocks_the_next_player_turns() -> None:
    game = GameState(seed=13)
    game.floor.monsters.clear()
    px, py = game.player.position
    target_position, direction = next(
        (
            (position, (position[0] - px, position[1] - py))
            for position in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1))
            if game.floor.is_walkable(position)
        ),
    )
    game.floor.traps.append(TrapState(918, TrapKind.SLEEPING_GAS, *target_position))

    result = game.move(*direction)

    assert result.success
    assert result.turn_consumed
    assert game.player.sleep_turns == 5
    assert "sleep" in result.message.lower()

    result = game.execute("wait")

    assert result.success
    assert result.turn_consumed
    assert game.player.sleep_turns == 4
    assert "asleep" in result.message.lower()


def test_mysterious_trap_uses_a_seeded_flavor_message() -> None:
    game = GameState(seed=14)
    game.floor.monsters.clear()
    px, py = game.player.position
    target_position, direction = next(
        (
            (position, (position[0] - px, position[1] - py))
            for position in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1))
            if game.floor.is_walkable(position)
        ),
    )
    trap = TrapState(919, TrapKind.MYSTERIOUS, *target_position)
    game.floor.traps.append(trap)

    result = game.move(*direction)

    assert result.success
    assert result.turn_consumed
    assert result.message != "A mysterious trap is triggered."
    assert result.message
    assert trap.discovered


def test_same_seed_and_commands_keep_effects_deterministic() -> None:
    def prepared_game() -> GameState:
        game = GameState(seed=15)
        game.floor.monsters.clear()
        game.player.inventory.extend(
            (
                ItemState(id=920, kind=ItemKind.SCROLL, name="teleport scroll", effect="teleport"),
                ItemState(id=921, kind=ItemKind.WAND, name="wand of light", effect="light", charges=1),
            )
        )
        return game

    first = prepared_game()
    second = prepared_game()
    commands = (("read", [920]), ("zap", [921, "north"]), ("wait", []))

    for command, args in commands:
        assert first.execute(command, args) == second.execute(command, args)

    assert first.to_dict() == second.to_dict()


def test_sleep_turns_round_trip_and_default_for_older_saves() -> None:
    game = GameState(seed=16)
    game.player.sleep_turns = 2

    restored = GameState.from_dict(game.to_dict())

    assert restored.player.sleep_turns == 2

    legacy_data = game.to_dict()
    legacy_data["player"].pop("sleep_turns")

    assert GameState.from_dict(legacy_data).player.sleep_turns == 0


def test_save_manager_loads_older_player_state_without_sleep_turns(tmp_path) -> None:
    game = GameState(seed=17)
    legacy_data = game.to_dict()
    legacy_data["player"].pop("sleep_turns")
    manager = SaveManager(tmp_path)

    assert manager.save_game_state(legacy_data)
    loaded = manager.load_game_state()

    assert loaded is not None
    assert GameState.from_dict(loaded).player.sleep_turns == 0
