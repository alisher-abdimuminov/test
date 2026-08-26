import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from questions.models import Choice

from .forms import StartAttemptForm
from .models import AttemptAnswer, AttemptQuestion, TestAssignment, TestAttempt
from .services.generator import InsufficientQuestionsError, create_attempt
from .services.scoring import finish_attempt


def _owned_assignment(user, pk):
	return get_object_or_404(
		TestAssignment.objects.select_related("test", "user"),
		pk=pk,
		user=user,
		is_active=True,
		test__is_active=True,
	)


def _owned_attempt(user, pk):
	return get_object_or_404(
		TestAttempt.objects.select_related(
			"assignment__test", "assignment__user", "speciality", "foreign_language"
		),
		pk=pk,
		assignment__user=user,
	)


@login_required
def dashboard(request):
	now = timezone.now()
	assignments = (
		TestAssignment.objects.filter(
			user=request.user, is_active=True, test__is_active=True
		)
		.select_related("test")
		.order_by("-created_at")
	)
	rows = []
	for assignment in assignments:
		attempt = TestAttempt.objects.filter(assignment=assignment).first()
		available = (
			not assignment.available_from or now >= assignment.available_from
		) and (not assignment.deadline or now <= assignment.deadline)
		rows.append(
			{"assignment": assignment, "attempt": attempt, "available": available}
		)
	return render(
		request,
		"dashboard/index.html",
		{"rows": rows, "start_form": StartAttemptForm()},
	)


@login_required
def start_test(request, assignment_id):
	assignment = _owned_assignment(request.user, assignment_id)
	now = timezone.now()

	existing = TestAttempt.objects.filter(assignment=assignment).first()
	if existing:
		if existing.status == TestAttempt.Status.IN_PROGRESS:
			return redirect("attempt", attempt_id=existing.pk)
		return redirect("result", attempt_id=existing.pk)

	if assignment.available_from and now < assignment.available_from:
		return HttpResponseBadRequest("Test hali ochilmagan.")
	if assignment.deadline and now > assignment.deadline:
		return HttpResponseBadRequest("Test muddati tugagan.")

	form = StartAttemptForm(request.POST or None)
	if request.method == "POST" and form.is_valid():
		try:
			attempt, _ = create_attempt(
				assignment=assignment,
				speciality=form.cleaned_data["speciality"],
				foreign_language=form.cleaned_data["foreign_language"],
			)
		except InsufficientQuestionsError as exc:
			form.add_error(None, str(exc))
		else:
			return redirect("attempt", attempt_id=attempt.pk)

	return render(request, "exams/start.html", {"assignment": assignment, "form": form})


@login_required
def attempt_view(request, attempt_id):
	attempt = _owned_attempt(request.user, attempt_id)

	if attempt.status != TestAttempt.Status.IN_PROGRESS:
		return redirect("result", attempt_id=attempt.pk)

	if timezone.now() >= attempt.expires_at:
		finish_attempt(attempt, expired=True)
		return redirect("result", attempt_id=attempt.pk)

	attempt_questions = list(
		AttemptQuestion.objects.filter(attempt=attempt)
		.select_related("question")
		.prefetch_related("attempt_choices__choice", "answer")
		.order_by("order")
	)

	answered_count = 0
	for aq in attempt_questions:
		try:
			aq.selected_choice_id = aq.answer.selected_choice_id
			answered_count += 1
		except AttemptAnswer.DoesNotExist:
			aq.selected_choice_id = None

	# Eski urinishlar ham avval random tartibda yaratilgan bo‘lishi mumkin.
	# UI doim kategoriyalar bo‘yicha qat’iy tartibda ko‘rsatadi.
	section_defs = [
		("speciality", "Mutaxassislik"),
		("pedagogy", "Pedagogika"),
		("it", "IT"),
		("foreign_language", f"Xorijiy til — {attempt.foreign_language}"),
	]
	sections = []
	display_order = 1
	for category, title in section_defs:
		items = [aq for aq in attempt_questions if aq.question.category == category]
		for aq in items:
			aq.display_order = display_order
			display_order += 1
		sections.append({"title": title, "questions": items})

	return render(
		request,
		"exams/attempt.html",
		{
			"attempt": attempt,
			"attempt_questions": attempt_questions,
			"sections": sections,
			"answered_count": answered_count,
			"unanswered_count": attempt.total_count - answered_count,
		},
	)


@login_required
@require_POST
def save_answer(request, attempt_id):
	attempt = _owned_attempt(request.user, attempt_id)
	if attempt.status != TestAttempt.Status.IN_PROGRESS:
		return JsonResponse({"ok": False, "error": "Test yakunlangan."}, status=409)

	if timezone.now() >= attempt.expires_at:
		finish_attempt(attempt, expired=True)
		return JsonResponse({"ok": False, "expired": True}, status=409)

	try:
		payload = json.loads(request.body)
		aq_id = int(payload["attempt_question_id"])
		choice_id = int(payload["choice_id"])
	except (ValueError, TypeError, KeyError, json.JSONDecodeError):
		return JsonResponse({"ok": False, "error": "Noto‘g‘ri ma'lumot."}, status=400)

	aq = get_object_or_404(AttemptQuestion, pk=aq_id, attempt=attempt)
	valid_choice_ids = aq.attempt_choices.values_list("choice_id", flat=True)
	if choice_id not in valid_choice_ids:
		return JsonResponse(
			{"ok": False, "error": "Javob bu savolga tegishli emas."}, status=400
		)

	choice = get_object_or_404(Choice, pk=choice_id)
	AttemptAnswer.objects.update_or_create(
		attempt_question=aq,
		defaults={"selected_choice": choice},
	)
	answered_count = AttemptAnswer.objects.filter(
		attempt_question__attempt=attempt
	).count()
	return JsonResponse({"ok": True, "answered_count": answered_count})


@login_required
@require_POST
def finish_test(request, attempt_id):
	attempt = _owned_attempt(request.user, attempt_id)
	expired = timezone.now() >= attempt.expires_at
	finish_attempt(attempt, expired=expired)
	return redirect("result", attempt_id=attempt.pk)


@login_required
def result_view(request, attempt_id):
	attempt = _owned_attempt(request.user, attempt_id)
	if attempt.status == TestAttempt.Status.IN_PROGRESS:
		if timezone.now() >= attempt.expires_at:
			attempt = finish_attempt(attempt, expired=True)
		else:
			return redirect("attempt", attempt_id=attempt.pk)

	category_stats = []
	for category, label in [
		("speciality", "Mutaxassislik"),
		("pedagogy", "Pedagogika"),
		("it", "IT"),
		("foreign_language", "Xorijiy til"),
	]:
		qs = AttemptQuestion.objects.filter(
			attempt=attempt, question__category=category
		)
		total = qs.count()
		correct = AttemptAnswer.objects.filter(
			attempt_question__in=qs,
			selected_choice__is_correct=True,
		).count()
		category_stats.append({"label": label, "correct": correct, "total": total})

	return render(
		request,
		"exams/result.html",
		{"attempt": attempt, "category_stats": category_stats},
	)
