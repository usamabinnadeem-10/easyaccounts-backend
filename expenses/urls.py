from django.urls import path

from .views import (
    CreateExpenseAccount,
    CreateExpenseDetail,
    EditUpdateDeleteExpenseDetail,
)

urlpatterns = [
    path("<uuid:pk>/", EditUpdateDeleteExpenseDetail.as_view()),
    path("account/", CreateExpenseAccount.as_view()),
    path("detail/", CreateExpenseDetail.as_view()),
]
