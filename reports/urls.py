from django.urls import path

from .views import BalanceSheet, IncomeStatement

urlpatterns = [
    path("balance-sheet/", BalanceSheet.as_view()),
    path("income-statement/", IncomeStatement.as_view()),
]
