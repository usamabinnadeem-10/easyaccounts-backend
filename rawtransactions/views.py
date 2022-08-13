from collections import defaultdict
from operator import itemgetter

from core.pagination import StandardPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from transactions.choices import TransactionChoices

from .queries import (
    FormulaQuery,
    RawProductQuery,
    RawPurchaseLotQuery,
    RawPurchaseQuery,
    RawSaleAndReturnQuery,
)
from .serializers import (
    CreateRawTransactionSerializer,
    FormulaSerializer,
    ListRawTransactionSerializer,
    RawDebitSerializer,
    RawLotNumberAndIdSerializer,
    RawProductSerializer,
    RawStockTransferSerializer,
    ViewAllStockSerializer,
)
from .utils import get_all_raw_stock


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


class CreateRawTransaction(RawPurchaseQuery, generics.CreateAPIView):

    serializer_class = CreateRawTransactionSerializer


class ListFormula(FormulaQuery, generics.ListAPIView):

    serializer_class = FormulaSerializer


class CreateFormula(FormulaQuery, generics.CreateAPIView):

    serializer_class = FormulaSerializer


class RawSaleAndReturnView(generics.CreateAPIView):

    serializer_class = RawDebitSerializer


class ListLotNumberAndIdView(RawPurchaseLotQuery, generics.ListAPIView):

    serializer_class = RawLotNumberAndIdSerializer
    filter_backends = [DjangoFilterBackend]
    pagination_class = StandardPagination
    filter_fields = {
        "raw_purchase__person": ["exact"],
    }

    def get_queryset(self):
        qp = self.request.query_params
        if "issued" in qp:
            issued = False if qp.get("issued") == "false" else True
            queryset = super().get_queryset()
            return queryset.filter(issued=issued)
        return super().get_queryset()


class ListRawTransactions(RawPurchaseQuery, generics.ListAPIView):

    serializer_class = ListRawTransactionSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "person": ["exact"],
        "date": ["exact", "gte", "lte"],
        "manual_serial": ["exact", "gte", "lte"],
        "transaction_lot__lot_number": ["exact", "gte", "lte"],
        "transaction_lot__raw_product": ["exact", "gte", "lte"],
    }

    def get_queryset(self):
        qp = self.request.query_params
        if "issued" in qp:
            issued = False if qp.get("issued") == "false" else True
            queryset = super().get_queryset()
            return queryset.filter(transaction_lot__issued=issued)
        return super().get_queryset()


class ViewAllStock(generics.ListAPIView):

    serializer_class = ViewAllStockSerializer

    def get_queryset(self):
        stock_array = get_all_raw_stock(self.request.branch)
        d = defaultdict(lambda: defaultdict(int))

        group_keys = [
            "actual_gazaana",
            "expected_gazaana",
            "raw_product",
            "warehouse",
            "formula",
        ]
        sum_keys = ["quantity"]

        for item in stock_array:
            for key in sum_keys:
                if item["nature"] == TransactionChoices.CREDIT:
                    d[itemgetter(*group_keys)(item)][key] += item[key]
                else:
                    d[itemgetter(*group_keys)(item)][key] -= item[key]

        stock = [{**dict(zip(group_keys, k)), **v} for k, v in d.items()]
        return stock


class TransferRawStockView(RawSaleAndReturnQuery, generics.CreateAPIView):

    serializer_class = RawStockTransferSerializer
