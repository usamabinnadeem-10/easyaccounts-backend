from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Min, Sum, F

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from essentials.pagination import CustomPagination

from ledgers.models import Ledger
from ledgers.serializers import LedgerSerializer
from cheques.choices import ChequeStatusChoices
from cheques.serializers import get_cheque_account
from cheques.models import ExternalCheque

from datetime import date, datetime, timedelta
from functools import reduce


class CreateOrListLedgerDetail(generics.ListCreateAPIView):
    """
    get ledger of a person by start date, end date, (when passing neither all ledger is returned)
    returns paginated response along with opening balance
    """

    serializer_class = LedgerSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        if self.request.method == "POST":
            return Ledger.objects.all()
        elif self.request.method == "GET":
            qp = self.request.query_params
            person = qp.get("person")
            endDate = qp.get("end") or date.today()
            return Ledger.objects.select_related(
                "person", "account_type", "transaction"
            ).filter(person=person, date__lte=endDate, draft=False)

    def list(self, request, *args, **kwargs):
        qp = self.request.query_params
        queryset = self.get_queryset()

        startDate = (
            datetime.strptime(qp.get("start"), "%Y-%m-%d") if qp.get("start") else None
        ) or (queryset.aggregate(Min("date"))["date__min"] or date.today())
        startDateMinusOne = startDate - timedelta(days=1)
        balance = (
            queryset.values("nature")
            .order_by("nature")
            .annotate(amount=Sum("amount"))
            .filter(date__lte=startDateMinusOne)
        )

        cheque_account = get_cheque_account().account

        # sum all the cheques which have a history, group by nature
        balance_cheques_history = (
            queryset.values(
                "nature",
                "external_cheque__parent_cheque__account_type",
            )
            .order_by("nature")
            .annotate(amount=Sum("external_cheque__parent_cheque__amount"))
        )

        # filter the cheques history which are cheque accounts
        filtered_balance_cheques_history = list(
            filter(
                lambda balance: balance["external_cheque__parent_cheque__account_type"]
                == cheque_account.id,
                balance_cheques_history,
            )
        )

        # get the sum of pending cheques amounts
        cheque_balance_with_history = reduce(
            lambda prev, curr: prev
            + (curr["amount"] if curr["nature"] == "D" else -curr["amount"]),
            filtered_balance_cheques_history,
            0,
        )

        persons_transferred_cheques = ExternalCheque.objects.filter(
            person=qp.get("person"), status=ChequeStatusChoices.TRANSFERRED
        ).aggregate(amount=Sum("amount"))

        # sum of cheques that have been transferred to this person
        balance_cheques = list(
            queryset.values("nature")
            .order_by("nature")
            .filter(external_cheque__status=ChequeStatusChoices.TRANSFERRED)
            .annotate(amount=Sum("external_cheque__amount"))
        )
        sum_of_transferred_to_this_person = reduce(
            lambda prev, curr: prev + curr["amount"], balance_cheques, 0
        )

        opening_balance = reduce(
            lambda prev, curr: prev
            + (curr["amount"] if curr["nature"] == "C" else -curr["amount"]),
            balance,
            0,
        )

        ledger_data = LedgerSerializer(
            self.paginate_queryset(
                queryset.filter(date__gte=startDate).order_by(
                    "date", "transaction__serial"
                )
            ),
            many=True,
        ).data
        page = self.get_paginated_response(ledger_data)
        page.data["opening_balance"] = opening_balance
        page.data["pending_cheques"] = cheque_balance_with_history
        page.data["transferred_cheques"] = persons_transferred_cheques
        page.data["transferred_to_this_person"] = sum_of_transferred_to_this_person

        return Response(page.data, status=status.HTTP_200_OK)


class EditUpdateDeleteLedgerDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Edit / Update / Delete a ledger record
    """

    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer


class GetAllBalances(APIView):
    """
    Get all balances
    Expects a query parameter person (S or C)
    Optional qp balance for balances gte or lte
    """

    def get(self, request):
        filters = {}
        if request.query_params.get("person"):
            filters.update({"person__person_type": request.query_params.get("person")})
        if request.query_params.get("person_id"):
            filters.update({"person": request.query_params.get("person_id")})

        balances = (
            Ledger.objects.values("nature", name=F("person__name"))
            .order_by("nature")
            .annotate(balance=Sum("amount"))
            .filter(**filters)
        )

        data = {}
        for b in balances:
            name = b["name"]
            amount = b["balance"]
            nature = b["nature"]
            if not name in data:
                data[name] = amount if nature == "C" else -amount
            else:
                data[name] += amount if nature == "C" else -amount

        balance_gte = request.query_params.get("balance__gte")
        balance_lte = request.query_params.get("balance__lte")

        if balance_gte or balance_lte:
            final_balances = {}
            if balance_gte:
                for person, balance in data.items():
                    if balance >= float(balance_gte):
                        final_balances[person] = balance
            if balance_lte:
                for person, balance in data.items():
                    if balance <= float(balance_lte):
                        final_balances[person] = balance

            return Response(final_balances, status=status.HTTP_200_OK)

        return Response(data, status=status.HTTP_200_OK)


class FilterLedger(generics.ListAPIView):
    """
    filter ledger records
    """

    serializer_class = LedgerSerializer
    queryset = Ledger.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte"],
        "amount": ["gte", "lte"],
        "account_type": ["exact"],
        "detail": ["icontains"],
        "nature": ["exact"],
        "person": ["exact"],
    }
