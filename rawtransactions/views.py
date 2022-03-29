from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from .queries import (
    FormulaQuery,
    RawProductQuery,
    RawTransactionLotQuery,
    RawTransactionQuery,
)
from .serializers import (
    CreateRawTransactionSerializer,
    FormulaSerializer,
    RawLotNumberAndIdSerializer,
    RawProductSerializer,
    RawReturnSerializer,
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


class CreateFormula(FormulaQuery, generics.CreateAPIView):

    serializer_class = FormulaSerializer


class RawReturnView(generics.CreateAPIView):

    serializer_class = RawReturnSerializer


class ListLotNumberAndIdView(RawTransactionLotQuery, generics.ListAPIView):

    serializer_class = RawLotNumberAndIdSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "raw_transaction__person": ["exact"],
    }

    def get_queryset(self):
        qp = self.request.query_params
        if "issued" in qp:
            issued = False if qp.get("issued") == "false" else True
            queryset = super().get_queryset()
            return queryset.filter(issued=issued)
        return super().get_queryset()
