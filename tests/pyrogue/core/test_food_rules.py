from pyrogue.core.rogue_game import HUNGERTIME, STARVETIME, STOMACHSIZE, GameState, ItemKind, ItemState


def test_food_restores_random_rogue_amount_and_caps_at_stomach_size() -> None:
    game = GameState(seed=12)
    game.floor.monsters.clear()
    food = ItemState(9001, ItemKind.FOOD, "food ration", nutrition=HUNGERTIME - 200)
    game.player.inventory.append(food)
    game.player.food_units = 500
    game.rng.seed(12)
    amount = game.rng.randrange(400)
    game.rng.seed(12)

    assert game.execute("eat", [food.id]).success

    assert game.player.food_units == min(STOMACHSIZE, 500 + HUNGERTIME - 200 + amount) - 1


def test_eating_while_full_caps_food_and_consumes_the_food() -> None:
    game = GameState(seed=12)
    game.floor.monsters.clear()
    food = ItemState(9001, ItemKind.FOOD, "food ration", nutrition=HUNGERTIME - 200)
    game.player.inventory.append(food)
    game.player.food_units = STOMACHSIZE

    assert game.execute("eat", [food.id]).success

    assert food not in game.player.inventory
    assert game.player.food_units == STOMACHSIZE - 1


def test_eating_resets_negative_hunger_before_adding_original_nutrition() -> None:
    game = GameState(seed=31)
    game.floor.monsters.clear()
    food = ItemState(9002, ItemKind.FOOD, "food ration")
    game.player.inventory.append(food)
    game.player.food_units = -100
    game.rng.seed(31)
    expected_food_gain = HUNGERTIME - 200 + game.rng.randrange(400)
    game.rng.seed(31)

    assert game.execute("eat", [food.id]).success

    assert game.player.food_units == expected_food_gain - 1


def test_bad_tasting_food_grants_experience_and_levels_up() -> None:
    game = GameState(seed=2)
    game.floor.monsters.clear()
    food = ItemState(9003, ItemKind.FOOD, "food ration")
    game.player.inventory.append(food)
    game.player.exp = 9
    game.rng.seed(0)
    game.rng.randrange(400)
    assert game.rng.randrange(1, 101) > 70
    game.rng.seed(0)

    assert game.execute("eat", [food.id]).success

    assert game.player.exp == 10
    assert game.player.level == 2
    assert any("food tastes awful" in message for message in game.messages)


def test_good_tasting_food_does_not_grant_experience() -> None:
    game = GameState(seed=1)
    game.floor.monsters.clear()
    food = ItemState(9004, ItemKind.FOOD, "food ration")
    game.player.inventory.append(food)
    game.rng.seed(4)
    game.rng.randrange(400)
    assert game.rng.randrange(1, 101) <= 70
    game.rng.seed(4)

    game.execute("eat", [food.id])

    assert game.player.exp == 0
    assert game.player.level == 1
    assert any("tasted good" in message for message in game.messages)


def test_fruit_skips_bad_taste_roll_and_experience() -> None:
    game = GameState(seed=2)
    game.floor.monsters.clear()
    fruit = ItemState(9005, ItemKind.FOOD, "slime mold")
    game.player.inventory.append(fruit)
    game.rng.seed(0)
    game.rng.randrange(400)
    expected_next = game.rng.getstate()
    game.rng.seed(0)

    game.execute("eat", [fruit.id])

    assert game.player.exp == 0
    assert game.rng.getstate() == expected_next
    assert any("yummy" in message for message in game.messages)


def test_hunger_messages_trigger_when_crossing_original_thresholds() -> None:
    game = GameState(seed=12)
    game.floor.monsters.clear()
    game.player.food_units = 300

    game.execute("wait")
    assert "You are starting to get hungry." in game.messages[-2:]

    game.player.food_units = 150

    game.execute("wait")
    assert "You are starting to feel weak." in game.messages[-2:]


def test_fainting_blocks_player_actions_and_survives_save_round_trip() -> None:
    game = GameState(seed=7)
    game.floor.monsters.clear()
    game.player.faint_turns = 2
    position = game.player.position
    restored = GameState.from_dict(game.to_dict())

    result = restored.execute("l")

    assert result.turn_consumed
    assert result.message == "You are too weak to act."
    assert restored.player.faint_turns == 1
    assert restored.player.position == position


def test_fainting_starts_on_seeded_starvation_roll() -> None:
    game = GameState(seed=2)
    game.floor.monsters.clear()
    game.player.food_units = 0
    game.rng.seed(2)

    game.execute("wait")

    assert "You faint from lack of food." in game.messages
    assert 4 <= game.player.faint_turns <= 11


def test_starvation_death_uses_original_strict_boundary() -> None:
    game = GameState(seed=4)
    game.floor.monsters.clear()
    game.player.food_units = -STARVETIME

    game.execute("wait")

    assert game.player.food_units == -STARVETIME - 1
    assert not game.player.dead

    game.execute("wait")

    assert game.player.dead
    assert game.player.food_units == -STARVETIME - 2


def test_equipped_regeneration_ring_adds_two_food_units_per_turn() -> None:
    game = GameState(seed=4)
    game.floor.monsters.clear()
    ring = ItemState(9002, ItemKind.RING, "ring of regeneration", effect="regeneration")
    game.player.inventory.append(ring)
    game.player.equipped_rings.append(ring.id)
    game.player.food_units = 1000

    game.execute("wait")

    assert game.player.food_units == 997


def test_searching_ring_adds_food_drain_on_its_seeded_roll() -> None:
    game = GameState(seed=4)
    game.floor.monsters.clear()
    ring = ItemState(9003, ItemKind.RING, "ring of searching", effect="search")
    game.player.inventory.append(ring)
    game.player.equipped_rings.append(ring.id)
    game.player.food_units = 1000
    game.rng.seed(1)

    game.execute("wait")

    assert game.player.food_units == 998
