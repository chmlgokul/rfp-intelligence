"""Extract source-grounded text records from Excel tender workbooks."""

from __future__ import annotations

from html.parser import HTMLParser
from io import StringIO
from pathlib import Path

import pandas as pd


def extract_spreadsheet_text(file_path: str) -> list[dict[str, object]]:
    """Read every worksheet and return records compatible with PDF processing.

    A worksheet is treated as a source page.  Blank cells and rows are omitted,
    while the original row order is retained for traceability in the review UI.
    ``.xls`` uses xlrd and modern workbooks use openpyxl.
    """
    path = Path(file_path)
    extension = path.suffix.casefold()
    raw = path.read_bytes()
    sheets = _read_source(path, raw, extension)
    records: list[dict[str, object]] = []

    for sheet_number, (sheet_name, frame) in enumerate(sheets.items(), start=1):
        rows: list[str] = []
        for row in frame.fillna("").astype(str).values.tolist():
            values = [value.strip() for value in row if value.strip() and value.strip().lower() != "nan"]
            if values:
                rows.append(" | ".join(values))
        if rows:
            records.append({
                "page": f"Sheet {sheet_number}: {sheet_name}",
                "text": "\n".join(rows),
            })

    return records


def _read_source(path: Path, raw: bytes, extension: str) -> dict[str, pd.DataFrame]:
    """Read real Excel files and common tender-portal mislabeled exports."""
    # Modern .xlsx files are ZIP containers. This also handles an xlsx file
    # downloaded with a non-standard .xlx suffix.
    if raw.startswith(b"PK"):
        return pd.read_excel(path, sheet_name=None, header=None, dtype=object, engine="openpyxl")

    # Legacy .xls files are OLE Compound Document files. This also handles an
    # old workbook whose extension was changed to .xlx by a tender portal.
    if raw.startswith(b"\xd0\xcf\x11\xe0") or extension == ".xls":
        try:
            return pd.read_excel(path, sheet_name=None, header=None, dtype=object, engine="xlrd")
        except Exception as error:
            if raw.startswith(b"\xd0\xcf\x11\xe0"):
                raise ValueError("The legacy Excel workbook could not be read. It may be corrupted or password-protected.") from error

    # Some portals serve an HTML table with an .xls/.xlx filename.
    try:
        tables = pd.read_html(StringIO(raw.decode("utf-8", errors="ignore")))
        if tables:
            return {f"Table {index}": table for index, table in enumerate(tables, start=1)}
    except (ValueError, ImportError):
        html_rows = _parse_html_rows(raw)
        if html_rows:
            return {"Table 1": pd.DataFrame(html_rows)}

    # Last fallback for text/CSV-like downloads with an Excel-looking suffix.
    try:
        frame = pd.read_csv(StringIO(raw.decode("utf-8-sig")), sep=None, engine="python", header=None, dtype=object)
        return {"Data": frame}
    except Exception as error:
        raise ValueError(
            "This file is not a readable XLS/XLSX workbook. The tender portal may have returned a web page or a protected download."
        ) from error


def _parse_html_rows(raw: bytes) -> list[list[str]]:
    """Parse simple HTML tables without requiring lxml or html5lib."""
    class TableParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.rows: list[list[str]] = []
            self.current_row: list[str] | None = None
            self.current_cell: list[str] | None = None

        def handle_starttag(self, tag: str, attrs) -> None:
            if tag.lower() == "tr":
                self.current_row = []
            elif tag.lower() in {"td", "th"} and self.current_row is not None:
                self.current_cell = []

        def handle_data(self, data: str) -> None:
            if self.current_cell is not None:
                self.current_cell.append(data)

        def handle_endtag(self, tag: str) -> None:
            tag = tag.lower()
            if tag in {"td", "th"} and self.current_row is not None and self.current_cell is not None:
                self.current_row.append(" ".join("".join(self.current_cell).split()))
                self.current_cell = None
            elif tag == "tr" and self.current_row:
                if any(self.current_row):
                    self.rows.append(self.current_row)
                self.current_row = None

    parser = TableParser()
    parser.feed(raw.decode("utf-8", errors="ignore"))
    return parser.rows
