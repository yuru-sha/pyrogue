# UI コンポーネント

PyRogueのユーザーインターフェースシステム。画面管理、描画処理、入力制御を統合し、直感的で応答性の高いゲーム体験を提供します。

## 概要

`src/pyrogue/ui/`は、PyRogueのフロントエンドを担当するユーザーインターフェースシステムです。TCODライブラリとの効率的な統合により、文字ベースながら高度な描画機能と包括的な入力処理を実現しています。

## アーキテクチャ

### ディレクトリ構成

```
ui/
├── __init__.py
├── screens/                    # 画面システム
│   ├── __init__.py
│   ├── screen.py              # Screen基底クラス
│   ├── menu_screen.py         # メニュー画面
│   ├── game_screen.py         # メインゲーム画面
│   ├── inventory_screen.py    # インベントリ画面
│   ├── magic_screen.py        # 魔法画面
│   ├── game_over_screen.py    # ゲームオーバー画面
│   └── victory_screen.py      # 勝利画面
└── components/                 # UIコンポーネント
    ├── __init__.py
    ├── game_renderer.py       # 描画処理
    ├── input_handler.py       # 入力処理
    ├── fov_manager.py         # 視界管理
    └── save_load_manager.py   # セーブ・ロード管理
```

### 設計原則

- **状態駆動設計**: GameStatesによる明確な画面状態管理
- **責務分離**: Screen基底クラス + 専門UIコンポーネント
- **レスポンシブ対応**: 動的ウィンドウリサイズへの適応
- **包括的入力**: 3種類の入力方式の統一サポート

## 画面システム (screens/)

### Screen基底クラス

全画面の共通インターフェースを定義。

```python
class Screen(ABC):
    """画面の抽象基底クラス"""

    @abstractmethod
    def render(self, root_console: tcod.Console,
               game_context: GameContext) -> None:
        """画面のレンダリング"""
        pass

    @abstractmethod
    def handle_key(self, key: tcod.event.KeyDown,
                   game_context: GameContext) -> Optional[Action]:
        """キー入力の処理"""
        pass
```

**設計思想:**
- 最小限のインターフェース（render + handle_key）
- 共通処理の抽象化
- 画面固有ロジックの分離

### MenuScreen (メニュー画面)

ゲーム開始時のメイン画面。

```python
class MenuScreen(Screen):
    """メインメニュー画面"""

    def render(self, root_console: tcod.Console,
               game_context: GameContext) -> None:
        """メニューのレンダリング"""
        # タイトル表示
        tcod.console_print(root_console,
                          x=center_x, y=5,
                          string="PYROGUE",
                          fg=color.YELLOW)

        # メニューオプション
        menu_options = [
            "1. New Game",
            "2. Load Game",
            "3. Quit"
        ]

        for i, option in enumerate(menu_options):
            tcod.console_print(root_console,
                              x=center_x, y=10 + i * 2,
                              string=option,
                              fg=color.WHITE)
```

### GameScreen (メインゲーム画面)

ゲームプレイ中心の画面システム。

**主要機能:**
- **レイヤー化描画**: マップ→オブジェクト→UI→メッセージ
- **動的レスポンス**: ウィンドウサイズ変更への適応
- **状態表示**: プレイヤーステータス、ミニマップ等

```python
class GameScreen(Screen):
    """メインゲーム画面"""

    def render(self, root_console: tcod.Console,
               game_context: GameContext) -> None:
        """ゲーム画面のレンダリング"""
        # 1. マップ描画
        self.game_renderer.render_dungeon(root_console, game_context)

        # 2. オブジェクト描画
        self.game_renderer.render_entities(root_console, game_context)

        # 3. UI要素描画
        self.game_renderer.render_status_bar(root_console, game_context)

        # 4. メッセージログ描画
        self.game_renderer.render_message_log(root_console, game_context)

    def handle_key(self, key: tcod.event.KeyDown,
                   game_context: GameContext) -> Optional[Action]:
        """ゲーム中の入力処理"""
        return self.input_handler.handle_game_input(key, game_context)
```

