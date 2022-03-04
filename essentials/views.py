from rest_framework import status
from rest_framework.generics import ListCreateAPIView, ListAPIView, CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from django.db.models import Sum, F
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import *
from .models import *
from .utils import get_account_balances, format_cheques_as_ledger, add_type

from datetime import date, datetime
from itertools import chain

from transactions.models import Transaction
from transactions.serializers import TransactionSerializer

from expenses.models import ExpenseDetail
from expenses.serializers import ExpenseDetailSerializer

from ledgers.models import Ledger
from ledgers.serializers import LedgerSerializer

from essentials.pagination import CustomPagination, PaginationHandlerMixin

from cheques.utils import get_cheque_account
from cheques.models import ExternalChequeHistory, PersonalCheque, ExternalCheque
from cheques.choices import PersonalChequeStatusChoices, ChequeStatusChoices
from cheques.serializers import (
    IssuePersonalChequeSerializer,
    ExternalChequeSerializer,
    ShortExternalChequeHistorySerializer,
)

from collections import defaultdict


class CreatePerson(CreateAPIView):
    """
    create person
    """

    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class ListPerson(ListAPIView):
    """
    list persons with the option of filtering by person_type
    """

    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["person_type"]


class CreateWarehouse(CreateAPIView):
    """
    create warehouse
    """

    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer


class ListWarehouse(ListAPIView):
    """
    list warehouses
    """

    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer


class CreateProduct(CreateAPIView):
    """
    create product
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ListProduct(ListAPIView):
    """
    list products
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class CreateAccountType(CreateAPIView):
    """
    create account type
    """

    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer


class ListAccountType(ListAPIView):
    """
    list account types
    """

    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer


class CreateArea(CreateAPIView):
    """
    create area
    """

    queryset = Area.objects.all()
    serializer_class = AreaSerializer


class ListArea(ListAPIView):
    """
    list areas
    """

    queryset = Area.objects.all()
    serializer_class = AreaSerializer


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

        cheque_account = get_cheque_account().account

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

        external_cheques_history = (
            ExternalChequeHistory.objects.select_related("parent_cheque")
            .filter(**filters)
            .exclude(return_cheque__status=ChequeStatusChoices.RETURNED)
            .order_by("parent_cheque__serial")
        )
        external_cheques_history_serialized = ShortExternalChequeHistorySerializer(
            external_cheques_history, many=True
        ).data

        personal_cheques = PersonalCheque.objects.filter(**filters)
        personal_cheques_serialized = IssuePersonalChequeSerializer(
            personal_cheques, many=True
        ).data

        accounts_opening_balances = AccountType.objects.all().values(
            account_type__name=F("name"), total=F("opening_balance")
        )

        balance_ledgers = (
            Ledger.objects.values("account_type__name", "nature")
            .order_by("nature")
            .filter(
                date__lte=today,
                account_type__isnull=False,
                # external_cheque__status=ChequeStatusChoices.PENDING,
            )
            .exclude(account_type=cheque_account)
            .annotate(amount=Sum("amount"))
        )

        balance_expenses = (
            ExpenseDetail.objects.values("account_type__name")
            .order_by("date")
            .filter(date__lte=today)
            .annotate(total=Sum("amount"))
        )

        balance_external_cheques = (
            ExternalCheque.objects.values("status")
            .filter(status=ChequeStatusChoices.PENDING)
            .aggregate(total=Sum("amount"))
        )
        balance_external_cheques = balance_external_cheques.get("total", 0)

        balance_external_cheques_history = (
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
            final_account_balances, accounts_opening_balances
        )
        final_account_balances = get_account_balances(
            final_account_balances, balance_external_cheques_history
        )
        final_account_balances = get_account_balances(
            final_account_balances, balance_personal_cheques, "sub"
        )
        final_account_balances = get_account_balances(
            final_account_balances, balance_expenses, "sub"
        )
        if balance_external_cheques is not None:
            final_account_balances.update({"Cheque Account": balance_external_cheques})

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

            account = get_object_or_404(AccountType, id=account)
            filters.update({"account_type": account})
            ledger = Ledger.objects.filter(**filters).values()
            ledger = add_type(ledger, "Ledger entry")

            external_cheque_history = format_cheques_as_ledger(
                ExternalChequeHistory.objects.filter(**filters).values(),
                "C",
                "Party cheque",
            )

            personal_cheques = format_cheques_as_ledger(
                PersonalCheque.objects.filter(
                    **filters, status=PersonalChequeStatusChoices.CLEARED
                ).values(),
                "D",
                "Personal cheque",
            )

            expenses = format_cheques_as_ledger(
                ExpenseDetail.objects.filter(**filters).values(), "D", "Expense"
            )

            final_result = sorted(
                chain(ledger, external_cheque_history, personal_cheques, expenses),
                key=lambda obj: obj["date"],
            )
            paginated = self.paginate_queryset(final_result)
            paginated = self.get_paginated_response(paginated).data
            return Response({"data": paginated}, status=status.HTTP_200_OK)

        except:
            return Response(
                {"error": "Please choose an account type"},
                status=status.HTTP_400_BAD_REQUEST,
            )
