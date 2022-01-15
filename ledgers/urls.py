from django.urls import path

from .views import *

urlpatterns = [
    path("", CreateOrListLedgerDetail.as_view()),
    path("<uuid:pk>/", EditUpdateDeleteLedgerDetail.as_view()),
    path("balances/all/", GetAllBalances.as_view()),
    path("search/", FilterLedger.as_view()),
]
