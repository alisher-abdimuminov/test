from django.urls import path

from . import views

urlpatterns = [
	path("", views.dashboard, name="dashboard"),
	path("tests/<int:assignment_id>/start/", views.start_test, name="start_test"),
	path("attempts/<int:attempt_id>/", views.attempt_view, name="attempt"),
	path("attempts/<int:attempt_id>/answer/", views.save_answer, name="save_answer"),
	path("attempts/<int:attempt_id>/finish/", views.finish_test, name="finish_test"),
	path("attempts/<int:attempt_id>/result/", views.result_view, name="result"),
]
