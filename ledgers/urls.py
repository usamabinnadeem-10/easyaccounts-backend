from django.urls import path

from .views import *

urlpatterns = [
    path("", LedgerDetail.as_view()),
    path("<uuid:pk>/", LedgerDetail.as_view()),
]
