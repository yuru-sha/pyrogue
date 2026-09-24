from unittest.mock import Mock

import pytest

from pyrogue.core.rogue_game import (
    MONSTER_SPAWN_ORDER,
    MONSTER_TYPES,
    EntityKind,
    GameState,
    ItemKind,
    ItemState,
    MonsterState,
    Room,
    Terrain,
)
from pyrogue.presentation.display_renderer import MONSTER_GLYPHS


def game_with_adjacent_monster(type_id: str, hp: int = 100) -> tuple[GameState, MonsterState]:
    game = GameState(seed=1)
    game.floor.monsters.clear()
    game.player.hp = game.player.max_hp = 100
    x, y = game.player.position
    monster = MonsterState(900, type_id, x + 1, y, hp)
    game.floor.monsters.append(monster)
    return game, monster


def test_monster_definitions_match_rogue_54_source_table() -> None:
    expected = {
        "aquator": (5, 2, ((0, 0), (0, 0)), 20, 0, {"mean"}),
        "bat": (1, 3, ((1, 2),), 1, 0, {"fly"}),
        "centaur": (4, 4, ((1, 2), (1, 5), (1, 5)), 17, 15, set()),
        "dragon": (10, -1, ((1, 8), (1, 8), (3, 10)), 5000, 100, {"mean"}),
        "emu": (1, 7, ((1, 2),), 2, 0, {"mean"}),
        "venus_flytrap": (8, 3, ((0, 0),), 80, 0, {"mean"}),
        "griffin": (13, 2, ((4, 3), (3, 5)), 2000, 20, {"mean", "fly", "regenerate"}),
        "hobgoblin": (1, 5, ((1, 8),), 3, 0, {"mean"}),
        "ice_monster": (1, 9, ((0, 0),), 5, 0, set()),
        "jabberwock": (15, 6, ((2, 12), (2, 4)), 3000, 70, set()),
        "kestrel": (1, 7, ((1, 4),), 1, 0, {"mean", "fly"}),
        "leprechaun": (3, 8, ((1, 1),), 10, 0, set()),
        "medusa": (8, 2, ((3, 4), (3, 4), (2, 5)), 200, 40, {"mean"}),
        "nymph": (3, 9, ((0, 0),), 37, 100, set()),
        "orc": (1, 6, ((1, 8),), 5, 15, {"greed"}),
        "phantom": (8, 3, ((4, 4),), 120, 0, {"invisible"}),
        "quagga": (3, 3, ((1, 5), (1, 5)), 15, 0, {"mean"}),
        "rattlesnake": (2, 3, ((1, 6),), 9, 0, {"mean"}),
        "snake": (1, 5, ((1, 3),), 2, 0, {"mean"}),
        "troll": (6, 4, ((1, 8), (1, 8), (2, 6)), 120, 50, {"mean", "regenerate"}),
        "ur_vile": (7, -2, ((1, 9), (1, 9), (2, 9)), 190, 0, {"mean"}),
        "vampire": (8, 1, ((1, 10),), 350, 20, {"mean", "regenerate"}),
        "wraith": (5, 4, ((1, 6),), 55, 0, set()),
        "xeroc": (7, 7, ((4, 4),), 100, 30, set()),
        "yeti": (4, 6, ((1, 6), (1, 6)), 50, 30, set()),
        "zombie": (2, 8, ((1, 8),), 6, 0, {"mean"}),
    }

    assert {
        monster.id: (
            monster.level,
            monster.armor_class,
            monster.damage_dice,
            monster.exp,
            monster.carry_chance,
            set(monster.abilities),
        )
        for monster in MONSTER_TYPES
    } == expected
    assert tuple(monster.name for monster in MONSTER_TYPES) == (
        "aquator",
        "bat",
        "centaur",
        "dragon",
        "emu",
        "venus flytrap",
        "griffin",
        "hobgoblin",
        "ice monster",
        "jabberwock",
        "kestrel",
        "leprechaun",
        "medusa",
        "nymph",
        "orc",
        "phantom",
        "quagga",
        "rattlesnake",
        "snake",
        "troll",
        "black unicorn",
        "vampire",
        "wraith",
        "xeroc",
        "yeti",
        "zombie",
    )
    assert "".join(MONSTER_GLYPHS[monster.id] for monster in MONSTER_TYPES) == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    assert MONSTER_SPAWN_ORDER == (
        "kestrel",
        "emu",
        "bat",
        "snake",
        "hobgoblin",
        "ice_monster",
        "rattlesnake",
        "orc",
        "zombie",
        "leprechaun",
        "centaur",
        "quagga",
        "aquator",
        "nymph",
        "yeti",
        "venus_flytrap",
        "troll",
        "wraith",
        "phantom",
        "xeroc",
        "ur_vile",
        "medusa",
        "vampire",
        "griffin",
        "jabberwock",
        "dragon",
    )


