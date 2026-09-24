from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_docs_separate_monster_data_from_renderer_glyphs() -> None:
    for relative_path in ("docs/features.md", "docs/game_design_document.md"):
        document = (ROOT / relative_path).read_text()

        assert "論理ID" in document
        assert "`pyrogue.presentation.display_renderer`" in document
        assert "文字、名前、出現階、レベル、HP、攻撃、AC" not in document


def test_game_design_document_is_supplementary_to_spec() -> None:
    document = (ROOT / "docs/game_design_document.md").read_text()

    assert "補助資料" in document
    assert "仕様の正本" in document


def test_current_feature_guide_does_not_list_exclusions_as_current_behavior() -> None:
    document = (ROOT / "docs/features.md").read_text()

    assert "はゲーム機能として提供しません" in document
    assert "特別室はゲーム機能として提供しません" in document


def test_gui_help_does_not_advertise_excluded_features() -> None:
    from pyrogue.ui.screens.help_menu_screen import HelpMenuScreen
    from pyrogue.ui.screens.symbol_explanation_screen import SymbolExplanationScreen

    help_screen = HelpMenuScreen.__new__(HelpMenuScreen)
    symbols_screen = SymbolExplanationScreen.__new__(SymbolExplanationScreen)
    help_content = " ".join(line for page in help_screen._get_help_sections() for line in page["content"])
    symbol_content = " ".join(symbols_screen._get_symbol_content())

    assert "hidden doors" not in help_content
    assert "Hunger reduces combat effectiveness" not in help_content
    assert "Dream Eater" not in symbol_content
    assert "Phantom Fungus" not in symbol_content
