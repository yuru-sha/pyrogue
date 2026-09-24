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

        save_manager = SaveManager()
        data = save_manager.load_game_state()
        if data is None:
            if save_manager.last_error is not None:
                self.add_message(f"Failed to load save data: {save_manager.last_error}")
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

    # canonical GameStateへの互換アクセサ
    @property
    def player(self) -> PlayerState:
        """プレイヤーオブジェクトへのアクセス。"""
        return self.rogue_game.player

    def add_message(self, message: str, color: tuple[int, int, int] = (255, 255, 255)) -> None:
        """メッセージをゲームログに追加。"""
        self.rogue_game.messages.append(message)

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
