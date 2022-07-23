from collections import defaultdict
from datetime import date, datetime, timedelta

from authentication.choices import RoleChoices
from authentication.mixins import (
    IsAdminOrAccountantMixin,
    IsAdminOrReadAdminOrAccountantMixin,
    IsAdminPermissionMixin,
)
from core.pagination import StandardPagination
from core.utils import convert_qp_dict_to_qp
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from essentials.models import Stock
from expenses.models import ExpenseDetail
from ledgers.views import GetAllBalances
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.status import *
from rest_framework.views import APIView

from .models import *
from .queries import (  # CancelledInvoiceQuery,; CancelStockTransferQuery,
    TransactionQuery,
    TransferQuery,
)
from .serializers import (  # CancelledInvoiceSerializer,; CancelStockTransferSerializer,
    GetAllStockSerializer,
    TransactionSerializer,
    TransferStockSerializer,
    UpdateTransactionSerializer,
    ViewTransfersSerializer,
)


class CreateTransaction(IsAdminOrAccountantMixin, generics.CreateAPIView):
    """
    get transactions with a time frame (optional), requires person to be passed
    """

    serializer_class = TransactionSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return Transaction.objects.filter(branch=self.request.branch)


class GetTransaction(IsAdminOrReadAdminOrAccountantMixin, generics.ListAPIView):
    """
    get transactions with a time frame (optional), requires person to be passed
    """

    serializer_class = TransactionSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        person_filter = {}
        if self.request.role not in [RoleChoices.ADMIN, RoleChoices.ADMIN_VIEWER]:
            person_filter = {"person__person_type": "C"}
        transactions = (
            Transaction.objects.select_related("person", "account_type")
            .prefetch_related(
                "transaction_detail",
                "transaction_detail__product",
                "transaction_detail__warehouse",
            )
            .filter(**person_filter, branch=self.request.branch)
        )
        qp = self.request.query_params
        person = qp.get("person")
        startDate = (
            qp.get("start")
            or transactions.aggregate(Min("date"))["date__min"]
            or date.today()
        )
        endDate = qp.get("end") or date.today()
        filters = {
            "date__gte": startDate,
            "date__lte": endDate,
        }
        if person:
            filters.update({"person": person})
        queryset = transactions.filter(**filters)
        return queryset


