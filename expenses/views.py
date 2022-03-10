from rest_framework import generics

from django_filters.rest_framework import DjangoFilterBackend

from .models import ExpenseAccount, ExpenseDetail
from .serializers import ExpenseAccountSerializer, ExpenseDetailSerializer
from .queries import ExpenseAccountQuery, ExpenseDetailQuery


class CreateExpenseAccount(ExpenseAccountQuery, generics.ListCreateAPIView):
    """
    create expense account or list all expense accounts
    """

    serializer_class = ExpenseAccountSerializer


class CreateExpenseDetail(ExpenseAccountQuery, generics.ListCreateAPIView):
    """
    get expense details with optional filters
    """

    serializer_class = ExpenseDetailSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = {
        "date": ["gte", "lte"],
        "amount": ["gte", "lte"],
        "account_type": ["exact"],
        "detail": ["icontains"],
    }


class EditUpdateDeleteExpenseDetail(
    ExpenseDetailQuery, generics.RetrieveUpdateDestroyAPIView
):
    """
    Edit / Update / Delete an expense record
    """

    serializer_class = ExpenseDetailSerializer
