from django.urls import path

from .views import (
    EditUpdateDeleteLedgerDetail,
    FilterLedger,
    GetAllBalances,
    ListLedger,
)

urlpatterns = [
    path("", ListLedger.as_view()),
    path("<uuid:pk>/", EditUpdateDeleteLedgerDetail.as_view()),
    path("balances/all/", GetAllBalances.as_view()),
    path("search/", FilterLedger.as_view()),
]
