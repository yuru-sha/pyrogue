"""
リファクタリングされたゲームスクリーンモジュール。

このモジュールは、元のGameScreenから責務を分離し、
各コンポーネントに処理を委譲する構造になっています。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrogue.core.rogue_game import CommandResult, DisplayCell, GameState
from pyrogue.ui.components.fov_manager import FOVManager
from pyrogue.ui.components.game_renderer import GameRenderer
from pyrogue.ui.components.input_handler import InputHandler

if TYPE_CHECKING:
    from collections.abc import Iterable

    import tcod

    from pyrogue.core.engine import Engine
    from pyrogue.core.game_states import GameStates
    from pyrogue.core.rogue_game import PlayerState


class GameScreen:
    """
    リファクタリングされたメインゲームスクリーン。

    各責務を専用のコンポーネントに委譲し、
    自身はコンポーネント間の調整役に徹します。

    Attributes
    ----------
        engine: ゲームエンジンインスタンス
        rogue_game: canonicalなゲーム状態
        renderer: 描画処理コンポーネント
        input_handler: 入力処理コンポーネント
        fov_manager: FOV管理コンポーネント
        dungeon_width: ダンジョンの幅
        dungeon_height: ダンジョンの高さ

    """

    def __init__(self, engine: Engine | None, seed: int | None = None) -> None:
        """
        ゲームスクリーンを初期化。

        Args:
        ----
            engine: メインゲームエンジンのインスタンス（CLIモードの場合はNone）
            seed: 決定論的なゲーム生成に使う乱数シード

        """
        self.engine = engine
        self.seed = seed

        # ダンジョンサイズの設定
        if engine:
            self.dungeon_width = getattr(engine, "map_width", 80)
            self.dungeon_height = getattr(engine, "map_height", 45)
        else:
            # CLIモードでは固定値を使用
            self.dungeon_width = 80
            self.dungeon_height = 45

        self.rogue_game = GameState(seed)

        # 各コンポーネントを初期化
        self.renderer = GameRenderer(self)
        self.input_handler = InputHandler(self)
        self.fov_manager = FOVManager(self)

    def setup_new_game(self) -> None:
        """新しいゲームをセットアップ。"""
        self.rogue_game = GameState(self.seed)
        self._reset_transient_fov_override()
        self.input_handler.reset_selection()

    def update_console(self) -> None:
        """コンソールを更新する（エンジンから呼ばれる）。"""
        if self.engine:
            self.engine.update_console()

    def render(self, console: tcod.Console) -> None:
        """
        画面の描画（レンダラーに委譲）。

        Args:
        ----
            console: TCODコンソール

        """
        # 描画処理を委譲
        self.renderer.render(console)

    def display_cells(self) -> dict[tuple[int, int], DisplayCell]:
        """Return canonical display cells using the current GUI FOV setting."""
        return self.rogue_game.display_cells(show_all=not self.fov_manager.fov_enabled)

    def execute(self, command: str, args: Iterable[object] = ()) -> CommandResult:
        """Execute a GUI command while respecting the display-only FOV override."""
        return self.rogue_game.execute(command, args, update_explored=self.fov_manager.fov_enabled)

    def handle_key(self, event: tcod.event.KeyDown) -> GameStates | None:
        """
        キー入力の処理（入力ハンドラーに委譲）。

        Args:
        ----
            event: TCODキーイベント

        Returns:
        -------
            新しいゲーム状態、またはNone

        """
        return self.input_handler.handle_key(event)

    def handle_targeting(self, event: tcod.event.KeyDown) -> None:
        """
        ターゲット選択モードのキー入力処理（入力ハンドラーに委譲）。

        Args:
        ----
            event: TCODキーイベント

        """
        self.input_handler.handle_targeting(event)

    def save_game(self) -> bool:
        """
        canonicalなゲーム状態を保存。

        Returns
        -------
            保存に成功した場合True

        """
        from pyrogue.core.save_manager import SaveManager

        return SaveManager().save_game_state(self.rogue_game.to_dict())

    def load_game(self) -> bool:
        """
        canonicalなゲーム状態を読み込み。

        Returns
        -------
            読み込みに成功した場合True

        """
        from pyrogue.core.save_manager import SaveManager

        data = SaveManager().load_game_state()
        if data is None:
            return False
        try:
            self.rogue_game = GameState.from_dict(data)
        except (TypeError, ValueError):
            return False
        self._reset_transient_fov_override()
        self.input_handler.reset_selection()
        return True

    def _reset_transient_fov_override(self) -> None:
        """Reset the display-only FOV override for the active game state."""
        self.fov_manager.fov_enabled = True
        self.fov_manager.update_fov()

    # canonical GameStateへの互換アクセサ
    @property
    def player(self) -> PlayerState:
        """プレイヤーオブジェクトへのアクセス。"""
        return self.rogue_game.player

    @property
    def dungeon(self):
        """ダンジョンオブジェクトへのアクセス。"""
        return self._create_dungeon_object()

    @property
    def game_screen(self):
        """ゲームスクリーン自身へのアクセス。"""
        return self

    def add_message(self, message: str, color: tuple[int, int, int] = (255, 255, 255)) -> None:
        """メッセージをゲームログに追加。"""
        self.rogue_game.messages.append(message)

    def _create_dungeon_object(self):
        """ダンジョンオブジェクトのプロキシを作成。"""
        game = self.rogue_game

        class DungeonProxy:
            current_floor = property(lambda _: game.current_floor)
            tiles = property(lambda _: game.floor.tiles)
            width = game.width
            height = game.height
            explored = property(lambda _: game.floor.explored)
            monsters = property(lambda _: game.floor.monsters)
            items = property(lambda _: game.floor.items)

            def get_blocking_entity_at(self, x, y):
                return next((monster for monster in game.floor.monsters if (monster.x, monster.y) == (x, y)), None)

        return DungeonProxy()

    # canonical GameStateの状態チェック
    def check_player_death(self) -> bool:
        """プレイヤーの死亡をチェック。"""
        return self.rogue_game.is_dead

    def check_game_over(self) -> bool:
        """ゲームオーバー状態をチェック。"""
        return self.rogue_game.is_dead

    def check_victory(self) -> bool:
        """勝利条件をチェック。"""
        return self.rogue_game.is_victory

    # CLIモード互換メソッド
    def try_move_player(self, dx: int, dy: int) -> bool:
        """プレイヤーの移動を試行。"""
        return self.rogue_game.move(dx, dy).success

    def try_attack_adjacent_enemy(self) -> bool:
        """隣接する敵を攻撃。"""
        for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
            monster = next(
                (
                    monster
                    for monster in self.rogue_game.floor.monsters
                    if (monster.x, monster.y) == (self.player.x + dx, self.player.y + dy)
                ),
                None,
            )
            if monster:
                return self.rogue_game._player_attack(monster).success  # noqa: SLF001
        return False

    def try_use_item(self, item) -> bool:
        """アイテムを使用。"""
        return self.rogue_game.execute("quaff", [item.id]).success

    def get_nearby_enemies(self) -> list:
        """周囲の敵を取得。"""
        return [
            monster
            for monster in self.rogue_game.floor.monsters
            if max(abs(monster.x - self.player.x), abs(monster.y - self.player.y)) <= 1
        ]

    def process_enemy_turns(self) -> None:
        """敵のターンを処理。"""
        self.rogue_game._process_monsters()  # noqa: SLF001

    # ユーティリティメソッド
    def start_targeting(self, start_x: int | None = None, start_y: int | None = None) -> None:
        """ターゲット選択モードを開始。"""
        self.input_handler.start_targeting(start_x, start_y)

    def get_targeting_info(self) -> tuple[bool, int, int]:
        """ターゲット選択の情報を取得。"""
        return self.input_handler.get_targeting_info()

    def toggle_fov(self) -> str:
        """FOV表示の切り替え。"""
        return self.fov_manager.toggle_fov()

    def has_save_file(self) -> bool:
        """セーブファイルが存在するかチェック。"""
        from pyrogue.core.save_manager import SaveManager

        save_manager = SaveManager()
        return save_manager.has_save_file()

    def delete_save_file(self) -> bool:
        """セーブファイルを削除。"""
        from pyrogue.core.save_manager import SaveManager

        save_manager = SaveManager()
        return save_manager.delete_save_data()
