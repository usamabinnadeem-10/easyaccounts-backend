from rest_framework import status
from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import *
from .models import *
from .utils import get_account_balances

from datetime import date, datetime
from itertools import chain

from transactions.models import Transaction
from transactions.serializers import TransactionSerializer

from expenses.models import ExpenseDetail
from expenses.serializers import ExpenseDetailSerializer

from ledgers.models import Ledger
from ledgers.serializers import LedgerSerializer

from essentials.pagination import CustomPagination, PaginationHandlerMixin

from cheques.models import ExternalChequeHistory, PersonalCheque, ExternalCheque
from cheques.choices import PersonalChequeStatusChoices
from cheques.serializers import (
    IssuePersonalChequeSerializer,
    ExternalChequeSerializer,
    ShortExternalChequeHistorySerializer,
)

from collections import defaultdict


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

        filters = {
            "date__gte": today,
            "date__lte": today,
        }

        expenses = ExpenseDetail.objects.filter(**filters)
        expenses_serialized = ExpenseDetailSerializer(expenses, many=True)

        ledgers = Ledger.objects.filter(**filters)
        ledger_serialized = LedgerSerializer(ledgers, many=True)

        transactions = Transaction.objects.filter(**filters)
        transactions_serialized = TransactionSerializer(transactions, many=True).data

        external_cheques = ExternalCheque.objects.filter(**filters)
        external_cheques_serialized = ExternalChequeSerializer(
            external_cheques, many=True
        ).data

        external_cheques_history = ExternalChequeHistory.objects.select_related(
            "parent_cheque"
        ).filter(**filters, return_cheque__isnull=True)
        external_cheques_history_serialized = ShortExternalChequeHistorySerializer(
            external_cheques_history, many=True
        ).data

        personal_cheques = PersonalCheque.objects.filter(**filters)
        personal_cheques_serialized = IssuePersonalChequeSerializer(
            personal_cheques, many=True
        ).data

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
            .annotate(total=Sum("amount"))
        )

        balance_external_cheques = (
            ExternalChequeHistory.objects.values(
                "account_type__name",
            )
            .filter(return_cheque__isnull=True)
            .annotate(total=Sum("amount"))
        )

        balance_personal_cheques = (
            PersonalCheque.objects.values("account_type__name")
            .filter(status=PersonalChequeStatusChoices.CLEARED)
            .annotate(total=Sum("amount"))
        )

        final_account_balances = defaultdict(lambda: 0)

        for ledger in balance_ledgers:
            current_amount = final_account_balances[ledger["account_type__name"]]
            if ledger["nature"] == "C":
                current_amount += ledger["amount"]
            else:
                current_amount -= ledger["amount"]
            final_account_balances[ledger["account_type__name"]] = current_amount

        final_account_balances = get_account_balances(
            final_account_balances, balance_external_cheques
        )
        final_account_balances = get_account_balances(
            final_account_balances, balance_personal_cheques, "sub"
        )
        final_account_balances = get_account_balances(
            final_account_balances, balance_expenses, "sub"
        )

        return Response(
            {
                "expenses": expenses_serialized.data,
                "ledgers": ledger_serialized.data,
                "transactions": transactions_serialized,
                "balance_ledgers": final_account_balances,
                "balance_expenses": balance_expenses,
                "external_cheques": external_cheques_serialized,
                "external_cheques_history": external_cheques_history_serialized,
                "personal_cheques": personal_cheques_serialized,
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


class GetAccountHistory(APIView, PaginationHandlerMixin):
    """Get account history for a specific account type"""

    pagination_class = CustomPagination

    def get(self, request):
        try:
            qp = request.query_params
            account = qp.get("account")
            filters = {}
            start_date = (
                datetime.strptime(qp.get("start"), "%Y-%m-%d")
                if qp.get("start")
                else None
            )
            if start_date:
                filters.update({"date__gte": start_date})
            end_date = (
                datetime.strptime(qp.get("end"), "%Y-%m-%d") if qp.get("end") else None
            )
            if end_date:
                filters.update({"date__lte": end_date})

            account = AccountType.objects.get(id=account)
            ledger = Ledger.objects.filter(
                **{**filters, "account_type": account}
            ).values()
            external_cheque_history = ExternalChequeHistory.objects.filter(
                **filters
            ).values()
            final_result = sorted(
                chain(ledger, external_cheque_history), key=lambda obj: obj["date"]
            )
            paginated = self.paginate_queryset(final_result)
            paginated = self.get_paginated_response(paginated).data
            return Response({"data": paginated}, status=status.HTTP_200_OK)

        except:
            return Response(
                {"error": "Please choose an account type"},
                status=status.HTTP_400_BAD_REQUEST,
            )
