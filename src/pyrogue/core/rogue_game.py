"""
Rogue 5.4-style game state and rules.

The module deliberately has no TCOD dependency.  GUI and CLI callers execute
the same :class:`GameState` commands and only the GUI is responsible for
turning display cells into coloured characters.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from itertools import pairwise
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from collections.abc import Iterable

Position = tuple[int, int]

GAME_VERSION = "0.3.1"
DEFAULT_WIDTH = 80
DEFAULT_HEIGHT = 45
MAX_FLOOR = 26
MAZE_FLOORS = frozenset({7, 13, 19})
MAX_PACK = 23
HUNGERTIME = 1300
STOMACHSIZE = 2000
MORETIME = 150
STARVETIME = 850
CURSE_CHANCE = 0.5
BEAR_TRAP_DAMAGE = 2
MAX_EQUIPPED_RINGS = 2
EXPERIENCE_LEVELS = (
    10,
    20,
    40,
    80,
    160,
    320,
    640,
    1300,
    2600,
    5200,
    13000,
    26000,
    50000,
    100000,
    200000,
    400000,
    800000,
    2000000,
    4000000,
    8000000,
)
MONSTER_EXPERIENCE_X4_LEVEL = 7
MONSTER_EXPERIENCE_X20_LEVEL = 10
MONSTER_SPAWN_ORDER = (
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
MONSTER_DISGUISES = ("potion", "scroll", "ring", "wand", "food", "weapon", "armor", "stairs", "gold", "amulet")
SLEEP_TURNS = 5
VS_POISON = 0
VS_MAGIC = 3
RUSTABLE_ARMOR_CLASS = 9
HUH_DURATION = 20
LAMP_DISTANCE = 3
DRAGON_BREATH_RANGE = 6
DRAGON_BREATH_CHANCE = 5
MONSTER_FLY_MOVE_DISTANCE_SQUARED = 3
MYSTERIOUS_TRAP_MESSAGES = (
    "You are suddenly in a parallel dimension.",
    "The light in here suddenly seems different.",
    "You feel a sting in the side of your neck.",
    "Multicolored lines swirl around you, then fade.",
    "A strange light flashes in your eyes.",
    "A spike shoots past your ear!",
    "Sparks dance across your armor.",
    "You suddenly feel very thirsty.",
    "You feel time speed up suddenly.",
    "Time now seems to be going slower.",
    "Your pack turns inside out!",
)


class Terrain(str, Enum):
    """Logical terrain; glyphs belong to a renderer."""

    WALL = "wall"
    FLOOR = "floor"
    DOOR_CLOSED = "door_closed"
    DOOR_OPEN = "door_open"
    STAIRS_UP = "stairs_up"
    STAIRS_DOWN = "stairs_down"


TileKind = Terrain


class EntityKind(str, Enum):
    """Logical entity categories rendered on a dungeon cell."""

    PLAYER = "player"
    MONSTER = "monster"
    ITEM = "item"
    TRAP = "trap"


class ItemKind(str, Enum):
    """Item categories supported by the game rules."""

    WEAPON = "weapon"
    ARMOR = "armor"
    FOOD = "food"
    POTION = "potion"
    SCROLL = "scroll"
    WAND = "wand"
    RING = "ring"
    GOLD = "gold"
    AMULET = "amulet"


ItemType = ItemKind


class TrapKind(str, Enum):
    """Trap categories that can appear on a floor."""

    TRAP_DOOR = "trap_door"
    BEAR = "bear_trap"
    TELEPORT = "teleport"
    POISON_DART = "poison_dart"
    SLEEPING_GAS = "sleeping_gas"
    RUST = "rust_trap"
    MYSTERIOUS = "mysterious_trap"
    ARROW = "arrow_trap"


class GameStatus(str, Enum):
    """Terminal and active states of a game."""

    PLAYING = "playing"
    DEAD = "dead"
    VICTORY = "victory"
    QUIT = "quit"


class SaveCompatibilityError(ValueError):
    """The save was created for another game-state format."""


@dataclass(frozen=True)
class Room:
    """Rectangular room bounds in dungeon coordinates."""

    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> Position:
        """Return the room center position."""
        return self.x + self.width // 2, self.y + self.height // 2

    def contains(self, x: int, y: int) -> bool:
        """Return whether a position lies inside the room."""
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height


@dataclass
class ItemState:
    """Serializable item state held by a floor or the player."""

    id: int = 0
    kind: ItemKind = ItemKind.FOOD
    name: str = "food ration"
    appearance: str = ""
    identified: bool = True
    cursed: bool = False
    enchantment: int = 0
    charges: int = 0
    nutrition: int = 0
    quantity: int = 1
    position: Position | None = None
    damage_dice: tuple[int, int] = (1, 1)
    hit_bonus: int = 0
    damage_bonus: int = 0
    armor_bonus: int = 0
    effect: str = ""

    @property
    def display_name(self) -> str:
        """Return the name visible with the current identification state."""
        if self.identified or self.kind in {
            ItemKind.WEAPON,
            ItemKind.ARMOR,
            ItemKind.FOOD,
            ItemKind.GOLD,
            ItemKind.AMULET,
        }:
            return self.name
        return self.appearance or f"unknown {self.kind.value}"

    def to_dict(self) -> dict[str, Any]:
        """Serialize the item to JSON-compatible values."""
        data = self.__dict__.copy()
        data["kind"] = self.kind.value
        data["position"] = list(self.position) if self.position else None
        data["damage_dice"] = list(self.damage_dice)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ItemState:
        """Restore an item from serialized data."""
        data = dict(data)
        data["kind"] = ItemKind(data.get("kind", ItemKind.FOOD))
        if data.get("position") is not None:
            data["position"] = tuple(data["position"])
        data["damage_dice"] = tuple(data.get("damage_dice", (1, 1)))
        return cls(**{key: value for key, value in data.items() if key in cls.__dataclass_fields__})


@dataclass(frozen=True)
class MonsterDefinition:
    """Static combat and spawning data for one monster type."""

    id: str
    name: str
    level: int
    armor_class: int
    damage_dice: tuple[tuple[int, int], ...]
    exp: int
    carry_chance: int = 0
    abilities: frozenset[str] = frozenset()


# Rogue 5.4's monsters[] stats and flags, in A-Z order.
MONSTER_TYPES: tuple[MonsterDefinition, ...] = (
    MonsterDefinition("aquator", "aquator", 5, 2, ((0, 0), (0, 0)), 20, abilities=frozenset({"mean"})),
    MonsterDefinition("bat", "bat", 1, 3, ((1, 2),), 1, abilities=frozenset({"fly"})),
    MonsterDefinition("centaur", "centaur", 4, 4, ((1, 2), (1, 5), (1, 5)), 17, carry_chance=15),
    MonsterDefinition("dragon", "dragon", 10, -1, ((1, 8), (1, 8), (3, 10)), 5000, 100, frozenset({"mean"})),
    MonsterDefinition("emu", "emu", 1, 7, ((1, 2),), 2, abilities=frozenset({"mean"})),
    MonsterDefinition("venus_flytrap", "venus flytrap", 8, 3, ((0, 0),), 80, abilities=frozenset({"mean"})),
    MonsterDefinition(
        "griffin", "griffin", 13, 2, ((4, 3), (3, 5)), 2000, 20, frozenset({"mean", "fly", "regenerate"})
    ),
    MonsterDefinition("hobgoblin", "hobgoblin", 1, 5, ((1, 8),), 3, abilities=frozenset({"mean"})),
    MonsterDefinition("ice_monster", "ice monster", 1, 9, ((0, 0),), 5),
    MonsterDefinition("jabberwock", "jabberwock", 15, 6, ((2, 12), (2, 4)), 3000, 70),
    MonsterDefinition("kestrel", "kestrel", 1, 7, ((1, 4),), 1, abilities=frozenset({"mean", "fly"})),
    MonsterDefinition("leprechaun", "leprechaun", 3, 8, ((1, 1),), 10),
    MonsterDefinition("medusa", "medusa", 8, 2, ((3, 4), (3, 4), (2, 5)), 200, 40, frozenset({"mean"})),
    MonsterDefinition("nymph", "nymph", 3, 9, ((0, 0),), 37, 100),
    MonsterDefinition("orc", "orc", 1, 6, ((1, 8),), 5, 15, frozenset({"greed"})),
    MonsterDefinition("phantom", "phantom", 8, 3, ((4, 4),), 120, abilities=frozenset({"invisible"})),
    MonsterDefinition("quagga", "quagga", 3, 3, ((1, 5), (1, 5)), 15, abilities=frozenset({"mean"})),
    MonsterDefinition("rattlesnake", "rattlesnake", 2, 3, ((1, 6),), 9, abilities=frozenset({"mean"})),
    MonsterDefinition("snake", "snake", 1, 5, ((1, 3),), 2, abilities=frozenset({"mean"})),
    MonsterDefinition("troll", "troll", 6, 4, ((1, 8), (1, 8), (2, 6)), 120, 50, frozenset({"mean", "regenerate"})),
    MonsterDefinition("ur_vile", "black unicorn", 7, -2, ((1, 9), (1, 9), (2, 9)), 190, abilities=frozenset({"mean"})),
    MonsterDefinition("vampire", "vampire", 8, 1, ((1, 10),), 350, 20, frozenset({"mean", "regenerate"})),
    MonsterDefinition("wraith", "wraith", 5, 4, ((1, 6),), 55),
    MonsterDefinition("xeroc", "xeroc", 7, 7, ((4, 4),), 100, 30),
    MonsterDefinition("yeti", "yeti", 4, 6, ((1, 6), (1, 6)), 50, 30),
    MonsterDefinition("zombie", "zombie", 2, 8, ((1, 8),), 6, abilities=frozenset({"mean"})),
)
MONSTER_BY_ID = {monster.id: monster for monster in MONSTER_TYPES}


@dataclass
class MonsterState:
    """Mutable monster instance on a dungeon floor."""

    id: int
    type_id: str
    x: int
    y: int
    hp: int
    asleep: bool = False
    max_hp: int | None = None
    exp_value: int | None = None
    running: bool = False
    gaze_attempted: bool = False
    level_bonus: int = 0
    revealed: bool = False
    disguise: str | None = None

    def __post_init__(self) -> None:
        if self.max_hp is None:
            self.max_hp = self.hp

    @property
    def definition(self) -> MonsterDefinition:
        """Return the static definition for this monster."""
        return MONSTER_BY_ID[self.type_id]

    @property
    def name(self) -> str:
        """Return the monster display name."""
        return self.definition.name

    @property
    def level(self) -> int:
        """Return the monster level."""
        return self.definition.level + self.level_bonus

    @property
    def attack(self) -> int:
        """Return the monster's attack bonus."""
        return self.level

    @property
    def defense(self) -> int:
        """Return the monster's armor class."""
        return self.definition.armor_class - self.level_bonus

    def to_dict(self) -> dict[str, Any]:
        """Serialize the monster to JSON-compatible values."""
        return {
            "id": self.id,
            "type_id": self.type_id,
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "asleep": self.asleep,
            "max_hp": self.max_hp,
            "exp_value": self.exp_value,
            "running": self.running,
            "gaze_attempted": self.gaze_attempted,
            "level_bonus": self.level_bonus,
            "revealed": self.revealed,
            "disguise": self.disguise,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MonsterState:
        """Restore a monster from serialized data."""
        return cls(
            id=int(data["id"]),
            type_id=data["type_id"],
            x=int(data["x"]),
            y=int(data["y"]),
            hp=int(data["hp"]),
            asleep=bool(data.get("asleep", False)),
            max_hp=int(data["max_hp"]) if data.get("max_hp") is not None else None,
            exp_value=int(data["exp_value"]) if data.get("exp_value") is not None else None,
            running=bool(data.get("running", False)),
            gaze_attempted=bool(data.get("gaze_attempted", False)),
            level_bonus=int(data.get("level_bonus", 0)),
            revealed=bool(data.get("revealed", False)),
            disguise=data.get("disguise"),
        )

    @property
    def experience_reward(self) -> int:
        """Return the stored experience or the Rogue 5.4 reward for this monster."""
        if self.exp_value is not None:
            return self.exp_value
        hp_bonus = (self.max_hp or 0) // (8 if self.level == 1 else 6)
        if self.level >= MONSTER_EXPERIENCE_X20_LEVEL:
            hp_bonus *= 20
        elif self.level >= MONSTER_EXPERIENCE_X4_LEVEL:
            hp_bonus *= 4
        return self.definition.exp + self.level_bonus * 10 + hp_bonus


@dataclass
class TrapState:
    """Mutable trap instance on a dungeon floor."""

    id: int
    kind: TrapKind
    x: int
    y: int
    discovered: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete game state to JSON-compatible values."""
        return {
            "id": self.id,
            "kind": self.kind.value,
            "x": self.x,
            "y": self.y,
            "discovered": self.discovered,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TrapState:
        """Restore a trap from serialized data."""
        return cls(
            id=int(data["id"]),
            kind=TrapKind(data["kind"]),
            x=int(data["x"]),
            y=int(data["y"]),
            discovered=bool(data.get("discovered", False)),
        )


@dataclass
class FloorState:
    """Serializable map and entity state for one dungeon floor."""

    number: int
    width: int
    height: int
    tiles: list[list[Terrain]]
    rooms: list[Room] = field(default_factory=list)
    up_stairs: Position | None = None
    down_stairs: Position | None = None
    monsters: list[MonsterState] = field(default_factory=list)
    items: list[ItemState] = field(default_factory=list)
    traps: list[TrapState] = field(default_factory=list)
    explored: set[Position] = field(default_factory=set)
    player_position: Position | None = None

    def tile_at(self, position: Position) -> Terrain:
        """Return a floor tile, treating out-of-bounds as a wall."""
        x, y = position
        if not (0 <= x < self.width and 0 <= y < self.height):
            return Terrain.WALL
        return self.tiles[y][x]

    def set_tile(self, position: Position, terrain: Terrain) -> None:
        """Set a tile when its position lies inside the floor."""
        x, y = position
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = terrain

    def is_walkable(self, position: Position, doors_open: bool = False) -> bool:
        """Return whether the player can enter a position."""
        terrain = self.tile_at(position)
        return terrain in {Terrain.FLOOR, Terrain.DOOR_OPEN, Terrain.STAIRS_UP, Terrain.STAIRS_DOWN} or (
            doors_open and terrain == Terrain.DOOR_CLOSED
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the floor to JSON-compatible values."""
        return {
            "number": self.number,
            "width": self.width,
            "height": self.height,
            "tiles": [[tile.value for tile in row] for row in self.tiles],
            "rooms": [room.__dict__ for room in self.rooms],
            "up_stairs": list(self.up_stairs) if self.up_stairs else None,
            "down_stairs": list(self.down_stairs) if self.down_stairs else None,
            "monsters": [monster.to_dict() for monster in self.monsters],
            "items": [item.to_dict() for item in self.items],
            "traps": [trap.to_dict() for trap in self.traps],
            "explored": [list(position) for position in sorted(self.explored)],
            "player_position": list(self.player_position) if self.player_position else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FloorState:
        """Restore a floor from serialized data."""
        return cls(
            number=int(data["number"]),
            width=int(data["width"]),
            height=int(data["height"]),
            tiles=[[Terrain(tile) for tile in row] for row in data["tiles"]],
            rooms=[Room(**room) for room in data.get("rooms", [])],
            up_stairs=tuple(data["up_stairs"]) if data.get("up_stairs") else None,
            down_stairs=tuple(data["down_stairs"]) if data.get("down_stairs") else None,
            monsters=[MonsterState.from_dict(monster) for monster in data.get("monsters", [])],
            items=[ItemState.from_dict(item) for item in data.get("items", [])],
            traps=[TrapState.from_dict(trap) for trap in data.get("traps", [])],
            explored={tuple(position) for position in data.get("explored", [])},
            player_position=tuple(data["player_position"]) if data.get("player_position") else None,
        )


@dataclass
class PlayerState:
    x: int = 0
    y: int = 0
    level: int = 1
    exp: int = 0
    hp: int = 12
    max_hp: int = 12
    strength: int = 16
    armor_class: int = 10
    food_units: int = HUNGERTIME
    max_food_units: int = STOMACHSIZE
    gold: int = 0
    inventory: list[ItemState] = field(default_factory=list)
    equipped_weapon: int | None = None
    equipped_armor: int | None = None
    equipped_rings: list[int] = field(default_factory=list)
    has_amulet: bool = False
    turns_played: int = 0
    sleep_turns: int = 0
    frozen_turns: int = 0
    confused_turns: int = 0
    held: bool = False
    flytrap_hits: int = 0
    deepest_floor: int = 1
    monsters_killed: int = 0
    dead: bool = False
    death_cause: str | None = None

    @property
    def position(self) -> Position:
        return self.x, self.y

    @position.setter
    def position(self, value: Position) -> None:
        self.x, self.y = value

    @property
    def hp_max(self) -> int:
        return self.max_hp

    @property
    def attack(self) -> int:
        weapon = self.equipped(ItemKind.WEAPON)
        return (
            self.level
            + (weapon.hit_bonus + weapon.enchantment if weapon else 0)
            + _strength_adjustment(STR_TO_HIT, self.effective_strength())
            + (self.ring_bonus("dexterity") if weapon else 0)
        )

    @property
    def defense(self) -> int:
        return self.effective_armor_class()

    def get_attack(self) -> int:
        return self.attack

    def get_defense(self) -> int:
        return self.defense

    def item(self, item_id: int) -> ItemState | None:
        return next((item for item in self.inventory if item.id == item_id), None)

    def ring_bonus(self, effect: str) -> int:
        """Return the combined enchantment of equipped rings with an effect."""
        return sum(
            item.enchantment
            for ring_id in self.equipped_rings
            if (item := self.item(ring_id)) is not None and item.effect == effect
        )

    def has_ring_effect(self, effect: str) -> bool:
        """Return whether an equipped ring provides the requested effect."""
        return any(
            (item := self.item(ring_id)) is not None and item.effect == effect for ring_id in self.equipped_rings
        )

    def effective_strength(self) -> int:
        """Return strength after equipped ring effects."""
        return self.strength + self.ring_bonus("strength")

    def equipped(self, kind: ItemKind) -> ItemState | None:
        item_id = self.equipped_weapon if kind == ItemKind.WEAPON else self.equipped_armor
        if kind == ItemKind.RING:
            for ring_id in self.equipped_rings:
                item = self.item(ring_id)
                if item:
                    return item
            return None
        return self.item(item_id) if item_id is not None else None

    @property
    def equipped_item_ids(self) -> set[int]:
        """Return the IDs of all currently equipped items."""
        return {
            item_id
            for item_id in (self.equipped_weapon, self.equipped_armor, *self.equipped_rings)
            if item_id is not None
        }

    def effective_armor_class(self) -> int:
        armor = self.equipped(ItemKind.ARMOR)
        return (
            self.armor_class - (armor.armor_bonus + armor.enchantment if armor else 0) - self.ring_bonus("protection")
        )

    def score(self) -> int:
        return self.gold + self.monsters_killed * 10 + (1000 if self.has_amulet else 0)

    def to_dict(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        data["inventory"] = [item.to_dict() for item in self.inventory]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerState:
        data = dict(data)
        data["inventory"] = [ItemState.from_dict(item) for item in data.get("inventory", [])]
        data["equipped_rings"] = list(data.get("equipped_rings", []))
        return cls(**{key: value for key, value in data.items() if key in cls.__dataclass_fields__})


@dataclass(frozen=True)
class DisplayCell:
    """Renderer input; no glyph, colour, or TCOD object is stored here."""

    position: Position
    terrain: Terrain | None
    visible: bool
    explored: bool
    entity: EntityKind | None = None
    priority: int = 0
    entity_variant: str | None = None

    @property
    def logical_terrain(self) -> Terrain | None:
        """Return the logical terrain for this cell."""
        return self.terrain

    @property
    def entity_type(self) -> EntityKind | None:
        """Return the logical entity type for this cell."""
        return self.entity


@dataclass(frozen=True)
class CombatResult:
    """Outcome of one combat exchange."""

    hit: bool
    damage: int
    target_defeated: bool
    attacker: str
    defender: str


@dataclass(frozen=True)
class CommandResult:
    """Result returned by every canonical game command."""

    success: bool
    message: str = ""
    turn_consumed: bool = False
    state: GameStatus = GameStatus.PLAYING
    data: Any = None

    @property
    def should_end_turn(self) -> bool:
        """Return whether the command advances the turn."""
        return self.turn_consumed


class DungeonGenerator:
    """Deterministic room/maze generator with guaranteed stair paths."""

    def __init__(
        self, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT, rng: random.Random | None = None
    ) -> None:
        self.width = width
        self.height = height
        self.rng = rng or random.Random()  # noqa: S311 - game randomness is not cryptographic

    def generate(self, floor_number: int) -> FloorState:
        """Generate one deterministic floor."""
        floor = self._generate_maze(floor_number) if floor_number in MAZE_FLOORS else self._generate_rooms(floor_number)
        if floor.up_stairs and floor.down_stairs and not self._path_exists(floor, floor.up_stairs, floor.down_stairs):
            raise RuntimeError
        return floor

    def _blank(self) -> list[list[Terrain]]:
        return [[Terrain.WALL for _ in range(self.width)] for _ in range(self.height)]

    def _carve_room(self, tiles: list[list[Terrain]], room: Room) -> None:
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 < x < self.width - 1 and 0 < y < self.height - 1:
                    tiles[y][x] = Terrain.FLOOR

    def _carve_corridor(self, tiles: list[list[Terrain]], first: Position, second: Position) -> None:
        x, y = first
        horizontal_first = self.rng.choice((True, False))
        bend = (second[0], first[1]) if horizontal_first else (first[0], second[1])
        points = (bend, second)
        for target_x, target_y in points:
            while (x, y) != (target_x, target_y):
                if x != target_x:
                    x += 1 if target_x > x else -1
                elif y != target_y:
                    y += 1 if target_y > y else -1
                if 0 < x < self.width - 1 and 0 < y < self.height - 1:
                    tiles[y][x] = Terrain.FLOOR

    def _generate_rooms(self, floor_number: int) -> FloorState:
        tiles = self._blank()
        rooms: list[Room] = []
        columns, rows = 4, 3
        cell_width = max(8, (self.width - 2) // columns)
        cell_height = max(8, (self.height - 2) // rows)
        for row in range(rows):
            for column in range(columns):
                cell_x = 1 + column * cell_width
                cell_y = 1 + row * cell_height
                max_width = min(cell_width - 2, 14)
                max_height = min(cell_height - 2, 8)
                room_width = self.rng.randint(5, max(5, max_width))
                room_height = self.rng.randint(4, max(4, max_height))
                max_x = max(cell_x + 1, cell_x + cell_width - room_width - 1)
                max_y = max(cell_y + 1, cell_y + cell_height - room_height - 1)
                room = Room(
                    self.rng.randint(cell_x + 1, max_x),
                    self.rng.randint(cell_y + 1, max_y),
                    room_width,
                    room_height,
                )
                rooms.append(room)
                self._carve_room(tiles, room)

        for first, second in pairwise(rooms):
            self._carve_corridor(tiles, first.center, second.center)

        start = rooms[0].center
        end = rooms[-1].center
        up_stairs = start if floor_number >= 1 else None
        down_stairs = end if floor_number < MAX_FLOOR else None
        tiles[start[1]][start[0]] = Terrain.STAIRS_UP
        if down_stairs:
            tiles[end[1]][end[0]] = Terrain.STAIRS_DOWN

        # Doors are logical barriers which the reachability check treats as
        # traversable; the game opens them before moving through them.
        for room in rooms[1:-1:2]:
            door = (room.x, room.y + room.height // 2)
            if tiles[door[1]][door[0]] == Terrain.FLOOR:
                tiles[door[1]][door[0]] = Terrain.DOOR_CLOSED

        return FloorState(floor_number, self.width, self.height, tiles, rooms, up_stairs, down_stairs)

    def _generate_maze(self, floor_number: int) -> FloorState:
        tiles = self._blank()
        start = (1, 1)
        stack = [start]
        tiles[start[1]][start[0]] = Terrain.FLOOR
        while stack:
            x, y = stack[-1]
            candidates = []
            for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                nx, ny = x + dx, y + dy
                if 1 <= nx < self.width - 1 and 1 <= ny < self.height - 1 and tiles[ny][nx] == Terrain.WALL:
                    candidates.append((nx, ny, dx // 2, dy // 2))
            if not candidates:
                stack.pop()
                continue
            nx, ny, step_x, step_y = self.rng.choice(candidates)
            tiles[y + step_y][x + step_x] = Terrain.FLOOR
            tiles[ny][nx] = Terrain.FLOOR
            stack.append((nx, ny))

        reachable = self._reachable_positions(tiles, start)
        end = max(reachable, key=lambda position: abs(position[0] - start[0]) + abs(position[1] - start[1]))
        tiles[start[1]][start[0]] = Terrain.STAIRS_UP
        if floor_number < MAX_FLOOR:
            tiles[end[1]][end[0]] = Terrain.STAIRS_DOWN
            down_stairs: Position | None = end
        else:
            down_stairs = None
        return FloorState(floor_number, self.width, self.height, tiles, [], start, down_stairs)

    def _reachable_positions(self, tiles: list[list[Terrain]], start: Position) -> set[Position]:
        seen = {start}
        queue = deque([start])
        while queue:
            x, y = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                position = (x + dx, y + dy)
                px, py = position
                if position in seen or not (0 <= px < self.width and 0 <= py < self.height):
                    continue
                if tiles[py][px] != Terrain.WALL:
                    seen.add(position)
                    queue.append(position)
        return seen

    def _path_exists(self, floor: FloorState, start: Position, end: Position) -> bool:
        return end in self._reachable_positions(floor.tiles, start)


STR_TO_HIT = (-7, -6, -5, -4, -3, -2, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3)
STR_TO_DAMAGE = (-7, -6, -5, -4, -3, -2, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6)


def _strength_adjustment(table: tuple[int, ...], strength: int) -> int:
    return table[max(0, min(len(table) - 1, strength))]


def _roll(rng: random.Random, dice: tuple[int, int]) -> int:
    count, sides = dice
    return sum(rng.randint(1, sides) for _ in range(max(0, count)))


WEAPON_DATA: dict[str, tuple[tuple[int, int], int, int]] = {
    "mace": ((2, 4), 1, 1),
    "long sword": ((3, 4), 0, 0),
    "short bow": ((1, 1), 1, 0),
    "dagger": ((1, 6), 0, 0),
    "two handed sword": ((4, 4), 0, 0),
    "spear": ((2, 3), 0, 0),
    "darts": ((1, 1), 0, 0),
    "shuriken": ((1, 2), 0, 0),
    "arrows": ((1, 1), 0, 0),
}
THROWN_WEAPON_DATA: dict[str, tuple[tuple[int, int], str | None]] = {
    "mace": ((1, 3), None),
    "long sword": ((1, 2), None),
    "short bow": ((1, 1), None),
    "dagger": ((1, 4), None),
    "two handed sword": ((1, 2), None),
    "spear": ((1, 6), None),
    "darts": ((1, 3), None),
    "shuriken": ((2, 4), None),
    "arrows": ((2, 3), "short bow"),
}
ARMOR_DATA = {
    "leather armor": 2,
    "ring mail": 3,
    "studded leather armor": 3,
    "scale mail": 4,
    "chain mail": 5,
    "splint mail": 6,
    "banded mail": 6,
    "plate mail": 7,
}
POTION_EFFECTS = {
    "healing potion": "healing",
    "extra healing potion": "extra_healing",
    "strength potion": "strength",
    "restore strength potion": "restore_strength",
}
SCROLL_EFFECTS = {
    "identify scroll": "identify",
    "light scroll": "light",
    "remove curse scroll": "remove_curse",
    "enchant weapon scroll": "enchant_weapon",
    "enchant armor scroll": "enchant_armor",
    "teleportation scroll": "teleport",
    "magic mapping scroll": "magic_mapping",
}
RING_EFFECTS = {
    "ring of protection": "protection",
    "ring of add strength": "strength",
    "ring of dexterity": "dexterity",
    "ring of sustain strength": "sustain",
    "ring of searching": "search",
    "ring of regeneration": "regeneration",
    "ring of increase damage": "increase_damage",
}
WAND_EFFECTS = {
    "wand of magic missile": "magic_missile",
    "wand of light": "light",
    "wand of lightning": "lightning",
    "wand of fire": "fire",
    "wand of cold": "cold",
    "wand of teleport monster": "teleport_monster",
}
APPEARANCE_EFFECTS = {
    ItemKind.POTION: tuple(POTION_EFFECTS.values()),
    ItemKind.SCROLL: tuple(SCROLL_EFFECTS.values()),
    ItemKind.RING: tuple(RING_EFFECTS.values()),
    ItemKind.WAND: tuple(WAND_EFFECTS.values()),
}
LEGACY_APPEARANCE_POOL_SIZE = 6

DIRECTIONS: dict[str, Position] = {
    "north": (0, -1),
    "n": (0, -1),
    "south": (0, 1),
    "s": (0, 1),
    "east": (1, 0),
    "e": (1, 0),
    "west": (-1, 0),
    "w": (-1, 0),
    "nw": (-1, -1),
    "ne": (1, -1),
    "northeast": (1, -1),
    "northwest": (-1, -1),
    "southwest": (-1, 1),
    "southeast": (1, 1),
}
COMMAND_ALIASES = {
    "fight": "attack",
    "get": "pickup",
    "rest": "wait",
    "equip_weapon": "wield",
    "equip_armor": "wear",
    "take_off": "unequip_armor",
    "equip_ring": "put_on_ring",
    "unequip_ring": "remove_ring",
}
EQUIPMENT_KINDS = {
    "wield": ItemKind.WEAPON,
    "wear": ItemKind.ARMOR,
    "put_on_ring": ItemKind.RING,
}
UNEQUIPMENT_KINDS = {
    "unequip_weapon": ItemKind.WEAPON,
    "unequip_armor": ItemKind.ARMOR,
    "remove_ring": ItemKind.RING,
}
USE_ACTIONS = {
    ItemKind.FOOD: "eat",
    ItemKind.POTION: "quaff",
    ItemKind.SCROLL: "read",
    ItemKind.WEAPON: "wield",
    ItemKind.ARMOR: "wear",
    ItemKind.RING: "put_on_ring",
    ItemKind.WAND: "zap",
}


class GameState:
    """Complete deterministic game state and the shared command API."""

    COMMAND_KEYS: ClassVar[dict[str, tuple[str, Any]]] = {
        "h": ("move", (-1, 0)),
        "j": ("move", (0, 1)),
        "k": ("move", (0, -1)),
        "l": ("move", (1, 0)),
        "y": ("move", (-1, -1)),
        "u": ("move", (1, -1)),
        "b": ("move", (-1, 1)),
        "n": ("move", (1, 1)),
        "a": ("attack", None),
        "f": ("attack", None),
        ".": ("wait", None),
        ",": ("pickup", None),
        "d": ("drop", None),
        "e": ("eat", None),
        "q": ("quaff", None),
        "r": ("read", None),
        "w": ("wield", None),
        "W": ("wear", None),
        "T": ("unequip_armor", None),
        "P": ("put_on_ring", None),
        "R": ("remove_ring", None),
        "t": ("throw", None),
        "z": ("zap", None),
        "s": ("search", None),
        "^": ("identify_trap", None),
        "<": ("ascend", None),
        ">": ("descend", None),
        "i": ("inventory", None),
        "@": ("status", None),
        "?": ("help", None),
        "/": ("identify_item", None),
        "S": ("save", None),
        "Q": ("quit", None),
    }

    def __init__(self, seed: int | None = None, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT) -> None:
        self.seed = seed if seed is not None else random.SystemRandom().randrange(0, 2**63)
        self.width = width
        self.height = height
        self.rng = random.Random(self.seed)  # noqa: S311 - seeded game randomness is not cryptographic
        self.generator = DungeonGenerator(width, height, self.rng)
        self.status = GameStatus.PLAYING
        self.current_floor = 1
        self.player = PlayerState()
        self.floors: dict[int, FloorState] = {}
        self.messages: list[str] = []
        self._next_item_id = 1
        self._next_monster_id = 1
        self._next_trap_id = 1
        self._appearance_names = self._make_appearances()
        self._ensure_floor(1)
        self._setup_initial_inventory(self.floor)
        self.player.position = self.floor.up_stairs or self._first_floor_position(self.floor)
        self.visible_positions()
        self._message("You enter the Dungeons of Doom.")

    @property
    def floor(self) -> FloorState:
        """Return the currently active floor."""
        return self.floors[self.current_floor]

    @property
    def game_status(self) -> GameStatus:
        """Return the current terminal status."""
        return self.status

    @property
    def is_dead(self) -> bool:
        """Return whether the player has died."""
        return self.status == GameStatus.DEAD

    @property
    def is_victory(self) -> bool:
        """Return whether the game has been won."""
        return self.status == GameStatus.VICTORY

    def _message(self, message: str) -> None:
        self.messages.append(message)

    def _make_appearances(self) -> dict[ItemKind, dict[str, str]]:
        pools = {
            ItemKind.POTION: ["red", "blue", "green", "yellow", "purple", "orange"],
            ItemKind.SCROLL: [
                "ZELGO MER",
                "JUYED AWK YACC",
                "NR 9",
                "XIXAXA XOXAXA",
                "KIRJE",
                "FOOBIE BLETCH",
            ],
            ItemKind.RING: ["wooden", "opal", "coral", "black onyx", "pearl", "ruby", "diamond"],
            ItemKind.WAND: ["glass", "iron", "silver", "copper", "brass", "crystal"],
        }
        appearances = {}
        for values in pools.values():
            self.rng.shuffle(values)
        for kind, values in pools.items():
            appearance_values = [*values, "GARVEN DEH"] if kind == ItemKind.SCROLL else values
            appearances[kind] = dict(zip(APPEARANCE_EFFECTS[kind], appearance_values, strict=False))
        return appearances

    def _ensure_floor(self, number: int) -> FloorState:
        if number in self.floors:
            return self.floors[number]
        floor = self.generator.generate(number)
        self._spawn_items(floor)
        self._spawn_monsters(floor)
        self._spawn_traps(floor)
        self.floors[number] = floor
        return floor

    def _first_floor_position(self, floor: FloorState) -> Position:
        for y, row in enumerate(floor.tiles):
            for x, terrain in enumerate(row):
                if terrain != Terrain.WALL:
                    return x, y
        return 1, 1

    def _occupied(self, floor: FloorState) -> set[Position]:
        return (
            {(monster.x, monster.y) for monster in floor.monsters}
            | {item.position for item in floor.items if item.position is not None}
            | {(trap.x, trap.y) for trap in floor.traps}
        )

    def _free_position(self, floor: FloorState, extra_avoid: Iterable[Position] = ()) -> Position:
        avoid = self._occupied(floor) | set(extra_avoid)
        candidates = [
            (x, y)
            for y, row in enumerate(floor.tiles)
            for x, terrain in enumerate(row)
            if terrain in {Terrain.FLOOR, Terrain.DOOR_OPEN} and (x, y) not in avoid
        ]
        if not candidates:
            return floor.up_stairs or (1, 1)
        return self.rng.choice(candidates)

    def _teleport_player(self) -> tuple[Position, Position]:
        """Move the player to a random unoccupied walkable cell."""
        old_position = self.player.position
        self.player.position = self._free_position(self.floor, (old_position,))
        return old_position, self.player.position

    def _descend_to_next_floor(self) -> None:
        """Move the player to the matching up stairs on the next floor."""
        self.floor.player_position = self.player.position
        self.current_floor += 1
        target = self._ensure_floor(self.current_floor)
        self.player.position = target.up_stairs or self._first_floor_position(target)
        self.player.deepest_floor = max(self.player.deepest_floor, self.current_floor)

    def _new_item(self, floor: FloorState, kind: ItemKind, name: str | None = None) -> ItemState:
        names = {
            ItemKind.WEAPON: tuple(WEAPON_DATA),
            ItemKind.ARMOR: tuple(ARMOR_DATA),
            ItemKind.FOOD: ("food ration",),
            ItemKind.POTION: tuple(POTION_EFFECTS),
            ItemKind.SCROLL: tuple(SCROLL_EFFECTS),
            ItemKind.WAND: tuple(WAND_EFFECTS),
            ItemKind.RING: tuple(RING_EFFECTS),
            ItemKind.GOLD: ("gold",),
            ItemKind.AMULET: ("amulet of yendor",),
        }
        name = self.rng.choice(names[kind]) if name is None else name
        item = ItemState(id=self._next_item_id, kind=kind, name=name, position=self._free_position(floor))
        self._next_item_id += 1
        appearance_kind = kind in APPEARANCE_EFFECTS
        if appearance_kind:
            self.rng.randrange(LEGACY_APPEARANCE_POOL_SIZE)
        if kind == ItemKind.WEAPON:
            item.damage_dice, item.hit_bonus, item.damage_bonus = WEAPON_DATA.get(name, ((1, 4), 0, 0))
            item.enchantment = self.rng.choice((-1, 0, 0, 0, 1))
            item.cursed = item.enchantment < 0 and self.rng.random() < CURSE_CHANCE
        elif kind == ItemKind.ARMOR:
            item.armor_bonus = ARMOR_DATA.get(name, 2)
            item.enchantment = self.rng.choice((-1, 0, 0, 0, 1))
            item.cursed = item.enchantment < 0 and self.rng.random() < CURSE_CHANCE
        elif kind == ItemKind.FOOD:
            item.nutrition = MORETIME
        elif kind == ItemKind.POTION:
            item.effect = POTION_EFFECTS.get(name, "healing")
        elif kind == ItemKind.SCROLL:
            item.effect = SCROLL_EFFECTS.get(name, "identify")
        elif kind == ItemKind.WAND:
            item.effect = WAND_EFFECTS.get(name, "magic_missile")
            item.charges = self.rng.randint(3, 8)
        elif kind == ItemKind.RING:
            item.effect = RING_EFFECTS.get(name, "protection")
            item.enchantment = self.rng.choice((-1, 0, 0, 1))
            item.cursed = item.enchantment < 0 and self.rng.random() < CURSE_CHANCE
        elif kind == ItemKind.GOLD:
            item.quantity = self.rng.randint(2, 5 + floor.number * 2)
        if appearance_kind:
            item.identified = False
            item.appearance = self._appearance_names[kind][item.effect]
        return item

    def _setup_initial_inventory(self, floor: FloorState) -> None:
        food = self._new_item(floor, ItemKind.FOOD)
        armor = self._new_item(floor, ItemKind.ARMOR, "ring mail")
        mace = self._new_item(floor, ItemKind.WEAPON, "mace")
        bow = self._new_item(floor, ItemKind.WEAPON, "short bow")
        arrows = self._new_item(floor, ItemKind.WEAPON, "arrows")
        for item in (food, armor, mace, bow, arrows):
            item.position = None
            item.identified = True
            item.cursed = False
            self.player.inventory.append(item)
        armor.armor_bonus = 3
        armor.enchantment = 1
        mace.hit_bonus = mace.damage_bonus = 1
        mace.enchantment = 0
        bow.hit_bonus = 1
        bow.enchantment = 0
        arrows.quantity = self.rng.randint(25, 39)
        arrows.damage_dice = (1, 1)
        arrows.enchantment = 0
        self.player.equipped_weapon = mace.id
        self.player.equipped_armor = armor.id

    def _spawn_items(self, floor: FloorState) -> None:
        if floor.number == MAX_FLOOR:
            amulet = self._new_item(floor, ItemKind.AMULET)
            amulet.position = floor.down_stairs or self._free_position(floor)
            floor.items.append(amulet)
            return
        guaranteed = {
            1: (ItemKind.WEAPON, ItemKind.ARMOR, ItemKind.FOOD),
            2: (ItemKind.POTION, ItemKind.SCROLL, ItemKind.WAND, ItemKind.RING, ItemKind.GOLD),
        }.get(floor.number, ())
        kinds = list(guaranteed)
        kinds.extend(self.rng.choices(list(ItemKind)[:8], weights=[12, 10, 20, 20, 15, 8, 8, 15], k=2))
        for kind in kinds:
            item = self._new_item(floor, kind)
            if item.position not in {floor.up_stairs, floor.down_stairs}:
                floor.items.append(item)

    def _spawn_monsters(self, floor: FloorState) -> None:
        count = min(12, 3 + (floor.number - 1) // 3)
        stairs = tuple(position for position in (floor.up_stairs, floor.down_stairs) if position is not None)
        for _ in range(count):
            index = floor.number + self.rng.randrange(10) - 5
            if index < 0:
                index = self.rng.randrange(5)
            elif index >= len(MONSTER_SPAWN_ORDER):
                index = self.rng.randrange(5) + len(MONSTER_SPAWN_ORDER) - 5
            definition = MONSTER_BY_ID[MONSTER_SPAWN_ORDER[index]]
            position = self._free_position(floor, stairs)
            level_add = max(0, floor.number - MAX_FLOOR)
            level = definition.level + level_add
            max_hp = _roll(self.rng, (level, 8))
            monster = MonsterState(
                self._next_monster_id,
                definition.id,
                *position,
                max_hp,
                max_hp=max_hp,
                level_bonus=level_add,
                disguise=(
                    self.rng.choice(MONSTER_DISGUISES[: 10 if floor.number >= MAX_FLOOR else 9])
                    if definition.id == "xeroc"
                    else None
                ),
            )
            monster.exp_value = monster.experience_reward
            self._next_monster_id += 1
            floor.monsters.append(monster)

    def _spawn_traps(self, floor: FloorState) -> None:
        count = 1 + min(2, floor.number // 9)
        kinds = list(TrapKind)
        stairs = tuple(position for position in (floor.up_stairs, floor.down_stairs) if position is not None)
        for _ in range(count):
            position = self._free_position(floor, stairs)
            floor.traps.append(TrapState(self._next_trap_id, self.rng.choice(kinds), *position))
            self._next_trap_id += 1

    def _line(self, start: Position, end: Position) -> list[Position]:
        x0, y0 = start
        x1, y1 = end
        points: list[Position] = []
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            points.append((x0, y0))
            if (x0, y0) == (x1, y1):
                break
            twice = 2 * error
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy
        return points

    def _can_see(self, start: Position, end: Position, radius: int = 8) -> bool:
        if max(abs(start[0] - end[0]), abs(start[1] - end[1])) > radius:
            return False
        points = self._line(start, end)
        return all(self.floor.tile_at(point) not in {Terrain.WALL, Terrain.DOOR_CLOSED} for point in points[1:-1])

    def _calculate_visible_positions(self) -> set[Position]:
        """Calculate the cells visible from the player without changing state."""
        visible = set()
        origin = self.player.position
        radius = 8
        for y in range(max(0, origin[1] - radius), min(self.height, origin[1] + radius + 1)):
            for x in range(max(0, origin[0] - radius), min(self.width, origin[0] + radius + 1)):
                if max(abs(x - origin[0]), abs(y - origin[1])) <= radius and self._can_see(origin, (x, y), radius):
                    visible.add((x, y))
        return visible

    def visible_positions(self, update_explored: bool = True) -> set[Position]:
        """Calculate visible cells, optionally recording them as explored."""
        visible = self._calculate_visible_positions()
        if update_explored:
            self.floor.explored.update(visible)
        return visible

    def _illuminate_current_area(self) -> None:
        """Reveal the room containing the player, or the visible corridor area."""
        room = next((room for room in self.floor.rooms if room.contains(*self.player.position)), None)
        if room is None:
            self.visible_positions()
            return
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if self.floor.tile_at((x, y)) != Terrain.WALL:
                    self.floor.explored.add((x, y))

    def display_cells(self, show_all: bool = False) -> dict[Position, DisplayCell]:
        """Return renderer-neutral display cells, optionally bypassing FOV for display only."""
        visible = self._calculate_visible_positions() if show_all else self.visible_positions()
        cells: dict[Position, DisplayCell] = {}
        monster_positions = {(monster.x, monster.y): monster for monster in self.floor.monsters if monster.hp > 0}
        item_positions = {item.position: item.kind.value for item in self.floor.items if item.position is not None}
        trap_positions = {(trap.x, trap.y): trap.kind.value for trap in self.floor.traps if show_all or trap.discovered}
        for y in range(self.height):
            for x in range(self.width):
                position = (x, y)
                is_visible = position in visible
                is_displayed = show_all or is_visible
                is_explored = position in self.floor.explored
                terrain = self.floor.tile_at(position) if is_displayed or is_explored else None
                entity: EntityKind | None = None
                priority = 0
                entity_variant: str | None = None
                if is_displayed:
                    if position == self.player.position:
                        entity, priority = EntityKind.PLAYER, 100
                    elif (monster := monster_positions.get(position)) is not None and (
                        "invisible" not in monster.definition.abilities or monster.revealed
                    ):
                        if monster.disguise is not None:
                            entity, priority = EntityKind.ITEM, 80
                            entity_variant = monster.disguise
                        else:
                            entity, priority = EntityKind.MONSTER, 90
                            entity_variant = monster.type_id
                    elif position in item_positions:
                        entity, priority = EntityKind.ITEM, 80
                        entity_variant = item_positions[position]
                    elif position in trap_positions:
                        entity, priority = EntityKind.TRAP, 70
                        entity_variant = trap_positions[position]
                cells[position] = DisplayCell(
                    position, terrain, is_visible, is_explored, entity, priority, entity_variant
                )
        return cells

    get_display_cells = display_cells

    def _result(self, success: bool, message: str = "", turn_consumed: bool = False, data: Any = None) -> CommandResult:
        if message:
            self._message(message)
        return CommandResult(success, message, turn_consumed, self.status, data)

    def _required_exp(self) -> int:
        return EXPERIENCE_LEVELS[min(self.player.level - 1, len(EXPERIENCE_LEVELS) - 1)]

    def _level_up_if_needed(self) -> None:
        old_level = self.player.level
        while self.player.level <= len(EXPERIENCE_LEVELS) and self.player.exp >= self._required_exp():
            self.player.level += 1
        gained = self.player.level - old_level
        if gained:
            hp_gain = _roll(self.rng, (gained, 10))
            self.player.max_hp += hp_gain
            self.player.hp += hp_gain
            self._message(f"You have attained level {self.player.level}.")

    def _consume_food(self) -> None:
        old_food = self.player.food_units
        self.player.food_units -= 1
        if self.player.food_units <= 0:
            if self.player.food_units < -STARVETIME:
                self._die("starvation")
            elif self.rng.randrange(5) == 0:
                self._message("You faint from lack of food.")
        elif old_food >= 2 * MORETIME > self.player.food_units:
            self._message("You are starting to get hungry.")
        elif old_food >= MORETIME > self.player.food_units:
            self._message("You are starting to feel weak.")

    def _finish_turn(self, *, process_monsters: bool = True) -> None:
        self.player.turns_played += 1
        self._consume_food()
        if self.player.frozen_turns > 0:
            self.player.frozen_turns -= 1
        if self.player.confused_turns > 0:
            self.player.confused_turns -= 1
        if self.status == GameStatus.PLAYING:
            if self.player.has_ring_effect("search"):
                self._reveal_nearby_traps()
            regeneration = sum(
                1
                for ring_id in self.player.equipped_rings
                if (ring := self.player.item(ring_id)) is not None and ring.effect == "regeneration"
            )
            self.player.hp = min(self.player.max_hp, self.player.hp + regeneration)
            if process_monsters:
                self._process_monsters()
        if getattr(self, "_update_explored", True):
            self.visible_positions()

    def _rust_armor(self) -> bool:
        armor = self.player.equipped(ItemKind.ARMOR)
        if (
            armor is None
            or armor.name.lower() == "leather armor"
            or self.player.effective_armor_class() >= RUSTABLE_ARMOR_CLASS
        ):
            return False
        armor.enchantment -= 1
        return True

    def _saving_throw(self, effect: int) -> bool:
        protection = self.player.ring_bonus("protection") if effect == VS_MAGIC else 0
        need = 14 + effect - protection - self.player.level // 2
        return self.rng.randint(1, 20) >= need

    def _die(self, cause: str) -> None:
        self.player.hp = 0
        self.player.dead = True
        self.player.death_cause = cause
        self.status = GameStatus.DEAD
        self._message(f"You died ({cause}).")

    def _resolve_attack(
        self,
        attacker: PlayerState | MonsterState,
        defender: PlayerState | MonsterState,
        weapon: ItemState | None = None,
        *,
        thrown: bool = False,
    ) -> CombatResult:
        if isinstance(attacker, PlayerState) and isinstance(defender, MonsterState):
            self._reveal_monster(defender)
        if isinstance(attacker, PlayerState):
            weapon = weapon or (attacker.item(attacker.equipped_weapon) if attacker.equipped_weapon else None)
            level = attacker.level
            weapon_data = THROWN_WEAPON_DATA.get(weapon.name) if thrown and weapon else None
            damage_dice: tuple[tuple[int, int], ...] = (
                (weapon_data[0],) if weapon_data else ((weapon.damage_dice if weapon else (1, 4)),)
            )
            hit_bonus = (weapon.hit_bonus + weapon.enchantment) if weapon else 0
            damage_bonus = (weapon.damage_bonus + weapon.enchantment) if weapon else 0
            if weapon_data and weapon_data[1] and attacker.equipped_weapon:
                launcher = attacker.item(attacker.equipped_weapon)
                if launcher and launcher.name == weapon_data[1]:
                    hit_bonus += launcher.hit_bonus + launcher.enchantment
                    damage_bonus += launcher.damage_bonus + launcher.enchantment
            strength = attacker.effective_strength()
            if weapon and attacker.equipped_weapon == weapon.id:
                hit_bonus += attacker.ring_bonus("dexterity")
                damage_bonus += attacker.ring_bonus("increase_damage")
            attacker_name = "you"
        else:
            definition = attacker.definition
            level = attacker.level
            damage_dice = definition.damage_dice
            hit_bonus = 0
            damage_bonus = 0
            strength = 10
            attacker_name = definition.name
        hit_bonus += _strength_adjustment(STR_TO_HIT, strength)
        damage_bonus += _strength_adjustment(STR_TO_DAMAGE, strength)
        defender_ac = defender.effective_armor_class() if isinstance(defender, PlayerState) else defender.defense
        if isinstance(defender, PlayerState) or not defender.running:
            hit_bonus += 4
        need = 20 - level - defender_ac
        hit = False
        damage = 0
        for dice in damage_dice:
            if self.rng.randrange(20) + hit_bonus >= need:
                hit = True
                damage += max(0, _roll(self.rng, dice) + damage_bonus)
        if isinstance(defender, PlayerState):
            defender.hp = max(0, defender.hp - damage)
            defeated = defender.hp == 0
            defender_name = "you"
        else:
            defender.hp = max(0, defender.hp - damage)
            defeated = defender.hp == 0
            defender_name = defender.definition.name
        return CombatResult(hit, damage, defeated, attacker_name, defender_name)

    def _apply_player_attack(
        self, monster: MonsterState, weapon: ItemState | None = None, *, thrown: bool = False
    ) -> CombatResult:
        result = self._resolve_attack(self.player, monster, weapon, thrown=thrown)
        if result.target_defeated:
            self._defeat_monster(monster)
        else:
            monster.asleep = False
            monster.running = True
        return result

    def _reveal_monster(self, monster: MonsterState) -> None:
        monster.revealed = True
        monster.disguise = None

    def _defeat_monster(self, monster: MonsterState) -> None:
        self.player.monsters_killed += 1
        self.player.exp += monster.experience_reward
        self._message(f"You defeated the {monster.name}.")
        self._level_up_if_needed()
        if monster.type_id == "venus_flytrap":
            self.player.held = False
            self.player.flytrap_hits = 0
        self.floor.monsters.remove(monster)

    def _player_attack(self, monster: MonsterState) -> CommandResult:
        result = self._apply_player_attack(monster)
        if result.hit:
            message = f"You hit the {monster.name} for {result.damage} damage."
        else:
            message = f"You miss the {monster.name}."
        self._message(message)
        self._finish_turn()
        return self._result(True, "", True, result)

    def attack(self, direction: Position | None = None) -> CommandResult:
        """Attack an adjacent monster, optionally in a named direction."""
        candidates = (
            [direction] if direction else [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
        )
        for dx, dy in candidates:
            target = (self.player.x + dx, self.player.y + dy)
            monster = next((item for item in self.floor.monsters if (item.x, item.y) == target), None)
            if monster:
                return self._player_attack(monster)
        return self._result(False, "There is no monster there.")

    def _monster_attack(self, monster: MonsterState) -> None:
        self._reveal_monster(monster)
        result = self._resolve_attack(monster, self.player)
        if result.target_defeated:
            self._die(f"the {monster.name}")
            return
        if result.hit:
            self._message(f"The {monster.name} hits you for {result.damage} damage.")
            if monster.type_id == "aquator" and self._rust_armor():
                self._message("The aquator's touch weakens your armor.")
            elif monster.type_id == "ice_monster":
                self.player.frozen_turns += self.rng.randrange(2) + 2
                self._message(f"You are frozen by the {monster.name}.")
            elif monster.type_id == "venus_flytrap":
                self.player.held = True
                self.player.hp -= self.player.flytrap_hits
                self.player.flytrap_hits += 1
                if self.player.hp <= 0:
                    self._die(monster.name)
            elif monster.type_id == "rattlesnake" and not self._saving_throw(VS_POISON):
                if not self.player.has_ring_effect("sustain"):
                    self.player.strength = max(1, self.player.strength - 1)
                    self._message("The rattlesnake's bite weakens you.")
            elif monster.type_id in {"wraith", "vampire"}:
                drain_chance = 15 if monster.type_id == "wraith" else 30
                if self.rng.randrange(100) < drain_chance:
                    if monster.type_id == "wraith":
                        if self.player.exp == 0:
                            self._die(monster.name)
                            return
                        self.player.level -= 1
                        if self.player.level == 0:
                            self.player.level = 1
                            self.player.exp = 0
                        else:
                            self.player.exp = EXPERIENCE_LEVELS[self.player.level - 1] + 1
                    drain = _roll(self.rng, (1, 10) if monster.type_id == "wraith" else (1, 3))
                    self.player.hp -= drain
                    self.player.max_hp -= drain
                    if self.player.hp <= 0:
                        self.player.hp = 1
                    self._message("You suddenly feel weaker.")
                    if self.player.max_hp <= 0:
                        self._die(monster.name)
            elif monster.type_id == "leprechaun":
                gold_roll = 50 + 10 * self.current_floor
                stolen = self.rng.randrange(gold_roll) + 2
                if not self._saving_throw(VS_MAGIC):
                    stolen += sum(self.rng.randrange(gold_roll) + 2 for _ in range(4))
                self.player.gold = max(0, self.player.gold - stolen)
                self.floor.monsters.remove(monster)
            elif monster.type_id == "nymph":
                magic_items = [
                    item
                    for item in self.player.inventory
                    if item.id not in self.player.equipped_item_ids
                    and (
                        item.kind in {ItemKind.POTION, ItemKind.SCROLL, ItemKind.WAND, ItemKind.RING}
                        or (item.kind == ItemKind.WEAPON and (item.enchantment or item.hit_bonus or item.damage_bonus))
                        or (item.kind == ItemKind.ARMOR and item.enchantment)
                    )
                ]
                if magic_items:
                    self._remove_inventory_item(self.rng.choice(magic_items))
                    self.floor.monsters.remove(monster)
        else:
            self._message(f"The {monster.name} misses you.")
            if monster.type_id == "venus_flytrap":
                self.player.hp -= self.player.flytrap_hits
                if self.player.hp <= 0:
                    self._die(monster.name)

    def _try_dragon_breath(self, monster: MonsterState) -> bool:
        monster_x, monster_y = monster.x, monster.y
        player_x, player_y = self.player.position
        dx, dy = abs(monster_x - player_x), abs(monster_y - player_y)
        path = self._line((monster_x, monster_y), self.player.position)
        monster_room = next((room for room in self.floor.rooms if room.contains(monster_x, monster_y)), None)
        player_room = next((room for room in self.floor.rooms if room.contains(player_x, player_y)), None)
        same_region = monster_room is player_room and monster_room is not None
        if monster_room is None and player_room is None:
            # ponytail: a clear corridor ray is one passage until passage IDs exist.
            same_region = not any(any(room.contains(*position) for room in self.floor.rooms) for position in path[1:-1])
        aligned = dx == 0 or dy in (0, dx)
        in_range = dx * dx + dy * dy <= DRAGON_BREATH_RANGE * DRAGON_BREATH_RANGE
        if not same_region or not aligned or not in_range or self.rng.randrange(DRAGON_BREATH_CHANCE) != 0:
            return False
        self._message("The dragon breathes fire at you.")
        x, y = monster_x, monster_y
        step_x = (player_x > monster_x) - (player_x < monster_x)
        step_y = (player_y > monster_y) - (player_y < monster_y)
        targets_player = True
        changed_target = False
        for _ in range(DRAGON_BREATH_RANGE):
            x += step_x
            y += step_y
            position = (x, y)
            target = next(
                (other for other in self.floor.monsters if other is not monster and (other.x, other.y) == position),
                None,
            )
            if (
                target is None
                and position != self.player.position
                and self.floor.tile_at(position) in {Terrain.WALL, Terrain.DOOR_CLOSED}
            ):
                if not changed_target:
                    targets_player = not targets_player
                changed_target = False
                step_x, step_y = -step_x, -step_y
                self._message("The dragon's fire bounces.")
                continue
            if not targets_player and target:
                if self.rng.randint(1, 20) < 14 + VS_MAGIC - target.level // 2:
                    if target.type_id == "dragon":
                        self._message("The flame bounces off the dragon.")
                    else:
                        self._reveal_monster(target)
                        target.hp = max(0, target.hp - _roll(self.rng, (6, 6)))
                        self._message(f"The flame hits the {target.name}.")
                        if target.hp == 0:
                            self._defeat_monster(target)
                    return True
                continue
            if targets_player and position == self.player.position:
                targets_player = False
                changed_target = not changed_target
                if not self._saving_throw(VS_MAGIC):
                    self.player.hp = max(0, self.player.hp - _roll(self.rng, (6, 6)))
                    self._message("The dragon's fire hits you.")
                    if self.player.hp == 0:
                        self._die(monster.name)
                    return True
        return True

    def _process_monsters(self) -> None:
        for monster in list(self.floor.monsters):
            if monster.hp <= 0 or self.status != GameStatus.PLAYING:
                continue
            if monster.asleep:
                continue
            visible = self._can_see((monster.x, monster.y), self.player.position, monster.level + 4)
            distance = max(abs(monster.x - self.player.x), abs(monster.y - self.player.y))
            # ponytail: rooms have no darkness flag; add one if dark rooms are modeled.
            player_room = next((room for room in self.floor.rooms if room.contains(*self.player.position)), None)
            monster_room = next((room for room in self.floor.rooms if room.contains(monster.x, monster.y)), None)
            in_gaze_range = (player_room is not None and player_room == monster_room) or distance < LAMP_DISTANCE
            abilities = monster.definition.abilities
            if visible and not monster.running and ("mean" in abilities or "greed" in abilities):
                monster.running = True
            if (
                monster.type_id == "medusa"
                and monster.running
                and not monster.gaze_attempted
                and visible
                and in_gaze_range
            ):
                monster.gaze_attempted = True
                if not self._saving_throw(VS_MAGIC):
                    confused_turns = HUH_DURATION - HUH_DURATION // 20 + self.rng.randrange(HUH_DURATION // 10)
                    self.player.confused_turns += confused_turns
                    self._message("The medusa's gaze confuses you.")
            if monster.type_id == "dragon" and monster.running and self._try_dragon_breath(monster):
                continue
            if distance <= 1:
                self._monster_attack(monster)
                continue
            if not visible or (not monster.running and "mean" not in abilities):
                continue
            gold = (
                next(
                    (
                        item
                        for item in self.floor.items
                        if item.kind == ItemKind.GOLD
                        and item.position is not None
                        and player_room is not None
                        and player_room.contains(*item.position)
                    ),
                    None,
                )
                if "greed" in abilities
                else None
            )
            if gold and (monster.x, monster.y) == gold.position:
                self.floor.items.remove(gold)
                gold = None
            chase_target = gold.position if gold and gold.position is not None else self.player.position
            for step in range(2 if "fly" in abilities else 1):
                player_dx = self.player.x - monster.x
                player_dy = self.player.y - monster.y
                if step and player_dx * player_dx + player_dy * player_dy < MONSTER_FLY_MOVE_DISTANCE_SQUARED:
                    break
                dx = chase_target[0] - monster.x
                dy = chase_target[1] - monster.y
                random_move = (
                    self.rng.randrange(2) == 0
                    if monster.type_id == "bat"
                    else monster.type_id == "phantom" and self.rng.randrange(5) == 0
                )
                if random_move:
                    choices = [
                        (monster.x + move_x, monster.y + move_y)
                        for move_x in (-1, 0, 1)
                        for move_y in (-1, 0, 1)
                        if (move_x or move_y)
                        and (
                            (monster.x + move_x, monster.y + move_y) == self.player.position
                            or self.floor.is_walkable((monster.x + move_x, monster.y + move_y))
                        )
                        and not any(
                            other.x == monster.x + move_x and other.y == monster.y + move_y
                            for other in self.floor.monsters
                            if other is not monster
                        )
                    ]
                    target = self.rng.choice(choices) if choices else (monster.x, monster.y)
                else:
                    target = (
                        monster.x + (dx > 0) - (dx < 0),
                        monster.y + (dy > 0) - (dy < 0),
                    )
                if target == self.player.position:
                    self._monster_attack(monster)
                    break
                if not self.floor.is_walkable(target) or any(
                    other.x == target[0] and other.y == target[1]
                    for other in self.floor.monsters
                    if other is not monster
                ):
                    break
                monster.x, monster.y = target
                monster.running = True
                if gold and target == gold.position:
                    self.floor.items.remove(gold)
                    break

    def move(self, dx: int, dy: int) -> CommandResult:
        """Move one step, open a closed door, or attack an adjacent monster."""
        if self.status != GameStatus.PLAYING:
            return self._result(False, "The game is over.")
        if dx not in {-1, 0, 1} or dy not in {-1, 0, 1} or (dx == 0 and dy == 0):
            return self._result(False, "Invalid movement.")
        if self.player.confused_turns > 0 and self.rng.randrange(5) == 0:
            dx = dy = 0
            while (dx, dy) == (0, 0):
                dx, dy = self.rng.randrange(3) - 1, self.rng.randrange(3) - 1
        target = (self.player.x + dx, self.player.y + dy)
        monster = next((monster for monster in self.floor.monsters if (monster.x, monster.y) == target), None)
        if monster and (not self.player.held or monster.type_id == "venus_flytrap"):
            return self._player_attack(monster)
        terrain = self.floor.tile_at(target)
        if terrain == Terrain.DOOR_CLOSED and not self.player.held:
            self.floor.set_tile(target, Terrain.DOOR_OPEN)
            self._message("You open the door.")
            self._finish_turn()
            return self._result(True, "", True)
        if self.player.held or not self.floor.is_walkable(target):
            message = "You are held by the venus flytrap." if self.player.held else "You cannot move there."
            return self._result(False, message)
        self.player.position = target
        trap = next((trap for trap in self.floor.traps if (trap.x, trap.y) == target), None)
        trap_message = self._trigger_trap(trap) if trap else ""
        self._finish_turn()
        return self._result(True, trap_message, True)

    def wait(self) -> CommandResult:
        """Consume one turn without moving."""
        if self.status != GameStatus.PLAYING:
            return self._result(False, "The game is over.")
        self._finish_turn()
        return self._result(True, "You wait.", True)

    def pickup(self) -> CommandResult:
        """Pick up the first item at the player's current position."""
        items = [item for item in self.floor.items if item.position == self.player.position]
        if not items:
            return self._result(False, "There is nothing here to pick up.")
        item = items[0]
        self.floor.items.remove(item)
        if item.kind == ItemKind.GOLD:
            self.player.gold += item.quantity
            self._message(f"You pick up {item.quantity} gold pieces.")
        elif item.kind == ItemKind.AMULET:
            item.position = None
            self.player.inventory.append(item)
            self.player.has_amulet = True
            self._message("You have found the Amulet of Yendor!")
        elif len(self.player.inventory) >= MAX_PACK:
            item.position = self.player.position
            self.floor.items.append(item)
            return self._result(False, "Your pack is full.")
        else:
            item.position = None
            self.player.inventory.append(item)
            self._message(f"You pick up {item.display_name}.")
        self._finish_turn()
        return self._result(True, "", True, item)

    def _find_item(self, value: Any, *, kind: ItemKind | None = None) -> ItemState | None:
        if value is None:
            return next((item for item in self.player.inventory if kind is None or item.kind == kind), None)
        text = str(value).strip().lower()
        if text.isdigit():
            item_id = int(text)
            by_id = next((item for item in self.player.inventory if item.id == item_id), None)
            if by_id:
                return by_id
            index = item_id
            if 0 <= index < len(self.player.inventory):
                return self.player.inventory[index]
        return next(
            (item for item in self.player.inventory if item.name.lower() == text or item.display_name.lower() == text),
            None,
        )

    def _remove_inventory_item(self, item: ItemState) -> None:
        if self.player.equipped_weapon == item.id:
            self.player.equipped_weapon = None
        if self.player.equipped_armor == item.id:
            self.player.equipped_armor = None
        self.player.equipped_rings = [ring_id for ring_id in self.player.equipped_rings if ring_id != item.id]
        self.player.inventory.remove(item)

    def drop(self, value: Any = None) -> CommandResult:
        """Drop one pack item on the current floor."""
        item = self._find_item(value)
        if not item:
            return self._result(False, "Usage: drop <item>")
        if item.cursed and item.id in self.player.equipped_item_ids:
            return self._result(False, "You cannot drop a cursed equipped item.")
        self._remove_inventory_item(item)
        item.position = self.player.position
        self.floor.items.append(item)
        self._finish_turn()
        return self._result(True, f"You drop the {item.display_name}.", True)

    def eat(self, value: Any = None) -> CommandResult:
        """Consume a food ration and restore food units."""
        item = self._find_item(value, kind=ItemKind.FOOD)
        if not item or item.kind != ItemKind.FOOD:
            return self._result(False, "You have no food to eat.")
        self._remove_inventory_item(item)
        self.player.food_units = min(self.player.max_food_units, self.player.food_units + item.nutrition)
        self._finish_turn()
        return self._result(True, "You eat the food.", True)

    def _use_potion(self, item: ItemState) -> str:
        effect = item.effect
        if effect in {"healing", "extra_healing"}:
            amount = 8 if effect == "healing" else 16
            self.player.hp = min(self.player.max_hp, self.player.hp + amount)
            return "You feel better."
        if effect == "strength":
            self.player.strength = min(31, self.player.strength + 1)
            return "You feel stronger."
        if effect == "restore_strength":
            self.player.strength = 16
            return "You feel your strength return."
        return "You feel a strange sensation."

    def quaff(self, value: Any = None) -> CommandResult:
        """Drink a potion and apply its effect."""
        item = self._find_item(value, kind=ItemKind.POTION)
        if not item or item.kind != ItemKind.POTION:
            return self._result(False, "You have no potion to drink.")
        message = self._use_potion(item)
        item.identified = True
        self._remove_inventory_item(item)
        self._finish_turn()
        return self._result(True, message, True)

    def read(self, value: Any = None) -> CommandResult:
        """Read a scroll and apply its effect."""
        item = self._find_item(value, kind=ItemKind.SCROLL)
        if not item or item.kind != ItemKind.SCROLL:
            return self._result(False, "You have no scroll to read.")
        item.identified = True
        effect = item.effect
        if effect == "identify":
            for other in self.player.inventory:
                if other.kind in {ItemKind.POTION, ItemKind.SCROLL, ItemKind.RING, ItemKind.WAND}:
                    other.identified = True
            message = "You identify the objects in your pack."
        elif effect == "remove_curse":
            for other in self.player.inventory:
                other.cursed = False
            message = "You feel as if somebody is watching over you."
        elif effect == "enchant_weapon":
            weapon = self.player.equipped(ItemKind.WEAPON)
            if weapon:
                weapon.enchantment += 1
            message = "Your weapon glows blue for a moment."
        elif effect == "enchant_armor":
            armor = self.player.equipped(ItemKind.ARMOR)
            if armor:
                armor.enchantment += 1
            message = "Your armor glows blue for a moment."
        elif effect == "light":
            self._illuminate_current_area()
            message = "The room is lit."
        elif effect == "teleport":
            old_position, new_position = self._teleport_player()
            message = f"You teleport from {old_position} to {new_position}."
        elif effect == "magic_mapping":
            self.floor.explored.update((x, y) for y in range(self.height) for x in range(self.width))
            message = "You feel more familiar with the dungeon."
        else:
            message = "The scroll disappears in a flash of light."
        self._remove_inventory_item(item)
        self._finish_turn()
        return self._result(True, message, True)

    def equip(self, value: Any, kind: ItemKind) -> CommandResult:
        """Equip a weapon, armor item, or ring from the pack."""
        item = self._find_item(value, kind=kind)
        if not item or item.kind != kind:
            return self._result(False, f"You have no {kind.value} to equip.")
        if item.cursed and item.id in self.player.equipped_item_ids:
            return self._result(False, "That item is already cursed on you.")
        if kind == ItemKind.WEAPON:
            self.player.equipped_weapon = item.id
        elif kind == ItemKind.ARMOR:
            self.player.equipped_armor = item.id
        elif item.id not in self.player.equipped_rings:
            if len(self.player.equipped_rings) >= MAX_EQUIPPED_RINGS:
                self.player.equipped_rings.pop(0)
            self.player.equipped_rings.append(item.id)
        self._finish_turn()
        return self._result(True, f"You equip the {item.display_name}.", True)

    def unequip(self, value: Any, kind: ItemKind) -> CommandResult:
        """Remove an equipped item unless it is cursed."""
        item = self.player.equipped(kind) if value is None else self._find_item(value)
        if not item or item.kind != kind:
            return self._result(False, "That item is not equipped.")
        if item.cursed:
            return self._result(False, "You cannot remove a cursed item.")
        if kind == ItemKind.WEAPON and self.player.equipped_weapon == item.id:
            self.player.equipped_weapon = None
        elif kind == ItemKind.ARMOR and self.player.equipped_armor == item.id:
            self.player.equipped_armor = None
        elif kind == ItemKind.RING and item.id in self.player.equipped_rings:
            self.player.equipped_rings.remove(item.id)
        else:
            return self._result(False, "That item is not equipped.")
        self._finish_turn()
        return self._result(True, f"You remove the {item.display_name}.", True)

    def _trace_projectile(self, direction: Position) -> tuple[Position, MonsterState | None]:
        """Return the last open position and the first monster in a direction."""
        x, y = self.player.position
        landing = self.player.position
        for _ in range(8):
            x += direction[0]
            y += direction[1]
            if not self.floor.is_walkable((x, y)):
                break
            landing = (x, y)
            monster = next((monster for monster in self.floor.monsters if (monster.x, monster.y) == landing), None)
            if monster:
                return landing, monster
        return landing, None

    def throw(self, value: Any, direction: Position = (1, 0)) -> CommandResult:
        """Throw a pack item in a direction."""
        item = self._find_item(value)
        if not item:
            return self._result(False, "Usage: throw <item> <direction>")
        if item.id in self.player.equipped_item_ids and item.cursed:
            return self._result(False, "You cannot throw a cursed equipped item.")
        landing, hit_monster = self._trace_projectile(direction)
        result = self._apply_player_attack(hit_monster, item, thrown=True) if hit_monster else None
        if item.quantity > 1:
            item.quantity -= 1
            projectile = ItemState.from_dict(item.to_dict())
            projectile.id = self._next_item_id
            projectile.quantity = 1
            self._next_item_id += 1
        else:
            self._remove_inventory_item(item)
            projectile = item
        if not result or not result.hit:
            projectile.position = landing
            self.floor.items.append(projectile)
        self._finish_turn()
        message = f"You throw the {item.display_name}."
        if result and hit_monster:
            message += (
                f" It hits the {hit_monster.name} for {result.damage} damage."
                if result.hit
                else f" It misses the {hit_monster.name}."
            )
        return self._result(True, message, True, result)

    def zap(self, value: Any, direction: Position | None = None) -> CommandResult:
        """Use one charge from a wand in the given direction."""
        item = self._find_item(value, kind=ItemKind.WAND)
        if not item or item.kind != ItemKind.WAND:
            return self._result(False, "Usage: zap <wand> <direction>")
        if item.charges <= 0:
            return self._result(False, "The wand has no charges left.")
        if item.effect == "light":
            target = None
        else:
            if direction is None or direction not in DIRECTIONS.values():
                return self._result(False, "You need to choose a direction.")
            _, target = self._trace_projectile(direction)
        item.charges -= 1
        if target and item.effect in {"magic_missile", "lightning", "fire", "cold"}:
            if target.type_id == "dragon" and item.effect == "fire":
                message = "The fire bounces off the dragon."
            else:
                damage = _roll(self.rng, (1, 4) if item.effect == "magic_missile" else (6, 6))
                self._reveal_monster(target)
                target.hp = max(0, target.hp - damage)
                message = f"The {item.display_name} hits the {target.name}."
                if target.hp == 0:
                    self._defeat_monster(target)
        elif target and item.effect == "teleport_monster":
            target.x, target.y = self._free_position(self.floor, (self.player.position,))
            message = f"The {target.name} vanishes."
        elif item.effect == "light":
            self._illuminate_current_area()
            message = "The room is lit."
        else:
            message = "The wand has no visible effect."
        item.identified = True
        self._finish_turn()
        return self._result(True, message, True)

    def _trigger_trap(self, trap: TrapState) -> str:
        trap.discovered = True
        if trap.kind == TrapKind.TRAP_DOOR:
            message = "You fall through a trap door."
            if self.current_floor < MAX_FLOOR:
                self._descend_to_next_floor()
        elif trap.kind == TrapKind.BEAR:
            self.player.hp = max(0, self.player.hp - BEAR_TRAP_DAMAGE)
            message = "You are caught in a bear trap."
        elif trap.kind == TrapKind.POISON_DART:
            self.player.hp = max(0, self.player.hp - _roll(self.rng, (1, 4)))
            if not self.player.has_ring_effect("sustain"):
                self.player.strength = max(1, self.player.strength - 1)
            message = "A poisoned dart hits you."
        elif trap.kind == TrapKind.ARROW:
            self.player.hp = max(0, self.player.hp - 3)
            message = "An arrow shoots out at you."
        elif trap.kind == TrapKind.TELEPORT:
            self.player.position = self._free_position(self.floor, (self.player.position,))
            message = "You are suddenly teleported."
        elif trap.kind == TrapKind.SLEEPING_GAS:
            self.player.sleep_turns = max(self.player.sleep_turns, SLEEP_TURNS)
            message = "A strange gas surrounds you and you fall asleep."
        elif trap.kind == TrapKind.MYSTERIOUS:
            message = self.rng.choice(MYSTERIOUS_TRAP_MESSAGES)
        elif trap.kind == TrapKind.RUST:
            message = "Your armor is weakened by rust." if self._rust_armor() else "The rust vanishes from your armor."
        else:
            message = "Your armor is covered with rust."
        if self.player.hp == 0:
            self._die(trap.kind.value)
        return message

    def _reveal_nearby_traps(self) -> bool:
        found = False
        for trap in self.floor.traps:
            if max(abs(trap.x - self.player.x), abs(trap.y - self.player.y)) <= 1:
                trap.discovered = True
                found = True
        return found

    def search(self) -> CommandResult:
        """Search adjacent cells for undiscovered traps."""
        found = self._reveal_nearby_traps()
        self._finish_turn()
        return self._result(True, "You found a trap." if found else "You find nothing.", True)

    def identify_trap(self, direction: Position = (0, -1)) -> CommandResult:
        """Identify a trap in an adjacent cell without consuming a turn."""
        position = (self.player.x + direction[0], self.player.y + direction[1])
        trap = next((trap for trap in self.floor.traps if (trap.x, trap.y) == position), None)
        return self._result(bool(trap), trap.kind.value if trap else "There is no trap there.")

    def identify_item(self, value: Any = None) -> CommandResult:
        """Identify one unknown item in the pack."""
        item = (
            next((item for item in self.player.inventory if not item.identified), None)
            if value is None
            else self._find_item(value)
        )
        if not item:
            return self._result(False, "You have nothing new to identify.")
        item.identified = True
        return self._result(True, f"You identify the {item.name}.")

    def ascend(self) -> CommandResult:
        """Ascend one floor, or win when returning to the surface with the Amulet."""
        if self.player.position != self.floor.up_stairs:
            return self._result(False, "There are no stairs up here.")
        if self.current_floor == 1:
            if not self.player.has_amulet:
                return self._result(False, "You need the Amulet of Yendor to escape.")
            self.status = GameStatus.VICTORY
            return self._result(
                True,
                "You return to the surface with the Amulet of Yendor.",
                True,
                self.victory_summary,
            )
        self.floor.player_position = self.player.position
        old_floor = self.current_floor
        self.current_floor -= 1
        target = self._ensure_floor(self.current_floor)
        self.player.position = target.down_stairs or target.up_stairs or self._first_floor_position(target)
        self._message(f"You ascend to level {self.current_floor}.")
        self._finish_turn(process_monsters=False)
        if old_floor != self.current_floor + 1:
            raise RuntimeError
        return self._result(True, "", True)

    def descend(self) -> CommandResult:
        """Descend one floor when standing on the down stairs."""
        if self.player.position != self.floor.down_stairs:
            return self._result(False, "There are no stairs down here.")
        if self.current_floor >= MAX_FLOOR:
            return self._result(False, "You cannot go any deeper.")
        self._descend_to_next_floor()
        self._message(f"You descend to level {self.current_floor}.")
        self._finish_turn(process_monsters=False)
        return self._result(True, "", True)

    def status_text(self) -> str:
        """Return the compact status line used by CLI and GUI."""
        return f"Level {self.player.level}  HP {self.player.hp}/{self.player.max_hp}  Atk {self.player.attack}  AC {self.player.defense}  Food {self.player.food_units}  Gold {self.player.gold}"

    @property
    def score(self) -> int:
        """Return the current score."""
        return self.player.score()

    @property
    def death_summary(self) -> dict[str, Any]:
        """Return the values shown on the terminal death screen."""
        return {"score": self.score, "deepest_floor": self.player.deepest_floor, "cause": self.player.death_cause}

    @property
    def victory_summary(self) -> dict[str, int]:
        """Return the values shown on the terminal victory screen."""
        return {"score": self.score, "deepest_floor": self.player.deepest_floor}

    def _normalize_command(self, command: str) -> tuple[str, Any]:
        if command in self.COMMAND_KEYS:
            return self.COMMAND_KEYS[command]
        normalized = command.strip().lower()
        return self.COMMAND_KEYS.get(normalized, (normalized, None))

    def execute(self, command: str, args: Iterable[Any] = (), *, update_explored: bool = True) -> CommandResult:
        """Execute one command, optionally omitting automatic visibility recording for display-only callers."""
        previous_update = getattr(self, "_update_explored", True)
        self._update_explored = update_explored
        try:
            return self._execute(command, args)
        finally:
            self._update_explored = previous_update

    def _execute(self, command: str, args: Iterable[Any] = ()) -> CommandResult:  # noqa: PLR0911
        """Execute one canonical command and return its state transition."""
        args = list(args)
        if self.status != GameStatus.PLAYING:
            return self._result(False, "The game is over.")
        if self.player.sleep_turns > 0:
            self.player.sleep_turns -= 1
            self._finish_turn()
            return self._result(True, "You are still asleep.", True)
        if self.player.frozen_turns > 0:
            self._finish_turn()
            return self._result(True, "You are frozen.", True)
        command, key_value = self._normalize_command(command)
        if command == "move" and key_value is not None:
            return self.move(*key_value)
        command = COMMAND_ALIASES.get(command, command)
        direction = DIRECTIONS.get(command)
        if direction is not None:
            return self.move(*direction)
        if command == "move":
            if not args:
                return self._result(False, "Usage: move <north|south|east|west>")
            direction = DIRECTIONS.get(str(args[0]).lower())
            return self.move(*direction) if direction is not None else self._result(False, "Invalid direction.")
        if command == "wait":
            return self.wait()
        if command == "attack":
            return self.attack(self._direction(args[0]) if args else None)
        if command == "pickup":
            return self.pickup()
        if command == "drop":
            return self.drop(args[0] if args else None)
        if command == "eat":
            return self.eat(args[0] if args else None)
        if command == "quaff":
            return self.quaff(args[0] if args else None)
        if command == "read":
            return self.read(args[0] if args else None)
        equipment_kind = EQUIPMENT_KINDS.get(command)
        if equipment_kind is not None:
            return self.equip(args[0] if args else None, equipment_kind)
        unequipment_kind = UNEQUIPMENT_KINDS.get(command)
        if unequipment_kind is not None:
            return self.unequip(args[0] if args else None, unequipment_kind)
        if command == "throw":
            return self.throw(args[0] if args else None, self._direction(args[1]) if len(args) > 1 else (1, 0))
        if command == "zap":
            return self.zap(args[0] if args else None, self._direction(args[1]) if len(args) > 1 else (0, 0))
        if command == "search":
            return self.search()
        if command == "identify_trap":
            return self.identify_trap(self._direction(args[0]) if args else (0, -1))
        if command == "identify_item":
            return self.identify_item(args[0] if args else None)
        if command == "ascend":
            return self.ascend()
        if command == "descend":
            return self.descend()
        if command == "stairs":
            if not args or str(args[0]).lower() not in {"up", "u", "down", "d"}:
                return self._result(False, "Usage: stairs <up|down>")
            return self.ascend() if str(args[0]).lower() in {"up", "u"} else self.descend()
        if command == "use":
            item = self._find_item(args[0] if args else None)
            if not item:
                return self._result(False, "Usage: use <item>")
            action = USE_ACTIONS.get(item.kind)
            if action is None:
                return self._result(False, "That item cannot be used.")
            return self._execute(action, [item.id, *args[1:]])
        if command in {"inventory", "info", "character"}:
            if command != "inventory":
                return self._result(True, self.status_text())
            return self._result(
                True, ", ".join(item.display_name for item in self.player.inventory) or "Your pack is empty."
            )
        if command == "status":
            return self._result(True, self.status_text())
        if command == "help":
            return self._result(
                True,
                "hjkl yubn move, , pickup, d drop, e eat, q quaff, r read, w/W equip, t throw, z zap, s search, ^ trap, / identify, </> stairs, ? help",
            )
        if command == "save":
            return self._result(True, "Game state ready to save.", False, self.to_dict())
        if command == "quit":
            self.status = GameStatus.QUIT
            return self._result(True, "Goodbye.")
        return self._result(False, f"Unknown command: {command}")

    @staticmethod
    def _direction(value: Any) -> Position:
        return DIRECTIONS.get(str(value).lower(), (0, 0))

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete game state to JSON-compatible values."""
        return {
            "spec_version": GAME_VERSION,
            "seed": self.seed,
            "width": self.width,
            "height": self.height,
            "status": self.status.value,
            "current_floor": self.current_floor,
            "player": self.player.to_dict(),
            "floors": {str(number): floor.to_dict() for number, floor in self.floors.items()},
            "messages": self.messages[-100:],
            "rng_state": _jsonable(self.rng.getstate()),
            "next_ids": {"item": self._next_item_id, "monster": self._next_monster_id, "trap": self._next_trap_id},
            "appearances": {
                kind.value: [values[effect] for effect in APPEARANCE_EFFECTS[kind]]
                for kind, values in self._appearance_names.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameState:
        """Restore a game state after validating its specification version."""
        version = data.get("spec_version")
        if version != GAME_VERSION:
            raise SaveCompatibilityError(version)
        game = cls.__new__(cls)
        game.seed = int(data["seed"])
        game.width = int(data.get("width", DEFAULT_WIDTH))
        game.height = int(data.get("height", DEFAULT_HEIGHT))
        game.rng = random.Random(game.seed)  # noqa: S311 - deterministic, not cryptographic randomness
        game.generator = DungeonGenerator(game.width, game.height, game.rng)
        game.status = GameStatus(data.get("status", GameStatus.PLAYING))
        game.current_floor = int(data.get("current_floor", 1))
        game.player = PlayerState.from_dict(data["player"])
        game.floors = {int(number): FloorState.from_dict(floor) for number, floor in data.get("floors", {}).items()}
        game.messages = list(data.get("messages", []))
        game._next_item_id = int(data.get("next_ids", {}).get("item", 1))  # noqa: SLF001
        game._next_monster_id = int(data.get("next_ids", {}).get("monster", 1))  # noqa: SLF001
        game._next_trap_id = int(data.get("next_ids", {}).get("trap", 1))  # noqa: SLF001
        game._appearance_names = game._make_appearances()  # noqa: SLF001
        for raw_kind, values in data.get("appearances", {}).items():
            kind = ItemKind(raw_kind)
            game._appearance_names[kind].update(  # noqa: SLF001
                dict(zip(APPEARANCE_EFFECTS[kind], values, strict=False))
            )
        game.rng.setstate(_tupleize(data["rng_state"]))
        if game.current_floor not in game.floors:
            raise SaveCompatibilityError
        return game


RogueGame = GameState
ClassicGame = GameState


def _jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _tupleize(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_tupleize(item) for item in value)
    return value


__all__ = [
    "ARMOR_DATA",
    "DEFAULT_HEIGHT",
    "DEFAULT_WIDTH",
    "GAME_VERSION",
    "HUNGERTIME",
    "MAX_FLOOR",
    "MAX_PACK",
    "MAZE_FLOORS",
    "MONSTER_TYPES",
    "MORETIME",
    "STARVETIME",
    "STOMACHSIZE",
    "ClassicGame",
    "CombatResult",
    "CommandResult",
    "DisplayCell",
    "DungeonGenerator",
    "EntityKind",
    "FloorState",
    "GameState",
    "GameStatus",
    "ItemKind",
    "ItemState",
    "ItemType",
    "MonsterDefinition",
    "MonsterState",
    "Position",
    "RogueGame",
    "Room",
    "SaveCompatibilityError",
    "Terrain",
    "TileKind",
    "TrapKind",
    "TrapState",
]
