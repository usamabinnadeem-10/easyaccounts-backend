from django.urls import path

from .views import CreatePaymentView, ListPaymentView

urlpatterns = [
    path("create/", CreatePaymentView.as_view()),
    path("list/", ListPaymentView.as_view()),
]
