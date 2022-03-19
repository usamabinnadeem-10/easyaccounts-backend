from django.urls import path

from .views import *

urlpatterns = [
    path("person/create/", CreatePerson.as_view()),
    path("person/list/", ListPerson.as_view()),
    path("product/create/", CreateProduct.as_view()),
    path("product/list/", ListProduct.as_view()),
    path("warehouse/create/", CreateWarehouse.as_view()),
    path("warehouse/list/", ListWarehouse.as_view()),
    path("account-type/create/", CreateAccountType.as_view()),
    path("account-type/list/", ListAccountType.as_view()),
    path("area/create/", CreateArea.as_view()),
    path("area/list/", ListArea.as_view()),
    path("daybook/", DayBook.as_view()),
    path("stock-quantity/", GetStockQuantity.as_view()),
    path("account-history/", GetAccountHistory.as_view()),
    path("create-opening-stock/", CreateOpeningStock.as_view()),
]
