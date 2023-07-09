from datetime import datetime, timedelta
from functools import reduce

from django.db.models import F, Max, Min, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.choices import RoleChoices
from authentication.mixins import (
    IsAdminOrAccountantMixin,
    IsAdminOrReadAdminOrAccountantMixin,
    IsAdminOrReadAdminOrAccountantOrHeadAccountantMixin,
    IsAdminPermissionMixin,
)
from cheques.choices import ChequeStatusChoices
from cheques.models import ExternalCheque, ExternalChequeTransfer, PersonalCheque
from core.pagination import LargePagination
from core.utils import convert_date_to_datetime
from ledgers.models import Ledger, LedgerAndExternalCheque
from ledgers.serializers import LedgerAndDetailSerializer, LedgerSerializer
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log

from .queries import LedgerAndDetailQuery, LedgerQuery


class ListLedger(
    LedgerQuery, IsAdminOrReadAdminOrAccountantOrHeadAccountantMixin, generics.ListAPIView
):
    """
    get ledger of a person by start date, end date, (when passing neither all ledger is returned)
    returns paginated response along with opening balance
    """

    serializer_class = LedgerSerializer
    page_size = 50
    pagination_class = LargePagination

    def filter_queryset(self):
        qp = self.request.query_params
        person = qp.get("person")
        endDate = (
            convert_date_to_datetime(qp.get("end"), True)
            or Ledger.objects.aggregate(date_max=Max("date"))["date_max"]
            or datetime.now()
        )
        filter = {}
        if self.request.role not in [RoleChoices.ADMIN, RoleChoices.ADMIN_VIEWER]:
            filter.update({"person__person_type": "C"})
        return Ledger.objects.select_related(
            "person",
            "account_type",
        ).filter(
            person__branch=self.request.branch,
            person=person,
            date__lte=endDate,
            **filter,
        )

    def list(self, request, *args, **kwargs):
        qp = self.request.query_params
        person = qp.get("person")
        queryset = self.filter_queryset()
        startDate = convert_date_to_datetime(qp.get("start"), True) or (
            queryset.aggregate(Min("date"))["date__min"] or datetime.now()
        )
        balance = (
            queryset.values("nature")
            .order_by("nature")
            .annotate(amount=Sum("amount"))
            .filter(date__lt=startDate)
        )

        branch = request.branch

        balance_external_cheques = LedgerAndExternalCheque.get_external_cheque_balance(
            person, branch
        )
        recovered_external_cheque_amount = ExternalCheque.get_amount_recovered(
            person, branch
        )
        cleared_cheques = LedgerAndExternalCheque.get_passed_cheque_amount(person, branch)

        cleared_transferred_cheques = (
            ExternalCheque.get_sum_of_cleared_transferred_cheques(person, branch)
        )

        PENDING_CHEQUES = balance_external_cheques - (
            recovered_external_cheque_amount
            + cleared_cheques
            + cleared_transferred_cheques
        )
        NUM_OF_PENDING = ExternalCheque.get_number_of_pending_cheques(person, branch)

        persons_transferred_cheques = ExternalCheque.get_sum_of_transferred_cheques(
            person, branch
        )

        # sum of cheques that have been transferred to this person
        balance_cheques = list(
            LedgerAndExternalCheque.objects.values("ledger_entry__nature")
            .order_by("ledger_entry__nature")
            .filter(external_cheque__status=ChequeStatusChoices.TRANSFERRED)
            .annotate(amount=Sum("external_cheque__amount"))
        )
        sum_of_transferred_to_this_person = reduce(
            lambda prev, curr: prev + curr["amount"], balance_cheques, 0
        )
        sum_of_transferred_to_this_person = ExternalChequeTransfer.sum_of_transferred(
            person, branch
        )

        personal_cheque_balance = PersonalCheque.get_pending_cheques(person, branch)

        opening_balance = reduce(
            lambda prev, curr: prev
            + (curr["amount"] if curr["nature"] == "C" else -curr["amount"]),
            balance,
            0,
        )

        ledger_data = LedgerSerializer(
            self.paginate_queryset(
                queryset.filter(date__gte=startDate).order_by(
                    F("date"),
                    # F("ledger_transaction__serial").asc(nulls_last=False),
                    F("time_stamp"),
                )
            ),
            many=True,
        ).data
        page = self.get_paginated_response(ledger_data)
        page.data["opening_balance"] = opening_balance
        page.data["pending_cheques"] = PENDING_CHEQUES
        page.data["pending_cheques_count"] = NUM_OF_PENDING
        page.data["transferred_cheques"] = persons_transferred_cheques
        page.data["transferred_to_this_person"] = sum_of_transferred_to_this_person
        page.data["personal_pending"] = personal_cheque_balance

        return Response(page.data, status=status.HTTP_200_OK)


class DeleteLedgerDetail(LedgerQuery, IsAdminPermissionMixin, generics.DestroyAPIView):
    """
    Delete a ledger record (only admin can delete)
    """

    serializer_class = LedgerSerializer

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        Log.create_log(
            ActivityTypes.DELETED,
            ActivityCategory.LEDGER_ENTRY,
            f"{instance.get_nature_display()} for {instance.person.name} for amount {instance.amount}/= from {instance.date}",
            self.request,
        )

    # def perform_update(self, serializer):
    #     instance = self.get_object()
    #     super().perform_update(serializer)
    #     updated = self.get_object()
    #     Log.create_log(
    #         ActivityTypes.EDITED,
    #         ActivityCategory.LEDGER_ENTRY,
    #         f"{instance.date} of type {instance.get_nature_display()} for {instance.person.name} for amount {instance.amount}/= to --> {updated.date} of type {updated.get_nature_display()} for {updated.person.name} for amount {updated.amount}",
    #         self.request,
    #     )


class GetAllBalances(IsAdminOrAccountantMixin, APIView):
    """
    Get all balances
    Expects a query parameter person (S or C)
    Optional qp balance for balances gte or lte
    """

    def get(self, request):
        filters = {"person__branch": request.branch}

        if request.role not in [RoleChoices.ADMIN, RoleChoices.ADMIN_VIEWER]:
            filters.update({"person__person_type": "C"})

        if request.query_params.get("person"):
            filters.update({"person__person_type": request.query_params.get("person")})
        if request.query_params.get("person_id"):
            filters.update({"person": request.query_params.get("person_id")})

        balances = (
            Ledger.objects.filter(**filters)
            .values("nature", "person")
            .order_by("nature")
            .annotate(balance=Sum("amount"))
        )

        data = {}
        for b in balances:
            name = str(b["person"])
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


class FilterLedger(LedgerQuery, generics.ListAPIView):
    """
    filter ledger records
    """

    serializer_class = LedgerSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte"],
        "amount": ["gte", "lte"],
        "account_type": ["exact"],
        "detail": ["icontains"],
        "nature": ["exact"],
        "person": ["exact"],
    }


class LedgerAndDetailEntry(
    LedgerAndDetailQuery,
    IsAdminOrAccountantMixin,
    generics.CreateAPIView,
):
    serializer_class = LedgerAndDetailSerializer


class UpdateLedgerAndDetailEntry(
    LedgerAndDetailQuery,
    IsAdminPermissionMixin,
    generics.UpdateAPIView,
):
    serializer_class = LedgerAndDetailSerializer
