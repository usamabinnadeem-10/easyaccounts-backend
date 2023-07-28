from datetime import date

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.mixins import (
    IsAdminOrAccountantOrHeadAccountantMixin,
    IsAdminOrReadAdminOrAccountantOrHeadAccountantMixin,
    IsAdminPermissionMixin,
)
from essentials.models import AccountType
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log

from .choices import ChequeStatusChoices, PersonalChequeStatusChoices
from .models import ExternalCheque, ExternalChequeHistory, ExternalChequeTransfer
from .queries import (
    ExternalChequeHistoryQuery,
    ExternalChequeQuery,
    ExternalChequeTransferQuery,
    PersonalChequeQuery,
)
from .serializers import (
    CancelPersonalChequeSerializer,
    CompleteExternalTransferChequeSerializer,
    CreateExternalChequeEntrySerializer,
    ExternalChequeHistorySerializer,
    ExternalChequeHistoryWithChequeSerializer,
    ExternalChequeSerializer,
    IssuePersonalChequeSerializer,
    ListExternalChequeHistorySerializer,
    PassPersonalChequeSerializer,
    ReIssuePersonalChequeFromReturnedSerializer,
    ReturnPersonalChequeSerializer,
    TransferExternalChequeSerializer,
)
from .utils import create_ledger_entry_for_cheque, get_cheque_account, has_history


def return_error(error_msg):
    return Response(
        {"error": error_msg},
        status=status.HTTP_400_BAD_REQUEST,
    )


class CreateExternalChequeEntryView(
    IsAdminOrAccountantOrHeadAccountantMixin, ExternalChequeQuery, CreateAPIView
):
    """create external cheque"""

    serializer_class = CreateExternalChequeEntrySerializer


class CreateExternalChequeHistoryView(
    IsAdminOrAccountantOrHeadAccountantMixin, ExternalChequeHistoryQuery, CreateAPIView
):
    """create external cheque's history (does not allow cheque account)"""

    serializer_class = ExternalChequeHistorySerializer


class CreateExternalChequeHistoryWithChequeView(
    IsAdminOrAccountantOrHeadAccountantMixin, ExternalChequeHistoryQuery, CreateAPIView
):
    """create external cheque history (only cheque account allowed)"""

    serializer_class = ExternalChequeHistoryWithChequeSerializer


class GetExternalChequeHistory(
    IsAdminOrReadAdminOrAccountantOrHeadAccountantMixin, ExternalChequeQuery, ListAPIView
):
    """get detailed history of external cheque"""

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


class ListExternalCheques(
    IsAdminOrReadAdminOrAccountantOrHeadAccountantMixin, ExternalChequeQuery, ListAPIView
):
    """list and filter external cheques"""

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


class PassExternalChequeView(IsAdminOrAccountantOrHeadAccountantMixin, APIView):
    """pass external cheque"""

    def post(self, request):
        cheque = None
        data = request.data
        branch = request.branch
        account_type = AccountType.objects.get(id=data["account_type"], branch=branch)
        date = data["date"]
        if date:
            date = {"date": date}
        else:
            date = {}
        cheque = get_object_or_404(
            ExternalCheque, id=data["cheque"], person__branch=branch
        )

        check_cheque_errors(cheque)

        # if this cheque has history then it can not be passed like this
        if has_history(cheque, branch):
            return return_error("This cheque has a history, it can not be passed")

        cheque_account = get_cheque_account(branch).account
        remaining_amount = None
        # check if this cheque has any history
        if ExternalChequeHistory.objects.filter(
            cheque=cheque, parent_cheque__person__branch=branch
        ).exists():
            remaining_amount = ExternalChequeHistory.get_remaining_amount(
                cheque, cheque_account, branch
            )
            is_return_cheque = ExternalChequeHistory.objects.filter(
                return_cheque=cheque, parent_cheque__person__branch=branch
            ).exists()
            # if this cheque has history but is a return cheque then pass it
            if is_return_cheque:
                cheque.status = ChequeStatusChoices.CLEARED
                cheque.save()
                return Response(
                    {"message": "Cheque passed"}, status=status.HTTP_201_CREATED
                )
            # if remaining_amount > 0:
            #     return return_error("This cheque has a history, it can not be passed")

        # check if account type is cheque account
        if cheque_account.id == account_type.id:
            return return_error("Please choose a different account type")

        # if there is remaining amount then create a cheque history for this entry
        if (remaining_amount is None) or (remaining_amount > 0):
            prev_history = ExternalChequeHistory.objects.filter(
                return_cheque=cheque, parent_cheque__person__branch=branch
            )
            parent = None
            if prev_history.exists():
                parent = prev_history[0].parent_cheque
            else:
                parent = cheque

            history = ExternalChequeHistory.objects.create(
                parent_cheque=parent,
                cheque=cheque,
                account_type=account_type,
                amount=cheque.amount,
                user=request.user,
                **date,
            )

        Log.create_log(
            ActivityTypes.EDITED,
            ActivityCategory.EXTERNAL_CHEQUE,
            f"CHE-{parent.serial} passed on {history.date}",
            request,
        )

        cheque.status = ChequeStatusChoices.CLEARED
        if remaining_amount == 0:
            cheque.is_passed_with_history = True
        cheque.save()

        return Response({"message": "Cheque passed"}, status=status.HTTP_201_CREATED)


