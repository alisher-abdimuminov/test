from django import forms

from .models import ForeignLanguage, Question, Speciality


class BulkQuestionImportForm(forms.Form):
	category = forms.ChoiceField(label="Kategoriya", choices=Question.Category.choices)
	speciality = forms.ModelChoiceField(
		label="Mutaxassislik",
		queryset=Speciality.objects.filter(is_active=True),
		required=False,
	)
	foreign_language = forms.ModelChoiceField(
		label="Xorijiy til",
		queryset=ForeignLanguage.objects.filter(is_active=True),
		required=False,
	)
	content = forms.CharField(
		label="Savollar",
		widget=forms.Textarea(
			attrs={"rows": 24, "style": "width: 100%; font-family: monospace;"}
		),
		help_text="Savollar bo‘sh qator bilan ajratiladi. To‘g‘ri javob # bilan boshlanadi.",
	)

	def clean(self):
		cleaned = super().clean()
		category = cleaned.get("category")
		speciality = cleaned.get("speciality")
		language = cleaned.get("foreign_language")

		if category == Question.Category.SPECIALITY and not speciality:
			self.add_error("speciality", "Mutaxassislikni tanlang.")
		if category != Question.Category.SPECIALITY:
			cleaned["speciality"] = None

		if category == Question.Category.FOREIGN_LANGUAGE and not language:
			self.add_error("foreign_language", "Xorijiy tilni tanlang.")
		if category != Question.Category.FOREIGN_LANGUAGE:
			cleaned["foreign_language"] = None

		return cleaned
