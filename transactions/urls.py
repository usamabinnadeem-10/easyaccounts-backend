from django.urls import path

from .views import *

urlpatterns = [
    path("", GetOrCreateTransaction.as_view()),
    path("<uuid:pk>/", EditUpdateDeleteTransaction.as_view()),
    path("product-quantity/", GetProductQuantity.as_view()),
    path("product-quantity/all/", GetAllQuantity.as_view()),
    path("product-quantity-by-warehouse/all/", GetAllQuantityByWarehouse.as_view()),
]