def test_spawned_monsters_use_rogue_hit_points_and_experience_values() -> None:
    game = GameState(seed=123)

    assert game.floor.monsters
    for monster in game.floor.monsters:
        exp_bonus = monster.max_hp // (8 if monster.level == 1 else 6)
        assert monster.max_hp == monster.hp
        assert monster.experience_reward == monster.definition.exp + exp_bonus


@pytest.mark.parametrize(
    ("floor_number", "expected_types"),
    [
        (1, {"kestrel", "emu", "bat", "snake", "hobgoblin"}),
        (26, {"ur_vile", "medusa", "vampire", "griffin", "jabberwock", "dragon"}),
    ],
)
def test_spawn_selection_uses_rogue_level_window(floor_number: int, expected_types: set[str]) -> None:
    game = GameState(seed=123)
    game.floor.number = floor_number
    game.floor.monsters.clear()
    game.rng.seed(123)

    game._spawn_monsters(game.floor)

    assert game.floor.monsters
    assert {monster.type_id for monster in game.floor.monsters} <= expected_types


def test_spawn_selection_uses_rogue_random_offset() -> None:
    game = GameState(seed=125)
    game.floor.number = 6
    game.floor.monsters.clear()
    rng = Mock()
    rng.randrange.return_value = 0
    rng.choice.side_effect = lambda choices: choices[0]
    rng.randint.return_value = 1
    game.rng = rng

    game._spawn_monsters(game.floor)

    assert {monster.type_id for monster in game.floor.monsters} == {"kestrel"}


def test_visible_nonmean_monster_does_not_chase_until_attacked() -> None:
    game = GameState(seed=124)
    game.floor.monsters.clear()
    game.floor.rooms.clear()
    game.player.position = (5, 5)
    monster = MonsterState(900, "centaur", 10, 5, 100)
    game.floor.monsters.append(monster)
    for x in range(5, 11):
        game.floor.set_tile((x, 5), Terrain.FLOOR)

    game.execute("wait")

    assert (monster.x, monster.y) == (10, 5)
    assert not monster.running


def test_pursuer_routes_around_a_blocking_monster() -> None:
    game = GameState(seed=126)
    game.floor.monsters.clear()
    game.floor.rooms.clear()
    game.player.position = (5, 5)
    for y in (4, 5, 6):
        for x in range(5, 12):
            game.floor.set_tile((x, y), Terrain.FLOOR)
    blocker = MonsterState(900, "centaur", 9, 5, 100)
    pursuer = MonsterState(901, "snake", 10, 5, 100)
    game.floor.monsters.extend((blocker, pursuer))

    game.execute("wait")

    assert (pursuer.x, pursuer.y) in {(9, 4), (9, 6)}


def test_pursuer_does_not_cut_a_blocked_diagonal_corner() -> None:
    game, monster = game_with_adjacent_monster("snake")
    game.player.position = (6, 6)
    monster.x, monster.y = 7, 7
    game.floor.set_tile((6, 6), Terrain.FLOOR)
    game.floor.set_tile((7, 7), Terrain.FLOOR)
    game.floor.set_tile((7, 6), Terrain.WALL)
    game.floor.set_tile((6, 7), Terrain.WALL)
    monster.running = True

    game.execute("wait")

    assert game.player.hp == 100
    assert (monster.x, monster.y) == (7, 7)


