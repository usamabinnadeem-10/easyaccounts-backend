from collections import defaultdict
from itertools import chain

from authentication.choices import RoleChoices
from authentication.mixins import (
    IsAdminOrReadAdminOrAccountantMixin,
    IsAdminPermissionMixin,
)
from cheques.choices import ChequeStatusChoices, PersonalChequeStatusChoices
from cheques.models import ExternalCheque, ExternalChequeHistory, PersonalCheque
from cheques.serializers import (
    ExternalChequeSerializer,
    IssuePersonalChequeSerializer,
    ShortExternalChequeHistorySerializer,
)
from core.pagination import PaginationHandlerMixin, StandardPagination
from core.utils import convert_date_to_datetime, get_cheque_account
from django.db.models import F, Q, Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from expenses.models import ExpenseDetail
from expenses.serializers import ExpenseDetailSerializer
from ledgers.models import Ledger, LedgerAndDetail
from payments.models import Payment
from payments.serializers import PaymentAndImageListSerializer
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from transactions.models import Transaction
from transactions.serializers import TransactionSerializer

from essentials.choices import PersonChoices

from .models import *
from .queries import (
    AccountTypeQuery,
    AreaQuery,
    PersonQuery,
    ProductCategoryQuery,
    ProductQuery,
    StockQuery,
    WarehouseQuery,
)
from .serializers import *
from .utils import (
    add_type,
    format_cheques_as_ledger,
    format_external_cheques_as_ledger,
    get_account_balances,
)


class CreatePerson(PersonQuery, IsAdminPermissionMixin, CreateAPIView):
    """
    create person
    """

    serializer_class = PersonSerializer


class ListPerson(PersonQuery, IsAdminOrReadAdminOrAccountantMixin, ListAPIView):
    """
    list persons with the option of filtering by person_type
    """

    serializer_class = PersonSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["person_type"]


class CreateWarehouse(WarehouseQuery, IsAdminPermissionMixin, CreateAPIView):
    """
    create warehouse
    """

    serializer_class = WarehouseSerializer


class ListWarehouse(WarehouseQuery, ListAPIView):
    """
    list warehouses
    """

    serializer_class = WarehouseSerializer


class CreateProduct(ProductQuery, IsAdminPermissionMixin, CreateAPIView):
    """
    create product
    """

    serializer_class = ProductSerializer


class ListProduct(ProductQuery, ListAPIView):
    """
    list products
    """

    serializer_class = ProductSerializer


class CreateAccountType(AccountTypeQuery, IsAdminPermissionMixin, CreateAPIView):
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


class CreateProductCategory(ProductCategoryQuery, CreateAPIView):
    """
    create product category
    """

    serializer_class = ProductCategorySerializer


class ListProductCategory(ProductCategoryQuery, ListAPIView):
    """
    list product categories
    """

    serializer_class = ProductCategorySerializer


