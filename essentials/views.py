from rest_framework import status
from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import *
from .models import *

from datetime import date

from transactions.models import Transaction
from transactions.serializers import TransactionSerializer
from expenses.models import ExpenseDetail
from expenses.serializers import ExpenseDetailSerializer
from ledgers.models import Ledger
from ledgers.serializers import LedgerSerializer


class CreateAndListPerson(ListCreateAPIView):
    """
    create or list persons with the option of filtering by person_type
    """

    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["person_type"]


class CreateAndListWarehouse(ListCreateAPIView):
    """
    create or list warehouses
    """

    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer


class CreateAndListProduct(ListCreateAPIView):
    """
    create or list products
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class CreateAndListAccountType(ListCreateAPIView):
    """
    create or list account types
    """

    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer


class DayBook(APIView):
    """
    get daybook for today or with a specific date
    """

    def get(self, request):
        today = date.today()
        if self.request.query_params.get("date"):
            today = self.request.query_params.get("date")

        all_ledger = Ledger.objects.all()

        expenses = ExpenseDetail.objects.filter(date__gte=today, date__lte=today)
        expenses_serialized = ExpenseDetailSerializer(expenses, many=True)

        ledgers = Ledger.objects.filter(date__gte=today, date__lte=today)
        ledger_serialized = LedgerSerializer(ledgers, many=True)

        transactions = Transaction.objects.filter(date__gte=today, date__lte=today)
        transactions_serialized = TransactionSerializer(transactions, many=True).data

        final_transactions = []
        for transaction in transactions_serialized:
            paid_amount = None
            serialized_account_type = None
            ledger_instance = all_ledger.filter(
                transaction=transaction["id"], account_type__isnull=False
            )
            if len(ledger_instance):
                serialized_account_type = (
                    AccountTypeSerializer(ledger_instance[0].account_type).data
                    if ledger_instance[0].account_type
                    else None
                )
                paid_amount = ledger_instance[0].amount
            final_transactions.append(transaction)

        balance_ledgers = (
            Ledger.objects.values("account_type__name", "nature")
            .order_by("nature")
            .filter(date__lte=today, account_type__isnull=False)
            .annotate(amount=Sum("amount"))
        )
        balance_expenses = (
            ExpenseDetail.objects.values("account_type__name")
            .order_by("date")
            .filter(date__lte=today)
            .annotate(amount=Sum("amount"))
        )

        return Response(
            {
                "expenses": expenses_serialized.data,
                "ledgers": ledger_serialized.data,
                "transactions": final_transactions,
                "balance_ledgers": balance_ledgers,
                "balance_expenses": balance_expenses,
            },
            status=status.HTTP_200_OK,
        )


class GetStockQuantity(ListAPIView):

    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "stock_quantity": ["gte", "lte"],
        "product": ["exact"],
        "warehouse": ["exact"],
        "yards_per_piece": ["gte", "lte", "exact"],
    }