### InventoryScreen (インベントリ画面)

アイテム管理画面システム。

**特徴:**
- **26アイテム制限**: a-z文字による選択システム
- **装備状態表示**: 装備中アイテムの視覚的識別
- **呪い表示**: 呪われたアイテムの警告表示
- **ヘルプ機能**: ?キーによる操作説明切り替え

```python
class InventoryScreen(Screen):
    """インベントリ管理画面"""

    def render(self, root_console: tcod.Console,
               game_context: GameContext) -> None:
        """インベントリのレンダリング"""
        inventory = game_context.player.inventory

        # タイトル表示
        tcod.console_print(root_console, 2, 1, "Inventory", color.YELLOW)

        # アイテムリスト表示
        for i, item in enumerate(inventory.items):
            item_letter = chr(ord('a') + i)
            item_color = self._get_item_color(item, inventory)

            # 装備状態の表示
            equipped_marker = self._get_equipped_marker(item, inventory)

            tcod.console_print(
                root_console, 2, 3 + i,
                f"{item_letter}) {equipped_marker}{item.name}",
                item_color
            )

    def _get_item_color(self, item: Item, inventory: Inventory) -> tuple[int, int, int]:
        """アイテム色の決定"""
        if item.cursed:
            return color.PURPLE  # 呪われたアイテム
        elif inventory.is_equipped(item):
            return color.GREEN   # 装備中アイテム
        else:
            return color.WHITE   # 通常アイテム

    def _get_equipped_marker(self, item: Item, inventory: Inventory) -> str:
        """装備マーカーの取得"""
        if inventory.weapon == item:
            return "(weapon) "
        elif inventory.armor == item:
            return "(armor) "
        elif inventory.ring_left == item or inventory.ring_right == item:
            return "(ring) "
        return ""
```

### MagicScreen (魔法画面)

呪文詠唱とターゲット選択画面。

**機能:**
- **呪文リスト**: 習得済み魔法の一覧表示
- **MP表示**: 現在MP/最大MPの状態表示
- **ターゲット選択**: 攻撃魔法のターゲット指定モード
- **射程表示**: 魔法射程の視覚的表示

```python
class MagicScreen(Screen):
    """魔法詠唱画面"""

    def render(self, root_console: tcod.Console,
               game_context: GameContext) -> None:
        """魔法画面のレンダリング"""
        player = game_context.player

        # MP状態表示
        tcod.console_print(
            root_console, 2, 1,
            f"MP: {player.mp}/{player.max_mp}",
            color.CYAN
        )

        # 呪文リスト表示
        for i, spell in enumerate(player.spells):
            spell_letter = chr(ord('a') + i)
            spell_color = color.WHITE if player.mp >= spell.mp_cost else color.GRAY

            tcod.console_print(
                root_console, 2, 3 + i,
                f"{spell_letter}) {spell.name} (MP:{spell.mp_cost})",
                spell_color
            )
```

## UIコンポーネント (components/)

### GameRenderer (描画処理)

レイヤー化された描画システム。

