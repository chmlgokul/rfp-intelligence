from pathlib import Path

import pandas as pd

from modules.spreadsheet_processor import extract_spreadsheet_text


def test_extract_spreadsheet_text_reads_all_non_empty_worksheets(tmp_path: Path):
    workbook_path = tmp_path / "tender.xlsx"
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        pd.DataFrame([
            ["Eligibility", "Supplier must provide ISO certification"],
            ["Deadline", "Submit proposal before the closing date"],
        ]).to_excel(writer, sheet_name="Requirements", index=False, header=False)
        pd.DataFrame([["Technical", "The bidder shall support API integration"]]).to_excel(
            writer, sheet_name="Technical", index=False, header=False
        )

    records = extract_spreadsheet_text(str(workbook_path))

    assert len(records) == 2
    assert records[0]["page"] == "Sheet 1: Requirements"
    assert "ISO certification" in records[0]["text"]
    assert records[1]["page"] == "Sheet 2: Technical"
    assert "API integration" in records[1]["text"]


def test_extract_spreadsheet_text_handles_html_tender_export_with_xlx_suffix(tmp_path: Path):
    source_path = tmp_path / "tender.xlx"
    source_path.write_text(
        "<table><tr><td>Requirement</td><td>Supplier must submit a bid document</td></tr></table>",
        encoding="utf-8",
    )

    records = extract_spreadsheet_text(str(source_path))

    assert records[0]["page"] == "Sheet 1: Table 1"
    assert "submit a bid document" in records[0]["text"]
