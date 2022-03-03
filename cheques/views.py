from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .choices import ChequeStatusChoices
from .serializers import (
    ExternalChequeHistorySerializer,
    CreateExternalChequeEntrySerializer,
    ExternalChequeHistoryWithChequeSerializer,
    ListExternalChequeHistorySerializer,
    TransferExternalChequeSerializer,
    IssuePersonalChequeSerializer,
    CancelPersonalChequeSerializer,
    PassPersonalChequeSerializer,
    ReIssuePersonalChequeFromReturnedSerializer,
    ReturnPersonalChequeSerializer,
    ExternalChequeSerializer,
)
from .models import (
    ExternalCheque,
    ExternalChequeHistory,
    PersonalCheque,
    ExternalChequeTransfer,
)
from .utils import (
    CHEQUE_ACCOUNT,
    create_ledger_entry_for_cheque,
    has_history,
    get_cheque_account,
)
from .choices import PersonalChequeStatusChoices

from essentials.models import AccountType, LinkedAccount

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


class ListExternalCheques(ListAPIView):
    queryset = ExternalCheque.objects.all()
    serializer_class = ExternalChequeSerializer
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


def check_cheque_errors(cheque):
    """Get cheque error when passing a cheque"""
    if cheque:
        today = date.today()
        if cheque.due_date > today:
            return return_error("Cheque due date is in future")
        elif cheque.status == ChequeStatusChoices.RETURNED:
            return return_error("Cheque is already returned")
        elif cheque.status != ChequeStatusChoices.PENDING:
            return return_error(f"Cheque is in {cheque.status} state")
        else:
            pass
    else:
        return return_error("Cheque not found")


class PassExternalChequeView(APIView):
    """pass external cheque"""

    def post(self, request):
        cheque = None
        data = request.data
        account_type = AccountType.objects.get(id=data["account_type"])
        cheque = get_object_or_404(ExternalCheque, id=data["cheque"])

        check_cheque_errors(cheque)

        cheque_account = get_cheque_account().account
        remaining_amount = None
        # check if this cheque has any history
        if ExternalChequeHistory.objects.filter(cheque=cheque).exists():
            remaining_amount = ExternalChequeHistory.get_remaining_amount(
                cheque, cheque_account
            )
            is_return_cheque = ExternalChequeHistory.objects.filter(
                return_cheque=cheque
            ).exists()
            # if this cheque has history but is a return cheque then pass it
            if is_return_cheque:
                cheque.status = ChequeStatusChoices.CLEARED
                cheque.save()
                return Response(
                    {"message": "Cheque passed"}, status=status.HTTP_201_CREATED
                )
            if remaining_amount > 0:
                return return_error("This cheque has a history, it can not be passed")

        # check if account type is cheque account
        if cheque_account.id == account_type.id:
            return return_error("Please choose a different account type")

        # if there is remaining amount then create a cheque history for this entry
        if (remaining_amount is None) or (remaining_amount > 0):
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

        cheque.status = ChequeStatusChoices.CLEARED
        if remaining_amount == 0:
            cheque.is_passed_with_history = True
        cheque.save()

        return Response({"message": "Cheque passed"}, status=status.HTTP_201_CREATED)


class TransferExternalChequeView(CreateAPIView):

    queryset = ExternalChequeTransfer.objects.all()
    serializer_class = TransferExternalChequeSerializer


class ReturnExternalTransferredCheque(APIView):
    """return the external transferred cheque"""

    def post(self, request):
        data = request.data
        cheque = get_object_or_404(
            ExternalCheque,
            id=data["cheque"],
            status=ChequeStatusChoices.TRANSFERRED,
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
            return return_error("This cheque has history, it can not be returned")

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
