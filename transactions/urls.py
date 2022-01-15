from django.urls import path

from .views import *

urlpatterns = [
    path("", GetOrCreateTransaction.as_view()),
    path("<uuid:pk>/", EditUpdateDeleteTransaction.as_view()),
]
