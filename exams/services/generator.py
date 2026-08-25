import random
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from exams.models import AttemptChoice, AttemptQuestion, TestAttempt
from questions.models import Question


class InsufficientQuestionsError(ValueError):
    pass


def _pick(queryset, count, label):
    ids = list(queryset.values_list("id", flat=True))
    if len(ids) < count:
        raise InsufficientQuestionsError(
            f"{label}: kerak {count} ta, bazada esa {len(ids)} ta faol savol bor."
        )
    return random.sample(ids, count)


@transaction.atomic
def create_attempt(*, assignment, speciality, foreign_language):
    existing = TestAttempt.objects.filter(assignment=assignment).first()
    if existing:
        return existing, False

    test = assignment.test
    now = timezone.now()

    speciality_ids = _pick(
        Question.objects.filter(
            category=Question.Category.SPECIALITY,
            speciality=speciality,
            is_active=True,
        ),
        test.speciality_count,
        "Mutaxassislik",
    )
    pedagogy_ids = _pick(
        Question.objects.filter(category=Question.Category.PEDAGOGY, is_active=True),
        test.pedagogy_count,
        "Pedagogika",
    )
    it_ids = _pick(
        Question.objects.filter(category=Question.Category.IT, is_active=True),
        test.it_count,
        "IT",
    )
    language_ids = _pick(
        Question.objects.filter(
            category=Question.Category.FOREIGN_LANGUAGE,
            foreign_language=foreign_language,
            is_active=True,
        ),
        test.language_count,
        "Xorijiy til",
    )

    # Kategoriyalar qat'iy tartibda saqlanadi: Mutaxassislik → Pedagogika → IT → Xorijiy til.
    # Har bir kategoriya ichidagi savollar _pick() sabab tasodifiy tanlanadi.
    question_ids = speciality_ids + pedagogy_ids + it_ids + language_ids

    attempt = TestAttempt.objects.create(
        assignment=assignment,
        speciality=speciality,
        foreign_language=foreign_language,
        started_at=now,
        expires_at=now + timedelta(minutes=test.duration_minutes),
        total_count=len(question_ids),
    )

    questions = Question.objects.in_bulk(question_ids)
    for index, question_id in enumerate(question_ids, start=1):
        aq = AttemptQuestion.objects.create(
            attempt=attempt,
            question=questions[question_id],
            order=index,
        )
        choice_ids = list(questions[question_id].choices.values_list("id", flat=True))
        random.shuffle(choice_ids)
        AttemptChoice.objects.bulk_create(
            [
                AttemptChoice(attempt_question=aq, choice_id=choice_id, order=order)
                for order, choice_id in enumerate(choice_ids, start=1)
            ]
        )

    return attempt, True
