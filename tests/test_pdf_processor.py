"""Tests for PDF text extraction."""

from pathlib import Path

import pymupdf

from modules.pdf_processor import extract_pdf_text


def _create_pdf(path: Path) -> None:
    document = pymupdf.open()
    first_page = document.new_page()
    first_page.insert_text((72, 72), "RFP deadline is 30 November 2026.")
    second_page = document.new_page()
    second_page.insert_text((72, 72), "The supplier must submit a technical proposal.")
    document.save(path)
    document.close()


def test_extract_pdf_text_returns_one_record_per_page(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _create_pdf(pdf_path)

    pages = extract_pdf_text(str(pdf_path))

    assert len(pages) == 2
    assert pages[0]["page"] == 1
    assert pages[1]["page"] == 2
    assert "RFP deadline" in pages[0]["text"]
    assert "technical proposal" in pages[1]["text"]


def test_extract_pdf_text_strips_page_text(tmp_path: Path) -> None:
    pdf_path = tmp_path / "whitespace.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "  Text that should be extracted  ")
    document.save(pdf_path)
    document.close()

    pages = extract_pdf_text(str(pdf_path))

    assert pages == [{"page": 1, "text": "Text that should be extracted"}]


def test_extract_pdf_text_raises_for_missing_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.pdf"

    try:
        extract_pdf_text(str(missing_path))
    except Exception as error:
        assert isinstance(error, (FileNotFoundError, RuntimeError, pymupdf.FileNotFoundError))
    else:
        raise AssertionError("extract_pdf_text should fail for a missing PDF")