def test_visible_greedy_orc_chases_gold_in_players_room() -> None:
    game = GameState(seed=129)
    game.floor.monsters.clear()
    game.floor.rooms = [Room(5, 5, 15, 5)]
    game.player.position = (5, 7)
    orc = MonsterState(905, "orc", 10, 7, 100)
    gold = ItemState(906, ItemKind.GOLD, "gold", position=(12, 7))
    game.floor.monsters.append(orc)
    game.floor.items.append(gold)
    for x in range(5, 16):
        game.floor.set_tile((x, 7), Terrain.FLOOR)

    game.execute("wait")

    assert (orc.x, orc.y) == (11, 7)
    assert gold in game.floor.items


def test_flying_monster_gets_rogue_second_move_when_far_from_player() -> None:
    game = GameState(seed=125)
    game.floor.monsters.clear()
    game.floor.rooms.clear()
    game.player.position = (5, 5)
    monster = MonsterState(901, "kestrel", 10, 5, 100, running=True)
    game.floor.monsters.append(monster)
    for x in range(5, 11):
        game.floor.set_tile((x, 5), Terrain.FLOOR)

    game.execute("wait")

    assert (monster.x, monster.y) == (8, 5)


def test_bat_can_move_randomly_while_chasing() -> None:
    game = GameState(seed=128)
    game.floor.monsters.clear()
    game.floor.rooms.clear()
    game.player.position = (5, 10)
    bat = MonsterState(904, "bat", 10, 10, 100, running=True)
    game.floor.monsters.append(bat)
    for x in range(5, 12):
        for y in range(9, 12):
            game.floor.set_tile((x, y), Terrain.FLOOR)
    game.rng.seed(2)

    game.execute("wait")

    assert (bat.x, bat.y) == (10, 9)


def test_phantom_is_hidden_until_the_player_discovers_it() -> None:
    game = GameState(seed=126)
    game.floor.monsters.clear()
    game.floor.rooms.clear()
    game.player.position = (5, 5)
    phantom = MonsterState(902, "phantom", 6, 5, 100)
    game.floor.monsters.append(phantom)
    game.floor.set_tile((5, 5), Terrain.FLOOR)
    game.floor.set_tile((6, 5), Terrain.FLOOR)

    assert game.display_cells()[(6, 5)].entity is None

    game.execute("attack", ["east"])

    assert game.display_cells()[(6, 5)].entity == EntityKind.MONSTER


def test_xeroc_uses_an_item_disguise_until_attacked() -> None:
    game = GameState(seed=127)
    game.floor.monsters.clear()
    game.floor.rooms.clear()
    game.player.position = (5, 5)
    xeroc = MonsterState(903, "xeroc", 6, 5, 100, disguise="potion")
    game.floor.monsters.append(xeroc)
    game.floor.set_tile((5, 5), Terrain.FLOOR)
    game.floor.set_tile((6, 5), Terrain.FLOOR)

    disguised = game.display_cells()[(6, 5)]
    assert disguised.entity == EntityKind.ITEM
    assert disguised.entity_variant == "potion"

    game.execute("attack", ["east"])

    revealed = game.display_cells()[(6, 5)]
    assert revealed.entity == EntityKind.MONSTER
    assert revealed.entity_variant == "xeroc"


def test_deep_monsters_scale_hp_and_only_scale_the_hp_experience_bonus() -> None:
    game = GameState(seed=123)
    game.floor.number = 26
    game.floor.monsters.clear()
    game.rng.seed(123)

    game._spawn_monsters(game.floor)

    assert any(monster.level >= 7 for monster in game.floor.monsters)
    for monster in game.floor.monsters:
        exp_bonus = monster.max_hp // 6
        if monster.level >= 10:
            exp_bonus *= 20
        elif monster.level >= 7:
            exp_bonus *= 4
        assert monster.experience_reward == monster.definition.exp + exp_bonus


