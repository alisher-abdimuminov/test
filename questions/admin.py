from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .forms import BulkQuestionImportForm
from .models import Choice, ForeignLanguage, Question, Speciality
from .services.importer import QuestionImportError, create_questions, parse_questions


@admin.register(Speciality)
class SpecialityAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(ForeignLanguage)
class ForeignLanguageAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


class ChoiceInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        correct = 0
        valid_choices = 0
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            if form.cleaned_data.get("text") or form.cleaned_data.get("image"):
                valid_choices += 1
                if form.cleaned_data.get("is_correct"):
                    correct += 1
        if valid_choices < 2:
            raise ValidationError("Kamida 2 ta javob varianti bo‘lishi kerak.")
        if correct != 1:
            raise ValidationError("Aynan 1 ta javob to‘g‘ri deb belgilanishi kerak.")


class ChoiceInline(admin.TabularInline):
    model = Choice
    formset = ChoiceInlineFormSet
    extra = 4
    min_num = 2
    fields = ("text", "image", "is_correct")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    change_list_template = "admin/questions/question/change_list.html"
    list_display = (
        "short_text",
        "category",
        "speciality",
        "foreign_language",
        "is_active",
    )
    list_filter = ("category", "speciality", "foreign_language", "is_active")
    search_fields = ("text",)
    inlines = [ChoiceInline]

    def short_text(self, obj):
        return obj.text[:80]

    short_text.short_description = "Savol"

    def get_urls(self):
        return [
            path(
                "import/",
                self.admin_site.admin_view(self.bulk_import_view),
                name="questions_question_import",
            )
        ] + super().get_urls()

    def bulk_import_view(self, request):
        form = BulkQuestionImportForm(request.POST or None)
        preview = None

        if request.method == "POST" and form.is_valid():
            try:
                parsed = parse_questions(form.cleaned_data["content"])
            except QuestionImportError as exc:
                form.add_error("content", str(exc))
            else:
                preview = parsed
                if "import" in request.POST:
                    created = create_questions(
                        parsed=parsed,
                        category=form.cleaned_data["category"],
                        speciality=form.cleaned_data["speciality"],
                        foreign_language=form.cleaned_data["foreign_language"],
                    )
                    self.message_user(
                        request,
                        f"{len(created)} ta savol muvaffaqiyatli yaratildi.",
                        messages.SUCCESS,
                    )
                    return redirect(reverse("admin:questions_question_changelist"))

        context = {
            **self.admin_site.each_context(request),
            "title": "Savollarni ommaviy import qilish",
            "form": form,
            "preview": preview,
            "opts": self.model._meta,
        }
        return render(request, "admin/questions/question/import.html", context)
