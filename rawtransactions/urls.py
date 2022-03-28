from django.urls import path

from .views import (
    CreateFormula,
    CreateRawProduct,
    CreateRawTransaction,
    ListFormula,
    ListRawProducts,
    RawReturnView,
)

urlpatterns = [
    # -----------------Raw Transaction--------------------- #
    path("transaction/create/", CreateRawTransaction.as_view()),
    path("transaction/return/", RawReturnView.as_view()),
    # -----------------Formula--------------------- #
    path("formula/list/", ListFormula.as_view()),
    path("formula/create/", CreateFormula.as_view()),
    # -----------------Raw Product--------------------- #
    path("product/list/", ListRawProducts.as_view()),
    path("product/create/", CreateRawProduct.as_view()),
]
