from django.urls import path

from .views import (
    BusinessPerformanceHistory,
    CreateTransaction,
    DeleteTransaction,
    DeleteTransferStock,
    DetailedStockView,
    EditRetrieveTransaction,
    EditTransferStock,
    FilterTransactions,
    GetTransaction,
    TransferStock,
    ViewAllStock,
    ViewTransfers,
)

urlpatterns = [
    path("create/", CreateTransaction.as_view()),
    path("list/", GetTransaction.as_view()),
    path("<uuid:pk>/", EditRetrieveTransaction.as_view()),
    path("<uuid:pk>/", DeleteTransaction.as_view()),
    path("search/", FilterTransactions.as_view()),
    path("business-performance-history/", BusinessPerformanceHistory.as_view()),
    path("detailed-stock/", DetailedStockView.as_view()),
    # // ---------Stock transfer----------  //
    path("transfer-stock/", TransferStock.as_view()),
    path("transfer-stock/delete/<uuid:pk>/", DeleteTransferStock.as_view()),
    path("transfer-stock/update/<uuid:pk>/", EditTransferStock.as_view()),
    path("view-transfers/", ViewTransfers.as_view()),
    # // ---------Stock------------------- //
    path("all-stock/", ViewAllStock.as_view()),
]
