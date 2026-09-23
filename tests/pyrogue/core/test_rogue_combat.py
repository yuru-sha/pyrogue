import pytest

from pyrogue.core.rogue_game import GameState, ItemKind, ItemState, MonsterState


def game_with_adjacent_monster(type_id: str, hp: int = 100) -> tuple[GameState, MonsterState]:
    game = GameState(seed=1)
    game.floor.monsters.clear()
    game.player.hp = game.player.max_hp = 100
    x, y = game.player.position
    monster = MonsterState(900, type_id, x + 1, y, hp)
    game.floor.monsters.append(monster)
    return game, monster


def test_spawned_monsters_use_rogue_hit_points_and_experience_values() -> None:
    game = GameState(seed=123)

    assert game.floor.monsters
    for monster in game.floor.monsters:
        exp_bonus = monster.max_hp // (8 if monster.level == 1 else 6)
        assert monster.max_hp == monster.hp
        assert monster.experience_reward == monster.definition.exp + exp_bonus


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
