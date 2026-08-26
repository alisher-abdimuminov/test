from django import forms

from questions.models import ForeignLanguage, Speciality


class StartAttemptForm(forms.Form):
	speciality = forms.ModelChoiceField(
		label="Mutaxassislik",
		queryset=Speciality.objects.filter(is_active=True),
		empty_label="Mutaxassislikni tanlang",
	)
	foreign_language = forms.ModelChoiceField(
		label="Xorijiy til",
		queryset=ForeignLanguage.objects.filter(is_active=True),
		empty_label="Xorijiy tilni tanlang",
	)
