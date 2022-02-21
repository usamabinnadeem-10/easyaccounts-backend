from django.urls import path

from .views import *

urlpatterns = [
    path("create/", CreateExternalChequeEntryView.as_view()),
    path("create/cheque-history/", CreateExternalChequeHistoryView.as_view()),
    path(
        "create/cheque-history-with-cheque/",
        CreateExternalChequeHistoryWithChequeView.as_view(),
    ),
    path("list/cheque-history/", GetExternalChequeHistory.as_view()),
    path("pass/", PassExternalChequeView.as_view()),
    path("transfer/", TransferExternalChequeView.as_view()),
    path("transfer/return/", ReturnExternalTransferredCheque.as_view()),
    path("return/", ReturnExternalCheque.as_view()),
]
