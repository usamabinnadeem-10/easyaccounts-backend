from django.urls import path

from .views import *

urlpatterns = [
    path('person/', PersonList.as_view()),
    path('product/', ProductList.as_view()),
    path('warehouse/', WarehouseList.as_view()),
    path('account-type/', AccountTypeList.as_view()),
]