from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

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

        expenses = ExpenseDetail.objects.filter(date__gte=today, date__lte=today)
        expenses_serialized = ExpenseDetailSerializer(expenses, many=True)

        ledgers = Ledger.objects.filter(date__gte=today, date__lte=today)
        ledger_serialized = LedgerSerializer(ledgers, many=True)

        transactions = Transaction.objects.filter(date__gte=today, date__lte=today)
        transactions_serialized = TransactionSerializer(transactions, many=True)

        accounts = AccountType.objects.all()
        accounts_serialized = AccountTypeSerializer(accounts, many=True)

        return Response(
            {
                "expenses": expenses_serialized.data,
                "ledgers": ledger_serialized.data,
                "transactions": transactions_serialized.data,
                "accounts": accounts_serialized.data,
            },
            status=status.HTTP_200_OK,
        )
