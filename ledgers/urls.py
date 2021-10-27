from django.urls import path

from .views import *

urlpatterns = [
    path("", CreateOrListLedgerDetail.as_view()),
    path("<uuid:pk>/", EditUpdateDeleteLedgerDetail.as_view()),
]
