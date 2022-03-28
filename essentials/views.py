from collections import defaultdict
from datetime import date, datetime
from itertools import chain

from cheques.choices import ChequeStatusChoices, PersonalChequeStatusChoices
from cheques.models import ExternalCheque, ExternalChequeHistory, PersonalCheque
from cheques.serializers import (
    ExternalChequeSerializer,
    IssuePersonalChequeSerializer,
    ShortExternalChequeHistorySerializer,
)
from cheques.utils import get_cheque_account
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from expenses.models import ExpenseDetail
from expenses.serializers import ExpenseDetailSerializer
from ledgers.models import Ledger
from ledgers.serializers import LedgerSerializer
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from transactions.models import Transaction
from transactions.serializers import TransactionSerializer

from essentials.choices import PersonChoices
from essentials.pagination import CustomPagination, PaginationHandlerMixin

from .models import *
from .queries import (
    AccountTypeQuery,
    AreaQuery,
    PersonQuery,
    ProductQuery,
    StockQuery,
    WarehouseQuery,
)
from .serializers import *
from .utils import add_type, format_cheques_as_ledger, get_account_balances


class CreatePerson(PersonQuery, CreateAPIView):
    """
    create person
    """

    serializer_class = PersonSerializer


class ListPerson(PersonQuery, ListAPIView):
    """
    list persons with the option of filtering by person_type
    """

    serializer_class = PersonSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["person_type"]


class CreateWarehouse(WarehouseQuery, CreateAPIView):
    """
    create warehouse
    """

    serializer_class = WarehouseSerializer


class ListWarehouse(WarehouseQuery, ListAPIView):
    """
    list warehouses
    """

    serializer_class = WarehouseSerializer


class CreateProduct(ProductQuery, CreateAPIView):
    """
    create product
    """

    serializer_class = ProductSerializer


class ListProduct(ProductQuery, ListAPIView):
    """
    list products
    """

    serializer_class = ProductSerializer


class CreateAccountType(AccountTypeQuery, CreateAPIView):
    """
    create account type
    """

    serializer_class = AccountTypeSerializer


class ListAccountType(AccountTypeQuery, ListAPIView):
    """
    list account types
    """

    serializer_class = AccountTypeSerializer


class CreateArea(AreaQuery, CreateAPIView):
    """
    create area
    """

    serializer_class = AreaSerializer


class ListArea(AreaQuery, ListAPIView):
    """
    list areas
    """

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
            "branch": request.branch,
        }

        cheque_account = get_cheque_account(request.branch).account

        expenses = ExpenseDetail.objects.filter(**filters)
        expenses_serialized = ExpenseDetailSerializer(expenses, many=True)

        ledgers = Ledger.objects.filter(
            person__person_type=PersonChoices.CUSTOMER, **filters
        )
        ledger_serialized = LedgerSerializer(ledgers, many=True)

        transactions = Transaction.objects.filter(
            person__person_type=PersonChoices.CUSTOMER, **filters
        )
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

        accounts_opening_balances = AccountType.objects.filter(
            branch=request.branch
        ).values(account_type__name=F("name"), total=F("opening_balance"))

        balance_ledgers = (
            Ledger.objects.values("account_type__name", "nature")
            .order_by("nature")
            .filter(
                date__lte=today,
                account_type__isnull=False,
                branch=request.branch
                # external_cheque__status=ChequeStatusChoices.PENDING,
            )
            .exclude(account_type=cheque_account)
            .annotate(amount=Sum("amount"))
        )

        balance_expenses = (
            ExpenseDetail.objects.values("account_type__name")
            .order_by("date")
            .filter(date__lte=today, branch=request.branch)
            .annotate(total=Sum("amount"))
        )

        balance_external_cheques = (
            ExternalCheque.objects.values("status")
            .filter(status=ChequeStatusChoices.PENDING, **filters)
            .aggregate(total=Sum("amount"))
        )
        balance_external_cheques = balance_external_cheques.get("total", 0)

        balance_external_cheques_history = (
            ExternalChequeHistory.objects.values(
                "account_type__name",
            )
            .filter(return_cheque__isnull=True, **filters)
            .annotate(total=Sum("amount"))
        )

        balance_personal_cheques = (
            PersonalCheque.objects.values("account_type__name")
            .filter(status=PersonalChequeStatusChoices.CLEARED, **filters)
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


class GetStockQuantity(StockQuery, ListAPIView):

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
            filters = {"branch": request.branch}
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

            account = get_object_or_404(AccountType, id=account, branch=request.branch)
            filters.update({"account_type": account})
            ledger = Ledger.objects.filter(**filters).values()
            ledger = add_type(ledger, "Ledger entry")

            opening_balance = [
                {
                    "id": account.id,
                    "date": None,
                    "nature": "C" if account.opening_balance >= 0 else "D",
                    "amount": account.opening_balance,
                    "type": "Opening Balance",
                }
            ]

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
                chain(
                    ledger,
                    external_cheque_history,
                    personal_cheques,
                    expenses,
                ),
                key=lambda obj: obj["date"],
            )
            final_result = [*opening_balance, *final_result]
            paginated = self.paginate_queryset(final_result)
            paginated = self.get_paginated_response(paginated).data
            return Response({"data": paginated}, status=status.HTTP_200_OK)

        except:
            return Response(
                {"error": "Please choose an account type"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CreateOpeningStock(StockQuery, CreateAPIView):

    serializer_class = StockSerializer
