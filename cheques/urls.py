from django.urls import path

from .views import *

urlpatterns = [
    path("external/create/", CreateExternalChequeEntryView.as_view()),
    path("external/create/cheque-history/", CreateExternalChequeHistoryView.as_view()),
    path(
        "external/create/cheque-history-with-cheque/",
        CreateExternalChequeHistoryWithChequeView.as_view(),
    ),
    path("external/list/", ListExternalCheques.as_view()),
    path("external/list/cheque-history/", GetExternalChequeHistory.as_view()),
    path("external/pass/", PassExternalChequeView.as_view()),
    path("external/complete-history/", CompleteExternalChequeWithHistory.as_view()),
    path("external/transfer/", TransferExternalChequeView.as_view()),
    path(
        "external/complete-transfer/<uuid:pk>/",
        CompleteExternalTransferChequeView.as_view(),
    ),
    path("external/transfer/return/", ReturnExternalTransferredCheque.as_view()),
    path("external/return/", ReturnExternalCheque.as_view()),
    path("external/delete/<uuid:pk>/", DeleteExternalChequeView.as_view()),
    # ---------------------------------PERSONAL APIS-------------------------------
    path("personal/issue/", IssuePersonalChequeView.as_view()),
    path("personal/return/", ReturnPersonalChequeView.as_view()),
    path("personal/return/reissue/", ReIssuePersonalChequeFromReturnedView.as_view()),
    path("personal/pass/<uuid:pk>/", PassPersonalChequeView.as_view()),
    path("personal/cancel/<uuid:pk>/", CancelPersonalChequeView.as_view()),
    path("personal/list/", ListPersonalChequeView.as_view()),
    path("personal/delete/<uuid:pk>/", DeletePersonalChequeView.as_view()),
]
