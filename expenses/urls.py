from django.urls import path

from .views import CreateExpenseAccount, CreateExpenseDetail

urlpatterns = [
    path("account/", CreateExpenseAccount.as_view()),
    path("detail/", CreateExpenseDetail.as_view()),
]
