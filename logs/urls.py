from django.urls import path

from .views import LogView

urlpatterns = [
    path("person/create/", LogView.as_view()),
]
