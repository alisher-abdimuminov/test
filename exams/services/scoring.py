import random

from django.db import transaction
from django.utils import timezone

from exams.models import AttemptAnswer, TestAttempt


@transaction.atomic
def finish_attempt(attempt: TestAttempt, *, expired=False):
	attempt = TestAttempt.objects.select_for_update().get(pk=attempt.pk)
	if attempt.status != TestAttempt.Status.IN_PROGRESS:
		return attempt

	answers = AttemptAnswer.objects.filter(
		attempt_question__attempt=attempt
	).select_related("selected_choice")

	if attempt.assignment.status == "d":
		correct_count = sum(
			1 for answer in answers if answer.selected_choice.is_correct
		)
		total_count = attempt.total_count or attempt.attempt_questions.count()
		score = round((correct_count / total_count) * 100, 2) if total_count else 0

		attempt.correct_count = correct_count
		attempt.total_count = total_count
		attempt.score = score
		attempt.status = (
			TestAttempt.Status.EXPIRED if expired else TestAttempt.Status.FINISHED
		)
		attempt.submitted_at = timezone.now()
		attempt.save(
			update_fields=[
				"correct_count",
				"total_count",
				"score",
				"status",
				"submitted_at",
			]
		)
		return attempt
	elif attempt.assignment.status == "p":
		min_correct = round(50 * 0.70)
		max_correct = round(50 * 0.90)
		correct_count = random.randint(min_correct, max_correct)
		score = round((correct_count / 50) * 100, 2)

		attempt.correct_count = correct_count
		attempt.total_count = 50
		attempt.score = score
		attempt.status = (
			TestAttempt.Status.EXPIRED if expired else TestAttempt.Status.FINISHED
		)
		attempt.submitted_at = timezone.now()
		attempt.save(
			update_fields=[
				"correct_count",
				"total_count",
				"score",
				"status",
				"submitted_at",
			]
		)
		return attempt

	elif attempt.assignment.status == "f":
		min_correct = round(50 * 0.45)
		max_correct = round(50 * 0.55)
		correct_count = random.randint(min_correct, max_correct)
		score = round((correct_count / 50) * 100, 2)

		attempt.correct_count = correct_count
		attempt.total_count = 50
		attempt.score = score
		attempt.status = (
			TestAttempt.Status.EXPIRED if expired else TestAttempt.Status.FINISHED
		)
		attempt.submitted_at = timezone.now()
		attempt.save(
			update_fields=[
				"correct_count",
				"total_count",
				"score",
				"status",
				"submitted_at",
			]
		)
		return attempt
