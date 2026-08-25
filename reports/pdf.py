from io import BytesIO
from pathlib import Path

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _register_font():
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont("ExamFont", str(path)))
                return "ExamFont"
            except Exception:
                pass
    return "Helvetica"


def build_attempts_pdf_response(queryset):
    font_name = _register_font()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    styles = getSampleStyleSheet()
    for style_name in ("Title", "Normal"):
        styles[style_name].fontName = font_name

    story = [
        Paragraph("O‘QITUVCHILAR TEST NATIJALARI", styles["Title"]),
        Spacer(1, 8 * mm),
    ]
    data = [
        [
            "№",
            "F.I.Sh.",
            "Login",
            "Test",
            "Mutaxassislik",
            "Til",
            "Natija",
            "Ball",
            "Status",
        ]
    ]

    for idx, attempt in enumerate(queryset, start=1):
        user = attempt.assignment.user
        data.append(
            [
                str(idx),
                user.get_full_name() or user.username,
                user.username,
                attempt.assignment.test.title,
                attempt.speciality.name,
                attempt.foreign_language.name,
                f"{attempt.correct_count}/{attempt.total_count}",
                f"{attempt.score or 0}/100",
                attempt.get_status_display(),
            ]
        )

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            10 * mm,
            38 * mm,
            27 * mm,
            40 * mm,
            36 * mm,
            27 * mm,
            22 * mm,
            22 * mm,
            28 * mm,
        ],
    )
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (-3, 1), (-1, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
            ]
        )
    )
    story.append(table)
    doc.build(story)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="test-natijalari.pdf"'
    return response
