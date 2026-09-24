from pyrogue.entities.actors.monster_types import FLOOR_MONSTERS, MONSTER_STATS


def test_floor_spawn_tables_only_reference_defined_monsters():
    assert {monster for entries in FLOOR_MONSTERS.values() for monster, _ in entries} <= MONSTER_STATS.keys()
