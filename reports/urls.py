from django.urls import path

from .views import (
    BalanceSheet,
    GetAllBalances,
    GetLowStock,
    IncomeStatement,
    ProductPerformanceHistory,
    RevenueByPeriod,
)

urlpatterns = [
    path("balance-sheet/", BalanceSheet.as_view()),
    path("income-statement/", IncomeStatement.as_view()),
    path("all-balances/", GetAllBalances.as_view()),
    path("get-low-stock/", GetLowStock.as_view()),
    path("product-performance-history/", ProductPerformanceHistory.as_view()),
    path("revenue-by-period/", RevenueByPeriod.as_view()),
]
