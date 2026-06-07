"""
corpus_loader.py — Auto-download 5000+ pages of free academic content
Run this ONCE before starting the app:
    python corpus_loader.py

Downloads free Wikipedia articles and converts them to PDFs stored in /corpus/
Then bulk-indexes all of them into ChromaDB automatically.
"""

import os
import sys
import requests
import time
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY

# ── 50 Wikipedia topics covering CS / MCA syllabus ───────────────────────────
TOPICS = [
    "Machine learning", "Deep learning", "Neural network", "Natural language processing",
    "Computer vision", "Artificial intelligence", "Reinforcement learning",
    "Support vector machine", "Random forest", "Decision tree",
    "Convolutional neural network", "Recurrent neural network", "Transformer model",
    "BERT language model", "Large language model", "Retrieval-augmented generation",
    "Database management system", "SQL", "NoSQL database", "PostgreSQL",
    "MongoDB", "Redis", "Data warehouse", "ETL process", "Data mining",
    "Cybersecurity", "Network security", "Cryptography", "Firewall", "Intrusion detection system",
    "Cloud computing", "Amazon Web Services", "Microservices", "Docker", "Kubernetes",
    "Software engineering", "Agile software development", "DevOps", "Git version control",
    "Application programming interface",
    "Computer network", "OSI model", "TCP/IP", "HTTP", "DNS",
    "Operating system", "Linux", "Memory management", "Process management",
    "Compiler", "Algorithm", "Data structure", "Big O notation"
]

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "corpus")
os.makedirs(CORPUS_DIR, exist_ok=True)

STYLES = getSampleStyleSheet()
BODY_STYLE = ParagraphStyle(
    "Body", parent=STYLES["Normal"],
    fontSize=11, leading=16, spaceAfter=8, alignment=TA_JUSTIFY
)
HEADING_STYLE = ParagraphStyle(
    "H", parent=STYLES["Heading2"], fontSize=13, spaceAfter=6, spaceBefore=12
)


def fetch_wikipedia(topic: str) -> str | None:
    """Fetch plain text from Wikipedia API."""
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query", "format": "json", "titles": topic,
            "prop": "extracts", "explaintext": True, "exsectionformat": "plain"
        }
        r = requests.get(url, params=params, timeout=15)
        pages = r.json()["query"]["pages"]
        page = next(iter(pages.values()))
        text = page.get("extract", "")
        return text if len(text) > 500 else None
    except Exception as e:
        print(f"    ⚠ Wikipedia fetch failed for '{topic}': {e}")
        return None


def text_to_pdf(topic: str, text: str, output_path: str) -> int:
    """Convert text to PDF, returns page count."""
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm
    )
    story = []
    story.append(Paragraph(topic, HEADING_STYLE))
    story.append(Spacer(1, 0.3*cm))

    # Split into paragraphs
    for para in text.split("\n\n"):
        para = para.strip()
        if not para or len(para) < 20:
            continue
        if para.startswith("==") and para.endswith("=="):
            heading = para.replace("=", "").strip()
            story.append(Paragraph(heading, HEADING_STYLE))
        else:
            # Escape XML characters for ReportLab
            para = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            try:
                story.append(Paragraph(para, BODY_STYLE))
            except Exception:
                continue
        story.append(Spacer(1, 0.2*cm))

    # Count pages by building
    from reportlab.platypus import SimpleDocTemplate as SDT
    from io import BytesIO
    buf = BytesIO()
    counter_doc = SDT(buf, pagesize=A4, leftMargin=2.5*cm, rightMargin=2.5*cm, topMargin=2.5*cm, bottomMargin=2.5*cm)
    counter_doc.build(story[:])

    doc.build(story)
    buf.seek(0)
    from pypdf import PdfReader
    try:
        return len(PdfReader(output_path).pages)
    except Exception:
        return 10


def bulk_index_corpus():
    """Index all PDFs in corpus/ into ChromaDB."""
    sys.path.insert(0, os.path.dirname(__file__))
    from services.pdf_processor import extract_text_from_pdf
    from services.vector_store import add_chunks, get_total_chunks
    import uuid

    pdf_files = [f for f in os.listdir(CORPUS_DIR) if f.endswith(".pdf")]
    print(f"\n📦 Indexing {len(pdf_files)} PDFs into ChromaDB...")

    for i, fname in enumerate(pdf_files):
        path = os.path.join(CORPUS_DIR, fname)
        doc_id = fname.replace(".pdf", "").replace(" ", "_")[:8]
        try:
            chunks = extract_text_from_pdf(path)
            add_chunks(doc_id, fname, chunks)
            print(f"  [{i+1}/{len(pdf_files)}] ✅ {fname} → {len(chunks)} chunks")
        except Exception as e:
            print(f"  [{i+1}/{len(pdf_files)}] ⚠ {fname} failed: {e}")

    total = get_total_chunks()
    print(f"\n✅ Total chunks in ChromaDB: {total:,}")


def main():
    print("=" * 55)
    print("  Enterprise RAG — Corpus Loader")
    print("  Downloading 50 Wikipedia topics (~5000+ pages)")
    print("=" * 55)

    total_pages = 0
    downloaded = 0

    for i, topic in enumerate(TOPICS):
        pdf_path = os.path.join(CORPUS_DIR, f"{topic.replace(' ', '_')}.pdf")

        # Skip if already downloaded
        if os.path.exists(pdf_path):
            print(f"  [{i+1}/50] ⏭ Already exists: {topic}")
            downloaded += 1
            continue

        print(f"  [{i+1}/50] 📥 Downloading: {topic} ...", end=" ", flush=True)
        text = fetch_wikipedia(topic)

        if not text:
            print("skipped (no content)")
            continue

        try:
            pages = text_to_pdf(topic, text, pdf_path)
            total_pages += pages
            downloaded += 1
            print(f"✅ {pages} pages")
        except Exception as e:
            print(f"❌ Failed: {e}")

        time.sleep(0.3)  # polite delay to Wikipedia

    print(f"\n{'='*55}")
    print(f"  Downloaded: {downloaded}/50 topics")
    print(f"  Estimated pages: {total_pages}+")
    print(f"{'='*55}")

    if downloaded > 0:
        bulk_index_corpus()
        print("\n🎉 Corpus ready! You can now run the app.")
    else:
        print("\n⚠ No topics downloaded. Check internet connection.")


if __name__ == "__main__":
    main()
