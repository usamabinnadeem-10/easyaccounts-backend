from django.urls import path

from .views import *

urlpatterns = [
    path("", GetOrCreateTransaction.as_view()),
    path("<uuid:pk>/", EditUpdateDeleteTransaction.as_view()),
    path("search/", FilterTransactions.as_view()),
    path("product-performance-history/", ProductPerformanceHistory.as_view()),
    path("business-performance-history/", BusinessPerformanceHistory.as_view()),
    path("transfer-stock/", TransferStock.as_view()),
    path("cancel-invoice/", CancelInvoice.as_view()),
    path("detailed-stock/", DetailedStockView.as_view()),
    path("view-transfers/", ViewTransfers.as_view()),
]
