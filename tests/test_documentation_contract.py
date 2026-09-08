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
