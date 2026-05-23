import fitz  # PyMuPDF
from pathlib import Path


def extract_pdf_text(pdf_path: Path) -> str:
    """
    Extract full machine-readable text from a PDF file.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    full_text_parts = []

    with fitz.open(pdf_path) as doc:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text")
            full_text_parts.append(f"\n--- PAGE {page_number} ---\n{text}")

    full_text = "\n".join(full_text_parts).strip()

    if not full_text:
        raise ValueError("No text extracted from PDF. The PDF may be scanned or unreadable.")

    return full_text


def get_pdf_page_count(pdf_path: Path) -> int:
    """
    Return total page count of the PDF.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    with fitz.open(pdf_path) as doc:
        return len(doc)
        