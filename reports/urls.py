from django.urls import path

from .views import BalanceSheet

urlpatterns = [
    path("balance-sheet/", BalanceSheet.as_view()),
]
