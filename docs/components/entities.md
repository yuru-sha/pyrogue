# Entities コンポーネント

PyRogueのゲームエンティティシステム。プレイヤー、モンスター、アイテム、魔法、トラップを統合管理し、オリジナルRogueの忠実な再現を実現します。

## 概要

`src/pyrogue/entities/`は、PyRogueの心臓部となるゲームエンティティシステムです。オリジナルRogueの26階層構造を忠実に再現し、現代的なソフトウェア設計パターンにより高い拡張性と保守性を実現しています。

## アーキテクチャ

### ディレクトリ構成

```
entities/
├── __init__.py
├── actors/                    # アクターシステム
│   ├── actor.py              # Actor基底クラス
│   ├── player.py             # プレイヤーシステム
│   ├── monster.py            # モンスターシステム
│   ├── inventory.py          # インベントリ管理
│   ├── status_effects.py     # 状態異常システム
│   └── npc.py               # NPCシステム（現在無効化）
├── items/                     # アイテムシステム
│   ├── item.py              # 基本アイテムクラス
│   ├── identification.py    # アイテム識別システム
│   ├── cursed_items.py      # 呪われたアイテム
│   ├── effects.py           # アイテム効果システム
│   └── item_spawner.py      # アイテム生成システム
├── magic/                     # 魔法システム
│   └── spells.py            # 呪文実装
└── traps/                     # トラップシステム
    └── trap.py              # トラップ実装
```

### 設計原則

- **継承ベース設計**: Actor基底クラスによる共通機能の提供
- **Command Pattern**: 状態異常・魔法・アイテム効果の統一実行
- **Strategy Pattern**: モンスターAI・魔法効果・トラップ動作の動的切り替え
- **オリジナル忠実性**: Rogue本来のゲームメカニクスの厳密な再現
- **Handler Pattern連携**: v0.1.0のHandler Patternとのシームレスな統合

## アクターシステム (actors/)

### Actor基底クラス

全アクター（Player、Monster、NPC）の共通基盤を提供。

```python
class Actor(ABC):
    """ゲーム内アクターの抽象基底クラス"""

    def __init__(self, char: str, color: tuple[int, int, int],
                 name: str, x: int = 0, y: int = 0):
        self.char = char
        self.color = color
        self.name = name
        self.x, self.y = x, y
        self.hp = self.max_hp = 30
        self.attack = 1
        self.defense = 0

    @abstractmethod
    def update_status_effects(self, context) -> None:
        """状態異常のターン経過処理"""

    @abstractmethod
    def has_status_effect(self, name: str) -> bool:
        """指定状態異常の保持判定"""
```

### Player クラス

ゲームの主人公となるプレイヤーシステム。

**統合機能:**
- **満腹度システム**: 戦闘能力に影響する飢餓管理
- **スコアシステム**: 詳細なゲーム記録管理
- **装備システム**: 動的な攻撃力・防御力計算
- **Light効果**: 一時的な視界拡張

```python
def get_attack(self) -> int:
    """装備ボーナスと飢餓ペナルティを含む総攻撃力"""
    base_attack = self.attack
    equipment_bonus = self.inventory.get_attack_bonus()
    hunger_penalty = self.get_hunger_attack_penalty()
    total_attack = base_attack + equipment_bonus - hunger_penalty
    return max(1, total_attack)  # 最低1の攻撃力保証

def get_hunger_attack_penalty(self) -> int:
    """満腹度による攻撃力ペナルティ"""
    if self.hunger_state == HungerState.WEAK:
        return 1
    elif self.hunger_state == HungerState.FAINT:
        return 2
    return 0
```

**満腹度管理:**
```python
class HungerState(Enum):
    SATISFIED = "Satisfied"    # 満腹
    HUNGRY = "Hungry"         # 空腹
    WEAK = "Weak"             # 衰弱（攻撃力-1）
    FAINT = "Faint"           # 瀕死（攻撃力-2）
```

### Monster クラス

多様なAIパターンを持つモンスターシステム。

**AIパターン:**
```python
# 基本AI
"basic": 標準的な追跡・攻撃行動
"thief": アイテム盗取能力
"drain": レベルドレイン攻撃
"split": 攻撃時分裂
"ranged": 遠距離攻撃
"flee": 逃走行動（HP30%以下）
```

