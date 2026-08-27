from django.contrib import admin

from reports.pdf import build_attempts_pdf_response

from .models import (
	AttemptAnswer,
	AttemptChoice,
	AttemptQuestion,
	Test,
	TestAssignment,
	TestAttempt,
)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
	list_display = (
		"title",
		"duration_minutes",
		"speciality_count",
		"pedagogy_count",
		"it_count",
		"language_count",
		"total_questions_display",
		"is_active",
	)
	list_filter = ("is_active",)
	search_fields = ("title",)

	def total_questions_display(self, obj):
		return obj.total_questions

	total_questions_display.short_description = "Jami"


@admin.register(TestAssignment)
class TestAssignmentAdmin(admin.ModelAdmin):
	list_display = (
		"user",
		"test",
		"available_from",
		"deadline",
		"is_active",
		"created_at",
	)
	list_filter = ("test", "is_active", "created_at")
	search_fields = (
		"user__username",
		"user__first_name",
		"user__last_name",
		"test__title",
	)
	autocomplete_fields = ("user", "test")


@admin.action(description="Tanlangan natijalarni PDF qilish")
def export_results_pdf(modeladmin, request, queryset):
	queryset = queryset.select_related(
		"assignment__user", "assignment__test", "speciality", "foreign_language"
	).order_by("-score")
	return build_attempts_pdf_response(queryset)


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
	list_display = (
		"user_display",
		"test_display",
		"speciality",
		"foreign_language",
		"status",
		"correct_count",
		"total_count",
		"score",
		"started_at",
		"submitted_at",
	)
	list_filter = (
		"status",
		"assignment__test",
		"speciality",
		"foreign_language",
		"started_at",
	)
	search_fields = (
		"assignment__user__username",
		"assignment__user__full_name",
		"assignment__test__title",
	)
	actions = [export_results_pdf]
	# readonly_fields = (
	# 	"assignment",
	# 	"speciality",
	# 	"foreign_language",
	# 	"started_at",
	# 	"expires_at",
	# 	"submitted_at",
	# 	"status",
	# 	"score",
	# 	"correct_count",
	# 	"total_count",
	# )

	def has_add_permission(self, request):
		return False

	def user_display(self, obj):
		return obj.assignment.user

	user_display.short_description = "User"

	def test_display(self, obj):
		return obj.assignment.test

	test_display.short_description = "Test"


admin.site.register(AttemptQuestion)
admin.site.register(AttemptChoice)
admin.site.register(AttemptAnswer)
