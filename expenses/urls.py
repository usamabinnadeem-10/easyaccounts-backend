from django.urls import path

from .views import (
    CreateExpenseAccount,
    CreateExpenseDetail,
    EditUpdateDeleteExpenseDetail,
    ListExpenseAccount,
    ListExpenseDetail,
)

urlpatterns = [
    path("<uuid:pk>/", EditUpdateDeleteExpenseDetail.as_view()),
    path("account/create/", CreateExpenseAccount.as_view()),
    path("account/list/", ListExpenseAccount.as_view()),
    path("detail/create/", CreateExpenseDetail.as_view()),
    path("detail/list/", ListExpenseDetail.as_view()),
]
