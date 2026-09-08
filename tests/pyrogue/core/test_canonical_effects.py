from unittest.mock import Mock

from pyrogue.core.rogue_game import GameState, ItemKind, ItemState, MonsterState, PlayerState, TrapKind, TrapState
from pyrogue.core.save_manager import SaveManager


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

    assert game.player.attack == base_attack + 2
    assert game.player.defense == base_defense - 2


def test_strength_ring_modifier_is_applied_directly_to_combat_rolls() -> None:
    game = GameState(seed=18)
    weapon = ItemState(id=904, kind=ItemKind.WEAPON, name="test weapon", damage_dice=(1, 2))
    ring = ItemState(
        id=905,
        kind=ItemKind.RING,
        name="ring of add strength",
        effect="strength",
        enchantment=2,
    )
    game.player.inventory.extend((weapon, ring))
    game.player.equipped_weapon = weapon.id
    assert game.equip(ring.id, ItemKind.RING).success

    game.rng = Mock()
    game.rng.randint.side_effect = [8, 2]
    result = game._resolve_attack(game.player, PlayerState(armor_class=10))

    assert result.hit
    assert result.damage == 5


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
    assert game.player.hp == initial_hp - 4
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
