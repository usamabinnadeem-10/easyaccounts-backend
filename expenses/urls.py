from django.urls import path

from .views import (
    CreateExpenseAccount,
    CreateExpenseDetail,
    EditUpdateDeleteExpenseDetail,
)

urlpatterns = [
    path("<uuid:pk>/", EditUpdateDeleteExpenseDetail.as_view()),
    path("account/create/", CreateExpenseAccount.as_view()),
    path("account/list/", CreateExpenseAccount.as_view()),
    path("detail/create/", CreateExpenseDetail.as_view()),
    path("detail/list/", CreateExpenseDetail.as_view()),
]
