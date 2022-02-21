from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .choices import ChequeStatusChoices
from .serializers import *
from .models import *
from ledgers.models import Ledger

from datetime import date


class CreateExternalChequeEntryView(CreateAPIView):

    queryset = ExternalCheque.objects.all()
    serializer_class = CreateExternalChequeEntrySerializer


class CreateExternalChequeHistoryView(CreateAPIView):

    queryset = ExternalChequeHistory.objects.all()
    serializer_class = ExternalChequeHistorySerializer


class CreateExternalChequeHistoryWithChequeView(CreateAPIView):

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
            return Response(
                {
                    "error": get_cheque_error(
                        ExternalCheque.objects.get(id=data["cheque"])
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # check if this cheque has any history
        if ExternalChequeHistory.objects.filter(cheque=cheque).exists():
            return Response(
                {"error": "This cheque has a history, it can not be passed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # check if account type is cheque account
        if LinkedAccount.objects.get(name=CHEQUE_ACCOUNT).account.id == account_type.id:
            return Response(
                {"error": "Please choose a different account type"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
    def post(self, request):
        data = request.data
        try:
            cheque = get_object_or_404(
                ExternalCheque,
                id=data["cheque"],
                status=ChequeStatusChoices.TRANSFERRED,
            )
        except:
            return Response(
                {"error": "Cheque not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
