"""
ゲーム状態モジュール。

このモジュールは、ゲームの各状態を定義し、状態遷移と
渡り制御を管理するためのEnumを提供します。

Example:
-------
    >>> if game.state == GameStates.PLAYERS_TURN:
    ...     handle_player_input()

"""

from enum import Enum, auto


class GameStates(Enum):
    """
    ゲームの状態を表す列挙型。

    ゲームの進行状態、メニューシステム、インベントリ管理等の
    各状態を定義し、ゲームエンジンが適切な処理を選択できるようにします。

    States:
        MENU: メインメニュー状態
        PLAYERS_TURN: プレイヤーのターン
        GAME_OVER: ゲームオーバー状態
        SHOW_INVENTORY: インベントリ表示状態
        EXIT: ゲーム終了状態
    """

    MENU = auto()  # メインメニュー表示中
    PLAYERS_TURN = auto()  # プレイヤーの入力待ち
    GAME_OVER = auto()  # ゲームオーバー画面表示
    VICTORY = auto()  # ゲーム勝利画面表示
    SHOW_INVENTORY = auto()  # インベントリ一覧表示
    HELP_MENU = auto()  # ヘルプメニュー表示
    QUICK_GUIDE = auto()  # クイックガイド表示
    EXIT = auto()  # ゲーム終了シグナル
