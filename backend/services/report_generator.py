import os
import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


def generate_report(topic: str, answer: str, chunks: list[dict], output_path: str) -> str:

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # -----------------------------
    # Styles
    # -----------------------------

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1a2e4a"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#666666"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1a2e4a"),
        spaceBefore=14,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#333333"),
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    )

    source_style = ParagraphStyle(
        "Source",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        leftIndent=10,
        spaceAfter=4,
    )

    # -----------------------------
    # Header
    # -----------------------------

    story.append(
        Paragraph(
            "Enterprise Research Assistant",
            subtitle_style
        )
    )

    story.append(
        Paragraph(
            f"Research Report: {topic}",
            title_style
        )
    )

    story.append(Spacer(1, 0.3 * cm))

    story.append(
        Paragraph(
            f"Generated: {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')} | Powered by RAG + Gemini",
            subtitle_style,
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=2,
            color=colors.HexColor("#1a2e4a")
        )
    )

    story.append(Spacer(1, 0.5 * cm))

    # -----------------------------
    # Report Content
    # -----------------------------

    sections = answer.split("\n")
    current_para = []

    for line in sections:

        line = line.strip()

        if not line:

            if current_para:
                story.append(
                    Paragraph(
                        " ".join(current_para),
                        body_style
                    )
                )
                current_para = []

            story.append(Spacer(1, 0.2 * cm))

        elif line.startswith(("1.", "2.", "3.", "4.", "5.")) and len(line) < 60:

            if current_para:
                story.append(
                    Paragraph(
                        " ".join(current_para),
                        body_style
                    )
                )
                current_para = []

            story.append(
                Paragraph(
                    line,
                    heading_style
                )
            )

        elif line.startswith("**") and line.endswith("**"):

            if current_para:
                story.append(
                    Paragraph(
                        " ".join(current_para),
                        body_style
                    )
                )
                current_para = []

            story.append(
                Paragraph(
                    line.replace("**", ""),
                    heading_style
                )
            )

        else:
            current_para.append(line)

    if current_para:
        story.append(
            Paragraph(
                " ".join(current_para),
                body_style
            )
        )

    # -----------------------------
    # Sources
    # -----------------------------

    story.append(Spacer(1, 0.5 * cm))

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#cccccc")
        )
    )

    story.append(
        Paragraph(
            "Retrieved Sources",
            heading_style
        )
    )

    for i, chunk in enumerate(chunks):

        metadata = chunk.get("metadata", {})

        fname = metadata.get(
            "filename",
            "document"
        )

        page = metadata.get(
            "page_number",
            "?"
        )

        text = chunk.get(
            "text",
            ""
        )

        preview = (
            text[:120] + "..."
            if len(text) > 120
            else text
        )

        story.append(
            Paragraph(
                f"[{i+1}] {fname} — Page {page}: {preview}",
                source_style
            )
        )

        story.append(
            Spacer(1, 0.1 * cm)
        )

    # -----------------------------
    # Build PDF
    # -----------------------------

    doc.build(story)

    return output_path