
import pymupdf


def extract_pdf_text(pdf_path):
    document = pymupdf.open(pdf_path)

    extracted_pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text("text")

        extracted_pages.append({
            "page": page_number,
            "text": text.strip()
        })

    document.close()

    return extracted_pages
