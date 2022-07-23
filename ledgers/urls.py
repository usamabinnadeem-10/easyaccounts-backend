from django.urls import path

from .views import (
    DeleteLedgerDetail,
    FilterLedger,
    GetAllBalances,
    LedgerAndDetailEntry,
    ListLedger,
    UpdateLedgerAndDetailEntry,
)

urlpatterns = [
    path("", ListLedger.as_view()),
    path("ledger-entry/create/", LedgerAndDetailEntry.as_view()),
    path("ledger-entry/edit/<uuid:pk>/", UpdateLedgerAndDetailEntry.as_view()),
    path("ledger-entry/delete/<uuid:pk>/", DeleteLedgerDetail.as_view()),
    path("balances/all/", GetAllBalances.as_view()),
    path("search/", FilterLedger.as_view()),
]