**特殊能力実装:**
```python
def can_steal_items(self) -> bool:
    """アイテム盗取能力判定"""
    return self.ai_pattern in ["item_thief", "leprechaun"]

def can_steal_gold(self) -> bool:
    """金貨盗取能力判定"""
    return self.ai_pattern in ["gold_thief", "nymph"]

def can_drain_level(self) -> bool:
    """レベルドレイン能力判定"""
    return self.ai_pattern in ["level_drain", "wraith"]

def can_split(self) -> bool:
    """分裂能力判定"""
    return self.ai_pattern in ["split", "split_on_hit"]
```

### Inventory システム

オリジナルRogue準拠の26アイテム制限インベントリシステム。

**主要機能:**
- **容量制限**: 26アイテム（a-z文字対応）
- **装備管理**: weapon、armor、ring_left、ring_right
- **呪い対応**: 呪われたアイテムの装備解除制限
- **統計計算**: 装備による攻撃力・防御力ボーナス

```python
def add_item(self, item: "Item") -> bool:
    """アイテム追加（スタック処理含む）"""
    if self.is_full() and not self._can_stack_with_existing(item):
        return False

    # スタック可能アイテムの統合
    for existing_item in self.items:
        if existing_item.can_stack_with(item):
            existing_item.stack_count += item.stack_count
            return True

    self.items.append(item)
    return True

def get_attack_bonus(self) -> int:
    """装備による攻撃力ボーナス"""
    bonus = 0
    if self.weapon:
        bonus += self.weapon.enchantment
    if self.ring_left and hasattr(self.ring_left, 'attack_bonus'):
        bonus += self.ring_left.attack_bonus
    if self.ring_right and hasattr(self.ring_right, 'attack_bonus'):
        bonus += self.ring_right.attack_bonus
    return bonus
```

### StatusEffects システム

Command Patternによる統一的な状態異常管理。

**状態異常基底クラス:**
```python
class StatusEffect(ABC):
    """状態異常の抽象基底クラス"""

    def __init__(self, duration: int):
        self.duration = duration
        self.permanent = False

    @abstractmethod
    def apply_per_turn(self, context: EffectContext) -> bool:
        """ターンごとの効果適用。継続時False返却"""

    def update_duration(self) -> bool:
        """持続時間更新。継続時True返却"""
        if self.permanent:
            return True
        self.duration -= 1
        return self.duration > 0
```

**実装済み状態異常:**

```python
class PoisonEffect(StatusEffect):
    """毒状態異常（防御力無視ダメージ）"""
    def apply_per_turn(self, context: EffectContext) -> bool:
        context.player.hp = max(0, context.player.hp - self.damage)
        context.message_log.add_message("You feel sick from poison!", color.RED)
        return self.update_duration()

class ParalysisEffect(StatusEffect):
    """麻痺状態異常（行動阻害）"""
    def apply_per_turn(self, context: EffectContext) -> bool:
        context.message_log.add_message("You are paralyzed!", color.YELLOW)
        # 行動制限は呼び出し側で判定
        return self.update_duration()

class ConfusionEffect(StatusEffect):
    """混乱状態異常（行動ランダム化）"""
    def apply_per_turn(self, context: EffectContext) -> bool:
        context.message_log.add_message("You feel confused!", color.MAGENTA)
        # 移動方向のランダム化は移動処理側で実装
        return self.update_duration()

class HallucinationEffect(StatusEffect):
    """幻覚状態異常（視覚混乱）"""
    def apply_per_turn(self, context: EffectContext) -> bool:
        context.message_log.add_message("You see strange things!", color.MAGENTA)
        # レンダリング時のランダム表示は描画処理側で実装
        return self.update_duration()
```

## アイテムシステム (items/)

### アイテム識別システム

オリジナルRogue風の段階的識別システム。

**未識別名の生成:**
```python
def _initialize_appearances(self) -> None:
    """未識別名をランダムに割り当て"""
    potion_colors = [
        "red", "blue", "green", "yellow", "black", "brown",
        "clear", "pink", "white", "purple"
    ]
    scroll_labels = [
        'scroll labeled "ZELGO MER"',
        'scroll labeled "JUYED AWK YACC"',
        'scroll labeled "NR 9"',
        'scroll labeled "XIXAXA XOXAXA XUXAXA"'
    ]
    ring_materials = [
        "wooden", "granite", "opal", "clay", "coral", "black",
        "moonstone", "silver", "tiger eye", "jade", "obsidian"
    ]
```

