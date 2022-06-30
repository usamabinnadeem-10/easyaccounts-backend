from django.urls import path

from .views import (
    EditUpdateDeleteLedgerDetail,
    FilterLedger,
    GetAllBalances,
    LedgerAndDetailEntry,
    ListLedger,
)

urlpatterns = [
    path("", ListLedger.as_view()),
    path("ledger-entry/create/", LedgerAndDetailEntry.as_view()),
    path("ledger-entry/edit/<uuid:pk>/", LedgerAndDetailEntry.as_view()),
    path("ledger-entry/delete/<uuid:pk>/", EditUpdateDeleteLedgerDetail.as_view()),
    path("balances/all/", GetAllBalances.as_view()),
    path("search/", FilterLedger.as_view()),
]
