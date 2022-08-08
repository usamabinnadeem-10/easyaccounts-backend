from django.urls import path

from .views import LogView

urlpatterns = [
    path("list/", LogView.as_view()),
]