```python
class GameRenderer:
    """ゲーム描画の統合管理"""

    def render_dungeon(self, console: tcod.Console,
                      game_context: GameContext) -> None:
        """ダンジョンマップの描画"""
        player = game_context.player
        dungeon = game_context.dungeon_manager.get_current_floor_data()

        # 視界範囲の計算
        fov = self.fov_manager.calculate_fov(
            dungeon.tiles, player.x, player.y, player.light_radius
        )

        # タイル描画
        for y in range(len(dungeon.tiles)):
            for x in range(len(dungeon.tiles[0])):
                tile = dungeon.tiles[y][x]

                if fov[y][x]:  # 視界内
                    tile.discovered = True
                    tcod.console_set_char_background(
                        console, x, y, tile.color, tcod.BKGND_SET
                    )
                    tcod.console_set_char(console, x, y, tile.char)
                elif tile.discovered:  # 記憶している場所
                    # 暗い色で表示
                    dark_color = tuple(c // 3 for c in tile.color)
                    tcod.console_set_char_background(
                        console, x, y, dark_color, tcod.BKGND_SET
                    )
                    tcod.console_set_char(console, x, y, tile.char)

    def render_entities(self, console: tcod.Console,
                       game_context: GameContext) -> None:
        """エンティティ（プレイヤー、モンスター、アイテム）の描画"""
        dungeon = game_context.dungeon_manager.get_current_floor_data()
        fov = self.fov_manager.get_current_fov()

        # アイテム描画
        for item in dungeon.items:
            if fov[item.y][item.x]:
                tcod.console_set_char(console, item.x, item.y, item.char)
                tcod.console_set_char_foreground(console, item.x, item.y, item.color)

        # モンスター描画
        for monster in dungeon.monsters:
            if fov[monster.y][monster.x]:
                # 幻覚状態での描画変更
                if game_context.player.has_status_effect("hallucination"):
                    char, color = self._get_hallucination_appearance()
                else:
                    char, color = monster.char, monster.color

                tcod.console_set_char(console, monster.x, monster.y, char)
                tcod.console_set_char_foreground(console, monster.x, monster.y, color)

        # プレイヤー描画
        player = game_context.player
        tcod.console_set_char(console, player.x, player.y, player.char)
        tcod.console_set_char_foreground(console, player.x, player.y, player.color)

    def render_status_bar(self, console: tcod.Console,
                         game_context: GameContext) -> None:
        """ステータスバーの描画"""
        player = game_context.player

        # ヘルスバー
        self._render_bar(
            console, 1, console.height - 5,
            "HP", player.hp, player.max_hp,
            color.RED, color.DARK_RED
        )

        # MPバー
        self._render_bar(
            console, 1, console.height - 4,
            "MP", player.mp, player.max_mp,
            color.BLUE, color.DARK_BLUE
        )

        # レベル・経験値表示
        tcod.console_print(
            console, 1, console.height - 3,
            f"Level: {player.level} XP: {player.experience}/{player.experience_to_next_level}",
            color.WHITE
        )

        # 現在階層表示
        current_floor = game_context.dungeon_manager.current_floor
        tcod.console_print(
            console, 1, console.height - 2,
            f"Floor: {current_floor}",
            color.YELLOW
        )
```

### InputHandler (入力処理)

包括的な入力処理システム。

**サポート入力方式:**
- **Vi-keys**: hjkl + 対角線移動 (yubn)
- **矢印キー**: 標準的な方向移動
- **テンキー**: 1-9による移動（対角線含む）