class DayBook(IsAdminOrReadAdminOrAccountantMixin, APIView):
    """
    get daybook for today or with a specific date
    """

    def get(self, request):
        today = convert_date_to_datetime(self.request.query_params.get("date"))
        today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        branch = request.branch
        filters = {
            "date__gte": today_start,
            "date__lte": today_end,
        }
        person_filter = {}
        if request.role not in [RoleChoices.ADMIN, RoleChoices.ADMIN_VIEWER]:
            person_filter = {"person__person_type": PersonChoices.CUSTOMER}

        cheque_account = get_cheque_account(request.branch).account

        expenses = ExpenseDetail.objects.filter(
            **filters, expense__branch=branch
        ).order_by("serial")
        expenses_serialized = ExpenseDetailSerializer(expenses, many=True)

        transactions = Transaction.objects.filter(
            **person_filter, **filters, person__branch=branch
        )
        transactions_serialized = TransactionSerializer(transactions, many=True).data

        payments = Payment.objects.filter(person__branch=branch, **filters).order_by(
            "serial"
        )
        payments_serialized = PaymentAndImageListSerializer(payments, many=True).data

        person_filter_2 = {}
        if request.role not in [RoleChoices.ADMIN, RoleChoices.ADMIN_VIEWER]:
            person_filter_2 = {
                "ledger_entry__person__person_type": PersonChoices.CUSTOMER
            }
        ledger_details = LedgerAndDetail.objects.values(
            "detail",
            "id",
            amount=F("ledger_entry__amount"),
            date=F("ledger_entry__date"),
            person=F("ledger_entry__person"),
            nature=F("ledger_entry__nature"),
            account_type=F("ledger_entry__account_type"),
        ).filter(**filters, **person_filter_2, ledger_entry__person__branch=branch)

        external_cheques = ExternalCheque.objects.filter(**filters, person__branch=branch)
        external_cheques_serialized = ExternalChequeSerializer(
            external_cheques, many=True
        ).data

        external_cheques_history = (
            ExternalChequeHistory.objects.select_related("parent_cheque")
            .filter(**filters, parent_cheque__person__branch=branch)
            .exclude(return_cheque__status=ChequeStatusChoices.RETURNED)
            .order_by("parent_cheque__serial")
        )
        external_cheques_history_serialized = ShortExternalChequeHistorySerializer(
            external_cheques_history, many=True
        ).data

        personal_cheques = PersonalCheque.objects.filter(
            **filters, **person_filter, person__branch=branch
        )
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
                date__lte=today, account_type__isnull=False, person__branch=request.branch
            )
            .exclude(account_type=cheque_account)
            .annotate(amount=Sum("amount"))
        )

        balance_expenses = (
            ExpenseDetail.objects.values("account_type__name")
            .order_by("date")
            .filter(date__lte=today, expense__branch=request.branch)
            .annotate(total=Sum("amount"))
        )

        balance_external_cheques = (
            ExternalCheque.objects.values("status")
            .filter(
                status=ChequeStatusChoices.PENDING,
                date__lte=today_end,
                person__branch=branch,
            )
            .aggregate(total=Sum("amount"))
        )
        balance_external_cheques = balance_external_cheques.get("total", 0)

        num_of_pending_cheques = ExternalCheque.objects.filter(
            status=ChequeStatusChoices.PENDING, date__lte=today_end
        ).count()

        balance_external_cheques_history = (
            ExternalChequeHistory.objects.values(
                "account_type__name",
            )
            .filter(
                return_cheque__isnull=True,
                date__lte=today_end,
                parent_cheque__person__branch=branch,
            )
            .annotate(total=Sum("amount"))
        )

        balance_personal_cheques = (
            PersonalCheque.objects.values("account_type__name")
            .filter(
                status=PersonalChequeStatusChoices.CLEARED,
                date__lte=today_end,
                person__branch=branch,
            )
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
            final_account_balances.update({"Pending cheques": num_of_pending_cheques})

        return Response(
            {
                "expenses": expenses_serialized.data,
                "payments": payments_serialized,
                "transactions": transactions_serialized,
                "balance_ledgers": final_account_balances,
                "balance_expenses": balance_expenses,
                "external_cheques": external_cheques_serialized,
                "external_cheques_history": external_cheques_history_serialized,
                "personal_cheques": personal_cheques_serialized,
                "ledger_details": ledger_details,
            },
            status=status.HTTP_200_OK,
        )


class GetStockQuantity(StockQuery, ListAPIView):

    serializer_class = StockSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "stock_quantity": ["gte", "lte"],
        "product": ["exact"],
        "product__category": ["exact"],
        "warehouse": ["exact"],
        "yards_per_piece": ["gte", "lte", "exact"],
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        qp = self.request.query_params
        if qp.get("outcut") and qp.get("outcut") == "True":
            return queryset.filter(~Q(yards_per_piece=44) & ~Q(yards_per_piece=66))
        return queryset


class GetAccountHistory(
    APIView, IsAdminOrReadAdminOrAccountantMixin, PaginationHandlerMixin
):
    """Get account history for a specific account type"""

    pagination_class = StandardPagination

    def get(self, request):
        try:
            qp = request.query_params
            account = qp.get("account")
            branch = request.branch
            filters = {}
            date_filters = {}
            ledger_detail_date_filter = {}
            start = convert_date_to_datetime(qp.get("start"), True)
            end = convert_date_to_datetime(qp.get("end"), True)
            if start:
                start_date = start.replace(hour=0, minute=0, second=0, microsecond=0)
                date_filters.update({"date__gte": start_date})
                ledger_detail_date_filter.update({"ledger_entry__date__gte": start_date})
            if end:
                end_date = end.replace(hour=23, minute=59, second=59, microsecond=999999)
                date_filters.update({"date__lte": end_date})
                ledger_detail_date_filter.update({"ledger_entry__date__lte": end_date})

            account = get_object_or_404(AccountType, id=account, branch=request.branch)
            cheque_account = get_cheque_account(branch).account

            filters.update({"account_type": account, **date_filters})

            payments = Payment.objects.filter(**filters, person__branch=branch).values(
                "amount", "nature", "serial", "date", "id"
            )
            payments = add_type(payments, "P")

            opening_balance = [
                {
                    "id": account.id,
                    "date": None,
                    "nature": "C" if account.opening_balance >= 0 else "D",
                    "amount": account.opening_balance,
                    "type": "Opening Balance",
                }
            ]
            external_cheques = []
            if account == cheque_account:
                external_cheques = format_external_cheques_as_ledger(
                    ExternalCheque.objects.filter(
                        **date_filters, person__branch=branch
                    ).values("amount", "date", "id", "serial", "status"),
                    "CHE",
                )

            external_cheque_history = format_cheques_as_ledger(
                ExternalChequeHistory.objects.filter(
                    **filters, **date_filters, parent_cheque__person__branch=branch
                )
                .exclude(account_type=cheque_account)
                .values(
                    "amount",
                    "date",
                    "id",
                    serial=F("parent_cheque__serial"),
                ),
                "C",
                "CHE-H",
            )

            personal_cheques = format_cheques_as_ledger(
                PersonalCheque.objects.filter(
                    **filters,
                    **date_filters,
                    status=PersonalChequeStatusChoices.CLEARED,
                    person__branch=branch,
                ).values("amount", "date", "serial", "id"),
                "D",
                "CH-P",
            )

            expenses = format_cheques_as_ledger(
                ExpenseDetail.objects.filter(
                    **filters, **date_filters, expense__branch=branch
                ).values("amount", "date", "serial", "id"),
                "D",
                "E",
            )
            ledger_details = LedgerAndDetail.objects.filter(
                ledger_entry__person__branch=branch,
                ledger_entry__account_type=account,
                **ledger_detail_date_filter,
            ).values(
                "id",
                amount=F("ledger_entry__amount"),
                date=F("ledger_entry__date"),
                nature=F("ledger_entry__nature"),
                serial=F("ledger_entry__person__name"),
            )

            final_result = sorted(
                chain(
                    payments,
                    external_cheques,
                    external_cheque_history,
                    personal_cheques,
                    expenses,
                    ledger_details,
                ),
                key=lambda obj: obj["date"],
            )
            final_result = [*opening_balance, *final_result]
            paginated = self.paginate_queryset(final_result)
            paginated = self.get_paginated_response(paginated).data
            return Response({"data": paginated}, status=status.HTTP_200_OK)

        except Exception:
            return Response(
                {"error": "Please choose an account type"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CreateOpeningStock(StockQuery, IsAdminPermissionMixin, CreateAPIView):

    serializer_class = StockSerializer