class EditUpdateDeleteTransaction(
    TransactionQuery, IsAdminPermissionMixin, generics.RetrieveUpdateDestroyAPIView
):
    """
    Edit / Update / Delete a transaction
    """

    serializer_class = UpdateTransactionSerializer

    def delete(self, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        Transaction.check_stock(self.request.branch, None)
        Log.create_log(
            ActivityTypes.DELETED,
            ActivityCategory.TRANSACTION,
            f"{instance.get_computer_serial()} for {instance.person.name}",
            self.request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class FilterTransactions(TransactionQuery, generics.ListAPIView):

    serializer_class = TransactionSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte"],
        "account_type": ["exact"],
        "detail": ["icontains"],
        "person": ["exact"],
        "serial": ["exact", "gte", "lte"],
        "manual_serial": ["exact", "gte", "lte"],
        "serial_type": ["exact"],
        "discount": ["gte", "lte"],
        "type": ["exact"],
        "requires_action": ["exact"],
        "transaction_detail__product": ["exact"],
        "transaction_detail__warehouse": ["exact"],
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by("serial_type", "serial", "-date")


class ProductPerformanceHistory(APIView):
    """
    statistics for a particular product or all products
    optional customer selected for customer purchase history
    """

    def get(self, request):
        filters = {
            "transaction__person__branch": request.branch,
            "transaction__nature": "D",
            "transaction__person__person_type": "C",
        }
        values = ["product__name"]
        person = request.query_params.get("person")
        product = request.query_params.get("product")
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        if person:
            filters.update({"transaction__person": person})
            values.append("transaction__person")
        if product:
            filters.update({"product": product})
        if start:
            filters.update({"transaction__date__gte": start})
        if end:
            filters.update({"transaction__date__lte": end})

        stats = (
            TransactionDetail.objects.values(*values)
            .annotate(
                quantity_sold=Sum("quantity"),
                average_rate=Avg("rate"),
                minimum_rate=Min("rate"),
                maximum_rate=Max("rate"),
                number_of_times_sold=Count("transaction__id"),
            )
            .filter(**filters)
            .order_by("-number_of_times_sold", "quantity_sold")
        )

        return Response(stats, status=status.HTTP_200_OK)


class BusinessPerformanceHistory(APIView):
    """
    get business' working statistics with optional date ranges
    """

    def get(self, request):
        qp = request.query_params
        branch = self.context["request"].branch
        branch_filter = {"branch": branch}
        filters = {}

        start_date = (
            datetime.strptime(qp.get("start"), "%Y-%m-%d") if qp.get("start") else None
        )
        end_date = datetime.strptime(qp.get("end"), "%Y-%m-%d") if qp.get("end") else None

        if start_date:
            filters.update({"transaction_id__date__gte": start_date})
        if end_date:
            filters.update({"transaction_id__date__lte": end_date})

        stats = (
            TransactionDetail.objects.values("transaction__nature")
            .filter(**filters, transaction__person__branch=branch)
            .annotate(
                quantity=Sum("quantity"),
                number_of_transactions=Count("transaction__id"),
                amount=Sum("amount"),
                avg_rate=Avg("rate"),
                avg_gazaana=Avg("yards_per_piece"),
            )
        )

        opening_stock = Product.objects.filter(**branch_filter).aggregate(
            avg_rate=Avg("opening_stock_rate"), total_quantity=Sum("opening_stock")
        )
        opening_stock_avg_rate = opening_stock.get("avg_rate", 0)
        opening_stock_avg_rate = opening_stock_avg_rate if opening_stock_avg_rate else 0
        opening_quantity = opening_stock.get("total_quantity", 0)
        opening_quantity = opening_quantity if opening_quantity else 0

        expense_filters = {"branch": branch}
        if start_date:
            expense_filters.update({"date__gte": start_date})
        if end_date:
            expense_filters.update({"date__lte": end_date})

        expenses = ExpenseDetail.objects.filter(**expense_filters).aggregate(
            total_expenses=Sum("amount")
        )
        balances = GetAllBalances.as_view()(request=request._request).data

        final_data = {
            "revenue": 0,
            "cogs": 0,
            "quantity_sold": 0,
            "number_of_transactions_bought": 0,
            "number_of_transactions_sold": 0,
            "quantity_bought": 0 + opening_quantity,
            "payable_total": 0,
            "recievable_total": 0,
            "expenses_total": expenses["total_expenses"]
            if expenses["total_expenses"]
            else 0,
            "profit": 0,
            "average_buying_rate": 0,
            "average_selling_rate": 0,
        }
        avg_gazaana_bought = 0
        avg_gazaana_sold = 0
        for stat in stats:
            if stat["transaction__nature"] == "D":
                final_data["revenue"] += stat["amount"]
                final_data["quantity_sold"] += stat["quantity"]
                final_data["number_of_transactions_sold"] += stat[
                    "number_of_transactions"
                ]
                final_data["average_selling_rate"] += stat["avg_rate"]
                avg_gazaana_sold += stat["avg_gazaana"] * stat["quantity"]
            else:
                final_data["quantity_bought"] += stat["quantity"]
                final_data["number_of_transactions_bought"] += stat[
                    "number_of_transactions"
                ]
                final_data["average_buying_rate"] += stat["avg_rate"]
                avg_gazaana_bought += stat["avg_gazaana"]

        for person, balance in balances.items():
            if balance >= 0:
                final_data["payable_total"] += balance
            else:
                final_data["recievable_total"] += abs(balance)

        divisor = 0
        if opening_stock_avg_rate:
            divisor += 1
        if final_data["average_buying_rate"]:
            divisor += 1

        final_data["average_buying_rate"] = (
            opening_stock_avg_rate + final_data["average_buying_rate"]
        ) / (divisor or 1)

        final_data["cogs"] = (
            final_data["average_buying_rate"]
            * final_data["quantity_sold"]
            * avg_gazaana_bought
        )

        final_data["profit"] = final_data["revenue"] - (
            final_data["expenses_total"] + final_data["cogs"]
        )

        return Response(final_data, status=status.HTTP_200_OK)


class TransferStock(IsAdminOrAccountantMixin, generics.CreateAPIView):
    """Transfer stock from one warehouse to another"""

    serializer_class = TransferStockSerializer


class DeleteTransferStock(TransferQuery, IsAdminPermissionMixin, generics.DestroyAPIView):
    """Delete transfer stock"""

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        Transaction.check_stock(self.request.branch)
        Log.create_log(
            ActivityTypes.DELETED,
            ActivityCategory.STOCK_TRANSFER,
            f"serial # {instance.manual_serial} of {instance.from_warehouse.name}",
            self.request,
        )


class ViewTransfers(
    TransferQuery, IsAdminOrReadAdminOrAccountantMixin, generics.ListAPIView
):
    """View for listing transfers"""

    serializer_class = ViewTransfersSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte"],
        "transfer_detail__product": ["exact"],
        "transfer_detail__yards_per_piece": ["exact", "gte", "lte"],
        "from_warehouse": ["exact"],
        "serial": ["gte", "lte", "exact"],
        "manual_serial": ["gte", "lte", "exact"],
        "transfer_detail__to_warehouse": ["exact"],
        "transfer_detail__quantity": ["exact", "gte", "lte"],
    }


class DetailedStockView(IsAdminOrReadAdminOrAccountantMixin, APIView):
    def get(self, request):
        qp = request.query_params
        product = get_object_or_404(Product, id=qp.get("product"))
        opening_stock = 0.0
        branch = request.branch

        initial_stock_filters = {"product": qp.get("product")}
        if qp.get("warehouse"):
            initial_stock_filters.update({"warehouse": qp.get("warehouse")})
        if qp.get("yards_per_piece"):
            initial_stock_filters.update({"yards_per_piece": qp.get("yards_per_piece")})

        initial_stock = (
            Stock.objects.filter(**initial_stock_filters).aggregate(
                total=Sum("opening_stock")
            )["total"]
            or 0
        )

        opening_stock += initial_stock

        filters = {"product": product, "transaction__person__branch": branch}
        filters_transfers = {"product": product, "transfer__branch": branch}
        if qp.get("start"):
            start = datetime.strptime(qp.get("start"), "%Y-%m-%d %H:%M:%S")
            filters.update({"transaction__date__gte": start})
            filters_transfers.update({"transfer__date__gte": start})
            startDateMinusOne = start - timedelta(days=1)

            old_stock = (
                TransactionDetail.objects.values("transaction__nature")
                .annotate(quantity=Sum("quantity"))
                .filter(
                    transaction__date__lte=startDateMinusOne,
                    product=product,
                    transaction__person__branch=branch,
                )
            )
            for old in old_stock:
                if old["transaction__nature"] == "C":
                    opening_stock += old["quantity"]
                else:
                    opening_stock -= old["quantity"]

        if qp.get("end"):
            filters.update({"transaction__date__lte": qp.get("end")})
            filters_transfers.update({"transfer__date__lte": qp.get("end")})

        if qp.get("yards_per_piece"):
            filters.update({"yards_per_piece": qp.get("yards_per_piece")})
            filters_transfers.update({"yards_per_piece": qp.get("yards_per_piece")})

        if qp.get("warehouse"):
            filters.update({"warehouse": qp.get("warehouse")})

        if qp.get("warehouse") and qp.get("start"):
            old_transfer_quantity = StockTransferDetail.calculateTransferredAmount(
                qp.get("warehouse"),
                qp.get("product"),
                {
                    "transfer__date__lte": startDateMinusOne,
                    "transfer__branch": branch,
                },
            )
            opening_stock += old_transfer_quantity

        stock = (
            TransactionDetail.objects.values(
                "transaction__nature",
                "transaction_id",
                "transaction__date",
                "transaction__serial",
                "transaction__manual_serial",
                "transaction__serial_type",
                "transaction__person",
                "warehouse",
                "yards_per_piece",
                "transaction__type",
            )
            .filter(**filters)
            .annotate(quantity=Sum("quantity"))
            .order_by("transaction__date")
        )

        transfer_values = [
            "transfer__date",
            "to_warehouse",
            "quantity",
            "id",
            "yards_per_piece",
            "transfer__from_warehouse",
        ]
        if qp.get("warehouse"):
            transfers = StockTransferDetail.objects.filter(
                Q(transfer__from_warehouse=qp.get("warehouse"))
                | Q(to_warehouse=qp.get("warehouse")),
                **filters_transfers,
            ).values(*transfer_values)
        else:
            transfers = StockTransferDetail.objects.filter(**filters_transfers).values(
                *transfer_values
            )

        transfers = map(lambda x: {**x, "date": x["transfer__date"]}, transfers)

        return Response(
            {
                "data": stock,
                "opening_stock": opening_stock,
                "transfers": transfers,
            },
            status=status.HTTP_200_OK,
        )


class ViewAllStock(TransactionQuery, generics.ListAPIView):

    serializer_class = GetAllStockSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "quantity": ["gte", "lte", "exact"],
        "yards_per_piece": ["gte", "lte", "exact"],
        "product": ["exact"],
        "warehouse": ["exact"],
    }

    def list(self, request, *args, **kwargs):
        qpDict = dict(request.GET.lists())
        qps = convert_qp_dict_to_qp(qpDict)
        outcut = qps.pop("outcut", None)
        date = qps.pop("date", None)
        quantity = qps.pop("quantity", None)
        quantity__gte = qps.pop("quantity__gte", None)
        quantity__lte = qps.pop("quantity__lte", None)
        stock = Transaction.get_all_stock(request.branch, date, None, None, **qps)
        if outcut:
            stock = filter(
                lambda x: x["yards_per_piece"] != 44 and x["yards_per_piece"] != 66, stock
            )
        if quantity:
            stock = filter(lambda x: x["quantity"] == quantity, stock)
        if quantity__gte:
            stock = filter(lambda x: x["quantity"] >= quantity__gte, stock)
        if quantity__lte:
            stock = filter(lambda x: x["quantity"] <= quantity__lte, stock)
        if qps.get("warehouse"):
            stock = filter(lambda x: x["warehouse"] == qps.get("warehouse"), stock)

        serializer = self.get_serializer(stock, many=True)
        return Response(serializer.data)
