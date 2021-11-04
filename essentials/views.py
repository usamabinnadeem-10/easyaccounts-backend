from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from django.db.models import Sum

from .serializers import *
from .models import *

from datetime import date

from transactions.models import Transaction
from transactions.serializers import TransactionSerializer
from expenses.models import ExpenseDetail
from expenses.serializers import ExpenseDetailSerializer
from ledgers.models import Ledger
from ledgers.serializers import LedgerSerializer

from .models import SUPPLIER, CUSTOMER


class CreateAndListPerson(ListCreateAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer

    def list(self, request, *args, **kwargs):
        person = request.query_params.get("person")
        if person == SUPPLIER or person == CUSTOMER:
            queryset = Person.objects.filter(person_type=person)
            serialized = PersonSerializer(queryset, many=True)
            return Response(serialized.data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


class CreateAndListWarehouse(ListCreateAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer


class CreateAndListProduct(ListCreateAPIView):
    queryset = Product.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductSerializer
        elif self.request.method == "POST":
            return CreateProductSerializer


class CreateAndListProductHead(ListCreateAPIView):
    queryset = ProductHead.objects.all()
    serializer_class = ProductHeadSerializer


class CreateAndListAccountType(ListCreateAPIView):
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer


class DayBook(APIView):
    def get(self, request):
        today = date.today()

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
            final_transactions.append(
                {
                    "transaction": transaction,
                    "account_type": serialized_account_type,
                    "paid_amount": paid_amount,
                }
            )

        balance_ledgers = (
            Ledger.objects.values("account_type__name", "nature")
            .filter(account_type__isnull=False)
            .annotate(amount=Sum("amount"))
        )
        balance_expenses = ExpenseDetail.objects.values("account_type__name").annotate(
            amount=Sum("amount")
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