def test_spawned_monsters_apply_rogue_depth_adjustments() -> None:
    game = GameState(seed=131)
    game.floor.number = 28
    game.floor.monsters.clear()
    game.rng.seed(131)

    game._spawn_monsters(game.floor)

    assert game.floor.monsters
    for monster in game.floor.monsters:
        assert monster.level == monster.definition.level + 2
        assert monster.defense == monster.definition.armor_class - 2
        assert 1 <= monster.max_hp <= monster.level * 8
        exp_bonus = monster.max_hp // (8 if monster.level == 1 else 6)
        if monster.level > 9:
            exp_bonus *= 20
        elif monster.level > 6:
            exp_bonus *= 4
        assert monster.experience_reward == monster.definition.exp + 20 + exp_bonus


@pytest.mark.parametrize(("seed", "running", "expected_hit"), [(12, True, True), (16, True, False), (16, False, True)])
def test_execute_attack_matches_rogue_hit_boundary(seed: int, running: bool, expected_hit: bool) -> None:
    game, monster = game_with_adjacent_monster("centaur")
    game.player.equipped_weapon = None
    monster.running = running
    game.rng.seed(seed)

    result = game.execute("attack", ["east"])

    assert result.data.hit is expected_hit


def test_execute_attack_applies_strength_and_ring_damage_modifiers() -> None:
    game, _ = game_with_adjacent_monster("kestrel")
    weapon = ItemState(901, ItemKind.WEAPON, "test weapon", damage_dice=(2, 4), damage_bonus=1)
    strength_ring = ItemState(902, ItemKind.RING, "ring of add strength", effect="strength", enchantment=2)
    damage_ring = ItemState(903, ItemKind.RING, "ring of increase damage", effect="increase_damage", enchantment=2)
    weapon.enchantment = 1
    game.player.inventory.extend((weapon, strength_ring, damage_ring))
    game.player.equipped_weapon = weapon.id
    game.player.equipped_rings = [strength_ring.id, damage_ring.id]
    game.rng.seed(0)

    result = game.execute("attack", ["east"])

    assert result.data.hit
    assert result.data.damage == 11


def test_execute_attack_applies_dexterity_ring_to_wielded_weapon() -> None:
    game, monster = game_with_adjacent_monster("centaur")
    monster.running = True
    ring = ItemState(906, ItemKind.RING, "ring of dexterity", effect="dexterity", enchantment=1)
    game.player.inventory.append(ring)
    game.player.equipped_rings = [ring.id]
    game.rng.seed(38)

    result = game.execute("attack", ["east"])

    assert result.data.hit


@pytest.mark.parametrize(("armor_equipped", "expected_damage"), [(True, False), (False, True)])
def test_execute_wait_applies_armor_and_stationary_hit_modifiers(armor_equipped: bool, expected_damage: bool) -> None:
    game, _ = game_with_adjacent_monster("bat")
    if not armor_equipped:
        game.player.equipped_armor = None
    game.rng.seed(3)

    game.execute("wait")

    assert (game.player.hp < 100) is expected_damage


def test_execute_wait_resolves_each_monster_damage_component() -> None:
    game, _ = game_with_adjacent_monster("centaur")
    game.rng.seed(11)

    result = game.execute("wait")

    assert result.success
    assert game.player.hp == 91


def test_execute_wait_rusts_equipped_armor_when_aquator_hits() -> None:
    game, _ = game_with_adjacent_monster("aquator")
    armor = game.player.equipped(ItemKind.ARMOR)
    assert armor is not None
    initial_armor_class = game.player.effective_armor_class()
    game.rng.seed(3)

    result = game.execute("wait")

    assert result.success
    assert armor.enchantment == 0
    assert game.player.effective_armor_class() == initial_armor_class + 1


@pytest.mark.parametrize(("seed", "expected_strength"), [(0, 15), (10, 16)])
def test_execute_wait_rattlesnake_poison_uses_rogue_saving_throw(seed: int, expected_strength: int) -> None:
    game, _ = game_with_adjacent_monster("rattlesnake")
    game.player.armor_class = 100
    game.rng.seed(seed)

    result = game.execute("wait")

    assert result.success
    assert game.player.strength == expected_strength


