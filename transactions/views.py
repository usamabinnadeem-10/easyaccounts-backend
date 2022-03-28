from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.status import *

from expenses.models import ExpenseDetail
from ledgers.views import GetAllBalances
from essentials.pagination import CustomPagination
from essentials.models import *
from .models import *
from .serializers import (
    TransactionSerializer,
    UpdateTransactionSerializer,
    update_stock,
    CancelledInvoiceSerializer,
)
from .utils import *
from .queries import (
    TransactionQuery,
    CancelledInvoiceQuery,
)

from django.db.models import Min, Max, Avg, Sum, Count, Q
from datetime import date, datetime, timedelta


class GetOrCreateTransaction(generics.ListCreateAPIView):
    """
    get transactions with a time frame (optional), requires person to be passed
    """

    serializer_class = TransactionSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        transactions = (
            Transaction.objects.select_related("person", "account_type")
            .prefetch_related(
                "transaction_detail",
                "transaction_detail__product",
                "transaction_detail__warehouse",
            )
            .filter(branch=self.request.branch)
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
            "draft": qp.get("draft") or False,
        }
        if person:
            filters.update({"person": person})
        queryset = transactions.filter(**filters)
        return queryset


class EditUpdateDeleteTransaction(
    TransactionQuery, generics.RetrieveUpdateDestroyAPIView
):
    """
    Edit / Update / Delete a transaction
    """

    serializer_class = UpdateTransactionSerializer

    def delete(self, *args, **kwargs):
        instance = self.get_object()

        transaction_details = TransactionDetail.objects.filter(
            branch=self.request.branch, transaction=instance
        ).values(
            "product",
            "quantity",
            "warehouse",
            "yards_per_piece",
        )

        for transaction in transaction_details:
            update_stock("C" if instance.nature == "D" else "D", transaction)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FilterTransactions(TransactionQuery, generics.ListAPIView):

    serializer_class = TransactionSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte"],
        "account_type": ["exact"],
        "detail": ["icontains"],
        "person": ["exact"],
        "draft": ["exact"],
        "serial": ["exact", "gte", "lte"],
        "discount": ["gte", "lte"],
        "type": ["exact"],
        "transaction_detail__amount": ["gte", "lte"],
        "requires_action": ["exact"],
    }


class ProductPerformanceHistory(APIView):
    """
    statistics for a particular product or all products
    optional customer selected for customer purchase history
    """

    def get(self, request):
        filters = {
            "branch": request.branch,
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
        filters = {"transaction__draft": False}

        start_date = (
            datetime.strptime(qp.get("start"), "%Y-%m-%d") if qp.get("start") else None
        )
        end_date = (
            datetime.strptime(qp.get("end"), "%Y-%m-%d") if qp.get("end") else None
        )

        if start_date:
            filters.update({"transaction_id__date__gte": start_date})
        if end_date:
            filters.update({"transaction_id__date__lte": end_date})

        stats = (
            TransactionDetail.objects.values("transaction__nature")
            .filter(**filters, **branch_filter)
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

        del filters["transaction__draft"]
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


class TransferStock(APIView):
    """Transfer stock from one warehouse to another"""

    def post(self, request):
        body = request.data
        branch = request.branch
        stock = Stock.objects.get(id=body["id"], branch=branch)
        product = stock.product
        warehouse = stock.warehouse
        if body["to_warehouse"] and body["transfer_quantity"]:
            data = {
                "product": product,
                "warehouse": warehouse,
                "yards_per_piece": stock.yards_per_piece,
                "quantity": body["transfer_quantity"],
                "branch": branch,
            }
            update_stock("D", data)
            to_warehouse = Warehouse.objects.get(id=body["to_warehouse"], branch=branch)
            data.update({"warehouse": to_warehouse})
            update_stock("C", data)

            TransferEntry.objects.create(
                branch=branch,
                product=product,
                yards_per_piece=stock.yards_per_piece,
                from_warehouse=warehouse,
                to_warehouse=to_warehouse,
                quantity=body["transfer_quantity"],
            )
            return Response({}, status=status.HTTP_201_CREATED)
        return Response(
            {"error": "Please provide warehouse and quantity to transfer"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CancelInvoice(CancelledInvoiceQuery, generics.ListCreateAPIView):

    serializer_class = CancelledInvoiceSerializer


class DetailedStockView(APIView):
    def get(self, request):
        qp = request.query_params
        product = get_object_or_404(Product, id=qp.get("product"))
        opening_stock = 0.0
        branch = request.branch
        filters = {"product": product, "branch": branch}
        filters_transfers = {"product": product, "branch": branch}
        if qp.get("start"):
            start = datetime.strptime(qp.get("start"), "%Y-%m-%d")
            filters.update({"transaction__date__gte": start})
            filters_transfers.update({"date__gte": start})
            startDateMinusOne = start - timedelta(days=1)

            old_stock = (
                TransactionDetail.objects.values("transaction__nature")
                .annotate(quantity=Sum("quantity"))
                .filter(
                    transaction__date__lte=startDateMinusOne,
                    product=product,
                    branch=branch,
                )
            )
            for old in old_stock:
                if old["transaction__nature"] == "C":
                    opening_stock += old["quantity"]
                else:
                    opening_stock -= old["quantity"]

        if qp.get("end"):
            filters.update({"transaction__date__lte": qp.get("end")})
            filters_transfers.update({"date__lte": qp.get("end")})

        if qp.get("yards_per_piece"):
            filters.update({"yards_per_piece": qp.get("yards_per_piece")})
            filters_transfers.update({"yards_per_piece": qp.get("yards_per_piece")})

        if qp.get("warehouse"):
            filters.update({"warehouse": qp.get("warehouse")})

        if qp.get("warehouse") and qp.get("start"):
            old_transfer_quantity = TransferEntry.calculateTransferredAmount(
                qp.get("warehouse"),
                qp.get("product"),
                {
                    "date__lte": startDateMinusOne,
                    "branch": branch,
                },
            )
            opening_stock += old_transfer_quantity

        stock = (
            TransactionDetail.objects.values(
                "transaction__nature",
                "transaction_id",
                "transaction__date",
                "transaction__serial",
                "transaction__manual_invoice_serial",
                "transaction__manual_serial_type",
                "transaction__person",
                "warehouse",
                "yards_per_piece",
                "transaction__type",
            )
            .annotate(quantity=Sum("quantity"))
            .filter(**filters)
            .order_by("transaction__date")
        )

        if qp.get("warehouse"):
            transfers = TransferEntry.objects.filter(
                Q(from_warehouse=qp.get("warehouse"))
                | Q(to_warehouse=qp.get("warehouse")),
                **filters_transfers,
            ).values()
        else:
            transfers = TransferEntry.objects.filter(**filters_transfers).values()

        return Response(
            {
                "data": stock,
                "opening_stock": opening_stock,
                "transfers": transfers,
            },
            status=status.HTTP_200_OK,
        )