class TransferExternalChequeView(
    IsAdminOrAccountantOrHeadAccountantMixin, ExternalChequeTransferQuery, CreateAPIView
):
    """transfer external cheque of a party"""

    serializer_class = TransferExternalChequeSerializer


class CompleteExternalTransferChequeView(
    IsAdminOrAccountantOrHeadAccountantMixin, ExternalChequeQuery, UpdateAPIView
):
    """transfer external cheque of a party"""

    serializer_class = CompleteExternalTransferChequeSerializer


class ReturnExternalTransferredCheque(IsAdminOrAccountantOrHeadAccountantMixin, APIView):
    """return the external transferred cheque"""

    def post(self, request):
        data = request.data
        branch = request.branch
        cheque = get_object_or_404(
            ExternalCheque,
            id=data["cheque"],
            status=ChequeStatusChoices.TRANSFERRED,
            person__branch=branch,
        )

        transfer = ExternalChequeTransfer.objects.get(
            cheque=cheque, person__branch=branch
        )

        log_string = (
            f"CHE-{transfer.cheque.serial} transferred back from {transfer.person.name}"
        )

        # create a credit entry in the ledger of the person the cheque is being returned from
        create_ledger_entry_for_cheque(
            cheque, "C", True, transfer.person, **{"date": data["date"]}
        )

        # set the state of cheque as PENDING
        cheque.status = ChequeStatusChoices.PENDING
        cheque.save()

        # delete the transfer entry
        transfer.delete()

        Log.create_log(
            ActivityTypes.EDITED,
            ActivityCategory.EXTERNAL_CHEQUE,
            log_string,
            request,
        )

        return Response(
            {"message": "Cheque returned successfully"}, status=status.HTTP_201_CREATED
        )


