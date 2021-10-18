from typing import List
from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView

from .serializers import *
from .models import *

class PersonList(ListCreateAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class WarehouseList(ListCreateAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

    
class ProductList(ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = CreateProductSerializer


class AccountTypeList(ListCreateAPIView):
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer