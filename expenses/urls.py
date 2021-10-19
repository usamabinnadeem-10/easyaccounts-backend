from django.urls import path

from .views import CreateExpenseAccount, CreateExpenseDetail

urlpatterns = [
    path("account/create/", CreateExpenseAccount.as_view()),
    path("detail/create/", CreateExpenseDetail.as_view()),
]