```python
class InputHandler:
    """統合入力処理システム"""

    def __init__(self):
        self.state_manager = StateManager()

    def handle_game_input(self, key: tcod.event.KeyDown,
                         game_context: GameContext) -> Optional[Action]:
        """ゲーム中の入力処理"""
        current_state = game_context.game_state

        # 状態別処理の委譲
        if current_state == GameStates.PLAYERS_TURN:
            return self._handle_player_turn(key, game_context)
        elif current_state == GameStates.SHOW_INVENTORY:
            return self._handle_inventory_input(key, game_context)
        elif current_state == GameStates.TARGETING:
            return self._handle_targeting_input(key, game_context)
        # ... 他の状態処理

    def _handle_player_turn(self, key: tcod.event.KeyDown,
                           game_context: GameContext) -> Optional[Action]:
        """プレイヤーターンの入力処理"""
        # 移動コマンド
        move_action = self._parse_movement_key(key)
        if move_action:
            return move_action

        # アクションコマンド
        if key.sym == tcod.event.K_g:
            return GetItemAction()
        elif key.sym == tcod.event.K_i:
            return ShowInventoryAction()
        elif key.sym == tcod.event.K_z:
            return ShowMagicAction()
        elif key.sym == tcod.event.K_o:
            return OpenDoorAction()
        elif key.sym == tcod.event.K_c:
            return CloseDoorAction()
        elif key.sym == tcod.event.K_s:
            return SearchAction()
        elif key.sym == tcod.event.K_d:
            return DisarmTrapAction()

        # セーブ・ロード
        if key.mod & tcod.event.KMOD_CTRL:
            if key.sym == tcod.event.K_s:
                return SaveGameAction()
            elif key.sym == tcod.event.K_l:
                return LoadGameAction()

        return None

    def _parse_movement_key(self, key: tcod.event.KeyDown) -> Optional[MoveAction]:
        """移動キーの解析"""
        # Vi-keys
        vi_keys = {
            tcod.event.K_h: (-1, 0),   # 左
            tcod.event.K_j: (0, 1),    # 下
            tcod.event.K_k: (0, -1),   # 上
            tcod.event.K_l: (1, 0),    # 右
            tcod.event.K_y: (-1, -1),  # 左上
            tcod.event.K_u: (1, -1),   # 右上
            tcod.event.K_b: (-1, 1),   # 左下
            tcod.event.K_n: (1, 1),    # 右下
        }

        # 矢印キー
        arrow_keys = {
            tcod.event.K_LEFT: (-1, 0),
            tcod.event.K_RIGHT: (1, 0),
            tcod.event.K_UP: (0, -1),
            tcod.event.K_DOWN: (0, 1),
        }

        # テンキー
        numpad_keys = {
            tcod.event.K_KP_1: (-1, 1),   # 左下
            tcod.event.K_KP_2: (0, 1),    # 下
            tcod.event.K_KP_3: (1, 1),    # 右下
            tcod.event.K_KP_4: (-1, 0),   # 左
            tcod.event.K_KP_6: (1, 0),    # 右
            tcod.event.K_KP_7: (-1, -1),  # 左上
            tcod.event.K_KP_8: (0, -1),   # 上
            tcod.event.K_KP_9: (1, -1),   # 右上
        }

        # 全入力方式をチェック
        for key_map in [vi_keys, arrow_keys, numpad_keys]:
            if key.sym in key_map:
                dx, dy = key_map[key.sym]
                return MoveAction(dx, dy)

        return None
```

### FOVManager (視界管理)

TCOD統合視界システム。

```python
class FOVManager:
    """視界管理システム"""

    def __init__(self):
        self.current_fov: Optional[list[list[bool]]] = None
        self.show_fov_toggle = False

    def calculate_fov(self, tiles: list[list[Tile]],
                     player_x: int, player_y: int,
                     radius: int) -> list[list[bool]]:
        """視界の計算"""
        width = len(tiles[0])
        height = len(tiles)

        # TCOD透明性マップの作成
        transparency_map = tcod.map.Map(width, height)

        for y in range(height):
            for x in range(width):
                tile = tiles[y][x]
                transparency_map.transparent[y, x] = tile.transparent
                transparency_map.walkable[y, x] = tile.walkable

        # FOV計算実行
        tcod.map.compute_fov(
            transparency_map,
            x=player_x, y=player_y,
            radius=radius,
            algorithm=tcod.FOV_SHADOW  # 影アルゴリズム使用
        )

        # 結果の変換
        fov = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append(transparency_map.fov[y, x])
            fov.append(row)

        self.current_fov = fov
        return fov

    def update_light_radius(self, player: Player) -> int:
        """光源アイテムを考慮した視界半径の更新"""
        base_radius = 3  # 基本視界半径

        # Light効果の確認
        light_bonus = 0
        if player.has_status_effect("light"):
            light_effect = player.get_status_effect("light")
            light_bonus = light_effect.light_bonus

        return base_radius + light_bonus

    def render_fov_overlay(self, console: tcod.Console) -> None:
        """FOV可視化オーバーレイ（Tabキーでトグル）"""
        if not self.show_fov_toggle or not self.current_fov:
            return

        for y in range(len(self.current_fov)):
            for x in range(len(self.current_fov[0])):
                if self.current_fov[y][x]:
                    # 視界内を薄い黄色でハイライト
                    tcod.console_set_char_background(
                        console, x, y, (50, 50, 0), tcod.BKGND_ADDALPHA(64)
                    )
```

## 状態管理とナビゲーション

### GameStates統合

UI画面とGameStatesの統合管理。

