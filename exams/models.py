from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from questions.models import ForeignLanguage, Question, Speciality


class Test(models.Model):
	title = models.CharField("Test nomi", max_length=255)
	duration_minutes = models.PositiveIntegerField("Davomiyligi (daqiqa)", default=60)
	speciality_count = models.PositiveIntegerField(
		"Mutaxassislik savollari", default=30
	)
	pedagogy_count = models.PositiveIntegerField("Pedagogika savollari", default=10)
	it_count = models.PositiveIntegerField("IT savollari", default=5)
	language_count = models.PositiveIntegerField("Xorijiy til savollari", default=5)
	is_active = models.BooleanField("Faol", default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = "Test"
		verbose_name_plural = "Testlar"

	@property
	def total_questions(self):
		return (
			self.speciality_count
			+ self.pedagogy_count
			+ self.it_count
			+ self.language_count
		)

	def __str__(self):
		return self.title


class TestAssignment(models.Model):
	class Status(models.TextChoices):
		passed = "p", "P"
		failed = "f", "f"
		default = "d", "d"

	test = models.ForeignKey(Test, on_delete=models.PROTECT, related_name="assignments")
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="test_assignments",
	)
	status = models.CharField(
		max_length=100, choices=Status.choices, default=Status.default
	)
	available_from = models.DateTimeField("Boshlanish vaqti", blank=True, null=True)
	deadline = models.DateTimeField("Oxirgi muddat", blank=True, null=True)
	is_active = models.BooleanField("Faol", default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = "Test biriktirish"
		verbose_name_plural = "Test biriktirishlar"
		constraints = [
			models.UniqueConstraint(
				fields=["test", "user"], name="unique_test_assignment_per_user"
			)
		]

	def clean(self):
		if (
			self.available_from
			and self.deadline
			and self.available_from >= self.deadline
		):
			raise ValidationError(
				"Oxirgi muddat boshlanish vaqtidan keyin bo‘lishi kerak."
			)

	def __str__(self):
		return f"{self.user} — {self.test}"


class TestAttempt(models.Model):
	class Status(models.TextChoices):
		IN_PROGRESS = "in_progress", "Jarayonda"
		FINISHED = "finished", "Yakunlangan"
		EXPIRED = "expired", "Vaqt tugagan"

	assignment = models.OneToOneField(
		TestAssignment, on_delete=models.CASCADE, related_name="attempt"
	)
	speciality = models.ForeignKey(Speciality, on_delete=models.PROTECT)
	foreign_language = models.ForeignKey(ForeignLanguage, on_delete=models.PROTECT)
	started_at = models.DateTimeField()
	expires_at = models.DateTimeField()
	submitted_at = models.DateTimeField(blank=True, null=True)
	status = models.CharField(
		max_length=20, choices=Status.choices, default=Status.IN_PROGRESS
	)
	score = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
	correct_count = models.PositiveIntegerField(default=0)
	total_count = models.PositiveIntegerField(default=0)

	class Meta:
		verbose_name = "Test natijasi"
		verbose_name_plural = "Test natijalari"
		ordering = ["-started_at"]

	def __str__(self):
		return f"{self.assignment.user} — {self.assignment.test}"


class AttemptQuestion(models.Model):
	attempt = models.ForeignKey(
		TestAttempt, on_delete=models.CASCADE, related_name="attempt_questions"
	)
	question = models.ForeignKey(Question, on_delete=models.PROTECT)
	order = models.PositiveIntegerField()

	class Meta:
		ordering = ["order"]
		constraints = [
			models.UniqueConstraint(
				fields=["attempt", "question"], name="unique_question_per_attempt"
			),
			models.UniqueConstraint(
				fields=["attempt", "order"], name="unique_question_order_per_attempt"
			),
		]

	def __str__(self):
		return f"{self.attempt_id} / {self.order}"


class AttemptChoice(models.Model):
	attempt_question = models.ForeignKey(
		AttemptQuestion, on_delete=models.CASCADE, related_name="attempt_choices"
	)
	choice = models.ForeignKey("questions.Choice", on_delete=models.PROTECT)
	order = models.PositiveIntegerField()

	class Meta:
		ordering = ["order"]
		constraints = [
			models.UniqueConstraint(
				fields=["attempt_question", "choice"],
				name="unique_choice_per_attempt_question",
			),
			models.UniqueConstraint(
				fields=["attempt_question", "order"],
				name="unique_choice_order_per_attempt_question",
			),
		]


class AttemptAnswer(models.Model):
	attempt_question = models.OneToOneField(
		AttemptQuestion, on_delete=models.CASCADE, related_name="answer"
	)
	selected_choice = models.ForeignKey("questions.Choice", on_delete=models.PROTECT)
	answered_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = "Tanlangan javob"
		verbose_name_plural = "Tanlangan javoblar"
