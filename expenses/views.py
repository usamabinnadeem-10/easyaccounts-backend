from django_filters.rest_framework import DjangoFilterBackend
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log
from rest_framework import generics

from .models import ExpenseAccount, ExpenseDetail
from .queries import ExpenseAccountQuery, ExpenseDetailQuery
from .serializers import ExpenseAccountSerializer, ExpenseDetailSerializer


class CreateExpenseAccount(ExpenseAccountQuery, generics.ListCreateAPIView):
    """
    create expense account or list all expense accounts
    """

    serializer_class = ExpenseAccountSerializer


class CreateExpenseDetail(ExpenseDetailQuery, generics.ListCreateAPIView):
    """
    get expense details with optional filters
    """

    serializer_class = ExpenseDetailSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte"],
        "amount": ["gte", "lte"],
        "account_type": ["exact"],
        "expense__type": ["exact"],
        "detail": ["icontains"],
    }


class EditUpdateDeleteExpenseDetail(
    ExpenseDetailQuery, generics.RetrieveUpdateDestroyAPIView
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
