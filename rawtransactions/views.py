from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from core.pagination import StandardPagination

from .filters import (
    RawDebitTransactionsFilter,
    RawTransactionsFilter,
    RawTransferTransactionsFilter,
)
from .queries import (
    FormulaQuery,
    RawDebitListQuery,
    RawProductQuery,
    RawTransactionLotQuery,
    RawTransactionQuery,
    RawTransferListQuery,
    RawTransferQuery,
)
from .serializers import (
    CreateRawTransactionSerializer,
    FormulaSerializer,
    ListRawDebitTransactionSerializer,
    ListRawTransactionSerializer,
    ListRawTransferTransactionSerializer,
    RawDebitSerializer,
    RawLotNumberAndIdSerializer,
    RawProductSerializer,
    UpdateRawTransactionSerializer,
    ViewAllStockSerializer,
)
from .utils import get_current_stock_position, validate_inventory


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


class FilterRawTransactions(RawTransactionQuery, generics.ListAPIView):
    serializer_class = ListRawTransactionSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RawTransactionsFilter


class FilterRawDebitTransactions(RawDebitListQuery, generics.ListAPIView):
    serializer_class = ListRawDebitTransactionSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RawDebitTransactionsFilter


class FilterRawTransferTransactions(RawTransferListQuery, generics.ListAPIView):
    serializer_class = ListRawTransferTransactionSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RawTransferTransactionsFilter


class ListFormula(FormulaQuery, generics.ListAPIView):
    serializer_class = FormulaSerializer


class CreateFormula(FormulaQuery, generics.CreateAPIView):
    serializer_class = FormulaSerializer


class RawDebitView(generics.CreateAPIView):
    serializer_class = RawDebitSerializer


class ListLotNumberAndIdView(RawTransactionLotQuery, generics.ListAPIView):
    serializer_class = RawLotNumberAndIdSerializer
    filter_backends = [DjangoFilterBackend]
    pagination_class = StandardPagination
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


class ViewAllStock(generics.ListAPIView):
    serializer_class = ViewAllStockSerializer

    def get_queryset(self):
        stock = get_current_stock_position(self.request.branch)
        return stock


class TransferRawStockView(RawTransferQuery, generics.CreateAPIView):
    serializer_class = ListRawTransferTransactionSerializer


class EditUpdateDeleteRawTransactionView(
    RawTransactionQuery, generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = UpdateRawTransactionSerializer

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        validated, error = validate_inventory(request.branch)
        if not validated:
            raise ValidationError(error)
        return Response(status=status.HTTP_204_NO_CONTENT)