@pytest.mark.parametrize(("seed", "expected_max_hp"), [(0, 98), (1, 100)])
def test_execute_wait_vampire_sometimes_drains_maximum_hit_points(seed: int, expected_max_hp: int) -> None:
    game, _ = game_with_adjacent_monster("vampire")
    game.player.armor_class = 100
    game.rng.seed(seed)

    result = game.execute("wait")

    assert result.success
    assert game.player.max_hp == expected_max_hp


def test_execute_wait_wraith_sometimes_drains_experience_level_and_maximum_hit_points() -> None:
    game, _ = game_with_adjacent_monster("wraith")
    game.player.level = 3
    game.player.exp = 41
    game.player.armor_class = 100
    game.rng.seed(0)

    result = game.execute("wait")

    assert result.success
    assert game.player.level == 2
    assert game.player.exp == 21
    assert game.player.max_hp == 95
    assert game.player.hp == 91


def test_execute_wait_wraith_kills_player_with_no_experience() -> None:
    game, _ = game_with_adjacent_monster("wraith")
    game.player.exp = 0
    game.player.armor_class = 100
    game.rng.seed(0)

    game.execute("wait")

    assert game.player.dead
    assert game.player.hp == 0


def test_execute_wait_ice_monster_freezes_player_for_two_or_three_turns() -> None:
    game, monster = game_with_adjacent_monster("ice_monster")
    game.player.armor_class = 100
    game.rng.seed(0)

    result = game.execute("wait")

    assert result.success
    assert game.player.frozen_turns in {2, 3}
    monster.asleep = True
    remaining = game.player.frozen_turns

    blocked = game.execute("wait")

    assert blocked.turn_consumed
    assert blocked.message == "You are frozen."
    assert game.player.frozen_turns == remaining - 1


def test_frozen_turns_round_trip_and_default_for_older_state() -> None:
    game = GameState(seed=20)
    game.player.frozen_turns = 2
    game.player.confused_turns = 4
    game.player.held = True
    game.player.flytrap_hits = 2

    restored = GameState.from_dict(game.to_dict()).player
    assert restored.frozen_turns == 2
    assert restored.confused_turns == 4
    assert restored.held
    assert restored.flytrap_hits == 2
    old_state = game.to_dict()
    old_state["player"].pop("frozen_turns")
    old_state["player"].pop("confused_turns")
    old_state["player"].pop("held")
    old_state["player"].pop("flytrap_hits")
    restored_old = GameState.from_dict(old_state).player
    assert restored_old.frozen_turns == 0
    assert restored_old.confused_turns == 0
    assert not restored_old.held
    assert restored_old.flytrap_hits == 0


def test_sleep_and_freeze_timers_both_advance_on_blocked_turns() -> None:
    game = GameState(seed=23)
    game.floor.monsters.clear()
    game.player.sleep_turns = 2
    game.player.frozen_turns = 2

    game.execute("wait")

    assert game.player.sleep_turns == 1
    assert game.player.frozen_turns == 1


def test_sleeping_monster_waits_for_the_player_to_wake_it() -> None:
    game, monster = game_with_adjacent_monster("medusa")
    monster.asleep = True
    game.player.armor_class = 100

    game.execute("wait")

    assert monster.asleep
    assert not monster.running

    game.execute("attack", ["east"])

    assert not monster.asleep
    assert monster.running


def test_execute_move_randomizes_one_in_five_confused_moves() -> None:
    game = GameState(seed=22)
    game.floor.monsters.clear()
    game.player.position = (5, 5)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx or dy:
                game.floor.set_tile((5 + dx, 5 + dy), Terrain.FLOOR)
    game.player.confused_turns = 20
    game.rng.seed(2)

    result = game.execute("move", ["east"])

    assert result.success
    assert game.player.position == (4, 4)
    assert game.player.confused_turns == 19