**識別メカニズム:**
```python
def identify_item(self, item: "Item") -> None:
    """アイテムの識別"""
    item_key = self._get_item_key(item)
    if item_key not in self.identified_items:
        self.identified_items.add(item_key)

        # 同種アイテムの一括識別
        if hasattr(item, 'item_type'):
            subtype_key = f"{item.item_type}_{item.subtype}"
            self.identified_subtypes.add(subtype_key)

def is_identified(self, item: "Item") -> bool:
    """アイテムの識別状態確認"""
    item_key = self._get_item_key(item)
    return item_key in self.identified_items
```

### アイテム効果システム

Strategy Patternによる統一的な効果処理。

**効果基底クラス:**
```python
class Effect(ABC):
    """アイテム効果の抽象基底クラス"""

    @abstractmethod
    def apply(self, context: EffectContext) -> bool:
        """効果適用。成功時True返却"""

class InstantEffect(Effect):
    """即座に発動する効果"""
    pass

class DelayedEffect(Effect):
    """遅延発動する効果"""
    pass
```

**主要効果実装:**

```python
class HealingEffect(InstantEffect):
    """HP回復効果"""
    def apply(self, context: EffectContext) -> bool:
        player = context.player
        old_hp = player.hp
        player.heal(self.heal_amount)
        actual_heal = player.hp - old_hp

        if actual_heal > 0:
            context.message_log.add_message(
                f"You feel better! (+{actual_heal} HP)", color.GREEN
            )
            return True
        return False

class TeleportEffect(InstantEffect):
    """ランダムテレポート効果"""
    def apply(self, context: EffectContext) -> bool:
        player = context.player
        dungeon = context.dungeon

        # ランダム位置の探索
        for _ in range(100):
            new_x = random.randint(1, dungeon.width - 2)
            new_y = random.randint(1, dungeon.height - 2)

            if dungeon.is_passable(new_x, new_y):
                player.x, player.y = new_x, new_y
                context.message_log.add_message(
                    "You feel disoriented!", color.MAGENTA
                )
                return True
        return False

class IdentifyEffect(InstantEffect):
    """アイテム識別効果"""
    def apply(self, context: EffectContext) -> bool:
        identification_system = context.player.inventory.identification_system
        unidentified_items = [
            item for item in context.player.inventory.items
            if not identification_system.is_identified(item)
        ]

        if unidentified_items:
            # ランダムなアイテムを識別
            item_to_identify = random.choice(unidentified_items)
            identification_system.identify_item(item_to_identify)
            context.message_log.add_message(
                f"This is a {item_to_identify.name}!", color.YELLOW
            )
            return True
        return False
```

### 呪いアイテムシステム

オリジナルRogue準拠の呪いメカニズム。

```python
class CursedItemManager:
    """呪いアイテムの管理"""

    def apply_curse(self, item: "Item") -> None:
        """アイテムに呪いを適用"""
        item.cursed = True
        item.color = color.PURPLE  # 視覚的な呪い表示

        # 能力値の悪化
        if hasattr(item, 'enchantment'):
            item.enchantment = min(item.enchantment, -1)

    def can_unequip(self, item: "Item") -> bool:
        """装備解除可能性の判定"""
        return not item.cursed

    def generate_cursed_item(self, item_type: str) -> "Item":
        """呪われたアイテムの生成"""
        item = self._create_base_item(item_type)
        self.apply_curse(item)
        return item
```

## 魔法システム (magic/)

### Spellbook システム

MP消費による魔法詠唱システム。

