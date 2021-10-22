from django.urls import path

from .views import *

urlpatterns = [
    path("person/", CreateAndListPerson.as_view()),
    path("product-head/", CreateAndListProductHead.as_view()),
    path("product/", CreateAndListProduct.as_view()),
    path("warehouse/", CreateAndListWarehouse.as_view()),
    path("account-type/", CreateAndListAccountType.as_view()),
    path("daybook/", DayBook.as_view()),
]