def test_execute_wait_venus_flytrap_holds_player_and_increases_damage() -> None:
    game, _ = game_with_adjacent_monster("venus_flytrap")
    game.player.armor_class = 100
    game.rng.seed(0)

    game.execute("wait")

    assert game.player.held
    assert game.player.flytrap_hits == 1
    assert game.player.hp == 100
    game.rng.seed(0)
    game.execute("wait")
    assert game.player.flytrap_hits == 2
    assert game.player.hp == 99


def test_execute_move_cannot_escape_flytrap_and_killing_it_releases_player() -> None:
    game, monster = game_with_adjacent_monster("venus_flytrap", hp=1)
    game.player.armor_class = 100
    game.rng.seed(0)
    game.execute("wait")
    start = game.player.position
    target = (start[0], start[1] - 1)
    game.floor.set_tile(target, Terrain.DOOR_CLOSED)

    blocked = game.execute("move", ["north"])

    assert not blocked.success
    assert game.player.position == start
    assert game.floor.tile_at(target) == Terrain.DOOR_CLOSED
    game.player.level = 100
    killed = game.execute("attack", ["east"])

    assert killed.success
    assert monster not in game.floor.monsters
    assert not game.player.held
    assert game.player.flytrap_hits == 0


def test_execute_wait_leprechaun_steals_gold_and_disappears_without_experience() -> None:
    game, monster = game_with_adjacent_monster("leprechaun")
    game.player.gold = 1000
    game.player.armor_class = 100
    game.rng.seed(0)

    result = game.execute("wait")

    assert result.success
    assert game.player.gold == 842
    assert monster not in game.floor.monsters
    assert game.player.monsters_killed == 0
    assert game.player.exp == 0


def test_execute_wait_nymph_steals_an_unequipped_magic_item_and_disappears() -> None:
    game, monster = game_with_adjacent_monster("nymph")
    ring = ItemState(910, ItemKind.RING, "ring of protection", effect="protection")
    game.player.inventory.append(ring)
    game.player.armor_class = 100
    game.rng.seed(0)

    result = game.execute("wait")

    assert result.success
    assert ring not in game.player.inventory
    assert monster not in game.floor.monsters
    assert game.player.monsters_killed == 0
    assert game.player.exp == 0


def test_execute_wait_medusa_gaze_confuses_player_once() -> None:
    game, monster = game_with_adjacent_monster("medusa")
    monster.running = True
    game.player.armor_class = 100
    game.rng.seed(0)

    result = game.execute("wait")

    assert result.success
    assert monster.gaze_attempted
    assert game.player.confused_turns in {19, 20}
    serialized = GameState.from_dict(game.to_dict())
    assert serialized.floor.monsters[0].gaze_attempted
    old_state = game.to_dict()
    old_state["floors"]["1"]["monsters"][0].pop("gaze_attempted")
    assert not GameState.from_dict(old_state).floor.monsters[0].gaze_attempted
    remaining = game.player.confused_turns
    game.execute("wait")
    assert game.player.confused_turns == remaining - 1


def test_execute_wait_medusa_gazes_when_first_seen() -> None:
    game, monster = game_with_adjacent_monster("medusa")
    game.player.armor_class = 100
    game.rng.seed(0)

    game.execute("wait")

    assert monster.running
    assert monster.gaze_attempted
    assert game.player.confused_turns in {19, 20}


def test_execute_wait_medusa_does_not_gaze_from_far_down_a_corridor() -> None:
    game, monster = game_with_adjacent_monster("medusa")
    game.floor.rooms.clear()
    game.player.position = (5, 5)
    monster.x, monster.y = (9, 5)
    monster.running = True
    for x in range(5, 10):
        game.floor.set_tile((x, 5), Terrain.FLOOR)
    game.player.armor_class = 100
    game.rng.seed(0)

    game.execute("wait")

    assert not monster.gaze_attempted
    assert game.player.confused_turns == 0


def test_execute_wait_medusa_does_not_gaze_from_a_different_room() -> None:
    game = GameState(seed=21)
    game.floor.monsters.clear()
    game.floor.rooms = [Room(5, 5, 5, 5), Room(11, 5, 5, 5)]
    game.player.position = (7, 7)
    game.player.armor_class = 100
    medusa = MonsterState(910, "medusa", 13, 7, 100, running=True)
    game.floor.monsters.append(medusa)
    for x in range(7, 14):
        game.floor.set_tile((x, 7), Terrain.FLOOR)
    game.rng.seed(0)

    game.execute("wait")

    assert not medusa.gaze_attempted
    assert game.player.confused_turns == 0