```python
# GameStatesと画面の対応
state_screen_mapping = {
    GameStates.MENU: MenuScreen(),
    GameStates.PLAYERS_TURN: GameScreen(),
    GameStates.ENEMY_TURN: GameScreen(),
    GameStates.SHOW_INVENTORY: InventoryScreen(),
    GameStates.DROP_INVENTORY: InventoryScreen(),
    GameStates.SHOW_MAGIC: MagicScreen(),
    GameStates.TARGETING: GameScreen(),  # ターゲット選択オーバーレイ
    GameStates.GAME_OVER: GameOverScreen(),
    GameStates.VICTORY: VictoryScreen(),
}
```

### ナビゲーション制御

```python
class NavigationManager:
    """画面遷移制御"""

    def handle_state_transition(self, old_state: GameStates,
                               new_state: GameStates,
                               game_context: GameContext) -> None:
        """状態遷移処理"""
        # 終了処理
        if old_state == GameStates.SHOW_INVENTORY:
            self._cleanup_inventory_screen()
        elif old_state == GameStates.TARGETING:
            self._cleanup_targeting_mode()

        # 初期化処理
        if new_state == GameStates.SHOW_INVENTORY:
            self._initialize_inventory_screen(game_context)
        elif new_state == GameStates.TARGETING:
            self._initialize_targeting_mode(game_context)
```

## パフォーマンス最適化

### 描画最適化

```python
class OptimizedRenderer:
    """最適化された描画処理"""

    def __init__(self):
        self.dirty_regions: set[tuple[int, int]] = set()
        self.last_frame_data: dict = {}

    def render_with_dirty_tracking(self, console: tcod.Console,
                                  game_context: GameContext) -> None:
        """変更領域のみの描画更新"""
        current_frame_data = self._capture_frame_data(game_context)

        # 変更検出
        for pos, data in current_frame_data.items():
            if pos not in self.last_frame_data or self.last_frame_data[pos] != data:
                self.dirty_regions.add(pos)

        # 変更領域のみ描画
        for x, y in self.dirty_regions:
            self._render_tile(console, x, y, current_frame_data[(x, y)])

        self.dirty_regions.clear()
        self.last_frame_data = current_frame_data
```

### メモリ効率化

```python
# 大きなマップでのメモリ使用量削減
def render_viewport_only(self, console: tcod.Console,
                        game_context: GameContext) -> None:
    """視界範囲のみの描画"""
    player = game_context.player
    viewport_size = 40  # 80x24画面の場合

    # 描画範囲の計算
    start_x = max(0, player.x - viewport_size // 2)
    end_x = min(dungeon.width, start_x + viewport_size)
    start_y = max(0, player.y - viewport_size // 2)
    end_y = min(dungeon.height, start_y + viewport_size)

    # 必要範囲のみ描画
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            self._render_tile(console, x - start_x, y - start_y, tiles[y][x])
```

## 既知の課題

### 1. 入力処理の安定性

**問題:** 特定のキー組み合わせでの不安定な動作
- 修飾キー（Ctrl、Shift）との組み合わせで未定義動作
- 一部の国際キーボード配列での互換性問題

**対応予定:**
- キーマッピングシステムの再設計
- より堅牢な入力バリデーション

### 2. レンダリングパフォーマンス

**問題:** 大規模マップでのフレームレート低下
- 100x100以上のマップでの描画遅延
- エンティティ数増加に伴うパフォーマンス劣化

**対応予定:**
- 視界範囲外の描画スキップ
- エンティティ描画の最適化

### 3. 状態永続化の課題

**問題:** セーブ・ロード時の画面状態復元
- 一部の画面状態が正しく復元されない
- セーブデータの肥大化

**対応予定:**
- 軽量化された状態保存形式
- 段階的復元プロセス

## 使用パターン

### 基本的な画面実装

