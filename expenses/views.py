from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from authentication.mixins import (
    IsAdminOrAccountantMixin,
    IsAdminOrAccountantOrHeadAccountantMixin,
    IsAdminPermissionMixin,
)
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log

from .queries import ExpenseAccountQuery, ExpenseDetailQuery
from .serializers import ExpenseAccountSerializer, ExpenseDetailSerializer


class ListExpenseAccount(ExpenseAccountQuery, generics.ListAPIView):
    """
    create expense account or list all expense accounts
    """

    serializer_class = ExpenseAccountSerializer


class CreateExpenseAccount(
    ExpenseAccountQuery, IsAdminPermissionMixin, generics.CreateAPIView
):
    """
    create expense account or list all expense accounts
    """

    serializer_class = ExpenseAccountSerializer


class ListExpenseDetail(ExpenseDetailQuery, generics.ListAPIView):
    """
    get expense details with optional filters
    """

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
    ExpenseDetailQuery, IsAdminOrAccountantMixin, generics.CreateAPIView
):
    """
    get expense details with optional filters
    """

    serializer_class = ExpenseDetailSerializer


class EditUpdateDeleteExpenseDetail(
    ExpenseDetailQuery,
    IsAdminOrAccountantOrHeadAccountantMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    """
    Edit / Update / Delete an expense record
    """

    serializer_class = ExpenseDetailSerializer

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        Log.create_log(
            ActivityTypes.DELETED,
            ActivityCategory.EXPENSE,
            f"'{instance.account_type.name}' for {instance.amount}/=",
            self.request,
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        super().perform_update(serializer)
        Log.create_log(
            ActivityTypes.EDITED,
            ActivityCategory.EXPENSE,
            f"'{instance.account_type.name}' for {instance.amount}/=",
            self.request,
        )
