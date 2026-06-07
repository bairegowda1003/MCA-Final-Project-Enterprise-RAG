import os
from pypdf import PdfReader


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """Extract text from PDF and return list of page chunks."""
    reader = PdfReader(file_path)
    chunks = []

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text or not text.strip():
            continue

        # Split page into smaller chunks (~500 chars each)
        words = text.split()
        chunk_size = 100  # words per chunk
        for i in range(0, len(words), chunk_size):
            chunk_text = " ".join(words[i:i + chunk_size])
            if len(chunk_text.strip()) > 50:
                chunks.append({
                    "text": chunk_text.strip(),
                    "page_number": page_num + 1,
                })

    return chunks


def get_pdf_page_count(file_path: str) -> int:
    reader = PdfReader(file_path)
    return len(reader.pages)
