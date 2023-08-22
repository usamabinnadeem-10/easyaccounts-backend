from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

import authentication.constants as PERMISSIONS
from authentication.mixins import CheckPermissionsMixin
from core.utils import check_permission
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log

from .queries import ExpenseAccountQuery, ExpenseDetailQuery
from .serializers import ExpenseAccountSerializer, ExpenseDetailSerializer


class ListExpenseAccount(
    ExpenseAccountQuery, CheckPermissionsMixin, generics.ListAPIView
):
    """
    create expense account or list all expense accounts
    """

    permissions = [PERMISSIONS.CAN_VIEW_EXPENSE_ACCOUNTS]
    serializer_class = ExpenseAccountSerializer


class CreateExpenseAccount(
    ExpenseAccountQuery, CheckPermissionsMixin, generics.CreateAPIView
):
    """
    create expense account or list all expense accounts
    """

    permissions = [PERMISSIONS.CAN_CREATE_EXPENSE_ACCOUNT]
    serializer_class = ExpenseAccountSerializer


class ListExpenseDetail(ExpenseDetailQuery, CheckPermissionsMixin, generics.ListAPIView):
    """
    get expense details with optional filters
    """

    permissions = [PERMISSIONS.CAN_VIEW_EXPENSES]
    serializer_class = ExpenseDetailSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte", "exact"],
        "amount": ["gte", "lte", "exact"],
        "serial": ["gte", "lte", "exact"],
        "account_type": ["exact"],
        "expense__type": ["exact"],
        "detail": ["icontains"],
        "expense": ["exact"],
    }


class CreateExpenseDetail(
    ExpenseDetailQuery, CheckPermissionsMixin, generics.CreateAPIView
):
    """
    get expense details with optional filters
    """

    permissions = [PERMISSIONS.CAN_CREATE_EXPENSE]
    serializer_class = ExpenseDetailSerializer


class EditExpenseDetail(
    ExpenseDetailQuery,
    CheckPermissionsMixin,
    generics.UpdateAPIView,
):
    """
    Edit an expense record
    """

    permissions = [PERMISSIONS.CAN_EDIT_EXPENSE]
    serializer_class = ExpenseDetailSerializer

    def perform_update(self, serializer):
        instance = self.get_object()
        super().perform_update(serializer)
        Log.create_log(
            ActivityTypes.EDITED,
            ActivityCategory.EXPENSE,
            f"'{instance.account_type.name}' for {instance.amount}/=",
            self.request,
        )


class DeleteExpenseDetail(
    ExpenseDetailQuery,
    CheckPermissionsMixin,
    generics.DestroyAPIView,
):
    """
    Delete an expense record
    """

    permissions = [PERMISSIONS.CAN_DELETE_EXPENSE]
    serializer_class = ExpenseDetailSerializer

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        Log.create_log(
            ActivityTypes.DELETED,
            ActivityCategory.EXPENSE,
            f"'{instance.account_type.name}' for {instance.amount}/=",
            self.request,
        )


class ViewSingleExpense(
    ExpenseDetailQuery,
    CheckPermissionsMixin,
    generics.RetrieveAPIView,
):
    """
    View an expense record
    """

    permissions = [PERMISSIONS.CAN_VIEW_EXPENSES]
    serializer_class = ExpenseDetailSerializer