def test_execute_wait_dragon_breathes_when_aligned_and_in_range() -> None:
    game = GameState(seed=21)
    game.floor.monsters.clear()
    room = Room(5, 5, 15, 5)
    game.floor.rooms = [room]
    game.player.position = (7, 7)
    game.player.hp = game.player.max_hp = 100
    game.player.armor_class = 100
    dragon = MonsterState(911, "dragon", 13, 7, 100, running=True)
    game.floor.monsters.append(dragon)
    for x in range(7, 14):
        game.floor.set_tile((x, 7), Terrain.FLOOR)
    game.rng.seed(2)

    result = game.execute("wait")

    assert result.success
    assert game.player.hp < 100
    assert (dragon.x, dragon.y) == (13, 7)


def test_fire_wand_bounces_off_dragon() -> None:
    game = GameState(seed=130)
    game.floor.monsters.clear()
    game.floor.rooms.clear()
    game.player.position = (5, 5)
    dragon = MonsterState(919, "dragon", 7, 5, 100)
    wand = ItemState(920, ItemKind.WAND, "wand of fire", effect="fire", charges=1)
    game.floor.monsters.append(dragon)
    game.player.inventory.append(wand)
    for x in range(5, 8):
        game.floor.set_tile((x, 5), Terrain.FLOOR)

    game.execute("zap", [wand.id, "east"])

    assert dragon.hp == 100


def test_execute_wait_dragon_does_not_breathe_across_passages_separated_by_a_room() -> None:
    game = GameState(seed=21)
    game.floor.monsters.clear()
    game.floor.rooms = [Room(7, 5, 3, 5)]
    game.player.position = (5, 7)
    game.player.hp = game.player.max_hp = 100
    game.player.armor_class = 100
    for x in range(5, 12):
        game.floor.set_tile((x, 7), Terrain.FLOOR)
    dragon = MonsterState(913, "dragon", 11, 7, 100, running=True)
    game.floor.monsters.append(dragon)
    game.rng.seed(2)

    game.execute("wait")

    assert game.player.hp == 100
    assert (dragon.x, dragon.y) == (10, 7)


def test_execute_wait_dragon_fire_bounces_off_wall_and_hits_monster() -> None:
    game = GameState(seed=21)
    game.floor.monsters.clear()
    room = Room(5, 5, 15, 5)
    game.floor.rooms = [room]
    game.player.position = (11, 7)
    game.player.hp = game.player.max_hp = 100
    game.player.armor_class = 100
    for x in range(7, 12):
        game.floor.set_tile((x, 7), Terrain.FLOOR)
    game.floor.set_tile((10, 7), Terrain.WALL)
    bat = MonsterState(914, "bat", 9, 7, 100)
    dragon = MonsterState(915, "dragon", 7, 7, 100, running=True)
    game.floor.monsters.extend((bat, dragon))
    game.rng.seed(2)

    game.execute("wait")

    assert bat.hp < 100
    assert game.player.hp == 100
    assert dragon in game.floor.monsters


def test_dragon_breath_continues_down_return_path_after_monster_saves(monkeypatch: pytest.MonkeyPatch) -> None:
    game = GameState(seed=21)
    game.floor.monsters.clear()
    game.floor.rooms = [Room(5, 5, 15, 5)]
    game.player.position = (11, 7)
    game.player.hp = game.player.max_hp = 100
    game.floor.set_tile((10, 7), Terrain.WALL)
    bat_that_saves = MonsterState(916, "bat", 9, 7, 100)
    bat_that_fails = MonsterState(917, "bat", 8, 7, 100)
    dragon = MonsterState(918, "dragon", 7, 7, 100, running=True)
    game.floor.monsters.extend((bat_that_saves, bat_that_fails, dragon))
    rolls = iter((19, 1, 2, 2, 2, 2, 2, 2))
    monkeypatch.setattr(game.rng, "randrange", lambda stop: 0)
    monkeypatch.setattr(game.rng, "randint", lambda start, stop: next(rolls))

    assert game._try_dragon_breath(dragon)

    assert bat_that_saves.hp == 100
    assert bat_that_fails.hp == 88
    assert game.player.hp == 100