```python
class Spell(ABC):
    """魔法の抽象基底クラス"""

    def __init__(self, name: str, mp_cost: int, spell_range: int = 0):
        self.name = name
        self.mp_cost = mp_cost
        self.spell_range = spell_range

    @abstractmethod
    def cast(self, context: EffectContext, **kwargs: Any) -> bool:
        """魔法詠唱と効果発動"""

class MagicMissile(Spell):
    """確実命中の魔法攻撃"""
    def cast(self, context: EffectContext,
             target_pos: tuple[int, int] | None = None) -> bool:
        player = context.player
        dungeon = context.dungeon

        if not target_pos:
            return False

        # 射程判定
        distance = max(abs(target_pos[0] - player.x),
                      abs(target_pos[1] - player.y))
        if distance > player.light_radius:
            context.message_log.add_message(
                "Target is too far away!", color.RED
            )
            return False

        # ターゲット検索
        monster = dungeon.get_monster_at(*target_pos)
        if monster:
            # 防御力無視ダメージ
            monster.hp = max(0, monster.hp - self.damage)
            context.message_log.add_message(
                f"Magic missile hits {monster.name}!", color.CYAN
            )
            return True
        return False

class Heal(Spell):
    """HP回復魔法"""
    def cast(self, context: EffectContext, **kwargs: Any) -> bool:
        player = context.player
        old_hp = player.hp
        player.heal(self.heal_amount)
        actual_heal = player.hp - old_hp

        if actual_heal > 0:
            context.message_log.add_message(
                f"You feel much better! (+{actual_heal} HP)", color.GREEN
            )
            return True
        return False
```

## トラップシステム (traps/)

### Trap システム

隠蔽・発見・解除メカニズムを持つトラップシステム。

```python
class Trap(ABC):
    """トラップの抽象基底クラス"""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.discovered = False
        self.disarmed = False

    @abstractmethod
    def activate(self, context: EffectContext) -> None:
        """トラップ発動"""

    def attempt_disarm(self, context: EffectContext) -> bool:
        """解除試行（成功率70%）"""
        if random.random() < 0.7:
            self.disarmed = True
            context.message_log.add_message(
                "You successfully disarm the trap!", color.GREEN
            )
            return True
        else:
            context.message_log.add_message(
                "You failed to disarm the trap and trigger it!", color.RED
            )
            self.activate(context)  # 解除失敗時の誤発動
            return False

class PoisonNeedleTrap(Trap):
    """毒針トラップ"""
    def activate(self, context: EffectContext) -> None:
        context.message_log.add_message(
            "A poison needle pricks you!", color.RED
        )

        poison_effect = PoisonEffect(
            duration=self.poison_duration,
            damage=2
        )
        context.player.status_effects.add_effect(poison_effect)

class TeleportTrap(Trap):
    """転移トラップ"""
    def activate(self, context: EffectContext) -> None:
        teleport_effect = TeleportEffect()
        if teleport_effect.apply(context):
            context.message_log.add_message(
                "You are teleported away!", color.MAGENTA
            )
```

## エンティティ間連携

### EffectContext プロトコル

エンティティ間の統一インターフェース。

```python
class EffectContext(Protocol):
    """効果実行時の共有コンテキスト"""

    @property
    def player(self) -> "Player": ...

    @property
    def dungeon(self) -> "Dungeon": ...

    @property
    def message_log(self) -> "MessageLog": ...

    @property
    def game_screen(self) -> "GameScreen": ...
```

### 状態異常の統合管理

```python
def update_status_effects(self, context: EffectContext) -> None:
    """全アクター共通の状態異常更新"""
    effects_to_remove = []

    for effect in self.status_effects.effects:
        if not effect.apply_per_turn(context):
            effects_to_remove.append(effect)

    for effect in effects_to_remove:
        self.status_effects.remove_effect(effect)
```

## オリジナルRogueとの忠実性

### アイテム容量制限

```python
MAX_INVENTORY_SIZE = 26  # a-z文字に対応

def get_item_letter(self, index: int) -> str:
    """インベントリスロットの文字取得"""
    if 0 <= index < 26:
        return chr(ord('a') + index)
    return '?'
```

### モンスター出現テーブル

```python
FLOOR_MONSTERS: dict[int, list[tuple[str, int]]] = {
    1: [("BAT", 50), ("RATTLESNAKE", 50)],
    2: [("JACKAL", 40), ("ICE_MONSTER", 40), ("CENTIPEDE", 20)],
    15: [("DRAGON", 40), ("JABBERWOCK", 60)],
    26: [("DRAGON", 100)]  # 最終階層
}
```

### 装備制限システム

```python
# オリジナルRogue準拠の装備スロット
equipment_slots = {
    "weapon": 1,      # 武器1つ
    "armor": 1,       # 防具1つ
    "ring_left": 1,   # 左手指輪
    "ring_right": 1   # 右手指輪
}
```

