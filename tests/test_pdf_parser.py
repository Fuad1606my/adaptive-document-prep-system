from src.config import PDF_PATH
from src.pdf_parser import extract_pdf_text, get_pdf_page_count


def test_pdf_file_exists():
    assert PDF_PATH.exists()


def test_pdf_page_count_is_50():
    page_count = get_pdf_page_count(PDF_PATH)
    assert page_count == 50


def test_extract_pdf_text_not_empty():
    text = extract_pdf_text(PDF_PATH)

    assert isinstance(text, str)
    assert len(text.strip()) > 0
    assert "Section" in text