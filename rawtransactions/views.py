from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend

from .queries import RawProductQuery, RawTransactionQuery, FormulaQuery, RawProduct
from .serializers import (
    RawProductSerializer,
    CreateRawTransactionSerializer,
    FormulaSerializer,
)


class CreateRawProduct(RawProductQuery, generics.CreateAPIView):

    serializer_class = RawProductSerializer


class ListRawProducts(RawProductQuery, generics.ListAPIView):

    serializer_class = RawProductSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "name": ["contains"],
        "type": ["exact"],
        "person": ["exact"],
    }


class CreateRawTransaction(RawTransactionQuery, generics.CreateAPIView):

    serializer_class = CreateRawTransactionSerializer


class ListFormula(FormulaQuery, generics.ListAPIView):

    serializer_class = FormulaSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "name": ["contains"],
        "person": ["exact"],
        "type": ["exact"],
    }


class CreateFormula(FormulaQuery, generics.CreateAPIView):

    serializer_class = FormulaSerializer