## 使用パターン

### プレイヤーの初期化

```python
from pyrogue.entities.actors.player import Player
from pyrogue.entities.actors.inventory import Inventory

# プレイヤー作成
player = Player(x=10, y=10)
player.inventory = Inventory()

# 初期装備の設定
starter_sword = Item("Short Sword", item_type="weapon")
player.inventory.add_item(starter_sword)
player.inventory.equip_item(starter_sword)
```

### モンスター生成

```python
from pyrogue.entities.actors.monster import Monster

# モンスター生成
orc = Monster.create_monster("ORC", x=15, y=15)
orc.ai_pattern = "basic"

# 特殊モンスター
thief = Monster.create_monster("NYMPH", x=20, y=20)
thief.ai_pattern = "item_thief"
```

### アイテム使用

```python
# ポーション使用
healing_potion = Item("Healing Potion", item_type="potion")
healing_effect = HealingEffect(heal_amount=20)
healing_potion.effects = [healing_effect]

# 効果適用
if healing_effect.apply(effect_context):
    player.inventory.remove_item(healing_potion)
```

### 魔法詠唱

```python
from pyrogue.entities.magic.spells import MagicMissile

# 魔法習得
magic_missile = MagicMissile(damage=15)
player.spells.add(magic_missile)

# 詠唱実行
if player.mp >= magic_missile.mp_cost:
    if magic_missile.cast(effect_context, target_pos=(enemy_x, enemy_y)):
        player.mp -= magic_missile.mp_cost
```

## 拡張ガイド

### 新しいモンスターの追加

```python
# 1. モンスター統計の定義
MONSTER_STATS["NEW_MONSTER"] = {
    "name": "New Monster",
    "char": "N",
    "color": color.ORANGE,
    "hp": 50,
    "attack": 8,
    "defense": 3,
    "ai_pattern": "special"
}

# 2. AI行動の実装
def execute_special_ai(self, context: EffectContext) -> None:
    """特殊AI行動"""
    # カスタムAI実装
    pass
```

### 新しい状態異常の追加

```python
class FreezeEffect(StatusEffect):
    """凍結状態異常"""
    def apply_per_turn(self, context: EffectContext) -> bool:
        context.message_log.add_message(
            "You are frozen solid!", color.CYAN
        )
        # 移動・攻撃阻害（呼び出し側で判定）
        return self.update_duration()
```

### 新しい魔法の追加

```python
class Fireball(Spell):
    """火球魔法（範囲攻撃）"""
    def cast(self, context: EffectContext,
             target_pos: tuple[int, int] | None = None) -> bool:
        # 範囲内の全敵にダメージ
        center_x, center_y = target_pos

        for monster in context.dungeon.monsters:
            distance = max(abs(monster.x - center_x),
                          abs(monster.y - center_y))
            if distance <= self.explosion_radius:
                monster.hp = max(0, monster.hp - self.damage)

        return True
```

## パフォーマンス最適化

### 状態異常処理の最適化

```python
# 効果的でない状態異常の早期除去
def cleanup_expired_effects(self) -> None:
    """期限切れ効果の削除"""
    self.effects = [
        effect for effect in self.effects
        if effect.duration > 0 or effect.permanent
    ]
```

### アイテム検索の最適化

```python
# インデックスベースの高速検索
def find_items_by_type(self, item_type: str) -> list["Item"]:
    """タイプ別アイテム検索"""
    return [item for item in self.items if item.item_type == item_type]
```

## Handler Pattern連携（v0.1.0）

### エンティティシステムとHandler Patternの統合

v0.1.0で導入されたHandler Patternとエンティティシステムは密接に連携し、以下の統合された処理を実現しています：

#### アイテム管理の統合

```python
class InfoCommandHandler:
    def handle_item_info(self, item_letter: str) -> CommandResult:
        """アイテム情報表示（エンティティシステム連携）"""
        inventory = self.context.game_context.player.inventory

        try:
            item_index = ord(item_letter.lower()) - ord('a')
            if 0 <= item_index < len(inventory.items):
                item = inventory.items[item_index]
                # アイテム識別システムとの連携
                if inventory.identification_system.is_identified(item):
                    info_msg = f"{item.name}: {item.get_description()}"
                else:
                    info_msg = f"{item.unidentified_name}: Unknown item"

                self.context.add_message(info_msg)
                return CommandResult.success()

        except (ValueError, IndexError):
            return CommandResult.failure("Invalid item letter")
```

