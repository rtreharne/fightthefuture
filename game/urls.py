from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("join", views.join_view, name="join"),
    path("play/<int:user_id>", views.play_view, name="play"),
    path("play/<int:user_id>/dataset/<int:stage>", views.dataset_download_view, name="dataset-download"),
    path("podium", views.podium_view, name="podium"),
    path("teacher", views.teacher_view, name="teacher"),
]
