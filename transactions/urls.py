from django.urls import path

from .views import CreateTransaction

urlpatterns = [path("", CreateTransaction.as_view())]
