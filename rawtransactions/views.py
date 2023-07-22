from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from core.pagination import StandardPagination
from core.utils import convert_qp_dict_to_qp

from .filters import (
    RawDebitTransactionsFilter,
    RawTransactionsFilter,
    RawTransferTransactionsFilter,
)
from .queries import (
    FormulaQuery,
    RawDebitListQuery,
    RawDebitQuery,
    RawProductQuery,
    RawTransactionLotDetailQueryWithId,
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
    RawStockTransferSerializer,
    RawTransactionLotAutofillSerializer,
    UpdateRawTransactionSerializer,
    ViewAllStockSerializer,
)
from .utils import get_current_stock_position, validate_inventory


class CreateRawProduct(RawProductQuery, generics.CreateAPIView):
    serializer_class = RawProductSerializer


class ListRawProducts(RawProductQuery, generics.ListAPIView):
    serializer_class = RawProductSerializer
    filter_backends = [DjangoFilterBackend]


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

    def list(self, request, *args, **kwargs):
        stock = self.get_queryset()
        qpDict = dict(request.GET.lists())
        qps = convert_qp_dict_to_qp(qpDict)

        lot_number = qps.pop("lot_number", None)
        raw_product = qps.pop("raw_product", None)
        warehouse = qps.pop("warehouse", None)
        actual_gazaana__gte = qps.pop("actual_gazaana__gte", None)
        actual_gazaana__lte = qps.pop("actual_gazaana__lte", None)
        quantity__gte = qps.pop("quantity__gte", None)
        quantity__lte = qps.pop("quantity__lte", None)
        expected_gazaana__gte = qps.pop("expected_gazaana__gte", None)
        expected_gazaana__lte = qps.pop("expected_gazaana__lte", None)
        product_glue = qps.pop("product_glue", None)
        product_type = qps.pop("product_type", None)
        if lot_number:
            stock = filter(lambda s: s["lot_number"] == lot_number, stock)
        if raw_product:
            stock = filter(lambda s: str(s["raw_product"]) == raw_product, stock)
        if warehouse:
            stock = filter(lambda s: s["warehouse"] == warehouse, stock)
        if quantity__gte:
            stock = filter(lambda s: s["quantity"] >= quantity__gte, stock)
        if quantity__lte:
            stock = filter(lambda s: s["quantity"] <= quantity__lte, stock)
        if actual_gazaana__gte:
            stock = filter(lambda s: s["actual_gazaana"] >= actual_gazaana__gte, stock)
        if actual_gazaana__lte:
            stock = filter(lambda s: s["actual_gazaana"] <= actual_gazaana__lte, stock)
        if expected_gazaana__gte:
            stock = filter(
                lambda s: s["expected_gazaana"] <= expected_gazaana__gte, stock
            )
        if expected_gazaana__lte:
            stock = filter(
                lambda s: s["expected_gazaana"] <= expected_gazaana__lte, stock
            )
        if product_glue:
            stock = filter(lambda s: s["product_glue"] == product_glue, stock)
        if product_type:
            stock = filter(lambda s: s["product_type"] == product_type, stock)

        stock = list(filter(lambda s: s["quantity"] > 0, stock))

        return Response(stock, status=status.HTTP_200_OK)


class TransferRawStockView(RawTransferQuery, generics.CreateAPIView):
    serializer_class = RawStockTransferSerializer


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


class EditUpdateDeleteRawDebitTransactionView(
    RawDebitQuery, generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = RawDebitSerializer

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        validated, error = validate_inventory(request.branch)
        if not validated:
            raise ValidationError(error)
        return Response(status=status.HTTP_204_NO_CONTENT)


class EditUpdateDeleteRawTransferTransactionView(
    RawTransferQuery, generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = RawStockTransferSerializer

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        validated, error = validate_inventory(request.branch)
        if not validated:
            raise ValidationError(error)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RawTransactionLotDetail(
    RawTransactionLotDetailQueryWithId, generics.RetrieveAPIView
):
    serializer_class = RawTransactionLotAutofillSerializer
