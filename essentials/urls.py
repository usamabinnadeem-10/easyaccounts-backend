from django.urls import path

from .views import *

urlpatterns = [
    path("person/create/", CreateAndListPerson.as_view()),
    path("person/list/", CreateAndListPerson.as_view()),

    path("product/create/", CreateAndListProduct.as_view()),
    path("product/list/", CreateAndListProduct.as_view()),

    path("warehouse/create/", CreateAndListWarehouse.as_view()),
    path("warehouse/list/", CreateAndListWarehouse.as_view()),

    path("account-type/create/", CreateAndListAccountType.as_view()),
    path("account-type/list/", CreateAndListAccountType.as_view()),

    path("daybook/", DayBook.as_view()),

    path("stock-quantity/", GetStockQuantity.as_view()),
]
