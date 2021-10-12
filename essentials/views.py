from typing import List
from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView

from .serializers import *
from .models import *

class AccountList(ListCreateAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class WarehouseList(ListCreateAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

    
class ProductList(ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ParentProductSerializer