```python
from pyrogue.ui.screens.screen import Screen

class CustomScreen(Screen):
    """カスタム画面の実装例"""

    def render(self, root_console: tcod.Console,
               game_context: GameContext) -> None:
        # カスタム描画処理
        tcod.console_print(root_console, 10, 10, "Custom Screen", color.WHITE)

    def handle_key(self, key: tcod.event.KeyDown,
                   game_context: GameContext) -> Optional[Action]:
        # カスタム入力処理
        if key.sym == tcod.event.K_ESCAPE:
            return BackToGameAction()
        return None
```

### カスタム描画コンポーネント

```python
from pyrogue.ui.components.game_renderer import GameRenderer

class CustomRenderer(GameRenderer):
    """カスタム描画機能"""

    def render_custom_overlay(self, console: tcod.Console,
                            game_context: GameContext) -> None:
        """カスタムオーバーレイの描画"""
        # 特殊な描画処理
        for x in range(console.width):
            for y in range(console.height):
                if self._should_highlight(x, y, game_context):
                    tcod.console_set_char_background(
                        console, x, y, color.YELLOW, tcod.BKGND_ADDALPHA(128)
                    )
```

## 拡張ガイド

### 新しい画面の追加

```python
# 1. 新しい画面クラスの作成
class SettingsScreen(Screen):
    def render(self, root_console: tcod.Console,
               game_context: GameContext) -> None:
        # 設定画面の描画処理
        pass

    def handle_key(self, key: tcod.event.KeyDown,
                   game_context: GameContext) -> Optional[Action]:
        # 設定画面の入力処理
        pass

# 2. GameStatesへの追加
class GameStates(Enum):
    # 既存状態...
    SETTINGS = auto()

# 3. Engine画面マッピングへの追加
def _get_screen_for_state(self, state: GameStates) -> Screen:
    mapping = {
        # 既存マッピング...
        GameStates.SETTINGS: SettingsScreen(),
    }
    return mapping[state]
```

### カスタム入力処理

```python
class ExtendedInputHandler(InputHandler):
    """拡張入力処理"""

    def handle_custom_keys(self, key: tcod.event.KeyDown) -> Optional[Action]:
        """カスタムキーの処理"""
        # ファンクションキー対応
        if key.sym == tcod.event.K_F1:
            return ShowHelpAction()
        elif key.sym == tcod.event.K_F5:
            return QuickSaveAction()
        elif key.sym == tcod.event.K_F9:
            return QuickLoadAction()

        # マウス対応（将来実装）
        return None
```

### アニメーション機能

```python
class AnimationManager:
    """アニメーション管理"""

    def __init__(self):
        self.active_animations: list[Animation] = []

    def add_animation(self, animation: Animation) -> None:
        """アニメーションの追加"""
        self.active_animations.append(animation)

    def update_animations(self, delta_time: float) -> None:
        """アニメーション更新"""
        completed = []
        for animation in self.active_animations:
            if animation.update(delta_time):
                completed.append(animation)

        for animation in completed:
            self.active_animations.remove(animation)
```

## アクセシビリティ

### カラーバリアフリー

```python
# 色覚異常対応のカラーパレット
accessibility_colors = {
    "health": (220, 50, 50),     # 明るい赤
    "mana": (50, 50, 220),       # 明るい青
    "warning": (255, 165, 0),    # オレンジ
    "success": (50, 220, 50),    # 明るい緑
}
```

### 操作支援

```python
# キーリピート機能
class KeyRepeatHandler:
    def __init__(self):
        self.repeat_delay = 0.5  # 初回リピート遅延
        self.repeat_rate = 0.1   # リピート間隔
```

## まとめ

UI コンポーネントは、PyRogueプロジェクトのユーザー体験において以下の価値を提供します：

- **直感的操作**: 3種類の入力方式による包括的なサポート
- **視覚的魅力**: 文字ベースながら豊富な視覚情報
- **レスポンシブ**: ウィンドウサイズ変更への適応
- **拡張性**: 新しい画面・機能の容易な追加
- **アクセシビリティ**: 多様なユーザーニーズへの配慮

この設計により、オリジナルRogueの魅力的なゲームプレイを現代的なUIで体験できる、使いやすく美しいインターフェースを実現しています。既知の課題についても明確な改善計画があり、継続的な品質向上が期待できます。
