from django.urls import path

from .views import *

urlpatterns = [
    path("", CreateTransaction.as_view()),
    path("<uuid:pk>/", CreateTransaction.as_view()),
    path("product-quantity/", GetProductQuantity.as_view()),
]
