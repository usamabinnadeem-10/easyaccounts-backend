from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .choices import ChequeStatusChoices
from .serializers import *
from .models import *

from datetime import date


def return_error(error_msg):
    return Response(
        {"error": error_msg},
        status=status.HTTP_400_BAD_REQUEST,
    )


class CreateExternalChequeEntryView(CreateAPIView):
    """create external cheque"""

    queryset = ExternalCheque.objects.all()
    serializer_class = CreateExternalChequeEntrySerializer


class CreateExternalChequeHistoryView(CreateAPIView):
    """create external cheque's history (does not allow cheque account)"""

    queryset = ExternalChequeHistory.objects.all()
    serializer_class = ExternalChequeHistorySerializer


class CreateExternalChequeHistoryWithChequeView(CreateAPIView):
    """create external cheque history (only cheque account allowed)"""

    queryset = ExternalChequeHistory.objects.all()
    serializer_class = ExternalChequeHistoryWithChequeSerializer


class GetExternalChequeHistory(ListAPIView):

    queryset = ExternalCheque.objects.all()
    serializer_class = ListExternalChequeHistorySerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "id": ["exact"],
        "date": ["gte", "lte", "exact"],
        "due_date": ["gte", "lte", "exact"],
        "cheque_number": ["contains"],
        "serial": ["gte", "lte", "exact"],
        "status": ["exact"],
        "amount": ["gte", "lte", "exact"],
        "bank": ["exact"],
        "person": ["exact"],
    }


def get_cheque_error(cheque):
    """Get cheque error when passing a cheque"""
    if cheque:
        today = date.today()
        if cheque.due_date > today:
            return "Cheque due date is in future"
        elif cheque.is_returned:
            return "Cheque is already returned"
        elif cheque.status != ChequeStatusChoices.PENDING:
            return f"Cheque is in {cheque.status} state"
        else:
            return "Oops, something went wrong"
    else:
        return "Cheque not found"


class PassExternalChequeView(APIView):
    """pass external cheque"""

    def post(self, request):
        cheque = None
        try:
            data = request.data
            account_type = get_object_or_404(AccountType, id=data["account_type"])
            cheque = get_object_or_404(
                ExternalCheque,
                id=data["cheque"],
                due_date__lte=date.today(),
                is_returned=False,
                status=ChequeStatusChoices.PENDING,
            )
        except:
            return_error(
                get_cheque_error(ExternalCheque.objects.get(id=data["cheque"]))
            )

        # check if this cheque has any history
        if ExternalChequeHistory.objects.filter(cheque=cheque).exists():
            return_error("This cheque has a history, it can not be passed")

        # check if account type is cheque account
        if LinkedAccount.objects.get(name=CHEQUE_ACCOUNT).account.id == account_type.id:
            return_error("Please choose a different account type")

        prev_history = ExternalChequeHistory.objects.filter(return_cheque=cheque)
        parent = None
        if prev_history.exists():
            parent = prev_history[0].parent_cheque
        else:
            parent = cheque

        ExternalChequeHistory.objects.create(
            parent_cheque=parent,
            cheque=cheque,
            account_type=account_type,
            amount=cheque.amount,
        )

        cheque.status = ChequeStatusChoices.COMPLETED
        cheque.save()

        return Response({"message": "Cheque passed"}, status=status.HTTP_201_CREATED)


class TransferExternalChequeView(CreateAPIView):

    queryset = ExternalChequeTransfer.objects.all()
    serializer_class = TransferExternalChequeSerializer


class ReturnExternalTransferredCheque(APIView):
    """return the external transferred cheque"""

    def post(self, request):
        data = request.data
        try:
            cheque = get_object_or_404(
                ExternalCheque,
                id=data["cheque"],
                status=ChequeStatusChoices.TRANSFERRED,
            )
        except:
            return_error("Cheque not found")

        transfer = ExternalChequeTransfer.objects.get(
            cheque=cheque,
        )

        # create a credit entry in the ledger of the person the cheque is being returned from
        create_ledger_entry_for_cheque(cheque, "C", True, transfer.person)

        # set the state of cheque as PENDING
        cheque.status = ChequeStatusChoices.PENDING
        cheque.save()

        # delete the transfer entry
        transfer.delete()

        return Response(
            {"message": "Cheque returned successfully"}, status=status.HTTP_201_CREATED
        )


class ReturnExternalCheque(APIView):
    """return external cheque from the person it came from"""

    def post(self, request):
        data = request.data
        try:
            cheque = get_object_or_404(
                ExternalCheque,
                id=data["cheque"],
                status=ChequeStatusChoices.PENDING,
            )
        except:
            return Response(
                {"error": "Cheque not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # make sure cheque does not have a history
        if has_history(cheque):
            return_error("This cheque has history, it can not be returned")

        create_ledger_entry_for_cheque(cheque, "D")
        cheque.status = ChequeStatusChoices.RETURNED
        cheque.save()

        return Response(
            {"message": "Cheque returned successfully"}, status=status.HTTP_201_CREATED
        )


class IssuePersonalChequeView(CreateAPIView):
    """Issue personal cheque view"""

    queryset = PersonalCheque.objects.all()
    serializer_class = IssuePersonalChequeSerializer


class ReturnPersonalChequeView(CreateAPIView):
    """return personal cheque from a person"""

    serializer_class = ReturnPersonalChequeSerializer
    queryset = PersonalCheque.objects.all()


class ReIssuePersonalChequeFromReturnedView(CreateAPIView):
    """issue a personal cheque which was returned by a person"""

    serializer_class = ReIssuePersonalChequeFromReturnedSerializer
    queryset = PersonalCheque.objects.all()


class PassPersonalChequeView(UpdateAPIView):
    """set the status of cheque from pending to completed"""

    serializer_class = PassPersonalChequeSerializer
    queryset = PersonalCheque.objects.filter(status=PersonalChequeStatusChoices.PENDING)


class CancelPersonalChequeView(UpdateAPIView):
    """set the status of cheque from returned to cancelled"""

    serializer_class = CancelPersonalChequeSerializer
    queryset = PersonalCheque.objects.filter(
        status=PersonalChequeStatusChoices.RETURNED
    )


class ListPersonalChequeView(ListAPIView):
    queryset = PersonalCheque.objects.all()
    serializer_class = IssuePersonalChequeSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "id": ["exact"],
        "date": ["gte", "lte", "exact"],
        "due_date": ["gte", "lte", "exact"],
        "cheque_number": ["contains"],
        "serial": ["gte", "lte", "exact"],
        "status": ["exact"],
        "amount": ["gte", "lte", "exact"],
        "bank": ["exact"],
        "person": ["exact"],
        "account_type": ["exact"],
    }
