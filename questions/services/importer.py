from dataclasses import dataclass

from django.db import transaction

from questions.models import Choice, Question


class QuestionImportError(ValueError):
    pass


@dataclass
class ParsedChoice:
    text: str
    is_correct: bool


@dataclass
class ParsedQuestion:
    text: str
    choices: list[ParsedChoice]


def parse_questions(raw_text: str) -> list[ParsedQuestion]:
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise QuestionImportError("Matn bo‘sh.")

    blocks = [block.strip() for block in normalized.split("\n\n") if block.strip()]
    parsed: list[ParsedQuestion] = []

    for number, block in enumerate(blocks, start=1):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3:
            raise QuestionImportError(
                f"{number}-savol: kamida savol va 2 ta javob varianti bo‘lishi kerak."
            )

        question_text = lines[0]
        choices: list[ParsedChoice] = []
        correct_count = 0

        for line in lines[1:]:
            is_correct = line.startswith("#")
            text = line[1:].strip() if is_correct else line
            if not text:
                raise QuestionImportError(
                    f"{number}-savol: bo‘sh javob varianti topildi."
                )
            if is_correct:
                correct_count += 1
            choices.append(ParsedChoice(text=text, is_correct=is_correct))

        if correct_count != 1:
            raise QuestionImportError(
                f"{number}-savol: aynan 1 ta javob # bilan to‘g‘ri deb belgilanishi kerak."
            )

        parsed.append(ParsedQuestion(text=question_text, choices=choices))

    return parsed


@transaction.atomic
def create_questions(*, parsed, category, speciality=None, foreign_language=None):
    created = []
    for item in parsed:
        question = Question.objects.create(
            text=item.text,
            category=category,
            speciality=speciality,
            foreign_language=foreign_language,
        )
        Choice.objects.bulk_create(
            [
                Choice(
                    question=question,
                    text=choice.text,
                    is_correct=choice.is_correct,
                )
                for choice in item.choices
            ]
        )
        created.append(question)
    return created
