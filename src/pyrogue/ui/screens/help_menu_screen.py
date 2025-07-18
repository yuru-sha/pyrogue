"""
ヘルプメニュースクリーンモジュール。

このモジュールはゲームのヘルプメニューを表示し、
初心者向けのガイダンスを提供します。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
import tcod.console
import tcod.event

from pyrogue.core.game_states import GameStates

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine


class HelpMenuScreen:
    """
    ヘルプメニュースクリーンクラス。

    ゲームのヘルプとガイダンスを表示し、
    初心者プレイヤーに必要な情報を提供します。
    """

    def __init__(self, console: tcod.console.Console, engine: Engine) -> None:
        """
        ヘルプメニュースクリーンを初期化。

        Args:
        ----
            console: TCODコンソールオブジェクト
            engine: メインゲームエンジンのインスタンス

        """
        self.console = console
        self.engine = engine
        self.menu_selection = 0
        self.current_page = 0
        self.help_sections = self._get_help_sections()

    def update_console(self, console: tcod.console.Console) -> None:
        """
        コンソールの更新。

        Args:
        ----
            console: 新しいTCODコンソールオブジェクト

        """
        self.console = console

    def render(self) -> None:
        """ヘルプメニューを描画。"""
        self.console.clear()

        # タイトル表示
        title = "PyRogue - Help & Guide"
        self.console.print(
            (self.console.width - len(title)) // 2,
            2,
            title,
            fg=(255, 215, 0),  # 金色
        )

        # セクション一覧表示
        menu_start_y = 5
        for i, section in enumerate(self.help_sections):
            text = f"> {section['title']}" if i == self.menu_selection else f"  {section['title']}"
            color = (255, 255, 255) if i == self.menu_selection else (150, 150, 150)
            self.console.print(
                5,
                menu_start_y + i * 2,
                text,
                fg=color,
            )

        # 選択されたセクションの内容を表示
        content_start_x = 40
        content_start_y = 5
        if self.help_sections:
            section = self.help_sections[self.menu_selection]

            # セクションタイトル
            self.console.print(
                content_start_x,
                content_start_y - 1,
                section["title"],
                fg=(255, 255, 100),
            )

            # セクション内容
            for i, line in enumerate(section["content"]):
                if content_start_y + i < self.console.height - 4:
                    self.console.print(
                        content_start_x,
                        content_start_y + i,
                        line,
                        fg=(200, 200, 200),
                    )

        # 操作説明
        help_text = "UP/DOWN: Navigate  ENTER: Select  ESC: Back to Menu"
        self.console.print(
            (self.console.width - len(help_text)) // 2,
            self.console.height - 2,
            help_text,
            fg=(100, 100, 100),
        )

    def handle_input(self, key: tcod.event.KeyDown) -> GameStates | None:
        """
        ユーザー入力の処理。

        Args:
        ----
            key: キーボード入力イベント

        Returns:
        -------
            ゲーム状態、またはNone

        """
        # 上矢印キーで上のセクションへ移動
        if key.sym == tcod.event.KeySym.UP:
            self.menu_selection = (self.menu_selection - 1) % len(self.help_sections)
        # 下矢印キーで下のセクションへ移動
        elif key.sym == tcod.event.KeySym.DOWN:
            self.menu_selection = (self.menu_selection + 1) % len(self.help_sections)
        # ESCキーでメインメニューに戻る
        elif key.sym == tcod.event.KeySym.ESCAPE:
            return GameStates.MENU

        return None

    def _get_help_sections(self) -> list[dict]:
        """
        ヘルプセクションのデータを生成。

        Returns
        -------
            ヘルプセクションのリスト

        """
        return [
            {
                "title": "Game Overview",
                "content": [
                    "Welcome to PyRogue!",
                    "",
                    "PyRogue is a classic roguelike adventure game.",
                    "Your goal is to descend 26 levels deep into",
                    "the dungeon, find the Amulet of Yendor,",
                    "and escape back to the surface.",
                    "",
                    "• Turn-based gameplay",
                    "• Permadeath (no save scumming)",
                    "• Procedurally generated dungeons",
                    "• Item identification system",
                    "• Classic ASCII graphics",
                ],
            },
            {
                "title": "Basic Controls",
                "content": [
                    "Movement:",
                    "  hjkl yubn  - Vi-style movement",
                    "  Arrow keys - Standard movement",
                    "  Numpad     - Numeric pad movement",
                    "",
                    "Essential Commands:",
                    "  , (comma)  - Pick up items",
                    "  i          - Open inventory",
                    "  ?          - Show help (in-game)",
                    "  o          - Open doors",
                    "  c          - Close doors",
                    "  s          - Search for hidden doors/traps",
                    "",
                    "System Commands:",
                    "  Ctrl+S     - Save game",
                    "  Ctrl+L     - Load game",
                    "  ESC        - Return to main menu",
                ],
            },
            {
                "title": "Combat System",
                "content": [
                    "Combat in PyRogue is automatic when you",
                    "move into a monster or it moves into you.",
                    "",
                    "Combat Factors:",
                    "  • Your attack and defense values",
                    "  • Monster's attack and defense",
                    "  • Equipment bonuses",
                    "  • Hunger penalties (when hungry)",
                    "",
                    "Experience & Leveling:",
                    "  • Gain experience by defeating monsters",
                    "  • Level up for better stats",
                    "  • Each level gives +8 HP, +3 Attack, +2 Defense",
                    "",
                    "Strategic Tips:",
                    "  • Better equipment = better combat performance",
                    "  • Stay fed to avoid combat penalties",
                    "  • Some monsters have special abilities",
                ],
            },
            {
                "title": "Items & Equipment",
                "content": [
                    "Inventory Management:",
                    "  • Press 'i' to open inventory",
                    "  • Use 'u' to use/equip items",
                    "  • Use 'd' to drop items",
                    "",
                    "Equipment Types:",
                    "  • Weapons: Increase attack power",
                    "  • Armor: Increase defense",
                    "  • Rings: Various magical effects",
                    "",
                    "Item Identification:",
                    "  • Many items start unidentified",
                    "  • Use Scroll of Identify to reveal properties",
                    "  • Some items have unknown effects until used",
                    "",
                    "Consumables:",
                    "  • Potions: Drink for various effects",
                    "  • Scrolls: Read for magical effects",
                    "  • Food: Eat to satisfy hunger",
                ],
            },
            {
                "title": "Survival Tips",
                "content": [
                    "Hunger System:",
                    "  • You get hungry over time",
                    "  • Hunger reduces combat effectiveness",
                    "  • Eat food to restore hunger",
                    "  • Food becomes more common in deeper levels",
                    "",
                    "Exploration:",
                    "  • Search walls for hidden doors ('s' key)",
                    "  • Be careful of traps",
                    "  • Each level has a down staircase (>)",
                    "",
                    "Death & Permadeath:",
                    "  • When you die, the game is over",
                    "  • No resurrection or continues",
                    "  • Learn from each attempt",
                    "",
                    "General Strategy:",
                    "  • Explore thoroughly before descending",
                    "  • Identify items when possible",
                    "  • Manage resources carefully",
                ],
            },
            {
                "title": "Amulet Quest",
                "content": [
                    "Your Ultimate Goal:",
                    "  • Descend to level B26F",
                    "  • Find the Amulet of Yendor",
                    "  • Return to the surface (B1F)",
                    "  • Use the up staircase to escape",
                    "",
                    "The Return Journey:",
                    "  • With the amulet, monsters become MUCH harder",
                    "  • The entire dungeon will try to stop you",
                    "  • Elite monsters will spawn frequently",
                    "  • This is the ultimate challenge!",
                    "",
                    "Victory Conditions:",
                    "  • Reach B1F with the Amulet of Yendor",
                    "  • Use the up staircase to escape",
                    "  • You win the game!",
                ],
            },
            {
                "title": "Status Effects & Stats",
                "content": [
                    "Understanding Your Character:",
                    "",
                    "Level & Experience System:",
                    "  • Defeat monsters to gain experience points",
                    "  • Level up grants: +8 HP, +3 Attack, +2 Defense",
                    "  • Higher levels unlock better equipment use",
                    "  • Level affects monster spawn difficulty",
                    "",
                    "Hunger System (Critical!):",
                    "  • 100% = Well Fed (no penalties)",
                    "  • 50-99% = Normal (no penalties)",
                    "  • 25-49% = Hungry (-1 Attack/Defense)",
                    "  • 1-24% = Very Hungry (-2 Attack/Defense)",
                    "  • 0% = Starving (-3 Attack/Defense)",
                    "  • Hunger decreases over time and with actions",
                    "  • Eat food regularly to maintain combat effectiveness",
                    "",
                    "Equipment System:",
                    "  • +/- numbers show magical enchantment",
                    "  • Blessed items: enhanced effects",
                    "  • Cursed items: negative effects, can't remove",
                    "  • Unidentified items: unknown properties",
                    "  • Use Scroll of Identify to reveal item stats",
                    "  • Use Scroll of Remove Curse for cursed items",
                    "",
                    "Combat Statistics:",
                    "  • Attack = Base + Level Bonus + Equipment",
                    "  • Defense = Base + Level Bonus + Equipment",
                    "  • Damage reduced by hunger penalties",
                    "  • Ring effects stack with other equipment",
                ],
            },
        ]
