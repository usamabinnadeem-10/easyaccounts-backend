from django.urls import path

from .views import (
    CreateExpenseAccount,
    CreateExpenseDetail,
    DeleteExpenseDetail,
    EditExpenseDetail,
    ListExpenseAccount,
    ListExpenseDetail,
    ViewSingleExpense,
)

urlpatterns = [
    path("<uuid:pk>/", EditExpenseDetail.as_view()),
    path("<uuid:pk>/", DeleteExpenseDetail.as_view()),
    path("<uuid:pk>/", ViewSingleExpense.as_view()),
    path("account/create/", CreateExpenseAccount.as_view()),
    path("account/list/", ListExpenseAccount.as_view()),
    path("detail/create/", CreateExpenseDetail.as_view()),
    path("detail/list/", ListExpenseDetail.as_view()),
]