class ReturnExternalCheque(IsAdminOrAccountantOrHeadAccountantMixin, APIView):
    """return external cheque from the person it came from"""

    def post(self, request):
        data = request.data
        branch = request.branch
        try:
            cheque = get_object_or_404(
                ExternalCheque,
                id=data["cheque"],
                status=ChequeStatusChoices.PENDING,
                person__branch=branch,
            )
        except:
            return Response(
                {"error": "Cheque not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # make sure cheque does not have a history
        if has_history(cheque, branch):
            return return_error("This cheque has history, it can not be returned")

        create_ledger_entry_for_cheque(cheque, "D", **{"date": data["date"]})
        cheque.status = ChequeStatusChoices.RETURNED
        cheque.save()

        Log.create_log(
            ActivityTypes.EDITED,
            ActivityCategory.EXTERNAL_CHEQUE,
            f"CHE-{cheque.serial} returned to {cheque.person.name}",
            request,
        )

        return Response(
            {"message": "Cheque returned successfully"}, status=status.HTTP_201_CREATED
        )


class CompleteExternalChequeWithHistory(
    IsAdminOrAccountantOrHeadAccountantMixin, APIView
):
    """complete external cheque that has a history"""

    def post(self, request):
        data = request.data
        branch = request.branch
        try:
            cheque = get_object_or_404(
                ExternalCheque,
                id=data["cheque"],
                status=ChequeStatusChoices.PENDING,
                person__branch=branch,
            )
        except:
            return Response(
                {"error": "Cheque not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # make sure that the cheque has a history
        if not has_history(cheque, branch):
            return return_error("This cheque has no history, it can not be completed")

        amount_left = ExternalChequeHistory.get_remaining_amount(
            cheque, get_cheque_account(branch).account, branch
        )
        # make sure the amount received is not less than cheque's value
        if amount_left > 0:
            return return_error(
                f"This cheque has remaining amount, it can not be completed. Remaining = {amount_left}/="
            )

        cheque.status = ChequeStatusChoices.COMPLETED_HISTORY
        cheque.save()

        Log.create_log(
            ActivityTypes.EDITED,
            ActivityCategory.EXTERNAL_CHEQUE,
            f"CHE-{cheque.serial} history completed",
            request,
        )

        return Response(
            {"message": "Cheque history completed"}, status=status.HTTP_201_CREATED
        )


class IssuePersonalChequeView(IsAdminPermissionMixin, PersonalChequeQuery, CreateAPIView):
    """Issue personal cheque view"""

    serializer_class = IssuePersonalChequeSerializer


class ReturnPersonalChequeView(
    IsAdminPermissionMixin, PersonalChequeQuery, CreateAPIView
):
    """return personal cheque from a person"""

    serializer_class = ReturnPersonalChequeSerializer


class ReIssuePersonalChequeFromReturnedView(
    IsAdminPermissionMixin, PersonalChequeQuery, CreateAPIView
):
    """issue a personal cheque which was returned by a person"""

    serializer_class = ReIssuePersonalChequeFromReturnedSerializer


class PassPersonalChequeView(IsAdminPermissionMixin, PersonalChequeQuery, UpdateAPIView):
    """set the status of cheque from pending to completed"""

    serializer_class = PassPersonalChequeSerializer

    def get_queryset(self):
        return super().get_queryset().filter(status=PersonalChequeStatusChoices.PENDING)


class CancelPersonalChequeView(
    IsAdminPermissionMixin, PersonalChequeQuery, UpdateAPIView
):
    """set the status of cheque from returned to cancelled"""

    serializer_class = CancelPersonalChequeSerializer

    def get_queryset(self):
        return super().get_queryset().filter(status=PersonalChequeStatusChoices.RETURNED)


class ListPersonalChequeView(
    IsAdminOrReadAdminOrAccountantOrHeadAccountantMixin, PersonalChequeQuery, ListAPIView
):
    """list and filter personal cheques"""

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


class DeleteExternalChequeView(
    IsAdminPermissionMixin, ExternalChequeQuery, DestroyAPIView
):
    """delete external cheque"""

    serializer_class = ExternalChequeSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        log_string = f"CHE-{instance.serial} deleted"
        self.perform_destroy(instance)

        Log.create_log(
            ActivityTypes.DELETED, ActivityCategory.EXTERNAL_CHEQUE, log_string, request
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class DeleteExternalChequeHistoryView(
    IsAdminPermissionMixin, ExternalChequeHistoryQuery, DestroyAPIView
):
    """delete external cheque history"""

    serializer_class = ExternalChequeHistorySerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        print(instance)
        if instance.return_cheque:
            return Response(
                {"error": "Please delete the cheque itself"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeletePersonalChequeView(
    IsAdminPermissionMixin, PersonalChequeQuery, DestroyAPIView
):
    """delete personal cheque"""

    serializer_class = IssuePersonalChequeSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        log_string = f"CHP-{instance.serial} deleted"
        self.perform_destroy(instance)

        Log.create_log(
            ActivityTypes.DELETED, ActivityCategory.EXTERNAL_CHEQUE, log_string, request
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
