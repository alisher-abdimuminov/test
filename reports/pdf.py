from io import BytesIO
from pathlib import Path

from django.http import FileResponse, HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
	PageBreak,
	Paragraph,
	SimpleDocTemplate,
	Spacer,
	Table,
	TableStyle,
)


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
			50 * mm,
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


def build_attempt_detail_pdf_response(attempt):
	buffer = BytesIO()

	doc = SimpleDocTemplate(
		buffer,
		pagesize=A4,
		rightMargin=15 * mm,
		leftMargin=15 * mm,
		topMargin=15 * mm,
		bottomMargin=15 * mm,
	)

	styles = getSampleStyleSheet()

	title_style = ParagraphStyle(
		"CustomTitle",
		parent=styles["Title"],
		fontSize=16,
		leading=20,
		spaceAfter=12,
	)

	heading_style = ParagraphStyle(
		"CustomHeading",
		parent=styles["Heading2"],
		fontSize=13,
		leading=16,
		spaceBefore=10,
		spaceAfter=8,
	)

	normal_style = ParagraphStyle(
		"CustomNormal",
		parent=styles["BodyText"],
		fontSize=10,
		leading=14,
	)

	option_style = ParagraphStyle(
		"Option",
		parent=normal_style,
		leftIndent=8 * mm,
		spaceAfter=3,
	)

	story = []

	user = attempt.assignment.user
	test = attempt.assignment.test

	full_name = getattr(user, "full_name", "") or user.get_full_name() or user.username

	# =========================================================
	# HEADER
	# =========================================================

	story.append(
		Paragraph(
			"TEST NATIJASI",
			title_style,
		)
	)

	info_data = [
		["F.I.Sh.", full_name],
		["Login", user.username],
		["Test", test.title],
		["Mutaxassislik", str(attempt.speciality)],
		["Xorijiy til", str(attempt.foreign_language)],
		["Ball", f"{attempt.score or 0} / 100"],
		[
			"To'g'ri javoblar",
			f"{attempt.correct_count} / {attempt.total_count}",
		],
		[
			"Boshlangan vaqt",
			(
				attempt.started_at.strftime("%d.%m.%Y %H:%M")
				if attempt.started_at
				else "-"
			),
		],
		[
			"Yakunlangan vaqt",
			(
				attempt.submitted_at.strftime("%d.%m.%Y %H:%M")
				if attempt.submitted_at
				else "-"
			),
		],
	]

	info_table = Table(
		info_data,
		colWidths=[
			45 * mm,
			120 * mm,
		],
	)

	info_table.setStyle(
		TableStyle(
			[
				("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
				("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
				("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
				("VALIGN", (0, 0), (-1, -1), "TOP"),
				("FONTSIZE", (0, 0), (-1, -1), 9),
				("TOPPADDING", (0, 0), (-1, -1), 5),
				("BOTTOMPADDING", (0, 0), (-1, -1), 5),
				("LEFTPADDING", (0, 0), (-1, -1), 6),
				("RIGHTPADDING", (0, 0), (-1, -1), 6),
			]
		)
	)

	story.append(info_table)
	story.append(Spacer(1, 8 * mm))

	# =========================================================
	# QUESTIONS
	# =========================================================

	attempt_questions = (
		attempt.attempt_questions.select_related("question")
		.prefetch_related(
			"attempt_choices__choice",
			"answer__selected_choice",
		)
		.order_by("order")
	)

	result_rows = [
		[
			"№",
			"To'g'ri",
			"User",
			"Natija",
		]
	]

	detail_rows = []

	letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

	for number, attempt_question in enumerate(
		attempt_questions,
		start=1,
	):
		attempt_choices = list(
			attempt_question.attempt_choices.select_related("choice").order_by("order")
		)

		answer = getattr(
			attempt_question,
			"answer",
			None,
		)

		selected_choice_id = answer.selected_choice_id if answer else None

		correct_letter = "-"
		selected_letter = "-"

		options = []

		for index, attempt_choice in enumerate(
			attempt_choices,
		):
			letter = letters[index]
			choice = attempt_choice.choice

			if choice.is_correct:
				correct_letter = letter

			if choice.id == selected_choice_id:
				selected_letter = letter

			options.append(
				{
					"letter": letter,
					"choice": choice,
				}
			)

		is_correct = (
			selected_choice_id is not None and correct_letter == selected_letter
		)

		result_rows.append(
			[
				number,
				correct_letter,
				selected_letter,
				"To'g'ri" if is_correct else "Noto'g'ri",
			]
		)

		detail_rows.append(
			{
				"number": number,
				"question": attempt_question.question,
				"options": options,
				"correct_letter": correct_letter,
				"selected_letter": selected_letter,
				"is_correct": is_correct,
			}
		)

	# =========================================================
	# SHORT RESULT TABLE
	# =========================================================

	story.append(
		Paragraph(
			"QISQA JAVOBLAR NATIJASI",
			heading_style,
		)
	)

	summary_table = Table(
		result_rows,
		colWidths=[
			15 * mm,
			35 * mm,
			35 * mm,
			40 * mm,
		],
		repeatRows=1,
	)

	summary_table.setStyle(
		TableStyle(
			[
				("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
				("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
				("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
				("ALIGN", (0, 0), (-1, -1), "CENTER"),
				("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
				("FONTSIZE", (0, 0), (-1, -1), 9),
				("TOPPADDING", (0, 0), (-1, -1), 5),
				("BOTTOMPADDING", (0, 0), (-1, -1), 5),
			]
		)
	)

	story.append(summary_table)

	story.append(PageBreak())

	# =========================================================
	# FULL QUESTIONS
	# =========================================================

	story.append(
		Paragraph(
			"SAVOLLAR VA VARIANTLAR",
			title_style,
		)
	)

	for item in detail_rows:
		question = item["question"]

		question_text = question.text or ""

		story.append(
			Paragraph(
				f"<b>{item['number']}.</b> {question_text}",
				normal_style,
			)
		)

		story.append(
			Spacer(
				1,
				3 * mm,
			)
		)

		for option in item["options"]:
			choice = option["choice"]

			choice_text = choice.text if choice.text else "[Rasmli javob]"

			letter = option["letter"]

			story.append(
				Paragraph(
					f"<b>{letter}.</b> {choice_text}",
					option_style,
				)
			)

		story.append(
			Spacer(
				1,
				2 * mm,
			)
		)

		story.append(
			Paragraph(
				(f"<b>To'g'ri javob:</b> {item['correct_letter']}"),
				normal_style,
			)
		)

		story.append(
			Paragraph(
				(f"<b>User javobi:</b> {item['selected_letter']}"),
				normal_style,
			)
		)

		story.append(
			Paragraph(
				(
					"<b>Natija:</b> "
					+ ("To'g'ri" if item["is_correct"] else "Noto'g'ri")
				),
				normal_style,
			)
		)

		story.append(
			Spacer(
				1,
				8 * mm,
			)
		)

	doc.build(story)

	buffer.seek(0)

	filename = f"{user.username}-{test.title}-{attempt.pk}.pdf"

	filename = filename.replace(" ", "-").replace("/", "-")

	return FileResponse(
		buffer,
		as_attachment=True,
		filename=filename,
		content_type="application/pdf",
	)