@pytest.mark.parametrize("type_id", ["leprechaun", "vampire", "wraith"])
def test_execute_wait_does_not_apply_monster_special_effect_after_lethal_hit(type_id: str) -> None:
    game, monster = game_with_adjacent_monster(type_id)
    game.player.hp = 1
    game.player.gold = 1000
    game.player.level = 3
    game.player.exp = 40
    game.player.max_hp = 100
    game.player.armor_class = 100
    game.rng.seed(0)

    game.execute("wait")

    assert game.player.dead
    assert monster in game.floor.monsters
    if type_id == "leprechaun":
        assert game.player.gold == 1000
    else:
        assert game.player.max_hp == 100
        assert game.player.level == 3
        assert game.player.exp == 40


def test_execute_zap_awards_experience_when_wand_kills_monster() -> None:
    game, monster = game_with_adjacent_monster("bat", hp=1)
    expected_exp = monster.experience_reward
    wand = ItemState(912, ItemKind.WAND, "wand of magic missile", effect="magic_missile", charges=1)
    game.player.inventory.append(wand)
    game.rng.seed(0)

    result = game.execute("zap", [wand.id, "east"])

    assert result.success
    assert monster not in game.floor.monsters
    assert game.player.monsters_killed == 1
    assert game.player.exp == expected_exp


def test_execute_throw_uses_matching_launcher_and_thrown_damage() -> None:
    game, monster = game_with_adjacent_monster("kestrel")
    bow = ItemState(904, ItemKind.WEAPON, "short bow", hit_bonus=1, damage_bonus=1)
    arrows = ItemState(905, ItemKind.WEAPON, "arrows", quantity=2, damage_dice=(1, 1))
    game.player.inventory.extend((bow, arrows))
    game.player.equipped_weapon = bow.id
    game.rng.seed(0)

    result = game.execute("throw", [arrows.id, "east"])

    assert result.data.hit
    assert "It hits the kestrel for 5 damage." in result.message
    assert result.data.damage == 5
    assert monster.hp == 95
    assert arrows in game.player.inventory
    assert arrows.quantity == 1
    assert not any(item.name == "arrows" for item in game.floor.items)


@pytest.mark.parametrize("target_exists", [False, True])
def test_execute_throw_drops_projectile_when_it_does_not_hit(target_exists: bool) -> None:
    game, monster = game_with_adjacent_monster("kestrel")
    dagger = ItemState(906, ItemKind.WEAPON, "dagger")
    game.player.inventory.append(dagger)
    if target_exists:
        monster.type_id = "ur_vile"
        monster.running = True
        game.player.strength = 10
    else:
        game.floor.monsters.remove(monster)

    result = game.execute("throw", [dagger.id, "east"])

    if target_exists:
        assert result.data is not None
        assert not result.data.hit
    else:
        assert result.data is None
    assert dagger in game.floor.items


@pytest.mark.parametrize(
    ("starting_exp", "expected_level", "expected_hp", "expected_max_hp"), [(8, 1, 5, 20), (9, 2, 10, 25)]
)
def test_execute_kill_uses_rogue_experience_and_level_up_boundary(
    starting_exp: int, expected_level: int, expected_hp: int, expected_max_hp: int
) -> None:
    game, monster = game_with_adjacent_monster("kestrel", hp=1)
    game.player.exp = starting_exp
    game.player.hp = 5
    game.player.max_hp = 20
    monster.exp_value = 1
    game.rng.seed(0)

    result = game.execute("attack", ["east"])

    assert result.data.target_defeated
    assert game.player.exp == starting_exp + 1
    assert game.player.level == expected_level
    assert game.player.hp == expected_hp
    assert game.player.max_hp == expected_max_hp
