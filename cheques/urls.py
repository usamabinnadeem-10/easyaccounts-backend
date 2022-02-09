from django.urls import path

from .views import *

urlpatterns = [
    path("create/", CreateChequeEntryView.as_view()),
    path("create/cheque-history/", CreateChequeHistoryView.as_view()),
    path(
        "create/cheque-history-with-cheque/",
        CreateChequeHistoryWithChequeView.as_view(),
    ),
    path("list/cheque-history/", GetChequeHistory.as_view()),
]
