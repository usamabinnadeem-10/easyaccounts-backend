from django.urls import path

from .views import *

urlpatterns = [
    path('account/', AccountList.as_view()),
    path('product/', ProductList.as_view()),
    path('warehouse/', WarehouseList.as_view()),
]