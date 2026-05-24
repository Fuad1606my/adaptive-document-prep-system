import pytest

from src.config import PDF_PATH
from src.pdf_parser import extract_pdf_text
from src.section_mapper import split_sections, get_section_summary, SECTION_TITLES


def test_split_sections_returns_10_sections():
    full_text = extract_pdf_text(PDF_PATH)
    sections = split_sections(full_text)

    assert isinstance(sections, dict)
    assert len(sections) == 10


def test_section_5_exists_and_has_expected_title():
    full_text = extract_pdf_text(PDF_PATH)
    sections = split_sections(full_text)

    assert 5 in sections
    assert SECTION_TITLES[5] == "Operational Tactics and Combat Doctrine"
    assert len(sections[5]) > 100


def test_get_section_summary_returns_expected_keys():
    full_text = extract_pdf_text(PDF_PATH)
    sections = split_sections(full_text)

    summary = get_section_summary(5, sections[5])

    assert summary["section_id"] == 5
    assert summary["title"] == SECTION_TITLES[5]
    assert summary["characters"] > 0
    assert "preview" in summary


def test_split_sections_raises_error_for_invalid_text():
    invalid_text = "This text has no valid section headings."

    with pytest.raises(ValueError):
        split_sections(invalid_text)