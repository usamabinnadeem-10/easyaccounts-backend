from django.urls import path

from .views import (
    CreateRawTransaction,
    ListFormula,
    CreateFormula,
    ListRawProducts,
    CreateRawProduct,
)

urlpatterns = [
    path("transaction/create/", CreateRawTransaction.as_view()),
    # -----------------Formula--------------------- #
    path("formula/list/", ListFormula.as_view()),
    path("formula/create/", CreateFormula.as_view()),
    # -----------------Raw Product--------------------- #
    path("product/list/", ListRawProducts.as_view()),
    path("product/create/", CreateRawProduct.as_view()),
]