#### デバッグコマンドとエンティティ制御

```python
class DebugCommandHandler:
    def handle_spawn_monster(self, args: list[str]) -> CommandResult:
        """モンスター生成（デバッグ）"""
        if not args:
            return CommandResult.failure("Monster type required")

        monster_type = args[0].upper()
        player = self.context.game_context.player
        dungeon = self.context.game_context.dungeon_manager.current_dungeon

        # エンティティシステムを使ったモンスター生成
        monster = Monster.create_monster(monster_type, x=player.x+1, y=player.y+1)
        if monster:
            dungeon.monsters.append(monster)
            self.context.add_message(f"Spawned {monster.name}")
            return CommandResult.success_with_turn()

        return CommandResult.failure(f"Unknown monster type: {monster_type}")

    def handle_grant_item(self, args: list[str]) -> CommandResult:
        """アイテム付与（デバッグ）"""
        if not args:
            return CommandResult.failure("Item type required")

        item_type = args[0].lower()
        player = self.context.game_context.player

        # エンティティシステムを使ったアイテム生成
        from pyrogue.entities.items.item_spawner import ItemSpawner
        spawner = ItemSpawner()
        item = spawner.create_item(item_type)

        if item and player.inventory.add_item(item):
            self.context.add_message(f"Added {item.name} to inventory")
            return CommandResult.success()

        return CommandResult.failure("Failed to add item")
```

#### セーブ・ロードでのエンティティ状態管理

```python
class SaveLoadHandler:
    def _save_entity_states(self, game_context: GameContext) -> dict:
        """エンティティ状態の保存"""
        return {
            'player': self._serialize_player(game_context.player),
            'monsters': [self._serialize_monster(m) for m in game_context.dungeon_manager.current_dungeon.monsters],
            'items': [self._serialize_item(i) for i in game_context.dungeon_manager.current_dungeon.items],
            'status_effects': self._serialize_status_effects(game_context.player.status_effects)
        }

    def _serialize_player(self, player: Player) -> dict:
        """プレイヤー状態のシリアライズ"""
        return {
            'x': player.x, 'y': player.y,
            'hp': player.hp, 'max_hp': player.max_hp,
            'mp': player.mp, 'max_mp': player.max_mp,
            'level': player.level, 'experience': player.experience,
            'hunger_state': player.hunger_state.value,
            'inventory': self._serialize_inventory(player.inventory),
            'status_effects': [effect.to_dict() for effect in player.status_effects.effects]
        }
```

#### 自動探索とエンティティ検出

```python
class AutoExploreHandler:
    def _check_safety(self) -> bool:
        """安全性確認（エンティティ検出）"""
        player = self.context.game_context.player
        dungeon = self.context.game_context.dungeon_manager.current_dungeon

        # モンスター検出
        for monster in dungeon.monsters:
            distance = max(abs(monster.x - player.x), abs(monster.y - player.y))
            if distance <= player.light_radius:
                self.context.add_message(f"You see a {monster.name} nearby!")
                return False

        # トラップ検出
        for trap in dungeon.traps:
            if (trap.x, trap.y) == (player.x, player.y) and not trap.discovered:
                # トラップ発見ロジック
                if random.random() < 0.3:  # 30%の確率で発見
                    trap.discovered = True
                    self.context.add_message("You discovered a trap!")
                    return False

        return True
```

## まとめ

Entities コンポーネントは、PyRogueプロジェクトの中核として以下の価値を提供します：

- **オリジナル忠実性**: Rogueの本質的なゲームメカニクスの厳密な再現
- **現代的設計**: デザインパターンによる高い拡張性と保守性
- **統合管理**: 状態異常・効果・AIの統一的な処理システム
- **型安全性**: Protocol使用による堅牢な型システム
- **テスト対応**: 依存性注入によるテスタビリティ
- **Handler Pattern統合**: v0.1.0のHandler Patternとの完全な連携

この設計により、26階層の本格的なローグライクゲームとして、オリジナルRogueの魅力を現代的な技術で蘇らせることに成功しています。エンティティシステムは、ゲームの核心的な楽しさを支える重要な基盤として機能しています。
